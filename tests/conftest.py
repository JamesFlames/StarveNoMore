"""Shared fixtures/helpers for the StarveNoMore test suite.

The suite has no dependency on Tabletop Simulator. It tests:
  - content CSV schemas and cross-artifact consistency (test_csv_schema, test_cross_refs)
  - generated-file freshness (test_generated_freshness)
  - the XML <-> Lua UI contract (test_xml_lua_contract)
  - Lua static hazards like duplicate globals (test_lua_statics)
  - the built save JSON (test_build_output)
  - the concatenated Lua bundle running headlessly under Lua 5.2 via lupa
    with a TTS API stub (test_lua_runtime + tts_stub.lua)
  - simulate_balance.py invariants and its hand-mirrored constants (test_sim)

Run:  python -m pytest tests
"""
import csv
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
LUA_DIR = os.path.join(ROOT, "lua")
XML_DIR = os.path.join(ROOT, "xml")
ART_DIR = os.path.join(ROOT, "art")
SCRIPTS = os.path.join(ROOT, "scripts")
SAVES = os.path.join(ROOT, "saves")
TESTS = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, SCRIPTS)  # for importing simulate_balance


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_csv_rows(filename):
    with open(os.path.join(CONTENT, filename), "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_lua_load_order():
    """Parse LUA_LOAD_ORDER out of build_save.py without importing it
    (importing would execute the build)."""
    src = read_text(os.path.join(SCRIPTS, "build_save.py"))
    m = re.search(r"LUA_LOAD_ORDER\s*=\s*\[(.*?)\]", src, re.S)
    assert m, "LUA_LOAD_ORDER not found in build_save.py"
    files = re.findall(r'"([^"]+\.lua)"', m.group(1))
    assert files, "LUA_LOAD_ORDER parsed empty"
    return files


def all_lua_files():
    """Every .lua file under lua/, ordered as build_save.py concatenates them:
    LUA_LOAD_ORDER first, then any extras sorted."""
    order = parse_lua_load_order()
    extras = []
    for dirpath, _dirs, files in os.walk(LUA_DIR):
        for fn in files:
            if fn.endswith(".lua"):
                rel = os.path.relpath(os.path.join(dirpath, fn), LUA_DIR).replace("\\", "/")
                if rel not in order:
                    extras.append(rel)
    return order + sorted(extras)


def lua_bundle():
    """The concatenated global script exactly as build_save.py assembles it."""
    parts = []
    for rel in all_lua_files():
        path = os.path.join(LUA_DIR, rel)
        assert os.path.isfile(path), f"file in LUA_LOAD_ORDER missing on disk: {rel}"
        parts.append(f"-- ========== {rel} ==========")
        parts.append(read_text(path))
    return "\n\n".join(parts)


@pytest.fixture(scope="session")
def load_order():
    return parse_lua_load_order()


@pytest.fixture(scope="session")
def lua_sources():
    """{relpath: source} for every lua file, in bundle order."""
    return {rel: read_text(os.path.join(LUA_DIR, rel)) for rel in all_lua_files()}


@pytest.fixture(scope="session")
def bundle():
    return lua_bundle()


@pytest.fixture(scope="session")
def xml_source():
    return read_text(os.path.join(XML_DIR, "global_ui.xml"))


# --------------------------------------------------------------------------
# Card-id universe, used by cross-reference tests
# --------------------------------------------------------------------------

CSV_FOR_PREFIX = {
    "P1": "cards_phase1.csv",
    "P2": "cards_phase2.csv",
    "P3": "cards_phase3.csv",
    "P4": "cards_phase4.csv",
    "M": "cards_market.csv",
    "T": "cards_threats.csv",
    "TR": "cards_trophies.csv",
    "V": "cards_visitors.csv",
    "SC": "cards_scenarios.csv",
    # "R" is ambiguous: recipes (R_HOT_STEW) and resources (R_WOOD) share it,
    # so R_* membership is checked against the union of both files.
}


@pytest.fixture(scope="session")
def card_ids():
    """{prefix: set(ids)} for every content CSV with an id column."""
    ids = {}
    for prefix, fn in CSV_FOR_PREFIX.items():
        ids[prefix] = {r["id"] for r in read_csv_rows(fn)}
    ids["R"] = {r["id"] for r in read_csv_rows("cards_recipes.csv")} | {
        r["id"] for r in read_csv_rows("resources.csv")
    }
    return ids
