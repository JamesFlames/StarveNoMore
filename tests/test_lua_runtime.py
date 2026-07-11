"""Headless execution of the real game Lua under Lua 5.2 (lupa) with the TTS
stub from tts_stub.lua.

The bundle under test is byte-identical to what build_save.py embeds in the
TTS save, so "the bundle loads and onLoad() runs" here means the save's
global script would load in TTS (minus TTS-engine quirks).

Rule tests drive the actual game functions (combat, Charlie, Tick, revive,
victory/defeat, light checks) with a controlled world and, where dice are
involved, a scripted math.random.
"""
import json as _json
import os

import pytest

try:
    import lupa.lua52 as lua52
except ImportError:  # pragma: no cover
    lua52 = None

from conftest import TESTS, lua_bundle, read_text

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


# ---------------------------------------------------------------------------
# Environment construction
# ---------------------------------------------------------------------------

def lua_to_py(v):
    if lua52.lua_type(v) == "table":
        keys = list(v.keys())
        if keys and all(isinstance(k, (int, float)) for k in keys) and sorted(keys) == list(
                range(1, len(keys) + 1)):
            return [lua_to_py(v[k]) for k in sorted(keys)]
        return {str(k): lua_to_py(val) for k, val in v.items()}
    return v


def py_to_lua(rt, v):
    if isinstance(v, dict):
        return rt.table_from({k: py_to_lua(rt, x) for k, x in v.items()})
    if isinstance(v, list):
        return rt.table_from([py_to_lua(rt, x) for x in v])
    return v


def make_env():
    rt = lua52.LuaRuntime(unpack_returned_tuples=False)
    rt.execute(read_text(os.path.join(TESTS, "tts_stub.lua")))
    # JSON backed by Python's json module (mirrors TTS's JSON global)
    g = rt.globals()
    g.JSON = rt.table_from({
        "encode": lambda v: _json.dumps(lua_to_py(v)),
        "encode_pretty": lambda v: _json.dumps(lua_to_py(v), indent=2),
        "decode": lambda s: py_to_lua(rt, _json.loads(s)) if s else None,
    })
    rt.execute(lua_bundle())
    return rt


@pytest.fixture()
def env():
    return make_env()


def flush(rt):
    rt.eval("TTS.flushWaits")()


def broadcasts(rt):
    return [b["message"] for b in lua_to_py(rt.eval("TTS.broadcasts"))]


def script_dice(rt, rolls):
    """Make math.random return this exact sequence (asserts if exhausted)."""
    rt.execute(
        "local seq = {%s}; local i = 0\n"
        "math.random = function(...) i = i + 1\n"
        "  assert(seq[i], 'scripted dice exhausted at roll ' .. i)\n"
        "  return seq[i] end" % ",".join(str(r) for r in rolls)
    )


def add_char(rt, color, name, **overrides):
    """Install a character into gameState.activeChars[color] with sane defaults."""
    stats = {"James": (8, 6, 10), "Coco": (6, 8, 12), "Rayman": (12, 10, 6),
             "Ellie": (8, 10, 8), "Luca": (7, 8, 10)}[name]
    char = {
        "name": name,
        "health": stats[0], "maxHealth": stats[0],
        "hunger": stats[1], "maxHunger": stats[1],
        "sanity": stats[2], "maxSanity": stats[2],
        "actionsLeft": 3, "down": False, "briefed": True,
        "location": "JamesHouse",
    }
    char.update(overrides)
    rt.globals().gameState.activeChars[color] = py_to_lua(rt, char)
    return rt.globals().gameState.activeChars[color]


# ---------------------------------------------------------------------------
# Load-time smoke
# ---------------------------------------------------------------------------

