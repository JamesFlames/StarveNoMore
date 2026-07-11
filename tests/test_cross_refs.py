"""Cross-artifact consistency: CSVs <-> Lua dispatch tables <-> build scripts <-> art.

This is where the drift bugs live (e.g. the threat-deck atlas overflow):
one artifact changes and its mirror doesn't.
"""
import os
import re

import pytest

from conftest import (
    ART_DIR,
    LUA_DIR,
    SCRIPTS,
    card_ids,
    read_csv_rows,
    read_text,
)

DAWN_CSVS = ["cards_phase1.csv", "cards_phase2.csv", "cards_phase3.csv", "cards_phase4.csv"]


def dawn_effects_source():
    return read_text(os.path.join(LUA_DIR, "effects", "dawn_effects.lua"))


def dawn_card_ids():
    out = set()
    for fn in DAWN_CSVS:
        out |= {r["id"] for r in read_csv_rows(fn)}
    return out


# --------------------------------------------------------------------------
# Dawn cards <-> DAWN_EFFECTS / DAWN_MANUAL_STEPS
# --------------------------------------------------------------------------

def test_every_dawn_card_has_a_scripted_effect():
    src = dawn_effects_source()
    handled = set(re.findall(r'DAWN_EFFECTS\["([A-Z0-9_]+)"\]', src))
    missing = sorted(dawn_card_ids() - handled)
    assert not missing, (
        "Dawn cards with no DAWN_EFFECTS entry (dispatchDawnEffect will do nothing "
        f"for these): {missing}"
    )


def test_scenarios_csv_matches_lua_table():
    """cards_scenarios.csv is the authoring source for the SCENARIOS table in
    setup.lua (design §17.3) — the id sets must not drift."""
    csv_ids = {r["id"] for r in read_csv_rows("cards_scenarios.csv")}
    src = read_text(os.path.join(LUA_DIR, "setup.lua"))
    lua_ids = set(re.findall(r'gameState\.scenario = "(SC_[A-Z0-9_]+)"', src))
    assert csv_ids == lua_ids, (
        f"scenario drift — csv-only: {sorted(csv_ids - lua_ids)}, "
        f"lua-only: {sorted(lua_ids - csv_ids)}"
    )


def test_no_orphan_dawn_effect_entries():
    src = dawn_effects_source()
    handled = set(re.findall(r'DAWN_EFFECTS\["([A-Z0-9_]+)"\]', src))
    orphans = sorted(handled - dawn_card_ids())
    assert not orphans, f"DAWN_EFFECTS entries for cards not in any cards_phase*.csv: {orphans}"


def test_no_orphan_manual_steps():
    src = dawn_effects_source()
    m = re.search(r"DAWN_MANUAL_STEPS\s*=\s*\{(.*?)\n\}", src, re.S)
    assert m, "DAWN_MANUAL_STEPS table not found in dawn_effects.lua"
    keys = set(re.findall(r"^\s*([A-Z][A-Z0-9_]*)\s*=", m.group(1), re.M))
    orphans = sorted(keys - dawn_card_ids())
    assert not orphans, f"DAWN_MANUAL_STEPS keys for nonexistent cards: {orphans}"


# --------------------------------------------------------------------------
# ongoingDawnEffects flags <-> EFFECT_RULES labels (ui_rules.lua)
# --------------------------------------------------------------------------

# Flags that are internal bookkeeping, not player-visible ongoing rules.
EFFECT_FLAG_WHITELIST = {
    "strayCat",            # rendered with its own custom line in ui_rules.lua
    "deerclopsDefeated", "eyeDefeated", "sourceDefeated", "treeguardDefeated",
    "doom10", "doom15", "doom20", "doom25",  # thresholds have their own rule table
}


def test_every_ongoing_effect_flag_has_a_rules_panel_label():
    """agents.md: 'add a label [to EFFECT_RULES] whenever dawn_effects.lua gains a
    new ongoing flag'. Enforce that convention mechanically, across all lua files."""
    flags = set()
    for dirpath, _dirs, files in os.walk(LUA_DIR):
        for fn in files:
            if fn.endswith(".lua"):
                src = read_text(os.path.join(dirpath, fn))
                flags |= set(re.findall(r"ongoingDawnEffects\.(\w+)\s*=", src))
                flags |= set(re.findall(r'ongoingDawnEffects\["(\w+)"\]\s*=', src))

    rules_src = read_text(os.path.join(LUA_DIR, "ui_rules.lua"))
    m = re.search(r"EFFECT_RULES\s*=\s*\{(.*?)\n\}", rules_src, re.S)
    assert m, "EFFECT_RULES table not found in ui_rules.lua"
    labeled = set(re.findall(r"^\s*(\w+)\s*=", m.group(1), re.M))

    unlabeled = sorted(flags - labeled - EFFECT_FLAG_WHITELIST)
    assert not unlabeled, (
        "ongoingDawnEffects flags with no EFFECT_RULES label (invisible to players "
        f"in the Rules panel): {unlabeled}"
    )


