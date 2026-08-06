# Architecture

How the mod is assembled: the build pipeline, the single Lua namespace, and the load-order rule that follows from it.

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

## Runtime
- **Engine**: Tabletop Simulator (MoonSharp Lua 5.2, XML UI, JSON saves)
- **Object lookup**: Tag-based (never GUID)
- **Save format**: Single JSON file with embedded Lua + XML

## Build Pipeline
- `scripts/build_save.py` — Concatenates the Lua files in `LUA_LOAD_ORDER` + the `XML_LOAD_ORDER` files under `xml/` (hud / setup / dialogs) into the TTS save JSON. **Both load orders live in [`scripts/load_order.json`](../../scripts/load_order.json)** (`lua[]` + `xml[]`), a small machine-readable manifest build_save.py, `conftest.py`, and `generate_symbol_index.py` all read — so the build order is a diffable data file, not buried in the script. Deck `NumWidth/NumHeight` come from `art/decks/atlas_manifest.json` (written by the atlas generator; a card-count mismatch is a hard stop — rerun the atlas generator). `--publish BASE_URL [--out path]` writes a separate shareable save with every `file:///`/`localhost` asset URL rewritten to the hosted base (refuses to write if any local URL survives).
- Six of the Lua files in that list are **auto-generated** and should never be edited by hand:
  - `lua/audio_manifest.lua`  — built by `scripts/generate_audio_manifest.py` from the `sounds/` tree
  - `lua/whatnow_hints.lua`   — built by `scripts/generate_whatnow_hints.py` from `content/help/whatnow_hints.md`
  - `lua/market_data.lua`     — built by `scripts/generate_market_data.py` from `content/cards_market.csv` + `cards_starting.csv` (`MARKET_COSTS` for affordability + `WEAPON_DICE` parsed from "+N Attack die" effect text)
  - `lua/threat_types.lua`    — built by `scripts/generate_threat_types.py` from `content/cards_threats.csv` (`THREAT_TYPE_BY_NAME` for the Night Sounds peek + `SEALED_REWARDS` from the `pry_reward` column)
  - `lua/recipe_data.lua`     — built by `scripts/generate_recipe_data.py` from `content/cards_recipes.csv` (`RECIPE_DATA` from the structured `script` column)
  - `lua/notebook_data.lua`   — built by `scripts/generate_notebook.py` from `content/notebook/*.md` + `content/help/glossary.md` (the in-game Notebook tabs and Help-panel text)
- Two repo-root files are also generated: `SYMBOLS.md` + `.luacheckrc` — built by `scripts/generate_symbol_index.py` from `lua/` (rerun after any Lua change).
- Run those generators after editing the corresponding source, then `python scripts/build_save.py`. All generators are idempotent and order-independent; `tests/test_generated_freshness.py` fails if any output is stale.

## Asset Pipeline
- `scripts/generate_card_atlases.py` — Composites card faces from per-card illustrations + text panel; writes deck atlases to `art/decks/*.png`
- `scripts/generate_assets.py` — Renders tokens, boards, player boards, legends via Pillow
- `scripts/generate_cover.py` — Renders `saves/StarveNoMore.png` (Coco's front standee on a night-suburb backdrop), **1024×1024** — the Save & Load browser fits the thumbnail to a square tile's width, so a 16:9 cover wasted half the tile. A same-basename PNG beside the save is the cover art TTS shows in that browser; `iwanttoplay` copies it with the save. Deterministic; rerun only when the cover should change.
- `scripts/generate_comfyui_assets.py` — Queues board + per-card illustration prompts to local ComfyUI (Flux Dev). Hero art is intentionally excluded: character standees (hand-drawn) and the three house tiles (authored outside the pipeline).
- `scripts/sync_comfyui_output.py` — Copies ComfyUI's `output/snm_*_00001_.png` into the matching `art/<subdir>/<base>.png` (idempotent)
- `scripts/normalize_tile_art.py` — Derives `art/tiles/<name>_tile.png`: the largest square centred on the *content* of the source, so the disc TTS cuts is centred and free of letterbox bars. **`ASSET_MAP` points at the `_tile` files, not the sources** — skip this and new location art simply never reaches the table.
- `scripts/normalize_standee_art.py` — Derives `art/characters/<name>_standee.png`: cuts the backdrop to transparent (opt-in per character via `CUT_BACKGROUND`) and fits every figure to a common 512×1024. **`ASSET_MAP` points at the `_standee` files.** Why both exist: [`derived-art.md`](derived-art.md).
- `scripts/simulate_balance.py` — Monte Carlo balance probe (policies × rulesets; `--rules old` for pre-fix comparison, `--trace` for a day-by-day log). Standalone; not part of the build.
- Card data CSVs: `content/cards_phase1.csv` … `cards_phase4.csv`, plus `cards_market.csv`, `cards_recipes.csv`, `cards_threats.csv`, `cards_visitors.csv`, `cards_trophies.csv`, `cards_scenarios.csv`, and `locations.csv`, `resources.csv`, `tooltips.csv`
- Output images: `art/decks/`, `art/decks/illustrations/`, `art/tokens/`, `art/icons/`, `art/board/`, `art/characters/`, `art/legend/`, `art/tiles/`, `art/bosses/`, `art/ui/`
