"""Full-campaign integration: a trivial bot plays whole games headlessly.

The unit tests exercise systems in isolation; this file is the net for
cross-feature breakage (F in frameworkimprovements.md) — the "two features,
each tested, broken together" class. Assertions are invariants only:

  * no hard Lua error ever escapes a public entry point,
  * stats stay within 0..max, Doom stays sane,
  * every campaign reaches a verdict (GameOver) within its day budget.

A seeded fuzz variant slams random public verbs (with wrong colors, wrong
phases, wrong targets included) to check the guard rails hold.
"""
import random

import pytest

try:
    import lupa.lua52 as lua52
except ImportError:  # pragma: no cover
    lua52 = None

from conftest import make_env, populate_full_world, flush, lua_to_py

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")

# Seat colours follow characters (CHARACTER_COLORS): Coco=White,
# Rayman=Green, James=Blue — a trio with Rayman exercises the 3p reliefs.
SEATS = ("White", "Green", "Blue")
LOCATIONS = ["JamesHouse", "RaymanHouse", "EllieLucaHouse", "BasketballCourt", "BadmintonCourt"]


def start_game(env, difficulty="standard"):
    populate_full_world(env)
    env.globals().onLoad("")
    flush(env)
    env.execute("TTS.seated = {%s}" % ", ".join(f'"{c}"' for c in SEATS))
    if difficulty != "standard":
        env.execute(f'gameState.difficulty = "{difficulty}"')
    env.globals().Setup("White")
    flush(env)
    assert env.eval("gameState.started") is True
    assert env.eval("gameState.playerCount") == len(SEATS)


def subphase(env):
    return env.eval("gameState.subPhase")


def assert_invariants(env, context):
    chars = lua_to_py(env.eval("gameState.activeChars")) or {}
    for color, c in chars.items():
        for stat, cap in (("health", "maxHealth"), ("hunger", "maxHunger"), ("sanity", "maxSanity")):
            v, m = c[stat], c[cap]
            assert 0 <= v <= m, f"{context}: {c['name']} {stat}={v} outside 0..{m}"
        if not c.get("down"):
            assert c["health"] > 0 and c["sanity"] > 0, (
                f"{context}: {c['name']} standing at health={c['health']} sanity={c['sanity']}")
    doom = env.eval("gameState.doom")
    limit = env.globals().getDoomLimit()
    assert 0 <= doom <= limit + 10, f"{context}: doom {doom} far outside 0..{limit}"


def simple_bot_turn(env, color):
    """Gather when steady, rest when shaky, then pass — the turtle in Lua."""
    char = lua_to_py(env.eval(f'gameState.activeChars["{color}"]'))
    if char and not char.get("down"):
        for _ in range(int(char.get("actionsLeft") or 0)):
            if char["sanity"] <= 4 or char["health"] <= 3:
                env.globals().doRest(color, "sanity")
            else:
                env.globals().doGather(color)
    env.globals().doPass(color)


def play_day(env, turn_fn):
    env.globals().BeginDay()
    flush(env)
    if subphase(env) == "GameOver":
        return
    guard = 0
    while subphase(env) == "Day" and env.eval("gameState.activeColor"):
        guard += 1
        assert guard < 60, "day loop did not hand off to Dusk"
        turn_fn(env, env.eval("gameState.activeColor"))
        flush(env)
    if subphase(env) == "Dusk":
        env.globals().beginNight()
        flush(env)   # ResolveNight -> storytelling -> sleep -> resolveTick


@pytest.mark.parametrize("difficulty,day_budget", [
    ("standard", 7), ("weekend", 3), ("nightmare", 7),
])
def test_bot_campaign_reaches_a_verdict(difficulty, day_budget):
    env = make_env()
    start_game(env, difficulty)
    for played in range(day_budget + 1):
        if subphase(env) == "GameOver":
            break
        play_day(env, simple_bot_turn)
        assert_invariants(env, f"{difficulty} after day {played + 1}")
    assert subphase(env) == "GameOver", (
        f"{difficulty}: campaign never reached victory or defeat "
        f"(day={env.eval('gameState.day')}, doom={env.eval('gameState.doom')})")
    assert env.eval("gameState.gameOverCause") in (
        "victory", "defeat_doom", "defeat_all_down", "defeat_source")


