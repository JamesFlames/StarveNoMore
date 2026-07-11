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
    assert fresh == committed, (
        "saves/StarveNoMore.json is stale: rebuilding from the current lua/xml/content "
        "produces different output. Rerun: python scripts/build_save.py"
    )
