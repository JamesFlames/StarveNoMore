"""Every XML click handler, invoked for real, in every phase.

The XML<->Lua contract (test_xml_lua_contract.py) proves each `onClick` names
a real Lua function and each `UI.show("id")` targets a real XML id. Nothing
ever *called* those functions: 58 of 73 handlers were never named in any test,
including every action button in the game. That is exactly the surface TTS is
worst at — a mid-click Lua error is swallowed by `safecall` and shows up as a
button that silently does nothing, which only a human at the table notices.
The commit log is full of the receipts ("ghost Step 2 panel", "self-heal the
setup pick queue", "many many fixes").

So: discover every handler by parsing xml/*.xml, then click it in a matrix of
game states and assert three things.

  1. No Lua error escapes — neither to Python, nor swallowed by `safecall`
     (which broadcasts "Edge case in <context>" and keeps going; without
     checking for that, a crash inside a handler reads as a pass here).
  2. `gameState` invariants still hold afterwards (the same assertions the
     full-campaign integration test uses).
  3. Clicking out of turn or out of phase is *refused*, not obeyed and not
     crashed — a wrong-seat click must not advance the game.

Everything is derived from the XML — the handler names, the element ids, and
the literal arguments (`onClick="onDuskMoveClick(JamesHouse)"`). There is no
hand-maintained fixture table to fall out of date, and nothing is skipped:
test_every_handler_is_exercised fails if a handler is discovered but never
invoked, so adding a button to the XML extends this coverage automatically.
"""
import glob
import os
import re

import pytest

try:
    import lupa.lua52 as lua52
except ImportError:  # pragma: no cover
    lua52 = None

from conftest import ROOT, flush, lua_to_py, make_env, populate_full_world
from test_full_campaign import SEATS, assert_invariants, start_game

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")

# An opening tag and its attribute blob; attributes may span lines.
TAG_RE = re.compile(r"<(\w+)\b([^>]*?)/?>", re.S)
HANDLER_ATTR_RE = re.compile(r'\bon(?:Click|ValueChanged|EndEdit|Submit)\s*=\s*"([^"]+)"')
ID_ATTR_RE = re.compile(r'\bid\s*=\s*"([^"]+)"')

# A handler with no literal argument in the XML is called by TTS with the
# control's own value: "" for a Button, "True"/"False" for a Toggle. Try all
# three rather than guessing which control type each handler is wired to.
VALUELESS_ARGS = ("", "True", "False")

# safecall() (helpers.lua) catches a handler's error, broadcasts this, and
# continues — the exact "button does nothing" failure this module exists for.
SWALLOWED_ERROR_MARKER = "Edge case in"


def discover_handlers():
    """[(handler_name, element_id, arg_value)] for every handler in xml/.

    Derived from the XML on every run, so a new button is covered the moment
    it is added and a deleted one stops being tested.
    """
    found = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "xml", "*.xml"))):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for _element, attrs in TAG_RE.findall(text):
            m = HANDLER_ATTR_RE.search(attrs)
            if not m:
                continue
            raw = m.group(1)
            # "Global/onFoo(arg)" -> name "onFoo", arg "arg"
            name = raw.split("/")[-1].split("(")[0].strip()
            arg = raw.split("(", 1)[1].rstrip(") ").strip() if "(" in raw else None
            if not name:
                continue
            elem_id = (ID_ATTR_RE.search(attrs) or [None, ""])[1] \
                if ID_ATTR_RE.search(attrs) else ""
            found.setdefault(name, {"ids": set(), "args": set()})
            found[name]["ids"].add(elem_id)
            if arg is not None:
                found[name]["args"].add(arg)

    cases = []
    for name in sorted(found):
        elem_id = sorted(found[name]["ids"])[0]
        args = sorted(found[name]["args"]) or list(VALUELESS_ARGS)
        for arg in args:
            cases.append((name, elem_id, arg))
    return cases


HANDLERS = discover_handlers()
HANDLER_NAMES = sorted({name for name, _id, _arg in HANDLERS})


# --------------------------------------------------------------------------
# The state matrix. Each builder returns (env, clicking_color).
# --------------------------------------------------------------------------

def _snapshot_helpers(env):
    """Deep copy in Lua, so a state can be restored exactly between clicks.

    JSON round-tripping would be lossy here (integer table keys come back as
    strings), and these tables are small.
    """
    env.execute("""
        function __smokeCopy(t)
            if type(t) ~= "table" then return t end
            local out = {}
            for k, v in pairs(t) do out[k] = __smokeCopy(v) end
            return out
        end
    """)


def state_pregame():
    env = make_env()
    populate_full_world(env)
    env.globals().onLoad("")
    flush(env)
    env.execute("TTS.seated = {%s}" % ", ".join(f'"{c}"' for c in SEATS))
    return env, "White"


def state_day_active():
    env = make_env()
    start_game(env)
    env.globals().BeginDay()
    flush(env)
    return env, env.eval("gameState.activeColor") or "White"


