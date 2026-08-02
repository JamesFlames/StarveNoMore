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

from conftest import flush, lua_to_py, make_env, populate_full_world

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
        lambda c: g.doEatUncooked(c),
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

    env.globals().Setup("White")                               # bare path
    env.execute('onHostSetupGuided(Player["White"])')          # host panel path
    env.execute('startGuidedSetup("White")')                   # the walkthrough itself
    flush(env)

    assert env.eval("gameState.started") is True
    assert env.eval("gameState.day") == day_before
    party_after = sorted(c["name"] for c in lua_to_py(env.eval("gameState.activeChars")).values())
    assert party_after == party_before, "a re-entrant setup path rewrote the party"
    assert any("already started" in m for m in _broadcast_messages(env)), (
        "re-entrant setup must refuse loudly, not silently")


def test_guided_setup_reseats_players_to_character_colors():
    """A player's colour is determined by the character they pick, so setup
    ends with everyone on CHARACTER_COLORS' seat for their character.

    This is a straight SWAP — White takes James (Blue) while Blue takes Coco
    (White) — which is a closed 2-cycle: neither can move until the other
    does. applyCharacterSeating breaks it through a spare seat and must put
    BOTH players back on character colours, because a player stranded off
    the five seats has no hand zone and TTS re-prompts them to choose a
    colour mid-game. The reseat happens once, at finalize; nobody changes
    colour while the walkthrough is still on screen."""
    env = make_env()
    populate_full_world(env)
    env.globals().onLoad("")
    flush(env)
    env.execute('TTS.seated = {"White", "Blue"}')
    env.execute('onHostSetupGuided(Player["White"])')
    env.execute('onPickPath(Player["White"], "-1", "pickCompact")')
    env.execute('onVariantsContinue(Player["White"], "-1", "variantsContinue")')
    flush(env)

    env.execute('onPickChar(Player["White"], "-1", "pickJames")')
    env.execute('onBriefDismiss(Player["White"], "-1", "briefDismiss")')
    # Still White and Blue at this point — no colour has changed yet.
    mid = lua_to_py(env.eval("TTS.seated"))
    if isinstance(mid, dict):
        mid = list(mid.values())
    assert sorted(mid) == ["Blue", "White"], (
        f"somebody was reseated while the walkthrough was still open: {mid}")
    env.execute('onPickChar(Player["Blue"], "-1", "pickCoco")')
    env.execute('onBriefDismiss(Player["Blue"], "-1", "briefDismiss")')
    flush(env)

    assert env.eval("gameState.started") is True
    chars = lua_to_py(env.eval("gameState.activeChars"))
    assert chars["Blue"]["name"] == "James", chars
    assert chars["White"]["name"] == "Coco", chars
    seated = lua_to_py(env.eval("TTS.seated"))
    if isinstance(seated, dict):
        seated = list(seated.values())
    assert sorted(seated) == ["Blue", "White"], seated


def _run_guided_setup(env):
    """The two-player guided walkthrough, clicked through end to end."""
    populate_full_world(env)
    env.globals().onLoad("")
    flush(env)
    env.execute('TTS.seated = {"White", "Blue"}')
    env.execute('onHostSetupGuided(Player["White"])')
    env.execute('onPickPath(Player["White"], "-1", "pickCompact")')
    env.execute('onVariantsContinue(Player["White"], "-1", "variantsContinue")')
    flush(env)
    # Nobody changes colour during the walkthrough any more, so each player
    # picks and dismisses from the seat they sat down in. The reseat onto
    # character colours happens once, at finalize.
    env.execute('onPickChar(Player["White"], "-1", "pickJames")')
    env.execute('onBriefDismiss(Player["White"], "-1", "briefDismiss")')
    env.execute('onPickChar(Player["Blue"], "-1", "pickCoco")')
    env.execute('onBriefDismiss(Player["Blue"], "-1", "briefDismiss")')
    flush(env)


def _visible(env, panel):
    vis = lua_to_py(env.eval("TTS.ui.visible")) or {}
    return bool(vis.get(panel))


SETUP_PANELS = ("setupStep1", "setupStepVariants", "setupStep2", "charBriefing")


