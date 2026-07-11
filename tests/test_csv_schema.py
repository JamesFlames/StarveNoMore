"""Schema checks for every content/*.csv: required columns, unique ids,
id naming conventions, numeric fields in range."""
import re

import pytest

from conftest import read_csv_rows

# filename -> (required columns, id prefix regex)
SCHEMAS = {
    "cards_phase1.csv": (["id", "title", "severity", "immediate", "ongoing"], r"P1_[A-Z0-9_]+"),
    "cards_phase2.csv": (["id", "title", "severity", "immediate", "ongoing"], r"P2_[A-Z0-9_]+"),
    "cards_phase3.csv": (["id", "title", "severity", "immediate", "ongoing"], r"P3_[A-Z0-9_]+"),
    "cards_phase4.csv": (["id", "title", "severity", "immediate", "ongoing"], r"P4_[A-Z0-9_]+"),
    "cards_market.csv": (["id", "name", "category", "cost", "effect", "persistent", "tooltip"], r"M_[A-Z0-9_]+"),
    "cards_recipes.csv": (["id", "name", "ingredients", "cost", "effect"], r"R_[A-Z0-9_]+"),
    "cards_threats.csv": (["id", "name", "type", "hp", "attack", "severity", "special"], r"T_[A-Z0-9_]+"),
    "cards_visitors.csv": (["id", "character", "trigger", "immediate", "departure"], r"V_[A-Z0-9_]+"),
    "cards_trophies.csv": (["id", "boss", "bonus"], r"TR_[A-Z0-9_]+"),
    "cards_scenarios.csv": (["id", "name", "season", "effect", "ongoing"], r"SC_[A-Z0-9_]+"),
    "locations.csv": (["id", "name", "yields", "special", "sanity_modifier", "defense", "threat_rate", "house_owner"], r"L_[A-Z0-9_]+"),
    "resources.csv": (["id", "name", "color", "icon", "tag", "sources", "uses"], r"R_[A-Z0-9_]+"),
    "cards_starting.csv": (["id", "character", "name", "count", "effect"], r"S_[A-Z0-9_]+"),
}

CSV_FILES = sorted(SCHEMAS)


@pytest.mark.parametrize("filename", CSV_FILES)
def test_required_columns(filename):
    rows = read_csv_rows(filename)
    assert rows, f"{filename} has no data rows"
    required, _ = SCHEMAS[filename]
    missing = [c for c in required if c not in rows[0]]
    assert not missing, f"{filename} missing columns: {missing}"


@pytest.mark.parametrize("filename", CSV_FILES)
def test_ids_unique_and_well_formed(filename):
    rows = read_csv_rows(filename)
    _, id_pattern = SCHEMAS[filename]
    seen = set()
    problems = []
    for i, row in enumerate(rows, start=2):  # +header line
        cid = (row.get("id") or "").strip()
        if not cid:
            problems.append(f"line {i}: empty id")
            continue
        if cid in seen:
            problems.append(f"line {i}: duplicate id {cid}")
        seen.add(cid)
        if not re.fullmatch(id_pattern, cid):
            problems.append(f"line {i}: id {cid!r} does not match {id_pattern}")
    assert not problems, f"{filename}:\n" + "\n".join(problems)


def test_recipe_and_resource_ids_do_not_collide():
    # Both files use the R_ prefix; a collision would make R_* references ambiguous.
    recipes = {r["id"] for r in read_csv_rows("cards_recipes.csv")}
    resources = {r["id"] for r in read_csv_rows("resources.csv")}
    assert not (recipes & resources), f"id collision: {recipes & resources}"


@pytest.mark.parametrize(
    "filename", ["cards_phase1.csv", "cards_phase2.csv", "cards_phase3.csv", "cards_phase4.csv"]
)
def test_dawn_card_severity_in_range(filename):
    bad = [
        (r["id"], r["severity"])
        for r in read_csv_rows(filename)
        if not (r["severity"].strip().isdigit() and 1 <= int(r["severity"]) <= 5)
    ]
    assert not bad, f"{filename} severity must be 1-5: {bad}"


def test_threat_stats_numeric_and_sane():
    # hp 0 is legitimate: Soft threats are events, not combatants.
    problems = []
    for r in read_csv_rows("cards_threats.csv"):
        for col, lo, hi in (("hp", 0, 30), ("attack", 0, 10), ("severity", 1, 5)):
            v = r[col].strip()
            if not v.lstrip("-").isdigit() or not (lo <= int(v) <= hi):
                problems.append(f"{r['id']}: {col}={v!r} (expected {lo}..{hi})")
    assert not problems, "\n".join(problems)


def test_threat_types_enumerated():
    allowed = {"Soft", "Hard", "Persistent", "Boss"}
    bad = [(r["id"], r["type"]) for r in read_csv_rows("cards_threats.csv") if r["type"] not in allowed]
    assert not bad, f"unexpected threat types (allowed {sorted(allowed)}): {bad}"


def test_resource_tags_well_formed():
    # resources.csv tag column drives the Resource:* object tags used by
    # getPlayerResources / canAfford; a malformed tag breaks affordability.
    problems = []
    for r in read_csv_rows("resources.csv"):
        tag = (r["tag"] or "").strip()
        if not re.fullmatch(r"Resource:[A-Za-z]+", tag):
            problems.append(f"{r['id']}: tag {tag!r} is not of the form Resource:<Name>")
    assert not problems, "\n".join(problems)


def test_starting_items_characters_and_counts():
    """Every starting item belongs to a real character with a sane copy
    count, and every character actually has a starting hand."""
    valid_chars = {"James", "Coco", "Rayman", "Ellie", "Luca"}
    per_char = {}
    problems = []
    for r in read_csv_rows("cards_starting.csv"):
        char = (r["character"] or "").strip()
        if char not in valid_chars:
            problems.append(f"{r['id']}: unknown character {char!r}")
            continue
        count = (r["count"] or "").strip()
        if not count.isdigit() or not (1 <= int(count) <= 3):
            problems.append(f"{r['id']}: count {count!r} (expected 1..3)")
            continue
        per_char[char] = per_char.get(char, 0) + int(count)
    for char in sorted(valid_chars):
        if per_char.get(char, 0) < 3:
            problems.append(f"{char}: only {per_char.get(char, 0)} starting cards (expected 3+)")
    assert not problems, "\n".join(problems)


def test_tooltips_csv_shape():
    rows = read_csv_rows("tooltips.csv")
    assert rows and "tag" in rows[0] and "tooltip" in rows[0]
    empty = [r["tag"] for r in rows if not (r["tooltip"] or "").strip()]
    assert not empty, f"tooltips.csv rows with empty tooltip: {empty}"
    tags = [r["tag"] for r in rows]
    dupes = {t for t in tags if tags.count(t) > 1}
    assert not dupes, f"duplicate tooltip tags: {dupes}"