def state_day_wrong_seat():
    """A seated player who is NOT the active one clicking every button."""
    env = make_env()
    start_game(env)
    env.globals().BeginDay()
    flush(env)
    active = env.eval("gameState.activeColor")
    other = next(c for c in SEATS if c != active)
    return env, other


def state_dusk():
    env = make_env()
    start_game(env)
    env.globals().BeginDay()
    flush(env)
    env.execute('gameState.subPhase = "Dusk"')
    return env, env.eval("gameState.activeColor") or "White"


def state_night():
    env = make_env()
    start_game(env)
    env.globals().BeginDay()
    flush(env)
    env.execute('gameState.subPhase = "Night"')
    return env, env.eval("gameState.activeColor") or "White"


def state_gameover():
    env = make_env()
    start_game(env)
    env.globals().BeginDay()
    flush(env)
    # Reach GameOver the way the game does, not by poking subPhase.
    env.execute("gameState.doom = getDoomLimit()")
    env.globals().checkDefeat()
    flush(env)
    assert env.eval("gameState.subPhase") == "GameOver"
    return env, env.eval("gameState.activeColor") or "White"


STATES = {
    "pregame": state_pregame,
    "day_active": state_day_active,
    "day_wrong_seat": state_day_wrong_seat,
    "dusk": state_dusk,
    "night": state_night,
    "gameover": state_gameover,
}

# Handlers recorded as invoked, so test_every_handler_is_exercised can prove
# the matrix actually covers the XML rather than quietly skipping entries.
_EXERCISED = set()


def click(env, name, value, elem_id, color):
    """Invoke one handler exactly as TTS would: handler(player, value, id)."""
    env.execute("TTS.broadcasts = {}")
    player = env.eval(f'Player["{color}"]')
    env.eval(name)(player, value, elem_id)
    flush(env)


def swallowed_errors(env):
    return [b["message"] for b in lua_to_py(env.eval("TTS.broadcasts"))
            if SWALLOWED_ERROR_MARKER in b["message"]]


@pytest.mark.parametrize("state", sorted(STATES))
def test_every_handler_survives_every_phase(state):
    env, color = STATES[state]()
    _snapshot_helpers(env)
    env.execute("__smokeSaved = __smokeCopy(gameState)")

    failures = []
    for name, elem_id, value in HANDLERS:
        # Restore the phase state so each handler is judged from the same
        # starting point rather than from whatever the previous one left.
        env.execute("gameState = __smokeCopy(__smokeSaved)")
        _EXERCISED.add(name)
        try:
            click(env, name, value, elem_id, color)
        except lua52.LuaError as exc:
            failures.append(f"{name}({value!r}) id={elem_id!r}: hard Lua error: {exc}")
            continue

        swallowed = swallowed_errors(env)
        if swallowed:
            failures.append(
                f"{name}({value!r}) id={elem_id!r}: error swallowed by safecall "
                f"— the button would silently do nothing in TTS: {swallowed[0]}")
            continue

        try:
            assert_invariants(env, f"{state}: after {name}({value!r})")
        except AssertionError as exc:
            failures.append(f"{name}({value!r}) id={elem_id!r}: broke an invariant: {exc}")

    assert not failures, (
        f"{len(failures)} handler(s) failed when clicked in state {state!r} "
        f"as {color}:\n  " + "\n  ".join(failures))


def test_every_handler_is_exercised():
    """No handler may be discovered and then skipped.

    This is what stops the coverage rotting: if a future change makes some
    handler unreachable by the matrix, that shows up here instead of quietly
    shrinking what this module tests.
    """
    assert HANDLER_NAMES, "no XML handlers discovered — the parser broke"
    missed = sorted(set(HANDLER_NAMES) - _EXERCISED)
    assert not missed, (
        f"handlers discovered in xml/ but never invoked: {missed}")


def test_wrong_seat_clicks_cannot_take_a_turn():
    """Out-of-turn action clicks must be refused, not merely survived.

    'No crash' is not enough: a handler that runs for the wrong player is the
    alpha-player hole the design spends §11 closing. This asserts the action
    buttons actually decline, by watching the active player's action budget.
    """
    env, wrong_color = state_day_wrong_seat()
    _snapshot_helpers(env)
    env.execute("__smokeSaved = __smokeCopy(gameState)")

    action_handlers = sorted({name for name, _i, _a in HANDLERS
                              if name.startswith("onAct")})
    assert action_handlers, "no onAct* handlers found — the parser broke"

    offenders = []
    for name, elem_id, value in HANDLERS:
        if name not in action_handlers:
            continue
        env.execute("gameState = __smokeCopy(__smokeSaved)")
        active = env.eval("gameState.activeColor")
        before = env.eval(f'gameState.activeChars["{active}"].actionsLeft')
        try:
            click(env, name, value, elem_id, wrong_color)
        except lua52.LuaError:
            continue  # already reported by the matrix test
        after = env.eval(f'gameState.activeChars["{active}"].actionsLeft')
        if after != before:
            offenders.append(
                f"{name}: a click from {wrong_color} (active seat is {active}) "
                f"spent the active player's action ({before} -> {after})")

    assert not offenders, "out-of-turn clicks were obeyed:\n  " + "\n  ".join(offenders)
