#!/usr/bin/env python3
"""One command for "am I done?" — regenerate, build, test, lint.

The finish-line ritual used to be three commands (regenerate_all → build_save →
pytest), which is three chances to do two of them. This runs the lot and prints
a one-line verdict.

Stages, in order (each gates the next):

1. ``scripts/regenerate_all.py`` — every generator, then ``build_save.py``.
   Skips generators whose sources are absent (a clean clone has no ``sounds/``).
2. ``python -m pytest tests`` — the suite, including the freshness guards that
   catch a generated file nobody regenerated.
3. ``ruff check scripts tests`` — the Python linter, against the pinned rule
   set in ``ruff.toml``.
4. ``luacheck lua/`` — only if the binary is on PATH. It is absent from the
   default container, so this is reported as *skipped*, not failed.

**The lint stages must mirror CI exactly.** They did not, once: check.py ran
pytest and luacheck but not ruff, so ruff's CI job could sit red for a month
while this command said "everything green". If you add a job to
.github/workflows/tests.yml, add it here too.

A final check runs after the stages and is advisory: ``git status --short``.
A dirty tree after stage 1 means a generator rewrote a tracked file, and those
changes belong in the same commit as whatever caused them.

Usage:
    python scripts/check.py            # everything
    python scripts/check.py --fast     # skip regenerate/build, just test + lint
    python scripts/check.py --no-lint  # skip the linters even when installed
"""
import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import time

from utf8_console import child_env, use_utf8

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


def run_stage(name, argv, results, *, cwd=ROOT):
    """Run one stage, stream its output, and record (name, verdict, seconds)."""
    print(f"\n=== {name} ===", flush=True)
    started = time.monotonic()
    # A stage inherits this process's stdout. If that is a pipe or a file, a
    # child Python would encode to the legacy codepage and die on the first
    # non-ANSI character it printed — so hand every stage a UTF-8 environment.
    proc = subprocess.run(argv, cwd=cwd, env=child_env())
    elapsed = time.monotonic() - started
    verdict = PASS if proc.returncode == 0 else FAIL
    results.append((name, verdict, elapsed))
    return proc.returncode == 0


def skip_stage(name, why, results):
    print(f"\n=== {name} ===\nskipped: {why}", flush=True)
    results.append((name, SKIP, 0.0))


def have_module(name):
    """True if `python -m <name>` will work in this interpreter."""
    return importlib.util.find_spec(name) is not None


def git_status_short():
    """Tracked-file changes as a list of lines, or None if git is unavailable."""
    try:
        proc = subprocess.run(["git", "status", "--short"], cwd=ROOT,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def main():
    # First, before argparse: --help prints this module's docstring, which has
    # a → in it, and a redirected stdout defaults to the legacy codepage.
    # Called here rather than at import so importing this module (the tests do)
    # has no side effect on the caller's streams.
    use_utf8()
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fast", action="store_true",
                    help="skip regenerate+build; run only the tests and the linter")
    ap.add_argument("--no-lint", action="store_true",
                    help="skip luacheck even if it is installed")
    args = ap.parse_args()

    results = []
    started = time.monotonic()
    dirty_before = git_status_short()

    if args.fast:
        skip_stage("regenerate + build", "--fast", results)
    elif not run_stage("regenerate + build",
                       [sys.executable, os.path.join(ROOT, "scripts", "regenerate_all.py")],
                       results):
        return report(results, started, dirty_before)

    if not run_stage("pytest", [sys.executable, "-m", "pytest", "tests"], results):
        return report(results, started, dirty_before)

    # Both linters mirror a CI job. Keep them in step with
    # .github/workflows/tests.yml — see the module docstring.
    if args.no_lint:
        skip_stage("ruff", "--no-lint", results)
    elif not have_module("ruff"):
        skip_stage("ruff", "ruff is not installed (CI runs it; pip install ruff)", results)
    else:
        run_stage("ruff", [sys.executable, "-m", "ruff", "check", "scripts", "tests"],
                  results)

    luacheck = shutil.which("luacheck")
    if args.no_lint:
        skip_stage("luacheck", "--no-lint", results)
    elif not luacheck:
        skip_stage("luacheck",
                   "luacheck is not installed (CI runs it; install lua-check to run it here)",
                   results)
    else:
        run_stage("luacheck", [luacheck, "lua/"], results)

    return report(results, started, dirty_before)


def report(results, started, dirty_before):
    total = time.monotonic() - started
    print("\n" + "-" * 60)
    for name, verdict, elapsed in results:
        timing = f"{elapsed:5.1f}s" if verdict != SKIP else "     -"
        print(f"  {verdict:4}  {timing}  {name}")

    failed = [name for name, verdict, _ in results if verdict == FAIL]
    skipped = [name for name, verdict, _ in results if verdict == SKIP]

    # Advisory: a generator that rewrote a tracked file leaves work uncommitted.
    dirty_after = git_status_short()
    if dirty_before is not None and dirty_after is not None:
        new_changes = [ln for ln in dirty_after if ln not in dirty_before]
        if new_changes:
            print("\n  NOTE: regenerating rewrote tracked file(s) — commit these too:")
            for line in new_changes[:10]:
                print(f"        {line}")
            if len(new_changes) > 10:
                print(f"        … and {len(new_changes) - 10} more")

    print("-" * 60)
    if failed:
        print(f"FAILED ({', '.join(failed)}) in {total:.1f}s — fix the stage above and rerun.")
        return 1
    tail = f" ({', '.join(skipped)} skipped)" if skipped else ""
    print(f"OK — everything green in {total:.1f}s{tail}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
