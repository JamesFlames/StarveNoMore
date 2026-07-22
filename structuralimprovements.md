# Structural Improvements

A survey of improvements to the **Starve No More** repo across structure, code,
data, flow, and documentation — and the running record of which have shipped.
Items are tagged with a rough **priority** (P1 = highest value / lowest risk,
P3 = nice-to-have) and their **status**.

The `compartmentaliseplan.md` "make the repo AI-friendly at small context"
program is complete (retired to `Archive/`). This document is the *next* layer:
the drift, coupling, and enforcement gaps that surface *after* that
restructuring.

**Status legend:** ✅ done · 🔎 reconsidered / won't-fix (rationale below) · ⬜ deferred.

---

## Shipped (2026-07)

### 1.1 ✅ Fix stale `ui_actionbar.lua` refs in `agents.md` (P1)
`lua/ui_actionbar.lua` was split into four files (`ui_actionbar_core`,
`_targets`, `_handlers`, `_display`) during the compartmentalise work, but
`agents.md` still named the old single file in four places (the file tree,
`verifyAndPayResources`, the action-targets section, `getPlayerResources`).
**Fixed:** each reference now points at the correct split file.

### 1.2 ✅ Test that prose file-name references resolve (P1)
`test_doc_links.py` guards markdown *links*, but nothing caught a doc naming a
`lua/*.lua` file **inline in prose** that no longer exists — which is exactly
how 1.1 slipped through. **Added** `tests/test_doc_file_refs.py`: it scans the
navigation-layer docs (agents.md / README / TASKMAP / CLAUDE + the per-dir
CLAUDE stubs) for `*.lua` tokens and fails if any names a file that doesn't
exist anywhere in the tree. The map is now self-healing.

