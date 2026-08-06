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

| policy | batch 5 (Loud hardcoded) | batch 6 (Loud as written) |
|---|---|---|
| turtle (everyone camps at Ellie & Luca's) | 40.3% | **97.9%** |
| spread (gather near home, sleep at home) | 42.0% | **86.6%** |
| balanced (engage the map, fight the bosses) | 16.2% | 18.9% |
| court_camper | 13.9% | 24.9% |
| net_camper | 8.2% | 20.9% |

4 players, Star, no Scenario, 3000 games. The **entire** 40–50% calibration in
[balance-simulation.md](balance-simulation.md) was resting on that hardcode: it
was the only thing charging a stationary team anything. The design's stated
anti-stacking pressure (crowded floor, festering bosses, §15.1) is real but
nowhere near enough — a 4-player camp banks 25+ Provisions it never needs and
loses only to the Doom clock, which it beats 98 times in 100.

Everything below is therefore reported **per strategy**, not as a single "win
rate": the `turtle` column is what a table that discovers camping reaches, and
`balanced` is what a table that plays the map as designed reaches. The gap
between those two columns is the real balance problem; the columns themselves
are the answer to "which Scenario / which map / which team is harder".

Two knobs to price if you want the camp to cost something (neither measured —
they are design decisions, not sim findings): a non-zero house threat rate once
the Doom track opens, or making the crowded floor bite harder than "no regen".

## Scenario × strategy (4 players, Star)

| Scenario | turtle | spread | balanced | court_camper | net_camper |
|---|---|---|---|---|---|
| No Scenario *(control)* | 97.8% | 88.2% | 19.4% | 25.1% | 21.4% |
| **The Long Winter** | **25.1%** | 59.0% | 1.1% | 1.2% | 0.7% |
| The Scorching Summer | 97.4% | 86.8% | 9.7% | 14.4% | 10.3% |
| The Rotting Autumn | 98.2% | 85.4% | 4.3% | 5.9% | 4.6% |
| **The False Spring** | **43.5%** | 87.1% | 16.8% | 22.6% | 18.9% |
| Total Blackout | 96.2% | 55.4% | 17.5% | 17.5% | 17.5% |
| Strict Rationing | 97.6% | 77.1% | 20.6% | 26.0% | 22.7% |
| **The Full Moon** | **100.0%** | 87.8% | 32.4% | 35.8% | 33.6% |
| **The Shortcut** | 97.8% | **12.3%** | 6.5% | 9.0% | 6.5% |

Five readings:

1. **Only two Scenarios are a real tax on a camp.** The Long Winter (−73
   points) and The False Spring (−54) are the only cards that reach a team
   sitting in a house, because they are the only two that bypass the map:
   doubled Hunger decay does not care where you sleep, and `charlieEverywhere`
   from Day 4 puts Charlie *inside the houses*. Every other Scenario is priced
   in map terms — court yields, threat rates, Market shelves — and a camp has
   opted out of all of them.
2. **The Full Moon is the easiest card in the deck, and it reads as the
   scariest.** "Charlie never attacks; all Soft threats become Hard" trades a
   guaranteed nightly Sanity+Health drain for extra monsters *at the tiles
   where threats are drawn* — and a house draws none. It is a straight buff to
   camping (100%) and the best card for engaged play too (32% vs 19%). If it is
   meant to be a hard mode, `softToHard` needs to reach houses, or `noCharlie`
   has to cost something.
3. **The Shortcut is a spread-killer and nothing else** (88% → 12%). It puts
   +1 threat on James's House and the Badminton Court every night, and
   `spread` is the one line that sleeps at James's House. The free road is
   worth far less than the threat rate at both ends: a scenario whose upside is
   1 Hunger and whose downside is a nightly extra card.
4. **The Rotting Autumn's spoilage is invisible to a camp** (98%) and brutal to
   engaged play (19% → 4%). One Provisions per occupied tile per Dawn is a flat
   tax on *spreading out* — the more tiles you hold, the more you lose — which
   is the opposite of what the card's flavour ("cook them before you lose
   them") suggests it does.
5. **Total Blackout hurts the wrong line.** It costs the camp 2 points and
   `spread` 33, because its bite is "no Batteries in the world" and only a team
   working the houses was buying Flashlights in the first place. Note the
   interaction the sim had to model explicitly: the Telltale Heart revive costs
   1 Battery, so in a Blackout **Coco's Spare Phone Battery is the only revive
   in the game** — on a Coco-less roster a Down character stays down all week.

## Team × Scenario (the composition question, asked per card)

`--matrix scenario`, 600 games/cell, Star. Two strategies, because they answer
different questions: what a camping table gets away with, and which teams can
actually play the map.

### Camping (`--policy turtle`)

| team | none | WINTER | SPRING | FULL_MOON | other 5 (mean) | mean |
|---|---|---|---|---|---|---|
| 3p Coco+Ellie+Luca | 100% | 82% | 88% | 100% | 100% | 96% |
| 4p James+Coco+Ellie+Luca | 100% | 60% | 100% | 100% | 100% | 96% |
| 3p Coco+Rayman+Ellie | 100% | 63% | 87% | 100% | 100% | 94% |
| 5p all five | 100% | 54% | 94% | 100% | 99% | 94% |
| 4p Coco+Rayman+Ellie+Luca | 99% | 66% | 81% | 100% | 99% | 93% |
| 3p Coco+Rayman+Luca | 100% | **0%** | 99% | 100% | 100% | 89% |
| 3p James+Coco+Ellie | 95% | 33% | 93% | 99% | 95% | 88% |
| 3p Rayman+Ellie+Luca | 99% | 96% | **2%** | 100% | 99% | 88% |
| 4p James+Coco+Rayman+Luca | 100% | **0%** | 92% | 100% | 99% | 88% |
| 3p James+Coco+Rayman | 100% | **0%** | 95% | 100% | 99% | 87% |
| 3p James+Coco+Luca | 98% | **0%** | 93% | 99% | 97% | 86% |
| 4p James+Coco+Rayman+Ellie | 98% | 28% | 44% | 100% | 97% | 84% |
| 3p James+Rayman+Luca | 99% | **0%** | 19% | 100% | 98% | 79% |
| 4p James+Rayman+Ellie+Luca | 90% | 32% | 14% | 99% | 89% | 76% |
| 3p James+Ellie+Luca | 74% | 32% | 13% | 95% | 72% | 64% |
| 3p James+Rayman+Ellie | 53% | 38% | **2%** | 100% | 45% | 46% |

**Two hard composition gates, and each is a single character:**

* **The Long Winter needs Ellie.** Every one of the five Ellie-less teams wins
  **0%**; every team with her wins 28–96%. Doubled Hunger decay plus
  `foodGatherPenalty` means raw Provisions cannot keep up, and Ellie is the
  only character who makes the food economy work at the kitchen (Knows the
  Pantry's guaranteed +1, and Crockpot Master's 1-Provisions meal). This is a
  §6.6 "any 3 of the 5" violation with a hard edge: not "harder without her",
  *impossible* without her.
* **The False Spring needs Coco** (or a Flashlight nobody can build). From Day
  4 Charlie checks every tile; a camp at the kitchen can never craft a
  Flashlight, because the centre's draw table has no Metal and no Battery.
  Coco is Charlie-immune and James starts with a light, so teams holding
  neither collapse: Rayman+Ellie+Luca 2%, James+Rayman+Ellie 2%,
  James+Ellie+Luca 13%, James+Rayman+Ellie+Luca 14%.

Note that both gates are invisible on the "No Scenario" column, where 13 of 16
teams sit at 98–100%. **Composition only matters once a Scenario is on the
table** — which is always, since setup draws one.

### Engaged play (`--policy balanced`)

Column means: no Scenario 29%, Winter 5%, Summer 24%, Autumn 21%, Spring 22%,
Blackout 29%, Rationing 29%, Full Moon 41%, Shortcut 20%.

| team | none | WINTER | FULL_MOON | mean over all 9 |
|---|---|---|---|---|
| 4p James+Coco+Ellie+Luca | 88% | 45% | 89% | **79%** |
| 3p Coco+Ellie+Luca | 79% | 5% | 85% | 67% |
| 3p James+Ellie+Luca | 74% | 10% | 88% | 55% |
| 5p all five | 64% | 7% | 83% | 50% |
| 4p Coco+Rayman+Ellie+Luca | 48% | 4% | 80% | 43% |
| 3p James+Coco+Ellie | 41% | 1% | 42% | 29% |
| 3p Rayman+Ellie+Luca | 14% | 1% | 66% | 16% |
| 4p James+Coco+Rayman+Ellie | 19% | 1% | 30% | 14% |
| 3p Coco+Rayman+Ellie | 16% | 1% | 30% | 13% |
| 3p James+Coco+Luca | 12% | 0% | 12% | 7% |
| 4p James+Rayman+Ellie+Luca | 4% | 0% | 25% | 6% |
| 3p Coco+Rayman+Luca | 6% | 0% | 7% | 5% |
| 4p James+Coco+Rayman+Luca | 4% | 0% | 7% | 3% |
| 3p James+Rayman+Luca | 1% | 0% | 5% | 1% |
| 3p James+Rayman+Ellie | 1% | 1% | 5% | 1% |
| 3p James+Coco+Rayman | 0% | 0% | 0% | **0%** |

The spread here is 0–79%, and it is **not** a player-count story: the best team
is a 4p, the second and third are 3p, and the full 5p roster is fourth. It is a
Rayman story, exactly as batch 5 recorded — every team in the bottom half
carries him, and the top four are the four teams that do not. The standing
caveat still applies and matters more than ever here: **his costs are fully
modeled (Big Appetite, Loud, tank-takes-all-counters) and most of his value is
not** (Defend, Court Master, Speed's tactical reach, Trophies). Read his rows
as a floor, not a verdict — but note that Loud is now modeled *correctly*, and
its correct form makes him worse in exactly the situations the old hardcode was
hiding: he is the one character who cannot camp for free.

