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

| policy | batch 5 (Loud hardcoded) | batch 6 (Loud as written) | batch 6b (+ printed-rule fixes) |
|---|---|---|---|
| turtle (everyone camps at Ellie & Luca's) | 40.3% | 97.9% | **99.9%** |
| spread (gather near home, sleep at home) | 42.0% | 86.6% | **90.4%** |
| balanced (engage the map, fight the bosses) | 16.2% | 18.9% | 33.8% |
| court_camper | 13.9% | 24.9% | 37.4% |
| net_camper | 8.2% | 20.9% | 34.1% |

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

Everything below is therefore reported **per strategy**, not as a single "win
rate": the `turtle` column is what a table that discovers camping reaches, and
`balanced` is what a table that plays the map as designed reaches. The gap
between those two columns is the real balance problem; the columns themselves
are the answer to "which Scenario / which map / which team is harder".

Priced answers, in the order to take them:
[balance-recommendations.md](balance-recommendations.md). The short version is
that there are *two* free strategies — one house (`turtle`) and one-per-house
(`spread`) — and the crowd rule the game already owns as a Dawn-card effect
answers only the first.

## Scenario × strategy (4 players, Star)

| Scenario | turtle | spread | balanced | court_camper | net_camper |
|---|---|---|---|---|---|
| No Scenario *(control)* | 99.9% | 90.5% | 34.0% | 37.5% | 34.2% |
| **The Long Winter** | **44.4%** | 62.0% | 1.4% | 1.6% | 1.4% |
| The Scorching Summer | 99.8% | 89.5% | 16.2% | 18.8% | 13.6% |
| The Rotting Autumn | 99.9% | 90.0% | 6.2% | 7.4% | 6.0% |
| The False Spring | 95.2% | 89.9% | 28.8% | 31.9% | 29.8% |
| Total Blackout | 98.5% | 65.1% | 34.3% | 34.3% | 34.3% |
| Strict Rationing | 99.9% | 82.1% | 36.0% | 39.5% | 36.8% |
| **The Full Moon** | **100.0%** | 88.6% | 42.0% | 43.1% | 39.0% |
| **The Shortcut** | 99.9% | **14.6%** | 10.7% | 12.2% | 10.7% |

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

`--matrix scenario`, 500 games/cell, Star. Under **camping** every team clears
98–100% on eight of the nine columns, so only two columns discriminate at all:

| team | WINTER | SPRING | other 7 |
|---|---|---|---|
| 3p Rayman+Ellie+Luca | 97% | **45%** | 100% |
| 3p Coco+Ellie+Luca | 86% | 90% | 100% |
| 3p James+Ellie+Luca | 75% | 87% | 99% |
| 4p James+Coco+Ellie+Luca | 69% | 99% | 100% |
| 4p Coco+Rayman+Ellie+Luca | 69% | 89% | 100% |
| 5p all five | 67% | 97% | 100% |
| 3p Coco+Rayman+Ellie | 66% | 100% | 100% |
| 4p James+Rayman+Ellie+Luca | 65% | 89% | 100% |
| 3p James+Coco+Ellie | 51% | 95% | 99% |
| 4p James+Coco+Rayman+Ellie | 47% | 95% | 100% |
| 3p James+Rayman+Ellie | 45% | 93% | 100% |
| 3p Coco+Rayman+Luca | **0%** | 100% | 100% |
| 4p James+Coco+Rayman+Luca | **0%** | 98% | 100% |
| 3p James+Coco+Rayman | **0%** | 99% | 99% |
| 3p James+Rayman+Luca | **0%** | 100% | 100% |
| 3p James+Coco+Luca | **0%** | 96% | 99% |

**The Long Winter is a roster gate, not a difficulty.** Every one of the five
Ellie-less teams wins **0%**; every team with her wins 45–97%. Doubled Hunger
decay plus `foodGatherPenalty` closes the food economy, and only Ellie (Knows
the Pantry's guaranteed +1, Crockpot Master's 1-Provisions meal) beats both at
once. §6.6 promises any three of the five are a team; this card voids that for
a third of the rosters. Priced fixes:
[balance-recommendations.md](balance-recommendations.md#recommendation-4--the-long-winter-is-not-a-difficulty-it-is-a-roster-gate).

**The False Spring has a softer version of the same gate.** Charlie checks
every tile from Day 4, and a camp at the Kitchen can never craft a Flashlight
(the centre's draw table has no Metal and no Battery). Coco is Charlie-immune
and James starts with a light, so the one team holding neither — Rayman+Ellie
+Luca — sits at 45% while everyone else clears 87%.

### Engaged play (`--policy balanced`)

Column means: no Scenario 39%, Winter 7%, Summer 31%, Autumn 26%, Spring 29%,
Blackout 37%, Rationing 39%, Full Moon 50%, Shortcut 29%.

| team | none | WINTER | FULL_MOON | mean over all 9 |
|---|---|---|---|---|
| 4p James+Coco+Ellie+Luca | 91% | 45% | 91% | **83%** |
| 3p Coco+Ellie+Luca | 95% | 6% | 95% | 78% |
| 3p James+Ellie+Luca | 83% | 16% | 92% | 67% |
| 5p all five | 78% | 9% | 90% | 60% |
| 4p Coco+Rayman+Ellie+Luca | 60% | 4% | 92% | 54% |
| 3p James+Coco+Ellie | 49% | 1% | 50% | 35% |
| 3p Rayman+Ellie+Luca | 41% | 2% | 83% | 34% |
| 4p James+Coco+Rayman+Ellie | 37% | 2% | 42% | 24% |
| 3p Coco+Rayman+Ellie | 30% | 2% | 40% | 22% |
| 3p James+Rayman+Ellie | 15% | 18% | 34% | 15% |
| 4p James+Rayman+Ellie+Luca | 9% | 3% | 63% | 15% |
| 3p James+Coco+Luca | 12% | 0% | 12% | 8% |
| 3p Coco+Rayman+Luca | 7% | 0% | 7% | 5% |
| 3p James+Rayman+Luca | 6% | 0% | 9% | 5% |
| 4p James+Coco+Rayman+Luca | 6% | 0% | 6% | 4% |
| 3p James+Coco+Rayman | 0% | 0% | 0% | **0%** |

The spread is 0–83% and it is **not** a player-count story: the best team is a
4p, the second and third are 3p, and the full 5p roster is fourth. It is a
Rayman story — every team in the bottom half carries him, and three of the top
four do not. The standing caveat matters more than ever here: **his costs are
fully modeled and most of his value is not** (Defend, Court Master, Speed's
reach, Trophies), so read his rows as a floor. Loud is now modeled correctly,
and its correct form makes him worse in precisely the case the old hardcode
hid: he is the one character who cannot camp for free.
