"""Hard threats: the printed special on the card is a rule something enforces.

The last of the three threat kinds to have its card text read by anything.
Eighteen Hard cards carry a `special` line and exactly **one** of them was
wired — `COMBAT_SPECIALS` held a single row (Your Roommate's Sanity cost) and
nothing else. Seventeen printed rules had no code anywhere.

One of them was the same permanent-Doom bug this repo has now fixed three
times. **The Grue has hp 0.** Its card says "Cannot be fought … Discard
after"; `fightTargetsAt` filters out hp 0, nothing else removed it, and
`countFesteringThreats` counts every Threat card near a tile — so it charged
+1 Doom at every Dawn for the rest of the week while the attack it prints
never happened. Soft cards fell in that hole, the hp-less Persistents fell in
it, and the Grue fell in it wearing a Hard card's clothes.

And one was an exploit rather than an omission: the Roommate's "1 Sanity per
attack die rolled" was charged only when `#participants == 1`, so **Fight
Together turned the cost off entirely** — on the one card in the deck whose
whole point is that hitting it hurts.

The roster tests pin that every printed special is scripted, declared a table
step, or declared inert with a reason. Silence is what made seventeen of these
invisible.
"""
import csv
import os
import re

import pytest
from conftest import (
    CONTENT,
    LUA_DIR,
    add_char,
    broadcasts,
    lua52,
    lua_to_py,
    py_to_lua,
    read_text,
    script_dice,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


def _threat_rows():
    with open(os.path.join(CONTENT, "cards_threats.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _hard_with_specials():
    return [r for r in _threat_rows()
            if r["type"] == "Hard" and r["special"].strip()]


def _row_ids():
    src = read_text(os.path.join(LUA_DIR, "threat_hard.lua"))
    body = src.split("HARD_THREAT_SPECIALS = {", 1)[1].split("\n}", 1)[0]
    return set(re.findall(r"^\s{4}(T_[A-Z0-9_]+)\s*=", body, re.M))


# ---------------------------------------------------------------------------
# The roster.
# ---------------------------------------------------------------------------


def test_every_hard_special_has_a_row():
    missing = sorted({r["id"] for r in _hard_with_specials()} - _row_ids())
    assert not missing, (
        f"{len(missing)} Hard threat(s) printing a special with no "
        f"HARD_THREAT_SPECIALS row:\n  " + "\n  ".join(missing)
        + "\n\nAdd one in lua/threat_hard.lua: scripted keys if the engine can "
          "enforce it, `manual` if the table must, or `inert` with the reason "
          "it is a no-op here. Leaving it out is how seventeen printed rules "
          "became invisible.")


def test_the_table_names_only_hard_cards():
    hard = {r["id"] for r in _threat_rows() if r["type"] == "Hard"}
    stale = sorted(_row_ids() - hard)
    assert not stale, (
        f"HARD_THREAT_SPECIALS names cards that are not Hard: {stale}. Soft "
        "cards resolve through SOFT_THREAT_EFFECTS and Persistent ones through "
        "PERSISTENT_THREAT_RULES; a card in two tables gets its rule twice.")


SCRIPTED_KEYS = {
    "sanityPerAttackDie", "sanityPerFight", "counterDice", "hesitationRoll",
    "houseTilesOnly", "onDrawSanityHere", "onDrawDamageHere", "charlieAttackHere",
    "discardAfter", "tickSanityAtTile", "gatherSanityAtTile", "nightSanityAtTile",
    "onDefeatDrawThreat",
}


def test_no_row_is_silent(env):
    """A row with neither a scripted key, a table step, nor a declared reason
    is the original bug with extra steps: a card that looks handled and does
    nothing."""
    for cid in sorted(_row_ids()):
        rule = lua_to_py(env.eval(f"HARD_THREAT_SPECIALS.{cid}"))
        keys = set(rule)
        assert (keys & SCRIPTED_KEYS) or "manual" in keys or "inert" in keys, (
            f"{cid} has a row but says nothing: {sorted(keys)}. Give it a "
            "scripted key, a `manual` step, or an `inert` reason.")
        if "inert" in keys:
            assert not (keys & SCRIPTED_KEYS), (
                f"{cid} is declared inert and also scripted — pick one.")


def test_the_scripted_keys_list_is_complete(env):
    """Guards the guard: a new scripted key that this module doesn't know
    about would let `test_no_row_is_silent` pass a row it can't see."""
    known = SCRIPTED_KEYS | {"manual", "inert", "blurb"}
    for cid in sorted(_row_ids()):
        rule = lua_to_py(env.eval(f"HARD_THREAT_SPECIALS.{cid}"))
        unknown = sorted(set(rule) - known)
        assert not unknown, (
            f"{cid} uses key(s) {unknown} that SCRIPTED_KEYS in this module "
            "has never heard of — add them here so the silence check keeps "
            "meaning something.")


# ---------------------------------------------------------------------------
# The Grue: hp 0, typed Hard, and therefore invisible to every removal path.
# ---------------------------------------------------------------------------


class TestTheGrue:
    def _tile(self, env, loc="BasketballCourt", pos=(0, 1, 0)):
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": [f"Location:{loc}"], "position": list(pos)}))

    def _card(self, env, pos=(1, 1, 1)):
        env.execute(
            '__g = TTS.addObject({tags = {"ThreatCard", "T_THE_GRUE", "ThreatType:Hard"}, '
            'type = "Card", nickname = "The Grue (Charlie)", position = {%g,%g,%g}})' % pos)
        return env.eval("__g")

    def _fester(self, env):
        return env.eval("(function() local n = countFesteringThreats() return n end)()")

    def test_it_is_not_a_fight_target(self, env):
        """hp 0 — this is why nothing could ever remove it."""
        assert env.eval("THREAT_STATS.T_THE_GRUE.hp") == 0
        add_char(env, "White", "James", location="BasketballCourt")
        self._tile(env)
        self._card(env)
        assert env.eval("#fightTargetsAt('BasketballCourt')") == 0

    def test_it_bites_and_leaves(self, env):
        add_char(env, "White", "James", location="BasketballCourt", sanity=10, health=8)
        self._tile(env)
        card = self._card(env)
        script_dice(env, [8, 6])   # 1d8 Sanity, 1d6 Health, as the card prints
        spent = env.globals().resolveHardThreatDraw(
            "T_THE_GRUE", "BasketballCourt", "The Grue (Charlie)", card)
        assert spent is True, "the card resolves instead of becoming a fight"
        assert env.eval("gameState.activeChars.White.sanity") == 2
        assert env.eval("gameState.activeChars.White.health") == 2
        assert env.eval("__g.getPosition()")["x"] < -10, "and then it goes"
        assert self._fester(env) == 0

    def test_an_unresolved_grue_would_have_festered(self, env):
        """Pins the mechanism: while its card sat there, every Dawn cost +1
        Doom and no action in the game could stop it."""
        add_char(env, "White", "James", location="BasketballCourt")
        self._tile(env)
        self._card(env)
        assert self._fester(env) == 1

    def test_it_spares_coco(self, env):
        """It resolves *a Charlie attack*, and Coco's Night Vision is immunity
        to Charlie — resolveCharlieAttack has always said so."""
        add_char(env, "White", "Coco", location="BasketballCourt", sanity=12)
        self._tile(env)
        env.globals().resolveHardThreatDraw("T_THE_GRUE", "BasketballCourt", "The Grue", None)
        assert env.eval("gameState.activeChars.White.sanity") == 12

    def test_it_only_bites_its_own_tile(self, env):
        add_char(env, "White", "James", location="BasketballCourt", sanity=10)
        add_char(env, "Green", "Ellie", location="JamesHouse", sanity=8)
        self._tile(env)
        script_dice(env, [4, 2])
        env.globals().resolveHardThreatDraw("T_THE_GRUE", "BasketballCourt", "The Grue", None)
        assert env.eval("gameState.activeChars.White.sanity") == 6
        assert env.eval("gameState.activeChars.Green.sanity") == 8


# ---------------------------------------------------------------------------
# Riders inside a fight.
# ---------------------------------------------------------------------------


class TestCombatRiders:
    def test_the_roommate_bills_every_attacker_in_a_group(self, env):
        """The exploit: the per-die Sanity cost used to apply only when
        exactly one character swung, so Fight Together bought it off."""
        add_char(env, "White", "James", sanity=10)
        add_char(env, "Green", "Ellie", sanity=8)
        script_dice(env, [3, 3])          # two whiffs; the counter is irrelevant
        env.globals().beginCombat(
            py_to_lua(env, ["White", "Green"]),
            py_to_lua(env, {"name": "Your Roommate (Wrong)", "hp": 9, "attack": 0,
                            "sanityPerAttackDie": 1}))
        # 1 attack die each (no weapons, not Rayman) → 1 Sanity each.
        assert env.eval("gameState.activeChars.White.sanity") == 9
        assert env.eval("gameState.activeChars.Green.sanity") == 7

    def test_the_roommate_bills_per_die_not_per_fighter(self, env):
        """Rayman rolls 2 base dice, so he pays 2."""
        add_char(env, "Yellow", "Rayman", sanity=6, location="JamesHouse")
        script_dice(env, [3, 3])
        env.globals().beginCombat(
            py_to_lua(env, ["Yellow"]),
            py_to_lua(env, {"name": "Your Roommate (Wrong)", "hp": 9, "attack": 0,
                            "sanityPerAttackDie": 1}))
        assert env.eval("gameState.activeChars.Yellow.sanity") == 4

    def test_the_childs_shadow_bills_a_flat_one_however_many_dice(self, env):
        """'1 Sanity per attack', not per die — a different, cheaper shape
        than the Roommate's bill, which is why it is a separate key."""
        add_char(env, "Yellow", "Rayman", sanity=6, location="JamesHouse")
        script_dice(env, [3, 3])
        env.globals().beginCombat(
            py_to_lua(env, ["Yellow"]),
            py_to_lua(env, {"name": "A Child's Shadow", "hp": 9, "attack": 0,
                            "sanityPerFight": 1}))
        assert env.eval("gameState.activeChars.Yellow.sanity") == 5

    def test_the_spider_thing_counters_with_two_dice(self, env):
        add_char(env, "White", "James", health=8)
        # attack whiffs, then the counter rolls TWO dice — both hits.
        script_dice(env, [3, 5, 5])
        env.globals().beginCombat(
            py_to_lua(env, ["White"]),
            py_to_lua(env, {"name": "Spider Thing", "hp": 9, "attack": 1,
                            "counterDice": 2}))
        assert env.eval("gameState.activeChars.White.health") == 6, (
            "counterDice must override the printed Attack column, not add to it")

    def test_without_the_rider_it_counters_with_one(self, env):
        add_char(env, "White", "James", health=8)
        script_dice(env, [3, 5])
        env.globals().beginCombat(
            py_to_lua(env, ["White"]),
            py_to_lua(env, {"name": "Ordinary", "hp": 9, "attack": 1}))
        assert env.eval("gameState.activeChars.White.health") == 7

    def test_the_doppelganger_can_stop_the_attack(self, env):
        add_char(env, "White", "James", sanity=10)
        env.execute("gameState.undoSnapshot = {day = 1}")
        script_dice(env, [4])          # 1-4 = hesitate
        assert env.globals().hardThreatHesitation("T_DOPPELGANGER", "White") is False
        assert env.eval("gameState.activeChars.White.sanity") == 9
        assert env.eval("gameState.undoSnapshot") is None, (
            "a hesitation is dice rolled in the open — Undo must not hand the "
            "action back and let the nerve check be rerolled until it passes")

    def test_the_doppelganger_lets_a_steady_hand_through(self, env):
        add_char(env, "White", "James", sanity=10)
        script_dice(env, [5])          # 5+ = act
        assert env.globals().hardThreatHesitation("T_DOPPELGANGER", "White") is True
        assert env.eval("gameState.activeChars.White.sanity") == 10

    def test_an_ordinary_threat_never_asks_for_a_hesitation_roll(self, env):
        add_char(env, "White", "James", sanity=10)
        assert env.globals().hardThreatHesitation("T_SHADOW_STALKER", "White") is True
        assert env.globals().hardThreatHesitation(None, "White") is True

    def test_the_thing_in_the_attic_will_not_come_out_to_a_court(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        ok = env.eval(
            "(function() local a, b = hardThreatBlocksFight('T_THING_IN_ATTIC', 'White') "
            "return a end)()")
        assert ok is False
        add_char(env, "Green", "Ellie", location="JamesHouse")
        ok2 = env.eval(
            "(function() local a, b = hardThreatBlocksFight('T_THING_IN_ATTIC', 'Green') "
            "return a end)()")
        assert ok2 is True


# ---------------------------------------------------------------------------
# Riders that fire on the draw, and the standing sweeps.
# ---------------------------------------------------------------------------


class TestStandingAndDrawRiders:
    def _world(self, env, cid, loc="JamesHouse", tile=(0, 1, 0), card=(1, 1, 1)):
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": [f"Location:{loc}"], "position": list(tile)}))
        env.execute(
            '__h = TTS.addObject({tags = {"ThreatCard", "%s", "ThreatType:Hard"}, '
            'type = "Card", nickname = "%s", position = {%g,%g,%g}})' % (cid, cid, *card))
        return env.eval("__h")

    def test_the_hollow_spectator_costs_sanity_on_entry(self, env):
        add_char(env, "White", "James", location="JamesHouse", sanity=10)
        add_char(env, "Green", "Ellie", location="RaymanHouse", sanity=8)
        spent = env.globals().resolveHardThreatDraw(
            "T_HOLLOW_SPECTATOR", "JamesHouse", "Hollow Spectator", None)
        assert spent is False, "it still has to be fought"
        assert env.eval("gameState.activeChars.White.sanity") == 9
        assert env.eval("gameState.activeChars.Green.sanity") == 8

    def test_the_wall_crawler_draws_blood_before_anyone_reacts(self, env):
        add_char(env, "White", "James", location="JamesHouse", health=8)
        env.globals().resolveHardThreatDraw(
            "T_WALL_CRAWLER", "JamesHouse", "Wall Crawler", None)
        assert env.eval("gameState.activeChars.White.health") == 7

    def test_the_shadow_stalker_taxes_the_tick_at_its_tile(self, env):
        # Coco, not James: James's Wired constraint costs him 2 more Sanity at
        # every Tick he hasn't had an Energy Drink, which would swamp the +1
        # this test is about.
        add_char(env, "White", "Coco", location="JamesHouse", sanity=12)
        add_char(env, "Green", "Ellie", location="RaymanHouse", sanity=8)
        self._world(env, "T_SHADOW_STALKER")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:RaymanHouse"], "position": [30, 1, 30]}))
        env.globals().resolveTick()
        # Base tick is -1 Sanity; the Stalker's tile pays 2.
        assert env.eval("gameState.activeChars.White.sanity") == 10
        assert env.eval("gameState.activeChars.Green.sanity") == 7

    def test_the_scarecrow_taxes_a_gather_at_its_tile(self, env):
        add_char(env, "White", "James", location="JamesHouse", sanity=10)
        self._world(env, "T_SCARECROW")
        env.globals().doGather("White")
        assert env.eval("gameState.activeChars.White.sanity") == 9

    def test_the_scarecrow_does_not_reach_the_next_tile(self, env):
        add_char(env, "White", "James", location="EllieLucaHouse", sanity=10)
        self._world(env, "T_SCARECROW", loc="JamesHouse")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:EllieLucaHouse"], "position": [30, 1, 30]}))
        env.globals().doGather("White")
        assert env.eval("gameState.activeChars.White.sanity") == 10

    def test_the_glass_child_cries_every_night(self, env):
        add_char(env, "White", "James", location="JamesHouse", sanity=10)
        add_char(env, "Green", "Ellie", location="RaymanHouse", sanity=8)
        self._world(env, "T_GLASS_CHILD")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:RaymanHouse"], "position": [30, 1, 30]}))
        env.globals().resolveHardThreatNight()
        assert env.eval("gameState.activeChars.White.sanity") == 8
        assert env.eval("gameState.activeChars.Green.sanity") == 8

    def test_the_glass_child_announces_the_step_the_script_cannot_take(self, env):
        env.globals().resolveHardThreatDraw(
            "T_GLASS_CHILD", "JamesHouse", "The Glass Child", None)
        said = " ".join(broadcasts(env))
        assert "TABLE STEP" in said and "Calm it" in said

    def test_the_black_dog_calls_its_mate(self, env):
        """'Hunters in pairs. When defeated draw another Threat card.'"""
        add_char(env, "White", "James", location="JamesHouse")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:JamesHouse"], "position": [0, 1, 0]}))
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["ThreatCardDeck"],
            "contained": [{"nickname": "Shadow Stalker", "guid": "bd1"}]}))
        env.globals().resolveHardThreatDefeat("T_BLACK_DOG", "JamesHouse")
        said = " ".join(broadcasts(env))
        assert "answers from the dark" in said
        assert "THREAT at JamesHouse" in said, (
            "the reinforcement must actually be drawn, not just announced — "
            f"broadcasts were:\n{said}")

    def test_an_ordinary_kill_calls_nothing(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        env.globals().resolveHardThreatDefeat("T_SHADOW_STALKER", "JamesHouse")
        assert not any("answers from the dark" in b for b in broadcasts(env))

    def test_the_fight_flow_carries_the_card_id_to_the_defeat_hook(self, env):
        """The rider fires from applyThreatDefeat, which can only find the
        card's row if doFightTarget put its id on the combat context."""
        add_char(env, "White", "James", location="JamesHouse")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:JamesHouse"], "position": [0, 1, 0]}))
        env.execute(
            '__d = TTS.addObject({tags = {"ThreatCard", "T_BLACK_DOG", "ThreatType:Hard"}, '
            'type = "Card", nickname = "Black Dog", position = {1,1,1}})')
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["ThreatCardDeck"],
            "contained": [{"nickname": "Shadow Stalker", "guid": "bd2"}]}))
        # Already chipped to 1 HP by an earlier fight, so James's single base
        # die finishes it and the defeat path runs.
        env.execute('gameState.threatDamage = {[__d.guid] = 2}')
        script_dice(env, [6])
        env.globals().doFightTarget("White", env.eval("__d"), False)
        said = " ".join(broadcasts(env))
        assert "is DEFEATED!" in said
        assert "answers from the dark" in said
