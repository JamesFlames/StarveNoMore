"""Every global function must be reachable from something.

This mod's worst bug class is not a crash — it is a rule that was written,
tested by hand, and then never connected to anything. The code is correct, the
*consumers of its state* are correct, and no button, dialog or handler ever
calls it. Nothing errors. The feature is simply absent, and the UI often goes
on describing it, so it reads to a player as a broken rule rather than a
missing one.

A 2026-07 audit found eight of them at once:

  * `reviveCharacter` — §16.4. Telltale Hearts could be *cooked* but never
    *spent*: `gameState.heartCount` only ever went up, while four separate
    places in the UI said "use a Telltale Heart at this tile to revive".
  * `doEnergyDrink` — James's Wired constraint. Four files read
    `jamesEnergyDrinkUsed` and one resets it nightly; nothing ever set it, so
    the -2 Sanity penalty was unavoidable for the whole seven-day campaign.
  * `doDefend` — Rayman's Backboard Block, printed in PlayerRules.md and in
    his own stat-box perk line. `combat_resolve` redirects damage when
    `raymanDefending` is set; nothing set it.
  * `doBarricade`, `doEatRaw`, `doStabilize`, `doAppeaseTreeguard`,
    `ghostDrift` — same shape, each with live consumers.

Load order is this codebase's dependency graph and there is no `require`, no
`_G[name]` lookup and no other dynamic dispatch anywhere — which is exactly
what makes "is this reachable?" a question a test can answer. So it does.

Scope note: `tests/` counts as a reference. A function called only by the
suite can be a deliberate test seam rather than dead code — `resolveCombat`
is one, a single-fighter shorthand the combat tests drive the resolver
through. An earlier pass of this audit scanned only `lua/` and `xml/` and
deleted two such seams; the suite caught it in the same run. Worth knowing
which you have: `resolveGroupCombat` looked like a seam too, and turned out
to be a pure alias for `beginCombat` that was deleted instead.
"""
import json
import os
import re

from conftest import LUA_DIR, ROOT, TESTS, XML_DIR, read_text

# Tabletop Simulator invokes these by name on the Global script. They are
# entry points from the engine, so nothing in this repo calls them and
# nothing should. Anything added here must be a real TTS event — the API
# surface is pinned separately in test_tts_api_surface.py.
TTS_EVENT_CALLBACKS = frozenset({
    "onLoad",             # save loaded / mod started
    "onSave",             # autosave and Save & Play
    "onObjectDrop",       # a player let go of an object (drag-to-move)
})

# Console-only entry points: a human types these into the TTS scripting
# console during a playtest. They have no in-game caller by design.
CONSOLE_ENTRY_POINTS = frozenset({
    "runSelfTest",
    "auditFirstLoad", "auditTooltips", "auditHintCoverage", "auditObjectCount",
    "auditBoardGeometry", "auditObjectFootprints", "lockdownCriticalObjects",
})

ALLOWED_UNREFERENCED = TTS_EVENT_CALLBACKS | CONSOLE_ENTRY_POINTS


# A comment naming a function is not a call. Stripping them is what makes the
# difference between "somebody wrote this down" and "something runs it" —
# and this module's own prose is the extreme case, so it excludes itself.
SELF = os.path.basename(__file__)

LUA_COMMENT_RE = re.compile(r"--.*$", re.M)
XML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def _strip_comments(rel, src):
    if rel.endswith(".lua"):
        return LUA_COMMENT_RE.sub("", src)
    if rel.endswith(".xml"):
        return XML_COMMENT_RE.sub("", src)
    # Python: left alone. A test's `#` comment or docstring naming a function
    # it does not call is harmless in practice, and the strings *are* the
    # call sites here — env.execute("doDefend('White')") is a real reference,
    # so nothing string-shaped can be dropped.
    return src


def _corpus():
    """{relpath: source} for everything that can reference a Lua global."""
    out = {}
    for base, exts in ((LUA_DIR, (".lua",)),
                       (XML_DIR, (".xml",)),
                       (TESTS, (".py", ".lua"))):
        for dirpath, _dirs, files in os.walk(base):
            if "__pycache__" in dirpath:
                continue
            for fn in sorted(files):
                if not fn.endswith(exts) or fn == SELF:
                    continue
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
                out[rel] = _strip_comments(rel, read_text(path))
    return out


