"""Rules the game states as fact: the place you stand, and the boss you killed.

Five rules the UI asserts to the player, none of which existed.

**"its power is live"** — the boss-kill broadcast says this, twice, about the
Trophy it just flipped face-up. `revealTrophy` turned a card over and
highlighted it; that was the whole implementation. The Antler Sled's tow and
the Watching Jar's Dusk look at the Threat deck had no code at all. The Trophy
is the entire reward for the hardest content in the game — §14.1's "a boss kill
should visibly rescue the week, not just remove a penalty" — and it was a
picture of a reward.

**"Echoes: d6 on gather (6=bonus, 1-2=Sanity loss)"** — the Basketball Court's
board tooltip, and its What-now hint says it too. Design §7.4 specifies it. No
d6 was ever rolled: the court was a plain Gather wearing a gamble's
description, which is what its −1 Sanity at sleep and its threat rate are
supposed to be paid for with.

**"The Net gives +1 defense die in combat"** — the Badminton Court's What-now
hint, and its tooltip. There was no defence roll anywhere in the mod, and
`locations.csv` carried a `defense` column that nothing read.

**"-1 Sanity at Tick" / "+1 Sanity at Tick"** — every one of the five board
tooltips prints the tile's Sanity modifier, design §7.1-7.5 gives each tile
one, and the §8 cost table bills "sleeping at a court" for it. Nothing read
`locations.csv`'s `sanity_modifier` column: the Tick charged the same 1
wherever you slept, so the whole positional argument the Dusk scramble is
about had no mechanical weight.

**"Highest threat draw rate at Night"** — the Badminton Court's tooltip, its
What-now hint and design §7.5. `LOCATION_THREAT_RATE` gave it 1, exactly like
the Basketball Court, while `locations.csv` said 2. The tile's one distinctive
hazard was printed three times and rolled nowhere.

**"The Garage: Rest +1 Health"** — Rayman's House's tooltip, with no owner
qualifier, because §7.2 puts the bonus on the *place*. The code gave +1 Health
only at your own home, so the Garage did nothing for anyone except Rayman, for
whom it was already true. The one line that made it worth walking to was inert.
"""
import pytest
from conftest import (
    add_char,
    broadcasts,
    lua52,
    lua_to_py,
    py_to_lua,
    script_dice,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


# ---------------------------------------------------------------------------
# Echoes (Design §7.4) — the Basketball Court's gamble.
# ---------------------------------------------------------------------------


class TestEchoes:
    def test_a_six_finds_something_in_the_bleachers(self, env):
        add_char(env, "White", "James", location="BasketballCourt", sanity=10)
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["MarketCardDeck"],
            "contained": [{"nickname": "Improvised Bat", "guid": "mk1"}]}))
        script_dice(env, [6])
        env.globals().resolveEchoes("White", "BasketballCourt")
        said = " ".join(broadcasts(env))
        assert "6 — something useful" in said
        assert env.eval("gameState.activeChars.White.sanity") == 10

    @pytest.mark.parametrize("roll", [1, 2])
    def test_a_low_roll_costs_sanity(self, env, roll):
        add_char(env, "White", "James", location="BasketballCourt", sanity=10)
        script_dice(env, [roll])
        env.globals().resolveEchoes("White", "BasketballCourt")
        assert env.eval("gameState.activeChars.White.sanity") == 9

    @pytest.mark.parametrize("roll", [3, 4, 5])
    def test_the_middle_of_the_dice_is_only_the_wind(self, env, roll):
        add_char(env, "White", "James", location="BasketballCourt", sanity=10)
        script_dice(env, [roll])
        env.globals().resolveEchoes("White", "BasketballCourt")
        assert env.eval("gameState.activeChars.White.sanity") == 10
        assert any("only the wind" in b for b in broadcasts(env))

    def test_it_is_the_basketball_courts_rule_alone(self, env):
        """The Badminton Court has the Net; the Echoes are §7.4's, and giving
        them to every court would be inventing a rule, not fixing one."""
        for loc in ("BadmintonCourt", "JamesHouse", "EllieLucaHouse", "RaymanHouse"):
            add_char(env, "White", "James", location=loc, sanity=10)
            env.globals().resolveEchoes("White", loc)
            assert env.eval("gameState.activeChars.White.sanity") == 10
        assert not any("Echoes" in b for b in broadcasts(env))

    def test_a_gather_at_the_court_rolls_it(self, env):
        """The wiring, not just the function: doGather has four early-return
        paths and the court must reach the one that rolls."""
        add_char(env, "White", "James", location="BasketballCourt", sanity=10)
        script_dice(env, [1, 1])   # resource pick, then Echoes = 1
        env.globals().doGather("White")
        assert env.eval("gameState.activeChars.White.sanity") == 9


