"""--publish builds must be shippable: no machine-local URLs anywhere.

The dev save deliberately uses file:///<repo>/art/... and
http://localhost:8080/... (scripts/serve_art.bat); a save shared beyond this
machine needs every asset on a hosted base URL. build_save.py --publish
rewrites them all and refuses to write a save that still has local URLs —
this test proves that end-to-end, and that a publish build never touches the
committed dev saves.
"""
import hashlib
import json
import os
import subprocess
import sys

from conftest import ROOT, SAVES, SCRIPTS

BASE = "https://cdn.example.com/starvenomore"


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_publish_build_has_no_local_urls(tmp_path):
    dev_save = os.path.join(SAVES, "StarveNoMore.json")
    dev_hash_before = _sha(dev_save) if os.path.isfile(dev_save) else None

    out = tmp_path / "publish.json"
    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "build_save.py"),
         "--publish", BASE, "--out", str(out)],
        capture_output=True, text=True, timeout=300, cwd=ROOT,
    )
    assert proc.returncode == 0, f"publish build failed:\n{proc.stdout}\n{proc.stderr}"

    raw = out.read_text(encoding="utf-8")
    assert "file:///" not in raw, "publish save still contains file:/// URLs"
    assert "localhost" not in raw, "publish save still contains localhost URLs"
    assert BASE in raw, "publish save does not reference the hosted base URL"

    save = json.loads(raw)
    assert save.get("ObjectStates"), "publish save has no objects"
    assert len(save.get("LuaScript", "")) > 10000

    if dev_hash_before is not None:
        assert _sha(dev_save) == dev_hash_before, (
            "a --publish build modified the committed dev save")
