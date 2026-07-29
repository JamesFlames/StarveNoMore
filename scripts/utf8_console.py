#!/usr/bin/env python3
"""UTF-8 stdout for the command-line scripts, however they are invoked.

Python on Windows picks the encoding for `sys.stdout` from the terminal only
when stdout *is* a terminal. Redirect or pipe it — `python scripts/check.py >
log.txt`, `python scripts/sym.py Foo | head`, an agent capturing the output,
CI writing to a file — and it falls back to the legacy ANSI codepage (cp1252
on an English install). The first character outside that codepage then raises:

    UnicodeEncodeError: 'charmap' codec can't encode character '\\u2192'
    in position 2: character maps to <undefined>

`check.py` is documented as *the* command to finish every task with, and it
died on `regenerate_all.py`'s "  → <generator>" progress line the moment
anything captured its output. The failure looks like a broken build, not like
a print statement, because the traceback is the generator's.

Two halves, because a stage is a subprocess:

  * `use_utf8()` fixes this process's own streams;
  * `child_env()` makes any child Python do the same, so a stage added later
    is covered without anyone remembering this file exists.

Deliberately *not* setting PYTHONUTF8 (UTF-8 mode) in `child_env`: that also
changes the default encoding of `open()`, which would mask a missing
`encoding=` in the tests it runs rather than fix it. This is about the
console, and only the console.
"""
import os
import sys

__all__ = ["use_utf8", "child_env"]


def use_utf8(*streams):
    """Re-encode this process's stdout/stderr as UTF-8, in place.

    Safe to call more than once, and on a stream that cannot be reconfigured
    (pytest's capture replaces sys.stdout with an object that has no
    `reconfigure`) — such a stream is left alone rather than erroring.
    """
    for stream in streams or (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            # Detached or already-closed stream; printing is the caller's
            # problem at that point, not an encoding question.
            pass


def child_env(env=None):
    """`env` (default `os.environ`) plus the variable that makes a child
    Python write UTF-8 to its own stdout/stderr.

    Pair it with `encoding="utf-8"` on any captured `subprocess.run`: the
    child then emits UTF-8 and the parent decodes UTF-8, instead of both ends
    guessing a locale codec and disagreeing.
    """
    out = dict(os.environ if env is None else env)
    out["PYTHONIOENCODING"] = "utf-8"
    return out
