# Balance recommendations, priced

Candidate rule changes with a number attached, in the order they should be
taken. Nothing here is shipped: each one is a `--knob` in the Monte Carlo
probe, so any of them can be re-priced in a minute before it is written into
`lua/`.

*Part of the [agent reference](README.md); the index and the documentation map
live in [`agents.md`](../../agents.md). The evidence:
[balance-scenarios.md](balance-scenarios.md) and
[balance-map-and-rosters.md](balance-map-and-rosters.md). The model:
[balance-simulation.md](balance-simulation.md).*

```bash
python scripts/simulate_balance.py --sims 2000 --knob crowd --knob night6
python scripts/simulate_balance.py --knob winterlite --scenario SC_WINTER
```

The design target is **40–50% wins for an experienced group on Standard**
(§20.2). As shipped, the best line wins **99.9%**.

## The problem, in one table

4 players, Star, no Scenario, 1200 games/cell. Every row is the shipped rules
plus the named knob(s).

| knobs | turtle | spread | balanced | court | net | best |
|---|---|---|---|---|---|---|
| **none (shipped)** | **99.9%** | 90.0% | 33.2% | 37.1% | 33.7% | **100%** |
| `crowd` | 19.2% | **90.0%** | 27.0% | 29.2% | 26.5% | 90% |
| `night6` | 99.5% | 58.1% | 28.8% | 31.8% | 28.3% | 100% |
| `floorcost` | 99.7% | 90.0% | 32.2% | 36.2% | 32.8% | 100% |
| `kitchenflat` | 98.0% | 89.0% | 18.8% | 23.9% | 19.9% | 98% |
| **`crowd` + `night6`** | 18.2% | **58.1%** | 23.2% | 25.0% | 22.5% | **58%** |
| `crowd` + `night6` + Source HP 9 | 13.4% | 54.2% | 21.8% | 23.7% | 20.3% | 54% |
| `crowd` + `night6` + `kitchenflat` | 6.1% | 52.7% | 13.7% | 16.6% | 14.0% | 53% |

There are **two** free strategies, not one, and they need different answers:

* **turtle** — everyone in one house. Free because a house draws no threats
  until Doom 10, so a camp simply has no nights.
* **spread** — one or two per house, ignore the map. Free for the same reason,
  and `crowd` does not touch it at all (it never puts three on a tile).

That is why no single knob gets under 90%: `crowd` answers the first, `night6`
answers the second, and only together do they make sleeping indoors cost
anything.

## Recommendation 1 — adopt the crowd rule as a standing rule (take this first)

**Rule:** *a tile where three or more characters spend the Night draws +1
Threat card.*

**Price:** turtle 99.9% → 19.2%. No other line moves more than 6 points.

This is the cheapest possible fix because **the game already contains it**:
`ongoingDawnEffects.crowdThreat` (`resolveNightAtLocation`, night.lua) is
exactly this rule as a Dawn-card effect, broadcast as *"It is drawn to the
gathering at X — +1 Threat"*. Promoting it from a card to a standing rule adds
no vocabulary, no component, and no new player-facing concept — the table has
already seen it happen. It also states the design's intent out loud: §15.1
wants "ignoring the map is never the cheap line", and huddling is the purest
form of ignoring the map.

Implementation: `LOCATION_THREAT_RATE` is not the place — this is a
population term. Add it in `resolveNightAtLocation` beside the existing
"alone at a sport court" clause, so the two crowd-shaped modifiers live
together, and mirror it in the sim.

## Recommendation 2 — move the Doom "+1 Threat everywhere" threshold from 10 to 6

**Rule:** the Doom-10 threshold that puts +1 Threat on every tile fires at
**Doom 6** instead (`DOOM_THRESHOLDS.night`).

**Price:** spread 90.0% → 58.1%; with recommendation 1, best line 58.1%.

`spread` is untouched by the crowd rule and is the line that survives it. Its
whole engine is that three houses at 0 threats each is a free week, and the
only thing that ever ends it is the Doom-10 bump on about Day 5. At Doom 6 that
arrives around Day 3–4 and the back half of the week has actual nights in it.
This is a one-constant change, and it is the constant already written for
exactly this purpose.

