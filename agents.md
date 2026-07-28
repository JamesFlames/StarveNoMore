# Starve No More — Agent Reference

## Project Overview


**Starve No More** is a cooperative survival board game built as a Tabletop Simulator (TTS) mod. Players control 5 teenagers (James, Coco, Rayman, Ellie, Luca) surviving 7 days in a Don't Starve-inspired suburban setting. The game uses a 3-stat economy (Health, Hunger, Sanity), a Doom track (0–30), 4 escalating phases, and a day/night cycle with Dawn card events.

> **This file is the index.** For fast navigation start higher up:
> [`CLAUDE.md`](CLAUDE.md) (start-here card) → [`TASKMAP.md`](TASKMAP.md)
> ("where do I change X?" → files) → `python scripts/sym.py NAME`
> ("where is function X?" → `file:line` + signature + call sites).
> Rules/design questions live in [`docs/design/`](docs/design/README.md); the
> build manifest is [`scripts/load_order.json`](scripts/load_order.json) and the
> generator map is [`scripts/generators.json`](scripts/generators.json).
> README.md is the human landing page.
>
> The exhaustive detail this file used to carry is now one topic per file under
> [`docs/agents/`](docs/agents/README.md) — see the jump table below. What stays
> here is what gets read *first*: the documentation map and the conventions.

## Topic reference

The deep material lives one topic per file under [`docs/agents/`](docs/agents/README.md),
so a task pays for the topic it needs instead of this whole file. Open the row,
not the index.

| Topic | Open when you need to |
|---|---|
| [Architecture](docs/agents/architecture.md) | understand how the save is assembled, or why load order is the dependency graph |
| [File Structure](docs/agents/file-structure.md) | find what lives where, or what a directory is for |
| [Game Design Quick Reference](docs/agents/design-reference.md) | check characters, locations, phases, the Doom track, the win condition |
| [Combat and Action Rules](docs/agents/combat-and-actions.md) | change combat maths or any player action |
| [Test Suite](docs/agents/test-suite.md) | know which module covers what, or run the release checklist |
| [Balance Simulation](docs/agents/balance-simulation.md) | re-run the Monte Carlo after a rules change |
| [UX Affordances](docs/agents/ux-affordances.md) | keep "the next legal action is always visible" true |
| [Audio](docs/agents/audio.md) | add or change a sound |
| [ComfyUI Workflow](docs/agents/comfyui.md) | regenerate card or board art |
| [Working With This Project](docs/agents/working-with-this-project.md) | make any change, day to day |
| [`gameState` schema map](docs/gamestate.md) | add, rename or trace a `gameState` field |

## Documentation Map


Quick index of every Markdown doc in the repo, so you know which to open for which task.

### Top-level

