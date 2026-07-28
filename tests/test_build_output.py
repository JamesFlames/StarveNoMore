"""Build the TTS save and validate the output.

build_save.py is deterministic (no timestamps/randomness), so rebuilding and
comparing against the committed save also serves as a staleness check. The
committed bytes are always restored afterwards, whichever way the test goes.
"""
import json
import os
import re
import subprocess
import sys

import pytest
from conftest import ROOT, SAVES, SCRIPTS, parse_lua_load_order

SAVE_FILES = ["StarveNoMore.json", "StarveNoMore.pretty.json"]


@pytest.fixture(scope="module")
def built_save():
    originals = {}
    for fn in SAVE_FILES:
        path = os.path.join(SAVES, fn)
        if os.path.isfile(path):
            with open(path, "rb") as f:
                originals[fn] = f.read()

    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "build_save.py")],
        capture_output=True, text=True, timeout=300, cwd=ROOT,
    )
    try:
        assert proc.returncode == 0, f"build_save.py failed:\n{proc.stdout}\n{proc.stderr}"
        with open(os.path.join(SAVES, "StarveNoMore.json"), "r", encoding="utf-8") as f:
            fresh = f.read()
    finally:
        for fn, data in originals.items():
            with open(os.path.join(SAVES, fn), "wb") as f:
                f.write(data)

    return {
        "stdout": proc.stdout,
        "fresh": fresh,
        "committed": originals.get("StarveNoMore.json", b"").decode("utf-8", errors="replace"),
    }


def test_save_is_valid_json(built_save):
    save = json.loads(built_save["fresh"])
    assert save.get("SaveName"), "SaveName missing"
    assert save.get("ObjectStates"), "no objects in save"
    assert len(save["LuaScript"]) > 10000, "LuaScript suspiciously small"
    assert len(save["XmlUI"]) > 1000, "XmlUI suspiciously small"


def test_every_lua_file_made_it_into_the_bundle(built_save):
    save = json.loads(built_save["fresh"])
    script = save["LuaScript"]
    missing = [f for f in parse_lua_load_order()
               if f"-- ========== {f} ==========" not in script]
    assert not missing, f"LUA_LOAD_ORDER files absent from the built LuaScript: {missing}"


def test_no_objects_embedded_in_tabletop(built_save):
    """The glass table's playing surface is at y ~1.55 (TABLE_SURFACE_Y,
    build_save.py). Anything authored inside the 0..surface band starts
    embedded in the tabletop: locked objects sit invisible in the glass,
    unlocked ones fall through the table's partial-hull collider ("the
    player boards were invisible until I picked them up"). Under-table
    library items (y < 0) are deliberate. See docs/tts-runtime.md."""
    save = json.loads(built_save["fresh"])
    build_src = open(os.path.join(SCRIPTS, "build_save.py"), encoding="utf-8").read()
    surface = float(re.search(r"TABLE_SURFACE_Y\s*=\s*([\d.]+)", build_src).group(1))
    # The board IS the surface and hand zones are volumes. The board is a thin
    # tile resting ON the table, so its CENTRE legitimately sits inside the
    # band while its top face is above it — exempt it by tag, not by Name.
    exempt = {"Custom_Board", "HandTrigger"}
    embedded = [
        (o.get("Nickname") or o["Name"], round(o["Transform"]["posY"], 2))
        for o in save["ObjectStates"]
        if 0 < o["Transform"]["posY"] < surface
        and o["Name"] not in exempt
        and "MainBoard" not in (o.get("Tags") or [])
    ]
    assert not embedded, (
        f"objects authored inside the tabletop band (0 < y < {surface}) — they will "
        f"be invisible on the table: {embedded}. Spawn at SURFACE_Y or above."
    )


def test_doom_marker_height_mirrors_lua(built_save):
    """moveDoomMarker (setup.lua) re-pins the marker at DOOM_MARKER_Y after
    every slide; build_save.py spawns it at its own y. If they drift the
    marker visibly hops on the first Doom change."""
    save = json.loads(built_save["fresh"])
    marker = next(o for o in save["ObjectStates"] if "DoomMarker" in o.get("Tags", []))
    lua_src = open(os.path.join(ROOT, "lua", "setup.lua"), encoding="utf-8").read()
    lua_y = float(re.search(r"DOOM_MARKER_Y\s*=\s*([\d.]+)", lua_src).group(1))
    assert abs(marker["Transform"]["posY"] - lua_y) < 1e-9, (
        f"doom marker spawn y {marker['Transform']['posY']} != DOOM_MARKER_Y {lua_y} "
        "(setup.lua) — keep the mirror in sync"
    )


def test_build_emits_no_warnings(built_save):
    warnings = [line for line in built_save["stdout"].splitlines() if line.startswith("WARNING")]
    assert not warnings, "build_save.py warnings:\n" + "\n".join(warnings)


def test_committed_save_is_fresh(built_save):
    assert built_save["committed"], "saves/StarveNoMore.json missing — run scripts/build_save.py"

    def normalize(s):
        # newline convention and the machine-specific file:/// art prefix
        s = s.replace("\r\n", "\n").replace("\\r\\n", "\\n")
        return re.sub(r"file:///[^\"\\]*?/art/", "file:///ART/", s)

    fresh = normalize(built_save["fresh"])
    committed = normalize(built_save["committed"])
    if fresh == committed:
        return

    # Deliberately NOT `assert fresh == committed`. The save is ~1.2 MB, and
    # pytest's assertion rewriting builds a character-level diff of the two
    # strings on failure — which takes minutes and reads as a hung suite rather
    # than a stale file. pytest.fail() skips the rewriter entirely, so the
    # real failure mode reports in milliseconds. Locate the first divergence
    # ourselves and quote a short window around it.
    i = next((n for n, (a, b) in enumerate(zip(fresh, committed)) if a != b),
             min(len(fresh), len(committed)))
    window = 90
    lo, hi = max(0, i - window // 2), i + window
    pytest.fail(
        "saves/StarveNoMore.json is stale: rebuilding from the current "
        "lua/xml/content produces different output. "
        "Rerun: python scripts/build_save.py\n"
        f"  first difference at byte {i} of {len(committed)} "
        f"(rebuilt is {len(fresh)} bytes)\n"
        f"  committed: …{committed[lo:hi]!r}…\n"
        f"  rebuilt:   …{fresh[lo:hi]!r}…",
        pytrace=False,
    )
