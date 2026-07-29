"""The shared repository walker, and the rule that everyone uses it.

`.claude/worktrees/<branch>/` is a *complete second checkout of this
repository* — every doc, every lua file, at whatever revision that branch sits
on. Any test that scans the tree and forgets to prune it is validating a mix
of two revisions, and will blame the live file for the stale copy's contents.

Four modules had hand-rolled that walk with a copy-pasted exclusion tuple.
Three listed `.claude`; the fourth — the one that resolved citation *targets*
in test_doc_section_refs.py — did not. It resolved
`PrinciplesOfGoodBoardGames.md` to a worktree's older 13-section copy, and the
suite reported 11 failures against citations that were all correct.

So: one walker in conftest (`walk_repo` / `repo_files`, pruning `SKIP_DIRS`),
and the two tests below — one proving the walker really does prune nested
checkouts, one proving nobody has quietly reintroduced a private copy.
"""
import os
import re

from conftest import ROOT, SKIP_DIRS, TESTS, read_text, repo_files, walk_repo

# `os.walk(ROOT)` in a test module — the pattern that drifted. Anything that
# needs to scan the repo goes through conftest instead.
HANDROLLED_RE = re.compile(r"os\.walk\(\s*ROOT\b")


def _nested_checkout_roots():
    """Directories under ROOT that are themselves a git checkout: a worktree
    has a `.git` *file* pointing at the real gitdir, a clone has a `.git`
    directory. ROOT itself does not count."""
    found = []
    for dirpath, _dirs, _files in os.walk(ROOT):
        if os.path.abspath(dirpath) == os.path.abspath(ROOT):
            continue
        if os.path.exists(os.path.join(dirpath, ".git")):
            found.append(dirpath)
    return found


def test_walk_repo_prunes_nested_checkouts():
    """The walker must not yield anything from a second checkout of this repo.

    Skipped when there is no worktree to prune (a clean CI clone), because
    proving nothing about an absent directory is honest and asserting on one
    is not — the two tests below cover the mechanism either way.
    """
    nested = _nested_checkout_roots()
    walked = {os.path.abspath(dirpath) for dirpath, _files in walk_repo()}
    leaked = [n for n in nested
              if any(w == os.path.abspath(n) or w.startswith(os.path.abspath(n) + os.sep)
                     for w in walked)]
    assert not leaked, (
        f"walk_repo descended into a nested git checkout: {leaked} — those "
        "hold a second copy of every doc and lua file at another revision, so "
        "any basename lookup can resolve to the wrong one. Add the containing "
        "directory name to conftest.SKIP_DIRS.")


def test_walk_repo_prunes_every_skip_dir_at_any_depth():
    """Pruning is by directory name at any depth, not just the top level.

    The directory that caused the outage was two levels down
    (`.claude/worktrees/<branch>/`), which a `parts[0] in (...)` check catches
    only because `.claude` happens to be at the root. Pin the general rule.
    """
    offenders = []
    for dirpath, _files in walk_repo():
        parts = os.path.relpath(dirpath, ROOT).replace("\\", "/").split("/")
        hit = SKIP_DIRS.intersection(parts)
        if hit:
            offenders.append(f"{'/'.join(parts)} (contains {sorted(hit)})")
    assert not offenders, (
        "walk_repo yielded directories it was supposed to prune: " + str(offenders))


def test_repo_files_is_ordered_and_finds_the_obvious_files():
    """A "first match wins" lookup over an unordered walk is a coin flip that
    passes on one machine and fails on another. Order is part of the contract.
    """
    docs = repo_files(".md", skip=("Archive",))
    assert docs == sorted(docs), "repo_files must return a stable, sorted order"

    rel = {os.path.relpath(p, ROOT).replace("\\", "/") for p in docs}
    assert {"CLAUDE.md", "agents.md", "TASKMAP.md"}.issubset(rel), \
        "repo_files(.md) missed root docs that certainly exist — the walk broke"
    assert not any(r.startswith("Archive/") for r in rel), \
        "skip=('Archive',) did not prune Archive/"

    lua = {os.path.basename(p) for p in repo_files(".lua", skip=("Archive",))}
    assert {"global.lua", "helpers.lua"}.issubset(lua)


def test_no_test_module_hand_rolls_a_repo_walk():
    """Four copies of one walk, three of them right — the fourth cost a red
    suite. A private copy is how the exclusion list drifts, so it is banned
    rather than reviewed."""
    offenders = []
    for fn in sorted(os.listdir(TESTS)):
        if not fn.endswith(".py") or fn in ("conftest.py", os.path.basename(__file__)):
            continue
        for i, line in enumerate(read_text(os.path.join(TESTS, fn)).splitlines(), 1):
            if HANDROLLED_RE.search(line):
                offenders.append(f"{fn}:{i}")
    assert not offenders, (
        f"test modules walking ROOT directly: {offenders} — use "
        "conftest.walk_repo()/repo_files(), which prune .claude/worktrees and "
        "the other non-content directories in one place. Walking a specific "
        "subtree (os.walk(LUA_DIR)) is fine; it is the whole-repo scan that "
        "needs the shared exclusion list.")
