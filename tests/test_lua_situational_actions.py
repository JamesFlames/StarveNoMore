"""The situational action verbs (lua/ui_actionbar_situational.lua).

Seven rules had working implementations and no way to reach them; the eighth,
Ghost Drift, rides the Reactions panel. test_lua_reachability.py is the guard
that stops that recurring — this module is the proof the wiring actually
works, end to end, from the click a player makes.

Each verb gets the same three questions, because "the button exists" is not
the bug this file is about:

  1. does the precondition open and close at the right moments?
  2. does clicking it move the *state its consumers already read* — the
     `jamesEnergyDrinkUsed` flag four files check, the `barricades` table
     day_loop subtracts from, the `raymanDefending` flag combat_resolve
     redirects damage on?
  3. does it refuse cleanly when it shouldn't fire?
"""
import pytest
from conftest import add_char, broadcasts, flush, lua52, lua_to_py

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


def player(env, color):
    return env.eval(f'Player["{color}"]')


def give(env, color, res, n):
    env.execute(f'giveResource("{color}", "{res}", {n})')


def start_day(env, color="White"):
    """Minimum viable Day phase with `color` active — enough for
    validateActivePlayer to let an action through."""
    env.execute(f'gameState.started = true; gameState.subPhase = "Day"; '
                f'gameState.activeColor = "{color}"')


def click(env, handler, color, value=""):
    env.eval(handler)(player(env, color), value, "")
    flush(env)


def arm_flee(env, color="White"):
    """onActFlee without flush() — see test_the_click_offers_tiles_and_the_target_runs."""
    env.eval("onActFlee")(player(env, color), "", "")


def enabled(env):
    """Which action-bar buttons the last refresh left visible."""
    return set(lua_to_py(env.eval("ENABLED_ACTIONS")) or {})


# ---------------------------------------------------------------------------
# Energy Drink — James's Wired constraint (§2). Four files read
# jamesEnergyDrinkUsed; nothing set it, so the -2 Sanity was unavoidable.
# ---------------------------------------------------------------------------


class TestEnergyDrink:
    def test_drinking_satisfies_wired_and_spends_the_token(self, env):
        add_char(env, "White", "James", sanity=4)
        start_day(env)
        give(env, "White", "EnergyDrink", 1)

        assert env.eval("gameState.jamesEnergyDrinkUsed") in (False, None)
        click(env, "onActEnergyDrink", "White")

        assert env.eval("gameState.jamesEnergyDrinkUsed") is True
        assert env.eval("gameState.activeChars.White.sanity") == 6, "+2 Sanity"
        assert env.eval('getPlayerResources("White").EnergyDrink') == 0, \
            "the token is consumed, or Wired is free"

    def test_wired_penalty_is_avoidable_now(self, env):
        """The whole point. Tick docks James 2 Sanity unless he drank today."""
        add_char(env, "White", "James", sanity=10)
        start_day(env)
        give(env, "White", "EnergyDrink", 1)
        click(env, "onActEnergyDrink", "White")

        env.globals().resolveTick()
        flush(env)
        assert not any("Wired" in m for m in broadcasts(env)), \
            "James drank, so Tick must not charge him the Wired penalty"

    def test_refused_without_a_token(self, env):
        add_char(env, "White", "James", sanity=4)
        start_day(env)
        click(env, "onActEnergyDrink", "White")
        assert env.eval("gameState.activeChars.White.sanity") == 4
        assert env.eval("gameState.jamesEnergyDrinkUsed") in (False, None)

    def test_button_appears_only_when_holding_one(self, env):
        add_char(env, "White", "James", sanity=4)
        start_day(env)
        env.globals().refreshSituationalButtons("White")
        assert "actEnergy" not in enabled(env)

        give(env, "White", "EnergyDrink", 1)
        env.globals().refreshSituationalButtons("White")
        assert "actEnergy" in enabled(env)


# ---------------------------------------------------------------------------
# Eat Raw (§3, §8.4) — and Ellie's Particular Eater constraint, which was
# printed in the rulebook and impossible to bump into.
# ---------------------------------------------------------------------------


