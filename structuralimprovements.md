# Structural Improvements

A survey of improvements to the **Starve No More** repo across structure, code,
data, flow, and documentation. Findings are grouped by area and tagged with a
rough **priority** (P1 = highest value / lowest risk, P3 = nice-to-have). Each
item names the concrete file(s) involved so it can be picked up directly.

The `compartmentaliseplan.md` "make the repo AI-friendly at small context"
program is **fully complete** (every box checked). This document is the
*next* layer: the drift, coupling, and enforcement gaps that surface *after*
that restructuring, plus a few genuinely new ideas.

---

## 1. Documentation

### 1.1 Stale file references in `agents.md` (P1)
`lua/ui_actionbar.lua` was split into four files (`ui_actionbar_core`,
`_targets`, `_handlers`, `_display`) during Phase 2, but `agents.md` still
refers to the old single file in **four** places:

- line 122 — the File Structure tree lists `ui_actionbar.lua`
- line 221 — "`verifyAndPayResources` (ui_actionbar.lua)"
- line 440 — "`lua/ui_actionbar.lua` highlights world objects"
- line 453 — "`getPlayerResources(color)` in `lua/ui_actionbar.lua`"

These functions now live in `ui_actionbar_core.lua` / `ui_actionbar_targets.lua`.
**Fix:** update the four references; `getPlayerResources` / `verifyAndPayResources`
→ `ui_actionbar_core.lua`, target-spawn/highlight → `ui_actionbar_targets.lua`.

### 1.2 No test guards prose file-name references (P2)
`test_doc_links.py` checks link targets and the root-doc index, but nothing
catches a doc that names a `lua/*.lua` file **inline in prose** that no longer
exists (which is exactly how 1.1 slipped through). **Fix:** add a test that
greps the orientation docs (`agents.md`, `README.md`, `TASKMAP.md`,
`CLAUDE.md`) for `lua/[a-z_]+\.lua` tokens and asserts each resolves to a real
file. Cheap, and it makes the file-map self-healing.

### 1.3 `compartmentaliseplan.md` is done — retire it (P2)
Every checkbox is `[x]`. Per its own sibling convention (agents.md notes that
retired planning docs "live on as CHANGELOG entries + git history"), this file
should be folded into a `CHANGELOG.md` entry and removed, or moved to
`Archive/`. Leaving a 100%-complete plan at repo root:

- adds ~15 KB an agent may load "just in case",
- presents a **stale "Current pain points (measured 2026-07)" table** as if
  current: it lists `tests/test_lua_runtime.py` (1662) and
  `lua/ui_actionbar.lua` (1193), **both of which no longer exist** (split in
  Phases 2–3). A reader trusting that table is misled.

### 1.4 `docs/design/` split isn't spot-checked for section drift (P3)
The design doc was split into 20 one-topic files with `§N.N` prose cross-refs
kept as-is. There's a `test_cross_refs.py` — confirm it validates that every
`§N` cited in `lua/`/`scripts/` comments still maps to a real section in a
`docs/design/*.md` file. If it only checks doc-to-doc links, code-to-section
refs can rot silently.

---

## 2. Data — single source of truth

### 2.1 Combat constants are hand-mirrored between Lua and the simulator (P1)
The balance simulator re-declares gameplay constants that the runtime owns:

| Constant | Runtime (authoritative) | Mirror |
|---|---|---|
| `SOURCE_SPLIT_HP = 5` | `lua/combat.lua:84` | `scripts/simulate_balance.py:120` |
| Source max HP `= 8` | `lua/combat.lua:83` (`SOURCE_MAX_HP`) | sim comments / boss table |

`TASKMAP.md` even institutionalizes the hazard — "Change combat math →
`lua/combat.lua` … **mirror constants in `scripts/simulate_balance.py`**". A
mirror maintained by a checklist row drifts the first time someone forgets.
**Fix (pick one):**

