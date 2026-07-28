"""Achievements: the roster/rules contract, the vault, and the unlock rules.

Two lists that must agree (content/achievements.csv and ACHIEVEMENT_RULES) are
exactly the shape of drift this suite exists to prevent — see the "prefer a
test over a reminder" convention in tests/CLAUDE.md. The rest of the module
runs each predicate against the smallest game state that should satisfy it, so
a rule that quietly stops matching (a renamed chronicle field, a boss flag
that moves) fails here rather than at somebody's table.
"""
import csv
import json
import os
import re

import pytest
from conftest import CONTENT, ROOT, add_char, lua_to_py, make_env, read_text

pytest.importorskip("lupa")

CSV_PATH = os.path.join(CONTENT, "achievements.csv")


def csv_rows():
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if (r.get("id") or "").strip()]


# --------------------------------------------------------------------------
# The CSV itself
# --------------------------------------------------------------------------

def test_api_names_hidden_flags_and_art_notes():
    """Columns test_csv_schema.py's generic id/uniqueness pass doesn't cover.
    api_name is what Steamworks keys on and can never be reused; art_notes is
    the ComfyUI prompt, so an empty one means an icon nobody can generate."""
    rows = csv_rows()
    assert rows, "achievements.csv has no data rows"
    problems = []
    seen_api = set()
    for i, r in enumerate(rows, start=2):
        api = r["api_name"].strip()
        if not re.fullmatch(r"ACH_[A-Z0-9_]+", api):
            problems.append(f"line {i}: api_name {api!r} does not match ACH_[A-Z0-9_]+")
        if api in seen_api:
            problems.append(f"line {i}: duplicate api_name {api}")
        seen_api.add(api)
        if r["hidden"].strip() not in ("0", "1"):
            problems.append(f"line {i}: hidden must be 0 or 1")
        if not r["art_notes"].strip():
            problems.append(f"line {i}: empty art_notes — the ComfyUI prompt comes from it")
    assert not problems, "\n".join(problems)


def test_steam_names_fit_steamworks_limits():
    """Steamworks caps the API name at 64 chars and truncates long display
    strings in the overlay toast; a description past ~200 is unreadable there
    and in the panel alike."""
    problems = []
    for r in csv_rows():
        if len(r["api_name"]) > 64:
            problems.append(f"{r['id']}: api_name is {len(r['api_name'])} chars (max 64)")
        if len(r["name"]) > 40:
            problems.append(f"{r['id']}: name is {len(r['name'])} chars (keep under 40)")
        if len(r["description"]) > 200:
            problems.append(f"{r['id']}: description is {len(r['description'])} chars (keep under 200)")
    assert not problems, "\n".join(problems)


def test_steam_manifest_matches_the_csv():
    path = os.path.join(ROOT, "steam", "achievements.json")
    assert os.path.isfile(path), "steam/achievements.json missing — run scripts/generate_achievement_data.py"
    manifest = json.loads(read_text(path))
    rows = csv_rows()
    assert [a["name"] for a in manifest["achievements"]] == [r["api_name"].strip() for r in rows]
    for a, r in zip(manifest["achievements"], rows):
        assert a["displayName"]["english"] == r["name"].strip()
        assert a["description"]["english"] == r["description"].strip()
        assert a["hidden"] == int(r["hidden"].strip())


# --------------------------------------------------------------------------
# Roster <-> rules <-> art
# --------------------------------------------------------------------------

def test_every_achievement_has_a_rule_and_every_rule_an_achievement(env):
    roster = set(lua_to_py(env.eval("ACHIEVEMENTS")))
    rules = set(lua_to_py(env.eval("ACHIEVEMENT_RULES")))
    assert roster - rules == set(), (
        f"achievements with no rule in achievement_rules.lua: {sorted(roster - rules)}")
    assert rules - roster == set(), (
        f"rules with no achievement in content/achievements.csv: {sorted(rules - roster)}")


def test_order_covers_the_roster_exactly(env):
    order = lua_to_py(env.eval("ACHIEVEMENT_ORDER"))
    roster = lua_to_py(env.eval("ACHIEVEMENTS"))
    assert sorted(order) == sorted(roster)
    assert len(order) == len(set(order)), "duplicate id in ACHIEVEMENT_ORDER"


def test_every_achievement_has_an_icon_on_disk():
    missing = []
    for r in csv_rows():
        base = r["id"].strip()[2:].lower()
        for rel in (f"achievements/{base}.png",
                    f"achievements/steam/{base}.jpg",
                    f"achievements/steam/{base}_gray.jpg"):
            if not os.path.isfile(os.path.join(ROOT, "art", rel)):
                missing.append(f"{r['id']} -> art/{rel}")
    assert not missing, (
        "achievement art missing — run scripts/generate_achievement_icons.py:\n"
        + "\n".join(missing))


