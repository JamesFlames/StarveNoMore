# Starve No More — Agent Reference

## Project Overview

**Starve No More** is a cooperative survival board game built as a Tabletop Simulator (TTS) mod. Players control 5 teenagers (James, Coco, Rayman, Ellie, Luca) surviving 7 days in a Don't Starve-inspired suburban setting. The game uses a 3-stat economy (Health, Hunger, Sanity), a Doom track (0–30), 4 escalating phases, and a day/night cycle with Dawn card events.

## Documentation Map

Quick index of every Markdown doc in the repo, so you know which to open for which task.

### Top-level

- [StarveNoMoreRequirements.md](StarveNoMoreRequirements.md) — original commission brief (characters, locations, source-game influences). Frozen.
- [StarveNoMoreDesignConcept.md](StarveNoMoreDesignConcept.md) — **the canonical design doc** (~1300 lines). Pitch, pillars, character/location/deck specs, turn structure, combat, Doom track, victory conditions, TTS implementation plan, and the UX program (§18.10–18.18) that makes the game playable without reading rules. Open this for any rules or design question.
- [Checklist_For_TTS_Implementation.md](Checklist_For_TTS_Implementation.md) — phased build plan (Phases A–K) from design lock through Workshop publish. Use to find which phase a given task belongs to and its acceptance criteria.
- agents.md — this file.

### docs/ — reference material (read for context, not authoritative for the game itself)

- [docs/HowToCreateGamesInTabletopSimulator.md](docs/HowToCreateGamesInTabletopSimulator.md) — TTS API quick-reference: save JSON schema, object types, Lua callbacks, XML UI, common pitfalls. Open when scripting or building components.
- [docs/PrinciplesOfGoodBoardGames.md](docs/PrinciplesOfGoodBoardGames.md) — general board game design theory (MDA, elegance, replayability, pacing, common pitfalls).
- [docs/DontStarveVideoGamePrinciples.md](docs/DontStarveVideoGamePrinciples.md) — DST design pillars and how each translates to tabletop. Source for tone and the three-stat trade-off economy.
- [docs/InterestingGames.md](docs/InterestingGames.md) — mechanical tear-downs of Hogwarts Battle, Catan, and Cthulhu Wars. Source for the Dawn-deck "world acts first" pattern, modular map, and asymmetric factions.

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
- `scripts/build_save.py` — Concatenates 17 Lua files + XML into the TTS save JSON
- Lua load order is defined in `LUA_LOAD_ORDER` inside build_save.py
- All Lua files live in `lua/` and its subdirectories
- UI XML lives in `xml/global_ui.xml`

### Asset Pipeline
- `scripts/generate_card_atlases.py` — Renders card atlas PNGs from CSV data in `content/`
- `scripts/generate_assets.py` — Renders tokens, boards, player boards, legends via Pillow
- `scripts/generate_comfyui_assets.py` — Queues 23 illustration prompts to local ComfyUI (Flux Dev)
- Card data CSVs: `content/phase1_cards.csv` through `content/trophies.csv`
- Output images: `art/decks/`, `art/tokens/`, `art/icons/`, `art/board/`, `art/characters/`, `art/legend/`

## File Structure

```
StarveNoMore/
├── lua/
│   ├── global.lua              # Game state, lifecycle, onLoad/onSave
│   ├── helpers.lua             # Utility functions (safecall, getters)
│   ├── day_loop.lua            # Day advance, turn management, Dawn/Day/Dusk/Night
│   ├── actions.lua             # Player actions (move, gather, cook, trade, etc.)
│   ├── combat.lua              # Combat resolution, boss fights
│   ├── tick_victory.lua        # Tick decay, victory/defeat conditions
│   ├── ui_actionbar.lua        # Action bar button handlers
│   ├── ui_controls.lua         # Host controls, confirm dialogs, tooltips
│   ├── ui_hud.lua              # HUD panels (stats, doom, day display)
│   ├── ui_notebook.lua         # In-game notebook / log
│   ├── ui_setup.lua            # Guided setup walkthrough, character briefing
│   ├── ui_help.lua             # Help panel, "What now?" contextual hints
│   ├── ui_mood.lua             # Lighting presets, safety-net confirms, camera nudges
│   ├── audit.lua               # Performance audit, tooltip audit, first-load checks
│   └── effects/
│       ├── dawn_effects.lua    # 40 Dawn card effect dispatch table
│       ├── threat_effects.lua  # Threat card resolution
│       └── market_effects.lua  # Market item effects
├── xml/
│   └── global_ui.xml           # All UI panel definitions
├── content/
│   ├── phase1_cards.csv        # Dawn cards per phase (1–4)
│   ├── phase2_cards.csv
│   ├── phase3_cards.csv
│   ├── phase4_cards.csv
│   ├── market_cards.csv
│   ├── recipes.csv
│   ├── threats.csv
│   ├── visitors.csv
│   └── trophies.csv
├── art/                        # Generated image assets
├── saves/                      # Built TTS save JSON
├── scripts/                    # Build + asset generation scripts
└── docs/                       # Design documents
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

### Locations
JamesHouse, RaymanHouse, EllieLucaHouse, BasketballCourt, BadmintonCourt

### Phases
1. **Dusk of Week** (Days 1–2) — Calm intro
2. **Strange Days** (Days 3–4) — Escalation, Deerclops arrives
3. **Long Nights** (Day 5) — Eye of Terror arrives
4. **Final Hours** (Days 6–7) — The Source arrives, endgame

### Day Cycle
Dawn → Day (player turns, 3 actions each) → Dusk → Night → Tick (stat decay)

### Doom Track
0–30. Thresholds at 5 (warning), 10 (camera nudge), 15, 20, 25. Doom 30 = defeat.

### Win Condition
Survive all 7 days with at least one character standing.

## Key Conventions

- All object lookups use `getObjectsWithTag(tag)` — never hardcoded GUIDs
- `safecall(fn, label)` wraps all non-critical calls for graceful error handling
- `broadcastEvent(category, message)` for all player-facing messages (logs to dayLog)
- Game state is a single `gameState` table, persisted via `onSave`/`onLoad` with JSON encoding
- UI panels are shown/hidden via `UI.show(id)` / `UI.hide(id)` targeting XML element IDs
- The build script is the single source of truth for what gets packaged into the TTS save

## Working With This Project

### To build the TTS save:
```bash
python scripts/build_save.py
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
# Optional: filter by prefix
python scripts/generate_comfyui_assets.py snm_boss
```

### To test in TTS:
1. Build the save with `build_save.py`
2. Copy the output JSON to TTS saves folder
3. Load in TTS, click "Setup Game"
