# Test Suite

The modules that **run the game**: the headless Lua harness, the campaign
bots, the release checklist. The static consistency guards — content schemas,
UI contracts, reachability, regression classes — are in
[test-guards.md](test-guards.md).

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

`tests/` is a pytest suite (no TTS required). Run it after any change:

```bash
python scripts/check.py         # regenerate → build → test → lint. THE command.
python -m pytest tests          # the suite alone, when iterating on one test
```

CI runs it on every push (`.github/workflows/tests.yml`).

## The headless harness

`tests/conftest.py` executes the real concatenated bundle under Lua 5.2
(`lupa`) with `tests/tts_stub.lua` faking the TTS API, and provides the shared
fixtures every runtime module builds on: the `env` fixture, `make_env`,
`add_char`, `script_dice`, `broadcasts`, `flush`, `populate_full_world`, plus
`walk_repo`/`repo_files` for whole-tree scans. Tests script dice by
redefining `gameRoll` and never rely on real randomness. Extend
`tts_stub.lua` when the code uses a TTS API it doesn't cover yet — but see the
stub's own guard in [test-guards.md](test-guards.md).

## Gameplay modules

One topic per module, mirroring the Lua area under test. When adding a rule,
add its test to the matching module.

- **`test_lua_setup` / `test_lua_setup_walkthrough`** — load smoke, `onLoad`/`onSave` round-trip, the guided setup and the paths real tables take through it.
- **`test_lua_combat` / `test_lua_actions`** — fumble rules, group fights, press-the-attack, and every action verb.
- **`test_lua_dawn`** — an `apply()`/`expire()` sweep over every Dawn effect.
- **`test_lua_day_loop` / `test_lua_dusk_secret` / `test_lua_week_review`** — Tick decay, Down, victory/defeat, revive, night light checks, the Dusk variant, the end-of-week report.
- **`test_lua_situational_actions.py`** — the verbs that were implemented and unreachable until 2026-07 (Revive, Stabilize, Defend, Energy Drink, Eat Uncooked, Barricade, Appease, Ghost Drift — plus Flee and Use Item, found the same way in later passes). Each is checked three ways: the precondition opens and closes at the right moment, the click moves *the state its consumers already read*, and a wrong click refuses cleanly.
- **`test_lua_ongoing_effects.py`** — the ongoing Dawn-card rules, *executed*: the effect is set, the action is taken, and the number moves. Companion to `test_lua_effect_flags.py` (see [test-guards.md](test-guards.md)), which proves each announced effect has a reader at all — eleven of them didn't until 2026-07, so each case here is the shape of that bug as much as of its fix.
- **`test_lua_msglog.py`** — the Message Log (`ui_msglog.lua`): capped at `MSGLOG_MAX` oldest-first, the panel shows the newest lines, hiding it never drops the backlog, history survives save/load, and every `broadcastEvent` category has a colour in both tables (an unmapped one just renders grey).
- **`test_lua_achievements` / `test_lua_clues` / `test_lua_reactions` / `test_lua_telemetry` / `test_lua_help_pages` / `test_lua_durable_output`** — the systems that ride alongside the day loop.
- **`test_ui_handlers_smoke.py`** — every XML click handler, discovered from `xml/` and actually invoked, in a matrix of game states. Asserts no error escapes (including one swallowed by `safecall`, which reads as a button that silently does nothing), that `gameState` invariants hold afterwards, and that an out-of-turn click is *refused* rather than obeyed. Adding a button extends this coverage automatically.
- **`test_dead_handles.py`** — the dead-handle class from both ends: a runtime sweep that drops a poisoned handle on the table and runs the real entry points over it, plus a static scan for object fields dereferenced without a guard.

## Whole-game and data

- **`test_full_campaign.py`** — a trivial bot plays whole games headlessly at every difficulty (invariants only: no hard error, stats in range, a verdict is reached), plus seeded random-verb fuzz games and adversarial sequences (undo spam, re-entrant setup on all three UI paths, restart-then-re-setup). The net for cross-feature breakage.
- **`test_save_fixture.py`** — loads the frozen `saves/fixtures/midgame_v1.json` (and a stripped old-schema variant) into the current bundle and plays a full day. Guards `migrateGameState()`.
- **`test_sim.py`** — enforces the sim maintenance rule mechanically (sim constants must equal `global.lua`'s: stats, homes, Doom rates/thresholds, Cleanse, boss statlines vs build_save + combat.lua, difficulty invariants), asserts per-game invariants over seeded batches, and checks policy win rates stay inside bands around the baseline. If you change a rule intentionally: update the sim, rerun the 3000-sim baseline, update the table in [balance-simulation.md](balance-simulation.md) **and** the bands in `test_sim.py`.
- **`test_analyze_sessions.py`** — the playtest-log aggregator against synthetic and real telemetry exports.

In-TTS checks that can't run headlessly stay in `lua/audit.lua`
(`auditFirstLoad()`, `auditTooltips()`, `auditHintCoverage()`,
`auditObjectCount()` from the TTS console).

## In-TTS self-test

`lua/selftest.lua` adds **`runSelfTest()`** — run it from the TTS console
(~20s). It plays a scripted mini-game against the real components: component
audit → Setup → Begin Day → Gather → Undo → Pass → Dusk → Night → Tick →
save/load round-trip, asserting `gameState` after every step and reporting
`[OK]`/`[FAIL]` lines with a summary. **It resets game state and moves real
cards — run it on a fresh load, then reload the save before playing.** The
same steps are exercised headlessly in CI (`test_lua_setup.py::TestSelfTest`),
so in TTS it mainly catches the physical layer: missing objects, asset
loading, engine quirks.

## Release checklist (before sharing a new save)

1. `python scripts/check.py` — everything green.
2. Rebuild + serve: `python scripts/build_save.py`, start `scripts/serve_art.bat`.
3. Load the save fresh in TTS — no red errors in the console, board/tiles/cards show art (not placeholders), day ambience starts.
4. Run `runSelfTest()` from the console — 0 failures. Reload the save.
5. Spot-check the physical layer the tests can't see: hover a standee (live tooltip), click Setup and eyeball the walkthrough panels, open Help/Notebook tabs, confirm one boss arrival plays its roar (e.g. trigger Deerclops via a Day-4 run or console).
6. Save mid-game (Day 2+), reload, confirm the banner says "game restored" with the right Day/Doom.