def test_the_locked_placeholder_exists():
    assert os.path.isfile(os.path.join(ROOT, "art", "achievements", "locked.png")), (
        "art/achievements/locked.png missing — xml/achievements.xml names it "
        "literally, so the panel renders blank without it")


# --------------------------------------------------------------------------
# The vault
# --------------------------------------------------------------------------

def test_unlocking_is_idempotent_and_counted(env):
    assert env.eval("unlockAchievement")("A_SURVIVOR") is True
    assert env.eval("unlockAchievement")("A_SURVIVOR") is False
    assert env.eval("unlockedAchievementCount")() == 1
    assert env.eval("isAchievementUnlocked")("A_SURVIVOR") is True
    assert env.eval("isAchievementUnlocked")("A_HERO") is False


def test_unknown_id_never_enters_the_vault(env):
    assert env.eval("unlockAchievement")("A_NOT_A_REAL_ONE") is False
    assert env.eval("unlockedAchievementCount")() == 0


def test_a_finished_game_is_counted_once(env):
    assert env.eval("recordGameFinished")() is True
    assert env.eval("recordGameFinished")() is False
    assert env.eval("ensureAchievementVault")().games == 1


def test_code_round_trips_through_a_fresh_table(env):
    env.eval("unlockAchievement")("A_SURVIVOR")
    env.eval("unlockAchievement")("A_TREEGUARD")
    code = env.eval("exportAchievementCode")()
    assert code.startswith("SNM-ACH-1:")

    fresh = make_env()
    imported, skipped, err = fresh.eval("importAchievementCode")(code)
    assert err is None
    assert imported == 2 and skipped == 0
    assert fresh.eval("isAchievementUnlocked")("A_SURVIVOR") is True
    assert fresh.eval("isAchievementUnlocked")("A_TREEGUARD") is True


def test_a_junk_code_is_refused_without_unlocking_anything(env):
    imported, skipped, err = env.eval("importAchievementCode")("hello")
    assert imported == 0 and err
    assert env.eval("unlockedAchievementCount")() == 0


def test_importing_is_silent(env):
    """A restore must not fire 20 toasts and 20 chat lines."""
    env.eval("importAchievementCode")("SNM-ACH-1:A_SURVIVOR,A_HERO,A_TRUTH")
    assert env.eval("unlockedAchievementCount")() == 3
    assert lua_to_py(env.eval("TTS.broadcasts")) in ([], {})


# --------------------------------------------------------------------------
# The rules themselves — one minimal state per achievement
# --------------------------------------------------------------------------

def rule_holds(env, aid):
    return bool(env.eval("ACHIEVEMENT_RULES")[aid]())


def won(env):
    env.execute('gameState.gameOverCause = "victory"')


# state-setter -> the id it should unlock
RULE_CASES = {
    "A_FIRST_NIGHT": 'ensureChronicle().days[1] = { headline = "x", damageTonight = 0 }',
    "A_MIDWEEK":     'ensureChronicle().days[4] = { headline = "x", damageTonight = 0 }',
    "A_TRUTH":       "gameState.clueCount = 3",
    "A_HERO":        "gameState.bossesDefeated = { deerclops = true, eye = true, source = true }",
    "A_DEERCLOPS":   "gameState.bossesDefeated = { deerclops = true }",
    "A_EYE":         "gameState.bossesDefeated = { eye = true }",
    "A_SOURCE":      "gameState.bossesDefeated = { source = true }",
    "A_TREEGUARD":   'table.insert(ensureChronicle().kills, { threat = "Treeguard", who = "Rayman", day = 3, boss = true })',
    "A_CAMP_MOTHER": 'ensureChronicle().meals["Ellie"] = 10',
    "A_HANDY":       'ensureChronicle().usage = { crafted = { Flashlight = 5, Spear = 3 } }',
    "A_WATCH":       "for i = 1, 15 do table.insert(ensureChronicle().kills, { threat = 'T' .. i, day = 1 }) end",
    "A_PRESS":       "ensureChronicle().beats.pressKills = 3",
    "A_DARE":        "ensureChronicle().beats.daresTaken = 5",
    "A_HEART":       "ensureChronicle().revives = 1",
    "A_SPLIT":       "ensureChronicle().beats.sourceSplit = true",
    "A_CHARLIE":     'ensureChronicle().maxCharlieStreak = { value = 3, name = "Luca" }',
}


