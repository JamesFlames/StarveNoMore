"""
Scan lua/*.lua → docs/gamestate.md — the schema map for `gameState`.

`gameState` is the game's single source of truth: 71 distinct fields read or
written across 41 of 46 Lua files, with no schema anywhere. An agent asked to
"add a field" or "find who clears X" had to grep and guess, and a misspelling
(`activeChar` for `activeChars`) reads as nil, silently, at runtime, in TTS.

This emits, per field: its declared default (parsed straight out of
migrateGameState() in global.lua), the files that WRITE it, the files that
READ it, and its lifetime.

The map is documentation. The guard that pays for it is
tests/test_gamestate_schema.py, which asserts every `gameState.<name>` in
lua/ is either declared in migrateGameState() or listed in TRANSIENT_FIELDS
below — so a typo becomes a named test failure instead of a nil.

Run: python scripts/generate_gamestate_map.py
Output: docs/gamestate.md
"""
import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LUA_DIR = os.path.join(REPO_ROOT, "lua")
OUT_PATH = os.path.join(REPO_ROOT, "docs", "gamestate.md")

# --------------------------------------------------------------------------
# The transient allowlist.
#
# A field belongs here ONLY if nil is a meaningful state for it — i.e. it is
# created on demand and cleared again, so declaring a default in
# migrateGameState() would be wrong rather than merely redundant. Everything
# else belongs in migrateGameState().
#
# This list is the escape hatch for the schema guard, so keep it justified.
# Adding a name here is a deliberate act; the guard's whole value is that a
# field appearing in neither place fails the suite.
# --------------------------------------------------------------------------
TRANSIENT_FIELDS = {
    "nil is the default": (
        (
            "Absent means 'none right now'. migrateGameState() lists these "
            "explicitly as deliberately undeclared."
        ),
        ["activeColor", "activeDawn", "combatContext", "scenario", "pathVariant"],
    ),
    "per-turn": (
        (
            "Created when a turn needs them, dropped when it ends. A stale value "
            "surviving into the next turn would be the bug."
        ),
        ["pendingAction", "undoSnapshot", "tradesThisTurn", "turnStartedAt",
         "lastActiveColor", "duskReady", "duskMoves"],
    ),
    "per-day": (
        (
            "Reset at Dawn (BeginDay) — once-per-day flags and the day's opening "
            "snapshot. Lazily re-created at their read sites."
        ),
        # nightStage: which of the Night's four steps is running. Absent
        # outside the Night, which is exactly the question its readers ask —
        # a declared default would make every other phase look like a Night
        # step. Set and cleared by ResolveNight.
        ["nightStage",
         "raymanMovedToday", "raymanFoughtToday", "raymanBonusMove",
         "raymanDefending", "jamesEnergyDrinkUsed", "jamesPeekUsed",
         "jamesRerollUsed", "lucaRallyUsed", "dayStartStats", "dawnChecklist",
         "nightOmen", "usedRecipes"],
    ),
    "world state": (
        (
            "Set when the thing exists on the table and cleared when it does not "
            "(a boss, a barricade, an opened basement)."
        ),
        ["barricades", "basementOpened", "bossesDefeated", "eyeLocation",
         "heartCount", "treeguard", "sourceSplit", "wrongness",
         # Strict Rationing's restock clock. nil means "never restocked",
         # which is exactly what the first refill of the week must see — a
         # declared 0 would read as "restocked on day 0" and silently delay
         # it. Only that scenario ever writes it.
         "lastMarketRefillDay"],
    ),
    "end of game": (
        "Written once, when the game ends. Absent for the whole run before that.",
        ["gameOverCause", "gameCounted"],
    ),
    "ui-local": (
        (
            "Panel visibility that rides gameState only because onSave/onLoad is "
            "the only store a TTS mod has."
        ),
        ["msgLogHidden"],
    ),
    "lazily built": (
        (
            "Has exactly one constructor elsewhere, so declaring a default here "
            "would be a second copy of that shape waiting to drift. Reached "
            "through its accessor, never assumed to exist."
        ),
        ["chronicle"],   # ensureChronicle(), lua/ui_week_review.lua
    ),
}


def transient_names():
    out = {}
    for category, (_reason, fields) in TRANSIENT_FIELDS.items():
        for f in fields:
            out[f] = category
    return out


def lua_files():
    """Every lua source, as (relpath, text), in a stable order."""
    out = []
    for dirpath, _dirs, names in os.walk(LUA_DIR):
        for n in sorted(names):
            if not n.endswith(".lua"):
                continue
            path = os.path.join(dirpath, n)
            rel = os.path.relpath(path, LUA_DIR).replace(os.sep, "/")
            with open(path, encoding="utf-8") as f:
                out.append((rel, f.read()))
    return sorted(out)


def parse_declared():
    """field -> default expression, parsed out of migrateGameState()."""
    with open(os.path.join(LUA_DIR, "global.lua"), encoding="utf-8") as f:
        src = f.read()
    m = re.search(r"^function migrateGameState\(\).*?^end", src, re.M | re.S)
    if not m:
        raise SystemExit("could not find migrateGameState() in lua/global.lua")
    body = m.group(0)
    declared = {}
    # `gs.x = gs.x or DEFAULT`
    for name, default in re.findall(r"^\s*gs\.(\w+)\s*=\s*gs\.\1\s+or\s+(.+?)\s*(?:--.*)?$",
                                    body, re.M):
        declared.setdefault(name, default.strip())
    # `if gs.x == nil then gs.x = V end`
    for name, default in re.findall(
            r"if\s+gs\.(\w+)\s*==\s*nil\s+then\s+gs\.\1\s*=\s*(.+?)\s+end", body):
        declared.setdefault(name, default.strip())
    # plain `gs.x = V` (e.g. schemaVersion), and multi-line `or` continuations
    for name, default in re.findall(r"^\s*gs\.(\w+)\s*=\s*(.+?)\s*(?:--.*)?$", body, re.M):
        declared.setdefault(name, default.strip())
    return declared


