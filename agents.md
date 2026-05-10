# Starve No More — Agent Reference

## Project Overview

**Starve No More** is a cooperative survival board game built as a Tabletop Simulator (TTS) mod. Players control 5 teenagers (James, Coco, Rayman, Ellie, Luca) surviving 7 days in a Don't Starve-inspired suburban setting. The game uses a 3-stat economy (Health, Hunger, Sanity), a Doom track (0–30), 4 escalating phases, and a day/night cycle with Dawn card events.

## Documentation Map

Quick index of every Markdown doc in the repo, so you know which to open for which task.

### Top-level

- [StarveNoMoreDesignConcept.md](StarveNoMoreDesignConcept.md) — **the canonical design doc** (~1300 lines). Pitch, pillars, character/location/deck specs, turn structure, combat, Doom track, victory conditions, TTS implementation plan, and the UX program that makes the game playable without reading rules. Open this for any rules or design question.
- [README.md](README.md) — short orientation for the GitHub landing page.
- agents.md — this file.

### Archive/ — superseded reference material, kept for context

These files were the input/scaffolding for the design but are no longer
consulted by the build pipeline or by everyday work. Treat them as read-only
historical references; do not link to them from new documentation.

- `Archive/StarveNoMoreRequirements.md` — original commission brief.
- `Archive/Checklist_For_TTS_Implementation.md` — phased build plan that drove the early implementation.
- `Archive/HowToCreateGamesInTabletopSimulator.md` — TTS API notes used to scaffold the Lua/XML.
- `Archive/PrinciplesOfGoodBoardGames.md`, `DontStarveVideoGamePrinciples.md`, `InterestingGames.md` — design-theory sources.

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
- `scripts/build_save.py` — Concatenates the Lua files in `LUA_LOAD_ORDER` + `xml/global_ui.xml` into the TTS save JSON.
- Three of the Lua files in that list are **auto-generated** and should never be edited by hand:
  - `lua/audio_manifest.lua`  — built by `scripts/generate_audio_manifest.py` from the `sounds/` tree
  - `lua/whatnow_hints.lua`   — built by `scripts/generate_whatnow_hints.py` from `content/help/whatnow_hints.md`
  - `lua/market_data.lua`     — built by `scripts/generate_market_data.py` from `content/cards_market.csv`
- Run those three generators after editing the corresponding source, then `python scripts/build_save.py`.

### Asset Pipeline
- `scripts/generate_card_atlases.py` — Composites card faces from per-card illustrations + text panel; writes deck atlases to `art/decks/*.png`
- `scripts/generate_assets.py` — Renders tokens, boards, player boards, legends via Pillow
- `scripts/generate_comfyui_assets.py` — Queues board + per-card illustration prompts to local ComfyUI (Flux Dev). Character standees are intentionally excluded (hand-drawn).
- `scripts/sync_comfyui_output.py` — Copies ComfyUI's `output/snm_*_00001_.png` into the matching `art/<subdir>/<base>.png` (idempotent)
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
│   ├── market_data.lua         # AUTO-GENERATED — MARKET_COSTS table from cards_market.csv
│   ├── setup.lua               # Bare gameplay setup (deals/shuffles/places)
│   ├── day_loop.lua            # Day/Dusk/Night advance, turn management, idle nudge
│   ├── effects/
│   │   └── dawn_effects.lua    # Dawn card effect dispatch table (incl. boss arrivals)
│   ├── combat.lua              # Combat resolution; calls Audio.stopBossLoop on defeat
│   ├── crafting.lua            # Market craft + Crockpot cook handlers
│   ├── night.lua               # Night-phase resolver (threat draw, Charlie, sleep)
│   ├── tick_victory.lua        # Tick decay, victory/defeat, Down state + revival hint
│   ├── actions.lua             # Player actions (move, gather, fight, rest, cleanse)
│   ├── ui_banner.lua           # Phase Banner + recommendNext + CTA pulse + active-player indicator
│   ├── ui_actionbar.lua        # Action Bar + target highlights + market affordability
│   ├── ui_controls.lua         # Host controls, confirm dialogs, tooltips
│   ├── ui_setup.lua            # Guided 4-step setup walkthrough + welcome
│   ├── ui_help.lua             # Help panel tabs + What-now dispatch
│   ├── ui_mood.lua             # Phase lighting presets, safety-net confirms, camera nudges
│   ├── audit.lua               # auditTooltips / auditHintCoverage / auditFirstLoad
│   └── assets.lua              # ASSETS table — image URL constants (LOCAL_DEV switch)
├── xml/
│   └── global_ui.xml           # All UI panel definitions (Phase Banner, Action Bar, dialogs)
├── content/
│   ├── cards_phase1.csv ... cards_phase4.csv   # Dawn cards per phase
│   ├── cards_market.csv        # Source of truth for MARKET_COSTS
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
├── saves/                      # Built TTS save JSON (StarveNoMore.json + .pretty.json)
├── scripts/                    # Build + asset/data generation (Python)
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
    ├── tick_chime.wav             <-- synthesized two-note bell (G5+C6) for end-of-day Tick
    ├── Character_Walk_Sound.mp3   <-- played on Move into an empty location
    ├── Character_Meet_Sound.mp3   <-- played on Move into a location occupied by another character
    ├── Character_TalkTrade_Sound.mp3  <-- played on Trade
    └── Character_Death_Sound.mp3  <-- played when a character flips to Down
