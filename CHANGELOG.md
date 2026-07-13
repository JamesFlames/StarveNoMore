# Changelog — rule and tooling changes

*The diff of the **game**, not the code. One entry per batch; newest first. Sim win rates are the 3000-game 4-player baseline (see agents.md for the full tables).*

## The briefing promises, delivered (2026-07)

Every perk and constraint the character briefings advertise is now actually scripted — plus the Fight action itself, which had been a broadcast-only stub:

- **Fight is click-to-complete** like Move/Craft/Cook: the Fight button spawns a FIGHT button on every fightable thing at your tile (threat cards with real statlines from `cards_threats.csv` via the new generated `THREAT_STATS`, boss standees via their baked statlines), plus a TOGETHER button that pulls in every standing ally with Hunger 3+ (summed dice, shared counters — §12.2). Chip damage on threat cards persists between fights and across saves (`gameState.threatDamage`); a defeated card discards itself beside the Threat deck.
- **Bosses really arrive.** The arrival Dawn cards now pull the standee out of the Boss Pool onto the map (Deerclops → Basketball Court, Eye → a random house, Source → the center), seed script-tracked HP for every boss (not just the Source), and a defeated boss's standee returns to the pool — so festering, the Source's victory gate, and the Eye's each-Dawn extra-Threat stare (now scripted) all key off reality.
- **Character perks, implemented as briefed:** James's Gaming Reflexes (auto-reroll of his lowest failed die, once per turn on his turn) and Pattern Recognition (Peek button: top card of any deck, privately, once per day); Coco's Calming Presence (allies at her tile lose 1 less Sanity at Tick); Rayman's Court Master (+1 die at the Basketball Court, matching the sim) and Backboard Block (Defend now actually redirects counter-attack damage to him until his next turn); Ellie's Particular Eater (raw food refused); Luca's Rally (Rally button: a nearby ally gains a free non-movement action, once per turn), Calm Words (auto d6 on scripted group Sanity-loss events — 4+ spares his tile), and Needs an Audience (no solo Sanity regen from Rest, sleep, or storytelling).
- **Host Controls are contextual**: only the buttons valid in the current sub-phase show (Setup pre-game; Begin Day between days; Resolve Night at Dusk/Night; End Turn during the Day; Restart once started), and Begin Day refuses to re-run mid-day. Setup now parks the game in `PreDawn`, so the banner and CTA point at Begin Day instead of implying a Dawn is resolving.
- **Cover art**: `scripts/generate_cover.py` renders `saves/StarveNoMore.png` (Coco's hand-drawn standee on a night-suburb backdrop); `iwanttoplay` installs it beside the save so the TTS Save & Load browser shows real cover art.
- Fixed in passing: the Speed second-step message no longer mislabels itself "Court Master"; Wanderer's Gift (Coco, +1 Sanity on Move — implemented and briefed in-game all along) is now also in the briefing/notebook markdown; the supply-bag tooltip no longer claims Gather is fully automated.

## Player rulebook, publishable saves, structure pass (2026-07)

- **Player Rules on the table.** `scripts/generate_player_rules.py` assembles `PlayerRules.md` + `PlayerRules.html` from the same `content/` markdown as the in-game Notebook (Quick Start → Full Rules → Characters → Glossary — can't drift). A **Player Rules tablet** object on the table shows the HTML in-game via the local asset server; the same file opens in any desktop browser. Freshness-tested like every other generated artifact.
- **`--publish` builds.** `build_save.py --publish BASE_URL` writes a separate shareable save with every `file:///` and `localhost` URL rewritten to the hosted base — and refuses to write one that still contains a local URL. `test_publish_build.py` proves it end-to-end.
- **UI XML split** into `xml/hud.xml` / `xml/setup.xml` / `xml/dialogs.xml` (was one ~1,300-line `global_ui.xml`); the build and the whole test suite read the files in `XML_LOAD_ORDER`.
- **Adversarial tests**: undo spam refunds exactly once; all three setup entry points refuse re-entry on a running game; restart-through-the-confirm then re-setup yields a clean Day 1.
- Housekeeping: the robustness tracking file was implemented out and removed (its live pieces now live in the test suite + agents.md); the retired `Archive/Checklist_For_TTS_Implementation.md` and `Archive/InterestingGames.md` were deleted (git history keeps them; the design doc's citations became plain-text provenance notes, and code comments' phase codes are explained in agents.md).

## Starting hands + robustness program (2026-07)

- **Starting hands are real now.** Each character's personal items (design §6: Pocketknife/Flashlight/Headphones, First Aid Kit/Comfort Blanket/…, Basketball/Sports Drinks/…, Crockpot/Cooking Knife/…, Notebook/Pep Talk/…) exist as cards — authored in `content/cards_starting.csv`, rendered into a 10th deck atlas, built into per-character decks in the save, and dealt into each player's hand at setup (`dealStartingHands`). James's Energy Drink ×2 arrive as resource **tokens** by his board (Wired runs on tokens). His starting Flashlight counts for the night light check (nickname match).
- **Printed weapon dice are script-rolled.** `getAttackDice` had a TODO where equipment should have counted; `WEAPON_DICE` is now generated from "+N Attack die" card text (market + starting CSVs) and combat adds the best single carried weapon automatically.
- **Robustness program** (tracked in `robustnessimprovements.md` at the time; since implemented and removed — the enforced-mirrors list lives in agents.md): new test gates for XML well-formedness, literal `\n`, TTS-parseable colors (the white-panel bug class, checked in XML *and* Lua), image↔CustomUIAssets↔disk, dynamic per-character UI ids, luacheck (skips if not installed; CI runs it), TOOLTIP_DATA↔save tags, standee-slot constant mirror, starting-decks↔CSV; `onLoad` survives a corrupt saved state (pcall + fresh start); the dead bare-setup handler is gone; the hand+board "carried objects" scan is one shared helper for lights and weapons.

## Playtest UX fixes — first live-table feedback (2026-07)

No rule changes. Everything below came out of the first real sit-down:

- **Every UI color fixed at the root**: the XML/Lua wrote colors as `rgba(30,40,30,0.9)`-style 0–255 values, but TTS parses rgba() components as 0–1 floats — so every "dark" panel and button clamped to white and its pale text was unreadable ("What now?", "End Turn / Pass", the entire setup walkthrough). All 123 occurrences converted to `#RRGGBBAA` hex; the HUD is now actually dark.
- **Setup walkthrough restyled** as light "rulebook pages" with dark text. Step 2 became portrait cards (standee art, big bold name, role/stats/abilities/constraint); hovering a card shows that character's full briefing; literal `\n`s in labels render as real line breaks. The briefing page gained **Go Back — change character**.
- **The board's 3D Setup button now runs the guided walkthrough.** It used to fire the bare seat-order `Setup()`, which re-dealt the Market and silently replaced the picked party with the default seat assignment (the "picked Rayman/Coco/James, roster says James/Ellie/Luca" bug). Both setup paths now refuse to run on a started game and wipe the previous party before assigning.
- **Physical setup untangled**: every character owns a fixed standee slot on each tile (no more stacked standees at Ellie & Luca's); the market display is a spaced, locked column on the board's left flank (dealt cards no longer shove each other around, bury the Day Counter, or clip the board edge); the market deal skips occupied slots; unpicked characters move to an off-board bench.
- **Smaller reads**: the Party roster sizes itself to the actual party; the phase banner sits below the TTS menu bar; HP/HU/SA labels explain the stats on hover; supply bags say that Gather draws from them automatically.

## Framework improvements (2026-07)

No rule changes. Workshop hardening (the framework-improvements pass; planning doc since retired — this entry is its record): constant-mirror tests (bosses, thresholds, Cleanse, difficulty), `RECIPE_DATA`/`SEALED_REWARDS` now generated from CSV columns, atlas grids derived from card counts via `art/decks/atlas_manifest.json`, the `gameRoll` RNG seam, a TTS-stub divergence ledger, `SYMBOLS.md` + luacheck config, full-campaign bot/fuzz tests, save `SCHEMA_VERSION` + migration + frozen fixture, session-log analyzer, CI lint/artifact jobs. Fixed in passing: a malformed `T_CLOCK_STOPS` CSV row that had shifted its art note out of column. Follow-up: the in-game Notebook/Help text is now generated from `content/` markdown (`generate_notebook.py`) — previously three hand-copied versions, two of them stale.

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