def test_finalize_closes_every_walkthrough_panel():
    """Once the game starts, no setup panel may be left on screen. TTS
    rebuilds a player's UI canvas on Player.changeColor, so the reseat inside
    a pick can eat that client's hide — and nothing downstream ever hid
    setupStep2 again, leaving the reseated player clicking dead cards on a
    game that had already begun."""
    env = make_env()
    _run_guided_setup(env)
    assert env.eval("gameState.started") is True
    for panel in SETUP_PANELS:
        assert not _visible(env, panel), f"{panel} still on screen after setup finished"


def test_leftover_pick_panel_closes_instead_of_swallowing_the_click():
    env = make_env()
    _run_guided_setup(env)
    party_before = sorted(c["name"] for c in lua_to_py(env.eval("gameState.activeChars")).values())

    # The client that missed the hide still has the panel up (simulated here
    # by re-showing it) and clicks a card.
    env.execute('UI.show("setupStep2")')
    env.execute('TTS.broadcasts = {}')
    env.execute('onPickChar(Player["Blue"], "-1", "pickRayman")')
    flush(env)

    assert not _visible(env, "setupStep2"), "a click on the ghost panel must close it"
    party_after = sorted(c["name"] for c in lua_to_py(env.eval("gameState.activeChars")).values())
    assert party_after == party_before, "a post-setup pick click changed the party"
    assert any("Begin Day" in m for m in _broadcast_messages(env)), (
        "the dead click must explain itself, not vanish")


def test_late_briefing_clicks_cannot_rerun_setup():
    """Both briefing buttons are reachable from a ghost panel. 'I understand'
    ends in finalizeGuidedSetup — unguarded, a stray click mid-game wiped the
    party and reset the table to a fresh Day 1."""
    env = make_env()
    _run_guided_setup(env)
    env.globals().BeginDay()
    flush(env)
    env.execute('gameState.activeChars["Blue"].health = 3')
    subphase_before = subphase(env)

    env.execute('onBriefDismiss(Player["Blue"], "-1", "briefDismiss")')
    env.execute('onBriefBack(Player["Blue"], "-1", "briefBack")')
    flush(env)

    assert env.eval('gameState.activeChars["Blue"].health') == 3, (
        "a late briefing click re-ran setup and restored the party")
    assert subphase(env) == subphase_before, "a late briefing click rewound the phase"
    for panel in SETUP_PANELS:
        assert not _visible(env, panel), f"{panel} reopened mid-game"


def _begin_walkthrough(env, seated, host):
    populate_full_world(env)
    env.globals().onLoad("")
    flush(env)
    env.execute("TTS.seated = {%s}" % ", ".join(f'"{c}"' for c in seated))
    env.execute(f'onHostSetupGuided(Player["{host}"])')
    env.execute(f'onPickPath(Player["{host}"], "-1", "pickCompact")')
    env.execute(f'onVariantsContinue(Player["{host}"], "-1", "variantsContinue")')
    flush(env)


def _setup_field(env, field):
    """Read one field out of dumpSetupState()'s line (setupState is local)."""
    line = env.eval("dumpSetupState()")
    order = ["waiting:", "| picked:", "| seated:"]
    seg = line.split(field)[1]
    for nxt in order:
        if nxt != field and nxt in seg:
            seg = seg.split(nxt)[0]
    seg = seg.strip()
    return [] if seg == "nobody" else [p.strip() for p in seg.split(",")]


def test_pick_never_requeues_the_picker_under_their_new_colour():
    """A pick MOVES the picker onto their character's colour. When that
    colour was itself still queued (its player left, or an earlier swap
    freed it), the picker became the head of their own queue — "<name> picks
    a character" that never advances, one more card greyed out per click."""
    env = make_env()
    _begin_walkthrough(env, ("Blue", "Green", "Yellow"), "Green")
    # The Blue player leaves the table; Blue is still in the queue.
    env.execute('TTS.seated = {"Green", "Yellow"}')
    # Green picks James, whose seat is Blue — straight onto the queued seat.
    env.execute('onPickChar(Player["Green"], "-1", "pickJames")')
    env.execute('onBriefDismiss(Player["Blue"], "-1", "briefDismiss")')
    flush(env)

    waiting = [w.split("=")[0] for w in _setup_field(env, "waiting:")]
    assert waiting == ["Yellow"], f"picker re-queued under their new colour: {waiting}"


