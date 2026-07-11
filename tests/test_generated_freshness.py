"""The three auto-generated Lua files must match what their generators produce
from the current sources. Catches: edited the source (CSV/markdown/sounds) and
forgot the generator, or hand-edited a generated file.

Each test runs the generator, compares, and always restores the committed bytes,
so a failing test never leaves the working tree modified.
"""
import os
import subprocess
import sys

import pytest

from conftest import LUA_DIR, ROOT, SCRIPTS

GENERATORS = {
    "audio_manifest.lua": "generate_audio_manifest.py",
    "whatnow_hints.lua": "generate_whatnow_hints.py",
    "market_data.lua": "generate_market_data.py",
    "threat_types.lua": "generate_threat_types.py",
    "recipe_data.lua": "generate_recipe_data.py",
    "notebook_data.lua": "generate_notebook.py",
}


def test_symbol_index_is_fresh():
    """SYMBOLS.md and .luacheckrc must match what generate_symbol_index.py
    produces from the current lua/ tree (E in frameworkimprovements.md)."""
    targets = [os.path.join(ROOT, "SYMBOLS.md"), os.path.join(ROOT, ".luacheckrc")]
    committed = {}
    for t in targets:
        assert os.path.isfile(t), f"{os.path.basename(t)} missing — run scripts/generate_symbol_index.py"
        with open(t, "rb") as f:
            committed[t] = f.read()
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "generate_symbol_index.py")],
            capture_output=True, text=True, timeout=120, cwd=ROOT,
        )
        assert proc.returncode == 0, f"generator failed:\n{proc.stdout}\n{proc.stderr}"
        regenerated = {}
        for t in targets:
            with open(t, "rb") as f:
                regenerated[t] = f.read()
    finally:
        for t, data in committed.items():
            with open(t, "wb") as f:
                f.write(data)
    for t in targets:
        a = committed[t].replace(b"\r\n", b"\n")
        b = regenerated[t].replace(b"\r\n", b"\n")
        assert a == b, (
            f"{os.path.basename(t)} is stale — rerun scripts/generate_symbol_index.py")


@pytest.mark.parametrize("lua_file", sorted(GENERATORS))
def test_generated_file_is_fresh(lua_file):
    generator = GENERATORS[lua_file]
    target = os.path.join(LUA_DIR, lua_file)
    assert os.path.isfile(target), f"{lua_file} missing — run scripts/{generator}"
    with open(target, "rb") as f:
        committed = f.read()

    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, generator)],
            capture_output=True, text=True, timeout=120, cwd=ROOT,
        )
        assert proc.returncode == 0, f"{generator} failed:\n{proc.stdout}\n{proc.stderr}"
        with open(target, "rb") as f:
            regenerated = f.read()
    finally:
        with open(target, "wb") as f:
            f.write(committed)

    # normalize newlines so the check is stable across Windows/Linux checkouts
    committed = committed.replace(b"\r\n", b"\n")
    regenerated = regenerated.replace(b"\r\n", b"\n")
    assert regenerated == committed, (
        f"lua/{lua_file} is stale: scripts/{generator} produces different output "
        f"from the current sources. Rerun the generator and rebuild the save."
    )
