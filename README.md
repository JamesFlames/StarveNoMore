# Starve No More

A cooperative survival board game for 3–5 players, built as a [Tabletop Simulator](https://store.steampowered.com/app/286160/Tabletop_Simulator/) mod. Suburban friends caught when something cosmic descends on their neighborhood must scavenge, cook, fight, and hold their sanity together for seven nights. Tone modeled on *Don't Starve Together*; mechanical DNA drawn from DST, *Hogwarts Battle*, *Catan*, and *Cthulhu Wars*.

> **Status:** pre-playtest. The design is locked in [`StarveNoMoreDesignConcept.md`](StarveNoMoreDesignConcept.md); the Lua/XML scaffold (gameplay loop, UX, audio, atlas pipeline) is in place; card-art generation runs against a local ComfyUI instance. Not yet blind-tested with a fresh group.

## Dev quickstart

```bash
pip install pytest lupa Pillow      # lupa runs the real Lua bundle headlessly
python -m pytest tests              # ~250 tests; green = safe to build
python scripts/build_save.py        # assemble saves/StarveNoMore.json
```

Everything else — pipelines, conventions, the file map — is in [`agents.md`](agents.md). Rule-change history: [`CHANGELOG.md`](CHANGELOG.md). Lua symbol lookup: [`SYMBOLS.md`](SYMBOLS.md).

## Where to start reading

| If you want… | Open |
|---|---|
| The 5-minute pitch | [`content/notebook/quickstart.md`](content/notebook/quickstart.md) |
| A high-level orientation to the repo (file map, pipelines, conventions) | [`agents.md`](agents.md) |
| The canonical rules and design intent | [`StarveNoMoreDesignConcept.md`](StarveNoMoreDesignConcept.md) |
| What changed, per design batch | [`CHANGELOG.md`](CHANGELOG.md) |
| The blind-playtest protocol | [`playtest/facilitator_script.md`](playtest/facilitator_script.md) |

## Repository layout

```
StarveNoMore/
├── lua/         TTS Lua scripts (concatenated by build_save.py into the save JSON).
│                Includes auto-generated audio_manifest.lua, whatnow_hints.lua,
│                and market_data.lua — all built from sources under content/ + sounds/.
├── xml/         TTS UI XML — Phase Banner, Action Bar, Help panel, modal dialogs.
├── content/     Card CSVs (cards_*.csv), in-game text (notebook/, help/),
│                iconography, asset manifest. The CSV + Markdown files here are
│                the source of truth for cards, hints, and audio metadata.
├── art/         Image assets — boards, tiles, decks, tokens, characters, bosses.
│                Card illustrations live under art/decks/illustrations/.
├── sounds/      Local sound assets — ambient/{suburban,varied}, creatures/<boss>/,
│                sfx/. Served by scripts/serve_art.bat over :8080 during dev.
├── scripts/     Build + asset-generation Python scripts.
├── saves/       Built TTS save (StarveNoMore.json + pretty-printed copy).
└── Archive/     Superseded design / reference docs (frozen, no live links).
```

See [`agents.md`](agents.md) for the file-by-file breakdown.

## What's implemented

- **Gameplay loop** — Setup walkthrough (with optional variants: Rotation turns, random Scenario), Day/Dusk/Night/Tick state machine, combat resolution with **Press the Attack** (pay Sanity to keep rolling), **boss rewards** (Doom rebates, loot showers, build-around Trophies), crafting/cooking, doom track + threshold effects, victory/defeat conditions (The Source is mandatory), Down/ghost state, an end-of-game **Week in Review** chronicle, save/load persistence.
- **Picture-dominant card faces** — every card is `408×585 px` with a top art region (~65%) and a text panel below. Illustrations are produced by ComfyUI (Flux Dev + a Tim-Burton/Edward-Gorey LoRA), composited by `scripts/generate_card_atlases.py`. See [`agents.md`](agents.md) "ComfyUI Workflow" for the full pipeline.
- **Audio** — random suburban-ambient track at Day start chains into varied tracks until Night; per-boss roar loops while a boss is alive; soft chime at Tick; per-character SFX on walk / meet / trade / death. Single-channel via TTS `MusicPlayer`. Sounds under `sounds/`; manifest auto-generated from the filesystem.
- **"Always obvious next step" UX** — Phase Banner with dynamic next-action text and a pulsing-outline highlight on whichever XML control should be clicked next; a **day-cycle strip** (Dawn ▸ Day ▸ Dusk ▸ Night ▸ Tick, current step lit); a persistent **"Rules in effect" panel** mirroring every rule currently modifying play (Doom thresholds crossed, ongoing Dawn-card effects, loose bosses, per-character statuses like Haunted / Wired / Loud); an always-visible **character roster** showing every party member's live Health / Hunger / Sanity in their character color (plus live standee tooltips on hover); per-deck What-now hints (sub-phase × character × stats × strategic × location) auto-loaded from `content/help/whatnow_hints.md`; auto-broadcasts on critical events (character down, James-no-Energy-Drink, Dusk-alone-at-court, etc.); per-action target highlights with **click-to-complete buttons** (Move → MOVE HERE on adjacent tiles, Craft → CRAFT on Market cards, Cook → COOK on recipes, plus a Trade partner picker and one-step Undo); Market-card affordability glow (Green = you can craft this, Yellow = you can't yet); automated night light checks (Flashlight/Lantern/Fire Kit in hand or by your board, Campfire covers the whole tile); 45-second idle nudge on Day phase.
- **Anti-alpha-player guardrails** — private hand zones, soft turn-time signals, ghost-word-limit, reciprocal trades.