- [CLAUDE.md](CLAUDE.md) — the lean start-here card Claude Code auto-loads: project summary, build/test commands, the never-hand-edit list, and pointers to `TASKMAP.md` / `SYMBOLS.md` / this file. Per-directory `CLAUDE.md` stubs (`lua/`, `scripts/`, `tests/`, `content/`) carry the local conventions for scoped tasks.
- [TASKMAP.md](TASKMAP.md) — the "job → files to open" routing table. Start here for "where do I change X?"; use `SYMBOLS.md` for "where is function X?".
- [StarveNoMoreDesignConcept.md](StarveNoMoreDesignConcept.md) — **the canonical design doc**, now a thin index (Document Purpose + a Section → file jump table). The 20 numbered sections live one-topic-per-file under [docs/design/](docs/design/README.md): pitch/pillars, components/characters, locations/economy, decks, stats/turns, combat/crafting, week-arc/doom, victory/setup, TTS implementation, rationale/balancing. Open the specific `docs/design/*.md` for any rules or design question — prose cross-refs like "§6.7" map to files via the index table.
- [README.md](README.md) — short orientation for the GitHub landing page, dev quickstart, and the script-by-script build table.
- [CHANGELOG.md](CHANGELOG.md) — the rule-change history, one entry per design batch. The retired planning docs (improvements.md, design_batch1–4.md, frameworkimprovements.md, possible-design-improvements-to-snm.md) live on as these entries + git history. The 2026-07 design review in particular — 17 findings against `Archive/PrinciplesOfGoodBoardGames.md`, all shipped — is now the "Design review pass" entry below; read it for *why* a rule looks the way it does, never as the rule itself.
- [SYMBOLS.md](SYMBOLS.md) — AUTO-GENERATED index of every Lua global (function/constant → file:line) **and every XML UI id** (id → file:line + onClick handler). Regenerate with `scripts/generate_symbol_index.py`.
- [docs/tts-interface.md](docs/tts-interface.md) — how the mod talks to TTS: save format (Lua bundle + XML + ObjectStates), the Lua API surface rule (only call what exists), object-handle lifetime, the XML UI layer, and how to measure a running game. Read before calling an unfamiliar TTS API or debugging a runtime error.
- [docs/tts-runtime.md](docs/tts-runtime.md) — the TTS physical contract: surface heights (`TABLE_SURFACE_Y`), mesh extents vs. artwork, rotation conventions, hiding objects. Read before placing or rotating anything.
- [docs/achievements.md](docs/achievements.md) — the 24 achievements: where the roster lives (`content/achievements.csv` → `lua/achievement_data.lua`), where the unlock predicates live (`lua/achievement_rules.lua`), the four checkpoints that evaluate them, how the cross-game vault survives Restart, and why a TTS Workshop mod can't set a real Steam achievement (it ships `steam/achievements.json` for a future appid instead).
- [docs/comfyui-achievement-icons.md](docs/comfyui-achievement-icons.md) — the run book for regenerating the achievement art on a local ComfyUI, written to be handed to an agent verbatim: preflight checks, queue → sync → process → build → test, the thumbnail-legibility quality pass, and the failure table.
- [docs/debugging.md](docs/debugging.md) — live-session forensics: what TTS autosaves contain, `scripts/inspect_save.py` usage (incl. `--error N` to decode `<Global:N>` lines), the diagnosis flow.
- [docs/gamestate.md](docs/gamestate.md) — AUTO-GENERATED `gameState` schema map: every field with its declared default, the files that write it and the files that read it. Start here for "add a field" or "who clears X?". Regenerate with `scripts/generate_gamestate_map.py`; a test fails if any field is in neither `migrateGameState()` nor the reviewed transient list.
- [.claude/README.md](.claude/README.md) — the committed agent config: the `SessionStart` dependency hook, the `PostToolUse` symbol-index hook, the permission allowlist, and the `/verify` + `/newtask` commands.

> **No standing improvement plan.** All three programs — compartmentalise,
> structural, and the AI-workflow plan (`GoodForAiPlan.md`) — have shipped and
> are retired into [CHANGELOG.md](CHANGELOG.md) + git history. Read the
> "Cheaper, safer AI workflow" entry there before starting a "make the repo
> better for agents" task, so you do not re-derive what is already done or
> re-measure numbers that are already recorded.
- [PlayerRules.md](PlayerRules.md) / [PlayerRules.html](PlayerRules.html) — AUTO-GENERATED player rulebook (`scripts/generate_player_rules.py`), assembled from the same `content/` markdown as the in-game Notebook. Opens in any browser. **The same book is readable inside the game** as the Help panel's first tab, *Rulebook* (`rulebookText()` in `lua/ui_help_pages.lua`, paged); a cross-ref test keeps the two in step. (The in-TTS Player Rules **tablet** was removed 2026-07 — it defaulted to Google whenever the asset server wasn't running. The Rulebook tab is the replacement that needs no asset server.)
- [playtest/facilitator_script.md](playtest/facilitator_script.md) + [playtest/feedback_form.md](playtest/feedback_form.md) — the blind-playtest protocol and per-player form (batch 4 W4). Session data comes from the Week in Review panel's **Copy Session Log** button; logs collect in [playtest/sessions/](playtest/sessions/README.md) and aggregate via `scripts/analyze_sessions.py`.
- agents.md — this file.

### Archive/ — superseded reference material, kept for context

