"""Generic guards for the dead-handle crash class.

A TTS object handle can outlive its object: the object merges into a deck
mid-flight, a player deletes it, a token stacks onto another. ANY field
access on the stale handle then throws

    cannot access field getNickname of userdata<LuaObject>

and takes the whole action down with it. This has now bitten four separate
features (pry, dawn reveal, threat reveal, gather), each time as a fresh
one-off fix, so these tests target the CLASS instead of the instances:

  1. a runtime sweep that drops a dead handle onto the table and runs the
     real gameplay entry points over it — nothing may raise;
  2. a static scan for the shape that causes it (dereferencing a handle
     that came from a risky source without a guard).

The safe readers live in helpers.lua: safeNickname / safeHasTag /
isLiveObject. See docs/tts-runtime.md.
"""

import os
import re

import pytest

from conftest import (
    LUA_DIR, lua52, add_char, all_lua_files, flush, py_to_lua, read_text,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


# A handle whose object is gone: every field access errors exactly as TTS does.
POISON = """
TTS.addPoisonedHandle = function()
    local dead = setmetatable({}, { __index = function(_, k)
        error("cannot access field " .. tostring(k) .. " of userdata<LuaObject>")
    end })
    table.insert(TTS.world, dead)
    return dead
end
"""


def _world_with_a_dead_handle(env):
    """A normal mid-game table, plus one stale handle sitting in getAllObjects()."""
    add_char(env, "White", "James")
    env.execute("gameState.started = true; gameState.subPhase = 'Day'")
    # Something real to find as well, so the sweep isn't just exercising nil paths.
    env.eval("TTS.addObject")(py_to_lua(env, {
        "tags": ["PlayerBoard:James"], "position": [-18, 1.7, -16], "nickname": "James's Player Board"}))
    env.eval("TTS.addObject")(py_to_lua(env, {
        "tags": ["M_BACKPACK"], "position": [-18, 1.8, -16], "nickname": "Backpack"}))
    env.execute(POISON)
    env.eval("TTS.addPoisonedHandle")()


# Entry points that walk objects off the table. Each is called the way the
# game calls it; none may raise when a dead handle is in the world.
SWEEP = [
    ("playerHasBackpack", 'playerHasBackpack("White")'),
    ("getPlayerCarriedObjects", 'getPlayerCarriedObjects("White", "James")'),
    ("getPlayerResources", 'getPlayerResources("White")'),
    ("auditObjectCount", 'auditObjectCount()'),
    ("findAllByTag", 'findAllByTag("Resource")'),
    ("safeNickname", 'safeNickname(TTS.world[#TTS.world])'),
    ("safeHasTag", 'safeHasTag(TTS.world[#TTS.world], "M_BACKPACK")'),
    ("isLiveObject", 'isLiveObject(TTS.world[#TTS.world])'),
]


@pytest.mark.parametrize("name,call", SWEEP, ids=[s[0] for s in SWEEP])
def test_entry_point_survives_a_dead_handle_on_the_table(env, name, call):
    _world_with_a_dead_handle(env)
    try:
        env.execute("_deadHandleProbe = function() return %s end" % call)
        env.eval("_deadHandleProbe")()
        flush(env)
    except lua52.LuaError as exc:  # pragma: no cover - the failure we're guarding
        pytest.fail(
            f"{name} crashed on a dead object handle:\n  {exc}\n\n"
            "Read object fields through safeNickname / safeHasTag / isLiveObject "
            "(helpers.lua), or pcall-guard the scan, so one stale handle cannot "
            "take the action down. See docs/tts-runtime.md.")


def test_the_safe_readers_return_defaults_rather_than_raising(env):
    """The readers are the fix; if they ever propagate, every caller regresses."""
    env.execute(POISON)
    env.eval("TTS.addPoisonedHandle")()
    env.execute("""
        local dead = TTS.world[#TTS.world]
        _probeNick = safeNickname(dead)
        _probeTag  = safeHasTag(dead, "anything")
        _probeLive = isLiveObject(dead)
    """)
    assert env.eval("_probeNick") == ""
    assert env.eval("_probeTag") is False
    assert env.eval("_probeLive") is False


# ---------------------------------------------------------------------------
# Static scan: the shape that causes the crash.
# ---------------------------------------------------------------------------
# Field access straight off a handle that came from a risky source. `pcall`,
# `safecall` and the safe readers all count as guarded.

_RISKY_SOURCES = re.compile(
    r"(getObjectFromGUID|takeObject|getHandObjects|getObjects)\b")
_GUARDS = ("pcall", "safecall", "safeNickname", "safeHasTag", "isLiveObject",
           "_cardSnapshot")
# Fields that throw on a stale handle (the ones seen in real crash reports).
_FIELD_ACCESS = re.compile(
    r"\b(\w+)\.(getNickname|getDescription|getPosition|getGUID|hasTag|getTags)\s*\(")


def _guarded_window(lines, i, back=6):
    """Is this line inside something that already guards the access?"""
    window = "\n".join(lines[max(0, i - back):i + 1])
    return any(g in window for g in _GUARDS)


def test_no_unguarded_dereference_of_a_risky_handle():
    problems = []
    for rel in all_lua_files():
        src = read_text(os.path.join(LUA_DIR, rel))
        lines = src.splitlines()
        risky = set()
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("--"):
                continue
            # Track variables assigned from a risky source.
            m = re.search(r"local\s+(\w+)\s*=\s*[^=]*" + _RISKY_SOURCES.pattern, line)
            if m:
                risky.add(m.group(1))
            for var, field in _FIELD_ACCESS.findall(line):
                if var in risky and not _guarded_window(lines, i):
                    problems.append(
                        f"{rel}:{i + 1}: {var}.{field}() — {var} came from a handle "
                        "that can already be dead")
    assert not problems, (
        "object handles dereferenced without a guard. A stale handle throws "
        "'cannot access field X of userdata<LuaObject>' and kills the whole "
        "action. Use safeNickname / safeHasTag / isLiveObject (helpers.lua), "
        "or wrap the access in pcall/safecall:\n  " + "\n  ".join(problems))