def _global_functions():
    """[(name, file, line)] for every global function in the symbol index."""
    with open(os.path.join(ROOT, "symbols.json"), encoding="utf-8") as f:
        index = json.load(f)
    out = []
    for name, defs in index["symbols"].items():
        for d in defs:
            if d["kind"] == "function":
                out.append((name, d["file"].replace("\\", "/"), d["line"]))
    return sorted(out)


def _reference_count(name, definitions, corpus):
    """How many times `name` appears outside its own definition line(s).

    Namespaced entries (`Audio.playChime`) are matched on the member name:
    the index records the qualified name, the call sites write the same text,
    and the bare member is a tighter pattern than nothing.
    """
    pattern = re.compile(r"\b" + re.escape(name.split(".")[-1]) + r"\b")
    own = {(f, ln) for f, ln in definitions}
    count = 0
    for rel, text in corpus.items():
        for m in pattern.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            if (rel, line) not in own:
                count += 1
    return count


def test_no_global_function_is_unreachable():
    corpus = _corpus()
    by_name = {}
    for name, f, line in _global_functions():
        by_name.setdefault(name, []).append((f, line))

    orphans = []
    for name, definitions in sorted(by_name.items()):
        if name in ALLOWED_UNREFERENCED:
            continue
        if _reference_count(name, definitions, corpus) == 0:
            f, line = definitions[0]
            orphans.append(f"{f}:{line}  {name}()")

    assert not orphans, (
        f"{len(orphans)} global function(s) that nothing calls:\n  "
        + "\n  ".join(orphans)
        + "\n\nThis never fails at runtime — the rule is simply absent, while "
          "the UI may still describe it. Either wire it to a button, dialog or "
          "phase step, or delete it. If TTS itself calls it, add it to "
          "TTS_EVENT_CALLBACKS in this file (and check it against the real "
          "API); if it is a console-only playtest tool, add it to "
          "CONSOLE_ENTRY_POINTS."
    )


def test_the_allowlist_has_no_stale_entries():
    """An allowlist nobody prunes is where a real orphan hides."""
    defined = {name for name, _f, _l in _global_functions()}
    stale = sorted(ALLOWED_UNREFERENCED - defined)
    assert not stale, (
        f"allowlisted names that no longer exist in lua/: {stale} — remove "
        "them from TTS_EVENT_CALLBACKS / CONSOLE_ENTRY_POINTS in this file.")


def test_the_guard_can_actually_fail():
    """Pin the mechanism, so a broken matcher cannot silently pass everything.

    `onObjectDrop` really is referenced nowhere (it is why the allowlist
    exists), and `broadcastEvent` really is referenced everywhere.
    """
    corpus = _corpus()
    by_name = {}
    for name, f, line in _global_functions():
        by_name.setdefault(name, []).append((f, line))

    assert _reference_count("onObjectDrop", by_name["onObjectDrop"], corpus) == 0, \
        "onObjectDrop gained a caller — good, but then it should leave the allowlist"
    assert _reference_count("broadcastEvent", by_name["broadcastEvent"], corpus) > 100, \
        "the reference matcher stopped matching — every result above is meaningless"


def test_no_dynamic_dispatch_reintroduces_the_blind_spot():
    """The scan above is only sound because nothing looks a function up by
    name at runtime. `_G["doThing"]()` would make an orphan indistinguishable
    from a live handler, and this whole module would start lying."""
    offenders = []
    for rel, src in _corpus().items():
        if not rel.startswith("lua/"):
            continue
        for i, line in enumerate(src.splitlines(), 1):
            if line.lstrip().startswith("--"):
                continue
            if re.search(r"\b_G\s*\[", line) or re.search(r"\bloadstring\b", line):
                offenders.append(f"{rel}:{i}: {line.strip()}")
    assert not offenders, (
        "dynamic dispatch in lua/:\n  " + "\n  ".join(offenders)
        + "\n\nCall the function directly. Name-based lookup defeats "
          "test_no_global_function_is_unreachable, the symbol index, and "
          "luacheck all at once.")
