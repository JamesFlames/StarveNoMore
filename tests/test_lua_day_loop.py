"""day/night loop: Tick decay, revive, Rotation variant, difficulty, 3-player reliefs.

Headless execution of the real game Lua under Lua 5.2 (lupa) with the TTS
stub. The bundle harness (env fixture, add_char, script_dice, ...) lives in
tests/conftest.py; split out of the former monolithic test_lua_runtime.py.
"""

import pytest
from conftest import (
    ROOT,
    add_char,
    broadcasts,
    flush,
    lua52,
    lua_to_py,
    populate_full_world,
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
        Retuned to ~21% at the 4-player calibration count (§17.2); now ~13%
        after batch 5 raised the 4p Phase 4 base from +2 to +3, which stacks
        with this surcharge for a 4-per-day final act."""
        env.execute('gameState.difficulty = "nightmare"; gameState.playerCount = 4')
        rates = {}
        for phase in (1, 2, 3, 4):
            env.execute(f"gameState.phase = {phase}")
            rates[phase] = env.globals().getDoomRate()
        # 4p base is [1, 1, 1, 3]; the surcharge lands on 3 and 4 only.
        assert rates == {1: 1, 2: 1, 3: 2, 4: 4}, rates

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

    def test_standard_rates_carry_no_surcharge(self, env):
        """Standard's Phase 4 is the §15.6 base (+3 since batch 5) with no
        difficulty delta on top — the surcharge is Nightmare's alone."""
        env.execute("gameState.playerCount = 4; gameState.phase = 4")
        assert env.globals().getDoomRate() == 3


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

    def test_undo_rewinds_the_tile_count_too(self, env):
        """snapshotForUndo captured raymanMovedToday but not the tile COUNT,
        so an undone move kept ticking both 3-player thresholds — the Loud
        relief (< 3 tiles) and the Big Appetite relief (< 2)."""
        self._rayman(env, players=3)
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:EllieLucaHouse"], "position": [0, 1, 0]}))
        env.execute("gameState.activeChars.Yellow.location = 'JamesHouse'")
        env.globals().doMove("Yellow", "EllieLucaHouse")
        assert env.eval("gameState.raymanTilesMovedToday") == 1
        env.globals().doUndo("Yellow")
        assert env.eval("gameState.raymanTilesMovedToday") == 0
        assert not env.eval("gameState.raymanMovedToday")
        # ...so a genuinely quiet day is still quiet at Tick.
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Yellow.hunger") == 9   # -1, relieved

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


def test_spending_an_action_jiggles_the_actors_standee(env):
    """Feedback at the piece: the standee of whoever just acted shakes.

    Hooked into spendAction because every action verb funnels through it, so
    one hook covers Move, Gather, Fight, Craft, Cook, Rest, Trade and the rest
    — and a new verb gets it for free instead of being forgotten."""
    populate_full_world(env)
    add_char(env, "Blue", "James")
    env.execute('gameState.started = true; gameState.subPhase = "Day"; '
                'gameState.activeColor = "Blue"')

    def standee_tilt():
        return lua_to_py(env.eval(
            '(function() local s = getCharacterStandee("James") '
            'if not s then return nil end return s.getRotation().z end)()'))

    assert standee_tilt() == 0, "standee should start upright"
    assert env.globals().spendAction("Blue", "Gather") is True
    flush(env)
    assert standee_tilt() != 0, (
        "spendAction should have shaken James's standee — nothing moved, so "
        "the only feedback an action gives is a line in the message log")


def test_a_refused_action_does_not_jiggle(env):
    """The shake means "that landed". A rejected action must not fake it —
    Down characters, an empty action pool and rotation turns all bounce out of
    spendAction before anything is spent."""
    populate_full_world(env)
    add_char(env, "Blue", "James")
    env.execute('gameState.started = true; gameState.subPhase = "Day"; '
                'gameState.activeColor = "Blue"; '
                'gameState.activeChars.Blue.actionsLeft = 0')

    assert env.globals().spendAction("Blue", "Gather") is False
    flush(env)
    tilt = lua_to_py(env.eval(
        '(function() return getCharacterStandee("James").getRotation().z end)()'))
    assert tilt == 0, "a refused action shook the standee anyway"


def test_trade_does_not_offer_a_partner_you_cannot_pay_for(env):
    """A remote trade costs 1 action. Offering it to a character holding zero
    produced a button that bounced when clicked, which reads as the game
    changing its mind. Unaffordable partners are not listed at all."""
    populate_full_world(env)
    add_char(env, "Blue", "James", location="JamesHouse")
    add_char(env, "Green", "Rayman", location="RaymanHouse")
    env.execute('gameState.started = true; gameState.subPhase = "Day"; '
                'gameState.activeColor = "Blue"; '
                'gameState.activeChars.Blue.actionsLeft = 0')

    env.globals().onActTrade(py_to_lua(env, {"color": "Blue"}), None, "actTrade")
    flush(env)

    shown = lua_to_py(env.eval(
        '(function() return UI.getAttribute("tradeBtn_Green", "active") end)()'))
    assert shown != "true", (
        "Rayman is at another tile (1 action) and James has 0 actions — "
        "that trade cannot happen, so it must not be offered")
    said = " ".join(broadcasts(env))
    assert "afford" in said, (
        "with nothing offerable the player needs the reason, not an empty "
        f"dialog or a bare 'no one to trade with'; got: {said!r}")


def test_trade_still_offers_the_free_same_tile_trade_at_zero_actions(env):
    """The other half of the rule: a trade at your OWN tile is free once a
    turn, so 0 actions must not hide it. Hiding both would be a rules change."""
    populate_full_world(env)
    add_char(env, "Blue", "James", location="JamesHouse")
    add_char(env, "Green", "Rayman", location="JamesHouse")
    env.execute('gameState.started = true; gameState.subPhase = "Day"; '
                'gameState.activeColor = "Blue"; '
                'gameState.activeChars.Blue.actionsLeft = 0')

    env.globals().onActTrade(py_to_lua(env, {"color": "Blue"}), None, "actTrade")
    flush(env)

    shown = lua_to_py(env.eval(
        '(function() return UI.getAttribute("tradeBtn_Green", "active") end)()'))
    assert shown == "true", "the free same-tile trade must survive 0 actions"


def test_dusk_button_names_who_has_not_settled(env):
    """The Ready-for-Night button is a toggle and used to show only a count, so
    a player watching it refuse to reach 2/2 kept clicking — settling and
    un-settling themselves while the other character was never readied."""
    populate_full_world(env)
    add_char(env, "Blue", "James")
    add_char(env, "Green", "Rayman")
    # countDuskReady only counts SEATED colours — the stub seats White by
    # default, so the two players have to actually sit down.
    env.execute('TTS.seated = { "Blue", "Green" }; '
                'gameState.started = true; gameState.subPhase = "Dusk"; '
                'gameState.duskReady = { Blue = true }')

    env.globals().refreshDuskReadyLabel()
    label = lua_to_py(env.eval(
        '(function() return UI.getAttribute("duskReadyBtn", "text") end)()'))
    assert "Rayman" in label, (
        f"the button must name who is still to settle; got {label!r}")
    assert "un-settle" in label, (
        f"...and say that clicking again undoes your own ready; got {label!r}")


def _dusk_table(env):
    """Three seated characters, at Dusk, nobody settled yet."""
    populate_full_world(env)
    add_char(env, "Blue", "James")
    add_char(env, "Green", "Rayman")
    add_char(env, "White", "Coco")
    env.execute('TTS.seated = { "Blue", "Green", "White" }; '
                'gameState.started = true; gameState.subPhase = "Dusk"; '
                'gameState.turnOrder = { "Blue", "Green", "White" }; '
                'gameState.duskReady = {}; gameState.activeColor = "Blue"')


def test_settling_hands_dusk_on_to_the_next_character(env):
    """Settling passes the seat, the way ending a turn does.

    Dusk is a parallel phase by design, and in hotseat that meant one person
    clicking the SAME character's ready button over and over: a real session
    logged "Coco is settled / Coco is up again" five times while the count sat
    at 1/3 and the other two were never asked, because nothing moved the
    driver off Coco's chair.
    """
    _dusk_table(env)

    env.globals().toggleDuskReady("Blue")
    flush(env)
    assert env.eval("gameState.activeColor") == "Green", (
        "settling must hand the seat to the next character still to settle")

    env.globals().toggleDuskReady("Green")
    flush(env)
    assert env.eval("gameState.activeColor") == "White"


def test_settling_skips_characters_who_are_already_settled(env):
    _dusk_table(env)
    env.execute('gameState.duskReady = { Green = true }')
    env.globals().toggleDuskReady("Blue")
    flush(env)
    assert env.eval("gameState.activeColor") == "White", (
        "an already-settled character must not be handed the seat again")


def test_un_settling_takes_the_seat_back(env):
    """Clicking again means "wait, I'm not done" — so the seat returns."""
    _dusk_table(env)
    env.globals().toggleDuskReady("Blue")     # seat moves to Green
    flush(env)
    env.globals().toggleDuskReady("Blue")     # Blue is up again
    flush(env)
    assert env.eval("gameState.activeColor") == "Blue"


def test_the_last_settle_clears_the_seat(env):
    """Night has no active player, and a stale one leaves the banner naming a
    settler and a hand zone glowing all through the night resolution."""
    _dusk_table(env)
    for color in ("Blue", "Green", "White"):
        env.globals().toggleDuskReady(color)
    # No flush: the pending Wait is beginNight, and this assertion is about
    # the seat being cleared before it, not about the night resolving.
    assert env.eval("gameState.activeColor") is None


def test_spectators_are_told_why_nothing_they_click_works(env):
    """TTS refuses a Grey player's clicks with its own "Grey (Spectator) cannot
    interact" message, which reads as a bug because nobody joined AS a
    spectator — Grey is just where TTS puts you until you take a colour. Say it
    in words that connect the refusal to the fix."""
    env.execute('TTS.seated = { "Blue" }; TTS.spectators = { "Grey" }')
    assert env.globals().nudgeSpectatorsToSitDown() == 1
    said = " ".join(broadcasts(env))
    assert "Grey" in said and "Change Color" in said, (
        f"a spectator needs the reason and the fix; got {said!r}")


def test_setup_warns_the_host_that_a_spectator_is_not_in_the_game(env):
    """The pick queue is built from SEATED colours, so a spectator is simply
    absent from it. Without a word to the host, a three-person table silently
    starts a two-player game and nobody can see where the third went."""
    populate_full_world(env)
    env.execute('TTS.seated = { "Blue", "Green" }; TTS.spectators = { "Grey" }')
    env.globals().startGuidedSetup("Blue")
    flush(env)
    said = " ".join(broadcasts(env))
    assert "coloured seat" in said and "not in this game" in said, (
        f"the host was not told a player is missing; got {said!r}")


def test_hotseat_active_seat_follows_the_games_turn(env):
    """In hotseat, the seat a click carries is TTS's current turn, and this mod
    runs its own turns — so the two drift and the player is told "It's Coco's
    turn, and you are sitting in the Blue seat" with no way to act. Point TTS
    at whoever is up instead of asking the human to change colour by hand."""
    populate_full_world(env)
    add_char(env, "White", "Coco")
    env.execute('TTS.seated = { "White", "Blue" }; Turns.enable = true; '
                'Turns.turn_color = "Blue"; '
                'gameState.started = true; gameState.subPhase = "Day"; '
                'gameState.activeColor = "White"')

    env.globals().updateActivePlayerIndicator()
    assert lua_to_py(env.eval("Turns.turn_color")) == "White", (
        "TTS still had the wrong seat active — the hotseat driver has to fix "
        "it by hand, which is the confusion this removes")


def test_multiplayer_turn_system_is_left_alone(env):
    """The scoping rule. TTS's turn system is off in normal multiplayer (each
    player has their own client), and switching it on to drive it would put
    its turn plate back over the phase banner."""
    populate_full_world(env)
    add_char(env, "White", "Coco")
    env.execute('Turns.enable = false; Turns.turn_color = "Blue"; '
                'gameState.started = true; gameState.subPhase = "Day"; '
                'gameState.activeColor = "White"')

    env.globals().updateActivePlayerIndicator()
    assert lua_to_py(env.eval("Turns.turn_color")) == "Blue", (
        "the turn system was disabled and we wrote to it anyway")
    assert lua_to_py(env.eval("Turns.enable")) is False, (
        "TTS's turn system was switched ON — its plate draws over our banner")


def test_the_ready_button_follows_the_dusk_seat(env):
    """One person driving every seat must be able to settle all of them.

    The click used to settle player.color, so in hotseat — where TTS alone
    decides which colour a click carries — it settled the same character over
    and over: a session logged "Coco is settled / Coco is up again" five times
    with the count stuck at 1/3. Passing the seat on in gameState was half the
    fix; the click has to follow it.
    """
    _dusk_table(env)
    p = env.eval('Player["Blue"]')

    env.globals().onDuskReadyClick(p, None, "duskReadyBtn")   # settles Blue
    assert env.eval('gameState.duskReady.Blue') is True
    assert env.eval("gameState.activeColor") == "Green"

    # Blue clicks again. They are already settled, so this answers for the
    # seat that is up — it must not just un-settle Blue.
    env.globals().onDuskReadyClick(p, None, "duskReadyBtn")
    assert env.eval('gameState.duskReady.Green') is True, (
        "the second click did not settle the seat that was up")
    assert env.eval('gameState.duskReady.Blue') is True, "it un-settled the clicker"


def test_an_unsettled_player_still_answers_for_themselves(env):
    """In multiplayer the seat order is a nudge, not a lock: your own click
    settles your own character even when the seat is on someone else."""
    _dusk_table(env)
    env.execute('gameState.activeColor = "Blue"')
    env.globals().onDuskReadyClick(env.eval('Player["White"]'), None, "duskReadyBtn")
    assert env.eval('gameState.duskReady.White') is True
    assert env.eval('gameState.duskReady.Blue') is None


class TestBossLoot:
    """Boss spoils go to the fighters.

    dropBossLoot used to spawn three resource tokens on the ground beside the
    boss's standee and announce "3 resources salvaged". Nobody received them:
    the economy is authoritative in gameState.resources per colour and
    physical tokens are decoration (helpers.lua), so the spoils were props.
    A player asked "who should the wood go to?" — the game had no answer.
    """

    def _held(self, env, color):
        res = lua_to_py(env.eval(f'getPlayerResources("{color}")')) or {}
        return sum(res.values())

    def test_the_killer_is_paid(self, env):
        populate_full_world(env)
        add_char(env, "White", "James", location="BadmintonCourt")
        env.globals().dropBossLoot("deerclops", py_to_lua(env, ["White"]))
        assert self._held(env, "White") == env.eval("BOSS_LOOT_COUNT")

    def test_a_group_kill_splits_the_spoils(self, env):
        populate_full_world(env)
        add_char(env, "White", "James", location="BadmintonCourt")
        add_char(env, "Green", "Rayman", location="BadmintonCourt")
        env.globals().dropBossLoot("deerclops", py_to_lua(env, ["White", "Green"]))
        total = self._held(env, "White") + self._held(env, "Green")
        assert total == env.eval("BOSS_LOOT_COUNT")
        assert self._held(env, "White") >= 1 and self._held(env, "Green") >= 1, (
            "a group kill must pay everyone who fought")

    def test_the_broadcast_names_who_got_what(self, env):
        populate_full_world(env)
        add_char(env, "White", "James", location="BadmintonCourt")
        env.globals().dropBossLoot("deerclops", py_to_lua(env, ["White"]))
        said = " ".join(broadcasts(env))
        assert "James:" in said, said

    def test_a_down_fighter_is_skipped(self, env):
        populate_full_world(env)
        add_char(env, "White", "James", location="BadmintonCourt", down=True)
        add_char(env, "Green", "Rayman", location="BadmintonCourt")
        env.globals().dropBossLoot("deerclops", py_to_lua(env, ["White", "Green"]))
        assert self._held(env, "White") == 0, "a Down character cannot pick anything up"
        assert self._held(env, "Green") == env.eval("BOSS_LOOT_COUNT")

    def test_no_fighters_falls_back_to_whoever_is_standing(self, env):
        """A boss can be finished by something other than a fight — a
        Signature, a Dawn effect — and the loot still has to land."""
        populate_full_world(env)
        add_char(env, "Green", "Rayman", location="BadmintonCourt")
        env.globals().dropBossLoot("deerclops", None)
        assert self._held(env, "Green") == env.eval("BOSS_LOOT_COUNT")


class TestStandeePosture:
    """A Down character lies on the table.

    "X is DOWN" was a line of chat and nothing on the table changed, so a
    fallen character looked exactly like a standing one.
    """

    def _pitch(self, env, name):
        return env.eval(
            f'(function() local s = getCharacterStandee("{name}")'
            f' return s and s.getRotation().x or -1 end)()')

    def test_going_down_lays_the_standee_over(self, env):
        populate_full_world(env)
        add_char(env, "White", "James", health=0)
        add_char(env, "Green", "Rayman")   # someone still up, so it's not defeat
        assert self._pitch(env, "James") == 0
        env.globals().checkDownState("White")
        assert env.eval("gameState.activeChars.White.down") is True
        assert self._pitch(env, "James") == env.eval("STANDEE_DOWN_PITCH")

    def test_reviving_stands_it_back_up(self, env):
        populate_full_world(env)
        add_char(env, "White", "James", location="RaymanHouse", health=0)
        add_char(env, "Green", "Rayman", location="RaymanHouse")
        env.globals().checkDownState("White")
        env.execute("gameState.heartCount = 1")
        assert env.globals().reviveCharacter("Green", "White") is True
        assert self._pitch(env, "James") == 0, "the revived standee is still lying down"

    def test_a_standing_character_is_left_alone(self, env):
        populate_full_world(env)
        add_char(env, "White", "James")
        env.globals().checkDownState("White")
        assert self._pitch(env, "James") == 0

    def test_nobody_is_told_to_flip_to_a_ghost_side(self, env):
        """There ISN'T one. Each standee's back is a rear view of the LIVING
        character — James from behind, Coco from behind with her halo and
        wings intact — so "flip the standee to its ghost side" pointed at art
        nobody had drawn. Following it showed a character standing with their
        back turned, which reads as facing away, not fallen."""
        populate_full_world(env)
        add_char(env, "White", "James", health=0)
        add_char(env, "Green", "Rayman")
        env.globals().checkDownState("White")
        said = " ".join(broadcasts(env)).lower()
        assert "ghost side" not in said, (
            "the game is still asking for a flip that cannot be performed")
        assert "is down" in said


class TestFestering:
    """Doom from messes left on the map — the game's main responsive pressure.

    It was silently switched off, and in the way that hurt most: threats drawn
    to the same tile on successive nights MERGE into a TTS Deck, and the scan
    only counted objects whose `type` was "Card". So festering stopped exactly
    when the mess got big enough to stack — a team that turtled at home drew
    threats onto the same three tiles every night and, from night two, paid
    nothing for any of them.

    A real Nightmare game finished at Doom 11 of 30: the fixed clock (10) plus
    one Down (1), and not one point of festering across seven days.
    """

    def _board(self, env):
        import os
        import sys
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import path_layouts as pl
        populate_full_world(env)
        for loc, (wx, wz) in pl.LOCATION_WORLD.items():
            env.execute(f'(function() local t = getLocationTile("{loc}") '
                        f'if t then t.setPosition({{x={wx}, y=1.57, z={wz}}}) end end)()')
        return pl

    def _threat(self, env, pos, type_="Card", count=1, tags=("ThreatCard",)):
        spec = {"tags": list(tags), "type": type_, "position": list(pos)}
        if type_ == "Deck":
            spec["contained"] = [{"nickname": f"T{i}"} for i in range(count)]
        env.eval("TTS.addObject")(py_to_lua(env, spec))

    def test_loose_cards_fester(self, env):
        pl = self._board(env)
        for loc in ("RaymanHouse", "EllieLucaHouse"):
            wx, wz = pl.LOCATION_WORLD[loc]
            self._threat(env, [wx, 1.61, wz + 0.3])
        threats, bosses = env.eval("countFesteringThreats")()
        assert (threats, bosses) == (2, 0)

    def test_a_merged_stack_festers_per_card(self, env):
        """The whole bug: three threats on one tile is three threats."""
        pl = self._board(env)
        wx, wz = pl.LOCATION_WORLD["BadmintonCourt"]
        self._threat(env, [wx, 1.63, wz + 0.6], type_="Deck", count=3)
        threats, _ = env.eval("countFesteringThreats")()
        assert threats == 3, (
            f"a merged pile of 3 threats festered as {threats} — stacking must "
            "not make a mess free")

    def test_the_draw_pile_never_festers(self, env):
        """The under-table library sits DIRECTLY beneath the board: the Threat
        draw pile is 1.1 units from James's House in x/z, and the radius test
        is x/z only. Counting decks without a height test would have turned the
        46-card draw pile into a permanent maximum-festering source."""
        pl = self._board(env)
        wx, wz = pl.LOCATION_WORLD["JamesHouse"]
        self._threat(env, [wx - 1.0, -3.06, wz - 0.2], type_="Deck", count=46,
                     tags=("ThreatCard", "ThreatCardDeck"))
        threats, bosses = env.eval("countFesteringThreats")()
        assert (threats, bosses) == (0, 0), (
            f"the draw pile festered ({threats}) — it is under the table")

    def test_the_cap_still_holds(self, env):
        pl = self._board(env)
        wx, wz = pl.LOCATION_WORLD["BadmintonCourt"]
        self._threat(env, [wx, 1.63, wz + 0.6], type_="Deck", count=9)
        threats, _ = env.eval("countFesteringThreats")()
        assert threats == 3, f"ordinary threats cap at 3 per Dawn; got {threats}"