FIELD_RE = re.compile(r"\bgameState\.([A-Za-z_]\w*)")


def scan_usage():
    """field -> {"writes": [files], "reads": [files]}."""
    usage = {}
    for rel, src in lua_files():
        for field in set(FIELD_RE.findall(src)):
            entry = usage.setdefault(field, {"writes": [], "reads": []})
            # `gameState.f =` but not `==`; the same line can also be a read
            # (`gameState.f = gameState.f or {}`), which the counts below allow.
            writes = len(re.findall(rf"\bgameState\.{field}\s*=(?!=)", src))
            total = len(re.findall(rf"\bgameState\.{field}\b", src))
            if writes:
                entry["writes"].append(rel)
            if total > writes:
                entry["reads"].append(rel)
    return usage


def onsave_is_a_bare_encode():
    """True while onSave() persists the whole table with no exclusions."""
    with open(os.path.join(LUA_DIR, "global.lua"), encoding="utf-8") as f:
        src = f.read()
    m = re.search(r"^function onSave\(\).*?^end", src, re.M | re.S)
    return bool(m) and bool(re.search(r"return\s+JSON\.encode\(\s*gameState\s*\)", m.group(0)))


def main():
    declared = parse_declared()
    usage = scan_usage()
    transient = transient_names()
    fields = sorted(usage)

    undeclared = [f for f in fields if f not in declared and f not in transient]

    L = []
    L.append("# `gameState` schema map")
    L.append("")
    L.append("*AUTO-GENERATED by `scripts/generate_gamestate_map.py` — do not edit by hand.*")
    L.append("")
    L.append("Every field of `gameState`, where its default comes from, and which files "
             "touch it. `gameState` is the game's single source of truth and is persisted "
             "whole by `onSave`, so \"who clears this?\" and \"what is this when a save is "
             "restored?\" are the two questions that come up constantly.")
    L.append("")
    L.append(f"**{len(fields)} fields** across "
             f"**{len({f for v in usage.values() for f in v['writes'] + v['reads']})} files**. "
             f"{len([f for f in fields if f in declared])} have a declared default in "
             "`migrateGameState()` (`lua/global.lua`); "
             f"{len([f for f in fields if f in transient])} are deliberately transient "
             "(see the table's *lifetime* column).")
    L.append("")
    L.append("## Persistence")
    L.append("")
    if onsave_is_a_bare_encode():
        L.append("`onSave()` is `return JSON.encode(gameState)` — the **whole table** is "
                 "persisted with no exclusions, so every field below survives a save/load "
                 "if it is non-nil at save time. There is no per-field persistence rule to "
                 "look up. `tests/test_gamestate_schema.py::test_onsave_persists_the_whole_table` "
                 "fails if that ever stops being true, because this section would then be "
                 "lying.")
    else:
        L.append("> **`onSave()` no longer persists the whole table verbatim.** Per-field "
                 "persistence now has to be read out of `onSave()` in `lua/global.lua` — "
                 "and this generator should be taught to report it.")
    L.append("")
    L.append("## Adding a field")
    L.append("")
    L.append("Declare its default in `migrateGameState()` (`lua/global.lua`) — that is the "
             "one door both a restored save and the Restart path go through. Only add a "
             "name to `TRANSIENT_FIELDS` in the generator if **nil is a meaningful state** "
             "for it. A field in neither place fails "
             "`tests/test_gamestate_schema.py::test_every_field_is_declared_or_transient`, "
             "which is what turns a misspelling (`activeChar` for `activeChars`) from a "
             "silent nil into a named failure.")
    L.append("")
    L.append("## Fields")
    L.append("")
    L.append("| field | default | lifetime | written by | read by |")
    L.append("|---|---|---|---|---|")
    for f in fields:
        if f in declared:
            default = f"`{declared[f]}`"
            lifetime = "declared"
        else:
            default = "—"
            lifetime = transient.get(f, "**UNDECLARED**")
        writes = ", ".join(f"`{w}`" for w in usage[f]["writes"]) or "—"
        reads = ", ".join(f"`{r}`" for r in usage[f]["reads"]) or "—"
        L.append(f"| `{f}` | {default} | {lifetime} | {writes} | {reads} |")
    L.append("")

    L.append("## Transient categories")
    L.append("")
    L.append("Why each group is allowed to have no declared default:")
    L.append("")
    for category in sorted(TRANSIENT_FIELDS):
        reason, names = TRANSIENT_FIELDS[category]
        live = sorted(n for n in names if n in usage)
        L.append(f"- **{category}** — {reason}")
        L.append(f"  {', '.join('`' + n + '`' for n in live)}")
    L.append("")

    if undeclared:
        L.append("## ⚠ Undeclared")
        L.append("")
        L.append("These are in neither `migrateGameState()` nor `TRANSIENT_FIELDS`, so "
                 "`tests/test_gamestate_schema.py` is failing:")
        L.append("")
        for f in undeclared:
            L.append(f"- `{f}`")
        L.append("")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))

    print(f"wrote {os.path.relpath(OUT_PATH, REPO_ROOT)} ({len(fields)} fields, "
          f"{len(declared)} declared, {len(transient)} transient"
          + (f", {len(undeclared)} UNDECLARED" if undeclared else "") + ")")


if __name__ == "__main__":
    main()