### 3.1 ✅ One-command "regenerate everything" entrypoint (P1)
Correctly building meant running the *right* generator(s) for whatever source
you touched (six `generate_*` scripts), then `build_save.py`; `generators.json`
documented the mapping and `test_generated_freshness.py` only *caught*
staleness after the fact. **Added** `scripts/regenerate_all.py`: it derives its
plan from `generators.json` (so it can't drift), runs each generator in
dependency order, then `build_save.py`. Generators whose sources are absent
(e.g. `sounds/` on a clean clone) are skipped rather than erroring — a small
step toward 3.2. `tests/test_regenerate_all.py` pins that the plan covers every
manifest generator; TASKMAP.md and `scripts/CLAUDE.md` document it.

### 1.3 ✅ Retire the completed `compartmentaliseplan.md` (P2)
Every checkbox was `[x]`, yet it sat at repo root presenting a **stale
"Current pain points (measured 2026-07)" table** naming files that no longer
exist (`tests/test_lua_runtime.py`, `lua/ui_actionbar.lua` — both split). **Moved**
to `Archive/`, recorded in `CHANGELOG.md`, and de-linked from the live doc map
(now a non-linked mention in agents.md's Archive section, per the "no live
links into Archive" policy).

---

## Reconsidered on closer inspection

### 2.1 🔎 Combat constants are *already* single-sourced-by-test (P1 → resolved)
The original finding claimed "no test asserts the Lua ↔ sim combat constants
match." That was **wrong**: `tests/test_sim.py::test_source_constants_match_combat_lua`
already parses `SOURCE_MAX_HP` / `SOURCE_SPLIT_HP` from `lua/combat.lua` and
asserts they equal the sim's, and it runs in CI. This is the repo's deliberate
pattern (agents.md: "if a change requires remembering to update a second file,
add the test that remembers instead") — and it's applied to character stats,
Doom rates/thresholds, Cleanse, boss statlines, and difficulty params too.
Drift fails CI, not a playtest. **No change needed** — the coupling is
enforced, not latent.

### 2.2 🔎 The two save JSONs are not redundant churn (P2 → won't-fix)
`saves/` tracks `StarveNoMore.json` (minified deliverable, freshness-checked,
uploaded as the CI artifact hosts download) **and** `StarveNoMore.pretty.json`.
The original finding framed the pretty copy as "~2 MB churned every build."
That premise was wrong: `build_save.py` is deterministic, so the pretty file
only changes when the save's *content* changes — and when it does, its
pretty-printed diff is precisely the human-readable review aid the minified
file can't provide (build_save.py and README both describe it as the "copy for
diffing"). Removing it would delete an intentional aid to save 0 bytes of
noise-churn. **Left in place.**

### 3.3 🔎 CI guardrails are soft *by design* / can't be safely flipped here (P2 → deferred to maintainer)
Two of the four CI jobs never fail the build:
- **`filesize`** is deliberately warn-only — its own comment says "warn — never
  fail — so context-bloat regressions are visible in the PR without blocking."
  Hard-failing would immediately break CI on the intentionally grandfathered
  large files (`build_save.py` 1213, `simulate_balance.py` 969,
  `generate_assets.py` 795). Changing this is a policy call for the maintainer,
  not a safe unilateral edit.
- **`luacheck`** is `continue-on-error: true` with a comment saying to flip it
  off "once the first CI run has been reviewed." That flip can't be made safely
  from here — luacheck isn't installable in this environment, so there's no way
  to confirm the bundle is clean; flipping blind risks red CI on the next push.

**Recommendation (for a maintainer with CI access):** review one luacheck run,
then set `continue-on-error: false`; and if the budget should bite, make
`filesize` fail only for *newly added* files over budget (base-ref diff +
grandfather list) rather than the current all-or-nothing.

---

## Deferred (open, lower priority)

### 3.2 ⬜ Make the audio manifest regenerable from a clean clone (P2)
`sounds/` (~955 MB) is gitignored, but `lua/audio_manifest.lua` is generated
*from that tree*, so a fresh clone can't reproduce it. `regenerate_all.py` now
**skips** audio when `sounds/` is absent (build stays green), but the manifest
still isn't *regenerable* without the media. **Next step:** commit a small
`sounds/manifest.json` (paths + durations — the generator's actual input) so
the Lua manifest is rebuildable without the 955 MB, keeping media out-of-band.

### 4.1 ⬜ Lift static object templates out of `build_save.py` (P2)
Still the second-largest file and the single point every build flows through.
If touched again, the natural seam is to move the large static spawn-dict
*skeletons* into `scripts/templates/*.json` interpolated at build time. Not
urgent; do it opportunistically.

### 1.4 ⬜ Test that code→`§N` design cross-refs resolve (P3)
`test_cross_refs.py` covers many contracts but not the `§N.N` section refs that
`lua/`/`scripts/` comments cite. They're non-load-bearing provenance, so this
is low value — but a small test mapping each cited `§N` to a real
`docs/design/*.md` section would close the loop.

### 2.3 ⬜ Per-CSV column dictionary in `content/CLAUDE.md` (P3)
`test_csv_schema.py` enforces structure, but there's no "column → meaning →
consumed by" table per card CSV; an agent must reverse-engineer the generators
to learn, e.g., which column feeds `WEAPON_DICE`.

### 4.2 ⬜ Document the simulator's rule approximations (P3)
`simulate_balance.py` re-implements combat/economy logic the Lua owns; it
partly notes its approximations ("over-models trading", "shared pool"). A short
top-of-file block enumerating exactly which rules are approximated would tell a
rebalancer the model's blind spots.

### 4.3 ⬜ Map cross-file `gameState.*` ownership (P3)
One shared Lua global namespace, no `require`s: any file can mutate any
`gameState` field. A convention ("a `gameState.*` field is written only by its
owning module") plus a grep-based test would harden the most bug-prone surface.
Only worth it if state bugs recur.

### 5.1 ⬜ Move generated/retired docs out of repo root (P3)
With `compartmentaliseplan.md` retired, the remaining root cleanup is minor —
e.g. the generated `PlayerRules.html` could live under `docs/`.

### 5.2 ⬜ Cross-platform launcher entrypoint (P3)
`iwanttoplay.bat` / `serve_art.bat` are Windows-only; `scripts/iwanttoplay.py`
is the portable path. A one-line `.sh` or documenting the `python` entrypoint
as canonical would help non-Windows contributors.

---

## Shipped (2026-07, AI-workflow batch)

### 6.1 ✅ Live-session forensics tool (P1)
Debugging a user-reported session meant hand-writing JSON spelunking against
TTS autosaves every time. **Added** `scripts/inspect_save.py`: gameState
summary from any save (`--live` = newest autosave), object position dump,
embedded-in-tabletop check (`--band`), and `--error N` to decode an in-TTS
`<Global:N>` error line to `lua/<file>:<line>` with context. Documented in
`docs/debugging.md`.

### 6.2 ✅ Record the TTS physical/runtime contract (P1)
The table-surface height, the two rotation conventions, dead-handle
callbacks, the Button-styling reset, and the asset-cache staleness trap were
tribal knowledge rediscovered by forensics. **Written down** in
`docs/tts-runtime.md`; the height rule is enforced by
`test_build_output.py::test_no_objects_embedded_in_tabletop` and the
`DOOM_MARKER_Y` mirror test.

### 6.3 ✅ Cache purge in the deploy path (P1)
Stale cached art caused "the board doesn't match the objects" bugs after
every art regen. `iwanttoplay` now deletes this mod's `Mods/` cache entries
(`reposStarveNoMore` / `localhost8080` markers) on every deploy.

### 6.4 ✅ XML UI ids indexed in SYMBOLS.md (P1)
UI work starts from an element id ("where is `duskReadyBtn`?"), which took a
grep across `xml/` + `lua/`. `generate_symbol_index.py` now appends an
"XML UI ids" table (id → file:line, element, onClick handler) to SYMBOLS.md.

### 6.5 ✅ Split `day_loop.lua` at the turn-engine seam (P2)
723 lines (worst offender vs the ~500 budget) → `day_loop.lua` (492: Dawn
advance, Dusk, Night trigger) + `turns.lua` (239: beginDayPhase /
advanceToNextPlayer / endPlayerTurn / spendAction, dusk ready-check, idle
nudge).

## Newly deferred

### 6.6 ⬜ `CHAR_BRIEFINGS` duplicated against `content/help/character_briefings.md` (P2)
The briefing text is hardcoded in `lua/ui_setup.lua` while a same-purpose
markdown file sits in `content/help/` with no generator between them — the
only player-facing text NOT single-sourced. Either generate a
`lua/char_briefings.lua` from the markdown (the whatnow_hints pattern) or
delete the markdown and declare the Lua canonical.

### 6.7 ⬜ Oversized UI files (P3)
`xml/hud.xml` (~660) and `lua/ui_setup.lua` (~630) are the next split
candidates. XML splits are free (load_order.json just concatenates);
`ui_setup.lua`'s natural seam is the static text tables (briefings/card
styles) vs the walkthrough logic — best done together with 6.6.

---

## Status summary

| # | Item | Priority | Status |
|---|---|---|---|
| 1.1 | Fix stale `ui_actionbar.lua` refs in `agents.md` | P1 | ✅ done |
| 1.2 | Test that prose file-name refs resolve | P1 | ✅ done |
| 3.1 | One-command `regenerate_all` orchestrator | P1 | ✅ done |
| 1.3 | Retire completed `compartmentaliseplan.md` | P2 | ✅ done |
| 2.1 | Single-source combat constants | P1 | 🔎 already enforced by test |
| 2.2 | Two save JSONs | P2 | 🔎 intentional diff aid, kept |
| 3.3 | Enforce `filesize` / flip `luacheck` | P2 | 🔎 maintainer/CI decision |
| 3.2 | Audio manifest regenerable from clean clone | P2 | ⬜ deferred |
| 4.1 | Lift static templates out of `build_save.py` | P2 | ⬜ deferred |
| 1.4 | Test code→`§N` design cross-refs | P3 | ⬜ deferred |
| 2.3 | Per-CSV column dictionary | P3 | ⬜ deferred |
| 4.2 | Document simulator's rule approximations | P3 | ⬜ deferred |
| 4.3 | Map cross-file `gameState.*` ownership | P3 | ⬜ deferred |
| 5.1 | Move generated/retired docs out of root | P3 | ⬜ deferred |
| 5.2 | Cross-platform launcher entrypoint | P3 | ⬜ deferred |
| 6.1 | `inspect_save.py` live-session forensics | P1 | ✅ done |
| 6.2 | `docs/tts-runtime.md` physical/runtime contract | P1 | ✅ done |
| 6.3 | Cache purge in `iwanttoplay` | P1 | ✅ done |
| 6.4 | XML UI ids in SYMBOLS.md | P1 | ✅ done |
| 6.5 | Split `day_loop.lua` / add `turns.lua` | P2 | ✅ done |
| 6.6 | Single-source `CHAR_BRIEFINGS` | P2 | ⬜ deferred |
| 6.7 | Split `hud.xml` / `ui_setup.lua` | P3 | ⬜ deferred |
