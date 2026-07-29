#!/usr/bin/env python3
"""Run every generator (in dependency order), then build the save — one command.

Correctly rebuilding the mod means running the *right* generator for whatever
source you touched (six generate_*.py that write lua/*.lua, plus the symbol
index and the player rulebook), then build_save.py. generators.json documents
that mapping and tests/test_generated_freshness.py *catches* staleness after
the fact — this script just **does** it, so an agent or contributor doesn't
have to remember the DAG.

The plan is derived from scripts/generators.json (so it can't drift from the
manifest): each distinct generator script is run once, in the manifest's order,
which already lists the lua-data generators before generate_symbol_index.py
(it reads all of lua/). A generator whose sources are all missing is skipped —
that lets a fresh clone without the ~955 MB sounds/ tree still build (the
committed audio_manifest.lua is left untouched) instead of erroring out.

Usage:
    python scripts/regenerate_all.py            # regenerate everything + build
    python scripts/regenerate_all.py --no-build # generators only, skip build_save
    python scripts/regenerate_all.py --list     # print the plan and exit
"""
import argparse
import json
import os
import subprocess
import sys

from utf8_console import child_env, use_utf8

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATORS_JSON = os.path.join(ROOT, "scripts", "generators.json")
BUILD_SCRIPT = os.path.join(ROOT, "scripts", "build_save.py")


def load_plan():
    """Distinct generator scripts in manifest order, with their sources.

    Returns a list of (script_relpath, [source_relpath, ...]) preserving the
    order generators.json lists them and collapsing scripts that emit more
    than one output (generate_symbol_index, generate_player_rules).
    """
    with open(GENERATORS_JSON, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    plan = []
    seen = {}
    for entry in manifest["generators"]:
        script = entry["script"]
        if script in seen:
            # merge any additional sources for the same script
            for s in entry.get("sources", []):
                if s not in seen[script]:
                    seen[script].append(s)
            continue
        sources = list(entry.get("sources", []))
        seen[script] = sources
        plan.append((script, sources))
    return plan


def sources_present(sources):
    return any(os.path.exists(os.path.join(ROOT, s)) for s in sources)


def run(script):
    print(f"  → {script}")
    proc = subprocess.run([sys.executable, os.path.join(ROOT, script)],
                          cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=child_env())
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"generator failed: {script} (exit {proc.returncode})")
    return proc.stdout


def main():
    # Before argparse: --help prints this module's docstring, and the progress
    # lines below use →. Neither survives the legacy codepage a redirected
    # stdout falls back to. Not at import, so importing this module is inert.
    use_utf8()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-build", action="store_true",
                    help="run the generators but skip build_save.py")
    ap.add_argument("--list", action="store_true",
                    help="print the ordered plan and exit without running anything")
    args = ap.parse_args()

    plan = load_plan()

    if args.list:
        for script, sources in plan:
            state = "run" if sources_present(sources) else "skip (sources absent)"
            print(f"{state:24} {script}   <- {', '.join(sources)}")
        if not args.no_build:
            print(f"{'run':24} scripts/build_save.py")
        return

    print("Regenerating all derived files:")
    skipped = []
    for script, sources in plan:
        if sources_present(sources):
            run(script)
        else:
            skipped.append(script)
            print(f"  - {script} — skipped (sources absent: {', '.join(sources)})")

    if not args.no_build:
        print("Building save:")
        print("  → scripts/build_save.py")
        proc = subprocess.run([sys.executable, BUILD_SCRIPT], cwd=ROOT,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=child_env())
        sys.stdout.write(proc.stdout)
        if proc.returncode != 0:
            sys.stderr.write(proc.stderr)
            raise SystemExit(f"build_save.py failed (exit {proc.returncode})")

    print("Done." + (f" Skipped {len(skipped)} generator(s) with absent sources."
                      if skipped else ""))


if __name__ == "__main__":
    main()
