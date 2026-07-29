# Changelog — rule and tooling changes

*The diff of the **game**, not the code. One entry per batch; newest first. Sim win rates are the 3000-game 4-player baseline (see agents.md for the full tables).*

## Eight rules that were never wired up (2026-07)

A reachability audit of the Lua bundle found nine global functions that nothing
called. Eight of them were *rules*, fully implemented, with their state
consumers already in place — and no button, dialog or phase step anywhere that
would run them. Nothing errored; the rules were simply absent while the UI went
on describing them.

**Revive was the worst.** `cookTelltaleHeart` worked, so `gameState.heartCount`
went up and never down: Hearts could be cooked and never spent, while four
places in the UI told players to "use a Telltale Heart at this tile to revive".
The only revive path in the game had no caller.

Also restored: **Stabilize** (§12.3, the Bandage revive), **Defend** (Rayman's
Backboard Block — `combat_resolve` had always redirected counters on
`raymanDefending`; nothing set it), **Energy Drink** (James's Wired constraint
was a pure penalty: four files read `jamesEnergyDrinkUsed`, one reset it
nightly, nothing ever made it true, so the -2 Sanity was unavoidable for the
whole week), **Eat Raw** (§8.4, and with it Ellie's Particular Eater, which
could never be bumped into), **Barricade** (day_loop already subtracted it from
the night threat rate), **Appease Treeguard**, and **Ghost Drift** — §16.4's
one-tile-per-round move, which is the only decision a Down player has, and
whose absence is the co-op player-elimination failure §05 spends a page on.

The seven Day-phase verbs are situational, so they follow the Peek/Rally
pattern rather than taking permanent bar space: hidden until their `canX`
precondition holds. Ghost Drift rides the Reactions panel, since a ghost is
never the active player.

**The guard:** `tests/test_lua_reachability.py` now fails on any global
function nothing calls, allowlisting only TTS engine callbacks and console
tools, plus a companion check that bans `_G[name]` — dynamic dispatch would
make an orphan indistinguishable from a live handler.

## Nightmare is winnable now (2026-07)

Follow-up to the design pass, which had made Nightmare's problem visible for the
first time: a flat Doom +1 in every phase measured at **0-6%** for the best lines
at 4 players. That is a broken mode, not a hard one.

The cause is compounding. Most Doom pressure is already *responsive* (§15.1 -
festering threats, festering bosses, fallen friends), so a flat surcharge from
Day 1 taxes the exploratory half of the week §14 deliberately wants calm, and
runs the clock out before the arc reaches its climax. The losses were mid-week
strangulation, which is exactly what §20.1's calibration gate exists to catch.