# ---------------------------------------------------------------------------
# The Net, and the open court (Design §7.2 / §7.4 / §7.5).
# ---------------------------------------------------------------------------


class TestLocationDefence:
    def test_the_table_matches_the_design(self, env):
        assert lua_to_py(env.eval("LOCATION_DEFENSE")) == {
            "JamesHouse": 0, "RaymanHouse": 1, "EllieLucaHouse": 0,
            "BasketballCourt": -1, "BadmintonCourt": 1,
        }

    def test_the_net_turns_a_counter_hit_aside(self, env):
        add_char(env, "White", "James", location="BadmintonCourt", health=8)
        # attack whiffs (3), the threat's counter hits (5), the Net blocks (6).
        script_dice(env, [3, 5, 6])
        env.globals().beginCombat(
            py_to_lua(env, ["White"]),
            py_to_lua(env, {"name": "Thing", "hp": 9, "attack": 1}))
        assert env.eval("gameState.activeChars.White.health") == 8
        said = " ".join(broadcasts(env))
        assert "turns 1 hit(s) aside" in said
        assert "misses!" not in said, (
            "it connected and the cover ate it — crediting the dice with what "
            "the Net did is the wrong story")

    def test_a_failed_block_still_lets_the_hit_through(self, env):
        add_char(env, "White", "James", location="BadmintonCourt", health=8)
        script_dice(env, [3, 5, 2])   # block die misses
        env.globals().beginCombat(
            py_to_lua(env, ["White"]),
            py_to_lua(env, {"name": "Thing", "hp": 9, "attack": 1}))
        assert env.eval("gameState.activeChars.White.health") == 7

    def test_no_block_is_rolled_when_nothing_landed(self, env):
        """A missed counter must not spend the table's attention on a
        pointless roll — and the scripted dice prove none was taken."""
        add_char(env, "White", "James", location="BadmintonCourt", health=8)
        script_dice(env, [3, 2])      # attack whiff, counter miss. No third die.
        env.globals().beginCombat(
            py_to_lua(env, ["White"]),
            py_to_lua(env, {"name": "Thing", "hp": 9, "attack": 1}))
        assert env.eval("gameState.activeChars.White.health") == 8

    def test_the_open_court_gives_the_threat_an_extra_swing(self, env):
        add_char(env, "White", "James", location="BasketballCourt", health=8)
        # attack whiff, then TWO counter dice (attack 1, defence -1), both hit.
        script_dice(env, [3, 5, 5])
        env.globals().beginCombat(
            py_to_lua(env, ["White"]),
            py_to_lua(env, {"name": "Thing", "hp": 9, "attack": 1}))
        assert env.eval("gameState.activeChars.White.health") == 6
        assert any("No cover at BasketballCourt" in b for b in broadcasts(env))

    def test_a_neutral_house_changes_nothing(self, env):
        add_char(env, "White", "James", location="JamesHouse", health=8)
        script_dice(env, [3, 5])
        env.globals().beginCombat(
            py_to_lua(env, ["White"]),
            py_to_lua(env, {"name": "Thing", "hp": 9, "attack": 1}))
        assert env.eval("gameState.activeChars.White.health") == 7


# ---------------------------------------------------------------------------
# The Garage (Design §7.2).
# ---------------------------------------------------------------------------


class TestTheGarage:
    def test_anyone_resting_there_gets_the_health(self, env):
        add_char(env, "White", "James", location="RaymanHouse", health=5)
        env.globals().doRest("White", "sanity")
        assert env.eval("gameState.activeChars.White.health") == 6

    def test_rayman_does_not_get_it_twice(self, env):
        """Non-stacking with the own-home bonus, exactly like Doom 25."""
        add_char(env, "Yellow", "Rayman", location="RaymanHouse", health=5)
        env.globals().doRest("Yellow", "sanity")
        assert env.eval("gameState.activeChars.Yellow.health") == 6

    def test_it_does_not_follow_you_home(self, env):
        add_char(env, "White", "James", location="EllieLucaHouse", health=5)
        env.globals().doRest("White", "sanity")
        assert env.eval("gameState.activeChars.White.health") == 5

    def test_a_forbidden_health_day_still_wins(self, env):
        add_char(env, "White", "James", location="RaymanHouse", health=5)
        env.execute("gameState.ongoingDawnEffects.restNoHealth = true")
        env.globals().doRest("White", "sanity")
        assert env.eval("gameState.activeChars.White.health") == 5


