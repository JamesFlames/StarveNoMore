"""Static hazards specific to the concatenated-bundle architecture.

build_save.py joins every lua file into one global script, so a global
function or constant defined twice means the later definition silently
replaces the earlier one — the single most dangerous failure mode of this
architecture.
"""
import glob
import json
import os
import re
from collections import defaultdict

from conftest import ROOT

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
    """Every lua file must be deliberately placed in the build manifest.

    With one global namespace and no require(), load order IS the dependency
    graph. An unlisted file used to be appended last behind a printed NOTE
    that nothing failed on, so a new file whose globals another module read at
    load time would silently be nil — at runtime, in TTS, which is the
    hardest place to diagnose. build_save.py now hard-fails on the same
    condition; this is the static twin that reports it in the suite.
    """
    with open(os.path.join(ROOT, "scripts", "load_order.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    extras = set(lua_sources) - set(load_order) - set(manifest.get("lua_extra", []))
    assert not extras, (
        f"lua files in neither 'lua' nor 'lua_extra' in scripts/load_order.json: "
        f"{sorted(extras)} — add each to 'lua' at the position its dependencies "
        "require (definitions before consumers), or to 'lua_extra' if it must be "
        "excluded from the bundle on purpose."
    )


def test_manifest_names_only_files_that_exist():
    """The other direction: a manifest entry for a deleted file is a silent
    WARNING during the build, and the bundle quietly loses that code."""
    with open(os.path.join(ROOT, "scripts", "load_order.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    missing = []
    for key, subdir in (("lua", "lua"), ("lua_extra", "lua"),
                        ("xml", "xml"), ("xml_extra", "xml")):
        for rel in manifest.get(key, []):
            if not os.path.isfile(os.path.join(ROOT, subdir, rel)):
                missing.append(f"{key}: {rel}")
    assert not missing, (
        "scripts/load_order.json names files that do not exist:\n  "
        + "\n  ".join(missing)
    )


def test_no_accidental_extra_xml_files():
    """XML is concatenated too, so a later file can shadow an earlier file's
    element ids. Same manifest rule as Lua."""
    with open(os.path.join(ROOT, "scripts", "load_order.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    on_disk = {os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "xml", "*.xml"))}
    extras = on_disk - set(manifest["xml"]) - set(manifest.get("xml_extra", []))
    assert not extras, (
        f"xml files in neither 'xml' nor 'xml_extra' in scripts/load_order.json: "
        f"{sorted(extras)}"
    )
