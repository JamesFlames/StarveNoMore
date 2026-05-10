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
- Card data CSVs: `content/cards_phase1.csv` … `cards_phase4.csv`, plus `cards_market.csv`, `cards_recipes.csv`, `cards_threats.csv`, `cards_visitors.csv`, `cards_trophies.csv`, `cards_scenarios.csv`, and `locations.csv`, `resources.csv`, `tooltips.csv`
- Output images: `art/decks/`, `art/tokens/`, `art/icons/`, `art/board/`, `art/characters/`, `art/legend/`

## File Structure

```
StarveNoMore/
├── lua/
│   ├── helpers.lua             # Utility functions (safecall, getters)
│   ├── global.lua              # gameState table, lifecycle, onLoad/onSave
│   ├── setup.lua               # Bare gameplay setup (deals/shuffles/places)
│   ├── day_loop.lua            # Day advance, turn management, Dawn/Day/Dusk/Night
│   ├── effects/
│   │   └── dawn_effects.lua    # Dawn card effect dispatch table
│   ├── combat.lua              # Combat resolution, boss fights
│   ├── crafting.lua            # Market craft + Crockpot cook handlers
│   ├── night.lua               # Night-phase resolver (threat draw, Charlie, sleep)
│   ├── tick_victory.lua        # Tick decay, victory/defeat conditions
│   ├── actions.lua             # Player actions (move, gather, fight, rest, cleanse)
│   ├── ui_banner.lua           # Top-of-screen Phase Banner (day/phase/doom/active/next)
│   ├── ui_actionbar.lua        # Per-board action bar buttons + cube animation
│   ├── ui_controls.lua         # Host controls, confirm dialogs, tooltips
│   ├── ui_setup.lua            # Guided setup walkthrough, character briefing
│   ├── ui_help.lua             # Help panel tabs, "What now?" contextual hints
│   ├── ui_mood.lua             # Phase lighting presets, safety-net confirms, camera nudges
│   ├── audit.lua               # Performance audit, tooltip audit, first-load checks
│   └── assets.lua              # ASSETS table — single source of truth for image URLs
│                               # (NOTE: not in LUA_LOAD_ORDER; concatenated separately)
├── xml/
│   └── global_ui.xml           # All UI panel definitions
├── content/
│   ├── cards_phase1.csv        # Dawn cards per phase (1–4)
│   ├── cards_phase2.csv
│   ├── cards_phase3.csv
│   ├── cards_phase4.csv
│   ├── cards_market.csv
│   ├── cards_recipes.csv
│   ├── cards_threats.csv
│   ├── cards_visitors.csv
│   ├── cards_trophies.csv
│   ├── cards_scenarios.csv
│   ├── locations.csv
│   ├── resources.csv
│   ├── tooltips.csv
│   ├── iconography.md
│   ├── asset_manifest.md
│   ├── notebook/               # Quickstart + Full rules + Character reference
│   └── help/                   # Glossary + Character briefings + What-now hints
├── art/                        # Generated image assets
├── saves/                      # Built TTS save JSON (StarveNoMore.json + .pretty.json)
├── scripts/                    # Build + asset generation scripts
└── docs/                       # Design reference docs
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
0–30. Thresholds at 10 (night threats +1), 15 (Market refresh 1/day), 20 (−1 Sanity at Tick), 25 (bosses can appear in any phase), 30 = defeat. Cleanse action (1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink) reduces Doom by 2.

### Win Condition
Survive all 7 days with Doom < 30 and at least one character not Down. Bonus achievements: **Pristine** (all 5 alive), **Truth** (3 Clue cards), **Hero** (all 4 bosses defeated).

## Key Conventions

- All object lookups use `getObjectsWithTag(tag)` — never hardcoded GUIDs
- `safecall(fn, label)` wraps all non-critical calls for graceful error handling
- `broadcastEvent(category, message)` for all player-facing messages (logs to dayLog)
- Game state is a single `gameState` table, persisted via `onSave`/`onLoad` with JSON encoding
- UI panels are shown/hidden via `UI.show(id)` / `UI.hide(id)` targeting XML element IDs
- The build script is the single source of truth for what gets packaged into the TTS save

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
│   ├── suburban/   <-- 20 tracks: random pick plays first when each day starts
│   └── varied/     <-- 39 tracks: chained one-after-another for the rest of the day
├── creatures/
│   ├── bearger/    <-- 8 sounds (canonical name; folder was renamed from "beager")
│   ├── deerclops/  <-- 12 sounds (Phase 2 boss)
│   ├── eye_of_terror/  <-- 13 sounds (Phase 3 boss)
│   └── treeguard/  <-- 26 sounds (forward-looking; not yet spawned in code)
└── sfx/
    └── tick_chime.wav  <-- synthesized two-note bell (G5+C6) for end-of-day Tick
```

The Source has no audio folder; `Audio.playBossLoop("the_source")` no-ops
silently and ambient continues.

### In-game behaviour

- **Day start (Dawn):** `Audio.startDayAmbience()` picks a random suburban
  track. When it ends, varied tracks play one after another for the rest of
  the day.
- **Night start:** `Audio.stopAmbience()` pauses MusicPlayer. No music at night.
- **Boss arrives:** `Audio.playBossLoop(<key>)` suspends ambient and plays a
  random sound from `sounds/creatures/<key>/`. After the sound ends + 10s, if
  the boss is still alive, another random sound from the same folder plays.
  Loops until `Audio.stopBossLoop(<key>)` is called.
- **Boss defeated:** combat.lua maps the threat name to a boss key
  (`Audio.threatNameToBossKey`) and calls `Audio.stopBossLoop(<key>)`, which
  resumes ambient at whichever phase (suburban-first or varied) it had reached.
- **Tick (end of day):** `Audio.playChime()` briefly takes over MusicPlayer for
  the chime, then resumes ambient/boss audio.

Single-channel constraint: TTS has only one global `MusicPlayer`. One-shots
(chime, boss roar) interrupt the ambient track for their duration; the next
ambient track is rescheduled fresh after.

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
