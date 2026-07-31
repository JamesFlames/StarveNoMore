# Starve No More — Week Arc & Doom Track

> Part of the **Starve No More** design doc — [back to the index](../../StarveNoMoreDesignConcept.md).

## 14. The Week Arc and Pacing

Seven in-game days, divided into four narrative phases. This is the DST season structure ported to a tighter session length ([DontStarveVideoGamePrinciples.md §3](../../Archive/DontStarveVideoGamePrinciples.md)), explicitly mapped to the **Jo-Ha-Kyu** dramatic arc ([PrinciplesOfGoodBoardGames.md §9](../../Archive/PrinciplesOfGoodBoardGames.md) — Pacing and the Game Arc).

| Phase | Days | Jo-Ha-Kyu beat | Tone | Doom/Day | Phase Boss |
|---|---|---|---|---|---|
| 1 — Dusk of the Week | 1–2 | **Jo** (slow open) | Calm, exploratory. Resources are findable. Players learn the map. Day 1 opens on the fixed **First Dawn** (§15.9), so the deck only covers Day 2. | +1 | None |
| 2 — Strange Days | 3–4 | **Ha** (break) | Pressure rises. Threats appear regularly. | +1 | The Deerclops (mid-tier; Day 4) |
| 2.5 — The Grove Wakes | Dusk of Day 4 | **Ha** (aftershock) | Interlude mini-boss. The map itself pushes back. | — | The Treeguard (mini-boss; scheduled, not deck-drawn — §14.2) |
| 3 — Long Nights | 5 | **Ha → Kyu** (pivot) | Boss night. Major disruption. | +1 | The Eye of Terror (heavy boss) |
| 4 — Final Hours | 6–7 | **Kyu** (rapid climax) | Survival sprint. Doom races — mostly from what festers. Day 7 opens on the fixed **Last Dawn** (§15.7). | +2 | The Source (final boss; MUST be destroyed by end of Day 7 — §16.1; splits at 5 HP — §12.6) |

The pacing math is deliberate: roughly half the campaign is *Jo*-style exploration where players learn and plan, but the second half compresses sharply. This produces the felt arc players describe as "having a story," not just "having a session." Mid-game compression is the cure for the runaway-leader and dead-turn problems ([PrinciplesOfGoodBoardGames.md §16](../../Archive/PrinciplesOfGoodBoardGames.md) — Pitfalls; the feedback-loop mechanics behind them are §8) — late-game decisions matter more than early ones, so a perfect early game cannot win the game alone.

### 14.1 Phase boss arrivals

Each phase boss is a Threat-card-style enemy that appears on a specific Dawn card during its phase. Bosses:

- **Pre-warn.** A Dawn card the day before announces them.
- **Disrupt rules.** While present, change the game state ("All Sanity costs are doubled while The Deerclops is on the map").
- **Reward when defeated.** A boss kill must feel like it *rescued the week*, not merely stopped a penalty (an earlier draft rewarded only a passive Trophy, and simulation showed boss-avoidance dominating — the reward side has to be loud). On defeat:
  - **Doom rolls back**: Deerclops **−2**, Eye of Terror **−3**. (The Source ends the game; no rebate needed.) The one moment all week the public track lurches the *right* way — let the table cheer.
  - **Spoils**: 3 resources shower onto the boss's tile.
  - **The Trophy** — a unique **build-around**, not a stat bump: the Antler Sled (Deerclops) lets a Move carry a co-located ally; the Watching Jar (Eye) lets the team preview and reorder the top 2 Threat cards each Dusk. A Trophy is a new verb the team plays with, and the retold loot of the campaign.
  - **Spectacle** (TTS build): the boss's roar loop cuts mid-roar, the lighting flashes, and a boss-specific kill line lands in chat — a kill is an event, not a log entry.

Bosses are placed on a specific location determined by the Dawn card. The team must travel to or defend against them.

### 14.2 The Treeguard (Phase 2.5 mini-boss)

Between the Deerclops and the Eye of Terror sits a smaller, stranger fight. At **Dusk of Day 4** — always, scheduled by the clock rather than drawn from a deck — a **Treeguard** unfolds itself at a random sport court. The neighborhood has been feeding on the courts all week: broken bleachers for Wood, hoops for Metal, nets for Cloth. On Day 4, the timber notices.

