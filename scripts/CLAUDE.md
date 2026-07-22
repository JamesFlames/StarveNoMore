# scripts/ — build & generators

Python build pipeline. `build_save.py` is the single source of truth for what
gets packaged into the TTS save (`LUA_LOAD_ORDER` + `XML_LOAD_ORDER` + spawned
objects). The rest are generators (source → output) plus the standalone
`simulate_balance.py` (Monte Carlo, **not** on the build path).

The build load order (`lua[]` + `xml[]`) is data: [`load_order.json`](load_order.json).
The generator map below is mirrored machine-readably in [`generators.json`](generators.json)
(a freshness test keeps the two honest).

## Generator map — "what do I regenerate after editing X?"

| Edit this source | Run this generator | It writes |
|---|---|---|
| `sounds/…` | `generate_audio_manifest.py` | `lua/audio_manifest.lua` |
| `content/help/whatnow_hints.md` | `generate_whatnow_hints.py` | `lua/whatnow_hints.lua` |
| `content/cards_market.csv` + `cards_starting.csv` | `generate_market_data.py` | `lua/market_data.lua` |
| `content/cards_threats.csv` | `generate_threat_types.py` | `lua/threat_types.lua` |
| `content/cards_recipes.csv` | `generate_recipe_data.py` | `lua/recipe_data.lua` |
| `content/notebook/*.md` + `help/glossary.md` | `generate_notebook.py` | `lua/notebook_data.lua` |
| `content/notebook/*.md` + `help/glossary.md` | `generate_player_rules.py` | `PlayerRules.md` + `.html` |
| **any** `lua/*.lua` | `generate_symbol_index.py` | `SYMBOLS.md` + `.luacheckrc` |

Generators are idempotent and order-independent; `tests/test_generated_freshness.py`
fails if any output is stale. After regenerating, run `python scripts/build_save.py`.

**Or just run everything:** `python scripts/regenerate_all.py` runs every
generator (in manifest order) then `build_save.py` — one command instead of
remembering which generator matches your edit. It reads `generators.json`, so it
can't drift; generators whose sources are absent (e.g. `sounds/` on a clean
clone) are skipped rather than erroring. `--no-build` / `--list` are available.

## Debug / deploy tools (not generators)

- `inspect_save.py` — read any TTS save like a debugger: `--live` (newest
  autosave: gameState + object positions), `--band` (objects sunk in the
  tabletop), `--error N` (decode an in-TTS `<Global:N>` error to
  `lua/<file>:<line>`). See [`../docs/debugging.md`](../docs/debugging.md).
- `iwanttoplay.py` — regen → build → test → install save → **purge this
  mod's stale TTS asset cache** → asset server → launch TTS.

## Conventions

- **File-size budget:** if a file passes ~500 lines, split it before adding more.
- Never hand-edit a generated `lua/*.lua`; edit its source and rerun the generator.
- Full pipeline + asset/ComfyUI details: [`agents.md`](../agents.md).