```

Any audio file dropped into `sounds/sfx/` is auto-discovered by
`scripts/generate_audio_manifest.py` and exposed as `AUDIO.SFX.<key>`, where
`<key>` is the filename stem lowercased with a trailing `_sound` stripped
(e.g. `Character_Walk_Sound.mp3` → `character_walk`).

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
  - Tick → `btnBeginDay`
  - Night → `btnResolveNight`
  - GameOver → `btnRestart`

### 1b. Always-visible character roster + live standee tooltips
- `xml/global_ui.xml` `charRoster` panel (MiddleRight) shows every character's current Health / Hunger / Sanity as compact bars + numeric values. Each name uses that character's standee color (white / red / green / light blue / orange).
- `lua/ui_banner.lua` `refreshCharRoster()` (called from `refreshPhaseBanner`) updates the bars, dims rows for Down characters, and hides rows for characters not in the current game.
- `lua/ui_banner.lua` `refreshStandeeTooltips()` rewrites each character standee's `Description` on every state change so hovering a standee shows live `Health/Hunger/Sanity • At <Location>` (or the revival hint if Down).
- `scripts/build_save.py` `STANDEE_COLORS` tints each character's `Figurine_Custom` `ColorDiffuse` so the card holders match the roster naming (James white, Coco red, Rayman green, Ellie light blue, Luca orange).

### 2. What-now hints — auto-loaded from markdown
- `content/help/whatnow_hints.md` is the **source of truth**. `scripts/generate_whatnow_hints.py` parses it into `lua/whatnow_hints.lua` (the `WHATNOW_HINTS` table).
- Group keys: `PreGame`, `Dawn`, `Day`, `Dusk`, `Night`, `Tick`, `PostGame`, `Stats`, `James`, `Coco`, `Rayman`, `Ellie`, `Luca`, `Location`, `Strategic`.
- Dispatch in `lua/ui_help.lua` `onWhatNowClick()` composes a multi-line hint by stacking: phase-base + char-specific + stat warnings + strategic + location.
- Adding a hint: edit the markdown, run `python scripts/generate_whatnow_hints.py`, rebuild.

### 3. Action target highlights
- When the active player clicks an action button, `lua/ui_actionbar.lua` highlights world objects via `obj.highlightOn(color, 8)` for 8 seconds:
  - **Move** → adjacent location tiles glow Green (uses `LOCATION_ADJACENCY` table; Rayman gets 2-step neighbours via Speed perk).
  - **Craft** → Market deck + slots glow Yellow; **affordable** cards glow **Green** (see §4 below).
  - **Cook** → Recipe cards + EllieLucaHouse tile glow Orange.
  - **Cleanse** → required resource bags (Wood, Cloth, Battery, Energy Drink) glow White.
- Targets re-highlight on each click; no manual cleanup needed.

### 4. Market affordability
- `lua/market_data.lua` (auto-loaded) defines `MARKET_COSTS[<id>] = {Wood=2, Metal=1, ...}` for every Market card.
- `getPlayerResources(color)` in `lua/ui_actionbar.lua` counts `Resource:*` tagged tokens within a padded bounding box around that player's `PlayerBoard:<charName>` object.
- `canAfford(color, cardId)` compares. Affordable Market cards get a Green highlight when Craft is selected, plus a `printToColor` summary of the player's bag contents.

### 5. Auto-broadcast urgent hints
- `gameState.dailyAlerts[color]` flags so each urgent broadcast fires only once per character per day; cleared in `BeginDay()`.
- Triggers:
  - Character goes Down → `tick_victory.lua` `checkDownState` broadcasts the Telltale-Heart cook recipe.
  - James end-of-Day with no Energy Drink consumed → `day_loop.lua` `beginDusk` reminds him before Tick.
  - Dusk per-player warnings (alone at sport court, Coco alone non-house, public Charlie reminder) — also in `beginDusk`.

### 6. Idle nudge
- `day_loop.lua` runs an idle watcher during the `Day` sub-phase: every 10s it checks `os.time() - gameState.lastInteractionAt`.
- After 45s of inactivity, the active player is `printToColor`'d a "click What now?" prompt — once per turn (`gameState.idleNudgedThisTurn`).
- `noteInteraction()` is called from `validateActivePlayer()` so any action click resets the timer.

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
python scripts/generate_market_data.py       # cards_market.csv → lua/market_data.lua
```

### To test in TTS:
1. Run `python scripts/build_save.py`.
2. Start `scripts/serve_art.bat` so `http://localhost:8080/art/...` and `/sounds/...` resolve.
3. Copy `saves/StarveNoMore.json` to your TTS saves folder.
4. Load the save in TTS, click **Setup Game**.
