"""Relative markdown links in the live docs must point at files that exist.

Catches deleting/renaming a file that README, agents.md, the design doc, or
the content docs still reference. Archive/ is historical and exempt.
"""
import os
import re

import pytest
from conftest import ROOT

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def live_markdown_files():
    out = []
    for dirpath, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT)
        parts = rel.replace("\\", "/").split("/")
        if parts[0] in ("Archive", ".git", ".claude", "__pycache__", "node_modules"):
            dirs[:] = []
            continue
        for fn in files:
            if fn.endswith(".md"):
                out.append(os.path.join(dirpath, fn))
    return out


def test_every_root_doc_is_in_the_agents_map():
    """agents.md's Documentation Map is the index a newcomer (human or agent)
    navigates by — a root-level doc it doesn't mention is invisible. Guard
    the map against rot: every root *.md must be named in agents.md."""
    with open(os.path.join(ROOT, "agents.md"), "r", encoding="utf-8") as f:
        agents = f.read()
    missing = []
    for fn in sorted(os.listdir(ROOT)):
        if fn.endswith(".md") and fn != "agents.md" and fn not in agents:
            missing.append(fn)
    assert not missing, (
        f"root-level docs absent from agents.md's Documentation Map: {missing} — "
        "add an entry (or retire the doc into CHANGELOG.md + git history)")


@pytest.mark.parametrize("md_path", live_markdown_files(),
                         ids=lambda p: os.path.relpath(p, ROOT).replace("\\", "/"))
def test_relative_links_resolve(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    base = os.path.dirname(md_path)
    broken = []
    for target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # strip anchors and :line suffixes
        path = target.split("#")[0]
        path = re.sub(r":\d+$", "", path)
        if not path:
            continue
        resolved = os.path.normpath(os.path.join(base, path))
        if not os.path.exists(resolved):
            broken.append(target)
    assert not broken, (
        f"{os.path.relpath(md_path, ROOT)} links to missing files: {broken}"
    )
