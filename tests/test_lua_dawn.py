"""Dawn card effects: Last Dawn, Night Sounds, Dawn Dares, the Wrongness, per-card effects.

Headless execution of the real game Lua under Lua 5.2 (lupa) with the TTS
stub. The bundle harness (env fixture, add_char, script_dice, ...) lives in
tests/conftest.py; split out of the former monolithic test_lua_runtime.py.
"""
import json as _json
import os

import pytest

from conftest import (
    lua52, make_env, add_char, broadcasts, flush, lua_to_py, py_to_lua,
    script_dice, populate_full_world,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


class TestLastDawn:
    def _phase4_deck(self, env, cards=6):
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["PhaseCard:P4Deck"], "position": [50, 1, 0],
            "contained": [{"nickname": f"P4_TEST_{i}", "tags": [f"P4_TEST_{i}"]} for i in range(cards)]}))

    def test_day7_reveals_last_dawn_without_drawing(self, env):
        self._phase4_deck(env)
        env.execute("gameState.day = 7; gameState.phase = 4")
        env.globals().revealDawnCard()
        flush(env)
        assert env.eval("gameState.activeDawn.id") == "LAST_DAWN"
        assert env.eval('getPhaseDeck(4).getQuantity()') == 6   # untouched
        assert any("THE LAST DAWN" in m for m in broadcasts(env))

    def test_day6_still_draws_from_the_deck(self, env):
        self._phase4_deck(env)
        env.execute("gameState.day = 6; gameState.phase = 4")
        env.globals().revealDawnCard()
        flush(env)
        assert env.eval('getPhaseDeck(4).getQuantity()') == 5
        assert env.eval("gameState.activeDawn.id") != "LAST_DAWN"

    def test_last_dawn_cleans_up_day6_ongoing_effects(self, env):
        env.execute("""
            gameState.day = 7
            gameState.ongoingDawnEffects.restNoSanity = true
            gameState.activeDawn = { id = "P4_DESPAIR", prevId = "P4_DESPAIR" }
        """)
        env.globals().revealDawnCard()
        assert env.eval("gameState.ongoingDawnEffects.restNoSanity") is None


# ---------------------------------------------------------------------------
# Night Sounds (design_batch3.md §1) — the Dusk growl peek
# ---------------------------------------------------------------------------


class TestNightSounds:
    def _dusk_world(self, env, top_nickname):
        add_char(env, "White", "James")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["ThreatCardDeck"], "position": [50, 1, 50],
            "contained": [{"nickname": top_nickname, "guid": "top1"},
                          {"nickname": "A Phone Rings", "guid": "top2"}]}))
        # record growls instead of driving the MusicPlayer stub
        env.execute("GROWLS = 0; Audio.playGrowl = function() GROWLS = GROWLS + 1 end")
        env.execute('gameState.turnOrder = {"White"}; gameState.started = true')

    def test_growl_when_top_threat_is_hard(self, env):
        self._dusk_world(env, "Shadow Stalker")   # Hard in cards_threats.csv
        env.globals().beginDusk()
        assert env.eval("GROWLS") == 1

    def test_no_growl_on_soft_top(self, env):
        self._dusk_world(env, "A Howling Outside")   # Soft
        env.globals().beginDusk()
        assert env.eval("GROWLS") == 0

    def test_no_growl_when_deck_missing(self, env):
        add_char(env, "White", "James")
        env.execute("GROWLS = 0; Audio.playGrowl = function() GROWLS = GROWLS + 1 end")
        env.globals().beginDusk()
        assert env.eval("GROWLS") == 0

    def test_threat_type_table_matches_csv(self, env):
        # spot-check the generated table against known rows
        assert env.eval('THREAT_TYPE_BY_NAME["Shadow Stalker"]') == "Hard"
        assert env.eval('THREAT_TYPE_BY_NAME["A Phone Rings"]') == "Soft"
        assert env.eval('THREAT_TYPE_BY_NAME["The Sealed Shed"]') == "Persistent"


# ---------------------------------------------------------------------------
# Dawn Dares (design_batch3.md §2)
# ---------------------------------------------------------------------------


