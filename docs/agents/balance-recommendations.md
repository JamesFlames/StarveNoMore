# Balance recommendations, priced

Candidate rule changes with a number attached, in the order they should be
taken. Two have shipped; the rest are `--knob`s in the Monte Carlo probe, so
any of them can be re-priced in a minute before it is written into `lua/` —
including the ones **rejected on price**, which is most of them.

*Part of the [agent reference](README.md); the index and the documentation map
live in [`agents.md`](../../agents.md). The evidence:
[balance-scenarios.md](balance-scenarios.md) and
[balance-map-and-rosters.md](balance-map-and-rosters.md). The model:
[balance-simulation.md](balance-simulation.md).*

```bash
python scripts/simulate_balance.py --sims 2000 --knob night6
python scripts/simulate_balance.py --sims 2000 --knob nogathering   # batch-7 control
python scripts/simulate_balance.py --scenario SC_WINTER --knob winterlate
```

The design target is **40–50% wins for an experienced group on Standard**
(§20.2). One recommendation from the first pass has shipped; the ceiling is now
**90%**, held up by a different strategy than before.

## Status

| # | recommendation | state |
|---|---|---|
| 1 | The crowd rule | **shipped** as The Gathering (§15.10), in its gentler form |
| 2 | Doom night threshold 10 → 6 | open — this is now the top item |
| 3 | Source HP 8 → 9 | open, take after 2 |
| 4 | The Long Winter's roster gate | open; both cheap fixes priced and **rejected** |
| 5 | The Full Moon is the easiest card | open; every "add pressure" fix priced and **rejected** |
| 6 | The blind setup draw | **shipped** for the Scenario; the path variant never had the problem |

## The problem, in one table

4 players, Star, no Scenario, 1500 games/cell.

| knobs | turtle | spread | balanced | court | net | best |
|---|---|---|---|---|---|---|
| `nogathering` *(pre-batch-7 control)* | 99.9% | 90.5% | 33.4% | 37.3% | 34.3% | 100% |
| **shipped** | 72.8% | **90.5%** | 31.8% | 33.7% | 30.6% | **90%** |
| + `night6` | 68.0% | 61.5% | 25.0% | 26.1% | 23.3% | **68%** |
| + `night6` + Source HP 9 | 62.5% | 55.9% | 22.5% | 24.0% | 21.7% | 63% |
| + `crowd` *(the harsher Gathering)* | 15.9% | 90.5% | 25.3% | 27.9% | 25.7% | 90% |
| + `floorcost` | 48.9% | 90.5% | 28.1% | 30.9% | 28.5% | 90% |
| + `kitchenflat` | 39.0% | 87.2% | 15.5% | 18.8% | 16.3% | 87% |

Read the `spread` column down: **90.5% in every row that does not contain
`night6`**. Nothing aimed at huddling touches it, because one character per
house never puts three heads on a tile. That is the whole remaining problem.

## Recommendation 1 — the crowd rule *(SHIPPED, batch 7)*

Shipped as **The Gathering** (§15.10): *from Day 3, a tile where three or more
characters spend the Night draws +1 Threat — unless a boss is already standing
there.* Turtle 99.9% → **72.8%** at 4 players (57% at 3p, 93% at 5p).

The always-on, no-exemption version is still available as `--knob crowd` and
still prices at 15.9%. It was not taken: the Day-3 delay keeps the opening
calm, and the boss exemption stops the rule punishing the convergence the
design spends the whole week demanding (§16.3.3). The 5-player number is the
weak spot — a bigger group fights the extra card off — and is the first thing
to re-measure at a table.

## Recommendation 2 — move the Doom "+1 Threat everywhere" threshold from 10 to 6

**This is now the top item.** `spread` — one character per house, ignore the
map — sits at 90.5% and is untouched by everything else in the table. Its
engine is that three houses at 0 threats each is a free week, and the only
thing that ever ends it is the Doom-10 bump on about Day 5. At **Doom 6** it
arrives around Day 3–4 and the back half of the week has nights in it:
spread 90.5% → 61.5%, ceiling 68%.

One constant (`DOOM_THRESHOLDS.night`), already written for exactly this
purpose.

## Recommendation 3 — then re-price the Source

With 2 taken, the ceiling is 68%. §20.1's **knob 2 (Source HP 8 → 9)** is the
unused gentler alternative and still works: 63%, a clean −5. Take it after 2,
at a table, not before — it does nothing about free nights.