**Take 1 and 2 together.** Alone, each leaves a 90–100% line standing.

## Recommendation 3 — then re-price the Source, not the valve

With 1 + 2 the ceiling is 58%, eight points above the band. §20.1's **knob 2
(Source HP 8 → 9)** was the unused gentler alternative and it still works:
54.2%, a clean −4. Reach for it after 1 and 2 are at the table, not before —
it does nothing about camping and would just have made a 100% line a 98% one.

Do **not** reach for `kitchenflat` (removing the Kitchen's +1 Tick Sanity) as a
balance lever. It lands the ceiling at 53% but costs the *fighting* lines
another 9 points, and it does it by deleting a printed rule that just got
wired up. It is in the table as a control, not a candidate.

## Recommendation 4 — The Long Winter is not a difficulty, it is a roster gate

**Finding:** every team without Ellie wins **0%** under The Long Winter; every
team with her wins 45–97%. Five of sixteen rosters cannot win at all.

The gate is the *stack*, not either clause: `hungerDecayX2` doubles the drain
while `foodGatherPenalty` closes the only tap that keeps up, and Ellie's Knows
the Pantry (guaranteed +1 Provisions) plus Crockpot Master (a 1-Provisions
meal) is the only thing in the game that beats both at once.

Dropping `foodGatherPenalty` (`--knob winterlite`) reopens it — Coco+Rayman+Luca
11% → 99%, James+Coco+Rayman 1% → 58% — but it also takes the scenario's teeth
out (turtle 46% → 91%), so it is a diagnosis, not the fix. **Recommended:** keep
both clauses but stop them multiplying — either

* `foodGatherPenalty` applies only away from Ellie & Luca's House (the pantry
  is indoors; the *ground* is frozen), or
* `hungerDecayX2` starts on Day 4 rather than Day 1,

then re-run `--matrix scenario --policy turtle` and check the WINTER column has
no zeroes. §6.6 promises any three of the five are a team; one Scenario card in
eight currently voids that promise for a third of the rosters.

## Recommendation 5 — The Full Moon is the easiest card in the deck

**Finding:** it is the best card for every strategy (turtle 100%, balanced 42%
against 34% with no Scenario at all) while its text — "Charlie never attacks,
but the things in the moonlight are much worse" — promises the opposite.

The trade does not work because the two halves land on different tiles.
`noCharlie` removes a *guaranteed* nightly Sanity and Health drain from
whoever is standing in the dark; `softToHard` adds monsters only where threat
cards are drawn, and the tiles a team actually sleeps on draw none.

Do not fix it by adding threats: `--knob moonteeth` (+1 draw everywhere)
prices at spread 90% → **0%** and balanced 39% → 5% while turtle stays at
99.9%, because four fighters on one tile kill anything and a lone sleeper
does not. More threats punish spreading out, which is backwards.
**Recommended:** make the two halves land on the same tile — *Charlie does not
attack, but every tile where a Threat is drawn draws one more* — or accept it
as the deck's relief card and rewrite the flavour to say so.

## Recommendation 6 — decide what the path variant is for

Under `balanced`, the five variants price at Ring 19%, Star 39%, Compact 39%,
Linear 45%, Sprawl 46% (mean over all sixteen rosters), and individual teams
swing far harder — Coco+Ellie+Luca is 95% on Star and 13% on Ring; Rayman+Ellie
+Luca is 41% on Star and 74% on Linear. §7.6 calls this "slightly vary the
movement geometry". It is not slight, and it is drawn blind at setup before
anyone has picked a character.

Either narrow the variants (Ring's five-road cycle is the outlier — it strips
the centre of two edges, which no other variant does), or draw the variant
**before** characters are assigned so the roster can answer the map. The second
is free and turns a coin-flip into a decision.

## What none of this measures

The probe is a dynamics model, not a rules engine. Trophies, most Market
items, and most of Rayman's kit (Defend, Court Master, Speed's tactical reach)
are unmodeled, and all of them pay the boss-fighting lines — so `balanced` at
23–33% is a floor, and the gap between camping and fighting is narrower at a
real table than these tables show. What the probe *can* certify is the
ordering, and the ordering says camping is free. Recommendations 1 and 2 are
about that; everything after them should wait for a table.
