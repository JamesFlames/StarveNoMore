# lua/ — TTS game scripts

All `.lua` files are concatenated into one save by `build_save.py` in the
explicit `LUA_LOAD_ORDER`. **There is one shared global namespace and no
`require`s** — a global defined twice means the later definition silently wins
(`tests/test_lua_statics.py` guards this).

## Rules

- **After any Lua change:** `python scripts/generate_symbol_index.py` (refreshes
  `SYMBOLS.md` + `.luacheckrc`), then `python scripts/build_save.py`, then
  `python -m pytest tests`. A freshness test fails if `SYMBOLS.md` is stale.
- **When you split or add a file:** add it to `LUA_LOAD_ORDER` in
  `build_save.py`, in the correct position (definitions must load before
  consumers). Files not in the list are appended last — order not guaranteed.
- **File-size budget:** if a file passes ~500 lines, split it before adding more.
- Six files are AUTO-GENERATED (`audio_manifest`, `whatnow_hints`, `market_data`,
  `threat_types`, `recipe_data`, `notebook_data`) — never hand-edit; see
  [`../scripts/CLAUDE.md`](../scripts/CLAUDE.md).
- All object lookups use `getObjectsWithTag(tag)` (never GUIDs); wrap
  non-critical calls in `safecall(fn, label)`; all gameplay randomness goes
  through `gameRoll(a, b)` (never `math.random`).
- **TTS engine gotchas** — check these before debugging a runtime error from
  scratch: [`../docs/tts-interface.md`](../docs/tts-interface.md) (dead
  handles, Lighting/Notes API, Button style resets, measuring a live game)
  and [`../docs/tts-runtime.md`](../docs/tts-runtime.md) (spawn heights,
  mesh sizes, rotations).

Symbol lookup: [`../SYMBOLS.md`](../SYMBOLS.md). Deep reference: [`../agents.md`](../agents.md).