- **Stats:** HP 5, Attack 2 — tougher than any night threat, softer than a phase boss.
- **While it stands:** no one may **Gather at its court** (it guards the timber), and as a boss on the map it **festers Doom +1 at each Dawn** (§15.1).
- **Two outs, DST-style:**
  - **Fight it.** Standard combat (§12). Defeat: +1 Sanity to each attacker, and salvage **3 Wood** from where it stood.
  - **Appease it.** At its tile, spend an action and **2 Wood** to plant saplings. It watches, then folds back into stillness. No reward — but no wounds, and no more festering.
- **No Trophy.** It is a mini-boss; it does not count toward the Hero Run (§16.2).

Design intent, in order: (1) it is the mid-week **anti-turtling alarm** — a team camped at Ellie & Luca's kitchen must now march out to a court or eat +1 Doom per day; (2) the appeasement option is a pure **mismatched-currency** decision (pay the resource you were harvesting to keep harvesting it) and reads as instantly thematic to anyone who has played DST; (3) it is **scheduled, not deck-drawn**, so every campaign gets its Phase 2.5 beat — the shuffled Phase decks make the named bosses' arrival days wobble, and the Treeguard anchors the middle of the arc regardless.

While the Treeguard is awake, its roar library (26 sounds under `sounds/creatures/treeguard/`) loops in place of the ambient track.

---

## 15. The Doom Track and Scheduled Threats

