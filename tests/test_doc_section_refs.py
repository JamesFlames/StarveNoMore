"""A `<file>.md §N` citation must point at a section that exists in that file.

`test_doc_links.py` guards markdown *links* and `test_doc_file_refs.py` guards
inline *filenames*. Neither validates the §-number, so the design docs' cites
into `Archive/PrinciplesOfGoodBoardGames.md` drifted silently when that
document was renumbered: Jo-Ha-Kyu was cited as §7 when it had become §9, the
alpha-player problem as §8 when it was §10 (and then §20), multiple victory
paths as §11 when it was §12. Fixing those four by hand without this test
means the same drift again in six months, so the test is the fix.

Scope: cross-document citations only — `Foo.md §N` where the §-number is meant
to index *Foo*'s headings. Bare `§N` references (the overwhelming majority) are
self-references into the design doc's own numbering and are checked by the
design-doc index, not here. Archive/ files are historical: they are valid
*targets* but their own outbound citations are exempt.
"""
import os
import re

import pytest
from conftest import ROOT, repo_files, walk_repo

# "SomeDoc.md §12" / "SomeDoc.md §12.4" / "SomeDoc.md §1–26" — optionally with
# markdown link syntax and arbitrary path in between, e.g.
# "[PrinciplesOfGoodBoardGames.md §9](../../Archive/PrinciplesOfGoodBoardGames.md)".
CITE_RE = re.compile(r"([A-Za-z0-9_.\-]+\.md)\s*§\s*(\d+)")

# Headings numbered like "## 12. Victory Conditions" or "### 16.2 Bonus victories".
HEADING_RE = re.compile(r"^#{1,6}\s+(\d+)(?:\.\d+)*\.?\s", re.MULTILINE)

# Ranges ("§1–26", "§18.10–18.18") name a span, not one section; the endpoints
# are checked, the interior is not enumerated here.
EXEMPT_TARGETS = frozenset()


def live_markdown_files():
    return repo_files(".md", skip=("Archive",))


def _target_candidates(basename):
    """Every copy of a cited .md in the repo, Archive included — the citations
    point *into* Archive. Uses the shared walker, so `.claude/worktrees/`
    (a whole second checkout of this repo) is pruned rather than searched."""
    return [os.path.join(dirpath, basename)
            for dirpath, files in walk_repo() if basename in files]


def _find_target(basename):
    """The one copy of a cited .md, or None if it is not in the repo."""
    hits = _target_candidates(basename)
    return hits[0] if hits else None


def _section_numbers(path):
    with open(path, "r", encoding="utf-8") as f:
        return {int(m) for m in HEADING_RE.findall(f.read())}


@pytest.mark.parametrize("md_path", live_markdown_files(),
                         ids=lambda p: os.path.relpath(p, ROOT).replace("\\", "/"))
def test_cross_document_section_refs_exist(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    self_name = os.path.basename(md_path)
    bad = []
    cache = {}
    for basename, num in CITE_RE.findall(text):
        if basename == self_name or basename in EXEMPT_TARGETS:
            continue
        if basename not in cache:
            target = _find_target(basename)
            cache[basename] = _section_numbers(target) if target else None
        sections = cache[basename]
        if sections is None:
            continue  # a missing file is test_doc_links.py's job, not ours
        if int(num) not in sections:
            bad.append(f"{basename} §{num}")

    assert not bad, (
        f"{os.path.relpath(md_path, ROOT)} cites sections that don't exist in the "
        f"target document: {sorted(set(bad))} — the target was renumbered; "
        "re-read its headings and update the citation")


# The existence check above catches "§99" but not "§7 when you meant §9" — §7
# exists, it is simply a different chapter. The cheap fix for that is to name
# the chapter in the citation, which the 2026-07 fixes do:
#     [PrinciplesOfGoodBoardGames.md §9](...) — Pacing and the Game Arc
# This second test makes that habit load-bearing: wherever a citation supplies
# a title, the title must be the one that section actually carries. Citations
# without a title are still allowed (there are dozens) — but any that opt in
# get the strong check, so a renumber breaks the build instead of the reader.
TITLED_CITE_RE = re.compile(
    r"([A-Za-z0-9_.\-]+\.md)\s*§\s*(\d+)\](?:\([^)]*\))?\s*(?:—|--)\s*([^;.,()\n]+)")


def _section_titles(path):
    """{section number: heading title} for top-level numbered headings."""
    titles = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^#{1,6}\s+(\d+)\.?\s+(.*?)\s*$", line)
            if m:
                titles.setdefault(int(m.group(1)), m.group(2))
    return titles


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


@pytest.mark.parametrize("md_path", live_markdown_files(),
                         ids=lambda p: os.path.relpath(p, ROOT).replace("\\", "/"))
def test_titled_section_refs_name_the_right_section(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    self_name = os.path.basename(md_path)
    wrong = []
    cache = {}
    for basename, num, claimed in TITLED_CITE_RE.findall(text):
        if basename == self_name:
            continue
        if basename not in cache:
            target = _find_target(basename)
            cache[basename] = _section_titles(target) if target else None
        titles = cache[basename]
        if not titles:
            continue
        actual = titles.get(int(num))
        if not actual:
            continue  # existence is the other test's job
        if _norm(claimed) not in _norm(actual):
            wrong.append(f"{basename} §{num} called '{claimed.strip()}', "
                         f"but §{num} is '{actual}'")

    assert not wrong, (
        f"{os.path.relpath(md_path, ROOT)} mis-titles a cited section: {wrong} — "
        "either the number or the title is stale; check the target's headings")


def test_the_guard_can_actually_fail():
    """A citation checker that silently matches nothing is worse than none.
    Pin the mechanism: the principles doc really does have §9 and §20 (the two
    numbers the 2026-07 fix moved citations *to*) and really does not have §99.
    """
    target = _find_target("PrinciplesOfGoodBoardGames.md")
    assert target, "Archive/PrinciplesOfGoodBoardGames.md is missing"
    sections = _section_numbers(target)
    assert {9, 20}.issubset(sections)
    assert 99 not in sections


def test_cited_documents_resolve_unambiguously():
    """Every cited basename must name exactly one file in the repo.

    Resolution is by basename, so a second copy anywhere makes the answer a
    coin flip — and the *stale* copy is the one that fails. That is how this
    module went red for a whole afternoon: a git worktree under
    `.claude/worktrees/` carried an older PrinciplesOfGoodBoardGames.md with
    13 sections instead of 26, so every citation above §13 "did not exist".
    Failing here says which file is duplicated; failing above blames the docs.
    """
    cited = set()
    for md_path in live_markdown_files():
        self_name = os.path.basename(md_path)
        with open(md_path, "r", encoding="utf-8") as f:
            cited.update(b for b, _n in CITE_RE.findall(f.read()) if b != self_name)

    duplicated = {}
    for basename in sorted(cited):
        hits = _target_candidates(basename)
        if len(hits) > 1:
            duplicated[basename] = [
                os.path.relpath(p, ROOT).replace("\\", "/") for p in hits]

    assert not duplicated, (
        f"cited documents exist in more than one place: {duplicated} — a "
        "basename lookup cannot tell them apart, so the citation checks above "
        "silently validate against whichever copy the walk reached first. "
        "Delete the duplicate, or prune its directory in conftest.SKIP_DIRS.")
