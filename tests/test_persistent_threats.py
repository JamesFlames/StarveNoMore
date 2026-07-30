"""Persistent threats do what they print, and every one of them can be removed.

Two bugs live here, and the first is why the second went unnoticed.

**Nothing was ever classified.** `identifyThreatType` (lua/night.lua) read only
`ThreatType:<type>` tags and GMNotes. `build_save.py` emits neither — a threat
card carries `["ThreatCard", "<CSV id>"]` and every object's GMNotes is `""` —
so every drawn card fell through to `return "Hard"`. That made the whole Soft
branch of `drawThreatsAt` dead code in the shipped mod (the cards
threat_effects.lua exists to resolve never resolved, and never discarded), and
it announced all thirteen Persistent cards as "must be fought or fled" when
eleven of them cannot be fought at all.

**Persistent cards did nothing, and six could not be removed at any price.**
The printed rules ("Move actions out of this tile cost 1 extra Hunger", "No
Food can be gathered at this tile", "each Tick eats 1 Food at this tile") had
no code behind them. Meanwhile `countFesteringThreats` counts every Threat card
near a tile, so each one charged +1 Doom at every Dawn, for ever: hp 0 means
`fightTargetsAt` filters it out, and only four of the seven hp-0 Persistents
are Sealed (removable by Pry). That is the soft-threat pathology again, with
the extra sting that a Persistent card is *meant* to stay — nothing was ever
going to take it off the tile.

So: the roster tests below pin that every Persistent card has a rule row AND a
removal path (Fight, Pry, or Clear), and the behaviour tests pin the rules.
"""
import csv
import json
import os
import re

