"""Dawn card effects: Last Dawn, Night Sounds, Dawn Dares, the Wrongness, per-card effects.

Headless execution of the real game Lua under Lua 5.2 (lupa) with the TTS
stub. The bundle harness (env fixture, add_char, script_dice, ...) lives in
tests/conftest.py; split out of the former monolithic test_lua_runtime.py.
"""

import pytest
from conftest import (
    add_char,
    broadcasts,
    flush,
    lua52,
    lua_to_py,
    py_to_lua,
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


class TestSupplyDrop:
    def test_supply_drop_delivers_tokens_and_draws_a_threat(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:EllieLucaHouse"], "position": [0, 1, 8]}))
        for res in ["Metal", "Cloth"]:
            add(py_to_lua(env, {"tags": [f"ResourceBag:{res}"], "position": [60, 1, 60],
                                "contained": [{"nickname": res, "tags": ["Resource", f"Resource:{res}"]}] * 4}))
        add(py_to_lua(env, {"tags": ["ThreatCardDeck"], "position": [50, 1, 50],
                            "contained": [{"nickname": "Shadow Stalker", "guid": "sd1",
                                           "tags": ["ThreatCard"]}]}))
        env.execute('DAWN_EFFECTS["P2_SUPPLY_DROP"].onReveal(TTS.makeObject({}))')
        flush(env)
        assert env.eval('#findAllByTag("Resource:Metal")') == 1
        assert env.eval('#findAllByTag("Resource:Cloth")') == 1
        assert env.eval('#findAllByTag("ThreatCard")') == 1   # drawn onto the map


# ---------------------------------------------------------------------------
# Dead handles in the reveal callback (docs/tts-runtime.md)
# ---------------------------------------------------------------------------


class TestDawnRevealSurvivesDeadHandles:
    """2026-07-25 playtest: the Dawn card never resolved — no "DAWN:" line, just
    "(Edge case in DawnReveal - continuing.) cannot access field getNickname of
    userdata<LuaObject>". takeObject's callback got a handle whose card had
    merged into a deck mid-flight, and the re-find recovery failed too, because
    what sits on the reveal spot afterwards is a deck, not a card. The reveal
    now snapshots the card's identity while the handle is still known good.

    These tests model the real TTS ordering the stub does not reproduce: with
    smooth = true the callback fires LATER, after takeObject has returned.
    """

    def _phase1_deck(self, env, n=5):
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["PhaseCard:P1Deck"], "position": [50, 1, 0],
            "contained": [{"nickname": "P1_QUIET_EVENING",
                           "tags": ["P1_QUIET_EVENING"]} for _ in range(n)]}))
        # Day 2, not 1: Day 1's Dawn is the scripted First Dawn (§15.9) and
        # never touches the deck, so a deck-draw test must start on Day 2.
        env.execute("gameState.day = 2; gameState.phase = 1")

    _DEAD = """
        local dead = setmetatable({}, { __index = function()
            error("cannot access field getNickname of userdata<LuaObject>")
        end })
    """

    def test_dawn_still_resolves_when_the_handle_dies_in_flight(self, env):
        self._phase1_deck(env)
        # takeObject returns a good handle now, delivers a dead one later.
        env.execute("""
            local deck = getPhaseDeck(1)
            local realTake = deck.takeObject
            deck.takeObject = function(params)
                local taken = realTake({ position = params.position })
                %s
                Wait.time(function() params.callback_function(dead) end, 0)
                return taken
            end
        """ % self._DEAD)

        env.globals().revealDawnCard()
        flush(env)

        msgs = broadcasts(env)
        assert not any("Edge case in DawnReveal" in m for m in msgs), msgs
        assert any("DAWN: P1_QUIET_EVENING" in m for m in msgs), msgs
        assert env.eval("gameState.activeDawn.id") == "P1_QUIET_EVENING"

    def test_dawn_degrades_cleanly_when_no_handle_survives(self, env):
        self._phase1_deck(env)
        # Nothing usable at all: no live handle, no snapshot, nothing on the spot.
        env.execute("""
            local deck = getPhaseDeck(1)
            deck.takeObject = function(params)
                %s
                Wait.time(function() params.callback_function(dead) end, 0)
                return dead
            end
        """ % self._DEAD)

        env.globals().revealDawnCard()
        flush(env)   # must not raise

        msgs = broadcasts(env)
        assert any("landed oddly" in m for m in msgs), msgs
        assert env.eval("gameState.activeDawn") is None


