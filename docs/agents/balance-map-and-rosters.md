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
| Star | 4 | 97.8% | **88.3%** | 19.1% | 24.9% | 21.0% |
| Ring *(shipped default)* | 5 | 98.7% | 48.2% | 32.5% | 26.5% | 18.1% |
| Compact | 6 | 97.8% | 46.1% | 21.4% | 28.1% | 23.2% |
| Sprawl | 10 | 97.8% | 48.2% | **44.8%** | 42.8% | 32.5% |
| Linear | 4 | 98.8% | 46.1% | 33.8% | 37.2% | 27.4% |

1. **The map is worth nothing to a camp and ~25 points to everyone else.**
   Turtle is flat at 98% across all five variants — it walks once on Day 1 and
   then never moves, so the graph might as well not exist. `balanced` swings
   19% → 45%. Any lever that makes the map matter has to make *staying* cost
   something first.
2. **Sprawl is the easy map** for engaged play, which is the intuitive
   direction (one move reaches anything) but a bigger effect than the design's
   "slightly vary the movement geometry" (§7.6) implies. A quarter of the win
   rate is not a garnish.
3. **Star flatters `spread` for a structural reason worth knowing**: no court
   is adjacent to Rayman's House on Star, so the policy keeps him home; on
   every other variant a court is one tile away, he works it, and the tile's
   threat rate plus Loud costs the team ~40 points. "Gather next door" is a
   trap on the open maps.
4. **Which map is hardest depends on who is on the team.** On this roster
   (the standard 4p: James+Coco+Rayman+Ellie) Star is `balanced`'s worst map;
   averaged over all sixteen rosters it is Ring — the variant the shipped board
   prints — at a column mean of 18% against Star's 30% and Sprawl's 42% (see
   the matrix below). Ring has *more* roads than Star and is
   still harder for most teams, because its five roads form a cycle: the centre
   loses its edge to two of the four other tiles, so a kitchen team pays double
   to reach the courts. Road count is not difficulty; who is adjacent to what
   is.

## Team × path variant

`--matrix topology`, 600 games/cell, no Scenario.

Camping is flat: every team is within 2 points of its own mean across all five
variants (column means 93–94%). **The map only speaks to a team that uses it**
— under `balanced` the column means are Star 30%, Ring 18%, Compact 31%,
Sprawl 42%, Linear 36%, and individual teams swing far harder than the column:

| team | Star | Ring | Compact | Sprawl | Linear |
|---|---|---|---|---|---|
| 3p Coco+Ellie+Luca | 79% | **11%** | 79% | 79% | 61% |
| 4p James+Coco+Ellie+Luca | 88% | 37% | 89% | 88% | 75% |
| 3p Rayman+Ellie+Luca | 14% | 20% | 14% | 24% | **50%** |
| 3p Coco+Rayman+Ellie | 16% | 22% | 17% | **56%** | 42% |
| 4p James+Rayman+Ellie+Luca | 4% | 1% | 6% | **33%** | 5% |

A kitchen team (Coco+Ellie+Luca) loses 68 points moving from Star to Ring; a
Rayman team gains 36 moving from Star to Linear. **No team's ranking survives
the map draw**, which means a table that judges "is this trio any good?" is
really judging the variant it happened to draw. If the design wants
compositions to have stable identities, the variant should not be a blind
random draw at setup — or the variants need to be closer together than
"one move reaches anything" vs "the houses are four moves apart".

## Player count

Best line per count, no Scenario, Star, 3000 games: **3p 99.4%, 4p 97.9%,
5p 99.8%**. Under `balanced`: 3p 81.0%, 4p 18.9%, 5p 64.8%. The per-count Doom
rates (`DOOM_RATES`) make 4 players the hardest count by a wide margin on the
engaged line and no count hard at all on the camping line. The 4p row is the
one every historic baseline was measured at, so it is also the one that has
been tuned; 3p and 5p have not been tuned against a *correct* Loud.

## What changed in the model (batch 6)

Four fixes, all faithfulness, each one guarded by a test:

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

`LOCATION_THREAT_RATE` also picked up a mirror + test, which surfaced a live
data discrepancy worth a decision: **`content/locations.csv` gives the Badminton
Court `threat_rate` 2** (and design §15 calls it the highest-threat tile),
**but `lua/night.lua` rolls 1** for both courts. The sim mirrors the Lua,
because that is what a player actually experiences. If the CSV is the intent,
night.lua is a one-line fix and `net_camper` deserves a re-run.

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