def test_session_log_exports_after_bot_campaign():
    """The batch-4 telemetry must survive a real full game, not just unit
    fixtures: the log round-trips through JSON with turns recorded."""
    import json
    env = make_env()
    start_game(env, "weekend")   # shortest full campaign
    for _ in range(4):
        if subphase(env) == "GameOver":
            break
        play_day(env, simple_bot_turn)
    log = json.loads(env.globals().exportSessionLog())
    assert log["setup"]["playerCount"] == len(SEATS)
    assert log["setup"]["difficulty"] == "weekend"
    assert len(log["turns"]) >= 3, "turn durations were not recorded"
    assert log["outcome"]["cause"] in (
        "victory", "defeat_doom", "defeat_all_down", "defeat_source", None)


# ---------------------------------------------------------------------------
# Fuzz: random public verbs, random (often wrong) colors and targets.
# Reaching the end without a raised Lua error IS the assertion — every
# refusal must be a broadcast, never a crash.
# ---------------------------------------------------------------------------

def _fuzz_verbs(env, rng):
    g = env.globals()
    return [
        lambda c: g.doMove(c, rng.choice(LOCATIONS)),
        lambda c: g.doGather(c),
        lambda c: g.doRest(c, rng.choice(["hunger", "sanity"])),
        lambda c: g.doEatRaw(c),
        lambda c: g.doEnergyDrink(c),
        lambda c: g.doFlee(c, rng.choice(LOCATIONS)),
        lambda c: g.doBarricade(c),
        lambda c: g.doCleanse(c),
        lambda c: g.doSignature(c),
        lambda c: g.doPry(c),
        lambda c: g.doTrade(c, rng.choice(list(SEATS))),
        lambda c: g.doCook(c, rng.choice(["R_PORRIDGE", "R_LEFTOVERS", "R_HOT_STEW"])),
        lambda c: g.doDuskMove(c, rng.choice(LOCATIONS)),
        lambda c: g.doStabilize(c, rng.choice(list(SEATS))),
        lambda c: g.pressAttack(c, False),
        lambda c: g.doUndo(c),
    ]


# ---------------------------------------------------------------------------
# Adversarial sequences: hostile click patterns real tables produce — spam,
# re-entrancy, restarts — must degrade to broadcasts, never corrupt state.
# ---------------------------------------------------------------------------

def _broadcast_messages(env):
    broadcasts = lua_to_py(env.eval("TTS.broadcasts")) or []
    if isinstance(broadcasts, dict):     # lua_to_py maps array tables to lists, but be safe
        broadcasts = list(broadcasts.values())
    return [b["message"] for b in broadcasts]


def test_undo_spam_refunds_exactly_once():
    env = make_env()
    start_game(env)
    env.globals().BeginDay()
    flush(env)
    color = env.eval("gameState.activeColor")
    assert color, "no active player after BeginDay"
    before = env.eval(f'gameState.activeChars["{color}"].actionsLeft')
    env.globals().doGather(color)
    flush(env)
    for _ in range(5):
        env.globals().doUndo(color)
    after = env.eval(f'gameState.activeChars["{color}"].actionsLeft')
    assert after == before, f"undo spam changed actions {before} -> {after} (must refund once)"
    assert_invariants(env, "undo spam")


def test_reentrant_setup_is_refused():
    env = make_env()
    start_game(env)
    party_before = sorted(c["name"] for c in lua_to_py(env.eval("gameState.activeChars")).values())
    env.globals().BeginDay()
    flush(env)
    day_before = env.eval("gameState.day")

    env.globals().Setup("White")           # bare path
    env.execute('onSetupClick(TTS.makeObject({}), "White")')   # 3D board button path
    env.execute('onHostSetupGuided(Player["White"])')          # host panel path
    flush(env)

    assert env.eval("gameState.started") is True
    assert env.eval("gameState.day") == day_before
    party_after = sorted(c["name"] for c in lua_to_py(env.eval("gameState.activeChars")).values())
    assert party_after == party_before, "a re-entrant setup path rewrote the party"
    assert any("already started" in m for m in _broadcast_messages(env)), (
        "re-entrant setup must refuse loudly, not silently")


