#!/usr/bin/env python3
"""sym — answer "where is X, and who calls it?" in one command.

SYMBOLS.md is ~17k tokens, so reading it to locate one function is enormously
wasteful; grepping it returns a bare table row (`| 93 | function | beginNight |`)
with no signature and no neighbours, so you end up opening the file anyway.
This reads symbols.json (same generator, same freshness test) and prints the
location, the signature, the comment above the definition, and every call site.

    python scripts/sym.py beginNight        # exact, else substring matches
    python scripts/sym.py --ui duskReadyBtn # an XML UI element id
    python scripts/sym.py --file night.lua  # everything one file defines
    python scripts/sym.py -q gather         # locations only, no call sites

Regenerate with: python scripts/generate_symbol_index.py (or scripts/check.py).
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(ROOT, "symbols.json")
LUA_DIR = os.path.join(ROOT, "lua")
MAX_CALL_SITES = 25


def load_index():
    if not os.path.isfile(JSON_PATH):
        sys.exit("symbols.json missing — run: python scripts/generate_symbol_index.py")
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def signature(rec, name):
    if rec["kind"] != "function":
        return name
    if rec["params"] is None:
        return f"{name}(…)"  # multi-line signature; arity not recorded
    return f"{name}({', '.join(rec['params'])})"


def call_sites(name, defs):
    """Every lua/ line mentioning `name` that is not one of its definitions."""
    defined_at = {(d["file"], d["line"]) for d in defs}
    word = re.compile(rf"\b{re.escape(name)}\b")
    hits = []
    for dirpath, _dirs, filenames in os.walk(LUA_DIR):
        for fn in sorted(filenames):
            if not fn.endswith(".lua"):
                continue
            path = os.path.join(dirpath, fn)
            rel = "lua/" + os.path.relpath(path, LUA_DIR).replace(os.sep, "/")
            try:
                with open(path, encoding="utf-8") as f:
                    lines = f.read().splitlines()
            except OSError:
                continue
            for i, line in enumerate(lines, 1):
                if (rel, i) in defined_at or not word.search(line):
                    continue
                hits.append((rel, i, line.strip()))
    return hits


def show_symbol(name, defs, index, quiet):
    for rec in defs:
        print(f"\n{signature(rec, name)}")
        print(f"  {rec['file']}:{rec['line']}   ({rec['kind']}"
              + (f", arity {rec['arity']}" if rec["arity"] is not None else "") + ")")
        if rec["doc"]:
            print(f"  — {rec['doc']}")

    # An XML id whose onClick names this function is the other half of the
    # story for a UI handler: the button that fires it.
    buttons = [(eid, meta) for eid, meta in index.get("xml_ids", {}).items()
               if meta.get("onClick") == name]
    for eid, meta in buttons:
        print(f"  fired by XML id '{eid}' ({meta['file']}:{meta['line']}, "
              f"<{meta['element']}>)")

    if quiet:
        return
    hits = call_sites(name, defs)
    if not hits:
        print("\n  no other references in lua/ — dead code, or called from XML/TTS only")
        return
    print(f"\n  {len(hits)} reference(s):")
    for rel, lineno, text in hits[:MAX_CALL_SITES]:
        print(f"    {rel}:{lineno}  {text[:100]}")
    if len(hits) > MAX_CALL_SITES:
        print(f"    … and {len(hits) - MAX_CALL_SITES} more")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", nargs="?", help="symbol, XML id (--ui), or file (--file)")
    ap.add_argument("--ui", action="store_true", help="look NAME up as an XML element id")
    ap.add_argument("--file", action="store_true", help="list what a lua file defines")
    ap.add_argument("-q", "--quiet", action="store_true", help="skip the call-site scan")
    args = ap.parse_args()

    index = load_index()
    symbols = index["symbols"]

    if not args.name:
        print(f"{len(symbols)} symbols, {len(index.get('xml_ids', {}))} XML ids "
              f"indexed in symbols.json. Try: python scripts/sym.py beginNight")
        return 0

    if args.file:
        want = args.name if args.name.startswith("lua/") else f"lua/{args.name}"
        rows = sorted(((rec["line"], n, rec) for n, defs in symbols.items()
                       for rec in defs if rec["file"] == want))
        if not rows:
            files = sorted({rec["file"] for defs in symbols.values() for rec in defs})
            print(f"no symbols indexed for '{want}'. Known files:\n  "
                  + "\n  ".join(files))
            return 1
        print(f"{want} — {len(rows)} symbols")
        for line, n, rec in rows:
            print(f"  {line:5}  {rec['kind']:8}  {signature(rec, n)}")
        return 0

    if args.ui:
        ids = index.get("xml_ids", {})
        meta = ids.get(args.name)
        if not meta:
            near = [i for i in ids if args.name.lower() in i.lower()]
            print(f"no XML id '{args.name}'." + (f" Did you mean: {', '.join(near[:10])}"
                                                 if near else ""))
            return 1
        print(f"\n'{args.name}'  <{meta['element']}>")
        print(f"  {meta['file']}:{meta['line']}")
        if meta["onClick"]:
            handler = meta["onClick"]
            print(f"  onClick → {handler}")
            if handler in symbols:
                for rec in symbols[handler]:
                    print(f"            {rec['file']}:{rec['line']}  "
                          f"{signature(rec, handler)}")
            else:
                print("            (!) no Lua definition indexed for that handler")
        return 0

    if args.name in symbols:
        show_symbol(args.name, symbols[args.name], index, args.quiet)
        return 0

    needle = args.name.lower()
    near = sorted(n for n in symbols if needle in n.lower())
    if not near:
        print(f"no symbol matching '{args.name}'. "
              "Regenerate the index if you just added it: python scripts/check.py")
        return 1
    if len(near) == 1:
        show_symbol(near[0], symbols[near[0]], index, args.quiet)
        return 0
    print(f"{len(near)} symbols matching '{args.name}':")
    for n in near[:40]:
        rec = symbols[n][0]
        print(f"  {rec['file']}:{rec['line']:<5}  {signature(rec, n)}")
    if len(near) > 40:
        print(f"  … and {len(near) - 40} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
