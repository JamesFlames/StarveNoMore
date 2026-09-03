"""--publish builds must be shippable: no machine-local URLs, no unsafe ones.

The dev save deliberately uses file:///<repo>/art/... and
http://localhost:8080/... (scripts/serve_art.bat); a save shared beyond this
machine needs every asset on a hosted base URL. build_save.py --publish
rewrites them all and refuses to write a save that still has local URLs —
this test proves that end-to-end, and that a publish build never touches the
committed dev saves.

It also guards the *shape* of every rewritten URL. The dev server is
python -m http.server, which happily serves a path with a raw space in it;
a real CDN may answer 400 or 404 for the same request. One sound file
(`battlegrounds fall night_ds_amb.ogg`) shipped that way and would have
failed only on a published build, on somebody else's machine, for one clip
out of 84 — so the rule is enforced here instead of discovered there.
Keep asset filenames URL-safe; do not paper over this by percent-encoding
in build_save.py, because audio_manifest.lua stores the same string as the
display `name`.
"""
import hashlib
import json
import os
import re
import string
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


# Unreserved per RFC 3986, plus the separators a path legitimately uses.
URL_SAFE = set(string.ascii_letters + string.digits + "-._~" + "/:")


def test_publish_urls_need_no_escaping(tmp_path):
    """Every asset URL must survive a real host verbatim."""
    out = tmp_path / "publish.json"
    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "build_save.py"),
         "--publish", BASE, "--out", str(out)],
        capture_output=True, text=True, timeout=300, cwd=ROOT,
    )
    assert proc.returncode == 0, f"publish build failed:\n{proc.stdout}\n{proc.stderr}"

    urls = set(re.findall(re.escape(BASE) + r'[^"\\]*', out.read_text(encoding="utf-8")))
    assert len(urls) > 100, f"expected the full asset set, found {len(urls)} URLs"

    bad = sorted(u for u in urls if not set(u) <= URL_SAFE)
    assert not bad, (
        "asset URLs contain characters a host may reject or mangle "
        "(a space is the usual culprit) — rename the file to "
        "[A-Za-z0-9-._~] and re-run its generator:\n  "
        + "\n  ".join(bad)
    )
