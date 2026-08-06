"""Guards for the one class of bug this suite structurally cannot catch.

Everything else here runs the real Lua bundle under real Lua 5.2 (lupa). TTS
runs **MoonSharp**. Where the two disagree, the suite is green and the game
throws — there is no runtime test that can see it, because the runtime under
test is the wrong runtime.

Both of these shipped, both reached players, and both were found by reading an
error in the chat log rather than by anything in here:

  - `s:match("^%s*(.-)%s*$")` — the standard Lua trim. MoonSharp abandons the
    unbounded lazy capture with "pattern too complex" once the subject passes
    a couple of hundred characters. The rulebook has 400- and 600-character
    paragraphs, so pressing '?' threw before a single help page rendered —
    every tab, not just the Rulebook.
  - `table.remove(t, 1)` on an EMPTY table — "bad argument #1 to 'remove'
    (position out of bounds)" in MoonSharp, plain `nil` in real Lua. Every
    queue drain reaches the empty case on its last pass, so the achievement
    toast logged an error every single time one unlocked.

The fix in both cases was a helper in helpers.lua (`trim`, `popFirst`). These
tests keep the raw idioms from creeping back in. Adding to this file is
cheap and worth it: each entry is a bug that would otherwise only be found by
a player. Engine background: docs/tts-interface.md.
"""
import os
import re

from conftest import LUA_DIR, all_lua_files, read_text

# The file allowed to contain each idiom: the helper that replaces it.
HELPERS = "helpers.lua"


def _code_lines(rel):
    """(line_no, text) for every line of a Lua file that is not a comment.

    Prose gets to name the idiom it is warning about — several of these
    comments do exactly that — so only real code is scanned.
    """
    src = read_text(os.path.join(LUA_DIR, rel))
    out = []
    for i, line in enumerate(src.splitlines(), start=1):
        if line.lstrip().startswith("--"):
            continue
        out.append((i, re.sub(r"--.*$", "", line)))
    return out


def test_no_unbounded_lazy_capture_trim():
    """`(.-)` spanning a whole string is the shape MoonSharp gives up on."""
    # `(.-)` followed by anything anchored to the end: the trim family.
    pattern = re.compile(r"\(\s*\.\-\s*\)[^\"']*%s\*\$")
    problems = []
    for rel in all_lua_files():
        if rel == HELPERS:
            continue
        for lineno, line in _code_lines(rel):
            if pattern.search(line):
                problems.append(f"{rel}:{lineno}: {line.strip()}")
    assert not problems, (
        'MoonSharp aborts `("^%s*(.-)%s*$")`-shaped patterns with "pattern too '
        "complex" + " on long subjects, and real Lua (this suite) does not — so "
        "nothing here will fail when it breaks in game. Use trim() from "
        "helpers.lua:\n  " + "\n  ".join(problems))


def test_no_table_remove_from_the_front():
    """`table.remove(t, 1)` throws on an empty table in MoonSharp."""
    pattern = re.compile(r"table\.remove\s*\(\s*[\w_.\[\]\"']+\s*,\s*1\s*\)")
    problems = []
    for rel in all_lua_files():
        if rel == HELPERS:
            continue
        for lineno, line in _code_lines(rel):
            if pattern.search(line):
                problems.append(f"{rel}:{lineno}: {line.strip()}")
    assert not problems, (
        "table.remove(list, 1) throws in TTS when the list is empty ('position "
        "out of bounds') and returns nil in real Lua, so this suite cannot see "
        "it. Every queue drain hits the empty case on its final pass. Use "
        "popFirst() from helpers.lua:\n  " + "\n  ".join(problems))


def test_no_vector_distance_method_calls():
    """`pos:distance(other)` leans on the engine's Vector metatable.

    What `Object.getPosition()` hands back is engine-provided, and whether it
    carries Vector's methods is the engine's business — real Lua under this
    suite has whatever the stub gives it, which is not evidence about TTS. All
    three callers wrapped it in a bare pcall, so a failure was invisible:
    `_spawnCraftButtons` reported "No cards in the Market display" to a player
    looking at five of them, and `doCraft` spent the action and did nothing.
    objDistance() reads x/y/z and does the arithmetic itself.
    """
    pattern = re.compile(r":distance(?:Squared)?\s*\(")
    problems = []
    for rel in all_lua_files():
        if rel == HELPERS:
            continue
        for lineno, line in _code_lines(rel):
            if pattern.search(line):
                problems.append(f"{rel}:{lineno}: {line.strip()}")
    assert not problems, (
        "Vector:distance() calls. Use objDistance(a, b) from helpers.lua, which "
        "works off the x/y/z numbers and returns nil rather than throwing:\n  "
        + "\n  ".join(problems))


def test_the_helpers_that_replace_them_exist():
    """The bans above are only reasonable while the alternatives are there."""
    src = read_text(os.path.join(LUA_DIR, HELPERS))
    for fn in ("function trim(", "function popFirst(", "function objDistance("):
        assert fn in src, (
            f"{fn}...) is gone from {HELPERS}, but the guards above still send "
            "people to it")