def test_effect_rule_order_covers_all_rules():
    rules_src = read_text(os.path.join(LUA_DIR, "ui_rules.lua"))
    m = re.search(r"EFFECT_RULES\s*=\s*\{(.*?)\n\}", rules_src, re.S)
    labeled = set(re.findall(r"^\s*(\w+)\s*=", m.group(1), re.M))
    m2 = re.search(r"EFFECT_RULE_ORDER\s*=\s*\{(.*?)\n\}", rules_src, re.S)
    assert m2, "EFFECT_RULE_ORDER not found in ui_rules.lua"
    ordered = set(re.findall(r'"(\w+)"', m2.group(1)))
    missing = sorted(labeled - ordered)
    assert not missing, f"EFFECT_RULES keys absent from EFFECT_RULE_ORDER (never displayed): {missing}"


# --------------------------------------------------------------------------
# Atlas grid capacity vs card counts (regression for the 6x5 -> 6x8 overflow bug)
# --------------------------------------------------------------------------

def parse_atlas_grids():
    """Read the deck-section grids straight out of generate_card_atlases.py main()."""
    src = read_text(os.path.join(SCRIPTS, "generate_card_atlases.py"))
    main_src = src[src.index("def main("):]
    grids = {}
    # Phase decks: a loop over cards_phase{n}.csv with one build_atlas(cards, W, H)
    phase_m = re.search(
        r'read_csv\(f"cards_phase\{phase_num\}\.csv"\).*?build_atlas\(cards,\s*(\d+),\s*(\d+)\)',
        main_src, re.S)
    assert phase_m, "could not parse phase-deck grid from generate_card_atlases.py"
    for n in range(1, 5):
        grids[f"cards_phase{n}.csv"] = (int(phase_m.group(1)), int(phase_m.group(2)))
    # Flat decks
    for csv_name, w, h in re.findall(
            r'read_csv\("(cards_\w+\.csv)"\).*?build_atlas\(cards,\s*(\d+),\s*(\d+)\)',
            main_src, re.S):
        grids[csv_name] = (int(w), int(h))
    return grids


def test_atlas_grids_hold_every_card():
    grids = parse_atlas_grids()
    expected_decks = {
        "cards_market.csv", "cards_recipes.csv", "cards_threats.csv",
        "cards_visitors.csv", "cards_trophies.csv",
        "cards_phase1.csv", "cards_phase2.csv", "cards_phase3.csv", "cards_phase4.csv",
    }
    assert expected_decks <= set(grids), f"grids not parsed for: {expected_decks - set(grids)}"
    problems = []
    for csv_name, (w, h) in sorted(grids.items()):
        n = len(read_csv_rows(csv_name))
        if n > w * h:
            problems.append(
                f"{csv_name}: {n} cards but atlas grid is {w}x{h} = {w*h} "
                f"(cards beyond capacity are silently dropped)")
    assert not problems, "\n".join(problems)


def test_build_save_grids_match_atlas_generator():
    """TTS slices the atlas by NumWidth/NumHeight in build_save.py; those must
    equal the grid the atlas was rendered with, or cards show wrong faces."""
    atlas = parse_atlas_grids()
    src = read_text(os.path.join(SCRIPTS, "build_save.py"))

    checks = {
        "cards_market.csv": r'ph\("market_face"\).*?num_w=(\d+),\s*num_h=(\d+)',
        "cards_threats.csv": r'ph\("threat_face"\).*?num_w=(\d+),\s*num_h=(\d+)',
        "cards_visitors.csv": r'ph\("visitor_face"\).*?num_w=(\d+),\s*num_h=(\d+)',
        "cards_recipes.csv": r'ph\("recipe_face"\).*?"NumWidth":\s*(\d+),\s*"NumHeight":\s*(\d+)',
        "cards_trophies.csv": r'ph\("trophy_face"\).*?"NumWidth":\s*(\d+),\s*"NumHeight":\s*(\d+)',
    }
    problems = []
    for csv_name, pattern in checks.items():
        m = re.search(pattern, src, re.S)
        if not m:
            problems.append(f"could not find grid for {csv_name} in build_save.py")
            continue
        got = (int(m.group(1)), int(m.group(2)))
        if got != atlas[csv_name]:
            problems.append(f"{csv_name}: build_save.py grid {got} != atlas grid {atlas[csv_name]}")

    # Phase decks: (deck_num, rows, name, nw, nh) tuples
    for deck_num, nw, nh in re.findall(r'\(\s*(\d)\s*,\s*phase\d\s*,\s*"[^"]*"\s*,\s*(\d+),\s*(\d+)\)', src):
        key = f"cards_phase{deck_num}.csv"
        got = (int(nw), int(nh))
        if got != atlas[key]:
            problems.append(f"{key}: build_save.py grid {got} != atlas grid {atlas[key]}")
    assert not problems, "\n".join(problems)


