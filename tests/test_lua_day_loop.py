"""day/night loop: Tick decay, revive, Rotation variant, difficulty, 3-player reliefs.

Headless execution of the real game Lua under Lua 5.2 (lupa) with the TTS
stub. The bundle harness (env fixture, add_char, script_dice, ...) lives in
tests/conftest.py; split out of the former monolithic test_lua_runtime.py.
"""

import pytest
from conftest import (
    add_char,
    broadcasts,
    lua52,
    py_to_lua,
    script_dice,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


class TestTick:
    def test_base_decay_and_day_advance(self, env):
        add_char(env, "Green", "Ellie")
        env.execute("gameState.day = 2; gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Green.hunger") == 9   # -1
        assert env.eval("gameState.activeChars.Green.sanity") == 7   # -1
        assert env.eval("gameState.day") == 3
        assert env.eval("gameState.subPhase") == "PreDawn"

    def test_rayman_big_appetite(self, env):
        add_char(env, "Yellow", "Rayman")
        env.execute("gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Yellow.hunger") == 8  # -2

    def test_james_wired_penalty(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.jamesEnergyDrinkUsed = false")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.White.sanity") == 7   # -1 tick, -2 Wired

    def test_starvation_damage_at_zero_hunger(self, env):
        add_char(env, "Green", "Ellie", hunger=1)
        env.execute("gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Green.hunger") == 0
        assert env.eval("gameState.activeChars.Green.health") == 7   # starving

    def test_down_at_zero_health_feeds_doom(self, env):
        add_char(env, "Green", "Ellie", health=1, hunger=1)
        add_char(env, "White", "James")  # second survivor so it's not a full defeat
        env.execute("gameState.jamesEnergyDrinkUsed = true; gameState.doom = 5")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Green.down") is True
        assert env.eval("gameState.doom") == 6  # a fallen friend feeds the dark

    def test_victory_on_day_7_tick(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.day = 7; gameState.doom = 20; gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        assert env.eval("gameState.subPhase") == "GameOver"
        assert any("VICTORY" in m for m in broadcasts(env))

    def test_day7_defeat_if_source_still_stands(self, env):
        # Design §16.3(3): the Source is mandatory — surviving around it is a loss.
        add_char(env, "White", "James")
        env.execute("gameState.day = 7; gameState.doom = 20; gameState.jamesEnergyDrinkUsed = true")
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:EllieLucaHouse"], "position": [0, 1, 0]}))
        add(py_to_lua(env, {"tags": ["Boss", "Boss:TheSource"], "position": [1, 1, 1]}))
        env.globals().resolveTick()
        assert env.eval("gameState.subPhase") == "GameOver"
        assert env.eval("gameState.gameOverCause") == "defeat_source"
        assert any("SOURCE STILL STANDS" in m for m in broadcasts(env))

    def test_day7_victory_once_source_marked_defeated(self, env):
        # markBossDefeated (combat.lua) overrides the standee check — a killed
        # Source left standing on the table doesn't block the win.
        add_char(env, "White", "James")
        env.execute("gameState.day = 7; gameState.doom = 20; gameState.jamesEnergyDrinkUsed = true")
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:EllieLucaHouse"], "position": [0, 1, 0]}))
        add(py_to_lua(env, {"tags": ["Boss", "Boss:TheSource"], "position": [1, 1, 1]}))
        env.globals().markBossDefeated("The Source")
        env.globals().resolveTick()
        assert env.eval("gameState.subPhase") == "GameOver"
        assert env.eval("gameState.gameOverCause") == "victory"

    def test_defeat_at_doom_30(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.doom = 30")
        assert env.globals().checkDefeat() is True
        assert env.eval("gameState.subPhase") == "GameOver"

    def test_defeat_when_all_down(self, env):
        add_char(env, "White", "James", down=True)
        add_char(env, "Green", "Ellie", down=True)
        assert env.globals().checkDefeat() is True

    def test_no_defeat_while_someone_stands(self, env):
        add_char(env, "White", "James", down=True)
        add_char(env, "Green", "Ellie")
        env.execute("gameState.doom = 29")
        assert env.globals().checkDefeat() is False


class TestRevive:
    def test_revive_costs_and_half_stats(self, env):
        add_char(env, "White", "James", location="RaymanHouse")
        add_char(env, "Yellow", "Rayman", down=True, health=0, location="RaymanHouse")
        env.execute("gameState.heartCount = 1")
        ok = env.globals().reviveCharacter("White", "Yellow")
        assert ok is True
        assert env.eval("gameState.activeChars.White.health") == 6         # paid 2
        assert env.eval("gameState.activeChars.Yellow.down") is False
        assert env.eval("gameState.activeChars.Yellow.health") == 6        # ceil(12/2)
        assert env.eval("gameState.activeChars.Yellow.hunger") == 5        # ceil(10/2)
        assert env.eval("gameState.activeChars.Yellow.sanity") == 3        # ceil(6/2)
        assert env.eval("gameState.heartCount") == 0, "the Heart is consumed"

    def test_revive_requires_same_location(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        add_char(env, "Yellow", "Rayman", down=True, location="RaymanHouse")
        env.execute("gameState.heartCount = 1")
        assert env.globals().reviveCharacter("White", "Yellow") is False
        assert env.eval("gameState.activeChars.Yellow.down") is True
        assert env.eval("gameState.heartCount") == 1, "a refused revive keeps the Heart"

    def test_revive_without_a_heart_is_refused(self, env):
        """heartCount clamps at 0, so before this check an empty supply
        revived for free and the counter simply stayed at zero."""
        add_char(env, "White", "James", location="RaymanHouse")
        add_char(env, "Yellow", "Rayman", down=True, health=0, location="RaymanHouse")
        env.execute("gameState.heartCount = 0")
        assert env.globals().reviveCharacter("White", "Yellow") is False
        assert env.eval("gameState.activeChars.Yellow.down") is True
        assert env.eval("gameState.activeChars.White.health") == 8, "and costs nothing"


# ---------------------------------------------------------------------------
# Day turn structure: Rotation variant (day_loop.lua, Design §11.2)
# ---------------------------------------------------------------------------


class TestRotationVariant:
    def _two_player_day(self, env):
        add_char(env, "White", "James")
        add_char(env, "Green", "Ellie")
        env.execute("""
            gameState.turnOrder = {"White", "Green"}
            gameState.turnStyle = "rotate"
            gameState.subPhase = "Day"
            gameState.turnIndex = 1
            gameState.activeColor = "White"
            gameState.actedThisVisit = false
        """)

    def test_one_action_per_visit(self, env):
        self._two_player_day(env)
        assert env.globals().spendAction("White", "Rest") is True
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2
        # second action in the same visit is refused; nothing is spent
        assert env.globals().spendAction("White", "Rest") is False
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2

    def test_pass_after_acting_banks_actions_and_wraps(self, env):
        self._two_player_day(env)
        env.globals().spendAction("White", "Rest")
        env.globals().endPlayerTurn("White")
        # White banked 2 actions; priority moved to Green
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2
        assert env.eval("gameState.activeColor") == "Green"
        env.globals().spendAction("Green", "Rest")
        env.globals().endPlayerTurn("Green")
        # wraps back to White, who still holds the banked actions
        assert env.eval("gameState.activeColor") == "White"
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2

    def test_pass_without_acting_forfeits(self, env):
        self._two_player_day(env)
        env.globals().endPlayerTurn("White")
        assert env.eval("gameState.activeChars.White.actionsLeft") == 0
        assert env.eval("gameState.activeColor") == "Green"

    def test_undo_reopens_the_visit(self, env):
        self._two_player_day(env)
        env.globals().spendAction("White", "Rest")
        env.globals().doUndo("White")
        # the undone action no longer counts as this visit's one action
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3
        assert env.globals().spendAction("White", "Gather") is True

    def test_full_mode_multiple_actions_per_turn(self, env):
        add_char(env, "White", "James")
        env.execute("""
            gameState.turnOrder = {"White"}
            gameState.turnStyle = "full"
            gameState.subPhase = "Day"
            gameState.turnIndex = 1
            gameState.activeColor = "White"
        """)
        assert env.globals().spendAction("White", "Rest") is True
        assert env.globals().spendAction("White", "Rest") is True
        assert env.eval("gameState.activeChars.White.actionsLeft") == 1


# ---------------------------------------------------------------------------
# Scenarios (setup.lua, Design §17.3)
# ---------------------------------------------------------------------------


class TestDifficulty:
    def test_standard_is_the_default(self, env):
        assert env.globals().getTotalDays() == 7
        assert env.globals().getDoomLimit() == 30
        assert env.globals().getPhaseForDay(1) == 1
        assert env.globals().getPhaseForDay(7) == 4

    def test_weekend_three_days_half_track(self, env):
        env.execute('gameState.difficulty = "weekend"')
        assert env.globals().getTotalDays() == 3
        assert env.globals().getDoomLimit() == 15
        # Phase 1 + half of Phase 2
        assert [env.globals().getPhaseForDay(d) for d in (1, 2, 3)] == [1, 1, 2]

    def test_weekend_defeat_at_15(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.difficulty = "weekend"; gameState.doom = 15')
        assert env.globals().checkDefeat() is True
        assert env.eval("gameState.gameOverCause") == "defeat_doom"

    def test_weekend_victory_on_day_3_tick(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.difficulty = "weekend"; gameState.day = 3; '
                    'gameState.doom = 8; gameState.jamesEnergyDrinkUsed = true')
        env.globals().resolveTick()
        assert env.eval("gameState.gameOverCause") == "victory"

    def test_weekend_day3_gets_the_last_dawn(self, env):
        env.execute('gameState.difficulty = "weekend"; gameState.day = 3; gameState.phase = 2')
        env.globals().revealDawnCard()
        assert env.eval("gameState.activeDawn.id") == "LAST_DAWN"

    def test_nightmare_skips_phase_one(self, env):
        env.execute('gameState.difficulty = "nightmare"; gameState.playerCount = 4')
        assert env.globals().getTotalDays() == 7
        assert [env.globals().getPhaseForDay(d) for d in (1, 2, 3, 5, 7)] == [2, 2, 2, 3, 4]

    def test_nightmare_loads_its_doom_surcharge_onto_the_back_half(self, env):
        """A FLAT +1 measured at 0-6% for the best lines — unwinnable, not hard,
        because it compounds from Day 1 against an already-responsive clock.
        Phases 3-4 only keeps the exploratory half tense and makes the climax
        the part that kills you, which is where §14's arc wants the pressure.
        Retuned to ~21% at the 4-player calibration count (§17.2)."""
        env.execute('gameState.difficulty = "nightmare"; gameState.playerCount = 4')
        rates = {}
        for phase in (1, 2, 3, 4):
            env.execute(f"gameState.phase = {phase}")
            rates[phase] = env.globals().getDoomRate()
        # 4p base is [1, 1, 1, 2]; the surcharge lands on 3 and 4 only.
        assert rates == {1: 1, 2: 1, 3: 2, 4: 3}, rates

    def test_nightmare_source_is_tougher_than_standard(self, env):
        env.execute('gameState.difficulty = "nightmare"')
        nm = env.globals().getSourceMaxHP()
        env.execute('gameState.difficulty = "standard"')
        std = env.globals().getSourceMaxHP()
        env.execute('gameState.difficulty = "story"')
        story = env.globals().getSourceMaxHP()
        assert story < std < nm, (story, std, nm)

    def test_a_per_phase_doom_delta_is_describable_without_crashing(self, env):
        """doomDelta is a number for three modes and a table for Nightmare.
        Every caller that assumed 'number' was a latent crash — the setup
        announcement did `(diff.doomDelta or 0) > 0`, which throws 'attempt to
        compare table with number' the moment the surcharge went per-phase."""
        for mode in ("story", "standard", "nightmare", "weekend"):
            env.execute(f'gameState.difficulty = "{mode}"')
            text = env.globals().describeDoomDelta(env.eval("getDifficulty()"))
            assert isinstance(text, str)
        env.execute('gameState.difficulty = "nightmare"')
        text = env.globals().describeDoomDelta(env.eval("getDifficulty()"))
        assert "Phase 3" in text and "Phase 4" in text, text
        assert "Phase 1" not in text, text

    def test_standard_rates_unchanged(self, env):
        env.execute("gameState.playerCount = 4; gameState.phase = 4")
        assert env.globals().getDoomRate() == 2


# ---------------------------------------------------------------------------
# 3-player composition reliefs (design_batch4.md W2, §20.1)
# ---------------------------------------------------------------------------


class TestThreePlayerReliefs:
    def _rayman(self, env, players=3):
        add_char(env, "Yellow", "Rayman")
        env.execute(f"gameState.playerCount = {players}; gameState.jamesEnergyDrinkUsed = true")

    def test_quiet_day_eases_big_appetite_at_3p(self, env):
        self._rayman(env, players=3)
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Yellow.hunger") == 9   # -1, relieved

    def test_fighting_day_costs_full_appetite_at_3p(self, env):
        self._rayman(env, players=3)
        env.execute("gameState.raymanFoughtToday = true")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Yellow.hunger") == 8   # -2

    def test_two_tiles_moved_costs_full_appetite_at_3p(self, env):
        self._rayman(env, players=3)
        env.execute("gameState.raymanTilesMovedToday = 2")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Yellow.hunger") == 8   # -2

    def test_no_relief_at_four_players(self, env):
        self._rayman(env, players=4)
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Yellow.hunger") == 8   # -2 as always

    def test_loud_needs_three_tiles_at_3p(self, env):
        self._rayman(env, players=3)
        env.execute("gameState.raymanMovedToday = true; gameState.raymanTilesMovedToday = 2")
        assert env.globals().raymanLoudTonight() is False
        env.execute("gameState.raymanTilesMovedToday = 3")
        assert env.globals().raymanLoudTonight() is True

    def test_loud_fires_on_any_move_at_4p(self, env):
        self._rayman(env, players=4)
        env.execute("gameState.raymanMovedToday = true; gameState.raymanTilesMovedToday = 1")
        assert env.globals().raymanLoudTonight() is True

    def test_combat_marks_rayman_fought(self, env):
        self._rayman(env, players=3)
        script_dice(env, [3, 3])   # two dice, whiff, no counter
        env.globals().resolveCombat("Yellow", py_to_lua(env, {"name": "T", "hp": 3, "attack": 0}))
        assert env.eval("gameState.raymanFoughtToday") is True


# ---------------------------------------------------------------------------
# Charlie (Design §15.4)
# ---------------------------------------------------------------------------
