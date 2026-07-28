"""
Scan lua/*.lua + xml/*.xml → SYMBOLS.md + symbols.json + .luacheckrc

The Lua bundle is 25+ files of globals concatenated by build_save.py.
This generator produces:

1. SYMBOLS.md — the missing table of contents: every global function and
   top-level constant, which file owns it, and its line number — plus every
   XML UI element id (with its handler), since UI work always starts from
   an id like "duskReadyBtn". One lookup instead of N greps, for humans
   and AI agents alike.

2. symbols.json — the same index, machine-readable and with more per symbol
   (signature, arity, the comment above the definition). SYMBOLS.md is ~17k
   tokens, so reading it to answer "where is beginNight?" is enormously
   wasteful and grepping it returns a bare table row with no signature.
   `python scripts/sym.py beginNight` reads this file instead and answers in
   one call, with call sites. SYMBOLS.md stays: it is the human-browsable view.

3. .luacheckrc — a luacheck config whose `globals` list is exactly the
   bundle's own symbols plus the TTS API, so `luacheck lua/` flags reads
   or writes of anything undefined (i.e. typos like `gamestate`).

Run: python scripts/generate_symbol_index.py
Output: SYMBOLS.md, symbols.json, .luacheckrc (repo root)
"""

import json
import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LUA_DIR = os.path.join(REPO_ROOT, "lua")
XML_DIR = os.path.join(REPO_ROOT, "xml")
MD_PATH = os.path.join(REPO_ROOT, "SYMBOLS.md")
JSON_PATH = os.path.join(REPO_ROOT, "symbols.json")
LUACHECKRC_PATH = os.path.join(REPO_ROOT, ".luacheckrc")

FUNC_RE = re.compile(r"^function\s+([A-Za-z_][\w.]*)\s*\(", re.M)
CONST_RE = re.compile(r"^([A-Za-z_]\w*)\s*=", re.M)

# Globals provided by the TTS engine / the test stub, not the bundle.
TTS_API = [
    "Vector", "Wait", "UI", "Player", "JSON", "Global", "Turns", "Notes",
    "MusicPlayer", "Physics", "Time", "Color",
    "broadcastToAll", "broadcastToColor", "printToAll", "printToColor", "log",
    "getAllObjects", "getObjectsWithTag", "getObjectFromGUID",
    "spawnObject", "spawnObjectJSON", "destroyObject", "startLuaCoroutine",
    "TTS",
    # onLoad / onSave are TTS callbacks but the bundle *defines* them
    # (global.lua), so they belong in the bundle's own writable globals —
    # not here, where read_globals would flag the definition as read-only.
]

# TTS engine globals whose *fields* the bundle legitimately writes (e.g.
# ui_mood.lua sets Lighting.light_intensity). These must be writable globals,
# not read_globals, or luacheck flags "setting read-only field".
TTS_MUTABLE = ["Lighting"]