# --------------------------------------------------------------------------
# Card ids hardcoded in Lua must exist in the CSVs
# --------------------------------------------------------------------------

CARD_ID_RE = re.compile(r'"((?:P[1-4]|M|R|T|TR|V|SC)_[A-Z][A-Z0-9_]*)"')


def test_hardcoded_card_ids_exist(card_ids):
    problems = []
    for dirpath, _dirs, files in os.walk(LUA_DIR):
        for fn in files:
            if not fn.endswith(".lua"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), LUA_DIR)
            src = read_text(os.path.join(dirpath, fn))
            for cid in set(CARD_ID_RE.findall(src)):
                prefix = cid.split("_", 1)[0]
                if cid not in card_ids.get(prefix, set()):
                    problems.append(f"{rel}: references {cid!r}, not found in the {prefix}_* CSV")
    assert not problems, "\n".join(sorted(problems))


# --------------------------------------------------------------------------
# MARKET_COSTS <-> cards_market.csv
# --------------------------------------------------------------------------

def test_market_costs_cover_market_deck():
    src = read_text(os.path.join(LUA_DIR, "market_data.lua"))
    cost_ids = set(re.findall(r"^MARKET_COSTS\.([A-Z0-9_]+)\s*=", src, re.M))
    csv_ids = {r["id"] for r in read_csv_rows("cards_market.csv")}
    missing = sorted(csv_ids - cost_ids)
    orphans = sorted(cost_ids - csv_ids)
    assert not missing, f"market cards with no MARKET_COSTS entry (canAfford breaks): {missing}"
    assert not orphans, f"MARKET_COSTS entries for nonexistent cards: {orphans}"


# --------------------------------------------------------------------------
# Assets referenced by build_save.py and assets.lua exist on disk
# --------------------------------------------------------------------------

def test_build_save_asset_map_files_exist():
    src = read_text(os.path.join(SCRIPTS, "build_save.py"))
    m = re.search(r"ASSET_MAP\s*=\s*\{(.*?)\n\}", src, re.S)
    assert m, "ASSET_MAP not found in build_save.py"
    missing = []
    for name, rel in re.findall(r'"(\w+)":\s*"([^"]+\.png)"', m.group(1)):
        if not os.path.isfile(os.path.join(ART_DIR, rel)):
            missing.append(f"{name} -> art/{rel}")
    assert not missing, "ASSET_MAP entries with no file on disk:\n" + "\n".join(missing)


def test_assets_lua_files_exist():
    src = read_text(os.path.join(LUA_DIR, "assets.lua"))
    missing = []
    for rel in re.findall(r'url\("([^"]+\.png)"\)', src):
        if not os.path.isfile(os.path.join(ART_DIR, rel)):
            missing.append(rel)
    assert not missing, "assets.lua URLs with no file under art/:\n" + "\n".join(missing)


# --------------------------------------------------------------------------
# Audio manifest URLs point at files that exist
# --------------------------------------------------------------------------

def test_audio_manifest_files_exist():
    from conftest import ROOT
    src = read_text(os.path.join(LUA_DIR, "audio_manifest.lua"))
    rels = re.findall(r'url\s*=\s*"http://localhost:8080/([^"]+)"', src)
    assert rels, "no URLs parsed from audio_manifest.lua (format changed? update test)"
    missing = [rel for rel in rels if not os.path.isfile(os.path.join(ROOT, *rel.split("/")))]
    assert not missing, "audio_manifest.lua URLs with no file on disk:\n" + "\n".join(missing)
