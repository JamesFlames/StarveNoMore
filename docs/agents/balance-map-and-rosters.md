# Balance: the map, the roster, and the batch-6 model fixes

What the Monte Carlo probe says about the path variant setup draws, the size
and shape of the team, and the four modelling gaps closed in batch 6.

*Part of the [agent reference](README.md); the index and the documentation map
live in [`agents.md`](../../agents.md). The model itself and its policies:
[balance-simulation.md](balance-simulation.md). The Scenario cards — including
the camping finding that frames every number here:
[balance-scenarios.md](balance-scenarios.md).*

Run: 2026-08, `--rules new`, Standard, defence on, no Scenario, 600-3000
games/cell.

```bash
python scripts/simulate_balance.py --sweep-topology --sims 2000
python scripts/simulate_balance.py --sweep-roster   --sims 1000
python scripts/simulate_balance.py --matrix topology --policy balanced --sims 600
```

## Path variant × strategy (4 players, no Scenario)

| Variant | roads | turtle | spread | balanced | court_camper | net_camper |
|---|---|---|---|---|---|---|
| Star | 4 | 72.8% | **89.9%** | 31.9% | 33.9% | 31.0% |
| Ring *(shipped default)* | 5 | 72.7% | 52.9% | 34.8% | 28.1% | 17.7% |
| Compact | 6 | 72.8% | 50.9% | 33.9% | 38.0% | 34.7% |
| Sprawl | 10 | 72.8% | 52.9% | **47.2%** | 43.1% | 36.1% |
| Linear | 4 | 73.8% | 50.9% | 38.3% | 37.5% | 31.4% |

1. **The map is worth nothing to a camp and ~15 points to everyone else.**
   Turtle is flat at 72.8–73.8% across all five variants — it walks once on Day
   1 and then never moves, so the graph might as well not exist. Even The
   Gathering (§15.10) does not change that: it costs a camp the same extra card
   on every map. `balanced` swings 32% → 47%, and `net_camper` 18% → 36%.
2. **Sprawl and Linear are the easy maps** for engaged play. Sprawl is the
   intuitive direction (one move reaches anything); Linear is not, and it wins
   because its chain puts a court next to every house. Either way the effect is
   far bigger than the design's "slightly vary the movement geometry" (§7.6)
   implies — a third of the win rate is not a garnish.
3. **Star flatters `spread` for a structural reason worth knowing**: no court
   is adjacent to Rayman's House on Star, so the policy keeps him home; on
   every other variant a court is one tile away, he works it, and the tile's
   threat rate plus Loud costs the team ~40 points. "Gather next door" is a
   trap on the open maps.
4. **Which map is hardest depends on who is on the team.** On this roster
   (the standard 4p: James+Coco+Rayman+Ellie) Star is `balanced`'s worst map;
   averaged over all sixteen rosters it is Ring — the variant the shipped board
   prints — at a column mean of 19% against Star's 39% and Sprawl's 46% (see
   the matrix below). Ring has *more* roads than Star and is
   still harder for most teams, because its five roads form a cycle: the centre
   loses its edge to two of the four other tiles, so a kitchen team pays double
   to reach the courts. Road count is not difficulty; who is adjacent to what
   is.

## Team × path variant

`--matrix topology`, 500 games/cell, no Scenario.

**The map only speaks to a team that uses it** — under `balanced` the column
means are Star 29%, Ring 17%, Compact 32%, Sprawl 42%, Linear 34%, and
individual teams swing far harder than the column:

| team | Star | Ring | Compact | Sprawl | Linear |
|---|---|---|---|---|---|
| 3p James+Ellie+Luca | 55% | 45% | **84%** | 86% | 76% |
| 4p James+Coco+Ellie+Luca | 74% | **31%** | 72% | 74% | 65% |
| 5p all five | 70% | 64% | 65% | 81% | 78% |
| 4p Coco+Rayman+Ellie+Luca | 46% | **24%** | 46% | 66% | 50% |
| 4p James+Coco+Rayman+Luca | 6% | 11% | 4% | 22% | **29%** |

A kitchen team loses 43 points moving from Star to Ring; a Rayman team gains 23
moving from Star to Linear. **No team's ranking survives
the map draw**, which means a table that judges "is this trio any good?" is
really judging the variant it happened to draw. If the design wants
compositions to have stable identities, the variant should not be a blind
random draw at setup — or the variants need to be closer together than
"one move reaches anything" vs "the houses are four moves apart".

