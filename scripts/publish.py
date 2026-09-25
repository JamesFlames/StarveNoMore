#!/usr/bin/env python3
"""Build the Workshop save against GitHub-hosted assets, then prove every link.

The published mod's images and sounds are served straight from this public
repo, pinned to a release tag:

    https://raw.githubusercontent.com/<owner>/<repo>/<tag>/art/board/...

A tag never moves, so every release gets URLs of its own. That matters because
TTS caches each asset by URL, forever: a file replaced behind a URL a player
has already loaded never reaches them. New art means a new tag, never a
re-pointed one — and old tags stay, because saves in progress still use them.

Usage (from a clean, pushed main, after `python scripts/check.py`):
    git tag v1.0 && git push origin v1.0
    python scripts/publish.py v1.0              # build + verify
    python scripts/publish.py v1.0 --install    # ...and copy into TTS's Saves

It refuses to build unless HEAD *is* the release, so the save and the files its
URLs serve come from the same commit. The ref may also be a full commit SHA
already on origin/main — a release candidate, checked without cutting a tag.

Steps:
  1. HEAD is the ref, and no tracked file is modified.
  2. The ref is on GitHub (a pushed tag, or a commit on origin/main).
  3. build_save.py --publish <raw base> → saves/StarveNoMore.publish.json.
  4. Every asset path the save references is a file in the ref's tree —
     catches art that exists on disk but was never committed.
  5. Every URL answers 200 from GitHub.            (2 and 5 skip with --offline)
  6. --install: the save + cover PNG go into the TTS Saves folder.
Then upload from inside TTS — docs/publishing.md, Phase C.
"""
import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

from utf8_console import child_env, use_utf8

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS = os.path.join(REPO_ROOT, "scripts")
PUBLISH_SAVE = os.path.join(REPO_ROOT, "saves", "StarveNoMore.publish.json")
COVER = os.path.join(REPO_ROOT, "saves", "StarveNoMore.png")
ASSETS_LUA = os.path.join(REPO_ROOT, "lua", "assets.lua")
RAW_HOST = "https://raw.githubusercontent.com"
SHA_RE = re.compile(r"[0-9a-f]{40}")
REMOTE_RE = re.compile(
    r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
    r"([^/\s]+/[^/\s]+?)(?:\.git)?/?$")


def git(*args):
    proc = subprocess.run(["git", *args], cwd=REPO_ROOT,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def github_repo(remote_url):
    """'owner/repo' from an https or ssh GitHub remote URL."""
    m = REMOTE_RE.match(remote_url.strip())
    if not m:
        raise SystemExit(f"origin is not a GitHub repo: {remote_url}")
    return m.group(1)


def raw_base(repo, ref):
    return f"{RAW_HOST}/{repo}/{ref}"


def asset_paths(save, base, assets_lua):
    """Repo-relative path of every asset the publish save will fetch.

    They live in three places: object fields (image URLs on the table's
    objects), string literals in the Lua bundle (audio_manifest.lua), and
    lua/assets.lua — which builds its URLs at runtime as `_BASE .. "/" .. path`,
    so the save holds only `_BASE` and the paths come from its url("...") calls.
    """
    prefix = base.rstrip("/") + "/"
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str) and node.startswith(prefix):
            found.add(node[len(prefix):])

    for key, value in save.items():
        if key != "LuaScript":
            walk(value)
    lua = save.get("LuaScript", "")
    found.update(re.findall(re.escape(prefix) + r'([^"\s]+)"', lua))
    m = re.search(r'local _BASE = "' + re.escape(prefix) + r'([^"]+)"', lua)
    if m:
        found.discard(m.group(1))  # the directory itself, not a file
        found.update(f"{m.group(1)}/{p}"
                     for p in re.findall(r'\burl\("([^"]+)"\)', assets_lua))
    return found


