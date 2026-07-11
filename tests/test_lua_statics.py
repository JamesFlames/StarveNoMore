"""Static hazards specific to the concatenated-bundle architecture.

build_save.py joins every lua file into one global script, so a global
function or constant defined twice means the later definition silently
replaces the earlier one — the single most dangerous failure mode of this
architecture.
"""
import re
from collections import defaultdict

# Top-level (column 0) global definitions only; locals and indented
# definitions are scoped or intentional.
GLOBAL_FN_RE = re.compile(r"^function\s+([A-Za-z0-9_]+(?:[.:][A-Za-z0-9_]+)*)\s*\(", re.M)
GLOBAL_ASSIGN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?!=)", re.M)

# Names that are legitimately assigned more than once at top level.
REDEFINITION_WHITELIST = set()


def find_definitions(lua_sources, regex):
    defs = defaultdict(list)
    for rel, src in lua_sources.items():
        for m in regex.finditer(src):
            line = src.count("\n", 0, m.start()) + 1
            defs[m.group(1)].append(f"{rel}:{line}")
    return defs


def test_no_duplicate_global_functions(lua_sources):
    defs = find_definitions(lua_sources, GLOBAL_FN_RE)
    dupes = {name: places for name, places in defs.items()
             if len(places) > 1 and name not in REDEFINITION_WHITELIST}
    assert not dupes, (
        "Global functions defined more than once — the later definition silently "
        "wins in the concatenated bundle:\n"
        + "\n".join(f"  {n}: {', '.join(p)}" for n, p in sorted(dupes.items()))
    )


def test_no_duplicate_global_assignments(lua_sources):
    defs = find_definitions(lua_sources, GLOBAL_ASSIGN_RE)
    dupes = {name: places for name, places in defs.items()
             if len(places) > 1 and name not in REDEFINITION_WHITELIST}
    assert not dupes, (
        "Top-level globals assigned in more than one place — later assignment "
        "silently resets the earlier one:\n"
        + "\n".join(f"  {n}: {', '.join(p)}" for n, p in sorted(dupes.items()))
    )


def test_load_order_files_all_exist(load_order, lua_sources):
    missing = [f for f in load_order if f not in lua_sources]
    assert not missing, f"LUA_LOAD_ORDER names files that do not exist: {missing}"


def test_no_accidental_extra_lua_files(load_order, lua_sources):
    """Every lua file should be deliberately placed in LUA_LOAD_ORDER.
    Extras are appended *after* everything else, which breaks anything that
    must be defined before use at load time. assets.lua is the one known,
    self-contained extra."""
    known_extras = {"assets.lua"}
    extras = set(lua_sources) - set(load_order) - known_extras
    assert not extras, (
        f"lua files not in LUA_LOAD_ORDER (appended last, load order not guaranteed): "
        f"{sorted(extras)} — add them to LUA_LOAD_ORDER in build_save.py"
    )
