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
    """docs/agents/ux-affordances.md: 'add a label [to EFFECT_RULES] whenever dawn_effects.lua gains a
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
    "cards_phase1.csv": "phase1_face.jpg",
    "cards_phase2.csv": "phase2_face.jpg",
    "cards_phase3.csv": "phase3_face.jpg",
    "cards_phase4.csv": "phase4_face.jpg",
    "cards_market.csv": "market_face.jpg",
    "cards_recipes.csv": "recipe_face.jpg",
    "cards_threats.csv": "threat_face.jpg",
    "cards_visitors.csv": "visitor_face.jpg",
    "cards_trophies.csv": "trophy_face.jpg",
    "cards_starting.csv": "starting_face.jpg",
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


# --------------------------------------------------------------------------
# scripts/generators.json — the machine-readable "regenerate after editing X"
# map. Keep it honest: outputs/scripts/sources must exist, and every
# AUTO-GENERATED lua file must be listed (so a new generated file can't slip in
# unrecorded).
# --------------------------------------------------------------------------

def _generators_manifest():
    from conftest import ROOT
    with open(os.path.join(ROOT, "scripts", "generators.json"), encoding="utf-8") as f:
        return _json.load(f)["generators"]


def test_generators_manifest_paths_exist():
    from conftest import ROOT
    problems = []
    for g in _generators_manifest():
        if not os.path.exists(os.path.join(ROOT, g["output"])):
            problems.append(f"missing output: {g['output']}")
        if not os.path.exists(os.path.join(ROOT, g["script"])):
            problems.append(f"missing script: {g['script']}")
        for s in g.get("sources", []):
            if not os.path.exists(os.path.join(ROOT, s)):
                problems.append(f"missing source {s} (for {g['output']})")
    assert not problems, "scripts/generators.json is stale:\n" + "\n".join(problems)


def test_generators_manifest_covers_every_generated_lua_file():
    """Every lua/*.lua carrying the AUTO-GENERATED banner must be listed as an
    output in scripts/generators.json — otherwise 'what do I regenerate?' would
    silently miss it."""
    outputs = {g["output"] for g in _generators_manifest()}
    banner_files = set()
    for fn in os.listdir(LUA_DIR):
        if fn.endswith(".lua"):
            head = "\n".join(read_text(os.path.join(LUA_DIR, fn)).splitlines()[:3]).upper()
            # The generated files' own banner reads "AUTO-GENERATED by scripts/…".
            # (Hand-written files may *mention* another file's generation; those
            # say "auto-generated from content/…", not "by scripts/".)
            if "AUTO-GENERATED BY SCRIPTS/" in head:
                banner_files.add("lua/" + fn)
    missing = sorted(banner_files - outputs)
    assert not missing, (
        f"generated lua files not recorded in scripts/generators.json: {missing}")


def test_lua_doom_track_mirrors_board_geometry():
    """moveDoomMarker computes the marker's world position from these Lua
    constants instead of the board's snap points — going through
    board.positionToWorld made the marker's position depend on the board's
    Transform scale and on surviving the path-variant reload, and it landed
    at (-14.2, -15.7), off the board entirely. That means these constants
    must track the printed geometry themselves."""
    import sys
    sys.path.insert(0, SCRIPTS)
    import board_geometry as g

    src = read_text(os.path.join(LUA_DIR, "setup.lua"))
    for name, expected in (("DOOM_STEP0_X", g.DOOM_STEP0_WORLD_X),
                           ("DOOM_STEP30_X", g.DOOM_STEP30_WORLD_X),
                           ("DOOM_TRACK_Z", g.DOOM_TRACK_WORLD_Z)):
        m = re.search(rf"^{name}\s*=\s*(-?[\d.]+)", src, re.M)
        assert m, f"{name} not found in lua/setup.lua"
        assert abs(float(m.group(1)) - expected) < 0.01, (
            f"lua {name}={m.group(1)} but board_geometry says {expected} — "
            "the Doom marker would sit off its printed track")


def test_basketball_ring_clears_the_doom_track():
    """The printed ring around a location must not run through the Doom
    track: 'the basketball court graphic should not overlap the doom
    counter'. Basketball is the tight one — it sits nearest the south edge."""
    import sys
    sys.path.insert(0, SCRIPTS)
    import board_geometry as g
    import path_layouts as pl

    track_top = g.DOOM_TRACK_WORLD_Z + 0.4 + 0.05   # half-cell + a hair
    problems = []
    for loc, (wx, wz) in pl.LOCATION_WORLD.items():
        ring_bottom = wz - pl.LOCATION_RING_R
        if ring_bottom < track_top and abs(wx) < 11:
            problems.append(
                f"{loc}: ring reaches z={ring_bottom:.2f}, Doom track top is "
                f"z={track_top:.2f}")
    assert not problems, (
        "printed location rings overlap the Doom track:\n  " + "\n  ".join(problems))


def test_board_doom_thresholds_mirror_the_lua_table():
    """The ribbons printed on the board must be the thresholds the game
    actually fires. This was a third hand-typed copy of DOOM_THRESHOLDS
    (global.lua has the rules, simulate_balance.py has the sim's copy,
    generate_assets.py had the board's) — and the board is the copy players
    read, so a drift here is a rule the table believes and the code ignores."""
    import sys
    sys.path.insert(0, SCRIPTS)
    import board_geometry as g

    src = read_text(os.path.join(LUA_DIR, "global.lua"))
    body = re.search(r"DOOM_THRESHOLDS\s*=\s*\{(.*?)\n\}", src, re.S)
    assert body, "DOOM_THRESHOLDS not found in lua/global.lua"
    lua_steps = sorted(int(v) for v in re.findall(r"=\s*(\d+)", body.group(1)))
    assert sorted(g.DOOM_THRESHOLDS) == lua_steps, (
        f"board prints ribbons at {sorted(g.DOOM_THRESHOLDS)} but "
        f"checkDoomThresholds fires at {lua_steps}")


def test_every_difficulty_doom_limit_has_a_board():
    """DIFFICULTY_PARAMS decides how long the Doom track is; board_geometry
    decides which track lengths get drawn. A limit with no board falls back
    to the 30-cell art, which is the original bug: 'I picked Long Weekend,
    which says the doom track is halved, but it still goes up to 30'."""
    import sys
    sys.path.insert(0, SCRIPTS)
    import board_geometry as g
    import path_layouts as pl

    src = read_text(os.path.join(LUA_DIR, "global.lua"))
    body = re.search(r"DIFFICULTY_PARAMS\s*=\s*\{(.*?)\n\}", src, re.S)
    assert body, "DIFFICULTY_PARAMS not found in lua/global.lua"
    limits = sorted({int(v) for v in re.findall(r"doomLimit\s*=\s*(\d+)", body.group(1))})
    assert limits, "no doomLimit entries parsed from DIFFICULTY_PARAMS"

    missing = [lim for lim in limits if lim not in g.DOOM_LIMITS]
    assert not missing, (
        f"difficulties use Doom limit(s) {missing} with no board art — add them "
        f"to board_geometry.DOOM_LIMITS (and DOOM_LIMIT_DAYS) and regenerate")

    # ...and the art for each (variant, limit) pair must be on disk.
    absent = [pl.board_art_name(v, lim) + ".png"
              for v in pl.VARIANTS for lim in limits
              if not os.path.isfile(os.path.join(
                  ART_DIR, "board", pl.board_art_name(v, lim) + ".png"))]
    assert not absent, (
        f"missing board images: {absent} — run scripts/generate_assets.py")


def test_lua_knows_a_board_url_for_every_variant_and_doom_limit():
    """applyPathVariant resolves the board image from BOARD_ART_URLS[variant]
    [doomLimit]. A gap silently leaves the previous board printed, so a Long
    Weekend game keeps a 30-cell track under a HUD counting to 15."""
    import sys
    sys.path.insert(0, SCRIPTS)
    import board_geometry as g
    import path_layouts as pl

    assets = read_text(os.path.join(LUA_DIR, "assets.lua"))
    table = re.search(r"BOARD_ART_URLS\s*=\s*\{(.*?)\n\}", assets, re.S)
    assert table, "BOARD_ART_URLS table not found in lua/assets.lua"
    for v in pl.VARIANTS:
        row = re.search(rf"^\s*{v}\s*=\s*\{{(.*?)\}}", table.group(1), re.M)
        assert row, f"BOARD_ART_URLS has no row for {v}"
        for lim in g.DOOM_LIMITS:
            assert re.search(rf"\[\s*{lim}\s*\]\s*=", row.group(1)), (
                f"BOARD_ART_URLS[{v}] has no entry for Doom limit {lim}")


def test_lua_dawn_display_mirrors_board_geometry():
    """The Dawn card's reveal/discard spots are printed on the board AND
    hard-coded in day_loop.lua. Drift means the day's event lands somewhere
    the board doesn't explain — it used to land on the Day Counter's frame
    and across the title, reading as a card someone had dropped there."""
    import sys
    sys.path.insert(0, SCRIPTS)
    import board_geometry as g

    src = read_text(os.path.join(LUA_DIR, "day_loop.lua"))
    for name, (ex, ez) in (("DAWN_REVEAL_POS", g.DAWN_REVEAL_WORLD),
                           ("DAWN_DISCARD_POS", g.DAWN_DISCARD_WORLD)):
        m = re.search(rf"{name}\s*=\s*\{{x\s*=\s*(-?[\d.]+),\s*y\s*=\s*(-?[\d.]+),"
                      rf"\s*z\s*=\s*(-?[\d.]+)\s*\}}", src)
        assert m, f"{name} not found in lua/day_loop.lua"
        assert abs(float(m.group(1)) - ex) < 0.01 and abs(float(m.group(3)) - ez) < 0.01, (
            f"lua {name}=({m.group(1)}, {m.group(3)}) but board_geometry prints "
            f"its frame at ({ex}, {ez})")


def test_dawn_display_does_not_collide_with_the_rest_of_the_board():
    """The reason the Dawn cards moved at all: a card is 2.3x3.2 and the old
    spot overlapped the Day Counter and the printed title. Check the new box
    against every other printed feature rather than trusting the eye."""
    import sys
    sys.path.insert(0, SCRIPTS)
    import board_geometry as g
    import path_layouts as pl

    x0, z0, x1, z1 = g.DAWN_BOX
    assert (abs(x0) < g.BOARD_WORLD_HALF and abs(x1) < g.BOARD_WORLD_HALF
            and abs(z0) < g.BOARD_WORLD_HALF and abs(z1) < g.BOARD_WORLD_HALF), \
        "the Dawn box runs off the printed board"

    # Both card slots must sit inside their box.
    for cx, cz in (g.DAWN_REVEAL_WORLD, g.DAWN_DISCARD_WORLD):
        assert x0 <= cx - g.DAWN_SLOT_W / 2 and cx + g.DAWN_SLOT_W / 2 <= x1, \
            f"Dawn slot at x={cx} pokes out of its printed box"
        assert z0 <= cz - g.DAWN_SLOT_L / 2 and cz + g.DAWN_SLOT_L / 2 <= z1, \
            f"Dawn slot at z={cz} pokes out of its printed box"

    # The two slots must not overlap each other...
    (ax, az), (bx, bz) = g.DAWN_REVEAL_WORLD, g.DAWN_DISCARD_WORLD
    assert (abs(ax - bx) >= g.DAWN_SLOT_W or abs(az - bz) >= g.DAWN_SLOT_L), \
        "the Dawn reveal and discard frames overlap"
    # ...and must stay more than the 2-unit match radius apart, or
    # _findCardAtDawnRevealSpot picks a discarded card as today's Dawn.
    assert ((ax - bx) ** 2 + (az - bz) ** 2) > 4.0, \
        "discard pile is inside the reveal spot's 2-unit search radius"

    # Clear of the Day Counter's printed frame.
    dcx, dcz = g.DAY_COUNTER_WORLD
    assert not (x0 < dcx + 1.8 and dcx - 1.8 < x1
                and z0 < dcz + 1.3 and dcz - 1.3 < z1), \
        "the Dawn box overlaps the DAY COUNTER frame — the original bug"

    # Clear of every location ring.
    for name, (lx, lz) in pl.LOCATION_WORLD.items():
        r = pl.LOCATION_RING_R
        nearest_x = min(max(lx, x0), x1)
        nearest_z = min(max(lz, z0), z1)
        assert (nearest_x - lx) ** 2 + (nearest_z - lz) ** 2 >= r * r, \
            f"the Dawn box overlaps {name}'s printed ring"

    # Clear of the Doom track along the south edge.
    assert z0 > g.DOOM_TRACK_WORLD_Z + 0.5, "the Dawn box reaches the Doom track"


def test_ingame_rulebook_mirrors_the_player_rulebook():
    """Help > Rulebook (rulebookText, lua/ui_help_pages.lua) and
    PlayerRules.md/.html (scripts/generate_player_rules.py) are the same book
    shown two ways. They are assembled by different code from the same
    content/ markdown, so nothing but this test stops one gaining a section the
    other never hears about — and the in-game one is the copy a player at the
    table actually reads."""
    gen = read_text(os.path.join(SCRIPTS, "generate_player_rules.py"))
    lua = read_text(os.path.join(LUA_DIR, "ui_help_pages.lua"))

    # ("Quick Start", "content/notebook/quickstart.md"), ...
    sections = re.findall(r'\(\s*"([^"]+)"\s*,\s*"(content/[^"]+)"\s*\)', gen)
    assert len(sections) >= 4, (
        f"could not parse SECTIONS out of generate_player_rules.py (got {sections})")

    body = re.search(r"function rulebookText\(\)(.*?)\nend", lua, re.S)
    assert body, "rulebookText() not found in lua/ui_help_pages.lua"
    book = body.group(1)

    missing = [title for title, _src in sections
               if title.upper() not in book.upper()]
    assert not missing, (
        f"PlayerRules has section(s) {missing} that the in-game Rulebook tab "
        "does not: add them to rulebookText() (or drop them from SECTIONS). "
        "A rule a player can only read outside the game is a rule they won't.")


def test_trophy_names_mirror_the_trophies_csv():
    """TROPHY_BY_BOSS (lua/combat.lua) feeds the option-utilization report,
    which scores against content/cards_trophies.csv. A drifted name doesn't
    error — it just makes every Trophy read as never earned, which is the one
    conclusion the report must never produce by accident."""
    src = read_text(os.path.join(LUA_DIR, "combat.lua"))
    body = re.search(r"TROPHY_BY_BOSS\s*=\s*\{(.*?)\n\}", src, re.S)
    assert body, "TROPHY_BY_BOSS not found in lua/combat.lua"
    lua_names = set(re.findall(r'=\s*"([^"]+)"', body.group(1)))

    csv_names = {r["boss"] for r in read_csv_rows("cards_trophies.csv") if r.get("boss")}
    missing = sorted(lua_names - csv_names)
    assert not missing, (
        f"TROPHY_BY_BOSS names {missing} are not in cards_trophies.csv — the "
        "utilization report would score them as never earned")


def test_location_defense_mirrors_the_locations_csv():
    """LOCATION_DEFENSE (lua/global.lua) is the live rule — applyCounterAttack
    rolls the Net's blocking dice off it, and adds the Basketball Court's
    exposure as extra swings for the threat. content/locations.csv's `defense`
    column is where the design writes it down (§7.1-7.5). Drift here changes
    combat maths silently, in the direction nobody would notice: a lost block
    just looks like bad luck."""
    src = read_text(os.path.join(LUA_DIR, "global.lua"))
    body = re.search(r"LOCATION_DEFENSE\s*=\s*\{(.*?)\n\}", src, re.S)
    assert body, "LOCATION_DEFENSE not found in lua/global.lua"
    lua_def = {k: int(v) for k, v in
               re.findall(r"(\w+)\s*=\s*(-?\d+)", body.group(1))}

    csv_key = {
        "L_JAMES": "JamesHouse", "L_RAYMAN": "RaymanHouse",
        "L_ELLIE_LUCA": "EllieLucaHouse", "L_BASKETBALL": "BasketballCourt",
        "L_BADMINTON": "BadmintonCourt",
    }
    csv_def = {csv_key[r["id"]]: int(r["defense"])
               for r in read_csv_rows("locations.csv") if r["id"] in csv_key}
    assert lua_def == csv_def, (
        f"defence drift: lua={lua_def} csv={csv_def} — LOCATION_DEFENSE "
        "(global.lua) and the `defense` column of content/locations.csv "
        "must agree.")
