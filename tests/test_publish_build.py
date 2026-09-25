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

The published assets are served from this repo at a release tag
(scripts/publish.py), so every one of them must also be a *committed* file —
art that exists only on the build machine would 404 for everybody else.
"""
import hashlib
import json
import os
import re
import string
import subprocess
import sys

import pytest
from conftest import LUA_DIR, ROOT, SAVES, SCRIPTS

sys.path.insert(0, SCRIPTS)
import publish  # noqa: E402  (needs the sys.path line above)

BASE = "https://cdn.example.com/starvenomore"


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


@pytest.fixture(scope="module")
def publish_build(tmp_path_factory):
    """One --publish build for the module: (raw save text, dev save hash before)."""
    dev_save = os.path.join(SAVES, "StarveNoMore.json")
    dev_hash_before = _sha(dev_save) if os.path.isfile(dev_save) else None

    out = tmp_path_factory.mktemp("publish") / "publish.json"
    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "build_save.py"),
         "--publish", BASE, "--out", str(out)],
        capture_output=True, text=True, timeout=300, cwd=ROOT,
    )
    assert proc.returncode == 0, f"publish build failed:\n{proc.stdout}\n{proc.stderr}"
    return out.read_text(encoding="utf-8"), dev_hash_before


def test_publish_build_has_no_local_urls(publish_build):
    raw, dev_hash_before = publish_build
    dev_save = os.path.join(SAVES, "StarveNoMore.json")
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


def test_publish_urls_need_no_escaping(publish_build):
    """Every asset URL must survive a real host verbatim."""
    raw, _ = publish_build
    urls = set(re.findall(re.escape(BASE) + r'[^"\\]*', raw))
    assert len(urls) > 100, f"expected the full asset set, found {len(urls)} URLs"

    bad = sorted(u for u in urls if not set(u) <= URL_SAFE)
    assert not bad, (
        "asset URLs contain characters a host may reject or mangle "
        "(a space is the usual culprit) — rename the file to "
        "[A-Za-z0-9-._~] and re-run its generator:\n  "
        + "\n  ".join(bad)
    )


def test_every_published_asset_is_committed(publish_build):
    """publish.py serves the assets from the repo at the release tag, so a
    file the save references but git doesn't track would 404 for every
    player. Catch it here rather than after the Workshop upload."""
    raw, _ = publish_build
    with open(os.path.join(LUA_DIR, "assets.lua"), encoding="utf-8") as f:
        paths = publish.asset_paths(json.loads(raw), BASE, f.read())

    # All three sources must be seen, or the check below proves nothing:
    # object art, the audio manifest's literals, and assets.lua's runtime URLs.
    assert "art/board/main_board.png" in paths, "object-field art not found"
    assert any(p.startswith("sounds/") for p in paths), "audio URLs not found"
    assert "art/board/main_board_star_d15.png" in paths, (
        "lua/assets.lua's url(...) entries not found — the _BASE rewrite changed")
    assert "art" not in paths, "_BASE itself was counted as an asset"

    proc = subprocess.run(["git", "ls-files"], cwd=ROOT,
                          capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:  # pragma: no cover
        pytest.skip("git not available")
    untracked = sorted(paths - set(proc.stdout.splitlines()))
    assert not untracked, (
        "the publish save references files git doesn't track — they would 404 "
        "from GitHub. Commit them (or stop referencing them):\n  "
        + "\n  ".join(untracked))


@pytest.mark.parametrize("remote", [
    "https://github.com/JamesFlames/StarveNoMore.git",
    "https://github.com/JamesFlames/StarveNoMore",
    "git@github.com:JamesFlames/StarveNoMore.git",
    "ssh://git@github.com/JamesFlames/StarveNoMore.git",
])
def test_publish_reads_the_github_repo_from_origin(remote):
    assert publish.github_repo(remote) == "JamesFlames/StarveNoMore"
    assert (publish.raw_base("JamesFlames/StarveNoMore", "v1.0")
            == "https://raw.githubusercontent.com/JamesFlames/StarveNoMore/v1.0")