class TestEatRaw:
    def test_trades_sanity_for_hunger(self, env):
        add_char(env, "White", "James", hunger=3, sanity=8)
        start_day(env)
        give(env, "White", "Food", 1)

        click(env, "onActEatRaw", "White")
        assert env.eval("gameState.activeChars.White.hunger") == 4
        assert env.eval("gameState.activeChars.White.sanity") == 7
        assert env.eval('getPlayerResources("White").Food') == 0

    def test_ellie_cannot_eat_raw(self, env):
        add_char(env, "Green", "Ellie", hunger=3, sanity=8)
        start_day(env, "Green")
        give(env, "Green", "Food", 1)

        ok, why = env.eval("canEatRaw")("Green")
        assert ok is False
        assert "Particular Eater" in why

        click(env, "onActEatRaw", "Green")
        assert env.eval("gameState.activeChars.Green.hunger") == 3, "no Hunger gained"
        assert env.eval('getPlayerResources("Green").Food') == 1, "and the Food is kept"


# ---------------------------------------------------------------------------
# Defend — Rayman's Backboard Block. combat_resolve.lua has always redirected
# counter-attack damage when raymanDefending is set; nothing ever set it.
# ---------------------------------------------------------------------------


class TestDefend:
    def test_rayman_raises_the_block(self, env):
        add_char(env, "Yellow", "Rayman")
        start_day(env, "Yellow")

        click(env, "onActDefend", "Yellow")
        assert env.eval("gameState.raymanDefending") is True
        assert env.eval("gameState.activeChars.Yellow.actionsLeft") == 2, "costs 1 action"

    def test_only_rayman(self, env):
        add_char(env, "White", "James")
        start_day(env)
        ok, why = env.eval("canDefend")("White")
        assert ok is False and "Rayman" in why

        click(env, "onActDefend", "White")
        assert env.eval("gameState.raymanDefending") in (False, None)
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3, "and costs nothing"

    def test_button_hidden_for_everyone_else(self, env):
        add_char(env, "White", "James")
        add_char(env, "Yellow", "Rayman")
        start_day(env)
        env.globals().refreshSituationalButtons("White")
        assert "actDefend" not in enabled(env)
        env.globals().refreshSituationalButtons("Yellow")
        assert "actDefend" in enabled(env)


# ---------------------------------------------------------------------------
# Barricade — day_loop.lua subtracts gameState.barricades[tile] from the
# night threat rate and prints "[barricaded]". Nothing ever wrote the table.
# ---------------------------------------------------------------------------


