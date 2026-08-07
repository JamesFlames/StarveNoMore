# Balance: the Scenario cards

What the Monte Carlo probe says about the eight week-long twists setup draws
from — and which teams can survive each one.

*Part of the [agent reference](README.md); the index and the documentation map
live in [`agents.md`](../../agents.md). The model itself and its policies:
[balance-simulation.md](balance-simulation.md). The map's shape and player
count: [balance-map-and-rosters.md](balance-map-and-rosters.md).*

Run: 2026-08, `--rules new`, Standard, defence on, Star, 600-3000 games/cell
(+-1-2 points at 2000, +-2 at 600).

```bash
python scripts/simulate_balance.py --sweep-scenario --sims 2000
python scripts/simulate_balance.py --matrix scenario --policy turtle --sims 600
python scripts/simulate_balance.py --scenario SC_WINTER --sims 2000
```

## Read this first: the camp beats everything

Batch 6 fixed three movement gaps in the sim (below). One of them moves every
number on this page: **Rayman's Loud used to be hardcoded on**, so a team that
never moved was still charged the extra nightly threat card his §6.2 constraint
only levies on a day he *moved*. Applied as written, a house camp draws
**nothing at all** at night until Doom 10, because `LOCATION_THREAT_RATE`
(night.lua) is 0 at all three houses.