class TestLoad:
    def test_bundle_executes(self, env):
        # make_env() already executed the full bundle; reaching here means no
        # load-time error (this is the test that catches things like the
        # assets.lua url()-vs-_url() crash).
        assert env.eval("type(onLoad)") == "function"
        assert env.eval("type(onSave)") == "function"

    def test_key_tables_defined(self, env):
        for table in ["gameState", "CHARACTER_STATS", "DAWN_EFFECTS", "DAWN_MANUAL_STEPS",
                      "MARKET_COSTS", "WHATNOW_HINTS", "AUDIO", "ASSETS", "EFFECT_RULES",
                      "LIGHT_SOURCES", "DEATH_NARRATIONS"]:
            assert env.eval(f"type({table})") == "table", f"global table {table} not defined"

    def test_onload_fresh_game(self, env):
        env.globals().onLoad("")
        flush(env)  # runs the delayed refreshPhaseBanner/populateNotebook/audit
        assert env.eval("gameState.subPhase") == "PreGame"

    def test_onload_restores_saved_state(self, env):
        saved = _json.dumps({"day": 3, "doom": 12, "started": True, "subPhase": "Day",
                             "phase": 2, "activeChars": {}, "ongoingDawnEffects": {},
                             "dailyAlerts": {}, "turnOrder": [], "turnIndex": 0,
                             "playerCount": 4, "dayLog": []})
        env.globals().onLoad(saved)
        flush(env)
        assert env.eval("gameState.day") == 3
        assert env.eval("gameState.doom") == 12

    def test_save_load_roundtrip(self, env):
        env.globals().onLoad("")
        env.execute("gameState.day = 5; gameState.doom = 17; gameState.subPhase = 'Night'")
        add_char(env, "White", "James", health=4, sanity=2)
        saved = env.globals().onSave()
        env2 = make_env()
        env2.globals().onLoad(saved)
        assert env2.eval("gameState.day") == 5
        assert env2.eval("gameState.doom") == 17
        assert env2.eval("gameState.activeChars.White.health") == 4
        assert env2.eval("gameState.activeChars.White.sanity") == 2


# ---------------------------------------------------------------------------
# Pure rule helpers
# ---------------------------------------------------------------------------

class TestPhaseAndDoom:
    def test_phase_for_day(self, env):
        expected = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4}
        for day, phase in expected.items():
            assert env.globals().getPhaseForDay(day) == phase, f"day {day}"

    @pytest.mark.parametrize("players,phase,rate", [
        (3, 1, 1), (3, 4, 1),
        (4, 1, 1), (4, 3, 1), (4, 4, 2),
        (5, 2, 1), (5, 3, 2), (5, 4, 2),
    ])
    def test_doom_rate_by_player_count(self, env, players, phase, rate):
        env.execute(f"gameState.playerCount = {players}; gameState.phase = {phase}")
        assert env.globals().getDoomRate() == rate

    def test_doom_rate_clamps_player_count(self, env):
        env.execute("gameState.playerCount = 2; gameState.phase = 1")
        assert env.globals().getDoomRate() == 1  # clamped up to the 3p table

    def test_fester_threats_capped_bosses_uncapped(self, env):
        # Design §15.1: ordinary threats +1 each (max +3); phase bosses +2
        # each and the Treeguard +1, with no cap.
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:JamesHouse"], "position": [0, 1, 0]}))
        for _ in range(4):  # four loose threats — capped at +3
            add(py_to_lua(env, {"tags": ["ThreatCard"], "position": [1, 1, 0]}))
        add(py_to_lua(env, {"tags": ["Boss", "Boss:Deerclops"], "position": [2, 1, 0]}))
        add(py_to_lua(env, {"tags": ["Boss", "Boss:EyeOfTerror"], "position": [0, 1, 2]}))
        add(py_to_lua(env, {"tags": ["Boss", "Boss:Treeguard"], "position": [2, 1, 2]}))
        threat_fester, boss_fester = env.globals().countFesteringThreats()
        assert threat_fester == 3   # 4 threats, capped at +3
        assert boss_fester == 5     # 2 phase bosses x 2 + Treeguard x 1, uncapped

    def test_boss_off_the_map_does_not_fester(self, env):
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:JamesHouse"], "position": [0, 1, 0]}))
        # standee far from every tile (e.g. in the boss pool staging area)
        add(py_to_lua(env, {"tags": ["Boss", "Boss:TheSource"], "position": [90, 1, 90]}))
        threat_fester, boss_fester = env.globals().countFesteringThreats()
        assert (threat_fester, boss_fester) == (0, 0)
        assert env.globals().isBossOnMap("Boss:TheSource") is False


# ---------------------------------------------------------------------------
# Combat (Design §12) — dice are scripted, so outcomes are exact
# ---------------------------------------------------------------------------

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