def load_order():
    """File order from scripts/load_order.json (the build manifest), so the
    index reads in the same order the bundle loads."""
    with open(os.path.join(REPO_ROOT, "scripts", "load_order.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    files = manifest["lua"]
    if not files:
        raise SystemExit("load_order.json 'lua' list is empty")
    return files, manifest.get("xml", [])


# A run of `--` lines directly above a definition is its docstring. Banner
# comments (`-- ===== section =====`) are decoration, not documentation.
COMMENT_RE = re.compile(r"^\s*--+\s?(.*?)\s*$")
BANNER_RE = re.compile(r"^[=\-~*_ ]*$")
DOC_MAX = 160


def doc_above(lines, idx):
    """The comment block immediately above lines[idx], as one short string."""
    block = []
    i = idx - 1
    while i >= 0:
        m = COMMENT_RE.match(lines[i])
        if not m:
            break
        text = m.group(1)
        if not BANNER_RE.match(text):
            block.append(text)
        i -= 1
    if not block:
        return ""
    doc = " ".join(reversed(block)).strip()
    return doc[: DOC_MAX - 1] + "…" if len(doc) > DOC_MAX else doc


def scan(rel_path):
    """Return [{line, kind, name, params, doc}] of globals in one lua file.

    `params` is the parameter list for a function whose signature closes on
    its own line, else None — detection of the *definition* deliberately uses
    the same open-paren-only regex as before, so a multi-line signature is
    still indexed (just without a recorded arity).
    """
    path = os.path.join(LUA_DIR, rel_path.replace("/", os.sep))
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    out = []
    for idx, line in enumerate(lines):
        lineno = idx + 1
        m = re.match(r"^function\s+([A-Za-z_][\w.]*)\s*\(", line)
        if m:
            closed = re.match(r"^function\s+[A-Za-z_][\w.]*\s*\(([^)]*)\)", line)
            params = ([p.strip() for p in closed.group(1).split(",") if p.strip()]
                      if closed else None)
            out.append({"line": lineno, "kind": "function", "name": m.group(1),
                        "params": params, "doc": doc_above(lines, idx)})
            continue
        m = re.match(r"^([A-Za-z_]\w*)\s*=", line)
        if m and m.group(1) not in ("local",):
            out.append({"line": lineno,
                        "kind": "table" if "{" in line else "value",
                        "name": m.group(1), "params": None,
                        "doc": doc_above(lines, idx)})
    return out


XML_ID_RE = re.compile(r'<(\w+)\b[^>]*?\bid="([^"]+)"[^>]*?>', re.S)
XML_ONCLICK_RE = re.compile(r'onClick="([^"(]+)')


def scan_xml(rel_path):
    """Return [(line, element, id, onClick_or_empty)] for one xml file.
    Elements are matched from their opening '<' line; attributes may span
    lines, so search each tag's full text."""
    path = os.path.join(XML_DIR, rel_path)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    out = []
    for m in XML_ID_RE.finditer(text):
        lineno = text.count("\n", 0, m.start()) + 1
        onclick = XML_ONCLICK_RE.search(m.group(0))
        out.append((lineno, m.group(1), m.group(2), onclick.group(1) if onclick else ""))
    return out


def main():
    files, xml_files = load_order()
    per_file = {f: scan(f) for f in files}

    # ---- SYMBOLS.md ----
    L = []
    L.append("# Symbol Index")
    L.append("")
    L.append("*AUTO-GENERATED by `scripts/generate_symbol_index.py` — do not edit by hand.*")
    L.append("*Every global function and top-level constant in the Lua bundle, in load order.*")
    L.append("")
    total = 0
    for f in files:
        syms = per_file[f]
        total += len(syms)
        L.append(f"## lua/{f} ({len(syms)} symbols)")
        L.append("")
        if not syms:
            L.append("*(no top-level globals)*")
        else:
            L.append("| line | kind | symbol |")
            L.append("|---|---|---|")
            for s in syms:
                L.append(f"| {s['line']} | {s['kind']} | `{s['name']}` |")
        L.append("")
    L.append("## Alphabetical")
    L.append("")
    L.append("| symbol | file | line |")
    L.append("|---|---|---|")
    flat = sorted((s["name"], f, s["line"])
                  for f, syms in per_file.items()
                  for s in syms)
    for name, f, lineno in flat:
        L.append(f"| `{name}` | lua/{f} | {lineno} |")
    L.append("")

    # ---- XML UI ids ----
    # UI work starts from an element id ("where is duskReadyBtn?"); index
    # every id with its element type and onClick handler so the answer is
    # one lookup, not a grep across xml/ + lua/.
    xml_ids = []
    for xf in xml_files:
        for lineno, element, elem_id, onclick in scan_xml(xf):
            xml_ids.append((elem_id, xf, lineno, element, onclick))
    L.append(f"## XML UI ids ({len(xml_ids)} ids)")
    L.append("")
    L.append("*Element ids across xml/ (alphabetical). Lua targets these via "
             "`UI.show/hide/setAttribute`; onClick names the Lua handler.*")
    L.append("")
    L.append("| id | file | line | element | onClick |")
    L.append("|---|---|---|---|---|")
    for elem_id, xf, lineno, element, onclick in sorted(xml_ids):
        handler = f"`{onclick}`" if onclick else ""
        L.append(f"| `{elem_id}` | xml/{xf} | {lineno} | {element} | {handler} |")
    L.append("")
    with open(MD_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))

    # ---- symbols.json (the queryable view; see scripts/sym.py) ----
    # A name maps to a LIST of definitions: tests/test_lua_statics.py forbids
    # a duplicate global, but the index must be able to *show* one if the
    # guard is ever relaxed or bypassed, rather than silently keeping one.
    symbols = {}
    for f in files:
        for s in per_file[f]:
            symbols.setdefault(s["name"], []).append({
                "file": f"lua/{f}",
                "line": s["line"],
                "kind": s["kind"],
                "params": s["params"],
                "arity": None if s["params"] is None else len(s["params"]),
                "doc": s["doc"],
            })
    payload = {
        "_comment": (
            "AUTO-GENERATED by scripts/generate_symbol_index.py — do not edit by hand. "
            "Machine-readable twin of SYMBOLS.md. Query it with: python scripts/sym.py NAME"
        ),
        "symbols": dict(sorted(symbols.items())),
        "xml_ids": {
            elem_id: {"file": f"xml/{xf}", "line": lineno,
                      "element": element, "onClick": onclick}
            for elem_id, xf, lineno, element, onclick in sorted(xml_ids)
        },
    }
    with open(JSON_PATH, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, sort_keys=False, ensure_ascii=False)
        fh.write("\n")

    # ---- .luacheckrc ----
    # luacheck lints *every* file under lua/, so the globals list must cover
    # them all — including files not in the build load order (e.g. assets.lua,
    # appended separately by build_save.py). Scan those extras too, or their
    # top-level globals (ASSETS) read as "non-standard global" warnings.
    all_globals = {s["name"] for syms in per_file.values() for s in syms}
    for root, _dirs, names in os.walk(LUA_DIR):
        for n in sorted(names):
            if not n.endswith(".lua"):
                continue
            rel = os.path.relpath(os.path.join(root, n), LUA_DIR).replace(os.sep, "/")
            if rel in per_file:
                continue
            all_globals |= {s["name"] for s in scan(rel)}
    bundle_globals = sorted({name.split(".")[0] for name in all_globals})
    C = []
    C.append("-- .luacheckrc — AUTO-GENERATED by scripts/generate_symbol_index.py.")
    C.append("-- Run: luacheck lua/   (flags reads/writes of undefined globals, i.e. typos)")
    C.append('std = "lua52"')
    C.append("max_line_length = false")
    C.append("unused = false")
    C.append("unused_args = false")
    C.append("redefined = false")
    C.append("-- The bundle's own globals (defined across the concatenated files),")
    C.append("-- plus TTS engine globals the bundle writes fields on (TTS_MUTABLE):")
    C.append("globals = {")
    for g in sorted(set(bundle_globals) | set(TTS_MUTABLE)):
        C.append(f'    "{g}",')
    C.append("}")
    C.append("-- The TTS engine API (read-only from the bundle's perspective):")
    C.append("read_globals = {")
    for g in TTS_API:
        C.append(f'    "{g}",')
    C.append("}")
    C.append("")
    with open(LUACHECKRC_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(C))

    print(f"wrote {os.path.relpath(MD_PATH, REPO_ROOT)} ({total} symbols, {len(files)} files, "
          f"{len(xml_ids)} xml ids)")
    print(f"wrote {os.path.relpath(JSON_PATH, REPO_ROOT)} ({len(symbols)} unique names)")
    print(f"wrote {os.path.relpath(LUACHECKRC_PATH, REPO_ROOT)} ({len(bundle_globals)} bundle globals)")


if __name__ == "__main__":
    main()