- Emit the shared numbers to a tiny `content/combat_constants.json` (or
  `.csv`), have `lua/combat.lua` generated-or-checked against it (like the other
  `generate_*` outputs), and have the sim `import`/read the same file. Then the
  mirror is enforced by construction.
- Cheaper interim: a test that parses `SOURCE_SPLIT_HP` from both files and
  asserts equality, so drift fails CI instead of a playtest.

### 2.2 Two full save JSONs committed and rebuilt every time (P2)
`saves/` tracks both `StarveNoMore.json` (0.9 MB) **and**
`StarveNoMore.pretty.json` (1.2 MB) — the pretty file is a pretty-printed copy
of the *same content*. Every build churns ~2 MB of generated binary-ish JSON in
git history. **Fix:** gitignore `StarveNoMore.pretty.json` (regenerate on demand
for diffing), or keep only the pretty one under version control (human-diffable)
and gitignore the minified build artifact, treating it like other build output.
The CI already uploads the built save as an artifact, so hosts don't need it in
git at all.

### 2.3 CSV schema is validated but has no column dictionary (P3)
`test_csv_schema.py` enforces structure, but there's no single doc listing, per
CSV, what each column means and which generator consumes it. `content/CLAUDE.md`
is the place; a short "column → meaning → consumed by" table per card CSV would
save an agent from reverse-engineering `generate_market_data.py` to learn what
`WEAPON_DICE`'s source column is.

---

## 3. Flow — build & regeneration

### 3.1 No single "regenerate everything" entrypoint (P1)
Correctly building the save today requires running the *right* generator(s) for
whatever source you touched (six `generate_*` scripts), then `build_save.py`.
`generators.json` documents the mapping, and `test_generated_freshness.py`
*catches* staleness after the fact — but there's no command that just **does**
it. **Fix:** add `scripts/regenerate_all.py` (or a `Makefile`/`make build`)
that reads `generators.json`, runs every generator in dependency order, then
`build_save.py`. One command an agent or contributor can run blind, instead of
remembering the DAG. This also makes CI's "is everything fresh?" step a
one-liner.

### 3.2 Audio manifest can't be regenerated from a clean clone (P2)
`sounds/` (~955 MB) is gitignored, but `lua/audio_manifest.lua` is
*generated from that tree* by `generate_audio_manifest.py`. On a fresh clone the
sounds are absent, so:

- `generate_audio_manifest.py` can't reproduce the committed manifest, and
- `test_generated_freshness.py` would fail for audio if it ran the generator.

Confirm the freshness test skips audio when `sounds/` is missing (it presumably
does, since CI is green). Regardless, the *build is not reproducible* for the
audio layer from git alone. **Fix:** commit a small `sounds/manifest.json`
(paths + durations, the actual generator input) so the Lua manifest is
regenerable without the 955 MB of media; keep the media out-of-band.

### 3.3 CI guardrails are advisory-only (P2)
Two of the four CI jobs never fail the build:

- **`filesize`** emits `::warning` only — the ~500-line budget is unenforced, so
  `build_save.py` (1213), `simulate_balance.py` (969), `generate_assets.py`
  (795), `generate_card_atlases.py` (547) sit over budget with no signal beyond
  a warning annotation.
- **`luacheck`** is `continue-on-error: true`. Its own comment says "soft-fail
  until the first CI run has been reviewed — then flip continue-on-error off."
  That flip appears not to have happened, so Lua static analysis can regress
  freely.

**Fix:** review one luacheck run, then set `continue-on-error: false` (or add
an allowlist for accepted warnings). Consider making `filesize` fail for *new*
files over budget while grandfathering the known-large ones, so the budget
actually holds going forward.

---

## 4. Code