def test_guided_setup_reseats_players_to_character_colors():
    """A player's colour is determined by the character they pick: the
    guided walkthrough reseats each picker onto CHARACTER_COLORS' seat for
    that character. Anyone parked on the target seat SWAPS onto the
    picker's old seat — never a spare seat, because a player stranded off
    the five character seats has no hand zone and TTS re-prompts them to
    choose a colour mid-game."""
    env = make_env()
    populate_full_world(env)
    env.globals().onLoad("")
    flush(env)
    env.execute('TTS.seated = {"White", "Blue"}')
    env.execute('onHostSetupGuided(Player["White"])')
    env.execute('onPickPath(Player["White"], "-1", "pickCompact")')
    env.execute('onVariantsContinue(Player["White"], "-1", "variantsContinue")')
    flush(env)

    # White player picks James -> James plays Blue; the pending player
    # parked on Blue swaps onto White (the picker's old seat).
    env.execute('onPickChar(Player["White"], "-1", "pickJames")')
    env.execute('onBriefDismiss(Player["Blue"], "-1", "briefDismiss")')
    # The displaced player (now White) picks Coco -> Coco plays White,
    # already their seat, so no further move happens.
    env.execute('onPickChar(Player["White"], "-1", "pickCoco")')
    env.execute('onBriefDismiss(Player["White"], "-1", "briefDismiss")')
    flush(env)

    assert env.eval("gameState.started") is True
    chars = lua_to_py(env.eval("gameState.activeChars"))
    assert chars["Blue"]["name"] == "James", chars
    assert chars["White"]["name"] == "Coco", chars
    seated = lua_to_py(env.eval("TTS.seated"))
    if isinstance(seated, dict):
        seated = list(seated.values())
    assert sorted(seated) == ["Blue", "White"], seated


def test_restart_then_resetup_is_clean():
    env = make_env()
    start_game(env)
    env.globals().BeginDay()
    flush(env)
    # Host restarts mid-day, through the confirm dialog like a real click.
    env.execute('onHostRestart(Player["White"])')
    env.execute('onConfirmYes(Player["White"])')
    flush(env)
    assert env.eval("gameState.started") is False
    assert not (lua_to_py(env.eval("gameState.activeChars")) or {}), (
        "restart left stale characters in the roster")

    # A fresh setup on the same table works and produces a clean Day 1.
    env.globals().Setup("White")
    flush(env)
    assert env.eval("gameState.started") is True
    assert env.eval("gameState.day") == 1
    assert env.eval("gameState.doom") == 0
    assert_invariants(env, "post-restart re-setup")


@pytest.mark.parametrize("seed", [11, 23, 47])
def test_fuzz_campaign_no_hard_errors(seed):
    rng = random.Random(seed)
    env = make_env()
    start_game(env, "standard")
    verbs = _fuzz_verbs(env, rng)
    for _day in range(8):
        if subphase(env) == "GameOver":
            break
        env.globals().BeginDay()
        flush(env)
        guard = 0
        while subphase(env) == "Day" and env.eval("gameState.activeColor") and guard < 40:
            guard += 1
            # mostly the active player, sometimes a wrong one (guards must hold)
            color = env.eval("gameState.activeColor") if rng.random() < 0.8 else rng.choice(list(SEATS))
            rng.choice(verbs)(color)
            if rng.random() < 0.30 or guard > 25:
                active = env.eval("gameState.activeColor")
                if active:
                    env.globals().doPass(active)
            flush(env)
        if subphase(env) == "Dusk":
            if rng.random() < 0.5:
                env.globals().doDuskMove(rng.choice(list(SEATS)), rng.choice(LOCATIONS))
            env.globals().beginNight()
            flush(env)
        assert_invariants(env, f"fuzz seed {seed} day {_day + 1}")
