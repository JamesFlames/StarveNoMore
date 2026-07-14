"""session telemetry: the chronicle and Copy-Session-Log export.

Headless execution of the real game Lua under Lua 5.2 (lupa) with the TTS
stub. The bundle harness (env fixture, add_char, script_dice, ...) lives in
tests/conftest.py; split out of the former monolithic test_lua_runtime.py.
"""
import json as _json

import pytest

from conftest import (
    lua52, make_env, add_char, broadcasts, lua_to_py, py_to_lua,
    script_dice,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


class TestChronicle:
    def test_kills_and_meals_accumulate(self, env):
        add_char(env, "White", "James")
        env.globals().recordKillInChronicle("Shadow Stalker", py_to_lua(env, ["White"]))
        env.globals().recordMealInChronicle("Ellie")
        env.globals().recordMealInChronicle("Ellie")
        assert env.eval("#gameState.chronicle.kills") == 1
        assert env.eval("gameState.chronicle.meals.Ellie") == 2

    def test_day_record_survives_daylog_wipe(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.day = 3; gameState.doom = 14")
        env.globals().broadcastEvent("damage", "James is DOWN. Flip standee to ghost side.")
        env.globals().recordDayInChronicle()
        env.execute("gameState.dayLog = {}")   # the Dawn wipe
        assert env.eval("gameState.chronicle.days[3].damageTonight") == 1
        assert env.eval("gameState.chronicle.peakDoom.value") == 14
        assert "DOWN" in env.eval("gameState.chronicle.days[3].headline")

    def test_down_and_revive_counters(self, env):
        add_char(env, "White", "James")
        add_char(env, "Green", "Ellie")
        env.execute("gameState.activeChars.White.health = 0")
        env.globals().checkDownState("White")
        assert env.eval("gameState.chronicle.downs") == 1
        env.execute("gameState.activeChars.Green.location = gameState.activeChars.White.location")
        env.globals().reviveCharacter("Green", "White")
        assert env.eval("gameState.chronicle.revives") == 1

    def test_week_in_review_shows_on_victory(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.day = 7; gameState.doom = 20; gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        assert any("WEEK IN REVIEW" in m for m in broadcasts(env))

    def test_chronicle_survives_save_load(self, env):
        env.globals().recordMealInChronicle("Ellie")
        saved = env.globals().onSave()
        env.globals().onLoad(saved)
        assert env.eval("gameState.chronicle.meals.Ellie") == 1


# ---------------------------------------------------------------------------
# Nothing Left to Lose — the Doom-25 buff (design_batch2.md §1)
# ---------------------------------------------------------------------------


class TestTelemetry:
    def test_session_log_round_trips_through_json(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.day = 5; gameState.doom = 18; gameState.gameOverCause = 'victory'")
        log = _json.loads(env.globals().exportSessionLog())
        assert log["schema"] == 1
        assert log["outcome"]["cause"] == "victory"
        assert log["outcome"]["day"] == 5
        assert log["outcome"]["doom"] == 18
        names = [c["name"] for c in log["finalCharacters"]]
        assert names == ["James"]

    def test_setup_facts_recorded(self, env):
        add_char(env, "White", "James")
        add_char(env, "Green", "Ellie")
        env.execute("""
            gameState.playerCount = 2
            gameState.turnOrder = {"White", "Green"}
            gameState.turnStyle = "rotate"
            gameState.pathVariant = "Compact"
            gameState.difficulty = "nightmare"
        """)
        env.globals().recordSetupInChronicle()
        setup = _json.loads(env.globals().exportSessionLog())["setup"]
        assert setup["playerCount"] == 2
        assert setup["roster"] == ["James", "Ellie"]
        assert setup["turnStyle"] == "rotate"
        assert setup["difficulty"] == "nightmare"

    def test_turn_durations_accumulate(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.day = 2")
        env.globals().markTurnStart()
        env.execute("gameState.turnStartedAt = gameState.turnStartedAt - 7")  # 7s ago
        env.globals().recordTurnEnd("White")
        turns = lua_to_py(env.eval("gameState.chronicle.turns"))
        assert len(turns) == 1
        assert turns[0]["name"] == "James"
        assert turns[0]["day"] == 2
        assert turns[0]["seconds"] >= 7
        # a second end without a start records nothing
        env.globals().recordTurnEnd("White")
        assert env.eval("#gameState.chronicle.turns") == 1

    def test_beats_record_signature_and_press_kill(self, env):
        add_char(env, "White", "James")
        env.globals().doSignature("White")                    # All-Nighter fires
        script_dice(env, [5, 6])                              # hit; press kills
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "T", "hp": 2, "attack": 0}))
        env.globals().pressAttack("White", False)
        beats = _json.loads(env.globals().exportSessionLog())["beats"]
        assert beats["pressKills"] == 1
        assert beats["signaturesUsed"] == ["James"]

    def test_telemetry_survives_save_load(self, env):
        add_char(env, "White", "James")
        env.globals().recordBeat("dare")
        saved = env.globals().onSave()
        env2 = make_env()
        env2.globals().onLoad(saved)
        assert env2.eval("gameState.chronicle.beats.daresTaken") == 1


# ---------------------------------------------------------------------------
# Difficulty modes (Design §17.2, design_batch4.md W3)
# ---------------------------------------------------------------------------
