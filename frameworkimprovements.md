# Framework Improvements

*Ways to make this project easier to work on — for humans and AI agents — and more robust. Unlike the design batches, this is about the **workshop**, not the game. Every item below is grounded in friction actually hit while building batches 1–4; the "evidence" lines say where. Prioritized shortlist at the end.*

> **Status (2026-07): implemented.** Sections A–J are done, with three deliberate scope calls: A.2 (`rules_constants.json`) deferred — A.1's extended mirror tests cover the drift risk; B's third bullet (structured columns for simple Dawn effects) deferred — handlers are genuinely bespoke and the pairing tests already guard them; H.1 applied as one commit capturing the accumulated batches (retroactive per-batch splitting was impractical) with per-batch history recorded in [CHANGELOG.md](CHANGELOG.md) and the per-batch convention adopted going forward. The luacheck CI job ships soft-fail (`continue-on-error`) until its first run is reviewed.

---

## A. One source of truth for rule constants

**The problem.** A single rule number currently lives in up to five places: `lua/global.lua` (the game), `scripts/simulate_balance.py` (the sim mirror), `scripts/build_save.py` (physical component text/stats), `StarveNoMoreDesignConcept.md` (design prose), and the player docs (`content/notebook/`, `content/help/`). `tests/test_sim.py` mechanically mirrors *some* of them (character stats, Doom rates, phase map) — the rest are synced by hand and hope.

**Evidence.** The batch-4 calibration change (Source HP 10 → 8) required coordinated edits in `combat.lua`, the sim's `BOSSES` dict, `build_save.py`'s boss list, and two design-doc paragraphs — with **no test** that would have caught a missed one. The Doom-limit work similarly touched ten hardcoded `/ 30` strings across six Lua files.

**Proposals, cheapest first:**
1. **Extend the mirror tests** (`test_sim.py`) to cover what they currently miss: boss statlines (lua `SOURCE_MAX_HP` / `TREEGUARD_STATS` ↔ sim `BOSSES` ↔ `build_save.py` bosses list), `SOURCE_SPLIT_HP`, Doom thresholds, Cleanse cost/effect, and `DIFFICULTY_PARAMS`. An afternoon of work; converts every future constant change into a red test instead of a silent drift.
2. **A `content/rules_constants.json`** as the authored source, with a small generator emitting a `lua/rules_constants.lua` and importable Python constants. The design doc and player docs then *reference* names ("Source HP: see rules_constants") or get spot-checked by a grep test for the few load-bearing numbers. Bigger, but it makes the sim mirror structural instead of test-enforced.

## B. Generate what is currently hand-mirrored

The repo's best pattern is the generated data table (`market_data.lua`, `whatnow_hints.lua`, `audio_manifest.lua`, `threat_types.lua` — all freshness-tested). Three tables still hand-mirror CSV content:

- **`RECIPE_DATA`** (`crafting.lua`, ~20 entries) duplicates `cards_recipes.csv`. A `generate_recipe_data.py` with structured effect columns (`allAtTile=hunger:4;sanity:2`) would remove the drift risk entirely.
- **`SEALED_REWARDS`** (`actions.lua`) restates the reward text printed on the sealed threat cards. A `pry_reward` CSV column, parsed by the same generator style, keeps card face and code from ever disagreeing.
- **`DAWN_MANUAL_STEPS` / `DAWN_EFFECTS`** — the cross-ref tests guarantee *pairing* (every card has a handler), but not that the handler *does what the card says*. Full generation is over-reach (handlers are genuinely bespoke), but a `severity`/`flags` column for the simple 60% (stat blips, single ongoing flag) would shrink the hand-written surface to the cards that earn it.

**Evidence.** The batch-3 dare/wrongness work edited card text and handlers as two separate manual steps; the only net that would catch a mismatch is a human reading both.

## C. Kill the atlas-capacity bug class permanently

**The problem.** Card atlas grids are hand-declared in *two* places (`generate_card_atlases.py` and `build_save.py` `NumWidth/NumHeight`) and card counts grow. The cross-ref tests catch overflow — but only after it happens, and fixing it is a three-file dance.

**Evidence.** Hit twice: the pre-batch commit "Fix threat deck atlas grid overflow (6x5 → 6x8)", and again in batch 3 (6x8 → 7x8 for the sealed threats). Batch 3's Wrongness card was *designed around* Phase 2 being at exactly 16/16 capacity.

