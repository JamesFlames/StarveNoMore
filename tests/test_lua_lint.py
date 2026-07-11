"""Static analysis of the Lua sources with luacheck.

The generated .luacheckrc (scripts/generate_symbol_index.py) declares every
bundle global and disables the noisy warning classes, so anything luacheck
reports is a real hazard — typically a typo'd global.

Skips when luacheck isn't installed (CI's dedicated luacheck job always runs
it; locally: `luarocks install luacheck`, or the standalone luacheck release).
"""
import os
import shutil
import subprocess

import pytest

from conftest import ROOT

LUACHECK = shutil.which("luacheck")


@pytest.mark.skipif(LUACHECK is None, reason=(
    "luacheck not installed — CI's luacheck job covers this; install locally "
    "with `luarocks install luacheck` to run it here"))
def test_luacheck_clean():
    proc = subprocess.run(
        [LUACHECK, "lua", "--no-color"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, (
        "luacheck reported problems (regenerate .luacheckrc with "
        "scripts/generate_symbol_index.py if you added globals):\n"
        + proc.stdout + proc.stderr)


def test_luacheckrc_exists_and_is_generated():
    """The config luacheck depends on must exist and be the generated one."""
    path = os.path.join(ROOT, ".luacheckrc")
    assert os.path.isfile(path), ".luacheckrc missing — run scripts/generate_symbol_index.py"
    with open(path, "r", encoding="utf-8") as f:
        head = f.read(200)
    assert "AUTO-GENERATED" in head, (
        ".luacheckrc is no longer the generated file — regenerate with "
        "scripts/generate_symbol_index.py or update this test")
