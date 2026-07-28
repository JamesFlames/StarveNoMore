"""bundle load, phase/doom math, scenarios, night light checks, self-test.

Headless execution of the real game Lua under Lua 5.2 (lupa) with the TTS
stub. The bundle harness (env fixture, add_char, script_dice, ...) lives in
tests/conftest.py; split out of the former monolithic test_lua_runtime.py.
"""
import json as _json

import pytest
from conftest import (
    add_char,
    flush,
    lua52,
    lua_to_py,
    make_env,
    populate_full_world,
    py_to_lua,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


class TestLoad:
    def test_bundle_executes(self, env):
        # make_env() already executed the full bundle; reaching here means no
        # load-time error (this is the test that catches things like the
        # assets.lua url()-vs-_url() crash).
        assert env.eval("type(onLoad)") == "function"
        assert env.eval("type(onSave)") == "function"

    def test_key_tables_defined(self, env):
        for table in ["gameState", "CHARACTER_STATS", "DAWN_EFFECTS", "DAWN_MANUAL_STEPS",
                      "MARKET_COSTS", "WHATNOW_HINTS", "AUDIO", "ASSETS", "EFFECT_RULES",
                      "LIGHT_SOURCES", "DEATH_NARRATIONS"]:
            assert env.eval(f"type({table})") == "table", f"global table {table} not defined"

    def test_onload_fresh_game(self, env):
        env.globals().onLoad("")
        flush(env)  # runs the delayed refreshPhaseBanner/populateNotebook/audit
        assert env.eval("gameState.subPhase") == "PreGame"

    def test_onload_restores_saved_state(self, env):
        saved = _json.dumps({"day": 3, "doom": 12, "started": True, "subPhase": "Day",
                             "phase": 2, "activeChars": {}, "ongoingDawnEffects": {},
                             "dailyAlerts": {}, "turnOrder": [], "turnIndex": 0,
                             "playerCount": 4, "dayLog": []})
        env.globals().onLoad(saved)
        flush(env)
        assert env.eval("gameState.day") == 3
        assert env.eval("gameState.doom") == 12

    def test_save_load_roundtrip(self, env):
        env.globals().onLoad("")
        env.execute("gameState.day = 5; gameState.doom = 17; gameState.subPhase = 'Night'")
        add_char(env, "White", "James", health=4, sanity=2)
        saved = env.globals().onSave()
        env2 = make_env()
        env2.globals().onLoad(saved)
        assert env2.eval("gameState.day") == 5
        assert env2.eval("gameState.doom") == 17
        assert env2.eval("gameState.activeChars.White.health") == 4
        assert env2.eval("gameState.activeChars.White.sanity") == 2


# ---------------------------------------------------------------------------
# Pure rule helpers
# ---------------------------------------------------------------------------


class TestPhaseAndDoom:
    def test_phase_for_day(self, env):
        expected = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4}
        for day, phase in expected.items():
            assert env.globals().getPhaseForDay(day) == phase, f"day {day}"

    @pytest.mark.parametrize("players,phase,rate", [
        (3, 1, 1), (3, 4, 1),
        (4, 1, 1), (4, 3, 1), (4, 4, 2),
        (5, 2, 1), (5, 3, 2), (5, 4, 2),
    ])
    def test_doom_rate_by_player_count(self, env, players, phase, rate):
        env.execute(f"gameState.playerCount = {players}; gameState.phase = {phase}")
        assert env.globals().getDoomRate() == rate

    def test_doom_rate_clamps_player_count(self, env):
        env.execute("gameState.playerCount = 2; gameState.phase = 1")
        assert env.globals().getDoomRate() == 1  # clamped up to the 3p table

    def test_fester_threats_capped_bosses_uncapped(self, env):
        # Design §15.1: ordinary threats +1 each (max +3); phase bosses +2
        # each and the Treeguard +1, with no cap.
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:JamesHouse"], "position": [0, 1, 0]}))
        for _ in range(4):  # four loose threats — capped at +3
            add(py_to_lua(env, {"tags": ["ThreatCard"], "position": [1, 1, 0]}))
        add(py_to_lua(env, {"tags": ["Boss", "Boss:Deerclops"], "position": [2, 1, 0]}))
        add(py_to_lua(env, {"tags": ["Boss", "Boss:EyeOfTerror"], "position": [0, 1, 2]}))
        add(py_to_lua(env, {"tags": ["Boss", "Boss:Treeguard"], "position": [2, 1, 2]}))
        threat_fester, boss_fester = env.globals().countFesteringThreats()
        assert threat_fester == 3   # 4 threats, capped at +3
        assert boss_fester == 5     # 2 phase bosses x 2 + Treeguard x 1, uncapped

    def test_boss_off_the_map_does_not_fester(self, env):
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:JamesHouse"], "position": [0, 1, 0]}))
        # standee far from every tile (e.g. in the boss pool staging area)
        add(py_to_lua(env, {"tags": ["Boss", "Boss:TheSource"], "position": [90, 1, 90]}))
        threat_fester, boss_fester = env.globals().countFesteringThreats()
        assert (threat_fester, boss_fester) == (0, 0)
        assert env.globals().isBossOnMap("Boss:TheSource") is False