class TestPathVariants:
    """Picking a variant must change the walkable map AND repaint the board."""

    def _board(self, env):
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["MainBoard", "Board"], "position": [0, 0.96, 0],
            "nickname": "Main Board",
            "snapPoints": [{"position": {"x": 1, "y": 0, "z": 2}, "tags": ["Snap:Doom:0"]}]}))

    def test_star_and_sprawl_give_different_neighbours(self, env):
        self._board(env)
        env.globals().applyPathVariant("Star")
        star = lua_to_py(env.eval("LOCATION_ADJACENCY"))
        env.globals().applyPathVariant("Sprawl")
        sprawl = lua_to_py(env.eval("LOCATION_ADJACENCY"))

        # Star: the houses only reach the hub. Sprawl: they reach everything.
        assert sorted(star["JamesHouse"]) == ["EllieLucaHouse"]
        assert len(sprawl["JamesHouse"]) == 4
        assert env.eval("gameState.pathVariant") == "Sprawl"

    def test_the_board_image_follows_the_variant(self, env):
        self._board(env)
        env.globals().applyPathVariant("Linear")
        flush(env)
        img = env.eval('getMainBoard().getCustomObject().image')
        assert img and "main_board_linear" in img, img

    def test_snap_points_survive_the_board_reload(self, env):
        self._board(env)
        env.globals().applyPathVariant("Compact")
        flush(env)
        snaps = lua_to_py(env.eval("getMainBoard().getSnapPoints()"))
        assert snaps and snaps[0]["tags"] == ["Snap:Doom:0"], (
            "reload() destroys and respawns the board; without re-applying "
            "snap points the Doom marker loses its track")

    def test_an_unknown_variant_falls_back_instead_of_emptying_the_map(self, env):
        self._board(env)
        picked = env.globals().applyPathVariant("NotARealLayout")
        adj = lua_to_py(env.eval("LOCATION_ADJACENCY"))
        assert picked == "Ring"
        assert all(len(v) > 0 for v in adj.values()), \
            "a bad variant name must never leave every tile unreachable"


class TestVariantAwareQuickStart:
    """The Quick Start card described a 7-day/30-Doom game no matter which
    variant was chosen — wrong on every line during a 3-day Long Weekend."""

    def test_long_weekend_rewrites_the_numbers(self, env):
        env.execute('gameState.difficulty = "weekend"')
        text = env.globals().quickStartTextForVariant()
        assert "Survive 3 nights" in text, text[:200]
        assert "below 15" in text
        assert "Long Weekend" in text
        assert "Survive 7 nights" not in text

    def test_standard_still_reads_as_the_seven_day_game(self, env):
        env.execute('gameState.difficulty = "standard"')
        text = env.globals().quickStartTextForVariant()
        assert "Survive 7 nights" in text and "below 30" in text

    def test_the_physical_card_is_restamped(self, env):
        """The card gets the SHORT brief (a Notecard clips anything longer),
        so match on the numbers rather than the Notebook's phrasing."""
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["QuickStart"], "position": [14.5, 1.65, -14],
            "nickname": "Quick Start", "description": "stale 7-day text"}))
        env.execute('gameState.difficulty = "weekend"')
        env.globals().refreshQuickStartCard()
        desc = env.eval('findOneByTag("QuickStart").getDescription()')
        assert "3 nights" in desc, desc[:200]
        assert "Doom under 15" in desc, desc[:200]
        assert "7 nights" not in desc, desc[:200]