# ---------------------------------------------------------------------------
# Trophy powers.
# ---------------------------------------------------------------------------


class TestAntlerSled:
    def _earn(self, env):
        env.execute("gameState.bossesDefeated = {deerclops = true}")

    def test_no_trophy_no_offer(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        add_char(env, "Green", "Ellie", location="JamesHouse")
        assert env.globals().offerAntlerSled("White", "JamesHouse", "EllieLucaHouse") is False

    def test_the_offer_needs_someone_to_bring(self, env):
        self._earn(env)
        add_char(env, "White", "James", location="EllieLucaHouse")
        assert env.globals().offerAntlerSled("White", "JamesHouse", "EllieLucaHouse") is False

    def test_it_offers_once_the_trophy_is_earned(self, env):
        self._earn(env)
        add_char(env, "White", "James", location="EllieLucaHouse")
        add_char(env, "Green", "Ellie", location="JamesHouse")
        assert env.globals().offerAntlerSled("White", "JamesHouse", "EllieLucaHouse") is True

    def test_a_down_ally_cannot_be_towed(self, env):
        self._earn(env)
        add_char(env, "White", "James", location="EllieLucaHouse")
        add_char(env, "Green", "Ellie", location="JamesHouse", down=True)
        assert env.globals().offerAntlerSled("White", "JamesHouse", "EllieLucaHouse") is False

    def test_the_tow_moves_the_ally_and_costs_them_hunger(self, env):
        self._earn(env)
        add_char(env, "White", "James", location="EllieLucaHouse")
        add_char(env, "Green", "Ellie", location="JamesHouse", hunger=10)
        assert env.globals().bringAllyOnSled("White", "Green", "EllieLucaHouse") is True
        assert env.eval("gameState.activeChars.Green.location") == "EllieLucaHouse"
        assert env.eval("gameState.activeChars.Green.hunger") == 9

    def test_the_tow_costs_the_ally_no_action(self, env):
        self._earn(env)
        add_char(env, "White", "James", location="EllieLucaHouse")
        add_char(env, "Green", "Ellie", location="JamesHouse", actionsLeft=3)
        env.globals().bringAllyOnSled("White", "Green", "EllieLucaHouse")
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 3

    def test_once_per_turn(self, env):
        self._earn(env)
        add_char(env, "White", "James", location="EllieLucaHouse")
        add_char(env, "Green", "Ellie", location="JamesHouse")
        add_char(env, "Red", "Luca", location="JamesHouse")
        env.globals().bringAllyOnSled("White", "Green", "EllieLucaHouse")
        assert env.globals().offerAntlerSled("White", "JamesHouse", "EllieLucaHouse") is False

    def test_a_new_turn_reopens_it(self, env):
        self._earn(env)
        add_char(env, "White", "James", location="EllieLucaHouse")
        add_char(env, "Green", "Ellie", location="JamesHouse")
        env.globals().bringAllyOnSled("White", "Green", "EllieLucaHouse")
        env.execute("gameState.sledUsedThisTurn = {}")   # beginDayPhase does this
        add_char(env, "Red", "Luca", location="JamesHouse")
        assert env.globals().offerAntlerSled("White", "JamesHouse", "EllieLucaHouse") is True


class TestWatchingJar:
    def _deck(self, env):
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["ThreatCardDeck"],
            "contained": [{"nickname": "Shadow Stalker", "guid": "wj1"},
                          {"nickname": "Lurker", "guid": "wj2"},
                          {"nickname": "Black Dog", "guid": "wj3"}]}))

    def test_silent_without_the_trophy(self, env):
        self._deck(env)
        assert env.globals().resolveWatchingJar() is False
        assert not any("WATCHING JAR" in b for b in broadcasts(env))

    def test_it_shows_the_top_two_to_everyone(self, env):
        env.execute("gameState.bossesDefeated = {eye = true}")
        self._deck(env)
        assert env.globals().resolveWatchingJar() is True
        said = " ".join(broadcasts(env))
        assert "Shadow Stalker" in said and "Lurker" in said
        assert "Black Dog" not in said, "it looks at two cards, not the deck"

    def test_dusk_opens_the_jar(self, env):
        """The wiring: the look has to happen while the scramble window is
        open, or the information cannot change anybody's mind."""
        env.execute("gameState.bossesDefeated = {eye = true}")
        env.execute("gameState.day = 2")
        self._deck(env)
        add_char(env, "White", "James")
        env.globals().beginDusk()
        assert any("WATCHING JAR" in b for b in broadcasts(env))