# ---------------------------------------------------------------------------
# Combat (Design §12) — dice are scripted, so outcomes are exact
# ---------------------------------------------------------------------------


class TestScenarios:
    def test_apply_scenario_sets_flags(self, env):
        env.globals().applyScenario("SC_WINTER")
        assert env.eval("gameState.scenario") == "SC_WINTER"
        assert env.eval("gameState.scenarioFlags.hungerDecayX2") is True

    def test_winter_doubles_hunger_decay_at_tick(self, env):
        add_char(env, "Green", "Ellie")
        env.execute("gameState.jamesEnergyDrinkUsed = true")
        env.globals().applyScenario("SC_WINTER")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Green.hunger") == 8  # -2, doubled

    def test_summer_trims_max_hunger(self, env):
        add_char(env, "Green", "Ellie")
        env.globals().applyScenario("SC_SUMMER")
        assert env.eval("gameState.activeChars.Green.maxHunger") == 8
        assert env.eval("gameState.activeChars.Green.hunger") == 8

    def test_unknown_scenario_is_rejected(self, env):
        env.globals().applyScenario("SC_NOPE")
        assert env.eval("gameState.scenario") is None


# ---------------------------------------------------------------------------
# Night light check (night.lua)
# ---------------------------------------------------------------------------


class TestLightCheck:
    def _tile(self, env, loc="JamesHouse", pos=(0, 1, 0)):
        env.eval("TTS.addObject")(py_to_lua(env, {"tags": [f"Location:{loc}"], "position": list(pos)}))

    def test_no_light_when_world_empty(self, env):
        add_char(env, "White", "James")
        assert env.globals().checkPlayerHasLight("White") is False

    def test_flashlight_in_hand_counts(self, env):
        add_char(env, "White", "James")
        self._tile(env)
        env.execute('TTS.setHand("White", { TTS.makeObject({tags={"M_FLASHLIGHT"}}) })')
        assert env.globals().checkPlayerHasLight("White") is True

    def test_flashlight_useless_on_fire_only_night(self, env):
        add_char(env, "White", "James")
        self._tile(env)
        env.execute('TTS.setHand("White", { TTS.makeObject({tags={"M_FLASHLIGHT"}}) })')
        env.execute("gameState.ongoingDawnEffects.flashlightsDisabled = true")
        assert env.globals().checkPlayerHasLight("White") is False

    def test_fire_kit_still_works_on_fire_only_night(self, env):
        add_char(env, "White", "James")
        self._tile(env)
        env.execute('TTS.setHand("White", { TTS.makeObject({tags={"M_FIRE_KIT"}}) })')
        env.execute("gameState.ongoingDawnEffects.flashlightsDisabled = true")
        assert env.globals().checkPlayerHasLight("White") is True

    def test_campfire_at_tile_covers_everyone(self, env):
        add_char(env, "Red", "Coco", location="BasketballCourt")
        self._tile(env, "BasketballCourt", (10, 1, 10))
        env.eval("TTS.addObject")(py_to_lua(env, {"tags": ["M_CAMPFIRE"], "position": [12, 1, 10]}))
        assert env.globals().checkPlayerHasLight("Red") is True

    def test_distant_campfire_does_not_count(self, env):
        add_char(env, "Red", "Coco", location="BasketballCourt")
        self._tile(env, "BasketballCourt", (10, 1, 10))
        env.eval("TTS.addObject")(py_to_lua(env, {"tags": ["M_CAMPFIRE"], "position": [30, 1, 30]}))
        assert env.globals().checkPlayerHasLight("Red") is False

    def test_nickname_fallback_matches_lantern(self, env):
        add_char(env, "White", "James")
        self._tile(env)
        env.execute('TTS.setHand("White", { TTS.makeObject({nickname="Camping Lantern"}) })')
        assert env.globals().checkPlayerHasLight("White") is True


