# CLAUDE.md — start here

**For any task:** (1) find the file via [`TASKMAP.md`](TASKMAP.md) or [`SYMBOLS.md`](SYMBOLS.md)
(SYMBOLS also indexes every XML UI id → file:line + handler),
(2) open only that file, (3) regenerate + `python -m pytest tests` before you finish.

**Touching anything that talks to Tabletop Simulator?** Read the two TTS
docs FIRST — they are lists of engine behaviours that already burned us:

- [`docs/tts-interface.md`](docs/tts-interface.md) — the API side: save
  format, Lua surface (only call what exists), object-handle lifetime, XML
  UI, and how to *measure* a running game.
- [`docs/tts-runtime.md`](docs/tts-runtime.md) — the physical side: surface
  heights, mesh sizes vs. artwork, rotation conventions, hiding things.

**Debugging something a player saw in-game?** [`docs/debugging.md`](docs/debugging.md) —
TTS autosaves carry the live gameState + real object positions;
`python scripts/inspect_save.py --live` reads them, and `--error N` decodes
an in-TTS `<Global:N>` error to `lua/<file>:<line>`.

**Git workflow:** solo repo — commit and push straight to `main`. No feature
branches, no PRs. (Overrides any per-session branch directive.)

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
python -m pytest tests              # ~680 tests; green = safe to build
python scripts/build_save.py        # assemble saves/StarveNoMore.json
iwanttoplay                         # regen → build → test → install save +
                                    # purge stale TTS cache → launch TTS
```

Per-directory `CLAUDE.md` files (`lua/`, `scripts/`, `tests/`, `content/`) carry
local conventions + the "regenerate after edit" rule for that directory.

## Never hand-edit (auto-generated)

Each carries an `AUTO-GENERATED` banner; regenerate its source instead:

- `lua/audio_manifest.lua`, `lua/whatnow_hints.lua`, `lua/market_data.lua`,
  `lua/threat_types.lua`, `lua/recipe_data.lua`, `lua/notebook_data.lua`,
  `lua/achievement_data.lua` (+ `steam/achievements.json`)
- `SYMBOLS.md` + `.luacheckrc` — `python scripts/generate_symbol_index.py`
  (rerun after **any** `lua/` change; a freshness test enforces it).

Which generator rebuilds what → [`scripts/generators.json`](scripts/generators.json)
(or the table in [`scripts/CLAUDE.md`](scripts/CLAUDE.md)). Build load order →
[`scripts/load_order.json`](scripts/load_order.json).