## Player count

Camping per count after The Gathering: **3p 57%, 4p 74%, 5p 93%** — a bigger
group fights the extra card off more easily, so the rule bites hardest at the
counts where a camp was most cramped anyway. The 5-player number is the rule's
weak spot and the first thing to re-measure at a table. Under `balanced` the
counts separate differently — 3p 41%, 4p 28%, 5p 69% — so the per-count Doom
rates (`DOOM_RATES`) still make 4 players the hardest count on the engaged
line. The 4p row is the one
every historic baseline was measured at, so it is also the only one that has
been tuned; 3p and 5p have never been tuned against a *correct* Loud.

## What changed in the model (batch 6)

Four sim fixes, all faithfulness, each one guarded by a test:

1. **Loud reads tracked movement** (§6.2, `raymanLoudTonight` in night.lua)
   instead of a hardcoded `True`. See the table at the top — this is the one
   that moves the headline.
2. **The Dusk scramble is one tile** (§11.3). It used to teleport a character
   to any berth for 1 Hunger, which made the map's shape free and let a strike
   pair fight at the Basketball Court and sleep at home. Anything further than
   one tile now has to be walked during the day, out of the action budget
   (`Game.commute`).
3. **Movement uses the real path variant.** Distances come from
   `scripts/path_layouts.py` — the same table the board art and the Lua Move
   adjacency are generated from — rather than "1 action to the centre, 2 to
   anywhere else". That hop model *is* Star, so Star remains the default and
   the historic baselines stay comparable.
4. **Policies became map-aware** so the bots stay competent under (2): a strike
   pair beds down next to the boss rather than pretending it can walk home, and
   `spread` gathers on a court only when a court is adjacent to the house it
   means to sleep in.

## Two printed rules that were not implemented (batch 6b)

Mirroring the location tables into the sim surfaced two rules the game states
to the player as fact and never rolled — the class
`tests/test_places_and_trophies.py` exists for. Both are now wired, mirrored,
and guarded by a CSV↔Lua cross-ref plus a behavioural test:

1. **The Badminton Court's threat rate.** `content/locations.csv` says 2, the
   tooltip says "Highest threat draw rate at Night", the `at_badminton_court`
   What-now hint says it, design §7.5 says it — and `LOCATION_THREAT_RATE`
   (night.lua) gave it 1, exactly like the Basketball Court. The tile's one
   distinctive hazard was printed three times and rolled nowhere. Now 2, which
   is what `net_camper` (17–36%) is measured against.
2. **The per-tile Tick Sanity modifier.** All five board tooltips print one
   ("+1 Sanity at Tick" at the Kitchen, "-1" at both courts), design §7.1-7.5
   gives every tile one, and the §8 cost table bills "sleeping at a court" for
   it. Nothing read the `sanity_modifier` column: the Tick charged the same 1
   wherever you slept. New `LOCATION_SANITY_MOD` (global.lua), subtracted from
   the Tick loss in `resolveTick` and floored at 0 so the Kitchen can never
   turn the Tick into a heal.

Fix 2 is correct and makes the balance problem worse: the Kitchen's printed +1
is a standing bonus for never leaving the tile the camp already occupies, and
it is worth ~+15 points to the boss-fighting lines and ~+2 to a camp already at
98%. That trade-off is priced in
[balance-recommendations.md](balance-recommendations.md) (`--knob kitchenflat`),
which recommends *against* solving it by un-printing the rule.

## Model caveats specific to these probes

The [general assumptions](balance-simulation.md#model-assumptions-documented-in-the-scripts-docstring)
all still hold. On top of them, for Scenarios:

* `slowMarket` is modeled as "one Market craft per two days" — the sim has no
  shelf, so it cannot model *which* card is missing.
* `cheapRecipes` discounts the Provisions half of a cook (never below 1); the
  sim's cooking is one abstract recipe, not the ten in `cards_recipes.csv`.
* Scenario clauses that only touch items the sim abstracts away (Energy Drink
  counts, specific Market cards) are priced through the resource pool, so the
  Scorching Summer and Strict Rationing rows are the least trustworthy.
* The Full Moon's promoted Soft threats are modeled at the statline
  `actions_combat.lua` gives them (2 HP / 1 Attack from a 0/0 line), losing
  each card's individual text.

Per-scenario modeling notes are in the `sim` field of `SCENARIOS`
(`scripts/sim_variants.py`), next to the flag set each one mirrors.
