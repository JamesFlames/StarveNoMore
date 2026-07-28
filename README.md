# Starve No More

A cooperative survival board game for 3–5 players, built as a [Tabletop Simulator](https://store.steampowered.com/app/286160/Tabletop_Simulator/) mod. Suburban friends caught when something cosmic descends on their neighborhood must scavenge, cook, fight, and hold their sanity together for seven nights. Tone modeled on *Don't Starve Together*; mechanical DNA drawn from DST, *Hogwarts Battle*, *Catan*, and *Cthulhu Wars*.

> **Status:** playtest-ready. The design is locked in [`StarveNoMoreDesignConcept.md`](StarveNoMoreDesignConcept.md); all four design batches are implemented (combat excitement, the finale, mid-week texture, validation & hardening — see [`CHANGELOG.md`](CHANGELOG.md)); Standard difficulty is sim-calibrated to the 40–50% target; sessions self-instrument via a one-click telemetry export; the blind-playtest kit lives in [`playtest/`](playtest/facilitator_script.md). What remains is human: the blind playtests themselves.

## Dev quickstart

```bash
pip install pytest lupa Pillow      # lupa runs the real Lua bundle headlessly
python scripts/check.py             # regenerate → build → test → lint (~22 s)
```

`check.py` is the whole verification loop in one command; the individual stages
and their flags are documented once in
[`scripts/CLAUDE.md`](scripts/CLAUDE.md#the-canonical-pipeline).

**Just want to play?** From the repo root:

```bash
./iwanttoplay          # or: iwanttoplay.bat on Windows
```

One command: regenerates every derived artifact → builds the save → runs the
full test suite → copies the save into your TTS saves folder → starts the
asset server → launches Tabletop Simulator. A red test stops the pipeline
before anything ships. Flags: `--skip-tests` (faster, unverified),
`--no-launch` (everything except starting TTS).

The regenerate/build/test half is cross-platform; the install, cache-purge and
launch half is Windows-only and is reported as skipped elsewhere. On Linux or
macOS use `python scripts/check.py` to verify a change.

Everything else — pipelines, conventions, the file map — is in [`docs/agents/`](docs/agents/README.md), indexed from [`agents.md`](agents.md). Rule-change history: [`CHANGELOG.md`](CHANGELOG.md). Lua symbol lookup: [`SYMBOLS.md`](SYMBOLS.md).

## Where to start reading

| If you want… | Open |
|---|---|
| The 5-minute pitch | [`content/notebook/quickstart.md`](content/notebook/quickstart.md) |
| A high-level orientation to the repo (file map, pipelines, conventions) | [`agents.md`](agents.md) → [`docs/agents/`](docs/agents/README.md) |
| The canonical rules and design intent | [`docs/design/`](docs/design/README.md) (split by topic; indexed from [`StarveNoMoreDesignConcept.md`](StarveNoMoreDesignConcept.md)) |
| What changed, per design batch | [`CHANGELOG.md`](CHANGELOG.md) |
| The blind-playtest protocol | [`playtest/facilitator_script.md`](playtest/facilitator_script.md) |

## Repository layout

```
StarveNoMore/
├── lua/         TTS Lua scripts (concatenated by build_save.py into the save JSON).
│                Eight are auto-generated from content/ + sounds/: audio_manifest,
│                whatnow_hints, market_data, threat_types, recipe_data, notebook_data,
│                character_briefings, achievement_data.
├── xml/         TTS UI XML — Phase Banner, Action Bar, Help panel, modal dialogs.
├── content/     Card CSVs (cards_*.csv), in-game text (notebook/, help/),
│                iconography, asset manifest. The CSV + Markdown files here are
│                the source of truth for cards, rules text, hints, and audio metadata.
├── art/         Image assets — boards, tiles, decks, tokens, characters, bosses.
│                Card illustrations live under art/decks/illustrations/;
│                atlas_manifest.json records each deck's rendered grid.
├── sounds/      Local sound assets — ambient/{suburban,varied,night}, creatures/<boss>/,
│                sfx/. Served by scripts/serve_art.bat over :8080 during play.
├── scripts/     Build + asset/data generation + balance sim + telemetry analyzer.
├── playtest/    Blind-playtest kit: facilitator script, feedback form, sessions/ logs.
├── saves/       Built TTS save (+ fixtures/ frozen mid-game save for compat tests).
├── tests/       pytest suite (~810 tests) — runs the real Lua bundle headlessly,
│                plus XML/color/lint quality gates and publish-build checks.
└── Archive/     Superseded design / reference docs (frozen, no live links).
```

See [`docs/agents/file-structure.md`](docs/agents/file-structure.md) for the file-by-file breakdown.

## What's implemented

- **Gameplay loop** — Setup walkthrough (with optional variants: Rotation turns, random Scenario, and a **mode selector** — three difficulties on the full 7-day arc, Story / Standard / Nightmare, plus Long Weekend as a 3-day *length*; also **Secret Dusk** and **Solo**), Day/Dusk/Night/Tick state machine, combat resolution with **Press the Attack** (pay Sanity to keep rolling), **boss rewards** (Doom rebates, loot showers, build-around Trophies), crafting/cooking, doom track + threshold effects, victory/defeat conditions (The Source is mandatory), Down/ghost state, an end-of-game **Week in Review** chronicle, save/load persistence with schema migration.
- **The climax & character identity (batch 2)** — **Nothing Left to Lose** (Doom 25 flips from pure penalty to a last-stand buff: +1 attack die for all, Rest heals anywhere), a once-per-game **Signature Move** for every character (All-Nighter / Touch of Hope / Posterize / The Feast / The Speech, each with its own button and confirm), the **Source's phase beat** (script-tracked boss HP; at 5 HP two Terror Beaks split off), and the fixed **Last Dawn** on the final day.
- **Mid-week texture & dread (batch 3)** — **Night Sounds** (a low growl at Dusk when the top Threat card is Hard — deliberately unexplained), **Dawn Dares** (optional temptations on early-week cards, offered never imposed), the coded **Pry** verb with sealed threats and the always-present **Sealed Basement** destination, and the **Wrongness token** (a face-down unresolved threat the table argues about visiting).
- **Validation & instrumentation (batch 4)** — session telemetry (setup, per-turn seconds, which designed beats actually fired) with a one-click **Copy Session Log** JSON export, aggregated by `scripts/analyze_sessions.py`; 3-player relief knobs for Rayman pending a table A/B; the blind-playtest facilitator script and feedback form under `playtest/`.
- **Picture-dominant card faces** — every card is `408×585 px` with a top art region (~65%) and a text panel below. Illustrations are produced by ComfyUI (Flux Dev + a Tim-Burton/Edward-Gorey LoRA), composited by `scripts/generate_card_atlases.py`. See [`docs/agents/comfyui.md`](docs/agents/comfyui.md) for the full pipeline.
- **Audio** — random suburban-ambient track at Day start chains into varied tracks until Night; per-boss roar loops while a boss is alive; soft chime at Tick; per-character SFX on walk / meet / trade / death. Single-channel via TTS `MusicPlayer`. Sounds under `sounds/`; manifest auto-generated from the filesystem.
- **"Always obvious next step" UX** — Phase Banner with dynamic next-action text and a pulsing-outline highlight on whichever XML control should be clicked next; a **day-cycle strip** (Dawn ▸ Day ▸ Dusk ▸ Night ▸ Tick, current step lit); a persistent **"Rules in effect" panel** mirroring every rule currently modifying play (Doom thresholds crossed, ongoing Dawn-card effects, loose bosses, per-character statuses like Haunted / Wired / Loud); an always-visible **character roster** showing every party member's live Health / Hunger / Sanity in their character color (plus live standee tooltips on hover); per-deck What-now hints (sub-phase × character × stats × strategic × location) auto-loaded from `content/help/whatnow_hints.md`; auto-broadcasts on critical events (character down, James-no-Energy-Drink, Dusk-alone-at-court, etc.); per-action target highlights with **click-to-complete buttons** (Move → MOVE HERE on adjacent tiles, Craft → CRAFT on Market cards, Cook → COOK on recipes, plus a Trade partner picker and one-step Undo); Market-card affordability glow (Green = you can craft this, Yellow = you can't yet); automated night light checks (Flashlight/Lantern/Fire Kit in hand or by your board, Campfire covers the whole tile); 45-second idle nudge on Day phase.
- **Anti-alpha-player guardrails** — private hand zones, soft turn-time signals, ghost-word-limit, reciprocal trades, and an optional **Secret Dusk** commitment (§11.3) that removes the alpha's ability to confirm compliance. Graded honestly in §19.5: two and a half of the original five fronts hold up.

## Building

Requires Python 3 with `Pillow`. Card illustrations and board scenes need a local [ComfyUI](https://github.com/comfyanonymous/ComfyUI) instance running on `http://127.0.0.1:8000` with `flux1-dev-Q8_0.gguf` + `c4r1mj34.safetensors` LoRA. Character standee art under `art/characters/` is **hand-drawn** and is intentionally skipped by the ComfyUI generator and the sync helper.

### What each script does

| Script | Reads | Writes | Purpose |
|---|---|---|---|
| `scripts/build_save.py` | every file listed in `LUA_LOAD_ORDER`, the `XML_LOAD_ORDER` files under `xml/` (hud / setup / dialogs), `art/decks/atlas_manifest.json` | `saves/StarveNoMore.json` + `saves/StarveNoMore.pretty.json` (dev) or `saves/StarveNoMore.publish.json` (`--publish BASE_URL`) | The final assembly step. Concatenates the Lua bundle (53 files today) and the XML into one TTS save JSON, spawns the table objects (board, decks, tokens, player boards, character standees with per-character holder colors, the Sealed Basement, the Player Rules tablet, etc.), reading deck grid dimensions from the atlas manifest (hard-stops if atlases are stale), and pretty-prints a copy for diffing. `--publish` rewrites every `file:///`/`localhost` asset URL to a hosted base and writes a separate shareable save. Run this last after any change to Lua, XML, or auto-generated data tables. |
| `scripts/generate_threat_types.py` | `content/cards_threats.csv` | `lua/threat_types.lua` | Emits `THREAT_TYPE_BY_NAME` (nickname → Hard/Soft/Persistent, used by the Night Sounds dusk peek — a face-down deck only exposes nicknames) and `SEALED_REWARDS` (from the structured `pry_reward` column, consumed by `doPry`). Re-run after editing the threats CSV. |
| `scripts/generate_recipe_data.py` | `content/cards_recipes.csv` | `lua/recipe_data.lua` | Emits `RECIPE_DATA` from the structured `script` column (`allAtTile=hunger:4+sanity:2\|cookPenalty=health:2\|...`), so the card face text and what `doCook` actually does can never drift apart. Re-run after editing recipes. |
| `scripts/generate_notebook.py` | `content/notebook/*.md`, `content/help/glossary.md` | `lua/notebook_data.lua` | Converts the player-doc markdown to plain text and emits the in-game Notebook tabs (Quick Start / Full Rules / Characters) and Help-panel Quick Start + Glossary constants. `build_save.py` imports its `md_to_text` for the physical Quick Start notecard — one source, every surface. |
| `scripts/generate_player_rules.py` | `content/notebook/*.md`, `content/help/glossary.md` | `PlayerRules.md` + `PlayerRules.html` | The player rulebook, assembled from the same markdown as the Notebook (Quick Start → Full Rules → Characters → Glossary). The HTML is a self-contained styled page: the in-TTS **Player Rules tablet** loads it from `http://localhost:8080/PlayerRules.html` (start `scripts/serve_art.bat`), and the same file opens in any desktop browser. Re-run after editing the notebook/glossary markdown. |
| `scripts/generate_symbol_index.py` | `lua/*.lua` (in `LUA_LOAD_ORDER` order) | `SYMBOLS.md`, `.luacheckrc` | The Lua bundle's table of contents: every global function/constant with file and line, plus a luacheck config whose globals list is generated from the bundle itself. Re-run after any Lua change (a freshness test enforces it). |
| `scripts/generate_achievement_data.py` | `content/achievements.csv` | `lua/achievement_data.lua`, `steam/achievements.json` | The achievement roster in both shapes: the in-game table (name, description, category, hidden flag, icon asset name) and a Steamworks-shaped manifest for a future standalone app. The unlock *conditions* are deliberately not generated — they are hand-written predicates in `lua/achievement_rules.lua`, and a test fails if the two lists disagree. See [`docs/achievements.md`](docs/achievements.md). |
| `scripts/generate_achievement_icons.py` | `content/achievements.csv`, `art/achievements/src/<base>.png` (ComfyUI renders, when present) | `art/achievements/<base>.png` (256px, in-game), `art/achievements/steam/<base>.jpg` + `_gray.jpg` | Square-crops, vignettes and frames each render into the sizes the mod and Steamworks want. With no render present it emits a procedural placeholder in the game's palette instead, so the panel and the test suite stay green before the art exists — and upgrades automatically once the render lands. `--only <id>`, `--force`. |
| `scripts/analyze_sessions.py` | `playtest/sessions/*.json` (Copy Session Log exports) | console report | Aggregates playtest telemetry into the tables the validation gates need: win rate by difficulty/player count, loss-day histogram, median turn seconds by turn style (the Rotation A/B verdict), and how often the designed beats (presses, Signatures, the Source split, dares) actually fire at real tables. |
| `scripts/generate_audio_manifest.py` | `sounds/ambient/{suburban,varied}/`, `sounds/creatures/<boss>/`, `sounds/sfx/` | `lua/audio_manifest.lua` | Walks the `sounds/` tree, computes each track's duration (precise for `.wav` via the stdlib `wave` module; estimated from filesize for `.mp3`), and emits a Lua table with `{url, duration, name}` entries grouped under `AUDIO.AMBIENT_SUBURBAN / AMBIENT_VARIED / CREATURES.<boss> / SFX.<key>`. Re-run after adding or removing any sound file. |
| `scripts/generate_whatnow_hints.py` | `content/help/whatnow_hints.md` | `lua/whatnow_hints.lua` | Parses the markdown source-of-truth for context-aware hints into a single `WHATNOW_HINTS` Lua table with 15 groups (PreGame, Dawn, Day, Stats, James, Coco, Rayman, Ellie, Luca, Location, Strategic, Dusk, Night, Tick, PostGame). Re-run after editing the markdown. |
| `scripts/generate_market_data.py` | `content/cards_market.csv`, `content/cards_starting.csv` | `lua/market_data.lua` | Tokenises each Market card's `cost` column ("2 Metal + 1 Wood", "Energy Drink", etc.) into a Lua sub-table — `MARKET_COSTS[<id>] = {Metal=2, Wood=1, ...}` — driving the in-game affordability glow. Also parses "+N Attack die" from both CSVs' effect text into `WEAPON_DICE`, so combat rolls printed weapon bonuses automatically. Body-cost terms (Health, Sanity) are intentionally omitted. Re-run after editing card costs/effects. |
| `scripts/generate_card_atlases.py` | `content/cards_*.csv` (rows + text), `art/decks/illustrations/<card_id>.png` (one per card if present) | `art/decks/{phase1..4,market,recipe,threat,visitor,trophy,starting}_face.jpg` + `_back.png` (10 face atlases + 10 backs) | Renders every card face as `408×585 px` with a top-art region (`~380 px`, full-bleed illustration cover-cropped from the per-card PNG) and a bottom text panel (title + severity dots + cost + effect, in the deck-specific accent color). Falls back to a flat color rectangle for any missing illustration so partial generations still build. Run after illustrations change or text edits. |
| `scripts/generate_assets.py` | `content/iconography.md` (icon list, in code) | `art/tokens/`, `art/icons/`, `art/legend/severity_legend.png`, `art/characters/board_*.png`, `art/board/main_board.png` | Pure-Pillow renderer for non-illustrated assets: 6 resource tokens, 3 stat marker tokens, Doom marker, Telltale Heart token, Sanity d8 face texture, severity legend card, 5 player boards, and the main board with the 31-step Doom track + threshold ribbons baked in. No AI involved. |
| `scripts/generate_cover.py` | `art/characters/coco_front.png` | `saves/StarveNoMore.png` | The save's cover art: Coco's hand-drawn front standee centered on a night-suburb backdrop with the title. TTS's Save & Load browser shows the same-basename PNG beside a save as its thumbnail; `iwanttoplay` copies it alongside the save. Deterministic — re-run only when the cover should change. |
| `scripts/generate_comfyui_assets.py` | `content/cards_*.csv` (for per-card prompts via the `art_notes` column), the in-script board/tile/boss prompt list | ComfyUI server queue (PNGs eventually appear in ComfyUI's `output/`) | Builds a 10-node Flux GGUF + LoRA workflow per asset (`UnetLoaderGGUF` → `DualCLIPLoader` → `LoraLoader` at strength 0.85 → CLIP encode → `EmptyLatentImage` → `KSampler` (euler, 30 steps, CFG 4.0) → `VAEDecode` → `SaveImage`) and POSTs them to `http://127.0.0.1:8000/prompt`. Fire-and-forget; the script gets a `prompt_id` back per request and exits without polling. Locked DST + modern-suburban style prefix is appended to every prompt. Also queues the 24 achievement icons from `content/achievements.csv` (`art_notes` again, wrapped in an icon-specific framing rather than the card one — one centred object on a dark field, so it still reads at 64 px). Useful flags: `--cards-only`, `--no-cards`, `--deck <name>` (repeatable), `--only <card_id>`, `--achievements-only`, `--no-achievements`, `--skip-existing`. Character standees are excluded by design. |
| `scripts/sync_comfyui_output.py` | `c:\Users\GGPC\Documents\ComfyUI\output\snm_*_00001_.png` | `art/decks/illustrations/<id>.png`, `art/tiles/<base>.png`, `art/board/<base>.png`, `art/bosses/<base>.png`, `art/achievements/src/<base>.png` | Idempotent copier that strips ComfyUI's `_00001_` suffix from generated PNGs and routes each to the right `art/` subdirectory based on its `snm_<category>_` prefix. Skips `snm_char_*` (hand-drawn) and skips files whose destination is already newer than the source. `--dry-run` to preview, `--force` to overwrite. |
| `scripts/serve_art.bat` | the repo root | (HTTP responses on `:8080`) | Starts `python -m http.server 8080` rooted at the repo so `http://localhost:8080/art/...` and `http://localhost:8080/sounds/...` both resolve during local development. Required while playing in TTS — the URLs in `lua/assets.lua` and `lua/audio_manifest.lua` point here. Keep the window open. |
| `scripts/simulate_balance.py` | (self-contained; constants mirror the design doc) | console report | Monte Carlo balance probe: simulates the 7-day loop with scripted team policies (turtle / spread / balanced / court_camper) and reports win rates, loss causes, Doom, downs, and festering threats. `--rules old` replays the pre-2026-07 ruleset for before/after comparison; `--trace` prints one game day-by-day. A dynamics probe, not a rules engine — assumptions are documented in its docstring. |

### Typical command order

```bash
# 1. After editing source data (CSVs, hints markdown, sounds), regenerate the Lua data tables:
python scripts/generate_audio_manifest.py
python scripts/generate_whatnow_hints.py
python scripts/generate_market_data.py
python scripts/generate_threat_types.py
python scripts/generate_recipe_data.py
python scripts/generate_notebook.py       # in-game Notebook/Help text from content/*.md
python scripts/generate_achievement_data.py  # achievement roster + steam/achievements.json
python scripts/generate_player_rules.py   # PlayerRules.md + PlayerRules.html from the same markdown
python scripts/generate_symbol_index.py   # after any lua/ change (SYMBOLS.md + .luacheckrc)

# 2. After adding new card illustrations to ComfyUI: queue, wait, sync.
python scripts/generate_comfyui_assets.py --skip-existing
#   ... wait for ComfyUI to drain the queue ...
python scripts/sync_comfyui_output.py

# 3. Composite card faces (always safe to re-run; missing art falls back to color blocks).
python scripts/generate_card_atlases.py

# 3b. Crop/frame the achievement icons (placeholders where no art exists yet).
#     Full run book: docs/comfyui-achievement-icons.md
python scripts/generate_achievement_icons.py

# 4. (Rare) regenerate non-illustrated art if the icon set or board layout changed.
python scripts/generate_assets.py

# 5. Build the TTS save.
python scripts/build_save.py
```

## Loading in Tabletop Simulator

> If you changed source data under `content/` or `sounds/` (hints markdown, market CSV, sound files), run the matching generator scripts first — see [Typical command order](#typical-command-order). A fresh clone can skip this: the generated Lua tables are committed.

1. Run `python scripts/build_save.py`.
2. Copy `saves/StarveNoMore.json` to your TTS saves folder
   (`%USERPROFILE%\Documents\My Games\Tabletop Simulator\Saves\` on Windows).
3. Start the local asset server: `scripts/serve_art.bat` — serves the repo root
   over `http://localhost:8080` so `/art/...`, `/sounds/...` and
   `/PlayerRules.html` all resolve.
4. In TTS, *Games → Save & Load*, select the save, and click **Setup Game** on the table.
5. Rules are on the table: the **Player Rules tablet** (bottom-right) shows the
   full rulebook in-game; the same page is `PlayerRules.html` in any browser
   (or `http://localhost:8080/PlayerRules.html` while the server runs).

To share a save beyond this machine, host the repo's `art/`, `sounds/` and
`PlayerRules.html` somewhere public and build with
`python scripts/build_save.py --publish https://your.host/starvenomore`.

## Design pillars

The five non-negotiables every rule must serve:

1. **Tone over polish** — coherent gothic-cartoon visual identity over asset volume.
2. **Decisions paid in mismatched currencies** — every action costs in a stat *adjacent* to the one it fills.
3. **The world acts first** — every round opens with a hostile Dawn card.
4. **Specialization beats parallelism** — characters are rule-distinct, not stat-distinct.
5. **Emergent stories, not scripted narrative** — systems interact; players write the lore.

Plus one operational pillar:

6. **Playable on first sit-down without reading rules** — Phase Banner, What-now hints, target highlights, auto-broadcasts on urgent states. The UX program in design `§18.10–18.19` is part of v1, not polish (§18.19 is the accessibility floor: no colour-only distinctions, every audio cue visually twinned, stated type-size and contrast minimums).

## Reference

The canonical design and rules live in [`StarveNoMoreDesignConcept.md`](StarveNoMoreDesignConcept.md). The repository's `Archive/` directory holds the original commission brief, the early build checklist, and the design-theory sources (DST, board-game theory, related-games tear-downs) that informed the design — they're frozen and no longer linked from the live documentation.
