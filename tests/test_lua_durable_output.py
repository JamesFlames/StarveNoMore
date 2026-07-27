"""Actions must deliver their result on a channel the player can still read.

The bug this module exists to stop: **Pattern Recognition (Peek)**. It spent
James's once-per-day free action, correctly read the top of the Threat deck,
and handed the answer to `broadcastToColor` — which renders *behind* the Phase
Banner and fades in seconds (docs/tts-interface.md, "Talking to players").
From the seat it looked like the button did nothing at all.

Why the obvious static check does not catch it: `doPeek` DID call
`broadcastEvent` — for the public flavour line ("James studies the Threat
deck..."). A "does this function mention a durable channel anywhere" scan
passes happily while the part that matters evaporates. So the check here is
behavioural: drive the action with a sentinel that can only come from the
payload, then look for that sentinel in the channels that survive —
`gameState.messageLog` (the Message Log panel) and any UI panel left visible.

Two guards:
  * INFORMATION_ACTIONS — verbs whose whole product is information. Each is
    driven for real and its payload must land somewhere durable.
  * test_every_action_verb_is_classified — every `function do*` in lua/ must
    appear in one of the lists below, so a new action cannot be added without
    someone deciding which kind it is.
"""
import os
import re

import pytest

from conftest import (
    lua52, add_char, lua_to_py, py_to_lua, LUA_DIR,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


# --------------------------------------------------------------------------
# What survives on screen after an action?
# --------------------------------------------------------------------------

def durable_text(env):
    """Everything the player can still read once the broadcasts have faded:
    the persistent Message Log, plus the text of every panel left visible."""
    out = []
    log = lua_to_py(env.eval("gameState.messageLog or {}"))
    if isinstance(log, dict):
        log = list(log.values())
    for entry in log or []:
        if isinstance(entry, dict):
            out.append(str(entry.get("text", "")))
        else:
            out.append(str(entry))

    ui = lua_to_py(env.eval("TTS.ui"))
    # A panel's children are named <panel>Body / <panel>Title (whatNowPanel ->
    # whatNowBody), so a visible "fooPanel" makes every "foo*" element's text
    # readable. Text sitting on a hidden panel does not count.
    prefixes = {k[:-5] if k.endswith("Panel") else k
                for k, v in (ui.get("visible") or {}).items() if v}
    for elem_id, attrs in (ui.get("attrs") or {}).items():
        if any(elem_id.startswith(pre) for pre in prefixes):
            out.append(str((attrs or {}).get("text", "")))
    return "\n".join(out)


def ephemeral_text(env):
    """Broadcast traffic — renders behind the Phase Banner and fades."""
    return "\n".join(str(m) for m in lua_to_py(env.eval("TTS.broadcasts")) or [])


# --------------------------------------------------------------------------
# 1. Information actions must put the information somewhere durable.
# --------------------------------------------------------------------------

SENTINEL = "Zzyzx Sentinel Card"
SENTINEL_RULES = "Sentinel rules text QQQ"


def _peek_world(env):
    add_char(env, "White", "James")
    env.eval("TTS.addObject")(py_to_lua(env, {
        "tags": ["ThreatCardDeck"], "position": [-9, -2.5, -4],
        "contained": [{"nickname": SENTINEL, "description": SENTINEL_RULES}],
    }))
    return lambda: env.globals().doPeek("White", "Threat")


# verb -> world builder returning a callable that performs the action.
INFORMATION_ACTIONS = {
    "doPeek": _peek_world,
}

# Verbs that change the game state. Their outcome is legible from the state
# and the Message Log entry that reports it, so they are not payload-checked
# here; the transient "cancelled" / "not adjacent" broadcasts they also emit
# are prompts, which is what a broadcast is for.
EFFECT_ACTIONS = {
    "doUndo", "doMove", "doRaymanBonusMove", "doDuskMove", "doGather", "doRest",
    "doFightTarget", "doFlee", "doTrade", "doEnergyDrink", "doEatRaw", "doPass",
    "doBarricade", "doDefend", "doRally", "doPry", "doStabilize", "doCraft",
    "doCook", "doSignature", "doCleanse", "doAppeaseTreeguard",
}


@pytest.mark.parametrize("verb", sorted(INFORMATION_ACTIONS))
def test_information_actions_leave_their_answer_on_screen(env, verb):
    perform = INFORMATION_ACTIONS[verb](env)
    assert perform() is True, f"{verb} did not succeed in the test world"

    durable = durable_text(env)
    assert SENTINEL in durable, (
        f"{verb} revealed '{SENTINEL}' but nothing durable carries it.\n"
        f"Only-ephemeral output was:\n{ephemeral_text(env)}\n\n"
        "Broadcasts render behind the Phase Banner and fade in seconds, so the "
        "player spends the action and sees nothing happen. Put the payload in "
        "a panel (per-player visibility if it is private) or the Message Log.")
    assert SENTINEL_RULES in durable, (
        f"{verb} carried the card's NAME durably but dropped its rules text — "
        "the half that tells the player what to do about it.")


def test_a_private_information_action_does_not_leak_to_the_shared_log(env):
    """The counterweight to the guard above: Peek is 'tell the team, or
    don't'. Making it durable must not make it public — the answer belongs in
    a panel scoped to the peeker, not in the Message Log everyone reads."""
    perform = INFORMATION_ACTIONS["doPeek"](env)
    perform()
    entries = lua_to_py(env.eval("gameState.messageLog or {}")) or []
    if isinstance(entries, dict):
        entries = list(entries.values())
    log = "\n".join(str(e.get("text", "")) for e in entries if isinstance(e, dict))
    assert SENTINEL not in log, (
        "the peeked card reached the shared Message Log — Pattern Recognition "
        "is private information")

    ui = lua_to_py(env.eval("TTS.ui"))
    panels = [pid for pid, a in (ui.get("attrs") or {}).items()
              if SENTINEL in str((a or {}).get("text", ""))]
    assert panels, "no panel carries the peeked card"
    for pid in panels:
        vis = (ui["attrs"][pid] or {}).get("visibility")
        owner = vis or (ui["attrs"].get(pid.replace("Body", "Panel"), {}) or {}).get("visibility")
        assert owner == "White", (
            f"panel '{pid}' shows the peeked card to everyone (visibility="
            f"{owner!r}); scope it to the peeker's colour")


# --------------------------------------------------------------------------
# 2. Nobody may add an action without deciding which kind it is.
# --------------------------------------------------------------------------

def test_every_action_verb_is_classified():
    verbs = set()
    for dirpath, dirnames, filenames in os.walk(LUA_DIR):
        for fn in filenames:
            if not fn.endswith(".lua"):
                continue
            with open(os.path.join(dirpath, fn), "r", encoding="utf-8") as f:
                verbs |= set(re.findall(r"^function (do[A-Z][A-Za-z0-9_]*)\s*\(",
                                        f.read(), re.M))

    known = set(INFORMATION_ACTIONS) | EFFECT_ACTIONS
    unclassified = sorted(verbs - known)
    assert not unclassified, (
        f"new action verb(s) {unclassified} — add each to INFORMATION_ACTIONS "
        "(its product is information the player must read: give it a world "
        "builder here so its payload is checked) or to EFFECT_ACTIONS (it "
        "changes the game state). See this module's docstring for why the "
        "distinction is what keeps Peek fixed.")

    stale = sorted(known - verbs)
    assert not stale, (
        f"classified verb(s) {stale} no longer exist in lua/ — drop them so "
        "the lists keep meaning something.")
