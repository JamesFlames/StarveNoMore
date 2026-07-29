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
from conftest import ROOT, repo_files

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
] + [
    # agents.md's deep reference, split one topic per file (see
    # docs/agents/README.md). Each carries the same per-file detail the
    # monolith did, so each needs the same dangling-filename guard.
    os.path.join("docs", "agents", f)
    for f in sorted(os.listdir(os.path.join(ROOT, "docs", "agents")))
    if f.endswith(".md")
]


def _real_lua_basenames():
    """Every real *.lua filename in the tree (basename → resolves somewhere)."""
    return {os.path.basename(p) for p in repo_files(".lua", skip=("Archive",))}


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


# --------------------------------------------------------------------------
# Guard names cited in the docs must resolve to a real test.
# --------------------------------------------------------------------------
# The TTS docs sell themselves on "every rule was learned from a live failure;
# the linked guards keep the fixed ones fixed". A guard name that no longer
# exists silently voids that promise — the reader trusts a check that isn't
# running. Renaming a test is exactly when this rots, and it did:
# test_locked_player_boards_rest_on_the_table_rather_than_hover grew to cover
# market slots too, was renamed, and left a dangling citation behind.

# Bare `test_foo` tokens: either a test function or a test MODULE
# (docs say things like "test_build_output.py::test_no_objects...").
# The trailing guard lets a doc write the glob `test_lua_*.py` for a whole
# family of modules without it reading as a test named "test_lua_".
TEST_TOKEN_RE = re.compile(r"\b(test_[a-zA-Z0-9_]+)(?![*\w])")


def _real_test_names():
    """Every test function name and test module basename in tests/."""
    names = set()
    tests_dir = os.path.join(ROOT, "tests")
    for fn in os.listdir(tests_dir):
        if not (fn.startswith("test_") and fn.endswith(".py")):
            continue
        names.add(fn[:-3])
        with open(os.path.join(tests_dir, fn), "r", encoding="utf-8") as f:
            names.update(re.findall(r"^\s*def (test_[a-zA-Z0-9_]+)", f.read(), re.M))
    return names


def _docs_that_cite_guards():
    out = []
    docs_dir = os.path.join(ROOT, "docs")
    if os.path.isdir(docs_dir):
        out += [os.path.join("docs", f) for f in sorted(os.listdir(docs_dir))
                if f.endswith(".md")]
    return out + ["agents.md", "TASKMAP.md", "CLAUDE.md"]


@pytest.mark.parametrize("doc", _docs_that_cite_guards())
def test_doc_guard_names_resolve(doc):
    path = os.path.join(ROOT, doc)
    if not os.path.isfile(path):
        pytest.skip(f"{doc} absent")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    real = _real_test_names()
    dangling = sorted({tok for tok in TEST_TOKEN_RE.findall(text) if tok not in real})
    assert not dangling, (
        f"{doc} cites guards that no longer exist: {dangling} — a test was "
        "renamed or removed. Point the doc at the test that covers it now, or "
        "drop the claim; a citation to a missing guard is worse than none.")
