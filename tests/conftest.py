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
import json as _json
import os
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


def _load_manifest():
    """The build manifest scripts/load_order.json (the source of truth for the
    Lua + XML concatenation order, read by build_save.py at build time)."""
    with open(os.path.join(SCRIPTS, "load_order.json"), "r", encoding="utf-8") as f:
        return _json.load(f)


def parse_lua_load_order():
    """The Lua concatenation order from scripts/load_order.json."""
    files = _load_manifest()["lua"]
    assert files, "load_order.json 'lua' list is empty"
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


def parse_xml_load_order():
    """The XML concatenation order from scripts/load_order.json."""
    files = _load_manifest()["xml"]
    assert files, "load_order.json 'xml' list is empty"
    return files


def all_xml_files():
    """Every xml/ file, ordered as build_save.py concatenates them."""
    order = parse_xml_load_order()
    extras = sorted(fn for fn in os.listdir(XML_DIR)
                    if fn.endswith(".xml") and fn not in order)
    for fn in order:
        assert os.path.isfile(os.path.join(XML_DIR, fn)), (
            f"file in XML_LOAD_ORDER missing on disk: {fn}")
    return order + extras


@pytest.fixture(scope="session")
def xml_source():
    """The concatenated global UI XML exactly as build_save.py assembles it."""
    return "\n".join(read_text(os.path.join(XML_DIR, fn)) for fn in all_xml_files())


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
    "S": "cards_starting.csv",
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


# --------------------------------------------------------------------------
# Headless Lua runtime harness (shared by tests/test_lua_*.py)
#
# Moved here from the former monolithic test_lua_runtime.py so each topic
# module (test_lua_combat, test_lua_dawn, ...) shares one bundle harness.
# --------------------------------------------------------------------------

try:
    import lupa.lua52 as lua52
except ImportError:  # pragma: no cover
    lua52 = None


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
    """Make gameRoll — the gameplay RNG seam (helpers.lua) — return this exact
    sequence (asserts if exhausted). math.random itself is left alone, so the
    stub's internals and cosmetic randomness never eat scripted rolls."""
    rt.execute(
        "local seq = {%s}; local i = 0\n"
        "gameRoll = function(...) i = i + 1\n"
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
