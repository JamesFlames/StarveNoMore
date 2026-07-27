# Starve No More — Design Rationale & Balancing

> Part of the **Starve No More** design doc — [back to the index](../../StarveNoMoreDesignConcept.md).

## 19. Design Rationale Cross-Reference

For traceability, every major design decision is tagged with its inspiration source. A second subsection (§19.5) self-audits against the Designer's Checklist from [PrinciplesOfGoodBoardGames.md](../../Archive/PrinciplesOfGoodBoardGames.md).

| Decision | Source | Rationale |
|---|---|---|
| Three-stat trade-off economy | DST §2 ([DontStarveVideoGamePrinciples.md](../../Archive/DontStarveVideoGamePrinciples.md)) | The heart of DST's decision-making. Mismatched currencies force interesting choices. |
| Day/night cycle with forced retreat | DST §4 | Built-in pacing rhythm; creates the campfire moment. |
| Phase-based week arc with bosses | DST §3, §10 | Game arc; rising tension; climactic punctuation. |
| Soft permadeath via ghost state | DST §7 | Death is meaningful but doesn't eliminate the player. |
| Asymmetric characters with hooks + constraints | DST §6, Cthulhu Wars §3.3.1 (InterestingGames.md) | Each character plays a different game; cooperation requires complementary roles. |
| 5 unique location tiles with special actions | DST §1, Catan §2.3.1 | Suburban map as DST world; tiles as Catan-style modular geography. |
| Doom track | Cthulhu Wars §3.3.5 + HPHB §1.3.5 | Visible loss timer; the game's main dramatic arc. |
| Market deck of craftable items | HPHB §1.3, Cthulhu Wars (spellbook unlocks) | Engine-building progression; encourages varied strategies. |
| Crockpot recipes | DST §2 + Catan trading | Cooking is a social magnet; encourages co-location. |
| Open negotiation / trading | Catan §2.3.8 | The replayability engine: other humans are infinite content. |
| Multiple paths to victory (Pristine, Truth, Hero) | Catan §2.3.9 + general design theory ([PrinciplesOfGoodBoardGames.md §12](../../Archive/PrinciplesOfGoodBoardGames.md) — Victory Conditions Frame Everything) | Replayability through varied goals. Note the honest accounting in §19.6 item 5: these are achievements layered on one victory path, and the strategic diversity claim rests on *strategies*, not win conditions. |
| Dawn card "world acts first" | HPHB §1.3.3 | No turn is safe; pressure is constant. |
| Full 3-action turns (default) + one-action-then-pass **Rotation variant** (§11.2) | Cthulhu Wars §3.2 | The default keeps a new player's turn coherent (plan 3 actions as one thought); the Rotation variant is the Cthulhu Wars downtime cure — at 5 players it cuts the wait between your decisions from up to 12 consecutive foreign actions to 4. Which one the table prefers is an explicit playtest A/B (§20.2). |
| Visible component scale (boss standees larger) | Cthulhu Wars §3.4 | Information design through physical hierarchy. |
| Variable map setup (3 path configurations) | Catan §2.3.1 | Cheap replayability lever. |
| Hand limit forces trade | Catan §2.3.5 (the "7 effect") | Discourages hoarding; forces interaction. |

### 19.5 Anti-alpha-player design

In a co-op game with public boards, the most common failure mode is the **alpha player problem**: one experienced player optimizes every decision for the table while everyone else watches. Starve No More fights this on five fronts ([DontStarveVideoGamePrinciples.md §9](../../Archive/DontStarveVideoGamePrinciples.md), [PrinciplesOfGoodBoardGames.md §20](../../Archive/PrinciplesOfGoodBoardGames.md) — Cooperative Games Are a Different Genre; the general interaction chapter is §10):

