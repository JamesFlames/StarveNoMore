"""The agent reference stays split, and the two jump tables stay honest.

agents.md was ~18.6k tokens in one file, and CLAUDE.md points at it as the deep
reference — so an agent that needed one section either paid for the whole file
or grepped blind. It is now an index plus one topic per file under docs/agents/.

Splits decay: files creep back over budget, and a new topic gets added to one
jump table but not the other, so it is unreachable from whichever index the
reader happened to open. Both are cheap to check.
"""
import os
import re

import pytest

from conftest import ROOT

AGENTS_DIR = os.path.join(ROOT, "docs", "agents")
INDEX = os.path.join(AGENTS_DIR, "README.md")
ROOT_DOC = os.path.join(ROOT, "agents.md")

# ~4 chars per token. The budget the split exists to hold; see
# docs/agents/README.md. A file over it should be split at a real seam.
CHARS_PER_TOKEN = 4
TOKEN_BUDGET = 2500
# The root index is deliberately larger: it keeps the Documentation Map, which
# is the thing read first and is a poor candidate for another indirection.
ROOT_TOKEN_BUDGET = 3200

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def topic_files():
    return sorted(f for f in os.listdir(AGENTS_DIR)
                  if f.endswith(".md") and f != "README.md")


def _tokens(path):
    with open(path, encoding="utf-8") as f:
        return len(f.read()) // CHARS_PER_TOKEN


@pytest.mark.parametrize("name", topic_files())
def test_topic_file_is_within_the_context_budget(name):
    tok = _tokens(os.path.join(AGENTS_DIR, name))
    assert tok <= TOKEN_BUDGET, (
        f"docs/agents/{name} is ~{tok} tokens (budget {TOKEN_BUDGET}). Split it "
        "at a real seam and add the new file to BOTH jump tables "
        "(agents.md and docs/agents/README.md) — that is how the monolith grew "
        "back last time."
    )


def test_root_agents_md_stays_an_index():
    tok = _tokens(ROOT_DOC)
    assert tok <= ROOT_TOKEN_BUDGET, (
        f"agents.md is ~{tok} tokens (budget {ROOT_TOKEN_BUDGET}). It is the "
        "index — the Documentation Map, the conventions, and the jump table. "
        "Deep material belongs in a docs/agents/ topic file."
    )


def _linked_topics(path, prefix):
    """Topic files linked from `path`.

    `prefix` anchors the match so the index's "related indexes, not here"
    links (../../TASKMAP.md, ../gamestate.md) are not mistaken for topics:
    from docs/agents/README.md a topic is a bare sibling filename, and from
    agents.md it is `docs/agents/<name>`.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()
    out = set()
    for target in LINK_RE.findall(text):
        target = target.split("#")[0]
        if not target.endswith(".md") or not target.startswith(prefix):
            continue
        rest = target[len(prefix):]
        if "/" in rest or rest == "README.md":
            continue
        out.add(rest)
    return out


def test_both_jump_tables_list_every_topic():
    """A topic reachable from one index but not the other is half-invisible."""
    on_disk = set(topic_files())
    from_root = _linked_topics(ROOT_DOC, "docs/agents/")
    from_index = _linked_topics(INDEX, "")

    assert on_disk == from_root, (
        "agents.md's jump table disagrees with docs/agents/: "
        f"missing={sorted(on_disk - from_root)} "
        f"stale={sorted(from_root - on_disk)}")
    assert on_disk == from_index, (
        "docs/agents/README.md's table disagrees with the directory: "
        f"missing={sorted(on_disk - from_index)} "
        f"stale={sorted(from_index - on_disk)}")


@pytest.mark.parametrize("name", topic_files())
def test_topic_file_points_back_at_the_index(name):
    """Every topic file must be navigable back out of, or a reader who lands
    in one by grep has no idea what else exists."""
    with open(os.path.join(AGENTS_DIR, name), encoding="utf-8") as f:
        text = f.read()
    assert "README.md" in text and "agents.md" in text, (
        f"docs/agents/{name} has no link back to the index or to agents.md")