class TestOneOptionIsHighlighted:
    """'Always highlight the only thing they can do if they can only do one
    thing' — with a single action offered, point at that button, not the bar."""

    def _day(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.started = true; gameState.subPhase = "Day"; '
                    'gameState.activeColor = "White"')

    def test_a_single_offered_action_is_the_cta(self, env):
        self._day(env)
        env.execute('ENABLED_ACTIONS = { actGather = true }')
        assert lua_to_py(env.globals().getNextCTA()) == ["actGather"]

    def test_several_options_highlight_the_whole_bar(self, env):
        self._day(env)
        env.execute('ENABLED_ACTIONS = { actGather = true, actMove = true }')
        assert lua_to_py(env.globals().getNextCTA()) == ["actionBar"]

    def test_out_of_actions_points_at_end_turn(self, env):
        self._day(env)
        env.execute('gameState.activeChars.White.actionsLeft = 0')
        assert lua_to_py(env.globals().getNextCTA()) == ["actPass"]


class TestTheFirstDawnAndTheGuidedOpening:
    """Day 1 is scripted (§15.9), and each player gets one concrete three-action
    plan on their first turn — the highest-value, lowest-cost onboarding
    intervention available (§22), aimed at the turn with the least context and
    the widest option set.
    """

    def test_day_one_never_draws_from_the_phase_deck(self, env):
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["PhaseCard:P1Deck"], "position": [50, 1, 0],
            "contained": [{"nickname": "P1_PHONES_DEAD", "tags": ["P1_PHONES_DEAD"]}
                          for _ in range(5)]}))
        env.execute("gameState.day = 1; gameState.phase = 1")
        before = env.eval("getPhaseDeck(1).getQuantity()")

        env.globals().revealDawnCard()
        flush(env)

        assert env.eval("getPhaseDeck(1).getQuantity()") == before, (
            "Day 1 drew a card — the Phase 1 deck should only have to cover Day 2")
        assert env.eval("gameState.activeDawn.id") == "FIRST_DAWN"
        assert any("FIRST MORNING" in m for m in broadcasts(env))

    def test_the_first_dawn_carries_no_penalty(self, env):
        add_char(env, "White", "Coco")
        env.execute("gameState.day = 1; gameState.phase = 1")
        before = tuple(env.eval(f"gameState.activeChars.White.{s}")
                       for s in ("health", "hunger", "sanity"))
        env.globals().revealDawnCard()
        flush(env)
        after = tuple(env.eval(f"gameState.activeChars.White.{s}")
                      for s in ("health", "hunger", "sanity"))
        assert before == after, "the guided opening must not cost anything"

    def test_each_character_has_a_three_action_opening(self, env):
        for name in ("James", "Coco", "Rayman", "Ellie", "Luca"):
            line = env.eval(f'OPENING_MOVES["{name}"]')
            assert line, f"{name} has no suggested opening"
            assert len(line) > 40, f"{name}'s opening is not a plan: {line!r}"

    def test_the_opening_is_offered_once_on_day_one(self, env):
        add_char(env, "Yellow", "Ellie")
        env.execute("gameState.day = 1")
        env.eval("offerOpeningSuggestion")("Yellow")
        first = [m for m in broadcasts(env) if "try:" in m]
        assert len(first) == 1, broadcasts(env)
        assert "Ellie" in first[0] and "Cook" in first[0]

        env.eval("offerOpeningSuggestion")("Yellow")
        assert len([m for m in broadcasts(env) if "try:" in m]) == 1, (
            "the opening suggestion repeated — it is for turn one only")

    def test_no_opening_suggestion_after_day_one(self, env):
        add_char(env, "Yellow", "Ellie")
        env.execute("gameState.day = 2")
        env.eval("offerOpeningSuggestion")("Yellow")
        assert not [m for m in broadcasts(env) if "try:" in m], (
            "still coaching the opening on Day 2")
