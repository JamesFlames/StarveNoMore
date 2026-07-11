# Changelog — rule and tooling changes

*The diff of the **game**, not the code. One entry per batch; newest first. Sim win rates are the 3000-game 4-player baseline (see agents.md for the full tables).*

## Framework improvements (2026-07)

No rule changes. Workshop hardening from [frameworkimprovements.md](frameworkimprovements.md): constant-mirror tests (bosses, thresholds, Cleanse, difficulty), `RECIPE_DATA`/`SEALED_REWARDS` now generated from CSV columns, atlas grids derived from card counts via `art/decks/atlas_manifest.json`, the `gameRoll` RNG seam, a TTS-stub divergence ledger, `SYMBOLS.md` + luacheck config, full-campaign bot/fuzz tests, save `SCHEMA_VERSION` + migration + frozen fixture, session-log analyzer, CI lint/artifact jobs. Fixed in passing: a malformed `T_CLOCK_STOPS` CSV row that had shifted its art note out of column.

## Batch 4 — validation & hardening (2026-07)

- **The Source: HP 10 → 8** (calibration knob, §20.1's first choice). Sim best line moved into the 40–50% target band (turtle 42%, spread 42%) with ~100% of losses on Days 6–7.
- **3-player reliefs** (both behind `playerCount == 3`; table A/B pending): Big Appetite costs 2 Hunger only on days Rayman fought or moved 2+ tiles; Loud requires 3+ tiles moved.
- **Difficulty modes** (§17.2, now real): Long Weekend (3 days, phases 1/1/2, Doom track to 15), Standard, Nightmare (Doom +1/phase, starts on Strange Days). Selectable at setup.
- **Session telemetry**: the chronicle records setup facts, per-turn seconds, and batch beats; **Copy Session Log** on the Week in Review panel exports JSON to the Notes panel.
- **Playtest protocol**: `playtest/facilitator_script.md` + `feedback_form.md`.

## Batch 3 — mid-week texture & dread (2026-07)

- **Night Sounds**: a low growl at Dusk when the top Threat card is Hard (generated `THREAT_TYPE_BY_NAME`). Deliberately unexplained.
- **Dawn Dares**: 5 Phase 1–2 cards gained optional hooks — scripted: court floodlights (`P1_LIGHTS_FLICKER`: courts +2 threats, survivors claim 2 Market cards) and porch light (`P2_PORCH_LIGHT`: first house Gather may take 3 resources for 2 Sanity); checklist offers on `P1_STRANGE_RADIO`, `P1_SOMETHING_WATCHED`, `P2_FOOD_SPOILS`.
- **Sealed Rooms**: the **Pry** verb coded (free action + Crowbar/Lockpick/Pry Bar); 3 new sealed threats (Shed, Locker, Car); the **Sealed Basement** placed at Ellie & Luca's House every game (free Market Item + 2 Food/1 Wood/1 Battery). Threat atlas grew 6×8 → 7×8 (now manifest-derived).
- **The Wrongness**: `P2_BASKETBALL_BOUNCE` converted to a deferred face-down threat at the court — resolves on tile entry or at the next Dawn; doesn't fester while face-down.
- Balance-neutral by design (turtle 34%, spread 27%, balanced 11%).

## Batch 2 — the climax & identity (2026-07)

- **Nothing Left to Lose** (Doom 25): +1 attack die for everyone; Rest heals +1 Health anywhere (non-stacking with home).
- **Signature Moves** (once per game, per character): James **All-Nighter** (+3 actions, −3 Sanity at next Tick), Coco **Touch of Hope** (+4 Health, any tile), Rayman **Posterize** (delete a non-boss threat at his tile; +1 draw there tonight), Ellie **The Feast** (1 action, cook freely, all held Food consumed), Luca **The Speech** (+2 Sanity to all; only while an ally is Down or below 3 Sanity).
- **Source phases**: boss HP script-tracked (`gameState.bossHP`); at ≤5 HP the Source splits into two Terror Beaks at adjacent tiles (once).
- **The Last Dawn**: Day 7's Dawn is fixed and toneless — no Phase-4 draw.
- Baseline: turtle 35%, spread 27% — win-rate-neutral, loss profile shifted late (as intended).

## Batch 1 — combat is the center (2026-07)

- **Press the Attack** (§12.5): after a hit, pay 1 Sanity per bonus die until you miss; the enemy waits. Press dice never fumble.
- **Boss-kill rewards**: Deerclops Doom −2, Eye −3, 3-resource spill, Trophy; kill narrations + lighting flash.
- **Week in Review**: the persistent chronicle, narrated at game end.
- Baseline: turtle 32%, spread 27% — unfought-Source losses collapsed 33%→8%.

## Pre-batch retune (2026-07)

Source-mandatory victory; uncapped boss festering (+2/dawn, Treeguard +1); no boss-arrival Doom; per-count Doom rates 3p [1,1,1,1] / 4p [1,1,1,2] / 5p [1,1,2,2]; whiff-only fumbles; escalating deterministic Charlie; crowded floor; Moonlit Salvage; the Treeguard; Scarcity at Doom 15.
