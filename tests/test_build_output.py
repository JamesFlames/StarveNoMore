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


def _every_object(save):
    """Every object in the save, including the ones inside bags — the six
    resource tokens and the five Telltale Hearts only exist as templates in
    their supply bags until a script pulls one out."""
    stack = list(save["ObjectStates"])
    while stack:
        o = stack.pop()
        yield o
        stack.extend(o.get("ContainedObjects") or [])


def test_tokens_carry_the_half_turn_on_the_object(built_save):
    """Flat art renders half a turn round in the table view, and there are two
    ways to cancel it: pre-rotate the PNG, or turn the OBJECT. Only the second
    survives Alt-zoom, which TTS draws in the object's LOCAL frame — art
    pre-rotated to suit the felt magnifies upside down. A token is 0.4 scale,
    so hovering is the only way anyone ever reads its label ("hovering over the
    token Cloth shows it reversed"), which makes the object the only correct
    place to put the turn. Same trade as PLAYER_BOARD_ZOOM_ROT.

    Three things have to agree: the built objects, build_save.TOKEN_ZOOM_ROT,
    and the TOKEN_FACE_UP that scripted respawns hand to takeObject.
    """
    build_src = open(os.path.join(SCRIPTS, "build_save.py"), encoding="utf-8").read()
    rot = float(re.search(r"^TOKEN_ZOOM_ROT\s*=\s*([\d.]+)", build_src, re.M).group(1))

    helpers = open(os.path.join(ROOT, "lua", "helpers.lua"), encoding="utf-8").read()
    m = re.search(r"^TOKEN_FACE_UP\s*=\s*\{\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\}",
                  helpers, re.M)
    assert m, "TOKEN_FACE_UP not found in lua/helpers.lua"
    face_x, face_y, face_z = (float(g) for g in m.groups())
    assert face_y % 360 == rot % 360, (
        f"TOKEN_FACE_UP yaw is {face_y} but build_save.TOKEN_ZOOM_ROT is {rot} — "
        "every token a script respawns would read 180 out from the ones the "
        "build placed")
    assert (face_x, face_z) == (0.0, 0.0), (
        f"TOKEN_FACE_UP has rotX/rotZ ({face_x}, {face_z}) — a token with no "
        "back image shows its art MIRRORED when it lands on rotZ=180")

    save = json.loads(built_save["fresh"])
    offenders = [
        (o.get("Nickname") or o["Name"], o["Transform"]["rotY"])
        for o in _every_object(save)
        if o["Name"] == "Custom_Token" and o["Transform"]["rotY"] % 360 != rot % 360
    ]
    assert not offenders, (
        f"Custom_Tokens not spawned at TOKEN_ZOOM_ROT ({rot}): {offenders}. Their "
        "art is authored upright (generate_assets.py), so at any other yaw the "
        "label prints turned round on the table")

    # The Doom marker is the one token a script re-pins after every move, so it
    # is the one that can silently drift back to a bare {0,0,0}.
    setup = open(os.path.join(ROOT, "lua", "setup.lua"), encoding="utf-8").read()
    body = setup[setup.index("function moveDoomMarker"):]
    body = body[:body.index("\nend")]
    assert "setRotation(TOKEN_FACE_UP)" in body, (
        "moveDoomMarker must re-pin the marker at TOKEN_FACE_UP — pinning it "
        "flat at {0,0,0} prints DOOM upside down on the track")


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


def test_lua_mirrors_the_tables_surface_height():
    """TABLE_SURFACE_Y (global.lua) must equal build_save.py's.

    Same rule as the doom marker above: the BUILD authors resting heights for
    locked pieces, and the SCRIPT authors drop heights for unlocked ones. If
    the two disagree about where the table is, script spawns land inside it —
    which is what happened to a whole starting hand and six resource tokens.
    Read from source, not by import: build_save.py parses argv at import time.
    """
    build_src = open(os.path.join(SCRIPTS, "build_save.py"), encoding="utf-8").read()
    build_y = float(re.search(r"^TABLE_SURFACE_Y\s*=\s*([\d.]+)", build_src, re.M).group(1))
    lua_src = open(os.path.join(ROOT, "lua", "global.lua"), encoding="utf-8").read()
    lua_y = float(re.search(r"^TABLE_SURFACE_Y\s*=\s*([\d.]+)", lua_src, re.M).group(1))
    assert lua_y == build_y, (
        f"global.lua says the table surface is y={lua_y}, build_save.py says "
        f"{build_y} — script spawns and built pieces must agree on where the "
        "table is")
