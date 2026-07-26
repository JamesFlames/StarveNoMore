# Starve No More — Agent Reference

## Project Overview

**Starve No More** is a cooperative survival board game built as a Tabletop Simulator (TTS) mod. Players control 5 teenagers (James, Coco, Rayman, Ellie, Luca) surviving 7 days in a Don't Starve-inspired suburban setting. The game uses a 3-stat economy (Health, Hunger, Sanity), a Doom track (0–30), 4 escalating phases, and a day/night cycle with Dawn card events.

> **This file is the deep reference** (architecture, conventions, pipelines,
> per-file map). For fast navigation start higher up:
> [`CLAUDE.md`](CLAUDE.md) (start-here card) → [`TASKMAP.md`](TASKMAP.md)
> ("where do I change X?" → files) → [`SYMBOLS.md`](SYMBOLS.md) ("where is
> function X?" → `file:line`). Rules/design questions live in
> [`docs/design/`](docs/design/README.md); the build manifest is
> [`scripts/load_order.json`](scripts/load_order.json) and the generator map is
> [`scripts/generators.json`](scripts/generators.json). README.md is the human
> landing page; this file owns the exhaustive detail.

## Documentation Map

Quick index of every Markdown doc in the repo, so you know which to open for which task.

### Top-level

- [CLAUDE.md](CLAUDE.md) — the lean start-here card Claude Code auto-loads: project summary, build/test commands, the never-hand-edit list, and pointers to `TASKMAP.md` / `SYMBOLS.md` / this file. Per-directory `CLAUDE.md` stubs (`lua/`, `scripts/`, `tests/`, `content/`) carry the local conventions for scoped tasks.
- [TASKMAP.md](TASKMAP.md) — the "job → files to open" routing table. Start here for "where do I change X?"; use `SYMBOLS.md` for "where is function X?".
- [StarveNoMoreDesignConcept.md](StarveNoMoreDesignConcept.md) — **the canonical design doc**, now a thin index (Document Purpose + a Section → file jump table). The 20 numbered sections live one-topic-per-file under [docs/design/](docs/design/README.md): pitch/pillars, components/characters, locations/economy, decks, stats/turns, combat/crafting, week-arc/doom, victory/setup, TTS implementation, rationale/balancing. Open the specific `docs/design/*.md` for any rules or design question — prose cross-refs like "§6.7" map to files via the index table.
- [README.md](README.md) — short orientation for the GitHub landing page, dev quickstart, and the script-by-script build table.
- [CHANGELOG.md](CHANGELOG.md) — the rule-change history, one entry per design batch. The retired planning docs (improvements.md, design_batch1–4.md, frameworkimprovements.md) live on as these entries + git history.
- [SYMBOLS.md](SYMBOLS.md) — AUTO-GENERATED index of every Lua global (function/constant → file:line) **and every XML UI id** (id → file:line + onClick handler). Regenerate with `scripts/generate_symbol_index.py`.
- [docs/tts-interface.md](docs/tts-interface.md) — how the mod talks to TTS: save format (Lua bundle + XML + ObjectStates), the Lua API surface rule (only call what exists), object-handle lifetime, the XML UI layer, and how to measure a running game. Read before calling an unfamiliar TTS API or debugging a runtime error.
- [docs/tts-runtime.md](docs/tts-runtime.md) — the TTS physical contract: surface heights (`TABLE_SURFACE_Y`), mesh extents vs. artwork, rotation conventions, hiding objects. Read before placing or rotating anything.
- [docs/debugging.md](docs/debugging.md) — live-session forensics: what TTS autosaves contain, `scripts/inspect_save.py` usage (incl. `--error N` to decode `<Global:N>` lines), the diagnosis flow.
- [structuralimprovements.md](structuralimprovements.md) — standing punch-list of proposed structure/code/data/flow/doc improvements (the layer *after* the completed `compartmentaliseplan.md`), each tagged with a priority and the files it touches. A working doc, not a design doc.
- [PlayerRules.md](PlayerRules.md) / [PlayerRules.html](PlayerRules.html) — AUTO-GENERATED player rulebook (`scripts/generate_player_rules.py`), assembled from the same `content/` markdown as the in-game Notebook. Opens in any browser. (The in-TTS Player Rules **tablet** was removed 2026-07 — it defaulted to Google whenever the asset server wasn't running, and duplicated the Notebook/Help/Quick-Start content.)
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
- [content/help/character_briefings.md](content/help/character_briefings.md) — per-character one-time popup text for the setup walkthrough.
- [content/help/whatnow_hints.md](content/help/whatnow_hints.md) — context-aware hint strings keyed by sub-phase + character state, used by the "What now?" button.

## Architecture

### Runtime
- **Engine**: Tabletop Simulator (MoonSharp Lua 5.2, XML UI, JSON saves)
- **Object lookup**: Tag-based (never GUID)
- **Save format**: Single JSON file with embedded Lua + XML

### Build Pipeline
- `scripts/build_save.py` — Concatenates the Lua files in `LUA_LOAD_ORDER` + the `XML_LOAD_ORDER` files under `xml/` (hud / setup / dialogs) into the TTS save JSON. **Both load orders live in [`scripts/load_order.json`](scripts/load_order.json)** (`lua[]` + `xml[]`), a small machine-readable manifest build_save.py, `conftest.py`, and `generate_symbol_index.py` all read — so the build order is a diffable data file, not buried in the script. Deck `NumWidth/NumHeight` come from `art/decks/atlas_manifest.json` (written by the atlas generator; a card-count mismatch is a hard stop — rerun the atlas generator). `--publish BASE_URL [--out path]` writes a separate shareable save with every `file:///`/`localhost` asset URL rewritten to the hosted base (refuses to write if any local URL survives).
- Six of the Lua files in that list are **auto-generated** and should never be edited by hand:
  - `lua/audio_manifest.lua`  — built by `scripts/generate_audio_manifest.py` from the `sounds/` tree
  - `lua/whatnow_hints.lua`   — built by `scripts/generate_whatnow_hints.py` from `content/help/whatnow_hints.md`
  - `lua/market_data.lua`     — built by `scripts/generate_market_data.py` from `content/cards_market.csv` + `cards_starting.csv` (`MARKET_COSTS` for affordability + `WEAPON_DICE` parsed from "+N Attack die" effect text)
  - `lua/threat_types.lua`    — built by `scripts/generate_threat_types.py` from `content/cards_threats.csv` (`THREAT_TYPE_BY_NAME` for the Night Sounds peek + `SEALED_REWARDS` from the `pry_reward` column)
  - `lua/recipe_data.lua`     — built by `scripts/generate_recipe_data.py` from `content/cards_recipes.csv` (`RECIPE_DATA` from the structured `script` column)
  - `lua/notebook_data.lua`   — built by `scripts/generate_notebook.py` from `content/notebook/*.md` + `content/help/glossary.md` (the in-game Notebook tabs and Help-panel text; build_save.py reuses its `md_to_text` for the Quick Start notecard)
- Two repo-root files are also generated: `SYMBOLS.md` + `.luacheckrc` — built by `scripts/generate_symbol_index.py` from `lua/` (rerun after any Lua change).
- Run those generators after editing the corresponding source, then `python scripts/build_save.py`. All generators are idempotent and order-independent; `tests/test_generated_freshness.py` fails if any output is stale.

### Asset Pipeline
- `scripts/generate_card_atlases.py` — Composites card faces from per-card illustrations + text panel; writes deck atlases to `art/decks/*.png`
- `scripts/generate_assets.py` — Renders tokens, boards, player boards, legends via Pillow
- `scripts/generate_cover.py` — Renders `saves/StarveNoMore.png` (Coco's front standee on a night-suburb backdrop). A same-basename PNG beside the save is the cover art TTS shows in its Save & Load browser; `iwanttoplay` copies it with the save. Deterministic; rerun only when the cover should change.
- `scripts/generate_comfyui_assets.py` — Queues board + per-card illustration prompts to local ComfyUI (Flux Dev). Character standees are intentionally excluded (hand-drawn).
- `scripts/sync_comfyui_output.py` — Copies ComfyUI's `output/snm_*_00001_.png` into the matching `art/<subdir>/<base>.png` (idempotent)
- `scripts/simulate_balance.py` — Monte Carlo balance probe (policies × rulesets; `--rules old` for pre-fix comparison, `--trace` for a day-by-day log). Standalone; not part of the build.
- Card data CSVs: `content/cards_phase1.csv` … `cards_phase4.csv`, plus `cards_market.csv`, `cards_recipes.csv`, `cards_threats.csv`, `cards_visitors.csv`, `cards_trophies.csv`, `cards_scenarios.csv`, and `locations.csv`, `resources.csv`, `tooltips.csv`
- Output images: `art/decks/`, `art/decks/illustrations/`, `art/tokens/`, `art/icons/`, `art/board/`, `art/characters/`, `art/legend/`, `art/tiles/`, `art/bosses/`, `art/ui/`

## File Structure

```
StarveNoMore/
├── lua/
│   ├── helpers.lua             # Utility functions (safecall, tag-based getters)
│   ├── global.lua              # gameState, lifecycle, onLoad/onSave, dailyAlerts
│   ├── audio_manifest.lua      # AUTO-GENERATED — track URLs + durations (AUDIO table)
│   ├── audio.lua               # Audio.startDayAmbience / playBossLoop / playChime / playWalk / playMeet / playTradeChat / playDeath / playSFX
│   ├── whatnow_hints.lua       # AUTO-GENERATED — WHATNOW_HINTS table from markdown
│   ├── market_data.lua         # AUTO-GENERATED — MARKET_COSTS + WEAPON_DICE from cards_market.csv + cards_starting.csv
│   ├── threat_types.lua        # AUTO-GENERATED — THREAT_TYPE_BY_NAME + SEALED_REWARDS from cards_threats.csv
│   ├── recipe_data.lua         # AUTO-GENERATED — RECIPE_DATA from cards_recipes.csv (script column)
│   ├── notebook_data.lua       # AUTO-GENERATED — Notebook/Help text from content/notebook/*.md + glossary.md
│   ├── setup.lua               # Bare gameplay setup (deals/shuffles/places)
│   ├── day_loop.lua            # Day lifecycle: Dawn advance (Doom/fester/reveal), Dusk, Night trigger
│   ├── turns.lua               # Turn engine: beginDayPhase, advanceToNextPlayer, endPlayerTurn, spendAction, dusk ready-check, idle nudge
│   ├── effects/
│   │   ├── dawn_effects.lua           # Core: DAWN_EFFECTS table + shared helpers + boss standee placement
│   │   ├── dawn_effects_phase1..4.lua # Per-phase Dawn card effects (add to DAWN_EFFECTS)
│   │   └── dawn_effects_dispatch.lua  # Anti-stacking cards + DAWN_MANUAL_STEPS + dispatchDawnEffect
│   ├── combat.lua              # Dice roll + boss/Source HP lifecycle + rewards/trophies (SOURCE_MAX_HP etc.)
│   ├── combat_resolve.lua      # Fight resolution flow (beginCombat..finishCombat, Charlie); calls Audio.stopBossLoop on defeat
│   ├── crafting.lua            # Market craft + Crockpot cook handlers
│   ├── night.lua               # Night-phase resolver (threat draw, Charlie, sleep)
│   ├── tick_victory.lua        # Tick decay, victory/defeat, Down state + revival hint
│   ├── actions.lua             # Player actions core: undo/snapshot, move, dusk-move, gather, rest
│   ├── actions_combat.lua      # Combat verbs: threat/boss statlines, fight, flee
│   ├── actions_social.lua      # Trade, energy drink, eat-raw, pass, barricade, defend, peek, rally, pry, stabilize
│   ├── treeguard.lua           # Phase 2.5 mini-boss (wakes Dusk D4; fight/appease/defeat)
│   ├── signatures.lua          # Signature Moves (§6.7) — once-per-game per-character actions + button/dialog UX
│   ├── telemetry.lua           # Session log (batch 4 W0): chronicle setup/turns/beats, exportSessionLog, Copy Session Log
│   ├── ui_banner.lua           # Phase Banner + recommendNext + CTA pulse + active-player indicator
│   ├── ui_actionbar_core.lua      # Resource helpers (getPlayerResources, verifyAndPayResources, canAfford) + Move adjacency + highlight duration
│   ├── ui_actionbar_targets.lua   # Target-button plumbing + move/craft/cook/fight target spawns, click handlers, highlights
│   ├── ui_actionbar_handlers.lua  # onActX action-bar handlers, Press-the-Attack panel, trade/peek/rally/undo/dusk handlers
│   ├── ui_actionbar_display.lua   # Validate, action-bar refresh + cubes, per-button enable/reasons, stat display, action tooltips
│   ├── ui_controls.lua         # Host controls (contextual — only valid buttons show), confirm dialogs, tooltips
│   ├── ui_setup.lua            # Guided setup walkthrough (path → variants → characters → briefing) + welcome
│   ├── ui_help.lua             # Help panel tabs + What-now dispatch (fills the whatNowPanel)
│   ├── ui_msglog.lua           # Persistent Message Log panel (fed by broadcastEvent)
│   ├── ui_rules.lua            # "Rules in effect" panel + day-cycle strip
│   ├── ui_mood.lua             # Phase lighting presets, safety-net confirms, camera nudges
│   ├── audit.lua               # auditTooltips / auditHintCoverage / auditFirstLoad
│   ├── selftest.lua            # runSelfTest() — scripted in-TTS smoke test (see Test Suite)
│   └── assets.lua              # ASSETS table — image URL constants (LOCAL_DEV switch)
├── xml/
│   ├── hud.xml                 # Persistent HUD: banner, cycle strip, host controls, action bar, stats, roster
│   ├── setup.xml               # Guided setup walkthrough panels + character briefing
│   ├── dialogs.xml             # Modal dialogs: confirm / summary / week review / help / trade / combat / dusk
│   └── msglog.xml              # Message Log panel + per-player What-now panel
├── content/
│   ├── cards_phase1.csv ... cards_phase4.csv   # Dawn cards per phase
│   ├── cards_market.csv        # Source of truth for MARKET_COSTS
│   ├── cards_recipes.csv
│   ├── cards_threats.csv
│   ├── cards_visitors.csv
│   ├── cards_trophies.csv
│   ├── cards_scenarios.csv     # 8 optional week-long Scenarios (design §17.3) — applied digitally by setup.lua; no physical deck yet
│   ├── cards_starting.csv      # Per-character starting items (S_*) — dealt to hands by dealStartingHands at setup
│   ├── locations.csv
│   ├── resources.csv
│   ├── tooltips.csv
│   ├── iconography.md
│   ├── asset_manifest.md
│   ├── notebook/               # Quickstart + Full rules + Character reference
│   └── help/
│       ├── glossary.md         # Icon and keyword glossary (Help-menu tab)
│       ├── character_briefings.md  # Per-character one-time setup popup text
│       └── whatnow_hints.md    # Source of truth for WHATNOW_HINTS
├── art/
│   ├── board/  tiles/  characters/  bosses/  decks/  icons/  ui/  legend/  tokens/
│   └── decks/illustrations/    # Per-card art from ComfyUI (sync target)
├── sounds/
│   ├── ambient/{suburban,varied}/   # Day-music tracks
│   ├── creatures/{bearger,deerclops,eye_of_terror,treeguard}/   # Boss roar libraries
│   └── sfx/tick_chime.wav      # Synthesized two-note bell
├── playtest/                   # Blind-playtest protocol (batch 4 W4): facilitator_script.md + feedback_form.md
│   └── sessions/               # Committed Copy-Session-Log exports; aggregate with scripts/analyze_sessions.py
├── saves/                      # Built TTS save JSON (StarveNoMore.json + .pretty.json)
│   └── fixtures/               # Frozen mid-game save (midgame_v1.json) for the save-compat test
├── scripts/                    # Build + asset/data generation (Python) + simulate_balance.py (Monte Carlo balance probe)
└── Archive/                    # Superseded reference docs (frozen — no live links)
```

## Game Design Quick Reference

### Characters
| Name   | Role             | Health | Hunger | Sanity | Home           |
|--------|------------------|--------|--------|--------|----------------|
| James  | The Gamer        | 8      | 6      | 10     | JamesHouse     |
| Coco   | The Angel        | 6      | 8      | 12     | (none)         |
| Rayman | Basketball Player| 12     | 10     | 6      | RaymanHouse    |
| Ellie  | The Cook         | 8      | 10     | 8      | EllieLucaHouse |
| Luca   | The Orator       | 7      | 8      | 10     | EllieLucaHouse |

Each character's starting items (`content/cards_starting.csv`, `S_*`) are a
small deck in the save, dealt into that player's hand by `dealStartingHands`
(setup.lua) at setup; James additionally gets 2 Energy Drink **tokens** by his
player board (his Wired economy runs on tokens, not cards). Weapon items with
"+N Attack die" text are counted automatically in combat via `WEAPON_DICE`
(best single carried weapon; no stacking).

### Locations
JamesHouse, RaymanHouse, EllieLucaHouse, BasketballCourt, BadmintonCourt

### Phases
1. **Dusk of Week** (Days 1–2) — Calm intro
2. **Strange Days** (Days 3–4) — Escalation, Deerclops arrives
2.5. **The Grove Wakes** (Dusk of Day 4, scheduled) — Treeguard mini-boss lairs at a random sport court: blocks Gather there, festers Doom; fight it (HP 5/Atk 2, drops 3 Wood) or appease it (2 Wood at its tile). `lua/treeguard.lua`
3. **Long Nights** (Day 5) — Eye of Terror arrives
4. **Final Hours** (Days 6–7) — The Source arrives, endgame. The Source's HP is script-tracked (`gameState.bossHP.source`); at ≤5 HP it splits into 2 Terror Beaks (once, `gameState.sourceSplit`). Day 7's Dawn is the fixed, scripted **Last Dawn** (no Phase-4 draw).

### Day Cycle
Dawn (Doom advance + Moonlit Salvage + Dawn card) → Day (player turns, 3 actions each) → Dusk (optional 1-tile scramble, 1 Hunger, then host clicks Resolve Night) → Night → Tick (stat decay)

### Doom Track
0–30. Advances each Dawn by phase rate **+1 per Threat/Boss still on the map (fester, cap +3)**, and **+1 whenever a character goes Down**. Thresholds at 10 (night threats +1), 15 (Scarcity: crafts +1 resource), 20 (−1 Sanity at Tick), 25 (bosses can appear in any phase + **Nothing Left to Lose**: +1 attack die for everyone, Rest heals +1 Health anywhere), 30 = defeat. Cleanse action (1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink) reduces Doom by 2.

### Night rules of note
- **Charlie attack** (no light source): 2 Sanity + 1 Health, +1 to each per consecutive dark night (`char.charlieStreak`, reset at Tick on a lit night). Coco immune.
- **Crowded floor**: a house sleeps 2 comfortably; sleepers beyond the second get no sleep regen (owners get beds first, then lowest-Sanity guests).
- **Moonlit Salvage**: survive a night at a sport court → gather 2 resources from that court's bag at Dawn.
- Ghosts do **not** drain ally Sanity (cut — positive feedback loop).

### Combat / action rules of note
- **Fight is click-to-complete** (2026-07): the Fight button spawns FIGHT (solo) and TOGETHER (group: every standing ally at the tile with Hunger ≥ 3) buttons on every fightable thing at the tile — threat cards with `hp > 0` (statlines from the generated `THREAT_STATS`, threat_types.lua) and boss standees (`BOSS_BASE_STATS`, actions.lua; Treeguard via `TREEGUARD_STATS`). `doFightTarget` → `beginCombat`. Threat-card chip damage persists in `gameState.threatDamage[guid]`; every boss's HP is script-tracked (`gameState.bossHP` / `gameState.treeguard.hp`), seeded by the arrival effects. A defeated card discards itself beside the Threat deck; a defeated boss's standee returns to the Boss Pool.
- **Boss arrivals place their own standee** from the Boss Pool (Deerclops → Basketball Court, Eye → random house recorded in `gameState.eyeLocation` + 1 extra Threat drawn there each Dawn, Source → Ellie & Luca's). On the map they fester and gate victory; in the bag they do neither.
- **Character perks are scripted** (§6, 2026-07): James — Gaming Reflexes (auto-reroll of the lowest failed die, once per turn on his turn, `maybeJamesReroll`) + Pattern Recognition (`doPeek`, Peek button, once/day, private). Coco — Calming Presence (−1 Sanity loss for tile-mates at Tick) + Wanderer's Gift (+1 Sanity on Move). Rayman — Court Master (+1 die at Basketball Court) + Backboard Block (`doDefend` sets `raymanDefending`; counters redirect to him until his next turn). Ellie — Particular Eater (doEatRaw refuses). Luca — Rally (`doRally`, Rally button: nearby ally +1 action, once per turn), Calm Words (auto d6 in `allPlayersLose` on group Sanity losses — 4+ spares his tile), Needs an Audience (no solo Sanity regen: Rest converts to Hunger, sleep/storytelling skip it; `charHasCompany`, helpers.lua).
- **Fumble**: a natural 1 deals 1 self-damage only if the roll contains **zero hits**, max 1 per roll (solo and group).
- **Flee**: always legal (even Hunger < 3): move 1 tile away, pay 1 Sanity; the threat stays and festers (`doFlee`).
- **Rayman's Loud**: if he moved at all today (`gameState.raymanMovedToday`, incl. Dusk scramble), his Night location draws +1 Threat (once).
- **The Stash**: a Gather at JamesHouse may take 2 Energy Drinks instead of a random draw.
- **Haunted** (Sanity < 3): at Dawn draw 1 Threat at that character's tile; only they may fight/flee it; discard when resolved; never festers.
- **Doom 15 = Scarcity**: crafts cost +1 extra resource of the crafter's choice (Market refills at full speed; `canAfford` accounts for it).
- **Visitors**: one-shot aid, depart at next Dawn — the adoption rule was cut.
- **Night light check is automated**: `checkPlayerHasLight` (night.lua) scans the player's hand + player-board area for Flashlight / Lantern / Fire Kit (matched by `M_*` card tag or nickname; fire-only nights ignore the Flashlight) and the character's tile for a Campfire (tile-wide, radius 7). No manual confirmation.
- **Held resources are virtual** (2026-07): the authoritative count lives in `gameState.resources[color]` (per the six resource types), NOT in physical token positions. Physical tokens are decoration laid beside the board. The old position-counting broke the instant a board drifted (boards spawned overlapping, physics flung them across the table, a gathered token ended up 11 units from its board and counted as zero). `giveResource` (increment + spawn a visual token), `getPlayerResources` (read the count), `verifyAndPayResources` / `takeResourceFromPlayer` (deduct + best-effort clear a visual token) all go through gameState via `ensurePlayerResources` (helpers.lua). Player boards are now **locked** and spaced 9 units apart (build_save), with unused ones benched under the table at setup (`benchUnusedBoards`).
- **All resource costs are auto-paid**: `verifyAndPayResources` (ui_actionbar_core.lua) checks the held count, deducts it, and blocks the action (with an action refund) if short. Used by Cleanse, Appease-Treeguard, Barricade, **Craft** (`doCraft` auto-pays `MARKET_COSTS` + a Scarcity surcharge at Doom ≥ 15, auto-picked from the most-held resource), **and Cook** (`doCook` auto-pays `RECIPE_DATA[id].ingredients`, parsed by `generate_recipe_data.py` from the `ingredients` CSV column; Ellie's Crockpot Master shaves 1 off the largest ingredient via `recipeIngredientCost`, and the Feast exempts cooking since it consumed all Food up front). There is no Discard Tray any more — nothing is dropped to pay.
- **Dusk ready-check**: each seated player with a living character clicks Ready on the Dusk panel (`toggleDuskReady`, turns.lua); Night begins automatically at full count. Host's Resolve Night is the override / hotseat path.
- **Drag-to-move** (2026-07): dropping a character standee on a location circle is a Move request (`onObjectDrop` → `_handleStandeeDrop`, ui_actionbar_targets.lua) — legal during Day on your turn (adjacency checked; Rayman's bonus hop supported) or as the Dusk scramble; anything illegal snaps the standee back to `char.location` with the reason.
- **Signature Moves** (§6.7, `lua/signatures.lua`): one once-per-game named move per character (`char.signatureUsed`), fired from the action bar's Signature button with a confirm. James All-Nighter (+3 actions, −3 Sanity at Tick via `gameState.pendingSanityPenalty`), Coco Touch of Hope (+4 Health any tile, dialog target-pick), Rayman Posterize (delete a non-boss threat at his tile; `gameState.loudSignature[loc]` = +1 night draw there), Ellie The Feast (1 action, all held Food consumed, `char.feastActive` makes cooking free until turn end), Luca The Speech (+2 Sanity to all; gated on an ally Down or Sanity < 3).
- **Pry** (§13.5, `doPry` in actions.lua): free action; needs a tool (M_CROWBAR / M_LOCKPICK / M_PRY_BAR in hand or by the board) and a sealed thing at the tile — sealed Threat cards (`SEALED_REWARDS` keys) or the `SealedBasement` object placed at Ellie & Luca's House by build_save.py (`gameState.basementOpened`). The actPry button lights only when both hold.
- **Dawn Dares** (batch 3): optional hooks on some Phase 1–2 Dawn cards. Scripted flags: `dareCourtGlow` (P1_LIGHTS_FLICKER — courts +2 night threats, survivors claim 2 Market cards at Dawn) and `darePorchLight` (P2_PORCH_LIGHT — first house Gather may upgrade to 3 resources for 2 Sanity, via confirm in doGather). The rest are optional `DAWN_MANUAL_STEPS` checklist offers.
- **The Wrongness** (batch 3, P2_BASKETBALL_BOUNCE): a face-down deferred threat at the Basketball Court, `gameState.wrongness = {location, guid, placedDay}`. Resolves on tile entry (`checkWrongnessEntry` from Move/bonus/Dusk/Flee) or at the next Dawn in place (`resolveWrongness`, BeginDay). Excluded from festering while pending.
- **Night Sounds** (batch 3): at Dusk, if the threat deck's top card maps to `"Hard"` in `THREAT_TYPE_BY_NAME`, `Audio.playGrowl()` fires. No rule text — deliberately unexplained.
- **Difficulty modes** (§17.2, batch 4 W3): `gameState.difficulty` = `standard` / `weekend` / `nightmare`, selected in the setup Variants step, driven by `DIFFICULTY_PARAMS` (global.lua). All day-count and doom-limit logic reads `getTotalDays()` / `getDoomLimit()` / `getPhaseForDay()` / `getDoomRate()` — never hardcode 7 or 30.
- **3-player reliefs** (§20.1, batch 4 W2, `playerCount == 3` only): Big Appetite costs 2 Hunger only on days Rayman fought (`gameState.raymanFoughtToday`) or moved 2+ tiles (`gameState.raymanTilesMovedToday`); Loud needs 3+ tiles (`raymanLoudTonight()`, night.lua). Table A/B pending.
- **Session telemetry** (batch 4 W0, `lua/telemetry.lua`): `gameState.chronicle` carries `setup` / `turns[]` (per-turn seconds) / `beats` (press kills, Signatures, Source split, dares). The Week in Review panel's **Copy Session Log** button writes the JSON to the Notes panel. Beat sites call `recordBeat(...)` via safecall.

### Win Condition
Survive all 7 days with Doom < 30 and at least one character not Down — and if The Source has arrived, it must be destroyed before Day 7 ends (a standing Source at the Day-7 Tick is a defeat, whatever the Doom track says). Bonus achievements: **Pristine** (all 5 alive), **Truth** (3 Clue cards), **Hero** (all 3 phase bosses defeated — the Treeguard doesn't count).

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

## ComfyUI Workflow

All artwork in this project is generated locally via ComfyUI — no paid image-API
calls. The pipeline is fire-and-forget: queue prompts → wait for ComfyUI to
finish → sync output into `art/` → run the atlas builder.

### Locked art direction

**Don't Starve Together aesthetic with a modern, urban (North American suburban)
twist.** Hand-drawn ink-line gothic cartoon (Tim Burton / Edward Gorey / Laika
lineage), with contemporary suburban props — smartphones, gaming PCs, energy
drink cans, basketball hoops, badminton nets — rendered *inside* that style,
not as photoreal interjections. This applies to every asset: cards, location
tiles, character standees, bosses, path tiles. The canonical `STYLE` prompt
prefix lives at the top of `scripts/generate_comfyui_assets.py` — keep that
single source of truth in sync if the direction is ever revised.

### Install

- **Path:** `c:\Users\GGPC\Documents\ComfyUI` (Python venv at `.venv/`)
- **Server URL** the scripts assume: `http://127.0.0.1:8000`
- **Models in use:**
  - Diffusion: `models/diffusion_models/flux1-dev-Q8_0.gguf` (loaded via `UnetLoaderGGUF`)
  - VAE: `models/vae/ae.safetensors`
  - CLIP: `models/clip/clip_l.safetensors` + `models/clip/t5xxl_fp16.safetensors`
  - LoRA: `models/loras/flux/c4r1mj34.safetensors` at strength 0.65 (model + clip)
- **Sampler:** `euler`, 30 steps, CFG 4.0, scheduler `normal`, denoise 1.0

### File-naming convention

ComfyUI writes `<prefix>_00001_.png` to `ComfyUI/output/`. Categories used by
the scripts:

| Prefix | Maps to | Sync destination |
|---|---|---|
| `snm_loc_<base>`  | Location tile scenes (1024×1024) | `art/tiles/<base>.png` |
| `snm_path_<base>` | Path-edge variants (1024×1024)   | `art/board/<base>.png` |
| `snm_char_<base>` | **Hand-drawn — never auto-generate.** | `art/characters/<base>.png` is authoritative; the generator and sync script both skip this prefix. |
| `snm_boss_<base>` | Boss / creature standees (512×1024) | `art/bosses/<base>.png` |
| `snm_card_<id>`   | Card illustrations (1024×1024)   | `art/decks/illustrations/<id>.png` |

`<id>` for cards is the `id` column from `content/cards_*.csv`
(e.g. `P1_QUIET_EVENING`, `M_FLASHLIGHT`).

### End-to-end card-art workflow

1. **Start ComfyUI.** From `c:\Users\GGPC\Documents\ComfyUI`, run the venv's
   ComfyUI entrypoint and confirm `http://127.0.0.1:8000` is reachable.
2. **Queue prompts:**
   ```bash
   python scripts/generate_comfyui_assets.py
   ```
   By default queues every board asset *and* every card. Useful flags:
   - `--cards-only` — only the ~150 card illustrations
   - `--no-cards` — only the original 23 board assets
   - `--deck phase1` (repeatable) — limit cards to one deck
   - `--only P1_QUIET_EVENING` — single card by id
   - `--skip-existing` — skip prompts whose `ComfyUI/output/<prefix>_*.png` already exists (ideal for incremental reruns)
3. **Wait** for ComfyUI to drain its queue (watch its console or `output/` mtime). Roughly 30s/image at 1024×1024 on the current rig.
4. **Sync output into the repo:**
   ```bash
   python scripts/sync_comfyui_output.py
   ```
   Idempotent; renames `<prefix>_00001_.png` → `<base>.png` in the right `art/` subdir.
5. **Build card atlases:**
   ```bash
   python scripts/generate_card_atlases.py
   ```
   Composites `art/decks/illustrations/<id>.png` into the top region of each card and renders the text panel beneath. Missing illustrations fall back to a flat accent rectangle — partial generations don't break the build.
6. **Build the TTS save:**
   ```bash
   python scripts/build_save.py
   ```

### Iteration tip

To regenerate a single card with a tweaked prompt:

1. Edit the `art_notes` column for that row in `content/cards_*.csv`.
2. Delete `c:\Users\GGPC\Documents\ComfyUI\output\snm_card_<id>_00001_.png`.
3. Run `python scripts/generate_comfyui_assets.py --only <id> --skip-existing`.
4. Rerun the sync + atlas builder.

## Audio

Game audio is local-asset-driven, no AI generation. Files under `sounds/` are
served by `scripts/serve_art.bat` (which now serves the repo root, so both
`art/` and `sounds/` are reachable at `http://localhost:8080/...`) and
referenced in `lua/audio_manifest.lua` (auto-generated).

### Asset layout

```
sounds/
├── ambient/
│   ├── suburban/   <-- 20 tracks: each Dawn picks ONE and loops it all day
│   ├── varied/     <-- 39 tracks: fallback pool if suburban/ is empty
│   └── night/      <-- 3 synthesized low drones: one picked per night, looped
├── creatures/
│   ├── bearger/    <-- 8 sounds (canonical name; folder was renamed from "beager")
│   ├── deerclops/  <-- 12 sounds (Phase 2 boss)
│   ├── eye_of_terror/  <-- 13 sounds (Phase 3 boss)
│   └── treeguard/  <-- 26 sounds (Phase 2.5 mini-boss — wakes Dusk of Day 4, lua/treeguard.lua)
└── sfx/
    ├── tick_chime.wav             <-- synthesized two-note bell (G5+C6) for end-of-day Tick
    ├── Character_Walk_Sound.mp3   <-- played on Move into an empty location
    ├── Character_Meet_Sound.mp3   <-- played on Move into a location occupied by another character
    ├── Character_TalkTrade_Sound.mp3  <-- played on Trade
    ├── Character_Death_Sound.mp3  <-- played when a character flips to Down
    ├── Turn_Ping_Sound.wav         <-- synthesized E5→A5 ping on turn start (Audio.playTurnPing)
    └── night_growl.wav             <-- synthesized low growl: Night Sounds (Audio.playGrowl, fires at Dusk when the top Threat card is Hard)
```

Any audio file dropped into `sounds/sfx/` is auto-discovered by
`scripts/generate_audio_manifest.py` and exposed as `AUDIO.SFX.<key>`, where
`<key>` is the filename stem lowercased with a trailing `_sound` stripped
(e.g. `Character_Walk_Sound.mp3` → `character_walk`).

The Source has no audio folder; `Audio.playBossLoop("the_source")` no-ops
silently and ambient continues.

### In-game behaviour

- **Day start (Dawn):** `Audio.startDayAmbience()` picks ONE suburban track
  (varied pool as fallback) and loops it until nightfall — a mid-day track
  change read as "did something happen?", so a new track means a new day.
- **Night start:** `Audio.startNightAmbience()` picks one low drone from `sounds/ambient/night/` and loops it. A live boss loop keeps priority (both `startDayAmbience` and `startNightAmbience` no-op while `mode == "boss"`); `stopBossLoop` resumes the night drone if it's Night, the day's track otherwise. `Audio.stopAmbience()` remains as a hard stop.
- **Boss arrives:** `Audio.playBossLoop(<key>)` suspends ambient and plays a
  random sound from `sounds/creatures/<key>/`. After the sound ends + 10s, if
  the boss is still alive, another random sound from the same folder plays.
  Loops until `Audio.stopBossLoop(<key>)` is called.
- **Boss defeated:** combat.lua maps the threat name to a boss key
  (`Audio.threatNameToBossKey`) and calls `Audio.stopBossLoop(<key>)`, which
  resumes the day's looped track (or the night drone at Night).
- **Tick (end of day):** `Audio.playChime()` briefly takes over MusicPlayer for
  the chime, then resumes ambient/boss audio.
- **Character SFX (one-shots):**
  - `Audio.playWalk()` on `doMove` / `doRaymanBonusMove` when the destination is empty.
  - `Audio.playMeet()` on the same handlers when the destination already has another non-Down character.
  - `Audio.playTradeChat()` at the end of `doTrade`.
  - `Audio.playDeath()` from `checkDownState` when a character flips to Down.
  - All four go through `Audio.playSFX(<key>)`, which uses the same brief-interrupt-then-resume machinery as `playChime()`.

Single-channel constraint: TTS has only one global `MusicPlayer`. One-shots
(chime, character SFX, boss roar) interrupt the ambient track for their
duration; the next ambient track is rescheduled fresh after.

### Pipeline

1. **Edit/add sound files** under `sounds/...`.
2. **Regenerate the manifest:** `python scripts/generate_audio_manifest.py` —
   walks the tree, computes durations (precise for `.wav`, file-size-estimated
   for `.mp3`), writes `lua/audio_manifest.lua`.
3. **Build the save:** `python scripts/build_save.py` — `audio_manifest.lua`
   and `audio.lua` are concatenated early in `LUA_LOAD_ORDER` so all gameplay
   files can reference `Audio.*`.
4. **Run the local server:** `scripts/serve_art.bat` (serves repo root over
   `:8080`) so TTS can reach the WAV/MP3 files at the URLs in the manifest.
5. **Hand-add new bosses:** drop sound files in `sounds/creatures/<name>/` and
   extend `Audio.threatNameToBossKey()` if the threat-card name doesn't
   contain `<name>` as a substring.

## Always-obvious next step

The design's stated UX goal (§18.10) is "playable on first sit-down without
reading the rulebook." The implementation layers six signals so the active
player never has to ask "what now?":

### 1. Phase Banner — text + pulse
- `lua/ui_banner.lua` `recommendNext()` writes a one-line "next thing to do" string into the banner every state change.
- `highlightCTA(ids)` pulses an outline around the actual XML control to click. Mapping (`getNextCTA()`):
  - PreGame → `btnSetup`
  - Day, has actions → `actionBar` panel
  - Day, no actions → `actPass`
  - Tick / PreDawn (between days) → `btnBeginDay`
  - Dusk → `btnResolveNight` (ends the scramble window and begins Night)
  - Night → `btnResolveNight`
  - GameOver → `btnRestart`

### 1b. Always-visible character roster + live standee tooltips
- `xml/hud.xml` `charRoster` panel (MiddleRight) shows every character's current Health / Hunger / Sanity as compact bars + numeric values. Each name uses that character's color (James blue / Coco white / Rayman green / Ellie yellow / Luca red).
- `lua/ui_banner.lua` `refreshCharRoster()` (called from `refreshPhaseBanner`) updates the bars, dims rows for Down characters, and hides rows for characters not in the current game.
- `lua/ui_banner.lua` `refreshStandeeTooltips()` rewrites each character standee's `Description` on every state change so hovering a standee shows live `Health/Hunger/Sanity • At <Location>` (or the revival hint if Down).
- `scripts/build_save.py` `STANDEE_COLORS` tints each character's `Figurine_Custom` `ColorDiffuse` so the card holders match the roster naming (James blue, Coco white, Rayman green, Ellie yellow, Luca red).
- **A player's seat colour is determined by the character they pick** (`CHARACTER_COLORS`, global.lua — mirrored by `STANDEE_COLORS`): the guided setup's `reseatPlayerForCharacter` (ui_setup.lua) moves each player onto their character's colour at pick time (anyone parked there is shifted to a spare seat); the bare `Setup()` assigns characters by the same colour scheme.

### 2. What-now hints — auto-loaded from markdown
- `content/help/whatnow_hints.md` is the **source of truth**. `scripts/generate_whatnow_hints.py` parses it into `lua/whatnow_hints.lua` (the `WHATNOW_HINTS` table).
- Group keys: `PreGame`, `Dawn`, `Day`, `Dusk`, `Night`, `Tick`, `PostGame`, `Stats`, `James`, `Coco`, `Rayman`, `Ellie`, `Luca`, `Location`, `Strategic`.
- Dispatch in `lua/ui_help.lua` `onWhatNowClick()` composes a multi-line hint by stacking: phase-base + char-specific + stat warnings + strategic + location.
- Adding a hint: edit the markdown, run `python scripts/generate_whatnow_hints.py`, rebuild.

### 3. Action targets — highlights + click-to-complete buttons
- When the active player clicks an action button, `lua/ui_actionbar_targets.lua` highlights world objects via `obj.highlightOn(color, 8)` AND spawns a clickable 3D `createButton` on every legal target. Clicking the button consumes `gameState.pendingAction` and calls the matching `do*` handler:
  - **Move** → adjacent tiles glow Green with a MOVE HERE button → `doMove`. Rayman's Speed perk chains a second round of FREE MOVE buttons (`doRaymanBonusMove`).
  - **Craft** → Market deck + slots glow Yellow, **affordable** cards Green (see §4); each displayed card gets a CRAFT button → `doCraft(color, slotIndex)`.
  - **Cook** → Recipe cards glow Orange with a COOK button → `doCook(color, recipeId)` (recipe id read from the card's `R_*` tag).
  - **Fight** → fightable threats/bosses at the tile glow Red with FIGHT (and, when fed allies share the tile, TOGETHER) buttons → `doFightTarget(color, obj, together)`.
  - **Peek** (James) / **Rally** (Luca) → per-character bar buttons open the `peekDialog` / `rallyDialog` pickers → `doPeek` / `doRally`.
  - **Cleanse** → required resource bags glow White (confirm dialog, no world button).
  - **Trade** → `tradeDialog` XML panel listing valid partners with the free/1-action cost per row → `doTrade`.
  - **Undo** → `doUndo` (snapshot taken in `spendAction`; also restores `raymanMovedToday`/`raymanBonusMove`; cleared at turn end).
- Target buttons are cleared on completion, on cancel (click the same action button again), at turn end (`endPlayerTurn`/`beginDusk` call `clearActionTargets()`), or after a 30 s timeout.

### 4. Market affordability
- `lua/market_data.lua` (auto-loaded) defines `MARKET_COSTS[<id>] = {Wood=2, Metal=1, ...}` for every Market card.
- `getPlayerResources(color)` in `lua/ui_actionbar_core.lua` reads the authoritative held count from `gameState.resources[color]` (see "Held resources are virtual" above) — position-independent.
- `canAfford(color, cardId)` compares. Affordable Market cards get a Green highlight when Craft is selected, plus a `printToColor` summary of the player's bag contents.

### 5. Auto-broadcast urgent hints
- `gameState.dailyAlerts[color]` flags so each urgent broadcast fires only once per character per day; cleared in `BeginDay()`.
- Triggers:
  - Character goes Down → `tick_victory.lua` `checkDownState` broadcasts the Telltale-Heart cook recipe.
  - James end-of-Day with no Energy Drink consumed → `day_loop.lua` `beginDusk` reminds him before Tick.
  - Dusk per-player warnings (alone at sport court, Coco alone non-house, public Charlie reminder) — also in `beginDusk`.

### 6. Idle nudge
- `turns.lua` runs an idle watcher during the `Day` sub-phase: every 10s it checks `os.time() - gameState.lastInteractionAt`.
- After 45s of inactivity, the active player is `printToColor`'d a "click What now?" prompt — once per turn (`gameState.idleNudgedThisTurn`).
- `noteInteraction()` is called from `validateActivePlayer()` so any action click resets the timer.

### 6b. Dawn-card manual-steps checklist
- `DAWN_MANUAL_STEPS` (effects/dawn_effects.lua) lists the physical/manual steps for every Dawn card the script can't fully resolve (token moves, group choices, deck searches). `dispatchDawnEffect` copies them into `gameState.dawnChecklist`.
- `refreshDawnChecklist` (ui_rules.lua) renders them as tickable rows in the `dawnChecklist` XML panel (top right, max 4 rows); any player clicks to tick; the panel hides itself when all are done. Outstanding steps also appear as "DAWN CARD TO-DO" lines in the Rules panel.
- When adding a Dawn card with a manual instruction, add its steps to `DAWN_MANUAL_STEPS` — fully scripted cards stay out of the table.

### 7. "Rules in effect" panel + day-cycle strip
- `lua/ui_rules.lua`, refreshed from `refreshPhaseBanner()` on every state change. Broadcasts scroll away; this panel mirrors every rule *currently* modifying play into a persistent left-side panel (`rulesPanel` in the XML, collapsible):
  - current sub-phase rules (one line, `SUBPHASE_RULES`),
  - crossed Doom thresholds (`DOOM_THRESHOLD_RULES`),
  - ongoing Dawn-card effects (`EFFECT_RULES` maps every `gameState.ongoingDawnEffects` flag to player-readable text; add a label here whenever `dawn_effects.lua` gains a new ongoing flag),
  - Treeguard status, and per-character statuses (Down / Haunted / can't-Fight / injured / Charlie streak / James Wired pending / Rayman Loud).
- `refreshCycleStrip()` renders `Dawn ▸ Day ▸ Dusk ▸ Night ▸ Tick` under the Phase Banner (`cycleStrip`) with the current step lit, so players always see where they are in the loop.
- The `PreDawn` sub-phase (between Tick and the next Begin Day) is fully wired: banner text, `btnBeginDay` CTA pulse, and a `between_days` What-now hint (Tick group in `whatnow_hints.md`).

### 8. Message Log — nothing said is ever lost
- TTS broadcasts fade in seconds and render behind the Phase Banner, so `broadcastEvent` (global.lua) also appends every public message to `gameState.messageLog` (persists through save/load, capped at 40).
- `lua/ui_msglog.lua` renders the newest entries in the draggable `msgLog` panel (xml/msglog.xml), colour-coded by category; Clear/Hide buttons on the panel, "Log" toggle on the banner. What-now hints open the per-player `whatNowPanel` (visibility set to the asking player's colour) with a "Got it" dismiss.

## Balance Simulation

`scripts/simulate_balance.py` is a standalone Monte Carlo probe of the 7-day campaign loop. It is **not part of the build pipeline** — it exists to answer "does this rule change move the win rate / Doom pressure the way we intended?" *before* human playtests. Design target: 40–50% wins on Standard for an experienced group (design §20.2).

### Commands

```bash
python scripts/simulate_balance.py                      # all 4 policies, current rules, 2000 games each
python scripts/simulate_balance.py --sims 5000          # tighter estimates
python scripts/simulate_balance.py --rules old          # frozen pre-2026-07 ruleset, for before/after diffs
python scripts/simulate_balance.py --players 3          # player-count scaling (3/4/5)
python scripts/simulate_balance.py --policy turtle      # single policy
python scripts/simulate_balance.py --trace --policy balanced --seed 7   # one game, day-by-day log
python scripts/simulate_balance.py --sweep3             # all ten 3-character teams (composition viability)
```

### Policies (what each one tests)

| Policy | Behavior | Probes |
|---|---|---|
| `turtle` | Everyone stacks at Ellie & Luca's, day and night; ignores the mid-bosses; fights the Source (all policies must — it's mandatory) | Anti-stacking pressure (crowded floor, festering bosses) |
| `spread` | Gather by day, everyone sleeps at their own home; ignores the mid-bosses | The boss-avoidance line — the strategy items 1–2 of the 2026-07 retune exist to kill |
| `balanced` | Pairs at night; strike pair (Rayman+James) day-chips loose bosses; all hands converge on the Source; appeases the Treeguard, cleanses | Whether engaging the whole map is worth it |
| `court_camper` | Balanced + Rayman sleeps at a court for Moonlit Salvage (unless a boss is loose) | Whether the salvage gamble is a temptation or an exploit |

### Baseline results (2026-07 batch 4 calibration, 3000 sims, 4 players — diff future runs against this)

Ruleset in this baseline: **Source-mandatory victory**, **uncapped boss festering** (+2/dawn per phase boss, +1 Treeguard; threats +1 capped at +3), **no boss arrival Doom**, retuned per-count Doom rates (3p [1,1,1,1] / 4p [1,1,1,2] / 5p [1,1,2,2]), batch 1 (**Press the Attack**, **boss-kill rewards**), batch 2 (**Nothing Left to Lose**, **Signature Moves**, **Source split**, **Last Dawn**), batch 3 (**Sealed Basement**, **Wrongness token**; Night Sounds and Dawn Dares are playtest-only) — plus batch 4: **the Source retuned HP 10 → 8** (the W3 calibration knob) and the **3-player reliefs** (Big Appetite conditional + Loud needs 3+ tiles, `playerCount == 3` only).

| policy | win% new rules | win% old rules | loss:source (new) | loss:down (new) | late-loss% |
|---|---|---|---|---|---|
| turtle | 42% | 84% | 1% | 30% | 100% |
| spread | 42% | ~100% | 14% | 1% | 100% |
| balanced | 15% | 76% | 25% | 25% | 99% |
| court_camper | 14% | 72% | 24% | 26% | 100% |

Reading: **the §20.2 calibration target is met on the simulator** — the best lines sit at 42% (target band 40–50%) and ~100% of losses land on Days 6–7 (a near-miss finish, not a mid-week strangle). The single knob taken was the design's own §20.1 first choice: Source HP 10 → 8 (turtle 34→42, spread 27→42, fighting lines 10→14-15). Table confirmation is still required — the sim's known bias (Trophies unmodeled, fighters undervalued) means the human number may run higher. The batch-3 table (turtle 34/spread 27/balanced 11/court_camper 10) is preserved in git.

**3-player sweep after the W2 reliefs** (`--sweep3`): the cliff is gone but over-corrected in the sim — Rayman trios now top the turtle table (97–99%) because Loud is his only modeled cost against his fully-modeled combat value. Floor gate passes (worst trio 31% under its best policy; nothing near 0). Treat the sim's Rayman numbers as a bracket, not a measurement: the real tuning verdict belongs to the W2 table A/B.

### 3-character composition sweep (2026-07, `--sweep3`)

The policies are **composition-aware** (strike pair, weapon carriers, and night pairing adapt to whoever is on the roster; `FIGHTER_PRIORITY` resolves to Rayman+James on the full roster, so 4p/5p baselines are unaffected). `--sweep3` runs every 3-character team; results at 2000 sims (win% under `balanced` / under `turtle`):

| team | balanced | turtle |
|---|---|---|
| Coco+Ellie+Luca | 50% | **86%** |
| James+Coco+Luca | 0% | **75%** |
| James+Coco+Ellie | 5% | **73%** |
| James+Ellie+Luca | 37% | 34% |
| every team with Rayman (6 teams) | ≤0.1% | ≤6% |

Three readings, in confidence order. (1) **3p viability is strongly composition-dependent** — the spread between best and worst team is ~85 points, and every team above 7% carries Coco or Luca. The design's "any 3 of 5" claim (§6.6) is not supported by the model; this is logged as a §20.1 balance risk. (2) **At 3 players, turtling dominates** — splitting up (balanced's stationing) is wrong at this action economy; the best play for a trio is one shared camp. (3) **Every Rayman team collapses** (down-losses 44–99%) — but read this one with the bias warning below: Rayman's costs (Big Appetite, Loud, tank-takes-all-counters) are fully modeled while his value (Defend, Court Master, Speed, and Trophy rewards for the fights he enables) is mostly *not*. The sim systematically undervalues the fighters and fully values the support cast, so the Rayman cliff is a flag for playtesting, not a stat-change warrant on its own.

### Model assumptions (documented in the script's docstring)

- Resources are a **shared team pool** — over-models trading (the real same-tile restriction is looser here).
- Named bosses arrive **on schedule** (Deerclops D4, Eye D5, Source D6) rather than by deck luck; Treeguard wakes Dusk D4 as in the real rules.
- Market is abstracted to Flashlights + one Weapon per fighter; Dawn cards are a random minor-effect distribution.
- Bots are competent, not brilliant. Calibration lesson: early "terrible" results were **bot blunders, not rule problems** (Rayman sleeping alone with Loud, James never visiting his Stash, nobody reviving the fallen). When a result looks insane, run `--trace` and read the day-by-day log before blaming the rules.

### Maintenance rule

The sim mirrors constants from `lua/global.lua` and the design doc by hand (stats, Doom rates, thresholds, yields, boss schedule). **When a gameplay rule changes, update the sim to match and rerun both rulesets.** Keep `--rules old` frozen as the pre-2026-07 snapshot — it is the control group, not a second live ruleset.

## Test Suite

`tests/` is a pytest suite (no TTS required). Run it after any change:

```bash
python -m pytest tests          # needs: pip install pytest lupa
```

CI runs it on every push (`.github/workflows/tests.yml`). What it covers:

- **`test_csv_schema.py`** — every `content/*.csv`: required columns, unique/well-formed ids, stat ranges, starting-item characters/counts.
- **`test_cross_refs.py`** — cross-artifact drift: every Dawn card has a `DAWN_EFFECTS` entry (and no orphans), every `ongoingDawnEffects` flag has an `EFFECT_RULES` label, atlas grids hold every card **and** match `NumWidth/NumHeight` in build_save.py, hardcoded card ids in Lua exist in the CSVs, `MARKET_COSTS` covers the Market deck, every asset/sound URL resolves to a file on disk, `TOOLTIP_DATA` keys are real save tags, starting-hand decks match `cards_starting.csv`, and the standee slot constants in build_save.py mirror `helpers.lua`.
- **`test_xml_quality.py`** — the silent TTS failure modes: XML well-formedness, no literal `\n` in attributes (renders as text), every color parseable by TTS (hex length 3/4/6/8; rgb()/rgba() components must be 0-1 floats — 0-255 values clamp to white; checked in the XML **and** Lua color literals), `<Image image=...>` names resolve to `CustomUIAssets` + files on disk, and the per-character UI ids the Lua composes dynamically all exist.
- **`test_lua_lint.py`** — runs `luacheck lua` against the generated `.luacheckrc` when luacheck is installed (skips otherwise; CI's luacheck job always runs it), and asserts `.luacheckrc` is still the generated file. (CI's luacheck job is `continue-on-error` — flip it to hard-fail after reviewing a green run.)
- **`test_generated_freshness.py`** — reruns the three generators and fails if `audio_manifest.lua` / `whatnow_hints.lua` / `market_data.lua` are stale (always restores the committed bytes).
- **`test_xml_lua_contract.py`** — every UI id the Lua targets exists in the `xml/` files; every XML `onClick` and Lua `click_function` names a defined function; XML ids are unique across all files.
- **`test_publish_build.py`** — a `--publish` build contains no `file:///` or `localhost` URL anywhere and never touches the committed dev save.
- **`test_lua_statics.py`** — no global function/constant is defined twice across the concatenated bundle (the later definition would silently win); every lua file is deliberately placed in `LUA_LOAD_ORDER`.
- **`test_build_output.py`** — rebuilds the save, validates the JSON, and fails if `saves/StarveNoMore.json` is stale relative to the sources (restores committed bytes; run `python scripts/build_save.py` to fix).
- **`test_lua_*.py`** (`test_lua_setup` / `test_lua_combat` / `test_lua_dawn` / `test_lua_actions` / `test_lua_day_loop` / `test_lua_telemetry`) — run the real concatenated bundle headlessly under Lua 5.2 (`lupa`) with `tests/tts_stub.lua` faking the TTS API: load smoke, `onLoad`/`onSave` round-trip, combat fumble rules, Charlie escalation/reset, Tick decay + Down + victory/defeat, revive, night light checks, and an `apply()`/`expire()` sweep over every Dawn effect. The shared bundle harness (`env` fixture, `make_env`, `add_char`, `script_dice`, `broadcasts`, `flush`, `populate_full_world`, …) lives in `tests/conftest.py`. When adding gameplay rules, add a test to the matching topic module; extend the stub in `tts_stub.lua` if the code uses a TTS API it doesn't cover yet. (Split 2026-07 from a single 1,662-line module.)
- **`test_sim.py`** — enforces the sim maintenance rule mechanically (sim constants must equal `global.lua`'s: stats, homes, Doom rates/thresholds, Cleanse, boss statlines vs build_save + combat.lua, difficulty invariants), asserts per-game invariants over seeded batches, and checks policy win rates stay inside bands around the baseline table above. If you change a rule intentionally: update the sim, rerun the 3000-sim baseline, update the table above **and** the bands in `test_sim.py`.
- **`test_full_campaign.py`** — a trivial bot plays whole games headlessly at every difficulty (invariants only: no hard error, stats in range, a verdict is reached), plus seeded random-verb fuzz games and adversarial sequences (undo spam, re-entrant setup on all three UI paths, restart-then-re-setup). The net for cross-feature breakage.
- **`test_save_fixture.py`** — loads the frozen `saves/fixtures/midgame_v1.json` (and a stripped old-schema variant) into the current bundle and plays a full day. Guards `migrateGameState()`.
- **`test_analyze_sessions.py`** — the playtest-log aggregator against synthetic and real telemetry exports.
- **`test_dead_handles.py`** — the dead-handle class from both ends: a runtime sweep that drops a poisoned handle on the table and runs the real gameplay entry points over it, plus a static scan for object fields dereferenced without a guard.
- **`test_tts_api_surface.py`** — a curated allowlist of the TTS singleton API, checked in both directions: Lua may only *call* what exists, and `tts_stub.lua` may only *define* what exists (a stub that invents API makes the suite confirm bugs instead of catching them).
- **`test_regression_guards.py`** — generic guards for the *classes* of bug that keep recurring in playtest, each encoding one hard-won lesson (see `docs/tts-runtime.md` and `docs/tts-interface.md`). Fourteen checks, covering spawn overlap, text-gadget rotation, button contrast and runtime colour overrides, unguarded object handles, board scale vs. artwork, on-board spawn heights, hidden objects staying hidden and silent, path-layout mirroring, and player-board alignment:
  1. laid-out object groups (player boards, location tiles) must not overlap at spawn — physics scatters an overlapping stack (the root cause of "Gather shows 0");
  2. text-gadget objects (Notecard/Counter) must be upright (rotY≈0), not 180 (the upside-down Quick Start);
  3. button text must clear a minimum contrast (3.0) against its own background (the dark-on-dark readability complaints); transparent click-overlays are excluded;
  4. **every `takeObject` callback that dereferences its object handle must wrap it in pcall/safecall** — a dead handle throws "cannot access field … of userdata"; that crash hit three times in one session and the guard immediately found five more latent ones;
  5. every tag passed to `findOneByTag`/`findAllByTag`/`getObjectsWithTag` — literal (`"DoomMarker"`) or namespaced (`"Location:" .. name`) — must exist in the built save, because a typo'd tag fails **silently** (returns nil, feature quietly does nothing);
  6. player-facing text must not name a component that was removed from the save (a Dawn card told players to use the Discard Tray for a release after it was deleted); keyed by tag, so it only fires once the component is really gone;
  7. no player-facing string may hardcode the Standard `of 7` / `/ 30` — those are wrong on Long Weekend (3 days, Doom 15) and Nightmare; use `getTotalDays()` / `getDoomLimit()` or the `{totalDays}` / `{doomLimit}` tooltip placeholders;
  8. `gameState` fields must be initialised (literal default, `migrateGameState`, or a lazy init earlier in the same function) before being indexed — otherwise a fresh setup or loaded old save crashes with "attempt to index a nil value".

  Runtime companions in `test_lua_actions.py`: `TestResourceModelRobustness` (held resources stay correct when a board is dragged away — the gather-shows-zero class), `TestStatDisplayNeverStale` (the left stat box shows live stats with no active player, not a frozen snapshot), and `TestDifficultyAwareText` (the Doom help panel and the Day/Doom tooltips print the *active difficulty's* limits, with no unsubstituted `{placeholders}`).

In-TTS checks that can't run headlessly stay in `lua/audit.lua` (`auditFirstLoad()`, `auditTooltips()`, `auditHintCoverage()`, `auditObjectCount()` from the TTS console).

### In-TTS self-test

`lua/selftest.lua` adds **`runSelfTest()`** — run it from the TTS console (~20s). It plays a scripted mini-game against the real components: component audit → Setup → Begin Day → Gather → Undo → Pass → Dusk → Night → Tick → save/load round-trip, asserting `gameState` after every step and reporting `[OK]`/`[FAIL]` lines with a summary. **It resets game state and moves real cards — run it on a fresh load, then reload the save before playing.** The same steps are exercised headlessly in CI (`test_lua_setup.py::TestSelfTest`), so in TTS it mainly catches the physical layer: missing objects, asset loading, engine quirks.

### Release checklist (before sharing a new save)

1. `python -m pytest tests` — everything green.
2. Rebuild + serve: `python scripts/build_save.py`, start `scripts/serve_art.bat`.
3. Load the save fresh in TTS — no red errors in the console, board/tiles/cards show art (not placeholders), day ambience starts.
4. Run `runSelfTest()` from the console — 0 failures. Reload the save.
5. Spot-check the physical layer the tests can't see: hover a standee (live tooltip), click Setup and eyeball the walkthrough panels, open Help/Notebook tabs, confirm one boss arrival plays its roar (e.g. trigger Deerclops via a Day-4 run or console).
6. Save mid-game (Day 2+), reload, confirm the banner says "game restored" with the right Day/Doom.

## Working With This Project

### To build the TTS save:
```bash
python scripts/build_save.py                                   # dev save (file:/// art, localhost sounds/rules)
python scripts/build_save.py --publish https://your.cdn/snm    # shareable save, hosted URLs only
```

### To regenerate card atlases:
```bash
python scripts/generate_card_atlases.py
```

### To regenerate tokens/boards/etc:
```bash
python scripts/generate_assets.py
```

### To queue illustration generation (requires ComfyUI running):
```bash
python scripts/generate_comfyui_assets.py
# Useful flags:
python scripts/generate_comfyui_assets.py --cards-only --skip-existing
python scripts/generate_comfyui_assets.py --deck phase1
python scripts/generate_comfyui_assets.py --only P1_QUIET_EVENING
python scripts/generate_comfyui_assets.py snm_boss   # backward-compatible substring filter
```

### To copy ComfyUI outputs into the repo art/ tree:
```bash
python scripts/sync_comfyui_output.py            # idempotent
python scripts/sync_comfyui_output.py --dry-run  # preview
```

### To regenerate the auto-loaded Lua data tables:
```bash
python scripts/generate_audio_manifest.py    # sounds/  → lua/audio_manifest.lua
python scripts/generate_whatnow_hints.py     # whatnow_hints.md → lua/whatnow_hints.lua
python scripts/generate_market_data.py       # cards_market.csv + cards_starting.csv → lua/market_data.lua (costs + weapon dice)
python scripts/generate_threat_types.py      # cards_threats.csv → lua/threat_types.lua (types + sealed rewards)
python scripts/generate_recipe_data.py       # cards_recipes.csv → lua/recipe_data.lua
python scripts/generate_notebook.py          # notebook/help markdown → lua/notebook_data.lua
python scripts/generate_player_rules.py      # notebook/glossary markdown → PlayerRules.md + PlayerRules.html
python scripts/generate_symbol_index.py      # lua/ → SYMBOLS.md + .luacheckrc
```

### To aggregate playtest session logs:
```bash
python scripts/analyze_sessions.py           # reads playtest/sessions/*.json
```

### To sanity-check a rule change against the balance sim:
```bash
python scripts/simulate_balance.py --sims 3000              # current rules
python scripts/simulate_balance.py --sims 3000 --rules old  # control group
# then compare against the baseline table in the "Balance Simulation" section
```

### To test in TTS:
```bat
iwanttoplay
```
(repo root) — regenerate everything → build → full pytest gate → copy the save
to the TTS saves folder → ensure the asset server is up → launch TTS via Steam.
`--skip-tests` / `--no-launch` to trim the ends. Driver: `scripts/iwanttoplay.py`.

Manually, the same steps are:
1. Run `python scripts/build_save.py`.
2. Start `scripts/serve_art.bat` so `http://localhost:8080/art/...` and `/sounds/...` resolve.
3. Copy `saves/StarveNoMore.json` to your TTS saves folder.
4. Load the save in TTS, click **Setup Game**.