**Proposal.** `generate_card_atlases.py` derives each grid from the card count (`cols = ceil(sqrt(n))`-style, or fixed-width rows) and writes a small `art/decks/atlas_manifest.json`; `build_save.py` reads its `NumWidth/NumHeight` from the manifest. The two existing tests become redundant guards instead of the only defense. One script session; removes a recurring, silently-wrong-card-faces failure mode.

## D. Make the headless TTS stub honest about its divergences

**The problem.** `tests/tts_stub.lua` is deliberately permissive, but a few behaviors diverge from real TTS in ways that *cost debugging time* rather than save it:

- `takeObject` ignores the `guid` parameter and always pops the first contained object.
- `makeObject` consumes `math.random` to invent GUIDs — which collides with `script_dice`'s global `math.random` replacement.
- Container `getObjects()` entries carry no `tags` (real TTS includes them), which forced the Night Sounds peek and the Source split to match on nicknames.

**Evidence.** The batch-2 Source-split test failed mysteriously with "scripted dice exhausted at roll 2" — an hour of debugging that ended at the stub's GUID generator, and a permanent test-side workaround (explicit guids in contained specs, padded dice arrays for loot rolls).

**Proposals:**
1. Fix the three divergences in the stub (guid-aware `takeObject`, a non-`math.random` GUID counter, tags in `getObjects` entries).
2. Add a **divergence ledger** comment block at the top of `tts_stub.lua`: every known real-TTS behavior the stub does not reproduce. Agents (and humans) read the stub header before trusting a green test.
3. Give game code an **RNG seam**: a `gameRoll(n)` wrapper in `helpers.lua` that all gameplay dice go through. Tests script `gameRoll` instead of monkeypatching `math.random` for the whole VM. Mechanical refactor (~10 call sites), ends the whole collision class.

## E. Navigability of the concatenated Lua bundle

**The problem.** 27 Lua files, every function a global, load-order concatenation. `test_lua_statics.py` prevents duplicate definitions, but *finding* things (`showConfirm`? `ensureChronicle`? `verifyAndPayResources`?) means grepping, and nothing states which file "owns" which subsystem except agents.md prose.

**Proposals:**
1. **A generated symbol index**: `scripts/generate_symbol_index.py` scanning `^function (\w+)` per file into a `SYMBOLS.md` (or an agents.md appendix). Regenerated in the freshness-test pattern. For an AI agent this converts N greps into one lookup; for a human it's the missing table of contents.
2. **Static analysis in CI**: a `.luacheckrc` (or lua-language-server config) with the TTS API and the bundle's own globals whitelisted. Catches typo'd globals (`gamestate` for `gameState`) *before* the runtime tests do — today a typo'd read is `nil` and may pass silently through a `safecall`.
3. **A one-line ownership header convention** per file (most already have one — make it uniform and greppable).

## F. Guard the game loop with one end-to-end bot game

**The problem.** The runtime tests exercise systems in isolation and `selftest.lua` scripts a single day. Cross-system interactions across a *whole campaign* (Feast × rotation turns, Wrongness × Last Dawn, doom25 × difficulty limits) are only covered where a test thought to combine them.