## Building

Requires Python 3 with `Pillow`. Card illustrations and board scenes need a local [ComfyUI](https://github.com/comfyanonymous/ComfyUI) instance running on `http://127.0.0.1:8000` with `flux1-dev-Q8_0.gguf` + `c4r1mj34.safetensors` LoRA. Character standee art under `art/characters/` is **hand-drawn** and is intentionally skipped by the ComfyUI generator and the sync helper.

### What each script does

| Script | Reads | Writes | Purpose |
|---|---|---|---|
| `scripts/build_save.py` | every file listed in `LUA_LOAD_ORDER`, plus `xml/global_ui.xml` | `saves/StarveNoMore.json` + `saves/StarveNoMore.pretty.json` | The final assembly step. Concatenates the 21 Lua files and the XML into one TTS save JSON, spawns the table objects (board, decks, tokens, player boards, character standees with per-character holder colors, etc.), and pretty-prints a copy for diffing. Run this last after any change to Lua, XML, or auto-generated data tables. |
| `scripts/generate_audio_manifest.py` | `sounds/ambient/{suburban,varied}/`, `sounds/creatures/<boss>/`, `sounds/sfx/` | `lua/audio_manifest.lua` | Walks the `sounds/` tree, computes each track's duration (precise for `.wav` via the stdlib `wave` module; estimated from filesize for `.mp3`), and emits a Lua table with `{url, duration, name}` entries grouped under `AUDIO.AMBIENT_SUBURBAN / AMBIENT_VARIED / CREATURES.<boss> / SFX.<key>`. Re-run after adding or removing any sound file. |
| `scripts/generate_whatnow_hints.py` | `content/help/whatnow_hints.md` | `lua/whatnow_hints.lua` | Parses the markdown source-of-truth for context-aware hints into a single `WHATNOW_HINTS` Lua table with 15 groups (PreGame, Dawn, Day, Stats, James, Coco, Rayman, Ellie, Luca, Location, Strategic, Dusk, Night, Tick, PostGame). Re-run after editing the markdown. |
| `scripts/generate_market_data.py` | `content/cards_market.csv` | `lua/market_data.lua` | Tokenises each Market card's `cost` column ("2 Metal + 1 Wood", "Energy Drink", etc.) into a Lua sub-table — `MARKET_COSTS[<id>] = {Metal=2, Wood=1, ...}`. Drives the in-game affordability glow on the Market display. Body-cost terms (Health, Sanity) are intentionally omitted. Re-run after editing market costs. |
| `scripts/generate_card_atlases.py` | `content/cards_*.csv` (rows + text), `art/decks/illustrations/<card_id>.png` (one per card if present) | `art/decks/{phase1..4,market,recipe,threat,visitor,trophy}_face.png` + `_back.png` (9 face atlases + 9 backs) | Renders every card face as `408×585 px` with a top-art region (`~380 px`, full-bleed illustration cover-cropped from the per-card PNG) and a bottom text panel (title + severity dots + cost + effect, in the deck-specific accent color). Falls back to a flat color rectangle for any missing illustration so partial generations still build. Run after illustrations change or text edits. |
| `scripts/generate_assets.py` | `content/iconography.md` (icon list, in code) | `art/tokens/`, `art/icons/`, `art/legend/severity_legend.png`, `art/characters/board_*.png`, `art/board/main_board.png` | Pure-Pillow renderer for non-illustrated assets: 6 resource tokens, 3 stat marker tokens, Doom marker, Telltale Heart token, Sanity d8 face texture, severity legend card, 5 player boards, and the main board with the 31-step Doom track + threshold ribbons baked in. No AI involved. |
| `scripts/generate_comfyui_assets.py` | `content/cards_*.csv` (for per-card prompts via the `art_notes` column), the in-script board/tile/boss prompt list | ComfyUI server queue (PNGs eventually appear in ComfyUI's `output/`) | Builds a 10-node Flux GGUF + LoRA workflow per asset (`UnetLoaderGGUF` → `DualCLIPLoader` → `LoraLoader` at strength 0.85 → CLIP encode → `EmptyLatentImage` → `KSampler` (euler, 30 steps, CFG 4.0) → `VAEDecode` → `SaveImage`) and POSTs them to `http://127.0.0.1:8000/prompt`. Fire-and-forget; the script gets a `prompt_id` back per request and exits without polling. Locked DST + modern-suburban style prefix is appended to every prompt. Useful flags: `--cards-only`, `--no-cards`, `--deck <name>` (repeatable), `--only <card_id>`, `--skip-existing`. Character standees are excluded by design. |
| `scripts/sync_comfyui_output.py` | `c:\Users\GGPC\Documents\ComfyUI\output\snm_*_00001_.png` | `art/decks/illustrations/<id>.png`, `art/tiles/<base>.png`, `art/board/<base>.png`, `art/bosses/<base>.png` | Idempotent copier that strips ComfyUI's `_00001_` suffix from generated PNGs and routes each to the right `art/` subdirectory based on its `snm_<category>_` prefix. Skips `snm_char_*` (hand-drawn) and skips files whose destination is already newer than the source. `--dry-run` to preview, `--force` to overwrite. |
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
python scripts/generate_symbol_index.py   # after any lua/ change (SYMBOLS.md + .luacheckrc)

# 2. After adding new card illustrations to ComfyUI: queue, wait, sync.
python scripts/generate_comfyui_assets.py --skip-existing
#   ... wait for ComfyUI to drain the queue ...
python scripts/sync_comfyui_output.py

# 3. Composite card faces (always safe to re-run; missing art falls back to color blocks).
python scripts/generate_card_atlases.py

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
   over `http://localhost:8080` so both `/art/...` and `/sounds/...` resolve.
4. In TTS, *Games → Save & Load*, select the save, and click **Setup Game** on the table.

## Design pillars

The five non-negotiables every rule must serve:

1. **Tone over polish** — coherent gothic-cartoon visual identity over asset volume.
2. **Decisions paid in mismatched currencies** — every action costs in a stat *adjacent* to the one it fills.
3. **The world acts first** — every round opens with a hostile Dawn card.
4. **Specialization beats parallelism** — characters are rule-distinct, not stat-distinct.
5. **Emergent stories, not scripted narrative** — systems interact; players write the lore.

Plus one operational pillar:

6. **Playable on first sit-down without reading rules** — Phase Banner, What-now hints, target highlights, auto-broadcasts on urgent states. The UX program in design `§18.10–18.18` is part of v1, not polish.

## Reference

The canonical design and rules live in [`StarveNoMoreDesignConcept.md`](StarveNoMoreDesignConcept.md). The repository's `Archive/` directory holds the original commission brief, the early build checklist, and the design-theory sources (DST, board-game theory, related-games tear-downs) that informed the design — they're frozen and no longer linked from the live documentation.
