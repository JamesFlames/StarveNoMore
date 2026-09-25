"""The command-line scripts must survive a redirected stdout.

Python only asks the *terminal* what encoding to use. Pipe or redirect stdout
and it falls back to the platform's legacy codepage — cp1252 on an English
Windows install — so the moment a script prints a character outside that
codepage it dies:

    UnicodeEncodeError: 'charmap' codec can't encode character '\\u2192'

`check.py` is documented as the command to finish every task with, and it did
exactly that on `regenerate_all.py`'s "  → <generator>" progress line: green
in a terminal, a traceback the instant anything captured the output — CI
writing to a file, an agent reading the result, `check.py > log.txt`. The
traceback names the generator, so it reads as a broken build rather than as a
print statement.

These tests force the legacy codepage on a child process and assert the
scripts print anyway. `PYTHONIOENCODING=cp1252` is the same lever Python uses
for a redirected stream, so it reproduces the failure on any platform — the
suite would have caught this on Linux too.
"""
import os
import subprocess
import sys

import pytest
from conftest import ROOT, SCRIPTS

sys.path.insert(0, SCRIPTS)
import utf8_console  # noqa: E402  (needs the sys.path line above)

# Outside cp1252, and the exact character that broke the build.
ARROW = "→"

# Entry points that print non-ASCII and are cheap to run: (argv, must_print).
# --list / --help do no work and touch no files, so this stays a fast test.
SAFE_INVOCATIONS = [
    pytest.param(["regenerate_all.py", "--list"], id="regenerate_all --list"),
    pytest.param(["regenerate_all.py", "--help"], id="regenerate_all --help"),
    pytest.param(["check.py", "--help"], id="check --help"),
    pytest.param(["sym.py", "--help"], id="sym --help"),
    pytest.param(["publish.py", "--help"], id="publish --help"),
    pytest.param(["sym.py", "-q", "beginNight"], id="sym beginNight"),
]


def _legacy_console_env():
    """An environment that mimics a redirected stdout on Windows: the child
    encodes its output with the legacy ANSI codepage."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "cp1252"
    return env


@pytest.mark.parametrize("argv", SAFE_INVOCATIONS)
def test_scripts_print_under_a_legacy_codepage(argv):
    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, argv[0])] + argv[1:],
        cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace",
        env=_legacy_console_env())

    assert "UnicodeEncodeError" not in proc.stderr, (
        f"scripts/{argv[0]} crashed encoding its own output when stdout is not "
        f"UTF-8 — the failure every redirect, pipe and CI log hits:\n{proc.stderr}")
    assert proc.returncode == 0, f"scripts/{argv[0]} exited {proc.returncode}:\n{proc.stderr}"


def test_child_env_lets_a_subprocess_print_the_character_that_broke_the_build():
    """check.py runs every stage as a subprocess, so fixing only its own
    streams would leave the stages broken. child_env() is what covers them —
    including stages added later, which is the point of it being an env var
    rather than a call each script has to remember."""
    code = f"print({ARROW!r})"

    without = subprocess.run([sys.executable, "-c", code], capture_output=True,
                             encoding="utf-8", errors="replace",
                             env=_legacy_console_env())
    assert without.returncode != 0 and "UnicodeEncodeError" in without.stderr, (
        "the legacy-codepage reproduction stopped reproducing — this test can "
        "no longer prove child_env() does anything")

    with_env = subprocess.run([sys.executable, "-c", code], capture_output=True,
                              encoding="utf-8", errors="replace",
                              env=utf8_console.child_env(_legacy_console_env()))
    assert with_env.returncode == 0, (
        f"child_env() did not fix a child's stdout encoding:\n{with_env.stderr}")
    assert with_env.stdout.strip() == ARROW


def test_use_utf8_leaves_an_unreconfigurable_stream_alone():
    """pytest's own capture replaces sys.stdout with an object that has no
    `reconfigure`. use_utf8() must no-op there rather than take the suite down
    with it — this test is running through exactly such a stream."""
    class Captured:
        pass

    utf8_console.use_utf8(Captured())  # must not raise
    utf8_console.use_utf8()            # whatever pytest has installed


def test_every_script_that_prints_non_ansi_calls_use_utf8():
    """The fix is per-entry-point, so a new script printing → would reopen the
    hole. Anything under scripts/ whose *output* has a non-cp1252 character
    must either call use_utf8() or be imported by something that does."""
    exempt = {"utf8_console.py"}  # defines it; prints nothing itself
    offenders = []
    for fn in sorted(os.listdir(SCRIPTS)):
        if not fn.endswith(".py") or fn in exempt:
            continue
        with open(os.path.join(SCRIPTS, fn), encoding="utf-8") as f:
            src = f.read()
        prints_non_ansi = any(
            ord(ch) > 127 and not _in_cp1252(ch)
            for line in src.splitlines()
            if "print(" in line or ".write(" in line
            for ch in line)
        if prints_non_ansi and "use_utf8()" not in src:
            offenders.append(fn)

    assert not offenders, (
        f"scripts printing characters the legacy Windows codepage lacks, "
        f"without calling use_utf8(): {offenders} — add "
        "`from utf8_console import use_utf8` and call it in main(), or keep "
        "the output ASCII.")


def _in_cp1252(ch):
    try:
        ch.encode("cp1252")
    except UnicodeEncodeError:
        return False
    return True