import pytest
from conftest import (
    CONTENT,
    LUA_DIR,
    SAVES,
    add_char,
    broadcasts,
    lua52,
    lua_to_py,
    py_to_lua,
    read_text,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")

# Tile world positions (scripts/path_layouts.py LOCATION_WORLD) are irrelevant
# to these tests — each one places its own tile and puts the card on top of it.
TILE = (0, 1, 0)
ON_TILE = (1, 1, 1)


def _threat_rows():
    with open(os.path.join(CONTENT, "cards_threats.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _persistent_rows():
    return [r for r in _threat_rows() if r["type"] == "Persistent"]


def _rule_ids():
    src = read_text(os.path.join(LUA_DIR, "threat_persistent.lua"))
    body = src.split("PERSISTENT_THREAT_RULES = {", 1)[1].split("\n}", 1)[0]
    return set(re.findall(r"^\s{4}(T_[A-Z0-9_]+)\s*=", body, re.M))


# ---------------------------------------------------------------------------
# The roster: every Persistent card is described, and every one can be removed.
# ---------------------------------------------------------------------------


def test_every_persistent_threat_has_a_rule_row():
    missing = sorted({r["id"] for r in _persistent_rows()} - _rule_ids())
    assert not missing, (
        f"{len(missing)} Persistent threat(s) with no PERSISTENT_THREAT_RULES entry:\n  "
        + "\n  ".join(missing)
        + "\n\nAdd one in lua/threat_persistent.lua. A Persistent card with no "
          "row still sits on the tile costing +1 Doom every Dawn — it just does "
          "so with none of its printed rule applied and no way to be rid of it.")


def test_the_rule_table_names_only_persistent_cards():
    stale = sorted(_rule_ids() - {r["id"] for r in _persistent_rows()})
    assert not stale, (
        f"PERSISTENT_THREAT_RULES names cards that are not Persistent: {stale}. "
        "A Soft card is resolved and discarded; a Hard one is fought. Neither "
        "should acquire an ongoing tile rule.")


def test_every_persistent_threat_has_a_removal_path(env):
    """The bug this module is named for: six cards that could never leave.

    Fight (hp > 0), Pry (a pry_reward), or Clear (everything else). A card with
    none of the three is a permanent +1 Doom per Dawn with no counterplay.
    """
    for row in _persistent_rows():
        rule = env.eval(f"PERSISTENT_THREAT_RULES.{row['id']}")
        fought = bool(rule["fought"])
        sealed = bool(rule["sealed"])
        # Neither flag means Clear, which is always available — so the removal
        # path exists by construction. What can go wrong is a flag that does
        # not match the card, which advertises a verb that will refuse.
        assert fought == (int(row["hp"]) > 0), (
            f"{row['id']}: `fought` is {fought} but hp is {row['hp']} — Fight is "
            "offered for exactly the cards fightTargetsAt will accept.")
        assert sealed == bool(row["pry_reward"].strip()), (
            f"{row['id']}: `sealed` is {sealed} but pry_reward is "
            f"{row['pry_reward']!r} — Pry is offered for exactly the cards "
            "SEALED_REWARDS can pay out.")


def test_the_unfightable_unsealed_persistents_are_clearable(env):
    """Names the six cards the Clear action exists for, so a content change
    that adds a seventh has to notice it."""
    clearable = sorted(
        r["id"] for r in _persistent_rows()
        if int(r["hp"]) == 0 and not r["pry_reward"].strip())
    assert clearable == ["T_CONTAMINATED", "T_CRACKED_FLOOR", "T_FOG_BANK",
                         "T_NEST", "T_ROOTS", "T_SPIRAL", "T_WATCHER"]
    for cid in clearable:
        rule = env.eval(f"PERSISTENT_THREAT_RULES.{cid}")
        assert not rule["fought"] and not rule["sealed"]


# ---------------------------------------------------------------------------
# Classification — the root cause.
# ---------------------------------------------------------------------------


class TestIdentifyThreatType:
    def _card(self, env, tags, nickname="x"):
        env.execute(
            '__c = TTS.addObject({tags = {%s}, type = "Card", nickname = "%s", '
            'position = {1,1,1}})' % (", ".join(f'"{t}"' for t in tags), nickname))
        return env.eval("__c")

    @pytest.mark.parametrize("cid,ttype", [
        ("T_HOWLING", "Soft"), ("T_SHADOW_STALKER", "Hard"),
        ("T_CRACKED_FLOOR", "Persistent"), ("T_SEALED_SHED", "Persistent"),
    ])
    def test_the_id_tag_alone_is_enough(self, env, cid, ttype):
        """The shape the shipped save actually had: ThreatCard + the CSV id,
        empty GMNotes, no ThreatType tag. Every one of these used to come back
        "Hard"."""
        card = self._card(env, ["ThreatCard", cid])
        assert env.globals().identifyThreatType(card) == ttype

    def test_the_nickname_alone_is_enough(self, env):
        """Hand-placed cards, and anything whose tags were stripped."""
        card = self._card(env, ["ThreatCard"], nickname="A Howling Outside")
        assert env.globals().identifyThreatType(card) == "Soft"

    def test_an_explicit_type_tag_still_wins_for_unknown_cards(self, env):
        card = self._card(env, ["ThreatCard", "ThreatType:Soft"], nickname="Homebrew")
        assert env.globals().identifyThreatType(card) == "Soft"

    def test_an_unknown_card_is_hard(self, env):
        card = self._card(env, ["ThreatCard"], nickname="Homebrew")
        assert env.globals().identifyThreatType(card) == "Hard"


def test_the_built_save_labels_every_threat_card_with_its_type():
    """The save is now self-describing: identifyThreatType's first tag check
    finds a real answer even without the generated lookup table."""
    with open(os.path.join(SAVES, "StarveNoMore.json"), encoding="utf-8") as f:
        save = json.load(f)
    by_id = {r["id"]: r["type"] for r in _threat_rows()}
    seen = 0
    for obj in save["ObjectStates"]:
        if "ThreatCardDeck" not in (obj.get("Tags") or []):
            continue
        for card in obj.get("ContainedObjects") or []:
            tags = card.get("Tags") or []
            cid = next((t for t in tags if t in by_id), None)
            assert cid, f"threat card {card.get('Nickname')!r} carries no CSV id tag"
            assert f"ThreatType:{by_id[cid]}" in tags, (
                f"{cid} is missing its ThreatType tag: {tags}")
            seen += 1
    assert seen == len(_threat_rows())


# ---------------------------------------------------------------------------
# Behaviour: the printed rules apply.
# ---------------------------------------------------------------------------


class TestPersistentRules:
    def _world(self, env, cid, loc="JamesHouse", tile=TILE, card=ON_TILE):
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": [f"Location:{loc}"], "position": list(tile)}))
        env.execute(
            '__p = TTS.addObject({tags = {"ThreatCard", "%s", "ThreatType:Persistent"}, '
            'type = "Card", nickname = "%s", position = {%g,%g,%g}})'
            % (cid, cid, *card))
        return env.eval("__p")

    def test_the_registry_sees_a_card_on_the_tile(self, env):
        self._world(env, "T_WATCHER")
        found = env.eval("#persistentThreatsAt('JamesHouse')")
        assert found == 1
        assert env.eval("persistentThreatsAt('JamesHouse')[1].id") == "T_WATCHER"

    def test_a_card_off_the_tile_does_not_count(self, env):
        self._world(env, "T_WATCHER", card=(40, 1, 40))
        assert env.eval("#persistentThreatsAt('JamesHouse')") == 0

    def test_the_whole_board_pass_buckets_by_tile(self, env):
        """One table scan for the callers that want all five tiles (the Rules
        panel refreshes on every state change; the Tick runs nightly)."""
        self._world(env, "T_WATCHER", loc="JamesHouse")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:BadmintonCourt"], "position": [30, 1, 30]}))
        env.execute(
            '__q = TTS.addObject({tags = {"ThreatCard", "T_NEST"}, type = "Card", '
            'nickname = "T_NEST", position = {31,1,31}})')
        env.execute("__all = persistentThreatsEverywhere()")
        assert env.eval("#__all.JamesHouse") == 1
        assert env.eval("__all.JamesHouse[1].id") == "T_WATCHER"
        assert env.eval("#__all.BadmintonCourt") == 1
        assert env.eval("__all.BadmintonCourt[1].id") == "T_NEST"
        assert env.eval("__all.RaymanHouse") is None

    def test_the_rules_panel_names_the_card_and_the_way_out(self, env):
        """The card face is the only other place this rule is written, and it
        is face-up on a tile somebody has to walk over and read."""
        add_char(env, "White", "James", location="JamesHouse")
        env.execute("gameState.started = true")
        self._world(env, "T_FOG_BANK")
        env.eval("refreshRulesPanel()")
        body = lua_to_py(env.eval("TTS.ui"))["attrs"]["rulesBody"]["text"]
        assert "Fog Bank at JamesHouse" in body
        assert "Clear it: 2 actions + 1 Wood." in body

    def test_cracked_floor_charges_hunger_on_the_way_out(self, env):
        add_char(env, "White", "James", location="JamesHouse", hunger=6)
        self._world(env, "T_CRACKED_FLOOR")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:EllieLucaHouse"], "position": [30, 1, 30]}))
        env.globals().doMove("White", "EllieLucaHouse")
        # 1 Hunger for the move + 1 for the floor.
        assert env.eval("gameState.activeChars.White.hunger") == 4

    def test_the_surcharge_is_on_leaving_not_arriving(self, env):
        add_char(env, "White", "James", location="EllieLucaHouse", hunger=6)
        self._world(env, "T_CRACKED_FLOOR", loc="JamesHouse")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:EllieLucaHouse"], "position": [30, 1, 30]}))
        env.globals().doMove("White", "JamesHouse")
        assert env.eval("gameState.activeChars.White.hunger") == 5

    def test_fog_bank_charges_an_extra_action(self, env):
        add_char(env, "White", "James", location="JamesHouse", actionsLeft=3)
        self._world(env, "T_FOG_BANK")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:EllieLucaHouse"], "position": [30, 1, 30]}))
        env.globals().doMove("White", "EllieLucaHouse")
        assert env.eval("gameState.activeChars.White.actionsLeft") == 1

    def test_contaminated_water_keeps_food_off_the_tile(self, env):
        add_char(env, "White", "James", location="EllieLucaHouse")
        self._world(env, "T_CONTAMINATED", loc="EllieLucaHouse")
        # EllieLucaHouse yields {Food, Food, Cloth}; only the Cloth survives.
        for _ in range(6):
            env.globals().gatherRandomResources("White", "EllieLucaHouse", 1)
        held = env.eval("gameState.resources.White")
        assert held["Food"] == 0
        assert held["Cloth"] == 6

    def test_contaminated_water_doubles_the_cost_of_eating_raw(self, env):
        add_char(env, "White", "James", location="JamesHouse", sanity=10)
        self._world(env, "T_CONTAMINATED")
        env.globals().doEatRaw("White")
        assert env.eval("gameState.activeChars.White.sanity") == 8

    def test_roots_make_rest_restore_nothing(self, env):
        add_char(env, "White", "James", location="JamesHouse", hunger=2, sanity=2, health=2)
        self._world(env, "T_ROOTS")
        env.globals().doRest("White", "hunger")
        assert env.eval("gameState.activeChars.White.hunger") == 2
        assert env.eval("gameState.activeChars.White.health") == 2
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2, \
            "the action is still spent — the rule is that resting achieves nothing"

    def test_roots_forbid_a_barricade_without_charging_for_it(self, env):
        add_char(env, "White", "James", location="JamesHouse", actionsLeft=3)
        env.execute('gameState.resources = {White = {Wood = 3}}')
        self._world(env, "T_ROOTS")
        env.globals().doBarricade("White")
        assert env.eval("(gameState.barricades or {}).JamesHouse") is None
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3
        assert env.eval("gameState.resources.White.Wood") == 3
        ok = env.eval("(function() local a, b = canBarricade('White') return a end)()")
        assert ok is False

    def test_the_watcher_stops_a_trade(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        add_char(env, "Green", "Ellie", location="JamesHouse")
        self._world(env, "T_WATCHER")
        env.globals().doTrade("White", "Green")
        assert env.eval("(gameState.tradesThisTurn or {}).White") is None
        assert any("watching" in b for b in broadcasts(env))

    def test_the_nest_adds_a_threat_to_the_night_draw(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        self._world(env, "T_NEST", loc="BasketballCourt")
        env.globals().resolveNightAtLocation(
            "BasketballCourt", py_to_lua(env, ["White"]))
        # BasketballCourt's base rate is 1; alone there adds 1; the Nest adds 1.
        assert any("Drawing 3 threat(s)" in b for b in broadcasts(env))

    def test_the_hungry_dog_eats_at_tick(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        add_char(env, "Green", "Ellie", location="JamesHouse")
        env.execute('gameState.resources = {White = {Food = 1}, Green = {Food = 4}}')
        self._world(env, "T_HUNGRY_DOG")
        env.globals().resolvePersistentTick()
        # It takes from whoever has the most, not from whoever pairs() found first.
        assert env.eval("gameState.resources.Green.Food") == 3
        assert env.eval("gameState.resources.White.Food") == 1

    def test_the_hungry_dog_eats_only_at_its_own_tile(self, env):
        add_char(env, "White", "James", location="EllieLucaHouse")
        env.execute('gameState.resources = {White = {Food = 4}}')
        self._world(env, "T_HUNGRY_DOG", loc="JamesHouse")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:EllieLucaHouse"], "position": [30, 1, 30]}))
        env.globals().resolvePersistentTick()
        assert env.eval("gameState.resources.White.Food") == 4


# ---------------------------------------------------------------------------
# Clear: the removal path that did not exist.
# ---------------------------------------------------------------------------


class TestClear(TestPersistentRules):
    def _fester(self, env):
        return env.eval("(function() local n = countFesteringThreats() return n end)()")

    def test_an_uncleared_persistent_festers(self, env):
        """Pins the mechanism Clear exists for — six cards charged this every
        Dawn for the rest of the week with no way to stop it."""
        add_char(env, "White", "James", location="JamesHouse")
        self._world(env, "T_FOG_BANK")
        assert self._fester(env) == 1

    def test_clearing_takes_the_card_off_the_tile(self, env):
        add_char(env, "White", "James", location="JamesHouse", actionsLeft=3)
        env.execute('gameState.resources = {White = {Wood = 2}}')
        self._world(env, "T_FOG_BANK")
        assert env.globals().doClearPersistent("White") is True
        assert env.eval("__p.getPosition()")["x"] < -10
        assert env.eval("#persistentThreatsAt('JamesHouse')") == 0
        assert self._fester(env) == 0

    def test_clearing_costs_two_actions_and_a_wood(self, env):
        add_char(env, "White", "James", location="JamesHouse", actionsLeft=3)
        env.execute('gameState.resources = {White = {Wood = 2}}')
        self._world(env, "T_CRACKED_FLOOR")
        env.globals().doClearPersistent("White")
        assert env.eval("gameState.activeChars.White.actionsLeft") == 1
        assert env.eval("gameState.resources.White.Wood") == 1

    def test_one_action_is_not_enough(self, env):
        add_char(env, "White", "James", location="JamesHouse", actionsLeft=1)
        env.execute('gameState.resources = {White = {Wood = 2}}')
        self._world(env, "T_CRACKED_FLOOR")
        assert env.globals().doClearPersistent("White") is False
        assert env.eval("gameState.activeChars.White.actionsLeft") == 1
        assert env.eval("gameState.resources.White.Wood") == 2

    def test_no_wood_is_not_enough(self, env):
        add_char(env, "White", "James", location="JamesHouse", actionsLeft=3)
        env.execute('gameState.resources = {White = {Wood = 0}}')
        self._world(env, "T_CRACKED_FLOOR")
        assert env.globals().doClearPersistent("White") is False
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3

    def test_a_fightable_persistent_is_not_clearable(self, env):
        """The Lurker has 3 HP — Fight is its removal path, and Clear must not
        undercut it at a flat 2 actions + 1 Wood."""
        add_char(env, "White", "James", location="JamesHouse", actionsLeft=3)
        env.execute('gameState.resources = {White = {Wood = 5}}')
        self._world(env, "T_LURKER")
        ok = env.eval("(function() local a, b = canClearPersistent('White') return a end)()")
        assert ok is False
        assert env.globals().doClearPersistent("White") is False

    def test_a_sealed_persistent_is_not_clearable(self, env):
        """Pry pays out 3 Wood; Clear would let you bin the shed unopened for
        a Wood, which is the reward walking away."""
        add_char(env, "White", "James", location="JamesHouse", actionsLeft=3)
        env.execute('gameState.resources = {White = {Wood = 5}}')
        self._world(env, "T_SEALED_SHED")
        assert env.globals().doClearPersistent("White") is False


# ---------------------------------------------------------------------------
# The announcement on draw.
# ---------------------------------------------------------------------------


def test_a_persistent_draw_says_what_it_does_and_how_to_be_rid_of_it(env):
    env.globals().announcePersistentThreat("T_FOG_BANK", "Fog Bank", "JamesHouse")
    said = " ".join(broadcasts(env))
    assert "PERSISTENT" in said
    assert "extra action" in said
    assert "CLEAR it" in said


def test_a_sealed_draw_points_at_pry_not_at_fighting(env):
    env.globals().announcePersistentThreat("T_SEALED_CAR", "The Sealed Car", "JamesHouse")
    said = " ".join(broadcasts(env))
    assert "Pry" in said
    assert "Fight it" not in said


def test_a_fightable_draw_points_at_fighting(env):
    env.globals().announcePersistentThreat("T_LURKER", "Lurker", "JamesHouse")
    said = " ".join(broadcasts(env))
    assert "Fight it" in said
