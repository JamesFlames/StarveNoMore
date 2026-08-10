"""Soft threats resolve, and then they leave.

`drawThreatsAt` has always announced "X is a soft threat — resolves and
discards". It did neither, and the second half was the expensive one:

  * a Soft card has `hp = 0`, and `fightTargetsAt` filters those out, so it
    could never be fought;
  * nothing else removed it, so it stayed on the tile all week;
  * and `countFesteringThreats` counts every ThreatCard near a tile — so each
    one charged +1 Doom at every Dawn for the rest of the game, with no
    counterplay available at any price.

Twenty cards, each with a printed effect that never fired, each converting
instead into permanent Doom pressure. This module checks both halves: the
effect happens, and the card goes away.
"""
import csv
import os
import re

import pytest
from conftest import CONTENT, LUA_DIR, add_char, broadcasts, lua52, py_to_lua, read_text

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


def _soft_ids():
    with open(os.path.join(CONTENT, "cards_threats.csv"), encoding="utf-8") as f:
        return [r["id"] for r in csv.DictReader(f) if r["type"] == "Soft"]


def _table_ids(name):
    src = read_text(os.path.join(LUA_DIR, "threat_effects.lua"))
    body = src.split(name + " = {", 1)[1].split("\n}", 1)[0]
    return set(re.findall(r"^\s*(T_[A-Z0-9_]+)\s*=", body, re.M))


# ---------------------------------------------------------------------------
# The roster: every Soft card is scripted or explicitly a table judgement.
# ---------------------------------------------------------------------------


def test_every_soft_threat_is_scripted_or_declared_manual():
    soft = set(_soft_ids())
    covered = _table_ids("SOFT_THREAT_EFFECTS") | _table_ids("MANUAL_SOFT")
    missing = sorted(soft - covered)
    assert not missing, (
        f"{len(missing)} Soft threat(s) with a printed effect and no entry:\n  "
        + "\n  ".join(missing)
        + "\n\nAdd a SOFT_THREAT_EFFECTS function (lua/threat_effects.lua), or "
          "a MANUAL_SOFT line if the card asks the table for a judgement the "
          "script has no basis to make. Every Soft card is discarded either "
          "way — the resolution is what needs deciding."
    )


def test_the_tables_name_only_real_soft_cards():
    soft = set(_soft_ids())
    for name in ("SOFT_THREAT_EFFECTS", "MANUAL_SOFT"):
        stale = sorted(_table_ids(name) - soft)
        assert not stale, (
            f"{name} names cards that are not Soft threats: {stale} — a Hard or "
            "Persistent card is fought or stays on the tile; it must not be "
            "auto-resolved and discarded.")


def test_no_card_is_both_scripted_and_manual():
    both = sorted(_table_ids("SOFT_THREAT_EFFECTS") & _table_ids("MANUAL_SOFT"))
    assert not both, (
        f"{both} appear in both tables — the table step would be announced on "
        "top of a scripted resolution, so players would apply it twice.")


# ---------------------------------------------------------------------------
# The behaviour.
# ---------------------------------------------------------------------------