class TestBarricade:
    def test_it_marks_the_tile_the_night_draw_reads(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        start_day(env)
        give(env, "White", "Wood", 1)

        click(env, "onActBarricade", "White")
        assert env.eval('gameState.barricades.BasketballCourt') == 1
        assert env.eval('getPlayerResources("White").Wood') == 0
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2

    def test_refused_without_wood(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        start_day(env)
        click(env, "onActBarricade", "White")
        assert env.eval("gameState.barricades") is None or \
            env.eval('(gameState.barricades or {}).BasketballCourt') is None
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3, "action refunded"

    def test_not_offered_twice_on_the_same_tile(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        start_day(env)
        give(env, "White", "Wood", 2)
        click(env, "onActBarricade", "White")

        ok, why = env.eval("canBarricade")("White")
        assert ok is False and "already barricaded" in why


# ---------------------------------------------------------------------------
# Revive (§16.4) — the headline. Telltale Hearts could be cooked but never
# spent: gameState.heartCount only ever went up.
# ---------------------------------------------------------------------------


def _confirm(env):
    """Answer the safety-net dialog with Yes."""
    env.eval("onConfirmYes")(player(env, "White"), "", "")
    flush(env)


class TestRevive:
    def _two_at_a_tile(self, env):
        add_char(env, "White", "James", location="RaymanHouse")
        add_char(env, "Yellow", "Rayman", down=True, health=0, location="RaymanHouse")
        start_day(env)

    def test_the_whole_path_from_button_to_revived_ally(self, env):
        self._two_at_a_tile(env)
        env.execute("gameState.heartCount = 2")

        click(env, "onActRevive", "White")
        assert lua_to_py(env.eval("TTS.ui.visible")).get("downedDialog") is True
        assert env.eval('UI.getAttribute("downedBtn_Yellow", "active")') == "true"

        click(env, "onDownedTargetClick", "White", "Yellow")
        assert env.eval("gameState.activeChars.Yellow.down") is False
        assert env.eval("gameState.heartCount") == 1
        assert env.eval("gameState.activeChars.White.health") == 6, "reviver paid 2"

    def test_spending_the_last_heart_asks_first(self, env):
        self._two_at_a_tile(env)
        env.execute("gameState.heartCount = 1")

        click(env, "onActRevive", "White")
        click(env, "onDownedTargetClick", "White", "Yellow")
        assert env.eval("gameState.activeChars.Yellow.down") is True, \
            "the last Heart must not be spent before the player confirms"

        _confirm(env)
        assert env.eval("gameState.activeChars.Yellow.down") is False
        assert env.eval("gameState.heartCount") == 0

    def test_hidden_without_a_heart(self, env):
        self._two_at_a_tile(env)
        env.execute("gameState.heartCount = 0")
        env.globals().refreshSituationalButtons("White")
        assert "actRevive" not in enabled(env)

        env.execute("gameState.heartCount = 1")
        env.globals().refreshSituationalButtons("White")
        assert "actRevive" in enabled(env)

    def test_hidden_when_it_would_put_the_reviver_down(self, env):
        self._two_at_a_tile(env)
        env.execute("gameState.heartCount = 1; gameState.activeChars.White.health = 2")
        ok, why = env.eval("canRevive")("White")
        assert ok is False and "Down too" in why

    def test_only_targets_allies_at_your_own_tile(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        add_char(env, "Yellow", "Rayman", down=True, location="RaymanHouse")
        start_day(env)
        env.execute("gameState.heartCount = 1")
        ok, why = env.eval("canRevive")("White")
        assert ok is False and "Nobody is Down" in why


class TestStabilize:
    def test_brings_an_ally_back_at_one_health(self, env):
        add_char(env, "White", "James", location="RaymanHouse")
        add_char(env, "Yellow", "Rayman", down=True, health=0, location="RaymanHouse")
        start_day(env)

        click(env, "onActStabilize", "White")
        click(env, "onDownedTargetClick", "White", "Yellow")
        assert env.eval("gameState.activeChars.Yellow.down") is False
        assert env.eval("gameState.activeChars.Yellow.health") == 1, "not a full revival"
        assert env.eval("gameState.heartCount") in (0, None), "and costs no Heart"

    def test_cancel_leaves_everything_alone(self, env):
        add_char(env, "White", "James", location="RaymanHouse")
        add_char(env, "Yellow", "Rayman", down=True, health=0, location="RaymanHouse")
        start_day(env)

        click(env, "onActStabilize", "White")
        click(env, "onDownedCancel", "White")
        assert env.eval("gameState.activeChars.Yellow.down") is True
        assert env.eval("gameState.pendingAction") is None
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3


# ---------------------------------------------------------------------------
# Ghost Drift (§16.4) — a Down player's only remaining decision. It rides the
# Reactions panel because a ghost is never the active player.
# ---------------------------------------------------------------------------


class TestGhostDrift:
    def test_a_ghost_gets_a_reaction_row(self, env):
        add_char(env, "White", "James")
        add_char(env, "Yellow", "Rayman", down=True, location="RaymanHouse")
        start_day(env)
        env.globals().refreshReactionsPanel()

        labels = [env.eval(f'UI.getAttribute("reactBtn_{i}", "text")') for i in (1, 2, 3)]
        assert any(lbl and "ghost" in lbl for lbl in labels), \
            f"no drift row offered to the ghost: {labels}"

    def test_drift_moves_the_ghost_once_per_round(self, env):
        add_char(env, "Yellow", "Rayman", down=True, location="RaymanHouse")
        add_char(env, "White", "James")
        start_day(env)

        env.execute('gameState.pendingAction = {type = "drift", color = "Yellow"}')
        env.execute('__tile = TTS.addObject({tags = {"Location:JamesHouse"}, position = {0,1,0}})')
        env.eval("onMoveTargetClick")(env.eval("__tile"), "Yellow", False)
        flush(env)

        assert env.eval("gameState.activeChars.Yellow.location") == "JamesHouse"
        assert env.eval('gameState.driftedThisRound.Yellow') is True

        ok, why = env.eval("canDrift")("Yellow")
        assert ok is False and "per round" in why

    def test_a_living_character_never_drifts(self, env):
        add_char(env, "White", "James")
        start_day(env)
        ok, why = env.eval("canDrift")("White")
        assert ok is False and "Down" in why

    def test_dawn_clears_the_round_flag(self, env):
        add_char(env, "White", "James")
        add_char(env, "Yellow", "Rayman", down=True)
        env.execute('gameState.started = true; gameState.driftedThisRound = {Yellow = true}')
        env.globals().BeginDay()
        flush(env)
        assert env.eval('gameState.driftedThisRound.Yellow') is None, \
            "drift is once per ROUND — Dawn must hand it back"


# ---------------------------------------------------------------------------
# Flee (§12.4) — the escape valve. doFlee was implemented and correct and
# reachable only from this suite: no button, no handler, no XML. Meanwhile
# canFight's refusal, the threat-draw warning, the Hunger tooltip, the
# notebook, What-now and the Active Rules panel all told players to use it.
# ---------------------------------------------------------------------------


class TestFlee:
    def _cornered(self, env, color="White", loc="BasketballCourt", **overrides):
        """A character with a real threat card on their tile."""
        add_char(env, color, "James", location=loc, **overrides)
        env.execute(
            '__here = TTS.addObject({tags = {"Location:%s"}, position = {0,1,0}})\n'
            '__there = TTS.addObject({tags = {"Location:EllieLucaHouse"}, position = {40,1,40}})\n'
            'TTS.addObject({tags = {"ThreatCard", "T_SHADOW_STALKER"}, type = "Card",\n'
            '               nickname = "Shadow Stalker", position = {1,1,1}})' % loc)
        start_day(env, color)

    def test_the_button_appears_only_when_something_is_there(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        env.execute('TTS.addObject({tags = {"Location:BasketballCourt"}, position = {0,1,0}})')
        start_day(env)
        ok, why = env.eval("canFlee")("White")
        assert ok is False and "flee from" in why

    def test_a_cornered_character_may_flee(self, env):
        self._cornered(env)
        assert env.eval("canFlee")("White") is True

    def test_starving_does_not_block_flee(self, env):
        """Hunger < 3 blocks Fight and never Flee — that is the whole rule."""
        self._cornered(env, hunger=1)
        assert env.eval("canFight")("White") is not True
        assert env.eval("canFlee")("White") is True

    def test_no_actions_left_does_not_block_flee(self, env):
        self._cornered(env, actionsLeft=0)
        assert env.eval("canFlee")("White") is True

    def test_a_down_character_cannot_flee(self, env):
        self._cornered(env, down=True)
        ok, why = env.eval("canFlee")("White")
        assert ok is False and "Down" in why

    def test_the_click_offers_tiles_and_the_target_runs(self, env):
        # No flush() between the two clicks: the stub runs every pending Wait
        # immediately, which would fire the 30s target timeout and clear the
        # pending action before the player could pick a tile.
        self._cornered(env, sanity=8)
        arm_flee(env)
        assert env.eval('gameState.pendingAction.type') == "flee"

        env.eval("onMoveTargetClick")(env.eval("__there"), "White", False)
        flush(env)
        assert env.eval("gameState.activeChars.White.location") == "EllieLucaHouse"
        assert env.eval("gameState.activeChars.White.sanity") == 7   # -1
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3  # never an action

    def test_last_nerve_makes_running_free(self, env):
        self._cornered(env, sanity=2)
        arm_flee(env)
        env.eval("onMoveTargetClick")(env.eval("__there"), "White", False)
        flush(env)
        assert env.eval("gameState.activeChars.White.sanity") == 2   # no cost
        assert any("last nerve" in m.lower() for m in broadcasts(env))

    def test_clicking_flee_twice_cancels(self, env):
        self._cornered(env)
        arm_flee(env)
        arm_flee(env)
        assert env.eval('gameState.pendingAction') is None

    def test_flee_refuses_a_tile_that_is_not_adjacent(self, env):
        self._cornered(env, loc="JamesHouse", sanity=8)
        env.execute("LOCATION_ADJACENCY = buildAdjacency('Star')")  # James -> hub only
        env.globals().doFlee("White", "BadmintonCourt")
        assert env.eval("gameState.activeChars.White.location") == "JamesHouse"
        assert env.eval("gameState.activeChars.White.sanity") == 8

    def test_flee_follows_the_shortcut_like_every_other_move(self, env):
        self._cornered(env, loc="JamesHouse", sanity=8)
        env.execute("LOCATION_ADJACENCY = buildAdjacency('Star')")
        env.execute("gameState.scenarioFlags = { shortcutPath = true }")
        env.execute('TTS.addObject({tags = {"Location:BadmintonCourt"}, position = {60,1,60}})')
        env.globals().doFlee("White", "BadmintonCourt")
        assert env.eval("gameState.activeChars.White.location") == "BadmintonCourt"


# ---------------------------------------------------------------------------
# Appease — the non-violent Treeguard resolution.
# ---------------------------------------------------------------------------


class TestAppeaseTreeguard:
    def test_sends_it_back_to_sleep_for_two_wood(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        start_day(env)
        give(env, "White", "Wood", 2)
        env.execute('gameState.treeguard = {active = true, location = "BasketballCourt"}')

        click(env, "onActAppease", "White")
        assert env.eval("gameState.treeguard.active") is False
        assert env.eval('getPlayerResources("White").Wood') == 0

    def test_needs_to_be_at_its_tile(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        start_day(env)
        give(env, "White", "Wood", 2)
        env.execute('gameState.treeguard = {active = true, location = "BasketballCourt"}')

        ok, why = env.eval("canAppeaseTreeguard")("White")
        assert ok is False and "BasketballCourt" in why

    def test_hidden_when_no_treeguard_is_awake(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        start_day(env)
        give(env, "White", "Wood", 2)
        env.globals().refreshSituationalButtons("White")
        assert "actAppease" not in enabled(env)


# ---------------------------------------------------------------------------
# The bar itself: none of these may take up space when they don't apply.
# ---------------------------------------------------------------------------


def test_a_plain_turn_shows_no_situational_buttons(env):
    """Seven new buttons that were always visible would be seven buttons of
    noise on a bar that already carries fourteen."""
    add_char(env, "White", "James")
    start_day(env)
    env.globals().refreshSituationalButtons("White")

    ids = {e["id"] for e in lua_to_py(env.eval("SITUATIONAL_ACTIONS"))}
    assert ids and not (ids & enabled(env)), \
        f"situational buttons shown with nothing to use them on: {ids & enabled(env)}"


def test_every_situational_button_has_a_tooltip_either_way(env):
    """A hidden button still writes its why-disabled tooltip: that text is
    what the Help panel and the hover delay both read."""
    add_char(env, "White", "James")
    start_day(env)
    env.globals().refreshSituationalButtons("White")

    tips = lua_to_py(env.eval("ACTION_TOOLTIPS"))
    for entry in lua_to_py(env.eval("SITUATIONAL_ACTIONS")):
        tip = tips.get(entry["id"])
        assert tip, f"{entry['id']} has no tooltip"
        assert "Unavailable:" in tip, \
            f"{entry['id']} is hidden but its tooltip does not say why: {tip!r}"