# ---------------------------------------------------------------------------
# In-TTS self-test (lua/selftest.lua) — driven headlessly against a fully
# populated stub world. In TTS it runs from the console: runSelfTest()
# ---------------------------------------------------------------------------


class TestSelfTest:
    def test_runselftest_passes_headlessly(self, env):
        populate_full_world(env)
        env.globals().onLoad("")
        flush(env)
        env.globals().runSelfTest()
        flush(env)
        assert env.eval("SELFTEST.done") is True, "self-test never reached its summary"
        results = lua_to_py(env.eval("SELFTEST.results"))
        results = list(results.values()) if isinstance(results, dict) else list(results)
        failures = [r for r in results if "FAIL" in r]
        assert not failures, "in-TTS self-test steps failed:\n" + "\n".join(failures)
        assert env.eval("SELFTEST.passed") >= 15, (
            f"only {env.eval('SELFTEST.passed')} checks ran — self-test lost steps?")

    def test_runselftest_reports_missing_components(self, env):
        # With an empty table the audit step must FAIL loudly, not crash.
        env.globals().onLoad("")
        flush(env)
        env.globals().runSelfTest()
        flush(env)
        assert env.eval("SELFTEST.done") is True
        assert env.eval("SELFTEST.failed") > 0, (
            "self-test reported success on an empty table — audit step is broken")


# ---------------------------------------------------------------------------
# Dawn effect dispatch — every entry's apply() runs without hard error
# ---------------------------------------------------------------------------


class TestDoomTrackLength:
    """The printed track is the same strip of board at every difficulty; the
    DIFFICULTY decides how many cells it is cut into. So the marker's travel
    must be a fraction of getDoomLimit(), not of a hardcoded 30 — with 30
    baked in, a Long Weekend game ended (Doom 15 = defeat) with the marker
    parked halfway down a track the board labelled up to 30.
    """

    def _x(self, env, step):
        return lua_to_py(env.globals().doomStepWorld(step))["x"]

    def test_standard_marker_spans_the_track_from_0_to_30(self, env):
        env.execute('gameState.difficulty = "standard"')
        assert self._x(env, 0) == pytest.approx(-10.9, abs=0.01)
        assert self._x(env, 30) == pytest.approx(10.9, abs=0.01)

    def test_long_weekend_marker_reaches_the_east_end_at_its_own_limit(self, env):
        env.execute('gameState.difficulty = "weekend"')
        assert env.globals().getDoomLimit() == 15
        assert self._x(env, 0) == pytest.approx(-10.9, abs=0.01)
        assert self._x(env, 15) == pytest.approx(10.9, abs=0.01), (
            "at Doom 15 the Long Weekend is lost, so the marker must be on the "
            "last printed cell — not halfway down the track")
        # ...and the halfway point of the game is the halfway point of the track.
        assert self._x(env, 7.5) == pytest.approx(0.0, abs=0.01)

    def test_overshoot_pins_to_the_last_cell_of_the_active_track(self, env):
        env.execute('gameState.difficulty = "weekend"')
        assert self._x(env, 40) == pytest.approx(self._x(env, 15), abs=0.001)
