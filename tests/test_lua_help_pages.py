"""The in-game rulebook (Help > Rulebook) and the Help panel's pagination.

The bug class this guards is silent, which is why it needs a test rather than a
reminder: a TTS `Text` element renders what fits and CLIPS the rest — no
scrollbar, no ellipsis, no warning. An over-long Help tab therefore looks
perfectly fine and simply stops mid-sentence. The Glossary was ~7,000
characters against a body that holds roughly 2,000.

So two properties matter:
  1. Pagination loses NOTHING — every line of the book is reachable.
  2. No page overflows the body — or paging has just moved the clipping.
"""
import math

import pytest

from conftest import add_char, lua_to_py, make_env

pytest.importorskip("lupa")

# helpBody is 498px tall at fontSize 12 → ~34 rendered lines. A page estimated
# above this is one that will clip in the real client.
BODY_LINE_CAPACITY = 34


def _pages(env, expr):
    p = lua_to_py(env.eval(f"paginateHelpText({expr})"))
    return list(p.values()) if isinstance(p, dict) else p


def _estimated_lines(page, width=62):
    return sum(max(1, math.ceil(len(line) / width)) for line in page.split("\n"))


@pytest.fixture
def env():
    rt = make_env()
    rt.execute("gameState.started = true")
    add_char(rt, "White", "Coco")
    rt.execute('gameState.activeColor = "White"')
    return rt


TAB_SOURCES = {
    "rulebook": "rulebookText()",
    "glossary": "HELP_GLOSSARY",
    "quickstart": "quickStartTextForVariant()",
    "full_rules": "NOTEBOOK_FULL_RULES",
    "characters": "NOTEBOOK_CHARACTERS",
}


@pytest.mark.parametrize("name", sorted(TAB_SOURCES))
def test_pagination_loses_no_content(env, name):
    source = env.eval(TAB_SOURCES[name])
    pages = _pages(env, TAB_SOURCES[name])
    joined = "\n".join(pages)
    lost = [ln.strip() for ln in source.splitlines()
            if ln.strip() and ln.strip() not in joined]
    assert not lost, (
        f"{name}: pagination dropped {len(lost)} line(s), first: {lost[0]!r}")


@pytest.mark.parametrize("name", sorted(TAB_SOURCES))
def test_no_page_overflows_the_help_body(env, name):
    pages = _pages(env, TAB_SOURCES[name])
    over = [(i + 1, _estimated_lines(p)) for i, p in enumerate(pages)
            if _estimated_lines(p) > BODY_LINE_CAPACITY]
    assert not over, (
        f"{name}: page(s) estimated to overflow helpBody's ~{BODY_LINE_CAPACITY} "
        f"lines: {over} — a TTS Text clips silently, so this text is invisible. "
        "Lower HELP_PAGE_LINES in lua/ui_help_pages.lua.")


def test_the_rulebook_carries_all_four_sections(env):
    """It is the whole player rulebook or it isn't worth having in-game."""
    book = env.eval("rulebookText()")
    for heading in ("QUICK START", "FULL RULES", "THE CHARACTERS", "GLOSSARY"):
        assert heading in book, f"the in-game rulebook is missing {heading}"
    assert len(book) > 15000, (
        f"the rulebook is only {len(book)} chars — a section probably came "
        "through empty because a generated constant is missing")


def test_rulebook_quick_start_follows_the_chosen_difficulty(env):
    """A Story or Long Weekend table must not be handed Standard's numbers —
    that is §17.2's whole point, and the rulebook is the most authoritative
    place to get it wrong."""
    env.execute('gameState.difficulty = "weekend"')
    book = env.eval("rulebookText()")
    assert "Long Weekend" in book
    assert "Survive 3 nights" in book or "3 nights" in book

    env.execute('gameState.difficulty = "story"')
    book = env.eval("rulebookText()")
    assert "Story" in book
    assert "below 35" in book, "Story's Doom track is 35, not 30"


def test_rulebook_tab_is_reachable_and_pages_forward(env):
    env.eval("onHelpTab")({"color": "White"}, "", "helpTabRules")
    ui = lua_to_py(env.eval("TTS.ui"))
    assert ui["attrs"]["helpPageNav"]["active"] == "true"
    first = ui["attrs"]["helpBody"]["text"]
    assert "STARVE NO MORE" in first

    env.eval("onHelpPageNext")({"color": "White"}, "", "helpPageNext")
    ui = lua_to_py(env.eval("TTS.ui"))
    assert ui["attrs"]["helpBody"]["text"] != first, "More did not turn the page"
    assert "page 2 of" in ui["attrs"]["helpPageLabel"]["text"]


def test_paging_clamps_at_both_ends(env):
    env.eval("onHelpTab")({"color": "White"}, "", "helpTabRules")
    total = len(_pages(env, "rulebookText()"))
    for _ in range(total + 20):
        env.eval("onHelpPageNext")({"color": "White"}, "", "helpPageNext")
    ui = lua_to_py(env.eval("TTS.ui"))
    assert ui["attrs"]["helpPageLabel"]["text"] == f"page {total} of {total}"
    assert (ui["attrs"]["helpBody"]["text"] or "").strip(), (
        "the last page is blank — paging ran off the end of the book")

    for _ in range(total + 20):
        env.eval("onHelpPagePrev")({"color": "White"}, "", "helpPagePrev")
    ui = lua_to_py(env.eval("TTS.ui"))
    assert ui["attrs"]["helpPageLabel"]["text"] == f"page 1 of {total}"


def test_page_position_is_remembered_per_tab(env):
    env.eval("onHelpTab")({"color": "White"}, "", "helpTabRules")
    env.eval("onHelpPageNext")({"color": "White"}, "", "helpPageNext")
    env.eval("onHelpPageNext")({"color": "White"}, "", "helpPageNext")
    env.eval("onHelpTab")({"color": "White"}, "", "helpTabDoom")
    env.eval("onHelpTab")({"color": "White"}, "", "helpTabRules")
    ui = lua_to_py(env.eval("TTS.ui"))
    assert "page 3 of" in ui["attrs"]["helpPageLabel"]["text"], (
        "leaving the Rulebook and coming back reset it to the cover")


def test_short_tabs_hide_the_page_nav(env):
    """An always-visible pager on a one-page tab is noise."""
    env.eval("onHelpTab")({"color": "White"}, "", "helpTabDawn")
    ui = lua_to_py(env.eval("TTS.ui"))
    assert ui["attrs"]["helpPageNav"]["active"] == "false"