def check_release(ref, offline):
    """Stop unless HEAD is `ref`, the tree is clean, and (online) GitHub has it."""
    dirty = git("status", "--porcelain", "--untracked-files=no")
    if dirty:
        raise SystemExit("Tracked files are modified — commit and push first, so "
                         "the save and the files its URLs serve match:\n" + dirty)
    is_sha = bool(SHA_RE.fullmatch(ref))
    if not is_sha and git("tag", "--list", ref) != ref:
        raise SystemExit(f"'{ref}' is not a tag (or a full commit SHA). Branches "
                         "move, so they can't be released. Tag the release:\n"
                         f"  git tag {ref} && git push origin {ref}")
    head = git("rev-parse", "HEAD")
    commit = git("rev-parse", f"{ref}^{{commit}}")
    if commit != head:
        raise SystemExit(f"HEAD is {head[:7]} but {ref} is {commit[:7]}. Build from "
                         f"the release itself: git checkout {ref}")
    if offline:
        return
    if is_sha:
        git("fetch", "-q", "origin")
        if "origin/main" not in git("branch", "-r", "--contains", ref).split():
            raise SystemExit(f"{ref[:7]} is not on origin/main — push it first.")
        return
    remote = git("ls-remote", "--tags", "origin",
                 f"refs/tags/{ref}", f"refs/tags/{ref}^{{}}")
    shas = dict(reversed(line.split("\t")) for line in remote.splitlines())
    # An annotated tag lists its own object too; the peeled ^{} line is the commit.
    remote_commit = shas.get(f"refs/tags/{ref}^{{}}") or shas.get(f"refs/tags/{ref}")
    if remote_commit is None:
        raise SystemExit(f"Tag {ref} isn't on GitHub yet: git push origin {ref}")
    if remote_commit != commit:
        raise SystemExit(f"Tag {ref} on GitHub is {remote_commit[:7]}, locally "
                         f"{commit[:7]}. Never move a released tag — cut a new one.")


def build(base):
    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "build_save.py"),
         "--publish", base, "--out", PUBLISH_SAVE],
        cwd=REPO_ROOT, env=child_env(), capture_output=True,
        encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise SystemExit(f"publish build failed:\n{proc.stdout}\n{proc.stderr}")


def http_status(url, timeout=30):
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "StarveNoMore-publish-check"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, OSError) as e:
        return f"{type(e).__name__}: {e}"


def broken_urls(urls, workers=8):
    """(url, status) for every URL that doesn't answer 200, after one retry."""
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        first = dict(zip(urls, pool.map(http_status, urls)))
        retry = [u for u, status in first.items() if status != 200]
        second = dict(zip(retry, pool.map(http_status, retry)))
    return sorted(((u, s) for u, s in second.items() if s != 200),
                  key=lambda pair: pair[0])


def install(ref):
    from iwanttoplay import find_tts_saves_dir
    saves = find_tts_saves_dir()
    if not saves:
        raise SystemExit("TTS Saves folder not found — copy "
                         f"{os.path.relpath(PUBLISH_SAVE, REPO_ROOT)} there by hand.")
    name = f"StarveNoMore Workshop {ref}"
    shutil.copyfile(PUBLISH_SAVE, os.path.join(saves, name + ".json"))
    if os.path.isfile(COVER):
        shutil.copyfile(COVER, os.path.join(saves, name + ".png"))
    return name


def main():
    use_utf8()
    ap = argparse.ArgumentParser(
        description="Build the Workshop save against GitHub-hosted assets and "
                    "verify every asset URL. See docs/publishing.md.")
    ap.add_argument("ref", help="release tag (e.g. v1.0), or a full commit SHA "
                                "already on origin/main")
    ap.add_argument("--offline", action="store_true",
                    help="skip the GitHub checks (ref pushed, URLs answer 200)")
    ap.add_argument("--install", action="store_true",
                    help="copy the save + cover PNG into the TTS Saves folder")
    args = ap.parse_args()

    check_release(args.ref, args.offline)
    base = raw_base(github_repo(git("remote", "get-url", "origin")), args.ref)
    print(f"Building against {base}")
    build(base)

    with open(PUBLISH_SAVE, encoding="utf-8") as f:
        save = json.load(f)
    with open(ASSETS_LUA, encoding="utf-8") as f:
        paths = asset_paths(save, base, f.read())
    in_tree = set(git("ls-tree", "-r", "--name-only", args.ref).splitlines())
    missing = sorted(paths - in_tree)
    if missing:
        raise SystemExit(f"The save references files that aren't in {args.ref}:\n  "
                         + "\n  ".join(missing))
    print(f"  {len(paths)} assets referenced — all committed in {args.ref}")

    if not args.offline:
        broken = broken_urls([f"{base}/{p}" for p in sorted(paths)])
        if broken:
            raise SystemExit("These asset URLs don't answer 200:\n  "
                             + "\n  ".join(f"{s}  {u}" for u, s in broken))
        print(f"  {len(paths)} URLs answer 200 from GitHub")

    print(f"  save: {os.path.relpath(PUBLISH_SAVE, REPO_ROOT)}")
    loaded = os.path.basename(PUBLISH_SAVE)
    if args.install:
        loaded = install(args.ref)
        print(f"  installed into the TTS Saves folder as \"{loaded}\"")
    print("\nNext, in Tabletop Simulator (docs/publishing.md, Phase C):\n"
          f"  1. Games > Save & Load > \"{loaded}\" — do NOT click Setup Game.\n"
          "  2. Upload > Workshop Upload: the Upload Workshop tab for the first\n"
          "     release, Update Workshop (with the item's ID) after that.")


if __name__ == "__main__":
    main()
