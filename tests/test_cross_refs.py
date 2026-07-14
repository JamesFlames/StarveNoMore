"""Cross-artifact consistency: CSVs <-> Lua dispatch tables <-> build scripts <-> art.

This is where the drift bugs live (e.g. the threat-deck atlas overflow):
one artifact changes and its mirror doesn't.
"""
import glob
import json as _json
import os
import re

from conftest import (
    ART_DIR,
    LUA_DIR,
    SCRIPTS,
    read_csv_rows,
    read_text,
)

DAWN_CSVS = ["cards_phase1.csv", "cards_phase2.csv", "cards_phase3.csv", "cards_phase4.csv"]


def dawn_effects_source():
    """The whole dawn_effects module, concatenated. It is split across
    effects/dawn_effects*.lua (core + per-phase + dispatch), so read them all
    so the DAWN_EFFECTS / DAWN_MANUAL_STEPS checks see every entry."""
    parts = sorted(glob.glob(os.path.join(LUA_DIR, "effects", "dawn_effects*.lua")))
    return "\n".join(read_text(p) for p in parts)


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
# Atlas manifest vs card counts vs built save (regression for the grid-
# overflow bug class). Grids are DERIVED by generate_card_atlases.py and
# recorded in art/decks/atlas_manifest.json; build_save.py reads that file,
# so these tests check the manifest is current and the built save agrees.
# --------------------------------------------------------------------------

DECK_FACES = {
    "cards_phase1.csv": "phase1_face.png",
    "cards_phase2.csv": "phase2_face.png",
    "cards_phase3.csv": "phase3_face.png",
    "cards_phase4.csv": "phase4_face.png",
    "cards_market.csv": "market_face.png",
    "cards_recipes.csv": "recipe_face.png",
    "cards_threats.csv": "threat_face.png",
    "cards_visitors.csv": "visitor_face.png",
    "cards_trophies.csv": "trophy_face.png",
    "cards_starting.csv": "starting_face.png",
}


def load_atlas_manifest():
    path = os.path.join(ART_DIR, "decks", "atlas_manifest.json")
    assert os.path.isfile(path), (
        "art/decks/atlas_manifest.json missing — run scripts/generate_card_atlases.py")
    with open(path, "r", encoding="utf-8") as f:
        return _json.load(f)


def test_atlas_manifest_is_current_and_capacious():
    manifest = load_atlas_manifest()
    problems = []
    for csv_name, face in sorted(DECK_FACES.items()):
        entry = manifest.get(csv_name)
        if not entry:
            problems.append(f"{csv_name}: no manifest entry — rerun generate_card_atlases.py")
            continue
        n = len(read_csv_rows(csv_name))
        if entry["cards"] != n:
            problems.append(
                f"{csv_name}: atlas rendered for {entry['cards']} cards, CSV has {n} — "
                "stale atlases, rerun generate_card_atlases.py")
        if entry["cols"] * entry["rows"] < n:
            problems.append(
                f"{csv_name}: grid {entry['cols']}x{entry['rows']} cannot hold {n} cards")
        if entry.get("face") != face:
            problems.append(f"{csv_name}: manifest face {entry.get('face')!r} != {face!r}")
        if not os.path.isfile(os.path.join(ART_DIR, "decks", face)):
            problems.append(f"{face}: atlas image missing on disk")
    assert not problems, "\n".join(problems)


def test_built_save_grids_match_manifest():
    """Every CustomDeck in the built save must slice its atlas with the grid
    the atlas was actually rendered at, or cards show wrong faces."""
    from conftest import ROOT
    save_path = os.path.join(ROOT, "saves", "StarveNoMore.json")
    assert os.path.isfile(save_path), "saves/StarveNoMore.json missing — run build_save.py"
    with open(save_path, "r", encoding="utf-8") as f:
        save = _json.load(f)

    grids = {}   # face filename -> set of (w, h) seen in the save

    def walk(node):
        if isinstance(node, dict):
            if "FaceURL" in node and "NumWidth" in node:
                face = os.path.basename(node["FaceURL"])
                grids.setdefault(face, set()).add((node["NumWidth"], node["NumHeight"]))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(save)

    manifest = load_atlas_manifest()
    problems = []
    for csv_name, face in sorted(DECK_FACES.items()):
        entry = manifest[csv_name]
        expected = (entry["cols"], entry["rows"])
        seen = grids.get(face)
        if not seen:
            problems.append(f"{face}: no CustomDeck in the built save references it")
        elif seen != {expected}:
            problems.append(f"{face}: save grids {sorted(seen)} != manifest {expected}")
    assert not problems, "\n".join(problems)


# --------------------------------------------------------------------------
# Card ids hardcoded in Lua must exist in the CSVs
# --------------------------------------------------------------------------