@pytest.mark.parametrize("aid,setter", sorted(RULE_CASES.items()))
def test_rule_fires_on_its_own_state(env, aid, setter):
    assert not rule_holds(env, aid), f"{aid} fires on an empty game"
    env.execute(setter)
    assert rule_holds(env, aid), f"{aid} did not fire after: {setter}"


def test_winning_unlocks_the_week_but_not_the_variants(env):
    won(env)
    assert rule_holds(env, "A_SURVIVOR")
    assert not rule_holds(env, "A_NIGHTMARE")
    assert not rule_holds(env, "A_WEEKEND")
    assert not rule_holds(env, "A_SOLO")


@pytest.mark.parametrize("aid,setup", [
    ("A_NIGHTMARE", 'gameState.difficulty = "nightmare"'),
    ("A_WEEKEND", 'gameState.difficulty = "weekend"'),
    ("A_SOLO", "gameState.solo = true"),
])
def test_variant_wins_need_both_the_win_and_the_variant(env, aid, setup):
    env.execute(setup)
    assert not rule_holds(env, aid), f"{aid} fires without a win"
    won(env)
    assert rule_holds(env, aid)


def test_down_to_the_wire_needs_a_near_miss(env):
    won(env)
    env.execute("gameState.doom = 20")   # standard limit is 30
    assert not rule_holds(env, "A_WIRE")
    env.execute("gameState.doom = 28")
    assert rule_holds(env, "A_WIRE")


def test_pristine_needs_everyone_up_and_nobody_brought_back(env):
    add_char(env, "White", "Coco")
    add_char(env, "Green", "Rayman")
    won(env)
    assert rule_holds(env, "A_PRISTINE")

    env.execute("ensureChronicle().revives = 1")
    assert not rule_holds(env, "A_PRISTINE"), "a revived team is not pristine"

    env.execute("ensureChronicle().revives = 0")
    env.execute('gameState.activeChars["Green"].down = true')
    assert not rule_holds(env, "A_PRISTINE"), "a fallen team is not pristine"


def test_pristine_is_not_awarded_to_an_empty_roster(env):
    won(env)
    assert not rule_holds(env, "A_PRISTINE")


def test_last_one_standing_wants_exactly_one(env):
    add_char(env, "White", "Coco")
    add_char(env, "Green", "Rayman")
    won(env)
    assert not rule_holds(env, "A_LAST_ONE"), "two standing is not last one standing"
    env.execute('gameState.activeChars["Green"].down = true')
    assert rule_holds(env, "A_LAST_ONE")


def test_all_hands_needs_every_character_and_a_non_empty_table(env):
    assert not rule_holds(env, "A_ALL_HANDS"), "an empty roster satisfies All Hands"
    add_char(env, "White", "Coco", signatureUsed=True)
    add_char(env, "Green", "Rayman")
    assert not rule_holds(env, "A_ALL_HANDS")
    env.execute('gameState.activeChars["Green"].signatureUsed = true')
    assert rule_holds(env, "A_ALL_HANDS")


# --------------------------------------------------------------------------
# Wiring: the checkpoints, and what survives a Restart
# --------------------------------------------------------------------------

def test_checkpoint_unlocks_and_announces(env):
    env.execute("gameState.clueCount = 3")
    assert env.eval("checkAchievements")("test") == 1
    assert env.eval("isAchievementUnlocked")("A_TRUTH") is True
    said = [b["message"] for b in lua_to_py(env.eval("TTS.broadcasts"))]
    assert any("ACHIEVEMENT UNLOCKED" in m and "The Truth" in m for m in said), said


def test_a_broken_rule_costs_only_its_own_achievement(env):
    env.execute('ACHIEVEMENT_RULES.A_TRUTH = function() error("boom") end')
    env.execute("ensureChronicle().revives = 1")
    env.eval("checkAchievements")("test")
    assert env.eval("isAchievementUnlocked")("A_TRUTH") is False
    assert env.eval("isAchievementUnlocked")("A_HEART") is True


def test_game_over_counts_the_game_and_scores_the_week(env):
    env.execute("gameState.started = true")
    add_char(env, "White", "Coco")
    env.execute('gameState.gameOverCause = "victory"')
    env.execute("gameState.day = 7")
    env.eval("showWeekInReview")()
    assert env.eval("isAchievementUnlocked")("A_SURVIVOR") is True
    assert env.eval("isAchievementUnlocked")("A_PRISTINE") is True
    assert env.eval("ensureAchievementVault")().games == 1