class TestSoftResolution:
    def _tile(self, env, loc="BasketballCourt", pos=(0, 1, 0)):
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": [f"Location:{loc}"], "position": list(pos)}))

    def _fester(self, env):
        """countFesteringThreats returns (threats, bosses); we want the first."""
        return env.eval("(function() local n = countFesteringThreats() return n end)()")

    def _card(self, env, tid="T_WHISPERS", pos=(1, 1, 1)):
        env.execute(
            '__card = TTS.addObject({tags = {"ThreatCard", "%s", "ThreatType:Soft"}, '
            'type = "Card", nickname = "%s", position = {%g,%g,%g}})'
            % (tid, tid, *pos))
        return env.eval("__card")

    def test_a_resolved_card_leaves_the_tile(self, env):
        """The half that stopped the bleeding: while the card sat near the
        tile, countFesteringThreats charged +1 Doom every Dawn for it."""
        add_char(env, "White", "James", location="BasketballCourt")
        self._tile(env)
        card = self._card(env)
        env.globals().resolveSoftThreat("T_WHISPERS", "BasketballCourt", "Whispers", card)

        pos = env.eval("__card.getPosition()")
        assert pos["x"] < -10, "the card must end up off the map, not on the tile"
        assert self._fester(env) == 0

    def test_an_unresolved_card_would_have_festered(self, env):
        """Pins the mechanism this fix exists for — if this stops being true,
        the test above stops meaning anything."""
        add_char(env, "White", "James", location="BasketballCourt")
        self._tile(env)
        self._card(env)
        assert self._fester(env) == 1

    def test_whispers_costs_sanity_at_its_tile_only(self, env):
        add_char(env, "White", "James", location="BasketballCourt", sanity=8)
        add_char(env, "Green", "Ellie", location="JamesHouse", sanity=8)
        self._tile(env)
        env.globals().resolveSoftThreat("T_WHISPERS", "BasketballCourt", "Whispers", None)
        assert env.eval("gameState.activeChars.White.sanity") == 7
        assert env.eval("gameState.activeChars.Green.sanity") == 8

    def test_howling_reaches_everyone(self, env):
        add_char(env, "White", "James", location="BasketballCourt", sanity=8)
        add_char(env, "Green", "Ellie", location="JamesHouse", sanity=8)
        env.globals().resolveSoftThreat("T_HOWLING", "BasketballCourt", "A Howling Outside", None)
        assert env.eval("gameState.activeChars.White.sanity") == 7
        assert env.eval("gameState.activeChars.Green.sanity") == 7

    def test_the_furnace_spares_the_courts(self, env):
        add_char(env, "White", "James", location="JamesHouse", health=8)
        add_char(env, "Yellow", "Rayman", location="BadmintonCourt", health=8)
        env.globals().resolveSoftThreat("T_FURNACE", "JamesHouse", "The Furnace", None)
        assert env.eval("gameState.activeChars.White.health") == 7
        assert env.eval("gameState.activeChars.Yellow.health") == 8

    def test_the_doorbell_is_heard_indoors_and_nowhere_else(self, env):
        """It used to read "the player at the front-most house tile" — no such
        tile exists, so the card asked the table to invent one. Everyone in a
        house hears it; the courts do not."""
        add_char(env, "White", "James", location="JamesHouse", sanity=8)
        add_char(env, "Green", "Ellie", location="EllieLucaHouse", sanity=8)
        add_char(env, "Yellow", "Rayman", location="BadmintonCourt", sanity=8)
        env.globals().resolveSoftThreat("T_RUNG_DOORBELL", "JamesHouse", "The Doorbell Rang", None)
        assert env.eval("gameState.activeChars.White.sanity") == 7
        assert env.eval("gameState.activeChars.Green.sanity") == 7
        assert env.eval("gameState.activeChars.Yellow.sanity") == 8

    def test_voices_charges_one_per_ally_elsewhere(self, env):
        add_char(env, "White", "James", location="JamesHouse", sanity=8)
        add_char(env, "Green", "Ellie", location="RaymanHouse", sanity=8)
        add_char(env, "Yellow", "Rayman", location="BadmintonCourt", sanity=8)
        env.globals().resolveSoftThreat("T_VOICES", "JamesHouse", "Voices", None)
        # each is alone, so each hears the other two
        assert env.eval("gameState.activeChars.White.sanity") == 6

    def test_voices_is_silent_when_nobody_is_apart(self, env):
        add_char(env, "White", "James", location="JamesHouse", sanity=8)
        add_char(env, "Green", "Ellie", location="JamesHouse", sanity=8)
        env.globals().resolveSoftThreat("T_VOICES", "JamesHouse", "Voices", None)
        assert env.eval("gameState.activeChars.White.sanity") == 8

    def test_lights_out_reaches_the_night_light_check(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        self._tile(env, "JamesHouse")
        env.execute('TTS.setHand("White", { TTS.makeObject({tags={"M_FLASHLIGHT"}}) })')
        assert env.globals().checkPlayerHasLight("White") is True
        env.globals().resolveSoftThreat("T_LIGHTS_OUT", "JamesHouse", "Lights Out", None)
        assert env.globals().checkPlayerHasLight("White") is False

    def test_fire_out_kills_a_lantern_anywhere(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        self._tile(env, "JamesHouse")
        env.execute('TTS.setHand("White", { TTS.makeObject({tags={"M_LANTERN"}}) })')
        assert env.globals().checkPlayerHasLight("White") is True
        env.globals().resolveSoftThreat("T_FIRE_OUT", "JamesHouse", "The Fire Goes Out", None)
        assert env.globals().checkPlayerHasLight("White") is False

    def test_food_gone_wrong_takes_food_at_the_tile(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        env.globals().giveResource("White", "Provisions", 2)
        env.globals().resolveSoftThreat("T_FOOD_GONE_WRONG", "JamesHouse", "Food Gone Wrong", None)
        assert env.eval('getPlayerResources("White").Provisions') == 1

    def test_clock_stops_shortens_tomorrow(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.turnOrder = {"White"}')
        env.globals().resolveSoftThreat("T_CLOCK_STOPS", "JamesHouse", "The Clock Stops", None)
        env.globals().beginDayPhase()
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2

    def test_a_manual_card_announces_its_step_and_still_discards(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        self._tile(env, "JamesHouse")
        card = self._card(env, "T_FRIEND_BLOOD")
        env.globals().resolveSoftThreat("T_FRIEND_BLOOD", "JamesHouse", "Friend's Blood", card)
        assert any("TABLE STEP" in m for m in broadcasts(env))
        assert env.eval("__card.getPosition()")["x"] < -10

    def test_an_unknown_id_still_gets_discarded(self, env):
        """A Soft card the tables miss must not become permanent Doom."""
        add_char(env, "White", "James", location="JamesHouse")
        self._tile(env, "JamesHouse")
        card = self._card(env, "T_NOT_A_REAL_CARD")
        env.globals().resolveSoftThreat("T_NOT_A_REAL_CARD", "JamesHouse", "???", card)
        assert env.eval("__card.getPosition()")["x"] < -10


# ---------------------------------------------------------------------------
# Placement: two threats at one tile must not become one Deck.
# ---------------------------------------------------------------------------


def test_threats_at_one_tile_land_on_separate_spots(env):
    """Cards dropped within a card's own footprint of each other MERGE in TTS,
    and the engine replaces both with a Deck. fightTargetsAt only accepts
    `obj.type == "Card"`, so a merged threat cannot be fought — while
    countFesteringThreats still charges Doom for it every Dawn. A live game
    ended with three of these piles (one holding six cards), "Threats
    defeated: 0", and Doom at 30/30 on Day 7."""
    env.eval("TTS.addObject")(py_to_lua(env, {
        "tags": ["Location:BasketballCourt"], "position": [0, 1, 0]}))

    spots = []
    for n in range(6):
        p = dict(env.globals().threatSpotAt("BasketballCourt", n))
        spots.append((p["x"], p["z"]))

    # A TTS card is ~2.4 x 3.4; closer than that in BOTH axes and they merge.
    for i, a in enumerate(spots):
        for b in spots[i + 1:]:
            assert abs(a[0] - b[0]) >= 2.4 or abs(a[1] - b[1]) >= 3.4, (
                f"threat spots {a} and {b} overlap — TTS will merge those cards "
                "into an unfightable Deck")

    # ...and every one is still close enough to the tile to BE a threat:
    # fightTargetsAt only sees cards within FIGHT_RADIUS of the tile centre.
    r = env.eval("FIGHT_RADIUS")
    for x, z in spots:
        assert (x * x + z * z) ** 0.5 <= r, (
            f"spot ({x}, {z}) is outside FIGHT_RADIUS {r} — a card there cannot "
            "be fought, only festered")


def test_the_next_threat_counts_the_ones_already_there(env):
    """The old offset was indexed by the LOOP counter, so a second call at the
    same tile — the Eye of Terror's Dawn stare, or simply the next night —
    started over at spot 0 and dropped a card straight onto the last one."""
    env.eval("TTS.addObject")(py_to_lua(env, {
        "tags": ["Location:BasketballCourt"], "position": [0, 1, 0]}))
    assert env.globals().threatsPlacedAt("BasketballCourt") == 0

    first = dict(env.globals().threatSpotAt("BasketballCourt", 0))
    env.execute('TTS.addObject({tags = {"ThreatCard"}, type = "Card", '
                'nickname = "T1", position = {%g, %g, %g}})'
                % (first["x"], first["y"], first["z"]))
    assert env.globals().threatsPlacedAt("BasketballCourt") == 1, (
        "a card already on the tile was not counted, so the next one lands on it")
