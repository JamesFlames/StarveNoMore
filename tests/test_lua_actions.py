"""action verbs: pry, signatures, Nothing-Left-to-Lose buff, character perks.

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
    make_env,
    py_to_lua,
    script_dice,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


class TestPry:
    def _world(self, env, sealed_tag=None, basement=False):
        add_char(env, "White", "James", location="JamesHouse")
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:JamesHouse"], "position": [0, 1, 0]}))
        for res in ["Wood", "Metal", "Cloth", "Provisions", "EnergyDrink", "Battery"]:
            add(py_to_lua(env, {"tags": [f"ResourceBag:{res}"], "position": [60, 1, 60],
                                "contained": [{"nickname": res}] * 8}))
        add(py_to_lua(env, {"tags": ["MarketCardDeck"], "position": [55, 1, 55],
                            "contained": [{"nickname": "Duct Tape", "guid": "m1"}]}))
        if sealed_tag:
            add(py_to_lua(env, {"tags": ["ThreatCard", sealed_tag], "position": [1, 1, 1],
                                "nickname": "Sealed Thing"}))
        if basement:
            add(py_to_lua(env, {"tags": ["SealedBasement"], "position": [1, 1, -1],
                                "nickname": "The Sealed Basement"}))

    def _give_tool(self, env, nickname="Crowbar", tag="M_CROWBAR"):
        env.execute(f'TTS.setHand("White", {{ TTS.makeObject({{tags={{"{tag}"}}, nickname="{nickname}"}}) }})')

    def test_pry_refused_without_tool(self, env):
        self._world(env, sealed_tag="T_SEALED_SHED")
        assert env.globals().doPry("White") is False

    def test_pry_refused_with_nothing_sealed(self, env):
        self._world(env)
        self._give_tool(env)
        ok, _why = env.globals().canPry("White")
        assert ok is not True

    def test_pry_opens_sealed_shed(self, env):
        self._world(env, sealed_tag="T_SEALED_SHED")
        self._give_tool(env)
        assert env.globals().doPry("White") is True
        assert any("3 Wood" in m for m in broadcasts(env))
        assert env.eval('#findAllByTag("ThreatCard")') == 0   # the sealed card is gone

    def test_pry_the_door_draws_a_market_item(self, env):
        self._world(env, sealed_tag="T_THE_DOOR")
        self._give_tool(env, "Lockpick Set", "M_LOCKPICK")
        assert env.globals().doPry("White") is True
        flush(env)
        assert any("Duct Tape" in m for m in broadcasts(env))

    def test_basement_opens_once(self, env):
        self._world(env, basement=True)
        self._give_tool(env)
        assert env.globals().doPry("White") is True
        assert env.eval("gameState.basementOpened") is True
        assert any("basement cache" in m for m in broadcasts(env))
        # nothing sealed remains — a second pry is refused
        assert env.globals().doPry("White") is False

    def test_pry_is_a_free_action(self, env):
        self._world(env, sealed_tag="T_SEALED_SHED")
        self._give_tool(env)
        env.globals().doPry("White")
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3


# ---------------------------------------------------------------------------
# The Wrongness token (design_batch3.md §4)
# ---------------------------------------------------------------------------


class TestSignatures:
    def test_all_nighter_grants_actions_and_bills_at_next_tick(self, env):
        add_char(env, "White", "James")
        assert env.globals().doSignature("White") is True
        assert env.eval("gameState.activeChars.White.actionsLeft") == 6
        assert env.eval("gameState.activeChars.White.sanity") == 10   # not immediate
        assert env.eval("gameState.activeChars.White.signatureUsed") is True
        env.execute("gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        # tick -1, All-Nighter crash -3
        assert env.eval("gameState.activeChars.White.sanity") == 6
        # the bill is paid once — next tick is just the base decay
        env.execute("gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.White.sanity") == 5

    def test_second_use_is_refused(self, env):
        add_char(env, "White", "James")
        assert env.globals().doSignature("White") is True
        assert env.globals().doSignature("White") is False
        assert env.eval("gameState.activeChars.White.actionsLeft") == 6  # not 9

    def test_coco_heals_across_tiles_capped_at_max(self, env):
        add_char(env, "Red", "Coco", location="JamesHouse")
        add_char(env, "Yellow", "Rayman", health=4, location="BadmintonCourt")
        assert env.globals().doSignature("Red", "Yellow") is True
        assert env.eval("gameState.activeChars.Yellow.health") == 8
        assert env.eval("gameState.activeChars.Red.signatureUsed") is True

    def test_coco_cannot_reach_the_down(self, env):
        add_char(env, "Red", "Coco")
        add_char(env, "Yellow", "Rayman", down=True, health=0)
        assert env.globals().doSignature("Red", "Yellow") is False
        assert env.eval("gameState.activeChars.Red.signatureUsed") is not True
        assert env.eval("gameState.activeChars.Yellow.health") == 0

    def test_luca_speech_gated_until_someone_is_hurting(self, env):
        add_char(env, "Blue", "Luca")
        add_char(env, "Green", "Ellie")  # full sanity: no crisis
        assert env.globals().doSignature("Blue") is False
        assert env.eval("gameState.activeChars.Blue.signatureUsed") is not True
        env.execute("gameState.activeChars.Green.sanity = 2")  # now someone's hurting
        assert env.globals().doSignature("Blue") is True
        assert env.eval("gameState.activeChars.Green.sanity") == 4   # +2
        assert env.eval("gameState.activeChars.Blue.sanity") == 10   # capped at max

    def test_luca_speech_reaches_everyone_standing(self, env):
        add_char(env, "Blue", "Luca", sanity=6, location="JamesHouse")
        add_char(env, "White", "James", sanity=4, location="BadmintonCourt")
        add_char(env, "Yellow", "Rayman", down=True, sanity=0)
        assert env.globals().doSignature("Blue") is True  # Rayman Down satisfies the gate
        assert env.eval("gameState.activeChars.Blue.sanity") == 8
        assert env.eval("gameState.activeChars.White.sanity") == 6
        assert env.eval("gameState.activeChars.Yellow.sanity") == 0  # the Down don't hear it

    def _ellie_with_food(self, env, food=3):
        add_char(env, "Green", "Ellie", location="EllieLucaHouse")
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["PlayerBoard:Ellie"], "position": [20, 1, 20]}))
        add(py_to_lua(env, {"tags": ["ResourceBag:Provisions"], "position": [40, 1, 40]}))
        # Held resources are authoritative in gameState — grant them the same
        # way the game does (giveResource), not by placing physical tokens.
        env.globals().giveResource("Green", "Provisions", food)

    def test_feast_spends_one_action_zeroes_food_frees_cooking(self, env):
        self._ellie_with_food(env, food=3)
        assert env.globals().doSignature("Green") is True
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 2   # the single action
        assert env.eval("gameState.activeChars.Green.feastActive") is True
        assert lua_to_py(env.globals().getPlayerResources("Green"))["Provisions"] == 0
        # cooking now costs no actions
        env.globals().doCook("Green", "R_PORRIDGE")
        env.globals().doCook("Green", "R_LEFTOVERS")
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 2

    def test_feast_requires_the_crockpot(self, env):
        add_char(env, "Green", "Ellie", location="JamesHouse")
        assert env.globals().doSignature("Green") is False
        assert env.eval("gameState.activeChars.Green.signatureUsed") is not True

    def test_posterize_removes_threat_and_echoes_tonight(self, env):
        add_char(env, "Yellow", "Rayman", location="BasketballCourt")
        env.eval("TTS.addObject")(py_to_lua(env, {"tags": ["Location:BasketballCourt"], "position": [10, 1, 10]}))
        env.execute('SIG_TEST_THREAT = TTS.addObject({tags={"ThreatCard"}, nickname="Shadow Stalker", position={11, 1, 10}})')
        env.execute("SIG_TEST_RESULT = doSignature('Yellow', SIG_TEST_THREAT)")
        assert env.eval("SIG_TEST_RESULT") is True
        assert env.eval('#findAllByTag("ThreatCard")') == 0            # dunked out of existence
        assert env.eval("gameState.loudSignature.BasketballCourt") is True
        assert env.eval("gameState.activeChars.Yellow.signatureUsed") is True

    def test_posterize_needs_a_threat_at_his_tile(self, env):
        add_char(env, "Yellow", "Rayman", location="BasketballCourt")
        env.eval("TTS.addObject")(py_to_lua(env, {"tags": ["Location:BasketballCourt"], "position": [10, 1, 10]}))
        ok, _reason = env.globals().canUseSignature("Yellow")
        assert ok is not True

    def test_signature_used_survives_save_load(self, env):
        add_char(env, "White", "James")
        env.globals().doSignature("White")
        saved = env.globals().onSave()
        env2 = make_env()
        env2.globals().onLoad(saved)
        assert env2.eval("gameState.activeChars.White.signatureUsed") is True


# ---------------------------------------------------------------------------
# Source phases + The Last Dawn (Design §12.6/§15.7, design_batch2.md §3)
# ---------------------------------------------------------------------------


class TestNothingLeftToLose:
    def test_attack_dice_plus_one_at_doom25(self, env):
        add_char(env, "White", "James")
        assert env.globals().getAttackDice("White") == 1
        env.execute("gameState.ongoingDawnEffects.doom25 = true")
        assert env.globals().getAttackDice("White") == 2

    def test_rayman_stacks_base_and_doom25(self, env):
        add_char(env, "Yellow", "Rayman")
        env.execute("gameState.ongoingDawnEffects.doom25 = true")
        assert env.globals().getAttackDice("Yellow") == 3  # base 1 + Rayman + doom25

    def test_rest_heals_health_anywhere_only_at_doom25(self, env):
        # EllieLucaHouse, not RaymanHouse: the Garage (§7.2) heals +1 Health
        # for anyone resting there, which would mask the Doom-25 rule.
        add_char(env, "White", "James", health=5, location="EllieLucaHouse")
        env.globals().doRest("White", "sanity")
        assert env.eval("gameState.activeChars.White.health") == 5  # away from home, no buff
        env.execute("gameState.ongoingDawnEffects.doom25 = true")
        env.globals().doRest("White", "sanity")
        assert env.eval("gameState.activeChars.White.health") == 6  # buff active

    def test_home_bonus_does_not_stack_with_doom25(self, env):
        add_char(env, "White", "James", health=5, location="JamesHouse")
        env.execute("gameState.ongoingDawnEffects.doom25 = true")
        env.globals().doRest("White", "hunger")
        assert env.eval("gameState.activeChars.White.health") == 6  # exactly one +1

    def test_threshold_broadcast_announces_the_buff(self, env):
        env.execute("gameState.doom = 25")
        env.globals().checkDoomThresholds()
        assert any("Nothing Left to Lose" in m for m in broadcasts(env))

    def test_rules_panel_label_states_only_rules_that_exist(self, env):
        """The label used to open with "boss threats can appear in any phase",
        which described a mechanic the mod does not have: one un-phased Threat
        deck, and bosses placed by scripted Dawn cards that Doom never touches.
        Nothing read the claim; it was a paper rule printed to the table."""
        label = env.eval("DOOM_THRESHOLD_RULES[4][2]")
        assert "Nothing Left to Lose" in label
        assert "attack die" in label and "Health" in label
        assert "any phase" not in label


# ---------------------------------------------------------------------------
# Signature Moves (Design §6.7, design_batch2.md §2)
# ---------------------------------------------------------------------------


class TestPerks:
    def test_calming_presence_softens_tick(self, env):
        # Coco's tile-mates lose 1 less Sanity at Tick; she and the distant do not.
        add_char(env, "Red", "Coco", location="JamesHouse")
        add_char(env, "White", "James", location="JamesHouse")
        add_char(env, "Green", "Ellie", location="RaymanHouse")
        env.execute("gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.White.sanity") == 10  # -1 +1 aura = 0
        assert env.eval("gameState.activeChars.Red.sanity") == 11    # Coco herself pays
        assert env.eval("gameState.activeChars.Green.sanity") == 7   # out of range

    def test_needs_audience_blocks_solo_rest_sanity(self, env):
        add_char(env, "Blue", "Luca", hunger=5)
        env.globals().doRest("Blue", "sanity")
        assert env.eval("gameState.activeChars.Blue.sanity") == 10  # unchanged
        assert env.eval("gameState.activeChars.Blue.hunger") == 6   # converted to hunger

    def test_rest_sanity_works_with_company(self, env):
        add_char(env, "Blue", "Luca", sanity=6)
        add_char(env, "White", "James")  # same tile (JamesHouse default)
        env.globals().doRest("Blue", "sanity")
        assert env.eval("gameState.activeChars.Blue.sanity") == 8

    def test_needs_audience_blocks_solo_sleep_sanity(self, env):
        add_char(env, "Blue", "Luca", location="EllieLucaHouse", sanity=5, hunger=5, health=5)
        env.globals().resolveSleep()
        assert env.eval("gameState.activeChars.Blue.sanity") == 5   # no regen alone
        assert env.eval("gameState.activeChars.Blue.hunger") == 6   # body still rests
        assert env.eval("gameState.activeChars.Blue.health") == 6

    def test_storyteller_needs_an_audience(self, env):
        add_char(env, "Blue", "Luca", sanity=5, location="EllieLucaHouse")
        env.globals().resolveStorytelling()
        assert env.eval("gameState.activeChars.Blue.sanity") == 5   # alone: no story
        add_char(env, "Green", "Ellie", sanity=5, location="EllieLucaHouse")
        env.globals().resolveStorytelling()
        assert env.eval("gameState.activeChars.Blue.sanity") == 6
        assert env.eval("gameState.activeChars.Green.sanity") == 6

    def test_particular_eater_blocks_raw_food(self, env):
        add_char(env, "Green", "Ellie", hunger=4, sanity=8)
        env.globals().doEatUncooked("Green")
        assert env.eval("gameState.activeChars.Green.hunger") == 4  # refused
        assert env.eval("gameState.activeChars.Green.sanity") == 8
        add_char(env, "White", "James", hunger=4)
        env.globals().doEatUncooked("White")
        assert env.eval("gameState.activeChars.White.hunger") == 5  # others may

    def test_court_master_extra_die_at_basketball_court(self, env):
        add_char(env, "Yellow", "Rayman", location="BasketballCourt")
        assert env.globals().getAttackDice("Yellow") == 3  # 1 base +1 Rayman +1 court
        env.execute('gameState.activeChars.Yellow.location = "BadmintonCourt"')
        assert env.globals().getAttackDice("Yellow") == 2  # wrong court

    def test_backboard_block_redirects_counter_damage(self, env):
        add_char(env, "White", "James", health=8)
        add_char(env, "Yellow", "Rayman", health=12)
        env.execute("gameState.raymanDefending = true")
        script_dice(env, [3, 3, 3, 5, 5])  # whiff (no 1s); counter lands twice
        env.globals().beginCombat(
            py_to_lua(env, ["White", "Yellow"]),
            py_to_lua(env, {"name": "T", "hp": 9, "attack": 2}))
        assert env.eval("gameState.activeChars.Yellow.health") == 10  # took both
        assert env.eval("gameState.activeChars.White.health") == 8    # shielded

    def test_gaming_reflexes_rerolls_once_per_turn_on_his_turn(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.activeColor = "White"; gameState.jamesRerollUsed = false')
        script_dice(env, [3, 6])  # miss, rerolled into a kill
        r = env.globals().resolveCombat("White", py_to_lua(env, {"name": "T", "hp": 1, "attack": 0}))
        assert lua_to_py(r)["defeated"] is True
        assert env.eval("gameState.jamesRerollUsed") is True
        script_dice(env, [3])     # spent: the second whiff stays a whiff
        r2 = env.globals().resolveCombat("White", py_to_lua(env, {"name": "T2", "hp": 1, "attack": 0}))
        assert lua_to_py(r2)["defeated"] is False

    def test_pattern_recognition_peek_once_per_day(self, env):
        add_char(env, "White", "James")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["ThreatCardDeck"],
            "contained": [{"nickname": "Shadow Stalker", "guid": "ts1"},
                          {"nickname": "Lurker", "guid": "ts2"}]}))
        assert env.globals().doPeek("White", "Threat") is True
        assert env.eval("gameState.jamesPeekUsed") is True
        assert any("Shadow Stalker" in b for b in broadcasts(env))
        assert env.globals().doPeek("White", "Threat") is False  # once per day
        env.execute("gameState.jamesPeekUsed = false")            # BeginDay resets this
        assert env.globals().doPeek("White", "Threat") is True

    def test_rally_grants_action_once_per_turn_within_reach(self, env):
        add_char(env, "Blue", "Luca", location="JamesHouse")
        add_char(env, "Green", "Ellie", location="EllieLucaHouse", actionsLeft=2)  # adjacent
        add_char(env, "Yellow", "Rayman", location="RaymanHouse", actionsLeft=2)   # 2 tiles away
        assert env.globals().doRally("Blue", "Yellow") is False  # out of reach
        assert env.globals().doRally("Blue", "Green") is True
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 3
        assert env.eval("gameState.lucaRallyUsed") is True
        assert env.globals().doRally("Blue", "Green") is False   # once per turn

    def test_calm_words_negates_group_sanity_loss_at_lucas_tile(self, env):
        add_char(env, "Blue", "Luca", location="JamesHouse")
        add_char(env, "White", "James", location="JamesHouse")
        add_char(env, "Green", "Ellie", location="RaymanHouse", sanity=4)
        script_dice(env, [4])  # Calm Words d6: 4+ = the tile is spared
        env.execute('DAWN_EFFECTS["P3_SCREAMS"].onReveal(TTS.makeObject({}))')
        assert env.eval("gameState.activeChars.Blue.sanity") == 10
        assert env.eval("gameState.activeChars.White.sanity") == 10
        assert env.eval("gameState.activeChars.Green.sanity") == 1  # -1, then -2 (lowest)

    def test_calm_words_fizzle_spares_no_one(self, env):
        add_char(env, "Blue", "Luca", location="JamesHouse")
        add_char(env, "Green", "Ellie", location="RaymanHouse", sanity=4)
        script_dice(env, [3])  # 1-3: the words don't land
        env.execute('DAWN_EFFECTS["P3_SCREAMS"].onReveal(TTS.makeObject({}))')
        assert env.eval("gameState.activeChars.Blue.sanity") == 9
        assert env.eval("gameState.activeChars.Green.sanity") == 1


# ---------------------------------------------------------------------------
# Gather & resource automation (Design §7-8) — players never touch the bags.
# ---------------------------------------------------------------------------


class TestGatherAutomation:
    def _world(self, env, color, name, loc):
        add_char(env, color, name, location=loc)
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": [f"Location:{loc}"], "position": [0, 1, 0]}))
        add(py_to_lua(env, {"tags": [f"PlayerBoard:{name}"], "position": [20, 1, 20]}))
        for res in ["Wood", "Metal", "Cloth", "Provisions", "EnergyDrink", "Battery"]:
            add(py_to_lua(env, {
                "tags": [f"ResourceBag:{res}"], "position": [60, 1, 60],
                "contained": [{"nickname": res, "tags": ["Resource", f"Resource:{res}"]}] * 8}))

    def _held(self, env, color):
        return lua_to_py(env.globals().getPlayerResources(color))

    def test_gather_delivers_a_token_to_the_board(self, env):
        self._world(env, "Green", "Rayman", "RaymanHouse")
        env.globals().doGather("Green")
        held = self._held(env, "Green")
        assert sum(held.values()) == 1
        # Rayman's House yields only Metal / Battery / Provisions — never Wood or Cloth.
        assert held["Wood"] == 0 and held["Cloth"] == 0
        assert held["Metal"] + held["Battery"] + held["Provisions"] == 1

    def test_gather_spends_one_action(self, env):
        self._world(env, "Green", "Rayman", "RaymanHouse")
        env.globals().doGather("Green")
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 2

    def test_backpack_gathers_two(self, env):
        self._world(env, "Green", "Rayman", "RaymanHouse")
        env.execute('TTS.setHand("Green", { TTS.makeObject({tags={"M_BACKPACK"}, nickname="Backpack"}) })')
        env.globals().doGather("Green")
        assert sum(self._held(env, "Green").values()) == 2

    def test_stash_confirm_gives_two_energy_drinks(self, env):
        self._world(env, "Blue", "James", "JamesHouse")
        env.globals().doGather("Blue")
        assert env.eval('TTS.ui.visible["confirmDialog"]') is True
        env.globals().onConfirmYes(py_to_lua(env, {"color": "Blue"}), "", "")
        held = self._held(env, "Blue")
        assert held["EnergyDrink"] == 2 and sum(held.values()) == 2

    def test_stash_cancel_takes_the_random_draw(self, env):
        self._world(env, "Blue", "James", "JamesHouse")
        env.globals().doGather("Blue")
        env.globals().onConfirmNo(py_to_lua(env, {"color": "Blue"}), "", "")
        held = self._held(env, "Blue")
        assert sum(held.values()) == 1   # one JamesHouse yield, delivered automatically

    def test_ellie_pantry_picker_delivers_her_choice(self, env):
        self._world(env, "Yellow", "Ellie", "EllieLucaHouse")
        env.globals().doGather("Yellow")
        assert env.eval('TTS.ui.visible["resourcePickerDialog"]') is True
        env.globals().onResourcePickClick(py_to_lua(env, {"color": "Yellow"}), "Battery", "")
        held = self._held(env, "Yellow")
        assert held["Battery"] == 2 and sum(held.values()) == 2   # pantry: 2, her pick

    def test_gather_blocked_at_treeguard_lair(self, env):
        self._world(env, "Green", "Rayman", "BadmintonCourt")
        env.execute('gameState.treeguard = { active = true, location = "BadmintonCourt" }')
        env.globals().doGather("Green")
        assert sum(self._held(env, "Green").values()) == 0
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 3   # no action spent

    def test_spawn_resource_at_tile_and_treeguard_salvage(self, env):
        add_char(env, "Green", "Rayman", location="BadmintonCourt")
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:BadmintonCourt"], "position": [10, 1, -10]}))
        add(py_to_lua(env, {"tags": ["ResourceBag:Wood"], "position": [60, 1, 60],
                            "contained": [{"nickname": "Wood", "tags": ["Resource", "Resource:Wood"]}] * 8}))
        env.execute('gameState.treeguard = { active = true, location = "BadmintonCourt" }')
        env.globals().treeguardDefeated()
        assert env.eval('#findAllByTag("Resource:Wood")') == 3


# ---------------------------------------------------------------------------
# Cook ingredient automation — recipes auto-pay their Resource cost (like
# Craft), with Ellie's Crockpot Master discount and the Feast exemption.
# ---------------------------------------------------------------------------


class TestCookIngredients:
    def _cook_world(self, env, name, color="Green"):
        # Ellie & Luca's House is the Crockpot tile every recipe needs.
        add_char(env, color, name, location="EllieLucaHouse")
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:EllieLucaHouse"], "position": [0, 1, 0]}))
        add(py_to_lua(env, {"tags": [f"PlayerBoard:{name}"], "position": [20, 1, 20]}))
        for res in ["Wood", "Metal", "Cloth", "Provisions", "EnergyDrink", "Battery"]:
            add(py_to_lua(env, {
                "tags": [f"ResourceBag:{res}"], "position": [60, 1, 60],
                "contained": [{"nickname": res, "tags": ["Resource", f"Resource:{res}"]}] * 8}))

    def _held(self, env, color="Green"):
        return lua_to_py(env.globals().getPlayerResources(color))

    def test_cook_pays_ingredients_from_held(self, env):
        self._cook_world(env, "Rayman")   # non-Ellie: full cost
        env.globals().giveResource("Green", "Provisions", 2)
        env.globals().giveResource("Green", "Wood", 1)
        env.globals().doCook("Green", "R_HOT_STEW")   # costs 2 Provisions + 1 Wood
        held = self._held(env)
        assert held["Provisions"] == 0 and held["Wood"] == 0
        assert env.eval("gameState.activeChars.Green.hunger") >= 4   # effect applied

    def test_cook_refused_and_refunded_when_short(self, env):
        self._cook_world(env, "Rayman")
        env.globals().giveResource("Green", "Provisions", 1)   # need 2 Provisions + 1 Wood
        start_hunger = env.eval("gameState.activeChars.Green.hunger")
        env.globals().doCook("Green", "R_HOT_STEW")
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 3   # action refunded
        assert env.eval("gameState.activeChars.Green.hunger") == start_hunger  # no effect
        assert self._held(env)["Provisions"] == 1   # nothing spent

    def test_ellie_crockpot_master_pays_one_fewer(self, env):
        self._cook_world(env, "Ellie")
        env.globals().giveResource("Green", "Provisions", 2)   # 2 Provisions + 1 Wood, minus 1 = 1 Provisions + 1 Wood
        env.globals().giveResource("Green", "Wood", 1)
        env.globals().doCook("Green", "R_HOT_STEW")
        held = self._held(env)
        # Ellie shaves one Provisions (the largest ingredient); 1 Provisions is left over.
        assert held["Provisions"] == 1 and held["Wood"] == 0

    def test_full_heart_supply_refuses_before_charging_the_cook(self, env):
        """The Telltale Heart is the one recipe whose penalty (2 Health) is
        paid up front, and its supply ceiling used to be checked *after* —
        so a cook against a full supply cost 2 Health, three resources and an
        action, and produced nothing."""
        self._cook_world(env, "Rayman")
        for res in ("Battery", "Cloth", "Provisions"):
            env.globals().giveResource("Green", res, 1)
        env.execute("gameState.heartCount = HEART_SUPPLY_MAX")
        start_health = env.eval("gameState.activeChars.Green.health")
        env.globals().doCook("Green", "R_TELLTALE_HEART")
        assert env.eval("gameState.activeChars.Green.health") == start_health
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 3
        assert self._held(env)["Battery"] == 1   # nothing spent
        assert env.eval("gameState.heartCount") == env.eval("HEART_SUPPLY_MAX")

    def test_a_two_action_recipe_is_all_or_nothing(self, env):
        """Birthday Cake costs 2 actions. Starting it with 1 left used to
        spend that action inside the loop and then bail."""
        self._cook_world(env, "Rayman")
        env.execute("gameState.activeChars.Green.actionsLeft = 1")
        for res in ("Cloth", "EnergyDrink", "Provisions"):
            env.globals().giveResource("Green", res, 3)
        env.globals().doCook("Green", "R_BIRTHDAY_CAKE")
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 1
        assert env.eval("gameState.usedRecipes.R_BIRTHDAY_CAKE") is None

    def test_a_two_action_recipe_cooks_with_the_budget_for_it(self, env):
        self._cook_world(env, "Rayman")
        for res in ("Cloth", "EnergyDrink", "Provisions"):
            env.globals().giveResource("Green", res, 3)
        env.globals().doCook("Green", "R_BIRTHDAY_CAKE")
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 1   # 3 - 2
        assert env.eval("gameState.usedRecipes.R_BIRTHDAY_CAKE") is True

    def test_requires_crockpot_is_enforced(self, env):
        """Gumbo prints "Requires non-empty Crockpot tile"; the flag was
        generated into RECIPE_DATA and read by nothing."""
        self._cook_world(env, "Rayman")
        env.execute("gameState.activeChars.Green.location = 'BasketballCourt'")
        for res in ("Provisions", "Wood", "Cloth"):
            env.globals().giveResource("Green", res, 3)
        env.globals().doCook("Green", "R_GUMBO")
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 3
        assert self._held(env)["Wood"] == 3

    def test_portable_crockpot_makes_any_tile_a_kitchen(self, env):
        """"Persistent. Allows cooking at any tile (not just kitchen)" — the
        card was craftable and inert; crockpotAt() is now the one answer the
        Cook button, the Cook handler and requiresCrockpot all read."""
        self._cook_world(env, "Rayman")
        env.execute("gameState.activeChars.Green.location = 'BasketballCourt'")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:BasketballCourt"], "position": [30, 1, 30]}))
        assert env.globals().crockpotAt("BasketballCourt") is False
        env.execute('TTS.setHand("Green", { TTS.makeObject({tags={"M_PORTABLE_CROCKPOT"}}) })')
        assert env.globals().crockpotAt("BasketballCourt") is True
        for res in ("Provisions", "Wood", "Cloth"):
            env.globals().giveResource("Green", res, 3)
        env.globals().doCook("Green", "R_GUMBO")
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 2   # it cooked


# ---------------------------------------------------------------------------
# Regression guards for bug CLASSES seen in playtest (see also
# tests/test_regression_guards.py for the static ones).
# ---------------------------------------------------------------------------


class TestResourceModelRobustness:
    """Held resources must be authoritative in gameState — never recomputed
    from physical token positions. The old position-counting broke the moment
    a player board drifted (boards spawned overlapping and physics scattered
    them); a gathered token metres from its board counted as zero."""

    def _world(self, env, color="Green", name="Rayman"):
        add_char(env, color, name, location="RaymanHouse")
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:RaymanHouse"], "position": [0, 1, 0]}))
        board = add(py_to_lua(env, {"tags": [f"PlayerBoard:{name}"], "position": [20, 1, 20]}))
        for res in ["Wood", "Metal", "Cloth", "Provisions", "EnergyDrink", "Battery"]:
            add(py_to_lua(env, {"tags": [f"ResourceBag:{res}"], "position": [60, 1, 60],
                                "contained": [{"nickname": res, "tags": ["Resource", f"Resource:{res}"]}] * 8}))
        return board

    def test_count_survives_the_board_being_dragged_away(self, env):
        board = self._world(env)
        env.globals().giveResource("Green", "Wood", 3)
        assert lua_to_py(env.globals().getPlayerResources("Green"))["Wood"] == 3
        # Drag the board to the far side of the table (the failure that used
        # to zero the count). The held count must not care where the board is.
        board.setPosition(py_to_lua(env, [-40, 1, -40]))
        assert lua_to_py(env.globals().getPlayerResources("Green"))["Wood"] == 3

    def test_paying_a_cost_deducts_from_the_authoritative_count(self, env):
        self._world(env)
        env.globals().giveResource("Green", "Wood", 2)
        assert env.globals().verifyAndPayResources(
            "Green", py_to_lua(env, {"Wood": 2}), "test") is True
        assert lua_to_py(env.globals().getPlayerResources("Green"))["Wood"] == 0


class TestStatDisplayNeverStale:
    """The left stat box froze at pre-night values because refreshStatDisplay
    early-returned when no player was active (Dawn/Night/Tick). It must fall
    back to a living character and show live stats, never a stale snapshot."""

    def test_refresh_shows_live_stats_with_no_active_player(self, env):
        add_char(env, "Blue", "James", health=4, hunger=2, sanity=3)
        env.execute("gameState.started = true")
        env.execute("gameState.activeColor = nil")   # night/tick: nobody's turn
        env.globals().refreshStatDisplay()
        # The panel shows James (the only living character), not the "—" blank.
        name = env.eval('UI.getAttribute("statCharName", "text")')
        assert name and "James" in name


class TestDifficultyAwareText:
    """Player-facing limits must follow the chosen difficulty. Long Weekend is
    3 days with a 15-Doom track, but the tooltips and the Doom help panel used
    to print the Standard "of 7" / "/ 30" on every difficulty."""

    def test_doom_help_uses_the_difficulty_limit(self, env):
        env.execute('gameState.difficulty = "weekend"')   # 3 days, Doom to 15
        text = env.globals().getHelpDoomContent()
        assert "/ 15" in text, f"Doom help should show the weekend limit:\n{text}"
        # Defeat is at 15 here, so no threshold beyond it may be listed.
        for beyond in ("20:", "25:", "30:"):
            assert beyond not in text, (
                f"Doom help lists threshold {beyond} past the weekend defeat "
                f"point of 15:\n{text}")

    def test_tooltips_substitute_the_difficulty_limits(self, env):
        env.execute('gameState.difficulty = "weekend"')
        env.execute("gameState.day = 2")
        add = env.eval("TTS.addObject")
        counter = add(py_to_lua(env, {"tags": ["DayCounter"], "position": [0, 1, 0]}))
        marker = add(py_to_lua(env, {"tags": ["DoomMarker"], "position": [1, 1, 0]}))
        env.globals().applyTooltips()
        day_desc = counter.getDescription()
        doom_desc = marker.getDescription()
        assert "Day 2 of 3" in day_desc, day_desc
        assert "/ 15" in doom_desc, doom_desc
        # No unsubstituted placeholders left behind.
        for desc in (day_desc, doom_desc):
            assert "{" not in desc, f"unsubstituted placeholder: {desc}"


class TestMarketHelpTooltip:
    """The "what is this row of cards?" paragraph rides on the market CARD.

    It used to be printed on five notecard slot markers beside the board;
    those were far wider than a card and lay across the printed map. The text
    moved onto the card's own tooltip, which means it now has to be attached
    when a card is dealt and removed when the card is bought — in a player's
    hand, "use the Craft action to buy it" is a lie.
    """

    def _market(self, env, contained=None):
        add = env.eval("TTS.addObject")
        for i in range(5):
            add(py_to_lua(env, {"tags": [f"MarketSlot:{i}"],
                                "position": [-13.6, 1.6, 8.8 - i * 4.4]}))
        add(py_to_lua(env, {"tags": ["MarketCardDeck"], "position": [-9, -2.5, -10],
                            "contained": contained if contained is not None else
                            [{"nickname": f"Item {n}", "guid": f"mk{n}",
                              "tags": ["MarketCard"], "description": f"Cost: {n} Wood"}
                             for n in range(8)]}))

    def test_add_is_idempotent_and_strip_restores_the_original(self, env):
        add = env.eval("TTS.addObject")
        card = add(py_to_lua(env, {"tags": ["MarketCard"], "position": [0, 1, 0],
                                   "nickname": "Duct Tape",
                                   "description": "Cost: 1 Cloth"}))
        g = env.globals()
        g.addMarketHelp(card)
        g.addMarketHelp(card)
        desc = card.getDescription()
        assert "Cost: 1 Cloth" in desc
        assert "Craft action" in desc
        assert desc.count("— MARKET —") == 1, f"help appended twice:\n{desc}"
        g.stripMarketHelp(card)
        assert card.getDescription() == "Cost: 1 Cloth"

    def test_strip_is_a_no_op_on_a_card_that_never_got_it(self, env):
        add = env.eval("TTS.addObject")
        card = add(py_to_lua(env, {"tags": ["MarketCard"], "position": [0, 1, 0],
                                   "description": "Cost: 2 Wood"}))
        env.globals().stripMarketHelp(card)
        assert card.getDescription() == "Cost: 2 Wood"

    # lua_to_py flattens objects into plain data, so read the descriptions on
    # the Lua side and assert on those.
    _DESCS = '''(function()
        local out = {}
        for _, o in ipairs(findAllByTag("MarketCard")) do
            if o.type == "Card" then out[#out + 1] = o.getDescription() or "" end
        end
        return out
    end)()'''

    def _card_descs(self, env):
        return list(lua_to_py(env.eval(self._DESCS)))

    def test_dealt_market_cards_carry_the_help(self, env):
        self._market(env)
        env.globals().dealMarketDisplay()
        flush(env)
        descs = self._card_descs(env)
        assert len(descs) == 5, f"expected 5 cards dealt, got {len(descs)}"
        for d in descs:
            assert "Craft action" in d, f"card dealt without the market tooltip: {d!r}"

    def test_buying_a_card_strips_the_help_before_it_reaches_the_hand(self, env):
        add_char(env, "White", "James")
        self._market(env)
        env.globals().dealMarketDisplay()
        flush(env)
        assert all("Craft action" in d for d in self._card_descs(env))
        env.globals().doCraft("White", 1)
        flush(env)
        clean = [d for d in self._card_descs(env) if "Craft action" not in d]
        assert len(clean) == 1, (
            "the bought card should be the only one without the slot help; "
            f"found {len(clean)} of {len(self._card_descs(env))}")
        assert "Cost:" in clean[0], (
            f"stripping the help ate the card's own text: {clean[0]!r}")


class TestPeekDeliversItsAnswer:
    """Peek's whole product is the card it shows you. It used to arrive via
    broadcastToColor — which renders behind the Phase Banner and fades in
    seconds — so spending the once-per-day free action looked like a no-op
    ("I did Peek at the threat deck, but nothing happened"). The answer now
    goes to a per-player panel that stays until dismissed.
    """

    def _james(self, env, deck_tag="ThreatCardDeck", cards=None):
        add_char(env, "White", "James")
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": [deck_tag], "position": [-9, -2.5, -4],
                            "contained": cards if cards is not None else
                            [{"nickname": "Something In The Yard",
                              "description": "Type: Lurker  HP: 3  Atk: 2"}]}))

    def _panel(self, env):
        return lua_to_py(env.eval("TTS.ui"))

    def test_peek_opens_a_panel_carrying_the_card(self, env):
        self._james(env)
        assert env.globals().doPeek("White", "Threat") is True
        ui = self._panel(env)
        body = ui["attrs"]["peekResultBody"]["text"]
        assert "Something In The Yard" in body, body
        assert "Lurker" in body, "the card's rules text is the useful half"
        assert ui["visible"].get("peekResultPanel") is True, \
            "the peek result panel was never shown"

    def test_the_answer_is_private_to_the_peeker(self, env):
        self._james(env)
        env.globals().doPeek("White", "Threat")
        ui = self._panel(env)
        assert ui["attrs"]["peekResultPanel"]["visibility"] == "White", (
            "the panel must be restricted to the peeker — Pattern Recognition "
            "is 'tell the team, or don't'")

    def test_an_empty_deck_still_says_so_and_does_not_spend_the_peek(self, env):
        self._james(env, cards=[])
        assert env.globals().doPeek("White", "Threat") is False
        ui = self._panel(env)
        assert ui["visible"].get("peekResultPanel") is True, \
            "a failed peek must not be silent — that is the original bug"
        assert "empty" in ui["attrs"]["peekResultBody"]["text"].lower()
        assert not env.eval("gameState.jamesPeekUsed"), \
            "a peek that showed nothing must not burn the daily use"


class TestQuickStartCardFits:
    """A TTS Notecard renders ONE fixed-size page and clips the overflow with
    no scrollbar and no ellipsis. The card used to carry the whole ~1900-char
    quickstart.md and cut off mid-word — "...the neighbo" — so the day loop,
    the stats and the light rule were never on it at all. The long version
    belongs in the Notebook tab and the ? panel, which scroll.
    """

    def _budget(self, env):
        return int(env.eval("QUICKSTART_CARD_BUDGET"))

    @pytest.mark.parametrize("difficulty", ["weekend", "standard", "nightmare"])
    def test_card_text_fits_the_notecard_at_every_difficulty(self, env, difficulty):
        env.execute(f'gameState.difficulty = "{difficulty}"')
        text = env.globals().quickStartCardText()
        budget = self._budget(env)
        assert len(text) <= budget, (
            f"Quick Start card is {len(text)} chars at {difficulty} (budget "
            f"{budget}) — a Notecard silently clips the rest. Move detail to "
            f"the Notebook/? panel instead of growing the card.\n{text}")
        # The difficulty header is why this varies at all — keep it honest.
        assert str(env.globals().getDoomLimit()) in text
        assert str(env.globals().getTotalDays()) in text

    def test_the_full_rules_are_still_reachable_from_the_card(self, env):
        text = env.globals().quickStartCardText()
        assert "?" in text and "What now?" in text, (
            "the short card must point at the places that hold the long "
            "version, or the detail is simply gone")

    def test_the_notebook_still_carries_the_long_version(self, env):
        """Shortening the card must not shorten the rules — the Notebook tab
        is the thing that can actually hold them."""
        full = env.globals().quickStartTextForVariant()
        assert len(full) > self._budget(env) * 2, (
            "the Notebook's Quick Start looks truncated too — the card was "
            "supposed to shrink, not the rules")
