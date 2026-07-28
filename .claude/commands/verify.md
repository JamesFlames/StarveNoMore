---
description: Run the full verification pipeline (regenerate → build → test → lint) and summarise any failures.
allowed-tools: Bash(python scripts/check.py:*), Bash(git status:*), Bash(git diff:*), Read, Grep, Glob
---

Run `python scripts/check.py` and report the result.

- **If it passes:** say so in one line, including the wall time and whether
  either linter (`ruff`, `luacheck`) ran or was skipped. Do not re-run anything
  else.
- **If it fails:** do *not* dump the whole output. For each failing stage give
  the smallest useful thing:
  - *Stale generated file* → name the file and the generator that owns it
    (`scripts/generators.json` is the map), then rerun that generator.
  - *Test failure* → the test id, the assertion, and the `file:line` of the
    production code at fault (use `SYMBOLS.md` or `python scripts/sym.py NAME`
    to resolve a symbol rather than grepping).
  - *Build failure* → the message and the manifest entry
    (`scripts/load_order.json`) it points at.
- Then run `git status --short`. A non-empty status after `check.py` means a
  generator rewrote a tracked file — those changes belong in the same commit.

Fix what you find, then run `python scripts/check.py` once more to confirm.
