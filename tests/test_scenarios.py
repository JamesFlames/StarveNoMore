"""A Scenario's description is a promise it keeps for the whole week.

`gameState.scenarioFlags` is the twin of `ongoingDawnEffects`, and it sat
outside `test_lua_effect_flags.py` the entire time that module was guarding
the other one. The identical rot ran unchecked for longer and got further: a
2026-07 sweep found **twelve of the seventeen flags** the eight Scenario cards
set were read by nothing.

    SC_RATIONING  slowMarket, cheapRecipes            → both dead
    SC_AUTUMN     foodSpoilsAtDawn, recipeBonus, clothBonus → all three dead

so **The Rotting Autumn and Strict Rationing did literally nothing** — the
banner announced them, the Rules panel printed their full description for
seven days, and the game underneath was the base game. Four more were partly
inert: the Long Winter never froze the food, the Scorching Summer's Energy
Drinks and courts were ordinary, Total Blackout's Batteries were on the
shelves, and the Full Moon's Soft threats stayed soft.

A Scenario rots worse than a Dawn card when it rots. It is chosen once at
setup and announced once, so nobody re-reads it to check; and it lasts the
whole game, so its absence is seven days of a rule that never arrives.

**And two of the five that "worked" were on borrowed time.** Total Blackout
and The Full Moon put their rule in `ongoingDawnEffects` (`onlyFireLight`,
`charliePaused`) — a per-Dawn scratchpad that unrelated Dawn cards clear in
their `onCleanup`. `dawn_effects_phase4` nils `onlyFireLight`; `phase3` nils
`charliePaused`. Drawing either card would have switched a week-long scenario
off for the rest of the game, silently. Both rules are read from
`scenarioFlags` now, which nothing else can touch.
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


def scenario(env, flags):
    env.execute("gameState.scenarioFlags = {%s}" %
                ", ".join(f"{k} = true" for k in flags))


def tile(env, loc, pos=(0, 1, 0)):
    env.eval("TTS.addObject")(py_to_lua(env, {
        "tags": [f"Location:{loc}"], "position": list(pos)}))


# ---------------------------------------------------------------------------
# The Long Winter.
# ---------------------------------------------------------------------------


class TestLongWinter:
    def test_the_ground_keeps_its_food(self, env):
        add_char(env, "White", "James", location="EllieLucaHouse")
        scenario(env, ["foodGatherPenalty"])
        # EllieLucaHouse yields {Provisions, Provisions, Cloth}: pick Provisions twice, Cloth once.
        script_dice(env, [1, 2, 3])
        env.globals().gatherRandomResources("White", "EllieLucaHouse", 3)
        held = env.eval("gameState.resources.White")
        assert held["Provisions"] == 0
        assert held["Cloth"] == 1
        assert any("frozen scrap" in b for b in broadcasts(env))

    def test_a_gather_that_finds_only_food_finds_nothing(self, env):
        add_char(env, "White", "James", location="EllieLucaHouse")
        scenario(env, ["foodGatherPenalty"])
        script_dice(env, [1])
        env.globals().gatherRandomResources("White", "EllieLucaHouse", 1)
        assert any("finds nothing usable" in b for b in broadcasts(env))

    def test_without_the_scenario_food_still_comes_up(self, env):
        add_char(env, "White", "James", location="EllieLucaHouse")
        script_dice(env, [1])
        env.globals().gatherRandomResources("White", "EllieLucaHouse", 1)
        assert env.eval("gameState.resources.White.Provisions") == 1


# ---------------------------------------------------------------------------
# The Scorching Summer.
# ---------------------------------------------------------------------------


class TestScorchingSummer:
    def test_energy_drinks_hit_harder(self, env):
        add_char(env, "Green", "Ellie", sanity=4)
        scenario(env, ["energyDrinkBonus"])
        env.globals().doEnergyDrink("Green")
        assert env.eval("gameState.activeChars.Green.sanity") == 7

    def test_without_it_they_are_ordinary(self, env):
        add_char(env, "Green", "Ellie", sanity=4)
        env.globals().doEnergyDrink("Green")
        assert env.eval("gameState.activeChars.Green.sanity") == 6

    def test_the_courts_yield_one_more(self, env):
        add_char(env, "White", "James", location="BasketballCourt", sanity=10)
        scenario(env, ["courtGatherBonus"])
        script_dice(env, [1, 1, 3])   # two resource picks, then Echoes = 3
        env.globals().doGather("White")
        held = env.eval("gameState.resources.White")
        assert (held["Wood"] or 0) == 2, "1 base + 1 Scorching Summer"

    def test_the_houses_get_nothing_extra(self, env):
        add_char(env, "Green", "Ellie", location="RaymanHouse")
        scenario(env, ["courtGatherBonus"])
        script_dice(env, [1])
        env.globals().doGather("Green")
        total = sum(v for v in
                    [env.eval(f"gameState.resources.Green.{r}")
                     for r in ("Wood", "Metal", "Cloth", "Provisions", "EnergyDrink", "Battery")]
                    if v)
        assert total == 1


# ---------------------------------------------------------------------------
# The Rotting Autumn — every clause of it was dead.
# ---------------------------------------------------------------------------


class TestRottingAutumn:
    def test_one_food_spoils_per_location_not_per_player(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        add_char(env, "Green", "Ellie", location="JamesHouse")
        add_char(env, "Red", "Luca", location="RaymanHouse")
        env.execute("gameState.resources = {White = {Provisions = 2}, "
                    "Green = {Provisions = 5}, Red = {Provisions = 3}}")
        scenario(env, ["foodSpoilsAtDawn"])
        env.execute("gameState.started = true; gameState.day = 2")
        env.globals().BeginDay()
        # JamesHouse loses one, from the fullest larder there; RaymanHouse
        # loses one; nobody loses two.
        assert env.eval("gameState.resources.Green.Provisions") == 4
        assert env.eval("gameState.resources.White.Provisions") == 2
        assert env.eval("gameState.resources.Red.Provisions") == 2

    def test_recipes_go_further(self, env):
        add_char(env, "White", "James", hunger=1)
        scenario(env, ["recipeBonus"])
        env.execute("gameState.resources = {White = {Provisions = 5, Wood = 5, "
                    "Cloth = 5, Metal = 5, Battery = 5, EnergyDrink = 5}}")
        base = env.eval("RECIPE_DATA.R_HOT_STEW.allAtTile.hunger")
        env.globals().doCook("White", "R_HOT_STEW")
        assert env.eval("gameState.activeChars.White.hunger") == 1 + base + 1

    def test_cloth_turns_up_more_often(self, env):
        """'Cloth is easier to find' — a second entry in the draw table,
        which is what easier means when the draw is a uniform pick."""
        add_char(env, "White", "James", location="JamesHouse")
        scenario(env, ["clothBonus"])
        # JamesHouse yields {EnergyDrink, Battery, Provisions}; Cloth is appended.
        script_dice(env, [4])
        env.globals().gatherRandomResources("White", "JamesHouse", 1)
        assert env.eval("gameState.resources.White.Cloth") == 1


# ---------------------------------------------------------------------------
# Total Blackout.
# ---------------------------------------------------------------------------


class TestTotalBlackout:
    def test_no_battery_comes_out_of_the_ground(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        scenario(env, ["noBatteries"])
        # JamesHouse normally yields {EnergyDrink, Battery, Provisions}; with
        # Battery gone the table is {EnergyDrink, Provisions} and index 2 is Provisions.
        script_dice(env, [2])
        env.globals().gatherRandomResources("White", "JamesHouse", 1)
        assert env.eval("gameState.resources.White.Battery") == 0
        assert env.eval("gameState.resources.White.Provisions") == 1

    def test_the_scenario_rule_survives_a_dawn_card_cleanup(self, env):
        """The bug this fixes: Total Blackout put its only working rule in
        ongoingDawnEffects, and dawn_effects_phase4's onCleanup nils
        onlyFireLight — which would hand flashlights back for the rest of the
        week, silently."""
        add_char(env, "White", "James", location="JamesHouse")
        scenario(env, ["onlyFireLight"])
        env.execute("gameState.ongoingDawnEffects.onlyFireLight = true")
        env.execute('TTS.setHand("White", { TTS.makeObject({tags={"M_FLASHLIGHT"}, '
                    'nickname="Flashlight"}) })')
        assert env.globals().checkPlayerHasLight("White") is False
        # A Phase-4 card ends and clears the Dawn copy...
        env.execute("gameState.ongoingDawnEffects.onlyFireLight = nil")
        assert env.globals().checkPlayerHasLight("White") is False, (
            "the week-long scenario rule must not be cancellable by an "
            "unrelated Dawn card's cleanup")


# ---------------------------------------------------------------------------
# Strict Rationing — both clauses were dead.
# ---------------------------------------------------------------------------


class TestStrictRationing:
    def test_recipes_cost_one_fewer_ingredient(self, env):
        add_char(env, "White", "James")
        before = env.eval("(function() local t = 0 "
                          "for _, q in pairs(recipeIngredientCost('White', "
                          "RECIPE_DATA.R_HOT_STEW)) do t = t + q end return t end)()")
        scenario(env, ["cheapRecipes"])
        after = env.eval("(function() local t = 0 "
                         "for _, q in pairs(recipeIngredientCost('White', "
                         "RECIPE_DATA.R_HOT_STEW)) do t = t + q end return t end)()")
        assert after == before - 1

    def test_it_never_takes_the_last_ingredient(self, env):
        """A recipe that costs nothing is a different card."""
        add_char(env, "Green", "Ellie")   # her perk already discounts by 1
        scenario(env, ["cheapRecipes"])
        for rid in ("R_HOT_STEW", "R_PORRIDGE", "R_LEFTOVERS"):
            total = env.eval("(function() local t = 0 "
                             f"for _, q in pairs(recipeIngredientCost('Green', RECIPE_DATA.{rid}) or {{}}) "
                             "do t = t + q end return t end)()")
            assert total >= 1, f"{rid} became free"

    def _market(self, env):
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["MarketCardDeck"],
            "contained": [{"nickname": "A", "guid": "m1"},
                          {"nickname": "B", "guid": "m2"}]}))
        # refillMarketSlot takes the slot OBJECT (it reads getPosition), not
        # an index — the index lives one level up in doCraft.
        env.execute('__slot = TTS.addObject({tags = {"MarketSlot"}, position = {5,1,5}})')
        return env.eval("__slot")

    def test_the_market_restocks_only_every_second_day(self, env):
        slot = self._market(env)
        scenario(env, ["slowMarket"])
        env.execute("gameState.day = 1")
        env.globals().refillMarketSlot(slot)
        assert env.eval("gameState.lastMarketRefillDay") == 1
        env.execute("gameState.day = 2")
        env.globals().refillMarketSlot(slot)
        assert env.eval("gameState.lastMarketRefillDay") == 1, "too soon"
        assert any("the shelf stays empty" in b for b in broadcasts(env))
        env.execute("gameState.day = 3")
        env.globals().refillMarketSlot(slot)
        assert env.eval("gameState.lastMarketRefillDay") == 3

    def test_without_the_scenario_the_market_refills_freely(self, env):
        slot = self._market(env)
        env.execute("gameState.day = 1")
        env.globals().refillMarketSlot(slot)
        env.globals().refillMarketSlot(slot)
        assert env.eval("gameState.lastMarketRefillDay") is None


# ---------------------------------------------------------------------------
# The Full Moon.
# ---------------------------------------------------------------------------


class TestFullMoon:
    def _soft(self, env, pos=(1, 1, 1)):
        env.execute(
            '__s = TTS.addObject({tags = {"ThreatCard", "T_WHISPERS"}, type = "Card", '
            'nickname = "Whispers Behind the Walls", position = {%g,%g,%g}})' % pos)
        return env.eval("__s")

    def test_a_soft_card_becomes_a_fight(self, env):
        scenario(env, ["softToHard"])
        card = self._soft(env)
        assert env.globals().identifyThreatType(card) == "Hard"

    def test_it_gains_the_printed_statline(self, env):
        scenario(env, ["softToHard"])
        card = self._soft(env)
        stats = env.eval(
            "(function() local s = threatStatsForCard(__s) return s end)()")
        assert stats["hp"] == 2 and stats["attack"] == 1
        assert card is not None

    def test_the_promoted_card_is_actually_fightable(self, env):
        """The point of doing this in threatStatsForCard: fightTargetsAt
        filters hp 0, so promoting only the *type* would have turned every
        atmospheric card into an unkillable Doom tax."""
        scenario(env, ["softToHard"])
        add_char(env, "White", "James", location="JamesHouse")
        tile(env, "JamesHouse")
        self._soft(env)
        assert env.eval("#fightTargetsAt('JamesHouse')") == 1

    def test_the_generated_statline_is_not_mutated(self, env):
        """THREAT_STATS rows are shared references — promoting in place would
        leave every later game with a 2 HP Whispers."""
        scenario(env, ["softToHard"])
        self._soft(env)
        env.eval("threatStatsForCard(__s)")
        assert env.eval("THREAT_STATS.T_WHISPERS.hp") == 0

    def test_without_the_moon_it_is_still_soft(self, env):
        card = self._soft(env)
        assert env.globals().identifyThreatType(card) == "Soft"
        stats = env.eval("(function() local s = threatStatsForCard(__s) return s end)()")
        assert stats["hp"] == 0
        assert card is not None

    def test_hard_and_persistent_cards_are_untouched(self, env):
        scenario(env, ["softToHard"])
        env.execute(
            '__h = TTS.addObject({tags = {"ThreatCard", "T_SHADOW_STALKER"}, '
            'type = "Card", nickname = "Shadow Stalker", position = {1,1,1}})')
        stats = env.eval("(function() local s = threatStatsForCard(__h) return s end)()")
        assert stats["hp"] == 4 and stats["attack"] == 2

    def test_charlie_stays_away_even_after_a_dawn_card_cleanup(self, env):
        """The Full Moon's other borrowed flag: dawn_effects_phase3's
        onCleanup nils charliePaused, which would have brought Charlie back
        for the rest of the week."""
        scenario(env, ["noCharlie"])
        add_char(env, "White", "James", location="BasketballCourt")
        tile(env, "BasketballCourt")
        env.execute("gameState.ongoingDawnEffects.charliePaused = nil")
        env.globals().resolveNightAtLocation(
            "BasketballCourt", py_to_lua(env, ["White"]))
        assert not any("CHARLIE" in b for b in broadcasts(env))


def test_the_court_bonus_does_not_claim_to_be_a_backpack(env):
    """`extra > 0` used to be read as "has a Backpack" — true only while the
    Backpack was the one thing that could add to it."""
    add_char(env, "White", "James", location="BasketballCourt", sanity=10)
    scenario(env, ["courtGatherBonus"])
    script_dice(env, [1, 1, 3])
    env.globals().doGather("White")
    said = " ".join(broadcasts(env))
    assert "Scorching Summer" in said
    assert "Backpack" not in said