### 4.1 `build_save.py` (1213 lines) still holds embedded object templates (P2)
Phase 3 deliberately left the embedded object/JSON templates in place
(reasonable — they're parameterized assembly logic, not static config). But the
file is still the second-largest in the repo and the single point every build
flows through. If it's touched again, the natural seam is to lift the large
static object *skeletons* (bag/deck/board spawn dicts) into
`scripts/templates/*.json` loaded and interpolated at build time — keeping the
Python to the assembly logic. Not urgent; do it opportunistically.

### 4.2 `simulate_balance.py` (969 lines) is a monolith and a constants fork (P3)
Beyond 2.1's constant duplication, the sim re-implements combat/threat/economy
*logic* that the Lua owns. That's inherent to a fast Monte Carlo model, but the
divergence is a correctness risk: the sim can validate a ruleset the game
doesn't actually play. Worth a short doc block at the top enumerating **exactly
which rules are approximated** (it partly does — "over-models trading", "shared
pool") so a rebalancer knows the model's blind spots. Splitting it is low
priority per the plan; the *documented-divergence* note is the valuable part.

### 4.3 Global Lua namespace has no ownership map beyond `SYMBOLS.md` (P3)
Every `lua/*.lua` shares one global namespace with no `require`s, so any file
can read/write any global. `SYMBOLS.md` maps *definitions*, but there's no map
of *cross-file writes* (e.g. who mutates `gameState.bossHP`). For a co-op state
machine this is where subtle bugs live. A lightweight convention — "a
`gameState.*` field is written only by its owning module, listed in a comment
header" — plus a grep-based test would harden the most bug-prone surface. Lower
priority; only worth it if state bugs recur.

---

## 5. Repository structure

### 5.1 Root directory is crowded with docs (P3)
Repo root carries 11 top-level Markdown/HTML files (`README`, `CLAUDE`,
`agents`, `TASKMAP`, `SYMBOLS`, `CHANGELOG`, `PlayerRules.md`/`.html`,
`StarveNoMoreDesignConcept`, `compartmentaliseplan`, plus `.bat`). The
navigation layer (CLAUDE→TASKMAP→SYMBOLS→agents) is deliberate and should stay
at root, but the *generated* artifacts (`PlayerRules.html`, and per 1.3
`compartmentaliseplan.md`) could move to `docs/` to keep the root to the
"start-here" set. Minor.

### 5.2 `iwanttoplay.bat` / `serve_art.bat` are Windows-only (P3)
Two `.bat` launchers with no cross-platform equivalent. `scripts/iwanttoplay.py`
exists and is presumably portable — a one-line `iwanttoplay.sh` (or documenting
`python scripts/iwanttoplay.py` as the canonical entrypoint) would help non-
Windows contributors. Minor.

---

## Priority summary

| # | Item | Priority | Type |
|---|---|---|---|
| 1.1 | Fix stale `ui_actionbar.lua` refs in `agents.md` | **P1** | docs |
| 2.1 | Single-source combat constants (Lua ↔ sim) | **P1** | data |
| 3.1 | Add `regenerate_all` orchestrator / Makefile | **P1** | flow |
| 1.2 | Test that prose file-name refs resolve | P2 | docs |
| 1.3 | Retire completed `compartmentaliseplan.md` | P2 | docs |
| 2.2 | Stop committing/churning both save JSONs | P2 | data |
| 3.2 | Make audio manifest regenerable from a clean clone | P2 | flow |
| 3.3 | Enforce `filesize` / flip `luacheck` off soft-fail | P2 | flow |
| 4.1 | Lift static object templates out of `build_save.py` | P2 | code |
| 1.4 | Verify code→`§N` design cross-refs are tested | P3 | docs |
| 2.3 | Per-CSV column dictionary in `content/CLAUDE.md` | P3 | data |
| 4.2 | Document the simulator's rule approximations | P3 | code |
| 4.3 | Map cross-file `gameState.*` ownership | P3 | code |
| 5.1 | Move generated/retired docs out of repo root | P3 | structure |
| 5.2 | Cross-platform launcher entrypoint | P3 | structure |