`kitchenflat` (removing the Kitchen's +1 Tick Sanity) is in the table as a
**control, not a candidate**: it lands the ceiling at 87% while costing the
fighting lines 16 points, and it does it by un-printing a rule the board
states.

## Recommendation 4 — The Long Winter is a roster gate, and no cheap fix works

**Finding:** every team without Ellie wins **0%** under The Long Winter; every
team with her wins 45–97%. Five of sixteen rosters cannot win at all. The gate
is the *stack*: `hungerDecayX2` doubles the drain while `foodGatherPenalty`
closes the only tap that keeps up, and Ellie (Knows the Pantry's guaranteed +1,
Crockpot Master's 1-Provisions meal) is the only character who beats both.

Three fixes were priced. **All three were rejected, so nothing shipped:**

| candidate | what it does | why not |
|---|---|---|
| `winterpantry` — the freeze spares the Kitchen | opens the gate (Ellie-less trios 11% → 99%) | hands the *camp* its food back: turtle 46% → 92%. It exempts precisely the tile a huddling team already sits on. |
| `winterlate` — doubled decay from Day 4 | half-opens it (Coco+Rayman+Luca 11% → 51%) | leaves James+Coco+Rayman at 1.0% and James+Rayman+Luca at 3.8%, and softens the card overall (46% → 74%) |
| recipes cost 1 less all week | — | 0.8% → 0.8% on the broken teams. Does nothing. |

The gate is real and the cheap levers all miss it, so this needs a **design**
decision rather than a constant: give the Winter a counterplay that is not food
(the scenario already carries `housesSanityBonus` — a second non-food clause is
the natural shape), or accept it as the deck's hard card and say so on it.
§6.6 promises any three of the five are a team; today one card in eight voids
that for a third of the rosters.

## Recommendation 5 — The Full Moon is the easiest card, and pressure cannot fix it

**Finding:** it is the best card in the deck for every strategy — turtle
**100%** even after The Gathering, balanced 38.7% against 31.9% with no
Scenario at all — while its text promises the opposite. `noCharlie` removes a
*guaranteed* nightly Sanity and Health drain; `softToHard` adds monsters only
where threat cards are drawn, and the tiles a team sleeps on draw none.

Every "add pressure" fix was priced and **all were rejected**, for the same
reason each time — a camp kills whatever you send and a lone sleeper does not,
so pressure lands on the players who are already spread out:

| candidate | turtle | spread | balanced |
|---|---|---|---|
| as shipped | 100.0% | 89.1% | 38.7% |
| `moonlit` — every tile draws at least 1 Threat | 99.9% | **0.1%** | 3.9% |
| `moonwake` — +1 Sanity at Tick in place of Charlie | 100.0% | 57.8% | 19.2% |

**Recommended:** stop trying to make the card harder and make its *trade* real
— the two halves have to land on the same tile. "Charlie does not attack, but
every tile where a Threat is drawn draws one more" is the version that costs
the dark-sleeper what it gives them. Failing that, accept it as the deck's
relief card and rewrite the flavour to stop promising teeth.

## Recommendation 6 — the blind setup draw *(SHIPPED, batch 7)*

The Scenario used to be drawn and announced at the *end* of setup, after the
roster was locked — and the composition gates live in the Scenario (see 4). It
is now drawn and read out at the variants step, before the character picks, and
*applied* after the characters exist, because SC_SUMMER edits their stats.

The path variant never had this problem: guided setup has always picked it at
step 1. What remains is the spread itself — under `balanced` the variants price
at Ring 19%, Star 39%, Compact 39%, Linear 45%, Sprawl 46% (mean over sixteen
rosters), and single teams swing further (Coco+Ellie+Luca 95% on Star, 13% on
Ring). §7.6 calls that "slightly vary the movement geometry". It is not slight,
and Ring — the shipped board — is the outlier that strips the centre of two
edges. Narrowing the variants is a real option; it was not priced here.

## What none of this measures

The probe is a dynamics model, not a rules engine. Trophies, most Market
items, and most of Rayman's kit (Defend, Court Master, Speed's tactical reach)
are unmodeled, and all of them pay the boss-fighting lines — so `balanced` at
23–33% is a floor, and the gap between camping and fighting is narrower at a
real table than these tables show. What the probe *can* certify is the
ordering, and the ordering says camping is free. Recommendations 1 and 2 are
about that; everything after them should wait for a table.