def test_surviving_a_day_unlocks_first_night(env):
    """The dayEnd checkpoint runs after showEndOfDaySummary has chronicled the
    day — if it ever moves above that line, First Night silently never fires."""
    env.execute("gameState.started = true")
    env.execute("gameState.day = 1")
    add_char(env, "White", "Coco")
    env.eval("resolveTick")()
    assert env.eval("isAchievementUnlocked")("A_FIRST_NIGHT") is True


def test_restart_keeps_the_vault(env):
    env.eval("unlockAchievement")("A_SURVIVOR")
    env.execute("gameState.started = true")
    env.eval("onHostRestart")(env.eval('{ color = "White" }'), None, "btnRestart")
    env.eval("onConfirmYes")(env.eval('{ color = "White" }'), None, "confirmYes")
    assert env.eval("gameState").started is False, "restart did not reset the game"
    assert env.eval("isAchievementUnlocked")("A_SURVIVOR") is True, (
        "the achievement vault was wiped by Restart — it spans games")


# --------------------------------------------------------------------------
# The panel — TTS renders a wrong id as nothing at all, so check what the
# handlers actually write rather than that they ran.
# --------------------------------------------------------------------------

def ui_attrs(env):
    return lua_to_py(env.eval("TTS.ui"))["attrs"]


def ui_visible(env, panel):
    return lua_to_py(env.eval("TTS.ui"))["visible"].get(panel)


def test_opening_the_panel_fills_the_first_page(env):
    env.eval("unlockAchievement")("A_SURVIVOR")
    env.eval("onAchievementsClick")(env.eval('{ color = "White" }'), None, "achievementsBtn")
    attrs = ui_attrs(env)

    order = lua_to_py(env.eval("ACHIEVEMENT_ORDER"))
    roster = lua_to_py(env.eval("ACHIEVEMENTS"))
    assert attrs["achName_1"]["text"].startswith(roster[order[0]]["name"])
    assert attrs["achIcon_1"]["image"] == roster[order[0]]["icon"]
    assert "of " + str(len(order)) + " unlocked" in attrs["achievementsProgress"]["text"]
    assert attrs["achPageLabel"]["text"] == "Page 1 of 3"
    assert attrs["achPrev"]["active"] == "false", "page 1 offers a Previous button"


def test_a_hidden_achievement_keeps_its_secret_until_earned(env):
    hidden = [aid for aid, meta in lua_to_py(env.eval("ACHIEVEMENTS")).items()
              if meta.get("hidden")]
    assert hidden, "no hidden achievements to check"
    aid = hidden[0]
    name, desc, _status = env.eval("achievementRowText")(aid)
    assert name.startswith("???"), name
    assert lua_to_py(env.eval("ACHIEVEMENTS"))[aid]["description"] not in desc

    env.eval("unlockAchievement")(aid)
    name, desc, status = env.eval("achievementRowText")(aid)
    assert name.startswith(lua_to_py(env.eval("ACHIEVEMENTS"))[aid]["name"])
    assert status.startswith("Unlocked")


def test_the_last_page_blanks_its_unused_rows(env):
    """A stale row left over from the previous page reads as a real
    achievement — TTS just leaves the old text there."""
    total = len(lua_to_py(env.eval("ACHIEVEMENT_ORDER")))
    per_page = int(env.eval("ACH_ROWS_PER_PAGE"))
    env.execute(f"achievementsPage = {env.eval('achievementsPageCount')()}")
    env.eval("refreshAchievementPanel")()
    attrs = ui_attrs(env)
    used = total - (env.eval("achievementsPageCount")() - 1) * per_page
    for row in range(used + 1, per_page + 1):
        assert attrs[f"achRow_{row}"]["active"] == "false", f"row {row} left visible"


def test_an_unlock_raises_a_toast(env):
    env.execute("gameState.clueCount = 3")
    env.eval("checkAchievements")("test")
    assert ui_visible(env, "achToast") is True
    assert ui_attrs(env)["achToastName"]["text"] == (
        lua_to_py(env.eval("ACHIEVEMENTS"))["A_TRUTH"]["name"])


def test_toasts_queue_rather_than_overwrite_each_other(env):
    env.eval("showAchievementToast")("A_SURVIVOR")
    env.eval("showAchievementToast")("A_HERO")
    first = ui_attrs(env)["achToastName"]["text"]
    env.eval("TTS.flushWaits")()
    second = ui_attrs(env)["achToastName"]["text"]
    assert first != second, "the second toast replaced the first instead of queueing"


def test_a_save_from_before_achievements_migrates_clean(env):
    env.execute("gameState.achievements = nil")
    env.eval("migrateGameState")()
    assert env.eval("unlockedAchievementCount")() == 0
    assert env.eval("unlockAchievement")("A_HERO") is True