class TestChronicle:
    def test_kills_and_meals_accumulate(self, env):
        add_char(env, "White", "James")
        env.globals().recordKillInChronicle("Shadow Stalker", py_to_lua(env, ["White"]))
        env.globals().recordMealInChronicle("Ellie")
        env.globals().recordMealInChronicle("Ellie")
        assert env.eval("#gameState.chronicle.kills") == 1
        assert env.eval("gameState.chronicle.meals.Ellie") == 2

    def test_day_record_survives_daylog_wipe(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.day = 3; gameState.doom = 14")
        env.globals().broadcastEvent("damage", "James is DOWN. Flip standee to ghost side.")
        env.globals().recordDayInChronicle()
        env.execute("gameState.dayLog = {}")   # the Dawn wipe
        assert env.eval("gameState.chronicle.days[3].damageTonight") == 1
        assert env.eval("gameState.chronicle.peakDoom.value") == 14
        assert "DOWN" in env.eval("gameState.chronicle.days[3].headline")

    def test_down_and_revive_counters(self, env):
        add_char(env, "White", "James")
        add_char(env, "Green", "Ellie")
        env.execute("gameState.activeChars.White.health = 0")
        env.globals().checkDownState("White")
        assert env.eval("gameState.chronicle.downs") == 1
        env.execute("gameState.activeChars.Green.location = gameState.activeChars.White.location")
        env.globals().reviveCharacter("Green", "White")
        assert env.eval("gameState.chronicle.revives") == 1

    def test_week_in_review_shows_on_victory(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.day = 7; gameState.doom = 20; gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        assert any("WEEK IN REVIEW" in m for m in broadcasts(env))

    def test_chronicle_survives_save_load(self, env):
        env.globals().recordMealInChronicle("Ellie")
        saved = env.globals().onSave()
        env.globals().onLoad(saved)
        assert env.eval("gameState.chronicle.meals.Ellie") == 1


# ---------------------------------------------------------------------------
# Nothing Left to Lose — the Doom-25 buff (design_batch2.md §1)
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
        add_char(env, "White", "James", health=5, location="RaymanHouse")
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

    def test_rules_panel_label_shows_both_faces(self, env):
        label = env.eval("DOOM_THRESHOLD_RULES[4][2]")
        assert "Nothing Left to Lose" in label
        assert "any phase" in label  # the original penalty is still stated


# ---------------------------------------------------------------------------
# Signature Moves (Design §6.7, design_batch2.md §2)
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
        add(py_to_lua(env, {"tags": ["ResourceBag:Food"], "position": [40, 1, 40]}))
        for _ in range(food):
            add(py_to_lua(env, {"tags": ["Resource", "Resource:Food"], "position": [20, 1, 20]}))

    def test_feast_spends_one_action_zeroes_food_frees_cooking(self, env):
        self._ellie_with_food(env, food=3)
        assert env.globals().doSignature("Green") is True
        assert env.eval("gameState.activeChars.Green.actionsLeft") == 2   # the single action
        assert env.eval("gameState.activeChars.Green.feastActive") is True
        assert lua_to_py(env.globals().getPlayerResources("Green"))["Food"] == 0
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

class TestPry:
    def _world(self, env, sealed_tag=None, basement=False):
        add_char(env, "White", "James", location="JamesHouse")
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:JamesHouse"], "position": [0, 1, 0]}))
        for res in ["Wood", "Metal", "Cloth", "Food", "EnergyDrink", "Battery"]:
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

class TestTelemetry:
    def test_session_log_round_trips_through_json(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.day = 5; gameState.doom = 18; gameState.gameOverCause = 'victory'")
        log = _json.loads(env.globals().exportSessionLog())
        assert log["schema"] == 1
        assert log["outcome"]["cause"] == "victory"
        assert log["outcome"]["day"] == 5
        assert log["outcome"]["doom"] == 18
        names = [c["name"] for c in log["finalCharacters"]]
        assert names == ["James"]

    def test_setup_facts_recorded(self, env):
        add_char(env, "White", "James")
        add_char(env, "Green", "Ellie")
        env.execute("""
            gameState.playerCount = 2
            gameState.turnOrder = {"White", "Green"}
            gameState.turnStyle = "rotate"
            gameState.pathVariant = "Compact"
            gameState.difficulty = "nightmare"
        """)
        env.globals().recordSetupInChronicle()
        setup = _json.loads(env.globals().exportSessionLog())["setup"]
        assert setup["playerCount"] == 2
        assert setup["roster"] == ["James", "Ellie"]
        assert setup["turnStyle"] == "rotate"
        assert setup["difficulty"] == "nightmare"

    def test_turn_durations_accumulate(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.day = 2")
        env.globals().markTurnStart()
        env.execute("gameState.turnStartedAt = gameState.turnStartedAt - 7")  # 7s ago
        env.globals().recordTurnEnd("White")
        turns = lua_to_py(env.eval("gameState.chronicle.turns"))
        assert len(turns) == 1
        assert turns[0]["name"] == "James"
        assert turns[0]["day"] == 2
        assert turns[0]["seconds"] >= 7
        # a second end without a start records nothing
        env.globals().recordTurnEnd("White")
        assert env.eval("#gameState.chronicle.turns") == 1

    def test_beats_record_signature_and_press_kill(self, env):
        add_char(env, "White", "James")
        env.globals().doSignature("White")                    # All-Nighter fires
        script_dice(env, [5, 6])                              # hit; press kills
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "T", "hp": 2, "attack": 0}))
        env.globals().pressAttack("White", False)
        beats = _json.loads(env.globals().exportSessionLog())["beats"]
        assert beats["pressKills"] == 1
        assert beats["signaturesUsed"] == ["James"]

    def test_telemetry_survives_save_load(self, env):
        add_char(env, "White", "James")
        env.globals().recordBeat("dare")
        saved = env.globals().onSave()
        env2 = make_env()
        env2.globals().onLoad(saved)
        assert env2.eval("gameState.chronicle.beats.daresTaken") == 1


# ---------------------------------------------------------------------------
# Difficulty modes (Design §17.2, design_batch4.md W3)
# ---------------------------------------------------------------------------

class TestDifficulty:
    def test_standard_is_the_default(self, env):
        assert env.globals().getTotalDays() == 7
        assert env.globals().getDoomLimit() == 30
        assert env.globals().getPhaseForDay(1) == 1
        assert env.globals().getPhaseForDay(7) == 4

    def test_weekend_three_days_half_track(self, env):
        env.execute('gameState.difficulty = "weekend"')
        assert env.globals().getTotalDays() == 3
        assert env.globals().getDoomLimit() == 15
        # Phase 1 + half of Phase 2
        assert [env.globals().getPhaseForDay(d) for d in (1, 2, 3)] == [1, 1, 2]

    def test_weekend_defeat_at_15(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.difficulty = "weekend"; gameState.doom = 15')
        assert env.globals().checkDefeat() is True
        assert env.eval("gameState.gameOverCause") == "defeat_doom"

    def test_weekend_victory_on_day_3_tick(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.difficulty = "weekend"; gameState.day = 3; '
                    'gameState.doom = 8; gameState.jamesEnergyDrinkUsed = true')
        env.globals().resolveTick()
        assert env.eval("gameState.gameOverCause") == "victory"

    def test_weekend_day3_gets_the_last_dawn(self, env):
        env.execute('gameState.difficulty = "weekend"; gameState.day = 3; gameState.phase = 2')
        env.globals().revealDawnCard()
        assert env.eval("gameState.activeDawn.id") == "LAST_DAWN"

    def test_nightmare_skips_phase_one_and_raises_doom(self, env):
        env.execute('gameState.difficulty = "nightmare"; gameState.playerCount = 4')
        assert env.globals().getTotalDays() == 7
        assert [env.globals().getPhaseForDay(d) for d in (1, 2, 3, 5, 7)] == [2, 2, 2, 3, 4]
        env.execute("gameState.phase = 2")
        assert env.globals().getDoomRate() == 2   # base 1 + nightmare 1

    def test_standard_rates_unchanged(self, env):
        env.execute("gameState.playerCount = 4; gameState.phase = 4")
        assert env.globals().getDoomRate() == 2


# ---------------------------------------------------------------------------
# 3-player composition reliefs (design_batch4.md W2, §20.1)
# ---------------------------------------------------------------------------

class TestThreePlayerReliefs:
    def _rayman(self, env, players=3):
        add_char(env, "Yellow", "Rayman")
        env.execute(f"gameState.playerCount = {players}; gameState.jamesEnergyDrinkUsed = true")

    def test_quiet_day_eases_big_appetite_at_3p(self, env):
        self._rayman(env, players=3)
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Yellow.hunger") == 9   # -1, relieved

    def test_fighting_day_costs_full_appetite_at_3p(self, env):
        self._rayman(env, players=3)
        env.execute("gameState.raymanFoughtToday = true")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Yellow.hunger") == 8   # -2

    def test_two_tiles_moved_costs_full_appetite_at_3p(self, env):
        self._rayman(env, players=3)
        env.execute("gameState.raymanTilesMovedToday = 2")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Yellow.hunger") == 8   # -2

    def test_no_relief_at_four_players(self, env):
        self._rayman(env, players=4)
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Yellow.hunger") == 8   # -2 as always

    def test_loud_needs_three_tiles_at_3p(self, env):
        self._rayman(env, players=3)
        env.execute("gameState.raymanMovedToday = true; gameState.raymanTilesMovedToday = 2")
        assert env.globals().raymanLoudTonight() is False
        env.execute("gameState.raymanTilesMovedToday = 3")
        assert env.globals().raymanLoudTonight() is True

    def test_loud_fires_on_any_move_at_4p(self, env):
        self._rayman(env, players=4)
        env.execute("gameState.raymanMovedToday = true; gameState.raymanTilesMovedToday = 1")
        assert env.globals().raymanLoudTonight() is True

    def test_combat_marks_rayman_fought(self, env):
        self._rayman(env, players=3)
        script_dice(env, [3, 3])   # two dice, whiff, no counter
        env.globals().resolveCombat("Yellow", py_to_lua(env, {"name": "T", "hp": 3, "attack": 0}))
        assert env.eval("gameState.raymanFoughtToday") is True


# ---------------------------------------------------------------------------
# Charlie (Design §15.4)
# ---------------------------------------------------------------------------

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

class TestTick:
    def test_base_decay_and_day_advance(self, env):
        add_char(env, "Green", "Ellie")
        env.execute("gameState.day = 2; gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Green.hunger") == 9   # -1
        assert env.eval("gameState.activeChars.Green.sanity") == 7   # -1
        assert env.eval("gameState.day") == 3
        assert env.eval("gameState.subPhase") == "PreDawn"

    def test_rayman_big_appetite(self, env):
        add_char(env, "Yellow", "Rayman")
        env.execute("gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Yellow.hunger") == 8  # -2

    def test_james_wired_penalty(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.jamesEnergyDrinkUsed = false")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.White.sanity") == 7   # -1 tick, -2 Wired

    def test_starvation_damage_at_zero_hunger(self, env):
        add_char(env, "Green", "Ellie", hunger=1)
        env.execute("gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Green.hunger") == 0
        assert env.eval("gameState.activeChars.Green.health") == 7   # starving

    def test_down_at_zero_health_feeds_doom(self, env):
        add_char(env, "Green", "Ellie", health=1, hunger=1)
        add_char(env, "White", "James")  # second survivor so it's not a full defeat
        env.execute("gameState.jamesEnergyDrinkUsed = true; gameState.doom = 5")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Green.down") is True
        assert env.eval("gameState.doom") == 6  # a fallen friend feeds the dark

    def test_victory_on_day_7_tick(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.day = 7; gameState.doom = 20; gameState.jamesEnergyDrinkUsed = true")
        env.globals().resolveTick()
        assert env.eval("gameState.subPhase") == "GameOver"
        assert any("VICTORY" in m for m in broadcasts(env))

    def test_day7_defeat_if_source_still_stands(self, env):
        # Design §16.3(3): the Source is mandatory — surviving around it is a loss.
        add_char(env, "White", "James")
        env.execute("gameState.day = 7; gameState.doom = 20; gameState.jamesEnergyDrinkUsed = true")
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:EllieLucaHouse"], "position": [0, 1, 0]}))
        add(py_to_lua(env, {"tags": ["Boss", "Boss:TheSource"], "position": [1, 1, 1]}))
        env.globals().resolveTick()
        assert env.eval("gameState.subPhase") == "GameOver"
        assert env.eval("gameState.gameOverCause") == "defeat_source"
        assert any("SOURCE STILL STANDS" in m for m in broadcasts(env))

    def test_day7_victory_once_source_marked_defeated(self, env):
        # markBossDefeated (combat.lua) overrides the standee check — a killed
        # Source left standing on the table doesn't block the win.
        add_char(env, "White", "James")
        env.execute("gameState.day = 7; gameState.doom = 20; gameState.jamesEnergyDrinkUsed = true")
        add = env.eval("TTS.addObject")
        add(py_to_lua(env, {"tags": ["Location:EllieLucaHouse"], "position": [0, 1, 0]}))
        add(py_to_lua(env, {"tags": ["Boss", "Boss:TheSource"], "position": [1, 1, 1]}))
        env.globals().markBossDefeated("The Source")
        env.globals().resolveTick()
        assert env.eval("gameState.subPhase") == "GameOver"
        assert env.eval("gameState.gameOverCause") == "victory"

    def test_defeat_at_doom_30(self, env):
        add_char(env, "White", "James")
        env.execute("gameState.doom = 30")
        assert env.globals().checkDefeat() is True
        assert env.eval("gameState.subPhase") == "GameOver"

    def test_defeat_when_all_down(self, env):
        add_char(env, "White", "James", down=True)
        add_char(env, "Green", "Ellie", down=True)
        assert env.globals().checkDefeat() is True

    def test_no_defeat_while_someone_stands(self, env):
        add_char(env, "White", "James", down=True)
        add_char(env, "Green", "Ellie")
        env.execute("gameState.doom = 29")
        assert env.globals().checkDefeat() is False


class TestRevive:
    def test_revive_costs_and_half_stats(self, env):
        add_char(env, "White", "James", location="RaymanHouse")
        add_char(env, "Yellow", "Rayman", down=True, health=0, location="RaymanHouse")
        ok = env.globals().reviveCharacter("White", "Yellow")
        assert ok is True
        assert env.eval("gameState.activeChars.White.health") == 6         # paid 2
        assert env.eval("gameState.activeChars.Yellow.down") is False
        assert env.eval("gameState.activeChars.Yellow.health") == 6        # ceil(12/2)
        assert env.eval("gameState.activeChars.Yellow.hunger") == 5        # ceil(10/2)
        assert env.eval("gameState.activeChars.Yellow.sanity") == 3        # ceil(6/2)

    def test_revive_requires_same_location(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        add_char(env, "Yellow", "Rayman", down=True, location="RaymanHouse")
        assert env.globals().reviveCharacter("White", "Yellow") is False
        assert env.eval("gameState.activeChars.Yellow.down") is True


# ---------------------------------------------------------------------------
# Day turn structure: Rotation variant (day_loop.lua, Design §11.2)
# ---------------------------------------------------------------------------

class TestRotationVariant:
    def _two_player_day(self, env):
        add_char(env, "White", "James")
        add_char(env, "Green", "Ellie")
        env.execute("""
            gameState.turnOrder = {"White", "Green"}
            gameState.turnStyle = "rotate"
            gameState.subPhase = "Day"
            gameState.turnIndex = 1
            gameState.activeColor = "White"
            gameState.actedThisVisit = false
        """)

    def test_one_action_per_visit(self, env):
        self._two_player_day(env)
        assert env.globals().spendAction("White", "Rest") is True
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2
        # second action in the same visit is refused; nothing is spent
        assert env.globals().spendAction("White", "Rest") is False
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2

    def test_pass_after_acting_banks_actions_and_wraps(self, env):
        self._two_player_day(env)
        env.globals().spendAction("White", "Rest")
        env.globals().endPlayerTurn("White")
        # White banked 2 actions; priority moved to Green
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2
        assert env.eval("gameState.activeColor") == "Green"
        env.globals().spendAction("Green", "Rest")
        env.globals().endPlayerTurn("Green")
        # wraps back to White, who still holds the banked actions
        assert env.eval("gameState.activeColor") == "White"
        assert env.eval("gameState.activeChars.White.actionsLeft") == 2

    def test_pass_without_acting_forfeits(self, env):
        self._two_player_day(env)
        env.globals().endPlayerTurn("White")
        assert env.eval("gameState.activeChars.White.actionsLeft") == 0
        assert env.eval("gameState.activeColor") == "Green"

    def test_undo_reopens_the_visit(self, env):
        self._two_player_day(env)
        env.globals().spendAction("White", "Rest")
        env.globals().doUndo("White")
        # the undone action no longer counts as this visit's one action
        assert env.eval("gameState.activeChars.White.actionsLeft") == 3
        assert env.globals().spendAction("White", "Gather") is True

    def test_full_mode_multiple_actions_per_turn(self, env):
        add_char(env, "White", "James")
        env.execute("""
            gameState.turnOrder = {"White"}
            gameState.turnStyle = "full"
            gameState.subPhase = "Day"
            gameState.turnIndex = 1
            gameState.activeColor = "White"
        """)
        assert env.globals().spendAction("White", "Rest") is True
        assert env.globals().spendAction("White", "Rest") is True
        assert env.eval("gameState.activeChars.White.actionsLeft") == 1


# ---------------------------------------------------------------------------
# Scenarios (setup.lua, Design §17.3)
# ---------------------------------------------------------------------------

class TestScenarios:
    def test_apply_scenario_sets_flags(self, env):
        env.globals().applyScenario("SC_WINTER")
        assert env.eval("gameState.scenario") == "SC_WINTER"
        assert env.eval("gameState.scenarioFlags.hungerDecayX2") is True

    def test_winter_doubles_hunger_decay_at_tick(self, env):
        add_char(env, "Green", "Ellie")
        env.execute("gameState.jamesEnergyDrinkUsed = true")
        env.globals().applyScenario("SC_WINTER")
        env.globals().resolveTick()
        assert env.eval("gameState.activeChars.Green.hunger") == 8  # -2, doubled

    def test_summer_trims_max_hunger(self, env):
        add_char(env, "Green", "Ellie")
        env.globals().applyScenario("SC_SUMMER")
        assert env.eval("gameState.activeChars.Green.maxHunger") == 8
        assert env.eval("gameState.activeChars.Green.hunger") == 8

    def test_unknown_scenario_is_rejected(self, env):
        env.globals().applyScenario("SC_NOPE")
        assert env.eval("gameState.scenario") is None


# ---------------------------------------------------------------------------
# Night light check (night.lua)
# ---------------------------------------------------------------------------

class TestLightCheck:
    def _tile(self, env, loc="JamesHouse", pos=(0, 1, 0)):
        env.eval("TTS.addObject")(py_to_lua(env, {"tags": [f"Location:{loc}"], "position": list(pos)}))

    def test_no_light_when_world_empty(self, env):
        add_char(env, "White", "James")
        assert env.globals().checkPlayerHasLight("White") is False

    def test_flashlight_in_hand_counts(self, env):
        add_char(env, "White", "James")
        self._tile(env)
        env.execute('TTS.setHand("White", { TTS.makeObject({tags={"M_FLASHLIGHT"}}) })')
        assert env.globals().checkPlayerHasLight("White") is True

    def test_flashlight_useless_on_fire_only_night(self, env):
        add_char(env, "White", "James")
        self._tile(env)
        env.execute('TTS.setHand("White", { TTS.makeObject({tags={"M_FLASHLIGHT"}}) })')
        env.execute("gameState.ongoingDawnEffects.flashlightsDisabled = true")
        assert env.globals().checkPlayerHasLight("White") is False

    def test_fire_kit_still_works_on_fire_only_night(self, env):
        add_char(env, "White", "James")
        self._tile(env)
        env.execute('TTS.setHand("White", { TTS.makeObject({tags={"M_FIRE_KIT"}}) })')
        env.execute("gameState.ongoingDawnEffects.flashlightsDisabled = true")
        assert env.globals().checkPlayerHasLight("White") is True

    def test_campfire_at_tile_covers_everyone(self, env):
        add_char(env, "Red", "Coco", location="BasketballCourt")
        self._tile(env, "BasketballCourt", (10, 1, 10))
        env.eval("TTS.addObject")(py_to_lua(env, {"tags": ["M_CAMPFIRE"], "position": [12, 1, 10]}))
        assert env.globals().checkPlayerHasLight("Red") is True

    def test_distant_campfire_does_not_count(self, env):
        add_char(env, "Red", "Coco", location="BasketballCourt")
        self._tile(env, "BasketballCourt", (10, 1, 10))
        env.eval("TTS.addObject")(py_to_lua(env, {"tags": ["M_CAMPFIRE"], "position": [30, 1, 30]}))
        assert env.globals().checkPlayerHasLight("Red") is False

    def test_nickname_fallback_matches_lantern(self, env):
        add_char(env, "White", "James")
        self._tile(env)
        env.execute('TTS.setHand("White", { TTS.makeObject({nickname="Camping Lantern"}) })')
        assert env.globals().checkPlayerHasLight("White") is True


# ---------------------------------------------------------------------------
# In-TTS self-test (lua/selftest.lua) — driven headlessly against a fully
# populated stub world. In TTS it runs from the console: runSelfTest()
# ---------------------------------------------------------------------------

def populate_full_world(env):
    """Every component auditFirstLoad() checks for, plus playable decks."""
    add = env.eval("TTS.addObject")

    def obj(tags, **kw):
        spec = {"tags": tags, "position": kw.pop("position", [0, 1, 0])}
        spec.update(kw)
        add(py_to_lua(env, spec))

    positions = {"JamesHouse": [-10, 1, 0], "RaymanHouse": [10, 1, 0],
                 "EllieLucaHouse": [0, 1, 8], "BasketballCourt": [-10, 1, -10],
                 "BadmintonCourt": [10, 1, -10]}
    obj(["MainBoard"])
    for loc, pos in positions.items():
        obj([f"Location:{loc}"], position=pos)
    obj(["DoomMarker"])
    obj(["DayCounter"])
    obj(["SeverityLegend"])
    obj(["TelltaleHeartSupply"])
    obj(["BossPool"])
    for name in ["James", "Coco", "Rayman", "Ellie", "Luca"]:
        obj([f"Character:{name}"])
        obj([f"PlayerBoard:{name}"], position=[20, 1, 20])
    for res in ["Wood", "Metal", "Cloth", "Food", "EnergyDrink", "Battery"]:
        obj([f"ResourceBag:{res}"])
    for i in range(5):
        obj([f"MarketSlot:{i}"])
    # Decks with enough contained cards to draw from
    for p in range(1, 5):
        cards = [{"nickname": f"P{p}_TEST_CARD_{i}", "tags": [f"P{p}_TEST_CARD_{i}"]} for i in range(6)]
        obj([f"PhaseCard:P{p}Deck"], contained=cards)
    obj(["MarketCardDeck"], contained=[{"nickname": f"M_TEST_{i}"} for i in range(10)])
    obj(["ThreatCardDeck"], contained=[{"nickname": f"T_TEST_{i}"} for i in range(10)])
    obj(["VisitorCardDeck"], contained=[{"nickname": f"V_TEST_{i}"} for i in range(4)])


class TestSelfTest:
    def test_runselftest_passes_headlessly(self, env):
        populate_full_world(env)
        env.globals().onLoad("")
        flush(env)
        env.globals().runSelfTest()
        flush(env)
        assert env.eval("SELFTEST.done") is True, "self-test never reached its summary"
        results = lua_to_py(env.eval("SELFTEST.results"))
        results = list(results.values()) if isinstance(results, dict) else list(results)
        failures = [r for r in results if "FAIL" in r]
        assert not failures, "in-TTS self-test steps failed:\n" + "\n".join(failures)
        assert env.eval("SELFTEST.passed") >= 15, (
            f"only {env.eval('SELFTEST.passed')} checks ran — self-test lost steps?")

    def test_runselftest_reports_missing_components(self, env):
        # With an empty table the audit step must FAIL loudly, not crash.
        env.globals().onLoad("")
        flush(env)
        env.globals().runSelfTest()
        flush(env)
        assert env.eval("SELFTEST.done") is True
        assert env.eval("SELFTEST.failed") > 0, (
            "self-test reported success on an empty table — audit step is broken")


# ---------------------------------------------------------------------------
# Dawn effect dispatch — every entry's apply() runs without hard error
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