class TestDawnDares:
    def test_court_glow_dare_adds_threats_at_courts(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        env.execute("gameState.ongoingDawnEffects.dareCourtGlow = true")
        env.eval("TTS.addObject")(py_to_lua(env, {"tags": ["Location:BasketballCourt"], "position": [10, 1, 10]}))
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["ThreatCardDeck"], "position": [50, 1, 50],
            "contained": [{"nickname": f"T{i}", "guid": f"t{i}"} for i in range(6)]}))
        env.globals().resolveNightAtLocation("BasketballCourt", py_to_lua(env, ["White"]))
        flush(env)
        # court base 1 + alone-at-court 1 + dare 2 = 4 draws
        assert any("Drawing 4 threat(s)" in m for m in broadcasts(env))
        assert any("floodlights hum" in m for m in broadcasts(env))

    def test_court_glow_does_not_touch_houses(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        env.execute("gameState.ongoingDawnEffects.dareCourtGlow = true")
        env.eval("TTS.addObject")(py_to_lua(env, {"tags": ["Location:JamesHouse"], "position": [0, 1, 0]}))
        env.globals().resolveNightAtLocation("JamesHouse", py_to_lua(env, ["White"]))
        flush(env)
        assert not any("floodlights hum" in m for m in broadcasts(env))

    def test_porch_light_dare_offered_then_taken(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        env.execute("gameState.ongoingDawnEffects.darePorchLight = true")
        env.globals().doGather("White")
        # the offer is a confirm dialog; accept it via the stored callback
        assert env.eval('TTS.ui.visible["confirmDialog"]') is True
        env.globals().onConfirmYes(py_to_lua(env, {"color": "White"}), "", "")
        assert env.eval("gameState.activeChars.White.sanity") == 8   # -2
        assert env.eval("gameState.ongoingDawnEffects.darePorchLight") is None
        assert any("2 extra resources" in m for m in broadcasts(env))

    def test_porch_light_dare_not_offered_at_courts(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        env.execute("gameState.ongoingDawnEffects.darePorchLight = true")
        env.globals().doGather("White")
        assert env.eval('TTS.ui.visible["confirmDialog"]') is not True
        assert env.eval("gameState.ongoingDawnEffects.darePorchLight") is True


# ---------------------------------------------------------------------------
# Pry & sealed things (Design §13.5, design_batch3.md §3)
# ---------------------------------------------------------------------------


class TestWrongness:
    def _place(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        add = env.eval("TTS.addObject")
        for loc, pos in [("JamesHouse", [-10, 1, 0]), ("EllieLucaHouse", [0, 1, 8]),
                         ("BasketballCourt", [-10, 1, -10])]:
            add(py_to_lua(env, {"tags": [f"Location:{loc}"], "position": pos}))
        add(py_to_lua(env, {"tags": ["ThreatCardDeck"], "position": [50, 1, 50],
                            "contained": [{"nickname": "Shadow Stalker", "guid": "wrong1",
                                           "tags": ["ThreatCard"]}]}))
        env.execute('DAWN_EFFECTS["P2_BASKETBALL_BOUNCE"].onReveal(TTS.makeObject({}))')
        flush(env)

    def test_placement_defers_resolution(self, env):
        self._place(env)
        w = lua_to_py(env.eval("gameState.wrongness"))
        assert w["location"] == "BasketballCourt"
        assert w["placedDay"] == 1
        # unresolved: the reveal messages have not fired
        assert not any("Shadow Stalker" in m for m in broadcasts(env))

    def test_pending_wrongness_does_not_fester(self, env):
        self._place(env)
        threat_fester, _boss = env.globals().countFesteringThreats()
        assert threat_fester == 0

    def test_entering_the_tile_resolves_it(self, env):
        self._place(env)
        env.execute('gameState.activeChars.White.location = "EllieLucaHouse"')
        env.globals().doMove("White", "BasketballCourt")
        assert env.eval("gameState.wrongness") is None
        assert any("You went to look" in m and "Shadow Stalker" in m for m in broadcasts(env))
        # revealed and standing: now it festers like any threat
        threat_fester, _boss = env.globals().countFesteringThreats()
        assert threat_fester == 1

    def test_unvisited_wrongness_resolves_at_next_dawn(self, env):
        self._place(env)
        env.execute("gameState.day = 2; gameState.playerCount = 1; "
                    "gameState.started = true; gameState.turnOrder = {'White'}")
        env.globals().BeginDay()
        flush(env)
        assert env.eval("gameState.wrongness") is None
        assert any("Nobody went to look" in m for m in broadcasts(env))

    def test_pending_wrongness_survives_save_load(self, env):
        self._place(env)
        saved = env.globals().onSave()
        env.globals().onLoad(saved)
        w = lua_to_py(env.eval("gameState.wrongness"))
        assert w["location"] == "BasketballCourt"
        assert w["guid"] == "wrong1"


# ---------------------------------------------------------------------------
# Session telemetry (design_batch4.md W0)
# ---------------------------------------------------------------------------


class TestDawnEffects:
    def test_every_dawn_effect_reveals_cleanly(self, env):
        """Run onReveal(card) and (if present) onCleanup() for every
        DAWN_EFFECTS entry against a minimal populated world — the same calls
        dispatchDawnEffect makes. safecall-swallowed edge cases are fine; a
        hard Lua error here is a broken card."""
        env.globals().onLoad("")
        flush(env)
        for color, name in [("White", "James"), ("Red", "Coco"), ("Yellow", "Rayman"),
                            ("Green", "Ellie"), ("Blue", "Luca")]:
            add_char(env, color, name, location="JamesHouse")
        env.execute("gameState.playerCount = 5; gameState.started = true")
        for loc in ["JamesHouse", "RaymanHouse", "EllieLucaHouse", "BasketballCourt", "BadmintonCourt"]:
            env.eval("TTS.addObject")(py_to_lua(env, {"tags": [f"Location:{loc}"], "position": [0, 1, 0]}))
        result = lua_to_py(env.execute("""
            local failures, ran = {}, 0
            for id, eff in pairs(DAWN_EFFECTS) do
                local card = TTS.makeObject({ tags = { id }, nickname = id })
                if type(eff.onReveal) == "function" then
                    ran = ran + 1
                    local ok, err = pcall(eff.onReveal, card)
                    if not ok then failures[#failures + 1] = id .. ": " .. tostring(err) end
                end
                if type(eff.onCleanup) == "function" then
                    local ok, err = pcall(eff.onCleanup)
                    if not ok then failures[#failures + 1] = id .. " (cleanup): " .. tostring(err) end
                end
                TTS.flushWaits()
            end
            return { failures = failures, ran = ran }
        """))
        failures = result.get("failures") or []
        if isinstance(failures, dict):
            failures = list(failures.values())
        assert not failures, "Dawn effects that hard-error:\n" + "\n".join(failures)
        # guard against vacuous passes if the DAWN_EFFECTS shape ever changes
        assert result["ran"] >= 50, f"only {result['ran']} onReveal handlers ran — API shape changed?"


# ---------------------------------------------------------------------------
# Character perks + scripted Fight (2026-07: the briefing promises, delivered)
# ---------------------------------------------------------------------------
