---
description: Start a task the cheap way — route through TASKMAP, open only the routed files, state a plan before editing.
argument-hint: [what you want to change]
allowed-tools: Read, Grep, Glob, Bash(python scripts/sym.py:*), Bash(git log:*), Bash(git diff:*)
---

Task: **$ARGUMENTS**

Work the repo's navigation layer in this order, and stop as soon as you have
what you need. Do not read a file the route did not name.

1. **Route it.** Open [`TASKMAP.md`](../../TASKMAP.md) and find the row for this
   job. It maps job → the files to open. If nothing matches, fall back to the
   Documentation Map in [`agents.md`](../../agents.md).
2. **Resolve symbols, don't grep.** For a named function or constant, run
   `python scripts/sym.py NAME` — one call gives `file:line`, the signature and
   the call sites. Grep `SYMBOLS.md` only if that misses. Opening `SYMBOLS.md`
   itself costs ~17k tokens; it is a last resort.
3. **Check the TTS contract if the change touches the game surface.** Anything
   that spawns, moves, hides or draws an object, or touches XML UI, must be read
   against [`docs/tts-interface.md`](../../docs/tts-interface.md) and
   [`docs/tts-runtime.md`](../../docs/tts-runtime.md) *first* — they are lists of
   engine behaviours that have already caused bugs here.
4. **Check the local conventions.** The `CLAUDE.md` in the directory you are
   about to edit (`lua/`, `scripts/`, `tests/`, `content/`) carries the rules
   for that directory, including which generator owns any file you must not
   hand-edit.
5. **State the plan before editing.** List the files you will change and the
   test that will prove it. If the change would require remembering to update a
   second file, add the test that remembers instead — that is the house rule in
   [`tests/CLAUDE.md`](../../tests/CLAUDE.md).

Then implement, and finish with `python scripts/check.py`.