def test_the_rules_panel_lists_the_powers_the_team_holds(env):
    env.execute("gameState.started = true")
    env.execute("gameState.bossesDefeated = {deerclops = true}")
    add_char(env, "White", "James")
    env.eval("refreshRulesPanel()")
    body = lua_to_py(env.eval("TTS.ui"))["attrs"]["rulesBody"]["text"]
    assert "The Antler Sled" in body
    assert "The Watching Jar" not in body, "only the trophies actually earned"


# ---------------------------------------------------------------------------
# The tile you slept on (Design §7.1-7.5): the Tick's Sanity modifier and the
# Badminton Court's threat rate. Both were printed on the board and nowhere
# else — see this module's docstring.
# ---------------------------------------------------------------------------


class TestWhereYouSlept:
    @pytest.mark.parametrize("location,expected", [
        ("BasketballCourt", 8),    # -1 base, -1 the open court
        ("BadmintonCourt", 8),
        ("JamesHouse", 9),         # -1 base, no modifier
        ("EllieLucaHouse", 10),    # -1 base, +1 the warm kitchen
    ])
    def test_tick_sanity_depends_on_the_tile(self, env, location, expected):
        add_char(env, "Blue", "Luca", location=location, sanity=10)
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Blue.sanity") == expected

    def test_a_court_night_says_so(self, env):
        add_char(env, "Blue", "Luca", location="BadmintonCourt", sanity=10)
        env.globals().resolveTick()
        assert any("slept in the open" in b for b in broadcasts(env))

    def test_the_kitchen_never_gains_sanity(self, env):
        """The modifier subtracts from a loss; it must not turn the Tick into
        a heal, or the kitchen becomes a Sanity engine nobody would leave."""
        add_char(env, "Blue", "Luca", location="EllieLucaHouse", sanity=4)
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Blue.sanity") == 4

    def test_badminton_is_the_highest_threat_tile(self, env):
        rate = {loc: env.eval(f"LOCATION_THREAT_RATE.{loc}")
                for loc in ("JamesHouse", "RaymanHouse", "EllieLucaHouse",
                            "BasketballCourt", "BadmintonCourt")}
        assert rate["BadmintonCourt"] > rate["BasketballCourt"], (
            "the Badminton Court's tooltip, its What-now hint and §7.5 all call "
            "it the highest threat draw rate at Night")
        assert all(rate[house] == 0
                   for house in ("JamesHouse", "RaymanHouse", "EllieLucaHouse"))


# ---------------------------------------------------------------------------
# The Gathering (Design §15.10) — the anti-huddle rule. A house draws no
# threats of its own, so before this existed a whole team could sleep in one
# room for a week and simply have no nights: the balance probe measured that
# line at ~100% wins against a 40-50% design target.
# ---------------------------------------------------------------------------


class TestTheGathering:
    def _night(self, env, colors, day=4, location="EllieLucaHouse"):
        env.execute(f"gameState.day = {day}")
        for i, name in enumerate(("James", "Coco", "Ellie", "Luca")[:len(colors)]):
            add_char(env, colors[i], name, location=location)
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": [f"Location:{location}"], "position": [0, 1, 0]}))
        env.globals().resolveNightAtLocation(location, py_to_lua(env, colors))
        return " ".join(broadcasts(env))

    def test_three_in_one_room_draw_an_extra_threat(self, env):
        assert "drawn to the gathering" in self._night(env, ["White", "Red", "Green"])

    def test_two_is_a_pair_not_a_crowd(self, env):
        assert "drawn to the gathering" not in self._night(env, ["White", "Red"])

    def test_the_opening_stays_quiet(self, env):
        """Phase 1 is the calm the week is supposed to open on, so the rule
        waits for Day 3 — a Day-1 huddle is still allowed."""
        said = self._night(env, ["White", "Red", "Green"], day=2)
        assert "drawn to the gathering" not in said

    def test_converging_on_a_boss_is_not_hiding(self, env):
        """The design spends the whole week telling the team to gather on the
        Source (§16.3.3). Charging them a Threat for obeying it would be the
        rule punishing its own climax."""
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Boss", "Boss:TheSource"], "position": [0, 1, 0]}))
        said = self._night(env, ["White", "Red", "Green"])
        assert "drawn to the gathering" not in said
