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
