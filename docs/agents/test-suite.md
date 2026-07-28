# Test Suite

Per-module coverage map, the harness, and the release checklist.

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

`tests/` is a pytest suite (no TTS required). Run it after any change:

```bash
python -m pytest tests          # needs: pip install pytest lupa
```

CI runs it on every push (`.github/workflows/tests.yml`). What it covers:

- **`test_csv_schema.py`** — every `content/*.csv`: required columns, unique/well-formed ids, stat ranges, starting-item characters/counts.
- **`test_cross_refs.py`** — cross-artifact drift: every Dawn card has a `DAWN_EFFECTS` entry (and no orphans), every `ongoingDawnEffects` flag has an `EFFECT_RULES` label, atlas grids hold every card **and** match `NumWidth/NumHeight` in build_save.py, hardcoded card ids in Lua exist in the CSVs, `MARKET_COSTS` covers the Market deck, every asset/sound URL resolves to a file on disk, `TOOLTIP_DATA` keys are real save tags, starting-hand decks match `cards_starting.csv`, and the standee slot constants in build_save.py mirror `helpers.lua`.
- **`test_xml_quality.py`** — the silent TTS failure modes: XML well-formedness, no literal `\n` in attributes (renders as text), every color parseable by TTS (hex length 3/4/6/8; rgb()/rgba() components must be 0-1 floats — 0-255 values clamp to white; checked in the XML **and** Lua color literals), `<Image image=...>` names resolve to `CustomUIAssets` + files on disk, and the per-character UI ids the Lua composes dynamically all exist.
- **`test_lua_lint.py`** — runs `luacheck lua` against the generated `.luacheckrc` when luacheck is installed (skips otherwise; CI's luacheck job always runs it), and asserts `.luacheckrc` is still the generated file. (CI's luacheck job is `continue-on-error` — flip it to hard-fail after reviewing a green run.)
- **`test_generated_freshness.py`** — reruns the three generators and fails if `audio_manifest.lua` / `whatnow_hints.lua` / `market_data.lua` are stale (always restores the committed bytes).
- **`test_xml_lua_contract.py`** — every UI id the Lua targets exists in the `xml/` files; every XML `onClick` and Lua `click_function` names a defined function; XML ids are unique across all files.
- **`test_publish_build.py`** — a `--publish` build contains no `file:///` or `localhost` URL anywhere and never touches the committed dev save.
- **`test_lua_statics.py`** — no global function/constant is defined twice across the concatenated bundle (the later definition would silently win); every lua file is deliberately placed in `LUA_LOAD_ORDER`.
- **`test_build_output.py`** — rebuilds the save, validates the JSON, and fails if `saves/StarveNoMore.json` is stale relative to the sources (restores committed bytes; run `python scripts/build_save.py` to fix).
- **`test_lua_*.py`** (`test_lua_setup` / `test_lua_combat` / `test_lua_dawn` / `test_lua_actions` / `test_lua_day_loop` / `test_lua_telemetry`) — run the real concatenated bundle headlessly under Lua 5.2 (`lupa`) with `tests/tts_stub.lua` faking the TTS API: load smoke, `onLoad`/`onSave` round-trip, combat fumble rules, Charlie escalation/reset, Tick decay + Down + victory/defeat, revive, night light checks, and an `apply()`/`expire()` sweep over every Dawn effect. The shared bundle harness (`env` fixture, `make_env`, `add_char`, `script_dice`, `broadcasts`, `flush`, `populate_full_world`, …) lives in `tests/conftest.py`. When adding gameplay rules, add a test to the matching topic module; extend the stub in `tts_stub.lua` if the code uses a TTS API it doesn't cover yet. (Split 2026-07 from a single 1,662-line module.)
- **`test_sim.py`** — enforces the sim maintenance rule mechanically (sim constants must equal `global.lua`'s: stats, homes, Doom rates/thresholds, Cleanse, boss statlines vs build_save + combat.lua, difficulty invariants), asserts per-game invariants over seeded batches, and checks policy win rates stay inside bands around the baseline table above. If you change a rule intentionally: update the sim, rerun the 3000-sim baseline, update the table above **and** the bands in `test_sim.py`.
- **`test_full_campaign.py`** — a trivial bot plays whole games headlessly at every difficulty (invariants only: no hard error, stats in range, a verdict is reached), plus seeded random-verb fuzz games and adversarial sequences (undo spam, re-entrant setup on all three UI paths, restart-then-re-setup). The net for cross-feature breakage.
- **`test_save_fixture.py`** — loads the frozen `saves/fixtures/midgame_v1.json` (and a stripped old-schema variant) into the current bundle and plays a full day. Guards `migrateGameState()`.
- **`test_analyze_sessions.py`** — the playtest-log aggregator against synthetic and real telemetry exports.
- **`test_dead_handles.py`** — the dead-handle class from both ends: a runtime sweep that drops a poisoned handle on the table and runs the real gameplay entry points over it, plus a static scan for object fields dereferenced without a guard.
- **`test_tts_api_surface.py`** — a curated allowlist of the TTS singleton API, checked in both directions: Lua may only *call* what exists, and `tts_stub.lua` may only *define* what exists (a stub that invents API makes the suite confirm bugs instead of catching them).
- **`test_regression_guards.py`** — generic guards for the *classes* of bug that keep recurring in playtest, each encoding one hard-won lesson (see `docs/tts-runtime.md` and `docs/tts-interface.md`). Fourteen checks, covering spawn overlap, text-gadget rotation, button contrast and runtime colour overrides, unguarded object handles, board scale vs. artwork, on-board spawn heights, hidden objects staying hidden and silent, path-layout mirroring, and player-board alignment:
  1. laid-out object groups (player boards, location tiles) must not overlap at spawn — physics scatters an overlapping stack (the root cause of "Gather shows 0");
  2. text-gadget objects (Notecard/Counter) must be upright (rotY≈0), not 180 (the upside-down Quick Start);
  3. button text must clear a minimum contrast (3.0) against its own background (the dark-on-dark readability complaints); transparent click-overlays are excluded;
  4. **every `takeObject` callback that dereferences its object handle must wrap it in pcall/safecall** — a dead handle throws "cannot access field … of userdata"; that crash hit three times in one session and the guard immediately found five more latent ones;
  5. every tag passed to `findOneByTag`/`findAllByTag`/`getObjectsWithTag` — literal (`"DoomMarker"`) or namespaced (`"Location:" .. name`) — must exist in the built save, because a typo'd tag fails **silently** (returns nil, feature quietly does nothing);
  6. player-facing text must not name a component that was removed from the save (a Dawn card told players to use the Discard Tray for a release after it was deleted); keyed by tag, so it only fires once the component is really gone;
  7. no player-facing string may hardcode the Standard `of 7` / `/ 30` — those are wrong on Long Weekend (3 days, Doom 15) and Nightmare; use `getTotalDays()` / `getDoomLimit()` or the `{totalDays}` / `{doomLimit}` tooltip placeholders;
  8. `gameState` fields must be initialised (literal default, `migrateGameState`, or a lazy init earlier in the same function) before being indexed — otherwise a fresh setup or loaded old save crashes with "attempt to index a nil value".

  Runtime companions in `test_lua_actions.py`: `TestResourceModelRobustness` (held resources stay correct when a board is dragged away — the gather-shows-zero class), `TestStatDisplayNeverStale` (the left stat box shows live stats with no active player, not a frozen snapshot), and `TestDifficultyAwareText` (the Doom help panel and the Day/Doom tooltips print the *active difficulty's* limits, with no unsubstituted `{placeholders}`).

In-TTS checks that can't run headlessly stay in `lua/audit.lua` (`auditFirstLoad()`, `auditTooltips()`, `auditHintCoverage()`, `auditObjectCount()` from the TTS console).

## In-TTS self-test

`lua/selftest.lua` adds **`runSelfTest()`** — run it from the TTS console (~20s). It plays a scripted mini-game against the real components: component audit → Setup → Begin Day → Gather → Undo → Pass → Dusk → Night → Tick → save/load round-trip, asserting `gameState` after every step and reporting `[OK]`/`[FAIL]` lines with a summary. **It resets game state and moves real cards — run it on a fresh load, then reload the save before playing.** The same steps are exercised headlessly in CI (`test_lua_setup.py::TestSelfTest`), so in TTS it mainly catches the physical layer: missing objects, asset loading, engine quirks.

## Release checklist (before sharing a new save)

1. `python -m pytest tests` — everything green.
2. Rebuild + serve: `python scripts/build_save.py`, start `scripts/serve_art.bat`.
3. Load the save fresh in TTS — no red errors in the console, board/tiles/cards show art (not placeholders), day ambience starts.
4. Run `runSelfTest()` from the console — 0 failures. Reload the save.
5. Spot-check the physical layer the tests can't see: hover a standee (live tooltip), click Setup and eyeball the walkthrough panels, open Help/Notebook tabs, confirm one boss arrival plays its roar (e.g. trigger Deerclops via a Day-4 run or console).
6. Save mid-game (Day 2+), reload, confirm the banner says "game restored" with the right Day/Doom.
