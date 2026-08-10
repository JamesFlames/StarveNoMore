# `.claude/` — committed agent config

This directory is **tracked in git** (only `settings.local.json` is ignored).
Everything an agent needs to learn about *how to work here* lives here instead
of dying with the container.

| File | What it does |
|---|---|
| [`settings.json`](settings.json) | Hooks + the permission allowlist for the routine loop. |
| [`hooks/session-start.sh`](hooks/session-start.sh) | Installs `pytest lupa Pillow ruff` so the suite runs on the first try. Remote containers only. |
| [`hooks/refresh-symbol-index.sh`](hooks/refresh-symbol-index.sh) | After any `lua/` edit, reruns `generate_symbol_index.py` so `SYMBOLS.md` never goes stale. |
| [`commands/verify.md`](commands/verify.md) | `/verify` — run `scripts/check.py`, summarise failures. |
| [`commands/newtask.md`](commands/newtask.md) | `/newtask` — route through `TASKMAP.md`, open only the routed files, state a plan first. |

## Conventions

- **Personal overrides** go in `settings.local.json` (gitignored) — never edit
  `settings.json` for a machine-specific path or a one-off permission.
- **Running anything *in* the project needs no approval.** Every script under
  `scripts/` (by wildcard, so a new generator is covered the day it is added),
  the test suite, the linters and `./iwanttoplay`, in either shell. This
  replaced a per-script list that had to be extended each time a generator
  landed — and silently prompted until someone did.
- **The boundary is the repo, not the command.** Still not allowed: `git push`,
  `rm`, inline code (`python -c`), and anything that reaches outside the
  checkout. Add a permission when you approve the same command twice, but keep
  it on the running-a-project-file side of that line.
- **Hooks must be idempotent and silent on the happy path.** Both current hooks
  no-op when they have nothing to do.
- The hooks are a *fast path*, not a guarantee — the equivalent checks are all
  enforced by `tests/` as well, because a hook can be disabled and CI cannot.
