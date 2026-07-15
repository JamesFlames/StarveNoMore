"""Prose file-name references in the navigation-layer docs must resolve.

test_doc_links.py already guards markdown *links*; this guards bare source
file names mentioned inline in prose (e.g. "`getPlayerResources` in
`lua/ui_actionbar.lua`"). Those aren't links, so a rename/split that leaves a
stale name behind slips past the link checker — which is exactly how the
`ui_actionbar.lua` → `ui_actionbar_{core,targets,handlers,display}.lua` split
left four dangling references in agents.md.

Scope is the maps a newcomer navigates by (agents.md / README.md / TASKMAP.md
/ CLAUDE.md + the per-directory CLAUDE.md stubs). Working/historical docs that
discuss past states by name (structuralimprovements.md, anything in Archive/)
are intentionally out of scope.
"""
import os
import re

import pytest

from conftest import ROOT

# .lua tokens like `foo_bar.lua`; the leading char rules out `..4.lua` shorthand.
LUA_TOKEN_RE = re.compile(r"\b([a-z_][a-z0-9_]*\.lua)\b")

# The navigation-layer docs whose file names must stay accurate.
NAV_DOCS = [
    "agents.md",
    "README.md",
    "TASKMAP.md",
    "CLAUDE.md",
    os.path.join("lua", "CLAUDE.md"),
    os.path.join("scripts", "CLAUDE.md"),
    os.path.join("tests", "CLAUDE.md"),
    os.path.join("content", "CLAUDE.md"),
]


def _real_lua_basenames():
    """Every real *.lua filename in the tree (basename → resolves somewhere)."""
    names = set()
    for dirpath, dirs, files in os.walk(ROOT):
        parts = os.path.relpath(dirpath, ROOT).replace("\\", "/").split("/")
        if parts[0] in (".git", "Archive", ".claude", "__pycache__", "node_modules"):
            dirs[:] = []
            continue
        for fn in files:
            if fn.endswith(".lua"):
                names.add(fn)
    return names


@pytest.mark.parametrize("doc", NAV_DOCS)
def test_nav_doc_lua_refs_resolve(doc):
    path = os.path.join(ROOT, doc)
    if not os.path.isfile(path):
        pytest.skip(f"{doc} absent")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    real = _real_lua_basenames()
    dangling = sorted({tok for tok in LUA_TOKEN_RE.findall(text) if tok not in real})
    assert not dangling, (
        f"{doc} names *.lua files that don't exist: {dangling} — a file was "
        "renamed/split without updating this map. Fix the reference(s).")
