"""The ongoing Dawn-card rules, executed rather than merely announced.

`test_lua_effect_flags.py` proves each announced effect has *a* reader. This
module proves the reader does what the card says, by running the real bundle:
the effect is set, the action is taken, and the number moves.

Every case here was a live rule the game printed to the table and then did
not apply (2026-07 audit) — so each test is the shape of the bug as much as
the shape of the fix.
"""

import pytest
from conftest import (
    add_char,
    broadcasts,
    lua52,
    py_to_lua,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


def set_effect(env, name, value="true"):
    env.execute("gameState.ongoingDawnEffects.%s = %s" % (name, value))


def tile(env, loc, pos=(0, 1, 0)):
    """A location tile the Move/light code can find by tag."""
    env.eval("TTS.addObject")(py_to_lua(env, {
        "tags": ["Location:" + loc, "LocationTile"], "position": list(pos),
    }))


class TestRestRestrictions:
    def test_rest_no_health_suspends_the_home_heal(self, env):
        add_char(env, "White", "James", health=4, location="JamesHouse")
        set_effect(env, "restNoHealth")
        env.globals().doRest("White", "sanity")
        assert env.eval("gameState.activeChars.White.health") == 4
        assert any("no Health" in m for m in broadcasts(env))

    def test_rest_no_health_leaves_the_sanity_half_alone(self, env):
        add_char(env, "White", "James", sanity=4, location="JamesHouse")
        set_effect(env, "restNoHealth")
        env.globals().doRest("White", "sanity")
        assert env.eval("gameState.activeChars.White.sanity") == 6  # +2

    def test_luca_alone_is_not_redirected_past_rest_no_hunger(self, env):
        """The redirect bug: Needs an Audience sent Luca sanity -> hunger
        without re-checking the Dawn card that had just banned Hunger, so
        P2_HUNGRY handed him the exact restoration it forbade."""
        add_char(env, "Blue", "Luca", hunger=4, sanity=4)
        set_effect(env, "restNoHunger")
        env.globals().doRest("Blue", "sanity")
        assert env.eval("gameState.activeChars.Blue.hunger") == 4
        assert env.eval("gameState.activeChars.Blue.sanity") == 4
        assert any("rests for nothing" in m for m in broadcasts(env))

    def test_luca_with_company_still_rests_for_sanity(self, env):
        add_char(env, "Blue", "Luca", sanity=4)
        add_char(env, "Green", "Ellie")  # same tile: he has an audience
        set_effect(env, "restNoHunger")
        env.globals().doRest("Blue", "sanity")
        assert env.eval("gameState.activeChars.Blue.sanity") == 6


class TestMoveCosts:
    def test_move_cost_plus_1_charges_a_second_action(self, env):
        add_char(env, "Green", "Ellie", location="JamesHouse", actionsLeft=3)
        tile(env, "EllieLucaHouse")
        set_effect(env, "moveCostPlus1")
        env.globals().doMove("Green", "EllieLucaHouse")
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 1  # 3 - 1 - 1
        assert env.eval("gameState.activeChars.Green.location") == "EllieLucaHouse"

    def test_move_cost_plus_1_refuses_and_refunds_the_last_action(self, env):
        add_char(env, "Green", "Ellie", location="JamesHouse", actionsLeft=1)
        tile(env, "EllieLucaHouse")
        set_effect(env, "moveCostPlus1")
        env.globals().doMove("Green", "EllieLucaHouse")
        assert env.eval("gameState.activeChars.Green.location") == "JamesHouse"
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 1  # refunded

    def test_sport_court_surcharge_applies_to_arrival(self, env):
        add_char(env, "Green", "Ellie", location="JamesHouse", hunger=10)
        tile(env, "BasketballCourt")
        set_effect(env, "sportCourtHungerCost")
        env.globals().doMove("Green", "BasketballCourt")
        assert env.eval("gameState.activeChars.Green.hunger") == 8  # 1 base + 1

    def test_sport_court_surcharge_applies_to_departure(self, env):
        add_char(env, "Green", "Ellie", location="BadmintonCourt", hunger=10)
        tile(env, "EllieLucaHouse")
        set_effect(env, "sportCourtHungerCost")
        env.globals().doMove("Green", "EllieLucaHouse")
        assert env.eval("gameState.activeChars.Green.hunger") == 8

    def test_sport_court_surcharge_spares_house_to_house(self, env):
        add_char(env, "Green", "Ellie", location="JamesHouse", hunger=10)
        tile(env, "EllieLucaHouse")
        set_effect(env, "sportCourtHungerCost")
        env.globals().doMove("Green", "EllieLucaHouse")
        assert env.eval("gameState.activeChars.Green.hunger") == 9

    def test_dusk_scramble_pays_the_surcharge_too(self, env):
        add_char(env, "Green", "Ellie", location="EllieLucaHouse", hunger=10)
        tile(env, "BadmintonCourt")
        env.execute("gameState.subPhase = 'Dusk'")
        set_effect(env, "sportCourtHungerCost")
        env.globals().doDuskMove("Green", "BadmintonCourt")
        assert env.eval("gameState.activeChars.Green.hunger") == 8


class TestReducedActions:
    def test_long_night_gives_two_actions(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.turnOrder = {'White'}")
        set_effect(env, "reducedActions")
        env.globals().beginDayPhase()
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2

    def test_an_ordinary_day_still_gives_three(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.turnOrder = {'White'}")
        env.globals().beginDayPhase()
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3


class TestDeerclopsDrain:
    """simulate_balance.py has doubled the Tick Sanity loss while the Deerclops
    stands since the baseline was measured. The Lua never did — the boss
    arrived, announced that Sanity costs were doubled, and cost nothing. The
    order matters as much as the rule: doubled AFTER the Doom-20 surcharge and
    BEFORE Coco's relief, which is the order the sim uses."""

    def _tick(self, env):
        env.execute("gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()

    def test_the_night_takes_twice_as_much(self, env):
        add_char(env, "White", "James", sanity=8)
        set_effect(env, "deerclopsActive")
        self._tick(env)
        assert env.eval("gameState.activeChars.White.sanity") == 6   # -1 x2

    def test_an_ordinary_night_is_unchanged(self, env):
        add_char(env, "White", "James", sanity=8)
        self._tick(env)
        assert env.eval("gameState.activeChars.White.sanity") == 7   # -1

    def test_it_doubles_the_doom_surcharge_too(self, env):
        add_char(env, "White", "James", sanity=8)
        set_effect(env, "deerclopsActive")
        set_effect(env, "doom20")
        self._tick(env)
        assert env.eval("gameState.activeChars.White.sanity") == 4   # (1+1) x2

    def test_coco_softens_the_doubled_loss_after_doubling(self, env):
        add_char(env, "Red", "Coco", location="JamesHouse")
        add_char(env, "White", "James", sanity=8, location="JamesHouse")
        set_effect(env, "deerclopsActive")
        self._tick(env)
        # 1 -> x2 = 2 -> Coco -1 = 1, not (1-1) x2 = 0
        assert env.eval("gameState.activeChars.White.sanity") == 7

    def test_killing_it_stops_the_drain_the_same_night(self, env):
        add_char(env, "White", "James", sanity=8)
        set_effect(env, "deerclopsActive")
        env.globals().markBossDefeated("Deerclops")
        assert env.eval("gameState.ongoingDawnEffects.deerclopsActive") is None
        self._tick(env)
        assert env.eval("gameState.activeChars.White.sanity") == 7   # back to -1


class TestMissingAlly:
    def test_the_lightest_traveller_vanishes_and_comes_back_running(self, env):
        add_char(env, "White", "James")
        add_char(env, "Yellow", "Rayman")
        env.execute('TTS.setHand("White", { TTS.makeObject({}), TTS.makeObject({}) })')
        env.execute('gameState.turnOrder = {"White", "Yellow"}')

        env.eval("DAWN_EFFECTS.P3_ALLY_MISSING.onReveal")(None)
        assert env.eval("gameState.missingAlly") == "Yellow"   # carrying nothing

        env.globals().beginDayPhase()
        assert env.eval("gameState.activeChars.Yellow.actionsLeft") == 4
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3

    def test_it_stacks_with_a_shortened_day(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.turnOrder = {"White"}')
        env.eval("DAWN_EFFECTS.P3_ALLY_MISSING.onReveal")(None)
        set_effect(env, "reducedActions")
        env.globals().beginDayPhase()
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3   # 2 + 1

    def test_cleanup_hands_the_adrenaline_back(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.turnOrder = {"White"}')
        env.eval("DAWN_EFFECTS.P3_ALLY_MISSING.onReveal")(None)
        env.eval("DAWN_EFFECTS.P3_ALLY_MISSING.onCleanup")()
        assert env.eval("gameState.missingAlly") is None
        env.globals().beginDayPhase()
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3


class TestRain:
    def test_gather_in_the_rain_costs_sanity_at_a_court(self, env):
        add_char(env, "Green", "Ellie", location="BasketballCourt", sanity=8)
        set_effect(env, "rainSanityCost")
        env.globals().doGather("Green")
        assert env.eval("gameState.activeChars.Green.sanity") == 7

    def test_gather_in_the_rain_is_free_indoors(self, env):
        add_char(env, "Green", "Ellie", location="RaymanHouse", sanity=8)
        set_effect(env, "rainSanityCost")
        env.globals().doGather("Green")
        assert env.eval("gameState.activeChars.Green.sanity") == 8

    def test_rain_drowns_a_lantern_at_a_court(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        tile(env, "BasketballCourt")
        env.execute('TTS.setHand("White", { TTS.makeObject({tags={"M_LANTERN"}}) })')
        set_effect(env, "rainFireDisabled")
        assert env.globals().checkPlayerHasLight("White") is False
        assert any("rain has put every flame out" in m for m in broadcasts(env))

    def test_rain_leaves_the_lantern_lit_indoors(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        tile(env, "JamesHouse")
        env.execute('TTS.setHand("White", { TTS.makeObject({tags={"M_LANTERN"}}) })')
        set_effect(env, "rainFireDisabled")
        assert env.globals().checkPlayerHasLight("White") is True

    def test_rain_leaves_a_flashlight_working_at_a_court(self, env):
        """rainFireDisabled drowns flames, not batteries."""
        add_char(env, "White", "James", location="BadmintonCourt")
        tile(env, "BadmintonCourt")
        env.execute('TTS.setHand("White", { TTS.makeObject({tags={"M_FLASHLIGHT"}}) })')
        set_effect(env, "rainFireDisabled")
        assert env.globals().checkPlayerHasLight("White") is True

    def test_rain_also_drowns_the_shared_campfire_at_a_court(self, env):
        add_char(env, "Red", "Coco", location="BasketballCourt")
        tile(env, "BasketballCourt", (10, 1, 10))
        env.eval("TTS.addObject")(py_to_lua(env, {"tags": ["M_CAMPFIRE"], "position": [12, 1, 10]}))
        set_effect(env, "rainFireDisabled")
        assert env.globals().checkPlayerHasLight("Red") is False


class TestSleepEffects:
    def test_walls_close_puts_the_second_sleeper_on_the_floor(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        add_char(env, "Green", "Ellie", location="JamesHouse", sanity=4)
        set_effect(env, "reducedCapacity")
        env.globals().resolveSleep()
        # One bed, and it goes to the owner: Ellie is the guest on the floor.
        assert env.eval("gameState.activeChars.Green.sanity") == 4
        assert any("gets the floor" in m for m in broadcasts(env))

    def test_two_sleep_comfortably_without_the_card(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        add_char(env, "Green", "Ellie", location="JamesHouse", sanity=4)
        env.globals().resolveSleep()
        assert env.eval("gameState.activeChars.Green.sanity") == 5

    def test_memory_flood_doubles_the_home_sanity(self, env):
        add_char(env, "White", "James", location="JamesHouse", sanity=4)
        set_effect(env, "homeSanityBonus")
        env.globals().resolveSleep()
        assert env.eval("gameState.activeChars.White.sanity") == 6  # +1 +1

    def test_memory_flood_does_not_reach_a_friends_house(self, env):
        add_char(env, "White", "James", location="RaymanHouse", sanity=4)
        add_char(env, "Yellow", "Rayman", location="RaymanHouse")
        set_effect(env, "homeSanityBonus")
        env.globals().resolveSleep()
        assert env.eval("gameState.activeChars.White.sanity") == 5


class TestDoomTiming:
    """Both cards name the Doom advance that BeginDay already made, so they
    have to hand it back rather than set a flag for a read that has passed."""

    def test_hope_remains_gives_back_one_doom(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.doom = 12")
        env.eval("DAWN_EFFECTS.P4_HOPE_REMAINS.onReveal")(None)
        assert env.eval("gameState.doom") == 11

    def test_hope_remains_cannot_push_doom_below_zero(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.doom = 0")
        env.eval("DAWN_EFFECTS.P4_HOPE_REMAINS.onReveal")(None)
        assert env.eval("gameState.doom") == 0

    def test_dawn_breaks_refunds_the_phase_rate(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.doom = 12; gameState.day = 6")
        rate = env.globals().getDoomRate()
        env.eval("DAWN_EFFECTS.P4_DAWN_BREAKS.onReveal")(None)
        assert env.eval("gameState.doom") == 12 - rate


class TestRecipeEffects:
    def _stock(self, env, color, **res):
        for r, n in res.items():
            env.globals().giveResource(color, r, n)

    def test_iced_tea_reaches_an_adjacent_ally(self, env):
        add_char(env, "Green", "Ellie", location="EllieLucaHouse", sanity=4)
        add_char(env, "White", "James", location="JamesHouse", sanity=4)
        self._stock(env, "Green", Food=1, Cloth=1)
        env.globals().doCook("Green", "R_ICE_TEA")
        # cookOnly for the cook, adjacentAllies for the neighbour (the Ring
        # default connects EllieLucaHouse and JamesHouse).
        assert env.eval("gameState.activeChars.Green.sanity") == 5
        assert env.eval("gameState.activeChars.White.sanity") == 5

    def test_iced_tea_does_not_reach_two_tiles_away(self, env):
        add_char(env, "Green", "Ellie", location="JamesHouse", sanity=4)
        add_char(env, "Yellow", "Rayman", location="RaymanHouse", sanity=4)
        self._stock(env, "Green", Food=1, Cloth=1)
        # Star: JamesHouse and RaymanHouse are both leaves off EllieLucaHouse.
        env.execute("LOCATION_ADJACENCY = buildAdjacency('Star')")
        env.globals().doCook("Green", "R_ICE_TEA")
        assert env.eval("gameState.activeChars.Yellow.sanity") == 4

    def test_last_meal_makes_recipes_go_further(self, env):
        add_char(env, "White", "James", location="EllieLucaHouse", hunger=1)
        self._stock(env, "White", Food=1)
        set_effect(env, "recipeBonusHunger")
        env.globals().doCook("White", "R_LEFTOVERS")   # cookOnly hunger 2
        assert env.eval("gameState.activeChars.White.hunger") == 5  # 1 + 2 + 2

    def test_recipes_are_ordinary_without_the_card(self, env):
        add_char(env, "White", "James", location="EllieLucaHouse", hunger=1)
        self._stock(env, "White", Food=1)
        env.globals().doCook("White", "R_LEFTOVERS")
        assert env.eval("gameState.activeChars.White.hunger") == 3  # 1 + 2

    def test_the_bonus_touches_hunger_only(self, env):
        add_char(env, "White", "James", location="EllieLucaHouse", hunger=1, sanity=1)
        self._stock(env, "White", Food=1, Wood=1)
        set_effect(env, "recipeBonusHunger")
        env.globals().doCook("White", "R_HOT_CHOCOLATE")  # hunger 1, sanity 2
        assert env.eval("gameState.activeChars.White.hunger") == 4  # 1 + 1 + 2
        assert env.eval("gameState.activeChars.White.sanity") == 3  # 1 + 2