CARD_ID_RE = re.compile(r'"((?:P[1-4]|M|R|T|TR|V|SC|S)_[A-Z][A-Z0-9_]*)"')


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
# Built-save object contracts: tooltip tags, starting-hand decks, slot mirror
# --------------------------------------------------------------------------

def _load_built_save():
    from conftest import ROOT
    save_path = os.path.join(ROOT, "saves", "StarveNoMore.json")
    assert os.path.isfile(save_path), "saves/StarveNoMore.json missing — run build_save.py"
    with open(save_path, "r", encoding="utf-8") as f:
        return _json.load(f)


def _all_save_tags(save):
    tags = set()

    def walk(node):
        if isinstance(node, dict):
            for t in node.get("Tags", []) or []:
                tags.add(t)
            for key in ("ObjectStates", "ContainedObjects"):
                for child in node.get(key, []) or []:
                    walk(child)
            for sp in node.get("AttachedSnapPoints", []) or []:
                for t in sp.get("Tags", []) or []:
                    tags.add(t)

    walk({"ObjectStates": save.get("ObjectStates", [])})
    return tags


def test_tooltip_data_tags_exist_in_save():
    """Every TOOLTIP_DATA key must be a tag some object in the built save
    actually carries — otherwise applyTooltips() silently does nothing for it."""
    src = read_text(os.path.join(LUA_DIR, "ui_controls.lua"))
    m = re.search(r"TOOLTIP_DATA\s*=\s*\{(.*?)\n\}", src, re.S)
    assert m, "TOOLTIP_DATA table not found in ui_controls.lua"
    keys = set(re.findall(r'\["([^"]+)"\]\s*=', m.group(1)))
    assert keys, "no TOOLTIP_DATA keys parsed (format changed? update test)"

    tags = _all_save_tags(_load_built_save())
    missing = sorted(k for k in keys if k not in tags)
    assert not missing, f"TOOLTIP_DATA keys matching no object tag in the save: {missing}"


def test_starting_hand_decks_in_save_match_csv():
    """One StartingHand:<name> deck per character, holding exactly the CSV's
    cards (count column included)."""
    expected = {}
    for r in read_csv_rows("cards_starting.csv"):
        expected[r["character"]] = expected.get(r["character"], 0) + int(r["count"])

    save = _load_built_save()
    found = {}
    for obj in save.get("ObjectStates", []):
        for tag in obj.get("Tags", []):
            m = re.match(r"StartingHand:(\w+)$", tag)
            if m:
                found[m.group(1)] = len(obj.get("ContainedObjects", []))

    assert found == expected, (
        f"starting-hand decks in the save {found} != cards_starting.csv {expected} — "
        "rerun scripts/build_save.py (and generate_card_atlases.py if counts changed)")


def test_char_slot_offsets_mirror_helpers():
    """build_save.py bakes initial standee positions with CHAR_SLOT_X/Z;
    lua/helpers.lua recomputes the same slots at runtime (getCharSlotPosition).
    If they drift, standees teleport at the first move."""
    helpers = read_text(os.path.join(LUA_DIR, "helpers.lua"))
    m = re.search(
        r"Vector\(\s*(-?[\d.]+)\s*\+\s*i\s*\*\s*([\d.]+)\s*,\s*[\d.]+\s*,\s*(-?[\d.]+)\s*\)",
        helpers)
    assert m, "getCharSlotPosition offset expression not found in helpers.lua (update test)"
    base_x, step, z = float(m.group(1)), float(m.group(2)), float(m.group(3))

    idx = dict(re.findall(r"(\w+)\s*=\s*(\d)", re.search(
        r"CHAR_SLOT_INDEX\s*=\s*\{(.*?)\}", helpers, re.S).group(1)))
    assert set(idx) == {"James", "Coco", "Rayman", "Ellie", "Luca"}

    build = read_text(os.path.join(SCRIPTS, "build_save.py"))
    bx = dict(re.findall(r'"(\w+)":\s*(-?[\d.]+)', re.search(
        r"CHAR_SLOT_X\s*=\s*\{(.*?)\}", build, re.S).group(1)))
    bz = float(re.search(r"CHAR_SLOT_Z\s*=\s*(-?[\d.]+)", build).group(1))

    problems = []
    if abs(bz - z) > 1e-9:
        problems.append(f"CHAR_SLOT_Z {bz} != helpers z {z}")
    for name, i in idx.items():
        expected_x = base_x + int(i) * step
        got = bx.get(name)
        if got is None or abs(float(got) - expected_x) > 1e-9:
            problems.append(f"{name}: build_save x {got} != helpers slot {expected_x}")
    assert not problems, "\n".join(problems)


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
