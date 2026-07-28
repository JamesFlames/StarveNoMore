# lua/ — TTS game scripts

All `.lua` files are concatenated into one save by `build_save.py` in the
explicit `LUA_LOAD_ORDER`. **There is one shared global namespace and no
`require`s** — a global defined twice means the later definition silently wins
(`tests/test_lua_statics.py` guards this).

## Rules

- **After any Lua change:** `python scripts/check.py` — it refreshes
  `SYMBOLS.md` + `.luacheckrc`, rebuilds the save, runs the suite and lints.
  (A committed `PostToolUse` hook already reruns `generate_symbol_index.py` on
  every `lua/` edit; the freshness test is the backstop if the hook is off.)
  Debugging the index generator itself?
  `python scripts/generate_symbol_index.py` runs it alone.
- **When you split or add a file:** add it to `LUA_LOAD_ORDER` in
  `build_save.py`, in the correct position (definitions must load before
  consumers). Files not in the list are appended last — order not guaranteed.
- **File-size budget:** if a file passes ~500 lines, split it before adding more.
- Seven files are AUTO-GENERATED (`audio_manifest`, `whatnow_hints`, `market_data`,
  `threat_types`, `recipe_data`, `notebook_data`, `achievement_data`) — never
  hand-edit; see [`../scripts/CLAUDE.md`](../scripts/CLAUDE.md).
- All object lookups use `getObjectsWithTag(tag)` (never GUIDs); wrap
  non-critical calls in `safecall(fn, label)`; all gameplay randomness goes
  through `gameRoll(a, b)` (never `math.random`).
- **TTS engine gotchas** — check these before debugging a runtime error from
  scratch: [`../docs/tts-interface.md`](../docs/tts-interface.md) (dead
  handles, Lighting/Notes API, Button style resets, measuring a live game)
  and [`../docs/tts-runtime.md`](../docs/tts-runtime.md) (spawn heights,
  mesh sizes, rotations).

Symbol lookup: [`../SYMBOLS.md`](../SYMBOLS.md). Deep reference: [`../agents.md`](../agents.md).