These files were the input/scaffolding for the design but are no longer
consulted by the build pipeline or by everyday work. Treat them as read-only
historical references; do not link to them from new documentation.

- `Archive/HowToCreateGamesInTabletopSimulator.md` — TTS API notes used to scaffold the Lua/XML.
- `Archive/PrinciplesOfGoodBoardGames.md`, `DontStarveVideoGamePrinciples.md` — design-theory sources.
- `Archive/compartmentaliseplan.md` — the completed "make the repo AI-friendly at small context" program (navigation layer, file splits, manifests). Every phase shipped; retired here in 2026-07. Its outcome is the current `CLAUDE.md`/`TASKMAP.md`/`SYMBOLS.md`/`docs/design/` navigation layer.

(Deleted 2026-07, all recoverable from git history: the commission brief
`StarveNoMoreRequirements.md`; the phased build checklist
`Checklist_For_TTS_Implementation.md` — the phase codes in code comments,
e.g. `F.3`, `E.8`, `J.10`, refer to its sections; and the `InterestingGames.md`
game tear-downs, whose section numbers the design doc still cites as
plain-text provenance notes.)

### content/ — in-game text and asset specs (loaded into the mod at build/runtime)

- [content/iconography.md](content/iconography.md) — full icon vocabulary (stats, resources, actions, keywords) and the 5-tier severity-dot ladder. Authoritative for icon meaning.
- [content/asset_manifest.md](content/asset_manifest.md) — every asset's ID, local path, and planned URL. Drives `lua/assets.lua`.
- [content/notebook/quickstart.md](content/notebook/quickstart.md) — 1-page summary shown in the in-game Notebook.
- [content/notebook/full_rules.md](content/notebook/full_rules.md) — abridged rulebook for the Notebook.
- [content/notebook/character_reference.md](content/notebook/character_reference.md) — perks/constraints for all 5 characters.
- [content/help/glossary.md](content/help/glossary.md) — every icon and keyword with one-line definitions; populates the Help-menu Glossary tab.
- [content/help/character_briefings.md](content/help/character_briefings.md) — per-character one-time popup text for the setup walkthrough; source of truth for `CHAR_BRIEFINGS` (`lua/character_briefings.lua`).
- [content/help/whatnow_hints.md](content/help/whatnow_hints.md) — context-aware hint strings keyed by sub-phase + character state, used by the "What now?" button.

## Key Conventions


- All object lookups use `getObjectsWithTag(tag)` — never hardcoded GUIDs
- `safecall(fn, label)` wraps all non-critical calls for graceful error handling
- `broadcastEvent(category, message)` for all player-facing messages (logs to dayLog)
- Game state is a single `gameState` table, persisted via `onSave`/`onLoad` with JSON encoding. Schema changes go through `SCHEMA_VERSION` + `migrateGameState()` (global.lua) — new fields get their defaults THERE, not `or {}` at read sites. `tests/test_save_fixture.py` loads a frozen mid-game save against the current bundle.
- **All gameplay randomness goes through `gameRoll(a, b)`** (helpers.lua) — never call `math.random` directly in game logic. Tests script dice by redefining `gameRoll`; cosmetic randomness (audio shuffle) stays on `math.random`.
- UI panels are shown/hidden via `UI.show(id)` / `UI.hide(id)` targeting XML element IDs
- The build script is the single source of truth for what gets packaged into the TTS save
- **If a change requires remembering to update a second file, add the test that remembers instead.** The suite already enforces: generated-file freshness, Dawn card↔handler pairing, `ongoingDawnEffects`↔Rules-panel labels, XML↔Lua handler contracts, sim↔lua constant mirrors (stats, Doom rates/thresholds, Cleanse, boss statlines, difficulty params), atlas-manifest↔CSV↔save grids, standee-slot constants (build_save↔helpers), `TOOLTIP_DATA`↔save tags, starting decks↔CSV, XML image names↔`CustomUIAssets`, and TTS-parseable colors everywhere. Extend that list before relying on memory.
- Symbol lookup: `SYMBOLS.md` maps every global function/constant to its file and line — one lookup instead of N greps.
