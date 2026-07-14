"""combat resolution, press-the-attack, boss rewards, Source phases, Charlie, fight action, boss placement.

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


class TestCombat:
    def test_fumble_only_on_complete_whiff(self, env):
        add_char(env, "White", "James")  # 1 attack die
        script_dice(env, [1])  # natural 1, zero hits -> fumble
        r = env.globals().resolveCombat("White", py_to_lua(env, {"name": "T", "hp": 3, "attack": 0}))
        assert env.eval("gameState.activeChars.White.health") == 7
        assert lua_to_py(r)["defeated"] is False

    def test_no_fumble_when_hits_landed(self, env):
        add_char(env, "Yellow", "Rayman")  # 2 dice (Rayman +1)
        script_dice(env, [1, 5])  # a 1 AND a hit -> no fumble damage
        env.globals().resolveCombat("Yellow", py_to_lua(env, {"name": "T", "hp": 5, "attack": 0}))
        assert env.eval("gameState.activeChars.Yellow.health") == 12

    def test_defeat_grants_sanity_capped_at_max(self, env):
        add_char(env, "White", "James", sanity=10)  # already at max 10
        script_dice(env, [6])
        r = env.globals().resolveCombat("White", py_to_lua(env, {"name": "T", "hp": 1, "attack": 0}))
        assert lua_to_py(r)["defeated"] is True
        assert env.eval("gameState.activeChars.White.sanity") == 10  # not 11

    def test_counter_attack_applies_damage(self, env):
        add_char(env, "White", "James")
        script_dice(env, [3, 5, 5])  # miss; enemy rolls two hits
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "T", "hp": 3, "attack": 2}))
        assert env.eval("gameState.activeChars.White.health") == 6

    def test_group_fumble_max_one_damage_to_healthiest(self, env):
        add_char(env, "White", "James", health=8)
        add_char(env, "Yellow", "Rayman", health=12)  # healthiest takes the fumble
        script_dice(env, [1, 1, 1])  # James 1 die + Rayman 2 dice, all fumbles
        env.globals().resolveGroupCombat(
            py_to_lua(env, ["White", "Yellow"]),
            py_to_lua(env, {"name": "T", "hp": 5, "attack": 0}))
        assert env.eval("gameState.activeChars.Yellow.health") == 11  # exactly 1
        assert env.eval("gameState.activeChars.White.health") == 8   # untouched


# ---------------------------------------------------------------------------
# Press the Attack (Design §12.5, design_batch1.md §1)
# ---------------------------------------------------------------------------


class TestPressAttack:
    def _fight(self, env, hp=5, atk=0, name="T"):
        return env.globals().resolveCombat(
            "White", py_to_lua(env, {"name": name, "hp": hp, "attack": atk}))

    def test_hit_opens_press_window(self, env):
        add_char(env, "White", "James")
        script_dice(env, [5])
        r = self._fight(env)
        assert lua_to_py(r).get("pressWindow") is True
        assert env.eval("gameState.combatContext.open") is True

    def test_whiff_does_not_open_press_window(self, env):
        add_char(env, "White", "James")
        script_dice(env, [3])
        r = self._fight(env)
        assert lua_to_py(r).get("pressWindow") is None
        assert env.eval("gameState.combatContext") is None

    def test_press_spends_sanity_and_lands(self, env):
        add_char(env, "White", "James")   # Sanity 10
        script_dice(env, [5, 6])          # hit; press hits
        self._fight(env, hp=5)
        assert env.globals().pressAttack("White", False) is True
        assert env.eval("gameState.activeChars.White.sanity") == 9
        assert env.eval("gameState.combatContext.threatHP") == 3  # 5 -1 hit -1 press
        assert env.eval("gameState.combatContext.open") is True   # streak continues

    def test_press_fizzle_ends_streak_and_enemy_counters(self, env):
        add_char(env, "White", "James")
        script_dice(env, [5, 3, 5])       # hit; press fizzles on a 3; counter hits
        self._fight(env, hp=5, atk=1)
        env.globals().pressAttack("White", False)
        assert env.eval("gameState.combatContext") is None
        assert env.eval("gameState.activeChars.White.sanity") == 9
        assert env.eval("gameState.activeChars.White.health") == 7  # counter landed

    def test_press_die_never_fumbles(self, env):
        add_char(env, "White", "James")
        script_dice(env, [5, 1])          # press rolls a natural 1
        self._fight(env, hp=5, atk=0)
        env.globals().pressAttack("White", False)
        assert env.eval("gameState.activeChars.White.health") == 8  # no self-damage

    def test_press_blocked_without_sanity(self, env):
        add_char(env, "White", "James", sanity=1)
        script_dice(env, [5, 6])
        self._fight(env, hp=5)
        # At 1 Sanity the press needs an explicit confirm (it means going Lost).
        assert env.globals().pressAttack("White", False) is False
        assert env.eval("gameState.activeChars.White.sanity") == 1
        # Confirmed: the press goes through and the presser goes Down mid-fight.
        assert env.globals().pressAttack("White", True) is True
        assert env.eval("gameState.activeChars.White.sanity") == 0
        assert env.eval("gameState.activeChars.White.down") is True

    def test_press_kill_routes_through_boss_rewards(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.doom = 10")
        script_dice(env, [5, 6])          # hit to 1 HP; press kills
        self._fight(env, hp=2, name="Deerclops")
        env.globals().pressAttack("White", False)
        assert env.eval("gameState.combatContext") is None
        assert env.eval("gameState.bossesDefeated.deerclops") is True
        assert env.eval("gameState.doom") == 8   # -2 rebate

    def test_finish_combat_lets_enemy_counter(self, env):
        add_char(env, "White", "James")
        script_dice(env, [5, 5])          # hit; then the counter hits
        self._fight(env, hp=5, atk=1)
        env.globals().finishCombat()
        assert env.eval("gameState.combatContext") is None
        assert env.eval("gameState.activeChars.White.health") == 7

    def test_non_participant_cannot_press(self, env):
        add_char(env, "White", "James")
        add_char(env, "Green", "Ellie")
        script_dice(env, [5])
        self._fight(env, hp=5)
        assert env.globals().pressAttack("Green", False) is False
        assert env.eval("gameState.activeChars.Green.sanity") == 8  # unspent


# ---------------------------------------------------------------------------
# Boss rewards (design_batch1.md §2)
# ---------------------------------------------------------------------------


class TestBossRewards:
    def test_deerclops_kill_rebates_doom(self, env):
        env.execute("gameState.doom = 10")
        env.globals().markBossDefeated("Deerclops")
        assert env.eval("gameState.doom") == 8
        assert env.eval("gameState.ongoingDawnEffects.deerclopsDefeated") is True

    def test_eye_rebate_floors_at_zero(self, env):
        env.execute("gameState.doom = 2")
        env.globals().markBossDefeated("Eye of Terror")
        assert env.eval("gameState.doom") == 0
        assert env.eval("gameState.bossesDefeated.eye") is True

    def test_source_kill_has_no_rebate(self, env):
        env.execute("gameState.doom = 10")
        env.globals().markBossDefeated("The Source")
        assert env.eval("gameState.doom") == 10
        assert env.eval("gameState.bossesDefeated.source") is True

    def test_kill_narration_broadcast(self, env):
        env.globals().markBossDefeated("Deerclops")
        assert any("cold goes out of it" in m for m in broadcasts(env))


# ---------------------------------------------------------------------------
# Week in Review chronicle (design_batch1.md §3)
# ---------------------------------------------------------------------------


class TestSourcePhases:
    def _arrive(self, env):
        env.execute('DAWN_EFFECTS["P4_SOURCE_ARRIVES"].onReveal(TTS.makeObject({}))')

    def _split_world(self, env, beaks=3):
        """Tiles, the Source standee at the center house, and a threat deck
        holding Terror Beak cards for the split to pull."""
        add = env.eval("TTS.addObject")
        positions = {"JamesHouse": [-10, 1, 0], "RaymanHouse": [10, 1, 0],
                     "EllieLucaHouse": [0, 1, 8], "BasketballCourt": [-10, 1, -10],
                     "BadmintonCourt": [10, 1, -10]}
        for loc, pos in positions.items():
            add(py_to_lua(env, {"tags": [f"Location:{loc}"], "position": pos}))
        add(py_to_lua(env, {"tags": ["Boss", "Boss:TheSource"], "position": [0, 1, 8]}))
        # explicit guids so the stub's makeObject never rolls math.random for
        # one (scripted dice must stay reserved for the combat under test)
        add(py_to_lua(env, {"tags": ["ThreatCardDeck"], "position": [50, 1, 50],
                            "contained": [{"nickname": "Terror Beak", "guid": f"beak{i}",
                                           "tags": ["ThreatCard", "T_TERROR_BEAK"]}
                                          for i in range(beaks)]}))

    def test_source_hp_initialises_on_arrival(self, env):
        self._arrive(env)
        assert env.eval("gameState.bossHP.source") == 8   # retuned 10 -> 8 (batch 4 W3)
        assert env.eval("gameState.sourceSplit") is False

    def test_damage_decrements_persistent_hp(self, env):
        add_char(env, "White", "James")
        self._arrive(env)
        script_dice(env, [5])
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "The Source", "hp": 10, "attack": 0}))
        assert env.eval("gameState.bossHP.source") == 7

    def test_combat_uses_tracked_hp_not_the_card(self, env):
        add_char(env, "White", "James")
        self._arrive(env)
        env.execute("gameState.bossHP.source = 7; gameState.sourceSplit = true")
        script_dice(env, [5])
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "The Source", "hp": 10, "attack": 0}))
        assert env.eval("gameState.combatContext.threatHP") == 6
        assert env.eval("gameState.bossHP.source") == 6

    def test_split_fires_once_crossing_five(self, env):
        add_char(env, "White", "James")
        self._arrive(env)
        self._split_world(env)
        env.execute("gameState.bossHP.source = 6")
        script_dice(env, [5])   # 6 -> 5: the split
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "The Source", "hp": 10, "attack": 0}))
        assert env.eval("gameState.sourceSplit") is True
        splits = [m for m in broadcasts(env) if "SPLITS" in m]
        assert len(splits) == 1
        beaks_on_map = env.eval(
            '(function() local n = 0 '
            'for _, o in ipairs(findAllByTag("ThreatCard")) do '
            'if (o.getNickname() or ""):find("Terror Beak") then n = n + 1 end end '
            'return n end)()')
        assert beaks_on_map == 2
        # a second hit below 5 does not re-split
        env.globals().finishCombat()
        script_dice(env, [5])
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "The Source", "hp": 10, "attack": 0}))
        assert len([m for m in broadcasts(env) if "SPLITS" in m]) == 1

    def test_press_die_killing_blow_still_routes_through_boss_defeat(self, env):
        add_char(env, "White", "James")
        self._arrive(env)
        env.execute("gameState.bossHP.source = 2; gameState.sourceSplit = true")
        script_dice(env, [5, 6])   # hit to 1; press kills
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "The Source", "hp": 10, "attack": 0}))
        env.globals().pressAttack("White", False)
        assert env.eval("gameState.bossesDefeated.source") is True
        assert env.eval("gameState.bossHP.source") == 0
        assert env.eval("gameState.combatContext") is None

    def test_killing_blow_does_not_split_a_dead_source(self, env):
        add_char(env, "White", "James")
        self._arrive(env)
        self._split_world(env)
        env.execute("gameState.bossHP.source = 1")
        # 5 = the killing hit; the trailing 1s feed dropBossLoot's resource
        # picks (the Source standee is on the map in this test)
        script_dice(env, [5, 1, 1, 1])
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "The Source", "hp": 10, "attack": 0}))
        assert env.eval("gameState.sourceSplit") is False
        assert env.eval("gameState.bossesDefeated.source") is True


class TestCharlie:
    def test_first_attack_and_escalation(self, env):
        add_char(env, "White", "James")
        env.globals().resolveCharlieAttack("White")
        assert env.eval("gameState.activeChars.White.sanity") == 8   # -2
        assert env.eval("gameState.activeChars.White.health") == 7   # -1
        assert env.eval("gameState.activeChars.White.charlieStreak") == 1
        env.globals().resolveCharlieAttack("White")                  # bolder: -3/-2
        assert env.eval("gameState.activeChars.White.sanity") == 5
        assert env.eval("gameState.activeChars.White.health") == 5
        assert env.eval("gameState.activeChars.White.charlieStreak") == 2

    def test_coco_is_immune(self, env):
        add_char(env, "Red", "Coco")
        env.globals().resolveCharlieAttack("Red")
        assert env.eval("gameState.activeChars.Red.sanity") == 12
        assert env.eval("gameState.activeChars.Red.health") == 6

    def test_streak_resets_after_a_lit_night(self, env):
        add_char(env, "White", "James", charlieStreak=2)
        env.execute("gameState.jamesEnergyDrinkUsed = true")  # isolate the streak logic
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.White.charlieStreak") == 0


# ---------------------------------------------------------------------------
# Tick decay + Down + victory/defeat (tick_victory.lua)
# ---------------------------------------------------------------------------


class TestFightAction:
    def _world(self, env):
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:JamesHouse"], "position": [0, 1, 0]}))
        add(py_to_lua(env, {"tags": ["ThreatCard", "T_LURKER"], "type": "Card",
                            "nickname": "Lurker", "guid": "lk1", "position": [1, 1, 0]}))
        return add

    def test_fight_targets_only_fightable_things(self, env):
        add = self._world(env)
        # A Soft event card (hp 0) and Charlie's standee are not targets.
        add(py_to_lua(env, {"tags": ["ThreatCard", "T_HOWLING"], "type": "Card",
                            "nickname": "A Howling Outside", "position": [0, 1, 1]}))
        add(py_to_lua(env, {"tags": ["Boss", "Boss:Charlie"], "position": [1, 1, 1]}))
        add_char(env, "White", "James")
        targets = lua_to_py(env.execute("""
            local out = {}
            for _, t in ipairs(fightTargetsAt("JamesHouse")) do out[#out+1] = t.stats.name end
            return out"""))
        assert targets == ["Lurker"]

    def test_fight_persists_chip_damage_then_discards_on_kill(self, env):
        self._world(env)
        add_char(env, "White", "James", hunger=6)
        card = env.globals().getObjectFromGUID("lk1")
        # Lurker: hp 3, atk 1. Round 1: hit, then stop — counter misses.
        script_dice(env, [5, 3])
        env.globals().doFightTarget("White", card, False)
        env.globals().finishCombat()
        assert env.eval('gameState.threatDamage["lk1"]') == 1
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2
        # Round 2: another hit — 1 HP left.
        script_dice(env, [5, 3])
        env.globals().doFightTarget("White", card, False)
        env.globals().finishCombat()
        assert env.eval('gameState.threatDamage["lk1"]') == 2
        # Round 3: the kill. Damage record cleared, +1 victory Sanity.
        script_dice(env, [5])
        r = env.globals().doFightTarget("White", card, False)
        assert lua_to_py(r)["defeated"] is True
        assert env.eval('gameState.threatDamage["lk1"]') is None

    def test_fight_together_pulls_in_fed_allies(self, env):
        self._world(env)
        add_char(env, "White", "James", hunger=6)
        add_char(env, "Yellow", "Rayman", hunger=6, sanity=4)
        add_char(env, "Green", "Ellie", hunger=2)  # too hungry to join
        card = env.globals().getObjectFromGUID("lk1")
        script_dice(env, [5, 5, 5])  # 3 dice = James 1 + Rayman 2; Ellie sat out
        r = env.globals().doFightTarget("White", card, True)
        assert lua_to_py(r)["defeated"] is True
        assert env.eval("gameState.activeChars.Yellow.sanity") == 5  # 4 +1 victory
        assert env.eval("gameState.activeChars.Green.sanity") == 8   # not a fighter

    def test_too_hungry_cannot_start_a_fight(self, env):
        self._world(env)
        add_char(env, "White", "James", hunger=2)
        card = env.globals().getObjectFromGUID("lk1")
        env.globals().doFightTarget("White", card, False)
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3  # nothing spent


class TestBossPlacement:
    def _pool_and_courts(self, env):
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["BossPool"], "type": "Bag", "contained": [
            {"nickname": "Deerclops", "tags": ["Boss", "Boss:Deerclops"], "guid": "dc1"},
            {"nickname": "Eye of Terror", "tags": ["Boss", "Boss:EyeOfTerror"], "guid": "ey1"},
        ]}))
        for loc, pos in [("BasketballCourt", [5, 1, 0]), ("JamesHouse", [0, 1, 0]),
                         ("RaymanHouse", [10, 1, 0]), ("EllieLucaHouse", [15, 1, 0])]:
            add(py_to_lua(env, {"tags": [f"Location:{loc}"], "position": pos}))

    def test_deerclops_arrival_places_standee_and_tracks_hp(self, env):
        self._pool_and_courts(env)
        env.execute('DAWN_EFFECTS["P2_DEERCLOPS_ARRIVES"].onReveal(TTS.makeObject({}))')
        assert env.eval('findOneByTag("Boss:Deerclops") ~= nil') is True
        assert env.eval("gameState.bossHP.deerclops") == 6
        assert env.globals().isBossOnMap("Boss:Deerclops") is True

    def test_eye_arrival_lairs_at_a_house_and_defeat_pools_the_standee(self, env):
        self._pool_and_courts(env)
        script_dice(env, [2])  # house pick: RaymanHouse
        env.execute('DAWN_EFFECTS["P3_EYE_ARRIVES"].onReveal(TTS.makeObject({}))')
        assert env.eval("gameState.eyeLocation") == "RaymanHouse"
        assert env.eval("gameState.bossHP.eye") == 8
        assert env.globals().isBossOnMap("Boss:EyeOfTerror") is True
        env.execute("gameState.doom = 10")
        env.globals().markBossDefeated("Eye of Terror")
        assert env.eval('findOneByTag("Boss:EyeOfTerror")') is None  # back in the pool
        assert env.eval("gameState.doom") == 7  # -3 rebate

    def test_boss_fight_reads_persistent_hp(self, env):
        self._pool_and_courts(env)
        env.execute('DAWN_EFFECTS["P2_DEERCLOPS_ARRIVES"].onReveal(TTS.makeObject({}))')
        add_char(env, "White", "James", location="BasketballCourt", hunger=6)
        standee = env.eval('findOneByTag("Boss:Deerclops")')
        script_dice(env, [5, 3, 3, 3])  # one hit; counter (3 dice) misses
        env.globals().doFightTarget("White", standee, False)
        env.globals().finishCombat()
        assert env.eval("gameState.bossHP.deerclops") == 5  # 6 - 1, remembered