The Doom track is the main visible loss timer, lifted directly from Cthulhu Wars (InterestingGames.md §3.3.5) but inverted (it ticks against the players, like HPHB's location track).

### 15.1 The track

A 30-step linear track on the main board. The Doom marker advances each Dawn by the **phase rate** (4-player baseline; see §15.6 for the player-count table):

- Phase 1: +1 per day.
- Phase 2: +1 per day.
- Phase 3: +1 per day.
- Phase 4: +2 per day.

The fixed clock is deliberately gentle, because most of the Doom pressure is **responsive** (below): festering threats, festering bosses, and fallen friends. The world doesn't punish you for time passing nearly as much as it punishes you for what you leave undone. (Bosses also add **no Doom on arrival** — an earlier draft charged +1/+2/+3 as each boss appeared, which double-billed the fight on top of uncapped boss festering. A boss charges the track by *staying*, not by showing up.)

On top of the phase rate, Doom is **responsive to the state the players leave the world in**:

- **Festering threats.** At each Dawn, Doom advances **+1 for every ordinary Threat card still on the map**, capped at +3 per Dawn (a bad night can't cascade into an instant loss). A threat fled from, ignored, or left at 1 HP is not a saved action — it is a loan against the Doom track. This is what makes Fight, Cleanse, and finishing fights genuinely competitive with self-care actions.
- **Festering bosses.** Bosses are **exempt from the cap**: each phase boss on the map festers **+2 per Dawn** (the Treeguard mini-boss +1, §14.2). The cap exists so chaff can't snowball; bosses are not chaff. A team that decides to wait out the Deerclops is choosing to pay +2 Doom every single morning it stands — ignoring THE monster is never the cheap line. (Simulation showed that under a shared +3 cap, a boss-avoidance strategy comfortably out-performed engaging them; uncapped boss festering is what makes the boss fights economically real.)
- **Fallen friends.** Whenever a character goes Down, **Doom +1** immediately (§16.4). The dark feeds on collapse.

The clock is therefore partly in the players' hands: a clean map and a standing team hold Doom near the phase rate; a sloppy week compounds. If the marker reaches **30 before the team survives Day 7**, the team loses. Players can also push Doom back through specific "Cleanse" actions (see §15.3) — which the responsive sources make an actually-rational spend, not a theoretical one.

### 15.2 Doom thresholds (passive escalation)

The Doom track has annotated thresholds that change ongoing rules:

- **At 10:** The night phase threat draw is +1.
- **At 15:** **Scarcity** — every Market craft costs **+1 extra resource** of any type the crafter holds (their choice). (Replaced an earlier "refill 1 Market slot per day" rule, which reduced options without adding tension. Scarcity pressures instead of bores: players still see the full rotating market — they just can't quite afford it.)
- **At 20:** All characters lose +1 Sanity at the night Tick.
- **At 25:** Boss-level threats can appear in any phase — and **Nothing Left to Lose**: every character gains **+1 attack die** in all combat, and **Rest also restores +1 Health anywhere** (non-stacking with the at-home bonus). Every other threshold is a punishment; 25 is the moment the team *stops being afraid*. Doom 25 with the shared clock at 25/30 is already near-death — the buff is textbook negative feedback (catch-up that arrives as the *third act*), turning the most-dreaded number on the board into one desperate teams play toward. It cannot snowball: it only triggers when the co-op clock is nearly spent, and it helps everyone symmetrically.
- **At 30:** Game over.

### 15.3 Pushing back Doom

Players can spend an action and a specific resource bundle (typically: 1 of each: Wood, Cloth, Battery, Energy Drink — i.e., representative of community ritual) to do a **Cleansing**, reducing Doom by 2. This is rare, expensive, and a key strategic decision: do you spend this action on yourself, or on the world?

The other way to push Doom back is **violence**: phase-boss kills rebate the track directly (Deerclops −2, Eye −3 — §14.1). Cleansing is the quiet communal answer; the boss fight is the loud one. Both exist so the "spend on the world" decision has a fighter's path and a homebody's path.

### 15.4 Charlie attacks

Echoing DST's Charlie ([DontStarveVideoGamePrinciples.md §4](../../Archive/DontStarveVideoGamePrinciples.md)): any character at night without a light source suffers a Charlie attack — **2 Sanity + 1 Health**, escalating by **+1 to each for every consecutive night that character spends in darkness**. A night with light resets the escalation. Coco is immune. Some boss-phase rules disable certain light sources.

Deterministic by design (§1.4 "clever desperation"): losses must read as a chain of visible mistakes, not a die spike. One dark night is a survivable, legible lesson; making a habit of darkness is what kills. The escalation also makes light logistics a *week-long* plan rather than a nightly coin-flip.

### 15.5 Severity scaffolding (the dot system)

Borrowed from Catan's probability dots (InterestingGames.md §2.3.2): Dawn cards and Threat cards print a **severity rating** as 1–5 dots in the top corner. The dots are not used in any rule — they are pure information design.

- ●○○○○ — atmospheric flavor only.
- ●●○○○ — minor stat hit (1 of one stat).
- ●●●○○ — combat-grade or lasting effect.
- ●●●●○ — phase-shift event (changes ongoing rules).
- ●●●●● — boss arrival or apocalyptic Dawn.

This solves the new-player problem: a new player can see a 5-dot Dawn card and instinctively brace, even before reading the text. Experienced players use the dots to plan inventory and movement. The same component teaches at two skill levels — Catan's probability-dots pattern, ported to a horror co-op.

### 15.6 Doom rate scaling by player count

The doom-per-day rate is balanced for the 4-player baseline. Player counts adjust the rate:

| Players | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|
| 3 | +1 | +1 | +1 | +1 |
| 4 (default) | +1 | +1 | +1 | **+3** |
| 5 | +1 | +1 | +2 | +2 |

**Phase 4 at 4 players was +2 until the batch-5 calibration** (§20.1's third ordered knob). The Last Nerve valve had lifted the best simulated lines to 50–52%, above §20.2's 40–50% band; +3 lands them at 40–42% with losses still falling ~100% on Days 6–7. It is deliberately the *last* phase only: raising Phase 3 as well overshoots to ~22%, and raising Phase 3 alone undershoots at ~35–39%. The knob does nothing at 3 players (99.3% → 99.4%), where the roster and the policy dominate the clock — see §20.1.

Rationale: more bodies at the table means more occupied tiles at night, more threat draws, and therefore more *responsive* Doom (festering) — so the fixed clock ticks slightly faster at higher counts to a lesser degree than it used to, not more. (Retuned 2026-07: the original table — 3p up to +2, 4p up to +3, 5p up to +3 — was calibrated before uncapped boss festering and the mandatory Source. Simulation showed it made 5-player games nearly unwinnable, with ~90% of losses to Doom, while the responsive sources now carry the late-game pressure the old flat rates were simulating. The Monte Carlo probe in `scripts/simulate_balance.py` validates the ordering; the exact 40–50% human win-rate target in §20.2 still needs playtests — the probe's combat model is too crude to certify it.)

### 15.7 The Last Dawn

Day 7's Dawn is **fixed**, not drawn: *"THE LAST DAWN — the sky is trying to lighten. Survive until it's over."* No penalty, no effect — pure tone, the first Dawn all week that isn't a threat. It is scheduled by the clock and bypasses the Phase 4 deck entirely (the same pattern as the Treeguard, §14.2 — the deck only ever has to cover Day 6). Predictable structure, unpredictable details — the DST seasons principle the Phase decks already follow, applied to the finish so every campaign lands on the same held breath. A physical `P4_LAST_DAWN` card for the print edition is deferred; the TTS build scripts it.

### 15.8 Night Sounds and the dread of information

Two batch-3 effects sharpen dread through *information design* alone — telegraphed unknowns, never new randomness (the legible-losses contract, §1.4, is untouched):

- **Night Sounds.** At Dusk, if the top card of the Threat deck is a **Hard** threat, a distant growl plays across the table **and a waning moon appears in the Phase Banner**. No rule text, no mechanical tell, deliberately unexplained — veterans learn to brace; new players just feel the hair go up. It adds zero randomness: it merely *voices* a draw that was already going to happen. The knowledge that something is coming, without knowing what, is the core of horror. Discipline: only on Hard, only at Dusk, once, at low volume — the silence between growls is what makes the growl land. The moon clears at the next Dawn.

  **Why it is double-coded.** An earlier version of this section claimed the growl "reveals nothing gameable." That was wrong: it reveals exactly one bit — *the next threat is Hard* — and the section itself said veterans "learn to brace," which is the admission that it is information. Delivered on audio alone, that bit was unavailable to deaf and hard-of-hearing players, and to anyone playing muted or in voice chat with game audio down, which is a large fraction of the real audience for a virtual-tabletop mod. It was the one place this game's otherwise strong double-coding discipline (severity dots §15.5, boss standee scale §5, the red-bordered constraint panel §10.2) lapsed. The visual twin carries the **same single bit and no more** — not which threat, not where — so the design intent survives intact; only the channel count changed. The standing rule is now §18.19 item 2: every audio cue that carries information has a visual twin.
- **The Wrongness** (§9.4) applies the same principle to a physical object: a known-but-unresolved threat on the map converts a random Night draw into a *decision with anticipation* — the who-goes-to-look argument is the story.

### 15.9 The First Dawn (the guided opening)

Day 1's Dawn is **fixed**, not drawn — the bookend to the Last Dawn (§15.7): *"THE FIRST MORNING — the street looks exactly as it always has, which is somehow worse. Gather what you can. The dark is eight hours away."* Severity ●○○○○, no penalty, one line of tone and a printed nudge. It bypasses the Phase 1 deck entirely, so that deck only ever has to cover Day 2.

**Why the opening needs scaffolding at all.** First turns are structurally the hardest turn in most games ([PrinciplesOfGoodBoardGames.md §9](../../Archive/PrinciplesOfGoodBoardGames.md) — Pacing and the Game Arc): widest options, least context. Here turn one asks a brand-new player to choose among 8 action types across a 5-tile map with a 3-action budget, a private hand of 5 cards, a personal perk set, a constraint and a Signature — immediately after a 12-step setup (§17.1). [§22](../../Archive/PrinciplesOfGoodBoardGames.md) — Onboarding — identifies the guided opening as the highest-value, lowest-cost intervention available, and §19.6 item 9 is still ❌ (no blind playtest yet), so this is the cheapest thing that can be done before one.

The design's onboarding instincts elsewhere are strong — the severity dots (§15.5) teach at two skill levels, the Phase Banner (§11) walks the round, the player boards are built to be read without the rulebook (§10.2), the "Rules in effect" panel keeps Scenario state visible (§17.3). What was missing was guidance on the *first decision*, which is the one with none of that context yet.

Two components:

1. **The fixed Day 1 Dawn**, above. This uses the precedent the design already established twice: the Last Dawn (§15.7) and the Treeguard (§14.2) are both scheduled rather than drawn, on the stated logic that **predictable structure with unpredictable details** is the DST seasons principle. The cost is exactly the trade §15.7 already made at the other end of the week: Day 1 stops being a surprise.
2. **A per-character suggested opening**, printed privately to each player on their first turn of Day 1 and only then — *"Ellie — try: Gather with Knows the Pantry (pick Food), Gather again, then Cook for everyone standing in your kitchen. One action, the whole team fed."* It is phrased as the whole three-action turn rather than a first step, because **the classic unrecoverable turn-one mistake is not a wrong action; it is three actions spent without a plan.** Each one demonstrates the loop and half of them teach the cooperation dividend (§8.5).

The character briefing (§18.16 step 3) already ends with "Your first move," but that is a setup popup the player dismissed several minutes and one Dawn card ago. This is the same advice at the moment it is actionable.

**Risk: nearly none.** A suggestion is not a constraint, and it fires once. **Cost:** one scripted Dawn plus five one-line strings; no rules change.

---