**Proposal.** One **headless full-campaign test**: a trivial bot (gather/cook/fight/pass by priority — the sim's `Turtle` policy, in Lua) drives `BeginDay → actions → beginDusk → beginNight → resolveTick` for 7 days at each difficulty, asserting only invariants: no hard Lua error, stats within 0..max, `subPhase` reaches `GameOver` or Day N+1, doom within limit+fester margin. Plus a **fuzz variant**: N seeded games taking random legal actions. This is the cheapest insurance against the "two features, each tested, broken together" class — the kind of bug none of the 236 current tests is shaped to catch.

## G. Save-format discipline

**The problem.** `gameState` gains fields every batch (`bossHP`, `wrongness`, `chronicle.beats`, `difficulty`…). Old saves load because reads are defensively written (`or {}`), but that defense is ad hoc and unenforced — one confident read of a missing field is a runtime error inside somebody's restored campaign.

**Proposals:**
1. `gameState.schemaVersion` + a `migrateGameState()` in `onLoad` that fills defaults for known-missing fields in one place, instead of `or {}` scattered per read site.
2. A **frozen-fixture test**: commit one `saves/fixtures/midgame_v1.json` (a Day-4 save from the current build) and assert `onLoad` + one full day of play works against it. Update the fixture deliberately when the schema changes — the test makes "does an in-flight campaign survive this upgrade?" a checked property instead of a hope.

## H. Process and workflow

1. **Commit per batch.** The working tree currently carries four design batches of uncommitted changes on top of `main` (~50 modified + ~15 untracked files). Any mistake — a bad script, a wrong `git checkout` — is unrecoverable, and `git bisect` is useless for "which batch broke X". One commit (or PR) per batch, with the batch doc referenced in the message, is the single highest-value process change available.
2. **A CHANGELOG.md of rule changes.** The balance history (win-rate tables per batch) lives in agents.md-with-git-archaeology. A ten-line-per-batch changelog ("Source HP 10→8, 3p reliefs added, …") gives playtesters and future contributors the diff of the *game*, not the code.
3. **CI additions** (`.github/workflows/tests.yml` already runs pytest): add `ruff` for `scripts/` + `tests/`, luacheck (item E.2), and upload `saves/StarveNoMore.json` as a build artifact so a playtest host can grab the save from a green commit without a local Python setup.
4. **README dev quickstart**: three lines — `pip install pytest lupa pillow`, `python -m pytest tests`, `python scripts/build_save.py`. Everything else is discoverable from agents.md; the entry ramp is not.

## I. Close the playtest data loop

Batch 4's telemetry produces JSON session logs (schema-versioned — keep that discipline when the schema grows). What's missing is the consumer:

- **`scripts/analyze_sessions.py`**: read a directory of pasted session logs, output the tables the batch-4 gates need — win rate by difficulty/player count, loss-day histogram, median inter-turn wait split by `turnStyle` (the W1 A/B verdict), Signature/dare/press-kill usage rates (which batch beats actually fire at real tables). Without this, the "instrumented humans" plan decays back into anecdote at the aggregation step.
- Store logs in `playtest/sessions/` (gitignored or committed — committed is better: the evidence trail is part of the project).

## J. For AI agents specifically

Most of the above helps agents as much as humans (the mirror tests, symbol index, and divergence ledger most of all). Three agent-specific notes:

1. **agents.md's "rules of note" section is the project's best asset — keep feeding it.** Every batch added its mechanisms there; an agent that reads it can navigate 27 Lua files cold. The risk is length: consider splitting the "Game Design Quick Reference" into a linked `agents/` page per subsystem once it passes ~700 lines (it is ~600 now).
2. **Encode the "when you change X, touch Y" matrix as tests, not prose.** The repo already does this well (freshness tests, cross-ref tests, statics) — items A.1, B, and C above are exactly the remaining untested edges. A convention worth stating in agents.md: *if a change requires remembering to update a second file, add the test that remembers instead.*
3. **Keep generators idempotent and runnable in any order** (they are today — preserve it). An agent recovering from a half-finished state should always be able to run all five generators + `build_save.py` and reach a consistent tree.

---

## Prioritized shortlist

| # | Item | Effort | Pays off |
|---|---|---|---|
| 1 | Commit per batch (H.1) | trivial | recoverability, bisect, review |
| 2 | Extend constant-mirror tests to bosses/thresholds/difficulty (A.1) | small | kills the silent-drift class from batch 4 |
| 3 | Stub divergence fixes + ledger + RNG seam (D) | small | ends the worst test-debugging trap |
| 4 | Atlas manifest generated from card counts (C) | small | kills a twice-hit bug class permanently |
| 5 | Full-campaign bot test + fuzz (F) | medium | the only net for cross-feature breakage |
| 6 | `analyze_sessions.py` (I) | small | batch 4's gates need it to mean anything |
| 7 | Symbol index + luacheck (E) | small | navigation for agents and humans |
| 8 | Generate `RECIPE_DATA` / sealed rewards (B) | medium | extends the proven generator pattern |
| 9 | Save schemaVersion + frozen fixture (G) | medium | protects real campaigns across upgrades |
| 10 | rules_constants.json single source (A.2) | large | only if #2 proves insufficient |

Items 1–4 are a single working session and would have prevented, between them, most of the friction actually experienced building batches 1–4.