def test_a_seated_player_the_queue_missed_can_still_pick():
    """Sitting down after Setup started (or moving seats) left a real player
    out of the queue, and the walkthrough refused every card they clicked —
    a dead end, since the queue was waiting on a seat they weren't in."""
    env = make_env()
    _begin_walkthrough(env, ("White", "Blue"), "White")
    env.execute('TTS.seated = {"White", "Blue", "Yellow"}')
    env.execute('onPickChar(Player["Yellow"], "-1", "pickEllie")')
    flush(env)

    assert "Yellow=Ellie" in _setup_field(env, "| picked:"), (
        "a seated player without a character must pick for themself")


def test_a_player_leaving_mid_setup_does_not_hang_the_walkthrough():
    env = make_env()
    _begin_walkthrough(env, ("White", "Blue"), "White")
    env.execute('onPickChar(Player["White"], "-1", "pickCoco")')
    env.execute('TTS.seated = {"White"}')      # the Blue player quits
    env.execute('onBriefDismiss(Player["White"], "-1", "briefDismiss")')
    flush(env)

    assert env.eval("gameState.started") is True, (
        "setup hung waiting on a seat nobody is sitting in")
    party = sorted(c["name"] for c in lua_to_py(env.eval("gameState.activeChars")).values())
    assert party == ["Coco"], party


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


# gameState was built from scratch in two places that had to agree and were
# not bound: the literal in global.lua and a hand-copied shorter literal on
# the Restart path in ui_controls.lua. They had already drifted — Restart
# omitted resources, dailyAlerts, messageLog, haunted, threatDamage,
# cluesFound, duskPending and schemaVersion. Both now go through
# migrateGameState(), and this is the assertion that keeps them there.

# Fields whose default IS nil, so they are absent from a fresh state too and
# carry no information when present. Keep this list SHORT and justified — it
# is the escape hatch that would let the drift back in.
RESTART_OPTIONAL_FIELDS = {
    # The previous game's Week in Review record. Restart must NOT keep it;
    # ensureChronicle() (ui_week_review.lua) rebuilds it on first use.
    "chronicle",
}


def test_restart_state_matches_fresh_load():
    """Restarting must leave gameState with every field a fresh load has."""
    fresh = make_env()
    fresh.globals().onLoad("")
    flush(fresh)
    fresh_keys = set(lua_to_py(fresh.eval("gameState")).keys())

    env = make_env()
    start_game(env)
    env.globals().BeginDay()
    flush(env)
    env.execute('onHostRestart(Player["White"])')
    env.execute('onConfirmYes(Player["White"])')
    flush(env)
    restart_keys = set(lua_to_py(env.eval("gameState")).keys())

    missing = fresh_keys - restart_keys - RESTART_OPTIONAL_FIELDS
    assert not missing, (
        "Restart produced a gameState missing field(s) a fresh load has: "
        f"{sorted(missing)}. Both paths must go through migrateGameState() "
        "(lua/global.lua) — declare the default there, not in a literal."
    )

    # The vault is the one thing that outlives a game, and migrateGameState
    # must not have clobbered it on the way through.
    assert lua_to_py(env.eval("gameState.achievements")) is not None
    assert env.eval("gameState.schemaVersion") == env.eval("SCHEMA_VERSION")


def test_migrate_fills_every_field_for_an_empty_state():
    """migrateGameState() alone must produce a playable state from `{}`.

    This is what the Restart path relies on, and what an ancient save hits.
    """
    env = make_env()
    env.globals().onLoad("")
    flush(env)
    fresh_keys = set(lua_to_py(env.eval("gameState")).keys())

    env.execute("gameState = {}")
    env.globals().migrateGameState()
    migrated_keys = set(lua_to_py(env.eval("gameState")).keys())

    missing = fresh_keys - migrated_keys - RESTART_OPTIONAL_FIELDS
    assert not missing, (
        f"migrateGameState() left field(s) undeclared: {sorted(missing)} — "
        "they exist only in the gameState literal (lua/global.lua), so any "
        "path that does not start from that literal reads nil."
    )
    assert env.eval("gameState.day") == 1
    assert env.eval("gameState.doom") == 0
    assert env.eval("gameState.subPhase") == "PreGame"
    assert env.eval("gameState.started") is False


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