| policy | batch 5 | batch 6 (Loud as written) | batch 6b (printed rules) | **batch 7 (The Gathering)** |
|---|---|---|---|---|
| turtle (everyone camps at Ellie & Luca's) | 40.3% | 97.9% | 99.9% | **73.8%** |
| spread (gather near home, sleep at home) | 42.0% | 86.6% | 90.4% | **90.4%** |
| balanced (engage the map, fight the bosses) | 16.2% | 18.9% | 33.8% | 30.2% |
| court_camper | 13.9% | 24.9% | 37.4% | 33.1% |
| net_camper | 8.2% | 20.9% | 34.1% | 30.1% |

4 players, Star, no Scenario, 3000 games. The **entire** 40–50% calibration in
[balance-simulation.md](balance-simulation.md) was resting on that hardcode: it
was the only thing charging a stationary team anything. The design's stated
anti-stacking pressure (crowded floor, festering bosses, §15.1) is real but
nowhere near enough — a 4-player camp banks 25+ Provisions it never needs and
loses only to the Doom clock, which it beats 999 times in 1000.

Batch 6b then wired two rules the board had been printing at players and
nothing implemented (the Badminton Court's threat rate, and the per-tile Tick
Sanity modifier — see
[balance-map-and-rosters.md](balance-map-and-rosters.md)). Both were correct to
fix and both pushed the same way: the Kitchen's printed **+1 Sanity at Tick**
is a bonus for never leaving the tile the camp already sits on.

**Batch 7 shipped the answer**: The Gathering (§15.10) — from Day 3, a tile
holding three or more characters draws +1 Threat unless a boss stands there.
Camping falls to 74%, and the tables below are measured with it on
(`--knob nogathering` reproduces the row before it).

Everything below is therefore reported **per strategy**, not as a single "win
rate": the `turtle` column is what a table that discovers camping reaches, and
`balanced` is what a table that plays the map as designed reaches. The gap
between those two columns is the real balance problem; the columns themselves
are the answer to "which Scenario / which map / which team is harder".

**The ceiling is now `spread`, not `turtle`.** One character per house is a
second free strategy at 90%, and The Gathering cannot reach it — three separate
houses never put three heads on a tile. The priced answer to that one is open:
[balance-recommendations.md](balance-recommendations.md).

## Scenario × strategy (4 players, Star)

| Scenario | turtle | spread | balanced | court_camper | net_camper |
|---|---|---|---|---|---|
| No Scenario *(control)* | 72.8% | 89.9% | 31.9% | 33.9% | 31.0% |
| **The Long Winter** | **7.9%** | 63.5% | 0.5% | 0.8% | 0.7% |
| The Scorching Summer | 71.9% | 89.7% | 10.9% | 12.7% | 8.6% |
| The Rotting Autumn | 75.3% | 88.7% | 3.7% | 4.6% | 3.8% |
| The False Spring | 90.9% | 90.3% | 26.4% | 27.2% | 25.5% |
| **Total Blackout** | **11.7%** | 66.9% | 24.5% | 24.3% | 24.5% |
| Strict Rationing | 72.7% | 82.1% | 32.0% | 35.3% | 32.1% |
| **The Full Moon** | **100.0%** | 89.1% | 38.7% | 39.3% | 36.5% |
| **The Shortcut** | 72.8% | **15.2%** | 9.4% | 11.3% | 9.9% |

Five readings, all measured **with** The Gathering:

1. **Two cards now break a camp outright.** The Long Winter takes it to 7.9%
   and Total Blackout to 11.7%. Both were near-harmless to a camp before the
   new rule (44% and 98%): the extra nightly card is what turns "doubled Hunger
   decay" and "no light in the world" from an inconvenience into a fight the
   camp has to win every night. The Gathering did not just cost camping 26
   points on the control row — **it re-armed the Scenario deck**, which had
   been aiming at a strategy that took no nights.
2. **The Full Moon is the exception, and now a glaring one**: 100.0% for
   camping, the only card in the deck the new rule does not dent. `noCharlie`
   removes a guaranteed drain and `softToHard` only adds monsters where cards
   are drawn — and four fighters in one room kill whatever The Gathering sends.
   Every "add pressure" fix was priced and rejected (they all punish spreading
   out instead): [balance-recommendations.md](balance-recommendations.md).
3. **The Shortcut is a spread-killer and nothing else** (89.9% → 15.2%). It
   puts +1 threat on James's House and the Badminton Court every night, and
   `spread` is the one line that sleeps at James's House. Its upside is 1
   Hunger; its downside is a nightly extra card at two tiles.
4. **The Rotting Autumn is a tax on spreading out** — 75% camping against 3.7%
   for engaged play. One Provisions per *occupied tile* per Dawn charges you
   for holding ground, which is the opposite of what "cook them before you lose
   them" suggests, and the opposite of what the week is trying to encourage.
5. **Total Blackout's teeth are in a place worth knowing.** The Telltale Heart
   revive costs 1 Battery, so in a Blackout **Coco's Spare Phone Battery is the
   only revive in the game** — on a Coco-less roster a Down character stays
   down all week. That is why the BLACKOUT column below splits so sharply by
   roster rather than by strategy.

## Team × Scenario (the composition question, asked per card)

`--matrix scenario`, 400 games/cell, Star. Under **camping**, two columns now
decide everything — and each is a different single character:

| team | WINTER | BLACKOUT | none | mean over all 9 |
|---|---|---|---|---|
| 4p James+Coco+Ellie+Luca | 42% | 45% | 94% | **83%** |
| 5p all five | 33% | 37% | 94% | 82% |
| 3p James+Coco+Luca | **0%** | 46% | 94% | 79% |
| 4p James+Coco+Rayman+Luca | **0%** | 38% | 91% | 76% |
| 3p James+Coco+Ellie | 29% | 34% | 85% | 76% |
| 3p Coco+Rayman+Luca | **0%** | 69% | 83% | 75% |
| 3p Coco+Ellie+Luca | 57% | 53% | 75% | 73% |
| 3p Coco+Rayman+Ellie | 27% | 78% | 68% | 72% |
| 3p James+Coco+Rayman | **0%** | 35% | 86% | 72% |
| 4p Coco+Rayman+Ellie+Luca | 29% | 56% | 72% | 70% |
| 3p James+Rayman+Luca | **0%** | 46% | 76% | 67% |
| 4p James+Coco+Rayman+Ellie | 7% | **13%** | 73% | 64% |
| 3p James+Rayman+Ellie | 37% | 72% | 54% | 61% |
| 3p James+Ellie+Luca | 43% | 27% | 60% | 60% |
| 4p James+Rayman+Ellie+Luca | 19% | **16%** | 65% | 59% |
| 3p Rayman+Ellie+Luca | 18% | 30% | 32% | 37% |

**The Long Winter still needs Ellie.** Six teams sit at exactly **0%** and all
six lack her; every team with her clears 7–57%. Doubled Hunger decay plus
`foodGatherPenalty` closes the food economy, and Knows the Pantry's guaranteed
+1 plus Crockpot Master's 1-Provisions meal is the only thing that beats both.
Three candidate fixes were priced and all three rejected — see
[balance-recommendations.md](balance-recommendations.md); this one needs a
design decision, not a constant.

**Total Blackout is now a second, softer gate, and it points at Coco.** With
no Batteries in the world the Telltale Heart cannot be built, so the only
revive all week is Coco's Spare Phone Battery. The Blackout column tracks that
almost perfectly: Coco-less teams sit at 13–30% while Coco+Rayman trios reach
69–78%.

Note what is *not* here any more: with The Gathering on, the "none" column runs
32–94% instead of a flat 98–100%. **Composition is legible again without a
Scenario card doing the work.**

### Engaged play (`--policy balanced`)

Column means: no Scenario 27%, Winter 3%, Summer 20%, Autumn 16%, Spring 26%,
Blackout 24%, Rationing 28%, Full Moon 49%, Shortcut 20%.

| team | none | WINTER | FULL_MOON | mean over all 9 |
|---|---|---|---|---|
| 4p James+Coco+Ellie+Luca | 74% | 18% | 91% | **65%** |
| 5p all five | 70% | 3% | 88% | 53% |
| 3p Coco+Ellie+Luca | 56% | 4% | 93% | 51% |
| 3p James+Ellie+Luca | 56% | 9% | 92% | 45% |
| 4p Coco+Rayman+Ellie+Luca | 46% | 2% | 90% | 43% |
| 3p James+Coco+Ellie | 46% | 1% | 50% | 32% |
| 3p Rayman+Ellie+Luca | 23% | 1% | 83% | 23% |
| 3p Coco+Rayman+Ellie | 28% | 2% | 38% | 20% |
| 4p James+Coco+Rayman+Ellie | 31% | 0% | 38% | 19% |
| 4p James+Rayman+Ellie+Luca | 8% | 1% | 61% | 12% |
| 3p James+Rayman+Ellie | 8% | 8% | 29% | 9% |
| 3p James+Coco+Luca | 10% | 0% | 8% | 6% |
| 3p Coco+Rayman+Luca | 6% | 0% | 8% | 5% |
| 4p James+Coco+Rayman+Luca | 6% | 0% | 6% | 3% |
| 3p James+Rayman+Luca | 1% | 0% | 4% | 1% |
| 3p James+Coco+Rayman | 0% | 0% | 0% | **0%** |

The spread is 0–65% and it is **not** a player-count story: the best team is a
4p, the third and fourth are 3p, and the full 5p roster is second. It is an
Ellie story at the top (the four best teams all have her) and a Rayman story at
the bottom (nine of the bottom ten carry him). The standing caveat matters more
than ever: **his costs are fully modeled and most of his value is not** —
Defend, Court Master, Speed's reach, Trophies — so read his rows as a floor.

