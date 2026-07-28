# CLAUDE.md — start here

**For any task:** (1) find the file via [`TASKMAP.md`](TASKMAP.md) or
`python scripts/sym.py NAME` (symbol → `file:line` + signature + call sites),
(2) open only that file, (3) run **`python scripts/check.py`** before you finish
— it regenerates, rebuilds, tests and lints in one command (~22 s).

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
- **"Where is function/constant X?"** → `python scripts/sym.py NAME` — prints
  `file:line`, the signature, the comment above it, and every call site. One
  call instead of a grep plus an open. `--ui ID` for an XML element id,
  `--file night.lua` for everything one file defines.
  [`SYMBOLS.md`](SYMBOLS.md) is the same index as a browsable table; at ~17k
  tokens, read it only if `sym.py` cannot answer.
- **Deep reference** (architecture, conventions, pipelines) → [`agents.md`](agents.md).
- **Rules/design questions** → [`docs/design/`](docs/design/README.md) (split by
  topic), indexed from [`StarveNoMoreDesignConcept.md`](StarveNoMoreDesignConcept.md).

## Build & test

```bash
python scripts/check.py             # regenerate → build → test → lint. THE command.
./iwanttoplay                       # the above + install save + purge stale
                                    # TTS cache + launch TTS (Windows only for
                                    # the install/launch half)
```

Dependencies (`pytest lupa Pillow`) install automatically via the committed
`SessionStart` hook — see [`.claude/README.md`](.claude/README.md). Otherwise:
`pip install pytest lupa Pillow`.

<details><summary>Running a stage on its own (debugging a generator or the build)</summary>

- `python scripts/regenerate_all.py` — every generator, then the build.
- `python scripts/build_save.py` — assemble `saves/StarveNoMore.json`.
- `python -m pytest tests` — ~700 tests, ~21 s.
- `python scripts/check.py --fast` — skip regenerate/build, test + lint only.

The canonical description of the pipeline lives in
[`scripts/CLAUDE.md`](scripts/CLAUDE.md); everything else links to it.
</details>

Per-directory `CLAUDE.md` files (`lua/`, `scripts/`, `tests/`, `content/`) carry
local conventions + the "regenerate after edit" rule for that directory.

## Never hand-edit (auto-generated)

Each carries an `AUTO-GENERATED` banner; regenerate its source instead:

- `lua/audio_manifest.lua`, `lua/whatnow_hints.lua`, `lua/market_data.lua`,
  `lua/threat_types.lua`, `lua/recipe_data.lua`, `lua/notebook_data.lua`,
  `lua/character_briefings.lua`, `lua/achievement_data.lua`
  (+ `steam/achievements.json`)
- `docs/gamestate.md` — the `gameState` schema map
  (`python scripts/generate_gamestate_map.py`).
- `SYMBOLS.md` + `symbols.json` + `.luacheckrc` —
  `python scripts/generate_symbol_index.py` (rerun after **any** `lua/` change;
  a committed `PostToolUse` hook does it for you and a freshness test enforces it).

Which generator rebuilds what → [`scripts/generators.json`](scripts/generators.json)
(or the table in [`scripts/CLAUDE.md`](scripts/CLAUDE.md)). Build load order →
[`scripts/load_order.json`](scripts/load_order.json).
