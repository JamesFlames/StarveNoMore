# CLAUDE.md — start here

**For any task:** (1) find the file via [`TASKMAP.md`](TASKMAP.md) or [`SYMBOLS.md`](SYMBOLS.md),
(2) open only that file, (3) regenerate + `python -m pytest tests` before you finish.

## What this is

**Starve No More** is a cooperative survival board game built as a Tabletop
Simulator (TTS) mod: 5 teenagers survive 7 days against escalating cosmic horror
(3-stat economy, Doom track, day/night cycle, Dawn card events). The mod is a
single TTS save JSON assembled from Lua (`lua/`) + XML UI (`xml/`) + card data
(`content/`) by `scripts/build_save.py`. Lua files share one global namespace —
there are no `require`s; load order is the explicit `LUA_LOAD_ORDER` in
`build_save.py`.

## Finding the right file

- **"Where do I change X?"** → [`TASKMAP.md`](TASKMAP.md) (job → files to open).
- **"Where is function/constant X?"** → grep [`SYMBOLS.md`](SYMBOLS.md)
  (function → `file:line`) *before* opening source. One lookup instead of N greps.
- **Deep reference** (architecture, conventions, pipelines) → [`agents.md`](agents.md).
- **Rules/design questions** → [`docs/design/`](docs/design/README.md) (split by
  topic), indexed from [`StarveNoMoreDesignConcept.md`](StarveNoMoreDesignConcept.md).

## Build & test

```bash
pip install pytest lupa Pillow      # lupa runs the real Lua bundle headlessly
python -m pytest tests              # ~305 tests; green = safe to build
python scripts/build_save.py        # assemble saves/StarveNoMore.json
```

Per-directory `CLAUDE.md` files (`lua/`, `scripts/`, `tests/`, `content/`) carry
local conventions + the "regenerate after edit" rule for that directory.

## Never hand-edit (auto-generated)

Each carries an `AUTO-GENERATED` banner; regenerate its source instead:

- `lua/audio_manifest.lua`, `lua/whatnow_hints.lua`, `lua/market_data.lua`,
  `lua/threat_types.lua`, `lua/recipe_data.lua`, `lua/notebook_data.lua`
- `SYMBOLS.md` + `.luacheckrc` — `python scripts/generate_symbol_index.py`
  (rerun after **any** `lua/` change; a freshness test enforces it).

Which generator rebuilds what → the table in [`scripts/CLAUDE.md`](scripts/CLAUDE.md).