**Retuned:** the surcharge moved to **Phases 3-4 only**, and the Source went to
**9 HP** (one above Standard's calibrated 8), so Nightmare's finale is a harder
*fight* rather than the same fight on a shorter fuse. Best line **20.3%** over
3000 games with **100% of losses on Days 6-7** - a near-miss finish. Roughly one
win in five, and the real table number is lower: the probe cannot model
`minPhase` (phases 1 and 2 share a Doom rate), so it never sees that Nightmare
opens on the Strange Days deck instead of the gentle Phase 1 one.

`doomDelta` therefore accepts a per-phase table as well as a flat number, read
through the new `getDoomDelta(phase)` / `describeDoomDelta(diff)`. The setup
announcement used to do `(diff.doomDelta or 0) > 0`, which throws "attempt to
compare table with number" the moment the surcharge went per-phase - fixed, and
a test now describes every mode's delta to keep that from coming back.

Also recorded honestly in §17.2: **the probe is only trustworthy at 4 players.**
At 3 players every mode reads >=98% including Standard, because `ROSTERS[3]` is
the strongest trio by construction; at 5 players every mode reads high because
five bodies clear festering faster than the extra phase rate charges for it.
Neither spread is caused by the difficulty settings and neither is fixed by
tuning them - establishing real 3p/5p bands is §20.1's open composition work.
*(This also makes the achievements batch's **Nightmare win** unlock earnable —
it shipped against a mode measuring 0-6%.)*

## Achievements (2026-07)

24 achievements, a Steam-style panel in the mod, and a Steamworks manifest for
a future standalone app. Full detail: [`docs/achievements.md`](docs/achievements.md).

**What players see:** a *Trophies* button beside Hide UI opens a paged panel —
icon, name, description, and when it was earned. Unlocks raise a toast bottom
right and a chat line. Three of the 24 are hidden and show as `???` until they
happen. The roster spans the week's shape: living through Day 1, winning at
all, winning on Nightmare / Long Weekend / solo, each boss, the ten-meal cook,
the fifteen-kill week, the three-press finisher, everyone spending their
Signature, and the two endings that are worth the retelling (winning with two
Doom left, winning with one character standing).

**What it does not do, and why:** a Tabletop Simulator Workshop mod runs inside
someone else's Steam app. It has no appid and no Steamworks surface, so it
cannot set a real Steam achievement — nothing can, from inside TTS. The panel
is the working half; `steam/achievements.json` is generated from the same CSV
so that a future port is a copy-paste, not a redesign.

**Where unlocks live:** `gameState.achievements`, which rides the mod's saved
script state — the only store TTS gives a mod. It is deliberately *not* cleared
by Restart: it records what the table has done, not what this week did. A fresh
load from the Workshop starts empty (a TTS limit), so the panel's *Copy my
code* button writes a `SNM-ACH-1:` string to the Notes panel that restores
every unlock at another table.

**Nothing new is recorded at the table.** Every number the unlock rules read
was already tracked for the Week in Review (§16.5) or the session telemetry
(§20.2). The rules are pure reads of `gameState`, re-tested at four checkpoints
(a kill, end of turn, end of day, game over), each `pcall`-ed so a broken rule
costs its own achievement and nothing else.

**Adding one is a CSV row plus a predicate.** `content/achievements.csv` feeds
the in-game roster, the Steam manifest and the ComfyUI art prompt;
`lua/achievement_rules.lua` holds the condition. A row without a rule, or a
rule without a row, fails the test suite. Art comes from the same ComfyUI
pipeline as the cards ([`docs/comfyui-achievement-icons.md`](docs/comfyui-achievement-icons.md)
is the run book) and falls back to a procedural placeholder so the build is
never blocked waiting on a render.

## Design review pass — all 17 findings (2026-07)

The batch that shipped `possible-design-improvements-to-snm.md` (retired to git
history once all 17 landed), a review against
`Archive/PrinciplesOfGoodBoardGames.md` §1–26 (especially its
Part IV co-op / attrition / onboarding / accessibility / measurement chapters).
That document is now the *rationale record*, not a proposal list.

**Defects — three rules didn't do what they said, and one couldn't run at all:**

- **Pristine Run was unreachable at 3–4 players.** `checkBonusVictories` gated
  on `count >= 5`, but §6.6 turns spare characters into Visitor NPCs, so the
  *recommended* player count could never earn it. Now "every character in play,
  nobody revived".
- **The Truth Run could not fire under any draw.** Nothing in the mod ever
  incremented `gameState.clueCount` — three Clue cards, a Trophy and a Dawn card
  all pointed at a counter stuck on zero.
- **The default victory condition was circular** ("all *surviving* characters
  are alive"). §16.1 now states the permissive rule `checkVictory()` always
  enforced: one survivor, Doom under the limit, Source dead.
- **Night Sounds was audio-only** while carrying a gameable bit. The Dusk growl
  now ships with a moon glyph in the Phase Banner.

**Rules changes:**

- **Last Nerve** (§10.1.1) — while any stat is below 3, Flee costs 0 Sanity and
  Rest restores 1 extra. The individual mirror of Doom 25, closing the gap where
  a player could spiral into irrelevance on a healthy team clock. *Measured:
  best line 42% → 51%, collapse-losses 27.3% → 11.8%.*
- **Witness** (§10.1) — an ally at a Haunted character's tile may pay 1 Sanity
  to see their threat and fight it with them. Haunted stops deleting the co-op
  layer for the player who most needs it.
- **Rally is once per round and fires off-turn** (§6.5) — the cheapest downtime
  cure (§11) and the one that makes Luca's identity land. Retuned from per-turn,
  which off-turn would have made +4 actions a day at five players.
- **Truth Run is findable by decision** (§16.2) — a guaranteed Clue behind the
  Sealed Basement, Market checkpoints on Days 3 and 5, and James can *take* a
  Clue he peeks.
- **Difficulty and length are separate dials** (§17.2) — new **Story** mode
  (full 7-day arc, Doom 35, a 6 HP Source that splits at 4) is the new default;
  **Long Weekend** is reframed as a *short* mode and listed last. The old "Easy"
  was Long Weekend, so easy mode omitted the Eye, the Source, Doom 25 and every
  Signature's intended moment. *Measured ordering: Story 67/80%, Standard
  51/50%, Nightmare 0/2%.*
- **A guided opening** (§15.9) — Day 1's Dawn is fixed like Day 7's, and each
  player gets one concrete three-action plan on their first turn.
- **Two new off-by-default toggles:** **Secret Dusk** (§11.3 — argue freely,
  commit privately, all revealed at once) and **Solo** (§20.3, promoted from an
  expansion hook to an official mode: 3 characters, anti-alpha rules suspended).

**Measurement and documentation:**

- **§8.5 states the daily attrition ledger** — the per-day drain, the realistic
  restoration, a ~50% maintenance-tax target, and the cooperation dividend that
  makes the Crockpot the tax-reduction engine. It is a regression check.
- **Option utilization** (§20.2 item 8) — session logs (schema 2) now record
  every craft, cook, action, location, Visitor and Trophy, and
  `analyze_sessions.py` scores them against the authored catalog so unused
  content shows as explicit zeros. `simulate_balance.py --utilization` covers
  the action mix. *Confirmed: Cleanse is ≤1.5% of actions and 0.00/game for two
  of four policies. Not confirmed: the Badminton-Court prediction is untestable
  in the sim, because every policy hardcodes the Basketball Court.*
- **§18.19 states the accessibility floor** as six checkable rules, and
  **§19.6 item 5** now audits strategies (two measured lines) rather than
  claiming four victory paths.
- **The Week in Review ends on a margin and a hook**, not on statistics.
- **The whole rulebook is readable in-game** — a paged Rulebook tab in the Help
  panel, carrying the same four sections as `PlayerRules.md`. Paging also fixed
  a silent clip: the Glossary was ~7,000 characters in a body that holds ~2,000.

**Not done, deliberately:** Standard is *not* retuned to absorb the gentler
rules. Last Nerve, the Haunted buy-in, Secret Dusk and the difficulty axis all
push the same way, and §17's regression list forbids evaluating them together.
The knobs are named in §20.1 in the order to spend them.

## Cheaper, safer AI workflow (2026-07)

Tooling/tests only — no rule changes, with one exception noted below. The third
and last pass at making this repo cheap to work in (after the compartmentalise
and structural programs, both already retired here). Those two built the
*navigation* layer; this one attacked the three costs navigation could not
touch: session bootstrap, the untested interactive surface, and the size of the
two files an agent is told to consult. `GoodForAiPlan.md` is retired with it.

**Bootstrap — paid once per session, before any useful work.**
- `.claude/` is committed now (only `settings.local.json` is ignored), so what
  an agent learns about *how to work here* survives the container. A
  `SessionStart` hook installs `pytest lupa Pillow ruff` + `luacheck`; a
  `PostToolUse` hook reruns `generate_symbol_index.py` after any `lua/` edit; a
  permission allowlist covers the routine loop. `/verify` and `/newtask` are
  committed slash commands.
- **`python scripts/check.py` is the one command to finish a task** —
  regenerate → build → test → lint, one verdict line, ~22 s. The three-step
  ritual is demoted to a "debugging that stage" note in all six `CLAUDE.md`
  files, and the pipeline is written out in exactly one place
  (`scripts/CLAUDE.md`) instead of five.
- `./iwanttoplay` works on Linux (it used to die at step 4 after a good
  regenerate/build/test, because `os.startfile` is Windows-only).

**The interactive surface, which nothing tested.** 58 of 73 XML click handlers
were never named in a test — every action button in the game. That is where the
playtest bug reports came from, because nothing else could find them.
- `tests/test_ui_handlers_smoke.py` clicks **every** handler across six game
  states (PreGame, Day as the active seat, Day as a *wrong* seat, Dusk, Night,
  GameOver), asserting no Lua error escapes — *including one swallowed by
  `safecall`*, which is the "button silently does nothing" failure TTS is worst
  at — that invariants hold, and that out-of-turn clicks are refused rather
  than merely survived. Handlers, element ids and arguments are all parsed from
  `xml/`, so a new button is covered the moment it is added and nothing can be
  skipped. **0/73 uncovered**, in ~1 s.
- It immediately found a real one: the ghost-panel guard added to `onPickChar`
  after a human hit it in a playtest was never applied to the other setup
  steps, so clicking Continue on a leftover variants panel re-applied a
  difficulty — and a different Doom limit — after the game had ended. Now a
  shared `isGhostSetupClick()` on all nine step handlers. *(The one rule-facing
  change in this batch.)*
- `tests/test_lua_setup_walkthrough.py` walks guided setup for 1–5 players plus
  the paths real tables take: duplicate picks, a player leaving mid-pick, a
  seat change between steps, the hotseat path, and every stale click a
  disconnected client could still send.

**`gameState` had no schema.** 71 fields across 41 of 46 Lua files, and a
misspelling read as `nil`, silently, at runtime, in TTS.
- One initialiser instead of two: the Restart path was a hand-copied literal
  that had **already drifted** — a Restart produced a `gameState` missing
  `resources`, `dailyAlerts`, `lastInteractionAt`, `idleNudgedThisTurn` and
  `schemaVersion`. Both paths go through `migrateGameState()` now, which also
  hardens old-save migration.
- `docs/gamestate.md` (generated) maps every field to its default, its writers
  and its readers; `tests/test_gamestate_schema.py` fails if any
  `gameState.<name>` is neither declared nor on the reviewed transient list.
  36 declared, 36 transient, **0 unaccounted**.

**Drift pairs closed.** `CHAR_BRIEFINGS` is generated from
`content/help/character_briefings.md` (they had diverged — the markdown told
James about his house, the game never did). An unlisted `lua/`/`xml/` file now
**fails the build** instead of printing a note nothing checked; `assets.lua`
joined the manifest. `content/CLAUDE.md` carries a per-CSV column dictionary
bound to the schema test.

**Context bill.** `agents.md` 18.6k → **3.0k tokens**, split into ten topic
files under `docs/agents/`, each under a 2.5k budget a test enforces.
`symbols.json` + `python scripts/sym.py NAME` answers "where is X?" with
location, signature and call sites in one call, instead of grepping a 17k-token
index and opening the file anyway.

**Two real bugs found while building the above**, neither of them the thing
being worked on:
- A stale `saves/StarveNoMore.json` made the suite *hang for over four minutes*
  — `test_committed_save_is_fresh` asserted equality of two 1.2 MB strings, so
  pytest tried to build a character-level diff. It reports in 0.47 s now,
  naming the byte offset.
- Ambient track durations in the audio manifest were estimated from file size
  and wrong by up to **65%** (25.2 s recorded for a 72.0 s track). Those
  durations schedule the next track, so every one was a clip cut short.
  `generate_audio_manifest.py` now reads the exact duration out of the Ogg
  stream itself.

**Also:** the 17 MB WAV that escaped the earlier audio compression pass is OGG
q4 (1.0 MB); tracked media 286.7 → 270.2 MB, with a test capping any new
binary at 4 MB. `luacheck` **hard-fails in CI** now — the soft-fail was there
"until the first run has been reviewed", the review happened, and all five
warnings are fixed rather than whitelisted (one was a genuine fragility: a
file-local helper called from another file, working only because the bundle is
one concatenated chunk).

**And the CI job nobody could see was broken.** `ruff` had been failing on
every run for weeks — not from anything in this repo, but because the job
installed ruff unpinned and inherited each release's widening defaults, until
166 findings accumulated and a permanently-red job stopped meaning anything.
The rule set is now pinned in `ruff.toml` (ruff's own documented default plus
import sorting — real defects only; the 88 refactor-opinion findings are listed
there as deliberately unselected, with counts) and the version is pinned in the
workflow. All four CI jobs are green.

The root cause was closer to home: **`scripts/check.py` ran pytest and luacheck
but not ruff**, so the one command that says "everything green" could not see
it. Its stages now mirror the CI jobs one-for-one, and both files say so.
Fixing it turned up two genuinely dead imports in `build_save.py` — one of
which, `md_to_text`, README and `architecture.md` still described as the shared
source for the physical Quick Start notecard. It has not been for some time;
that notecard is hand-written text, and both docs now say so.

Suite: 683 → **812 tests**, still ~20 s (~26 s including both linters).

## Repo structure follow-ups (2026-07)

Tooling/docs only — no rule changes. The next layer after the completed
compartmentalise program (now retired to `Archive/compartmentaliseplan.md`):

- **One-command rebuild.** `scripts/regenerate_all.py` runs every generator (in
  `generators.json` order) then `build_save.py`, so you no longer have to
  remember which generator matches your edit. Generators whose sources are
  absent (e.g. `sounds/` on a clean clone) are skipped instead of erroring.
- **Doc-map self-healing.** `tests/test_doc_file_refs.py` fails if a
  navigation-layer doc (agents.md / README / TASKMAP / CLAUDE stubs) names a
  `lua/*.lua` file that doesn't exist — the gap that had left four stale
  `ui_actionbar.lua` references in agents.md after that file was split. Those
  references are now fixed.
- **Retired the finished plan.** `compartmentaliseplan.md` (all phases shipped)
  moved to `Archive/`; the standing improvement punch-list is
  `structuralimprovements.md`.

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