1. **Private item hands.** Every character's Item cards are face-down in their hand zone. Other players can suggest plays but cannot read the actual options. The owner has a private creative space.
2. **Asymmetric perks and constraints.** A James player and an Ellie player are good at *different* things. The optimal play for one is rarely the optimal play for another, so a single brain cannot drive everyone correctly.
3. **Ghost word-limit.** Down players can speak only one word per round to the team (§16.4). This stops a "dead" alpha from quarterbacking the survivors. (It also produces some of the game's funniest moments.)
4. **Soft turn timer (optional).** Default rules suggest a 60-second sand timer per player turn during Day Phase. Strictly optional, but groups with a known alpha player should turn it on — it short-circuits over-optimization.
5. **Trade-not-give.** When a stronger player wants to "fix" a weaker player's hand, they must publicly trade for it. The transaction is visible and reciprocal, not unilateral.

The design does *not* hide the global game state. Resources, the Doom track, and stat values are all public — that is necessary for the co-op layer to function. What is hidden is *the room to maneuver inside one player's options*. That is the right partition.

### 19.6 Designer's Checklist self-audit

[PrinciplesOfGoodBoardGames.md](../../Archive/PrinciplesOfGoodBoardGames.md) closes with a 10-item Designer's Checklist. Running this design against it:

| # | Check | Status |
|---|---|---|
| 1 | Can you name the emotion the game targets in one sentence? | ✅ "Cozy dread" — §1.4. |
| 2 | Does each turn present at least one meaningful choice with real trade-offs? | ✅ The 3-action budget combined with the mismatched-currency map (§8.4) makes every action a choice. |
| 3 | Is there a rule you're keeping out of fondness? | ✅ Acted on — the Visitor **adoption** sub-rule was cut (§9.5); Visitors are now one-shot aid only. The deck itself stays, at near-zero rules cost. |
| 4 | Do mechanics and theme reinforce each other? | ✅ Hunger/Sanity/Health, the Crockpot social magnet, Charlie attacks, and Telltale Heart sacrifice all are *consequences* of the world, not arbitrary rules. |
| 5 | At least 2–3 viable paths to victory? | ⚠️ **Rewritten to audit strategies, not win conditions.** There is exactly **one** victory path — survive seven days, hold Doom under 30, kill the Source — and §16.2 says so plainly: Pristine/Truth/Hero "are not separate goals; they are achievements layered on top of survival." The old ✅ ("four overlapping goals") contradicted §16.2 and answered a different question. What the checklist item is actually asking is whether there are 2–3 genuinely *different ways to survive the week*, which is how a co-op satisfies strategic diversity. The simulator says **two**: the "turtle" line and the "spread" line, at **42% and 41%** after the Source-HP knob (§20.1). Two is a pass, narrowly, and it is a real measured result rather than a claim. **Open question: is there a third?** Two candidate lines the design gestures at and has never measured — a Cleanse-heavy "hold the world back" line (§15.3) and a Pry/Basement/craft-rush line (§13.5). Until one of them is measured viable, the replayability argument (§15's "three viable strategies is three games in the box; one is one") rests on two, not three. |
| 6 | Different feel in early/mid/end game? | ✅ Jo-Ha-Kyu mapping (§14). Early days are exploratory; Day 5+ is climactic. |
| 7 | Stress-tested for runaway leader, kingmaking, AP, elimination? | ✅ Co-op (no runaway leader); ghost word-limit (no kingmaking); soft turn timer (AP); ghost state (no elimination). |
| 8 | Does player interaction generate stories? | ✅ Mismatched currency forces visible deals; the worked example in §11.6 shows the table-talk window naturally. |
| 9 | Has the rulebook been read by someone who wasn't in the room while you wrote it? | ❌ Pending — everything a blind playtest needs is now built (batch 4): session telemetry with a one-click export, the facilitator script and feedback form in `playtest/`, and a calibrated Standard difficulty. Two independent blind groups completing a game flips this. |
| 10 | Have you played it enough to be sick of it and still want to play again? | ❌ Pending — the retention question ("do you want to play again right now?") is on the feedback form; yes-without-prompting is the only pass. |

Two ❌ marks are acceptable at v1 (this document is the brief, not a finished game). Item 3's ⚠️ is the single most actionable note: the Visitor deck must justify itself in playtests or be cut.

---

## 20. Balancing, Playtest Plan, Expansion Hooks

### 20.1 Known balance risks

- **Coco's lack of house** — penalty is strong; if it's too punishing, allow her to "claim" a temporary home each game.
- **Rayman's loud movement penalty** — needs tuning; could make him underplayed if too harsh.
- **Doom track rate** — retuned 2026-07 to the §15.6 table (3p [1,1,1,1] / 4p [1,1,1,2] / 5p [1,1,2,2], no boss arrival Doom) after simulation showed the old table made 5p nearly unwinnable. The residual risk has inverted: with a gentle fixed clock, most Doom is now responsive (festering) — if playtests show diligent teams cruising, raise Phase 3–4 rates by +1 before touching festering.
- **Boss lethality under the mandatory Source** — the Source must be killed to win, and the sim's crude combat model loses ~20–30% of games to it or to Downs accumulated across three boss fights in four days. **Knob taken (batch 4 W3, 2026-07): Source HP 10 → 8** — the single sanctioned change that put the sim's best line in the 40–50% band (turtle 34%→42%, spread 27%→41%) with losses still clustering on Days 6–7. Trophy healing remains the next knob if tables still find the Final Hours a meat grinder.
- **Hand limit (5 cards)** — may need to be 6 to allow comfortable crafting; playtest both.
- **Telltale Heart cost** — 2 Health from reviver is significant; if revival is too rare, lower to 1 Health.
- **Festering Doom (+1/threat cap +3; bosses +2 uncapped) and Down Doom (+1)** — target end-of-game Doom around 18–26 on a Standard win; if games routinely blow past 30 by Day 5, lower the ordinary-threat cap to +2 before touching phase rates. Do NOT re-cap boss festering — the uncapped boss rate is what keeps boss-avoidance from being the dominant strategy (simulation-verified; see §15.1).
- **Charlie escalation (2/1 base, +1/+1 per consecutive dark night)** — watch whether two consecutive dark nights is a death sentence for low-Health characters; if so, escalate Sanity only.
- **Crowded floor (2 beds per house)** — check the 5-player geometry (forced 2/2/1 split); if the floor rule reads as pure punishment, let a Bedroll item add a third bed.
- **Moonlit Salvage (2 resources)** — the court-sleep gamble should be tempting roughly once per game per team, not a camping strategy; if court-camping dominates, drop to 1 resource + 1 Echoes roll.
- **Loud (moved today = +1 Threat at Rayman's night tile)** — watch whether Rayman players simply never move; if so, the constraint is over-tuned — soften to "moved 3+ tiles today."
- **3-player composition inequality (simulation flag, 2026-07; reliefs implemented batch 4 W2)** — the `--sweep3` composition sweep found 3-character teams ranging from ~86% to ~0.5% win rate under their best scripted policy: every viable trio includes Coco or Luca, and all six Rayman trios collapsed (his Big Appetite + Loud overheads don't shrink with the team). **Both cheap knobs from the candidate menu are now implemented, behind a `playerCount == 3` guard:** Big Appetite costs 2 Hunger only on days Rayman fought or moved 2+ tiles, and Loud requires 3+ tiles moved. Sweep after: the floor gate passes (worst trio 31% under its best policy, nothing near 0) — but the sim *over-corrects*, putting Rayman trios at the top (97–99%), because Loud was the only Rayman cost it models against his fully-modeled combat value. The Big Appetite knob alone moved almost nothing (the collapse was Loud→Charlie→Sanity-6, not Hunger). **Verdict: the sim brackets the answer; the real tuning decision belongs to the W2 table A/B** — a Rayman trio must be confirmed fun at a real 3-player table before this is closed. Do not fix it with roster restrictions (§6.6).
- **Flee (1 tile, 1 Sanity, threat festers)** — watch for flee-chaining as a free evasion loop; the Sanity bleed plus fester Doom should make three flights in a week feel expensive. If not, raise to 2 Sanity.
- **The Stash (2 Energy Drinks per gather at James's)** — if James stops visiting home entirely after one mega-stock, cap held Energy Drinks at 4.
- **Haunted (personal Threat at Dawn)** — the isolation is now buyable-into: an ally at your tile may pay 1 Sanity to see what you see and fight it with you (§10.1). Watch two things: whether the buy-in is *always* taken (in which case the isolation horror is gone and the price should rise to 2 Sanity), and whether it is *never* taken (in which case 1 Sanity is not the barrier — the barrier is being at the wrong tile, and the rule is dead weight). The lethality knob is still in reserve: cap Haunted threats at 2 HP.
- **Last Nerve (§10.1.1) — measured, and it moved the number.** Simulated at 400 games/policy, 4 players, comparing against the same build with the valve disabled:

  | Build | turtle | spread | turtle loss:down | turtle loss:source |
  |---|---|---|---|---|
  | No Last Nerve (the §20.2 item-5 calibration baseline) | 42.2% | 41.5% | 27.3% | 0.2% |
  | Free Flee only | 51.2% | 50.2% | 11.8% | 5.0% |
  | Free Flee + Rest bonus (shipped) | 51.0% | 50.2% | 12.0% | 5.2% |

  Three things to read off this. **(1) Free Flee is the entire effect** — the Rest bonus is worth ~0 pp in the sim, because the sim's rest policy triggers at Sanity ≤ 4 while the valve needs a stat below 3, and it does not model the Hunger/Sanity choice at all. The Rest half is kept because it is the half that *reads* at the table (a visible reward for resting when cornered), and it is the first half to cut if the endgame proves too soft. **(2) It does what it was built to do**: turtle's "everyone collapsed" losses fell by more than half, 27.3% → 11.8%. **(3) It converted those into boss losses** (0.2% → 5.0% unfought-Source). That is a strictly better *shape* of loss under §25's agency audit — the team lost a fight it chose to take rather than dissolving — but it is also a real difficulty reduction: **the best line now sits at ~51%, just above the 40–50% band §20.2 item 5 targets.**

  **Do not compensate for this by retuning Standard yet.** Per [§17](../../Archive/PrinciplesOfGoodBoardGames.md) — Improving an Existing Game — Last Nerve, the Haunted buy-in, the secret-Dusk variant and the difficulty axis all push difficulty the same way, and they must not be evaluated together or the combined effect is attributable to none of them. Standard's numbers stay where they are pending table data; the new **Story** mode (§17.2) is where a gentler game now lives. If tables confirm the Final Hours are too soft, the ordered knobs are: drop the Rest half of Last Nerve, then Source HP 8 → 9, then Phase 3–4 Doom rate +1.

### 20.2 Playtest plan

1. **Solo paper test** (designer + 2 hands) — verify the loop works mechanically, identify dead turns. 3 days only.
2. **3-player teach-and-play** — 3 days, then 7 days. Watch for analysis paralysis.
3. **5-player full game** — confirm the table doesn't get overwhelmed; check that 5 characters all feel relevant.
4. **Blind playtest** — give the rules to a group with no designer present; observe what they get wrong. Fix the rulebook accordingly.
5. **Stress test difficulty** — repeat plays with the same group to find the win rate (target: 40–50% on Standard difficulty for experienced groups). *Status (batch 4 W3, 2026-07): calibrated on the simulator — best line 42% with ~100% of losses on Days 6–7, via the Source HP 10 → 8 knob; the three difficulty modes (§17.2) are selectable at setup. Table confirmation pending; each session's Copy Session Log export feeds this.*
6. **Turn-structure A/B (5 players)** — play one full game with default 3-action turns and one with the Rotation variant (§11.2), same group. Watch for: time between one player's decisions, phone-checking during others' turns, and whether Rotation fragments planning ("I forgot what my second action was for"). This decides whether Rotation stays a variant, becomes the 5-player default, or gets cut. *Status (batch 4 W0/W1): fully instrumented — the session log records `turnStyle` and per-turn durations in seconds, so the two games are directly comparable. Protocol in [playtest/facilitator_script.md](../../playtest/facilitator_script.md). Decision pending table data.*
7. **Scenario pass** — once the base game's win rate is settled, one game per Scenario (§17.3) to catch degenerate combinations (e.g., Total Blackout with a Coco-less team that can't survive dark nights).
8. **Option utilization** — *"which of this game's options does anybody actually use?"* [§26](../../Archive/PrinciplesOfGoodBoardGames.md) — Measuring a Design — calls this "the single most actionable report a simulator or session log produces" and notes it is the metric most often skipped. This repo was unusually well placed to collect it (a simulator, a session log, a one-click export) and collected none of it. Now instrumented on both sides:

   - **Session logs** (`scripts/analyze_sessions.py`) report, across N logged games, the fraction in which each Market item is crafted, each recipe cooked, each action type taken, each location visited, each Visitor drawn and each Trophy earned — **scored against the full catalog in `content/`**, so options nobody has ever touched appear as explicit zeros instead of being invisible. Sorted ascending; the top of each list is the cut-candidate end. (Session log schema 2; schema-1 logs still aggregate for everything else.)
   - **The simulator** (`--utilization`) reports the action mix and where the team actually sleeps.

   **Predictions, recorded so the report either confirms or refutes them** (§26's discipline: write the prediction down *before* the data arrives):

   | Prediction | Status |
   |---|---|
   | Cleanse is rarely used | ✅ **Confirmed, and starkly.** Across 400 games/policy: ≤1.5% of all actions on the best line, and **0.00 per game** for two of four policies. A 4-resource bundle plus an action for Doom −2 competes badly against boss rebates of −2/−3 that also pay spoils and a Trophy. |
   | The Badminton Court is visited less than the Basketball Court | ⚠️ **Not testable in the simulator, and the apparent zero is an artifact.** Every policy's `berths()` hardcodes `COURTS[0]` (Basketball, for Rayman's Court Master), so no policy can ever choose Badminton. The probe encodes the very assumption the prediction was meant to test. Needs a court-choosing policy or table data. |
   | The Visitor deck is under-used | ⏳ Needs table data — the sim has no Visitors. This is §19.6 item 3's standing question, and it is substantially a *measurement* question rather than a judgement call: if Visitors are drawn in 90% of 3-player games and change the outcome they stay; if they are drawn and ignored they go. |
   | Several of the 49 Market items are never crafted | ⏳ Needs table data — the sim abstracts the Market to two craft targets. |

   The Cleanse result is actionable now and deliberately **not** acted on in this pass: it is a fifth change pushing difficulty in the same direction as findings 6–9, and §17's regression list forbids evaluating those together. Recorded as a knob, not spent.

### 20.3 Expansion hooks (post-launch)

- **More characters.** A Year 2 box adds 5 new survivors (e.g., a Musician, a Mechanic, a Dog).
- **More locations.** Extend the map to 8 locations: Library, Convenience Store, the Park.
- **The Source's Backstory** (campaign mode). A 5-game arc where decisions persist between sessions: which characters survived, which clues were found, what the Source actually was. (Borrowing HPHB's box-progression idea, InterestingGames.md §1.3.6.)
- **Co-op vs. Traitor variant.** One player secretly serves the Source. Raises the game's social-deduction layer.
- **Solo mode.** Single player controls 2–3 characters as a personal cast.

### 20.4 What's deliberately not in the design

In line with [PrinciplesOfGoodBoardGames.md §3](../../Archive/PrinciplesOfGoodBoardGames.md) (cut, fuse, generalize):

- **No tech tree beyond the Market.** A second tech progression would bloat the rules; the Market deck handles "tier" via card costs.
- **No weather system.** Already implemented via Dawn cards; a separate die or chart would duplicate.
- **No XP leveling.** Characters don't grow during a game; the Item cards are their progression.
- **No formal alliances/factions.** This is a co-op game; faction layers would dilute the cooperation pillar.
- **No resource market beyond player trade.** The Catan-style 4:1 bank trade tempted us, but adding it would weaken the social trade layer.

---

## Closing Notes

This document is the v1 design brief for Starve No More. It is written to be:

1. **Complete enough to playtest from.** A team could prototype on paper this week.
2. **Specific enough to implement in TTS.** Every component is mapped to a TTS object type.
3. **Open enough to iterate.** Numbers (stat values, costs, rates) are starting points, not gospel — playtesting will move them.

Next steps:
1. Build a paper prototype.
2. Run two solo playtests to debug the core loop.
3. Run a 3-player teach-and-play.
4. Refine, then begin asset production for the TTS implementation.
5. Once art and components are stable, build the TTS save per [HowToCreateGamesInTabletopSimulator.md §9](../../Archive/HowToCreateGamesInTabletopSimulator.md).

The game succeeds when: a group of three friends plays through a seven-day campaign, loses on Day 6 to the Eye of Terror, immediately resets, and starts over with different characters. That is the test. Everything in this document is in service of that outcome.

---

*Reference documents (archived; preserved for traceability):*
- [Archive/PrinciplesOfGoodBoardGames.md](../../Archive/PrinciplesOfGoodBoardGames.md) — design theory.
- [Archive/DontStarveVideoGamePrinciples.md](../../Archive/DontStarveVideoGamePrinciples.md) — DST translation.
- InterestingGames.md — patterns from HPHB, Catan, Cthulhu Wars (notes retired 2026-07; recover from git history).
- [Archive/HowToCreateGamesInTabletopSimulator.md](../../Archive/HowToCreateGamesInTabletopSimulator.md) — TTS implementation guide.
