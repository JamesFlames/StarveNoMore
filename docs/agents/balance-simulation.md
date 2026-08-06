# Balance Simulation

The Monte Carlo model, its calibration targets, and how to re-run it after a rules change.

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

`scripts/simulate_balance.py` is a standalone Monte Carlo probe of the 7-day campaign loop. It is **not part of the build pipeline** — it exists to answer "does this rule change move the win rate / Doom pressure the way we intended?" *before* human playtests. Design target: 40–50% wins on Standard for an experienced group (design §20.2).

## Commands

```bash
python scripts/simulate_balance.py                      # all 4 policies, current rules, 2000 games each
python scripts/simulate_balance.py --sims 5000          # tighter estimates
python scripts/simulate_balance.py --rules old          # frozen pre-2026-07 ruleset, for before/after diffs
python scripts/simulate_balance.py --players 3          # player-count scaling (3/4/5)
python scripts/simulate_balance.py --policy turtle      # single policy
python scripts/simulate_balance.py --trace --policy balanced --seed 7   # one game, day-by-day log
python scripts/simulate_balance.py --sweep3             # all ten 3-character teams (composition viability)
python scripts/simulate_balance.py --no-defence         # control group for location defence (§7.1-7.5)
python scripts/simulate_balance.py --scenario SC_WINTER # one of the eight Scenario cards (§17.3)
python scripts/simulate_balance.py --topology Ring      # one of the five path variants
python scripts/simulate_balance.py --sweep-scenario     # every Scenario / --sweep-topology / --sweep-roster
python scripts/simulate_balance.py --matrix scenario --policy turtle   # team x Scenario grid
```

**Setup draws a Scenario and a path variant at random in every real game**, so
the defaults (`none` / Star, and every baseline below) are a control group, not
a table state. The other cells: [balance-scenarios.md](balance-scenarios.md),
[balance-map-and-rosters.md](balance-map-and-rosters.md).

## Policies (what each one tests)

| Policy | Behavior | Probes |
|---|---|---|
| `turtle` | Everyone stacks at Ellie & Luca's, day and night; ignores the mid-bosses; fights the Source (all policies must — it's mandatory) | Anti-stacking pressure (crowded floor, festering bosses) |
| `spread` | Gather by day, everyone sleeps at their own home; ignores the mid-bosses | The boss-avoidance line — the strategy items 1–2 of the 2026-07 retune exist to kill |
| `balanced` | Pairs at night; strike pair (Rayman+James) day-chips loose bosses; all hands converge on the Source; appeases the Treeguard, cleanses | Whether engaging the whole map is worth it |
| `court_camper` | Balanced + Rayman sleeps at a court for Moonlit Salvage (unless a boss is loose) | Whether the salvage gamble is a temptation or an exploit |
| `net_camper` | court_camper with **one berth moved**: the salvage camp is the Badminton Court, not the Basketball Court | Whether The Net's +1 defence pays for the tile's threat rate — and the only policy that ever stands on the Badminton Court |

## Current baseline (2026-08 batch 6, 3000 sims, 4 players, Star, no Scenario)

Batch 6 is a **movement-model** batch: no rule changed, four modelling gaps
closed — real path variants, the one-tile Dusk scramble, map-aware policies,
and (the one that moves everything) Rayman's Loud read off tracked movement
instead of a hardcoded `True`. Write-up:
[balance-map-and-rosters.md](balance-map-and-rosters.md).

| policy | batch 5 | **batch 6** | loss:doom | loss:down | late-loss% |
|---|---|---|---|---|---|
| turtle | 40.3% | **97.9%** | 2% | 0% | 100% |
| spread | 42.0% | **86.6%** | 9% | 0% | 100% |
| balanced | 16.2% | **18.9%** | 47% | 20% | 99% |
| court_camper | 13.9% | **24.9%** | 41% | 18% | 99% |
| net_camper | 8.2% | **20.9%** | 46% | 18% | 99% |

**The 40–50% band is not met, and the batch-5 table that said it was had the
sim charging a stationary team for Loud every night.** §6.2 levies Loud only on
a day Rayman moved, and `LOCATION_THREAT_RATE` (night.lua) is 0 at every house,
so a camp draws nothing at all until Doom 10. Calibrating against the camping
line now means pricing a new anti-stacking rule, not turning an existing knob —
the priced knob list below moves the *fighting* lines, which were never the
ones setting the ceiling. Everything below this line is the batch-5 record,
kept because the knob prices and the `--rules old` control are still valid.

## Batch-5 results (2026-07, 3000 sims, 4 players — the historic record)

Ruleset: **Source-mandatory victory**, **uncapped boss festering**, **no boss arrival Doom**, retuned per-count Doom rates, batches 1–3 (Press the Attack, boss-kill rewards, Nothing Left to Lose, Signature Moves, Source split, Last Dawn, Sealed Basement, Wrongness), batch 4 (**Source HP 10 → 8**, the 3-player reliefs), batch 5 (**the Last Nerve valve**, **per-location defence**, **4p Phase 4 Doom +2 → +3**). Under `--rules old` the same policies win 72–100% — that control group is frozen and unaffected by anything below.

Earlier tables are in git: batch 3 turtle 34 / spread 27 / balanced 11, batch 4 turtle 42 / spread 42 / balanced 15.

| policy | win% (defence on) | win% (`--no-defence`) | Δ | loss:doom | loss:down | late-loss% |
|---|---|---|---|---|---|---|
| turtle | **40.3%** | 40.3% | 0.0 | 44% | 15% | 100% |
| spread | **42.0%** | 41.5% | +0.5 | 54% | 0% | 100% |
| balanced | 16.2% | 16.9% | −0.7 | 46% | 18% | 100% |
| court_camper | 13.9% | 16.8% | −2.9 | 49% | 19% | 100% |
| net_camper | 8.2% | 8.6% | −0.4 | 58% | 20% | 100% |

Standard error at 3000 sims is ~0.9 points. Batch 5 read this table as "the
band is met" and as "losses land on Days 6-7 ~100% of the time, mostly to
Doom". The second still holds; the first did not survive the batch-6 Loud fix.
The Last Nerve valve is worth ~+9 points here (`LAST_NERVE_THRESHOLD = 0`
reproduces the batch-4 row), a number §20.1 measured and accepted rather than a
regression anyone missed.

The `--no-defence` column is the control for batch 5's location-defence rule;
the probe that reads it apart is
[balance-location-defence.md](balance-location-defence.md).

### The ordered knobs, priced (knob 3 taken in batch 5)

§20.1 lists three knobs for a too-soft Final Hours: drop the Rest half of Last Nerve, then Source HP 8 → 9, then Phase 3–4 Doom +1. All were priced at 3000 sims/cell before one was chosen:

| knob | turtle | spread | balanced | court_camper |
|---|---|---|---|---|
| pre-knob shipped | 50.4% | 52.5% | 18.4% | 15.2% |
| 1 — drop Rest half | 50.7% | 52.5% | 17.0% | 14.5% |
| 2 — Source HP 8 → 9 | 45.8% | 47.8% | 16.7% | 13.7% |
| **3 — Phase 4 Doom +1 (taken)** | **40.3%** | **41.8%** | 16.4% | 13.7% |
| 2 + 3 together | 35.9% | 37.8% | 15.6% | 13.0% |

**Knob 1 does nothing, exactly as §20.1 predicted** — it recorded the Rest half at ~0 pp and lists it first because it is cheap, not because it is heavy. The valve's whole magnitude is free Flee (50.7% alone vs 42.0% valve-off), so there is no "tune it down" setting: cutting free Flee is cutting the rule.

**Knob 2 remains the unused gentler alternative** — 45.8–47.8%, mid-band, against knob 3's bottom-edge landing. Reach for it if 40–42% proves too harsh at the table. The two together overshoot below the band.

Phase **4** alone is knob 3's only usable setting: phase 3+4 crashes to 21.6–24.7%, phase 3 alone undershoots at 35.3–38.7%. It is worth −10 points at 4p and 5p and **nothing at 3p** (99.3 → 99.4), where the game ends before the Doom clock binds.

**Watch Nightmare.** Its Phase 3–4 surcharge stacks on the new rate for a 4-per-day final act, and that flipped which line is best: turtle falls 19.2% → 4.8% and spread to 7.8%, while the boss-fighting lines hold at 10.5–13.1%. The ladder still holds (76% / 42% / 13%, floor 8%), but Nightmare is now the mode where ignoring bosses stops working — an identity nobody designed on purpose.

## Composition sweeps

`--sweep3` (ten 3-character teams) and `--sweep-roster` (all sixteen 3-, 4- and
5-character teams) both still run. The batch-5 `--sweep3` table that used to
live here is superseded — it was measured against the hardcoded Loud, which
flattered every camping trio. Current numbers, per Scenario and per path
variant: [balance-scenarios.md](balance-scenarios.md) and
[balance-map-and-rosters.md](balance-map-and-rosters.md). The reading that did
survive: Rayman's costs are fully modeled and most of his value is not, so his
rows are a floor, not a verdict.

## Model assumptions (documented in the script's docstring)

- Resources are a **shared team pool** — over-models trading (the real same-tile restriction is looser here).
- Named bosses arrive **on schedule** (Deerclops D4, Eye D5, Source D6) rather than by deck luck; Treeguard wakes Dusk D4 as in the real rules.
- Market is abstracted to Flashlights + one Weapon per fighter; Dawn cards are a random minor-effect distribution.
- Bots are competent, not brilliant. Calibration lesson: early "terrible" results were **bot blunders, not rule problems** (Rayman sleeping alone with Loud, James never visiting his Stash, nobody reviving the fallen). When a result looks insane, run `--trace` and read the day-by-day log before blaming the rules.

## Maintenance rule

The sim mirrors constants from `lua/global.lua`, `lua/night.lua` and the design
doc by hand (stats, Doom rates, thresholds, yields, per-tile threat rates, boss
schedule), plus two setup dials in `scripts/sim_variants.py` (the eight
`SCENARIOS` flag sets from `lua/setup.lua`, and the path variants from
`scripts/path_layouts.py`). **When a gameplay rule changes, update the sim to
match and rerun both rulesets.** `tests/test_sim.py` enforces every one of
those mirrors, including that no Scenario flag is modeled and then never read.
Keep `--rules old` frozen as the pre-2026-07 snapshot — it is the control
group, not a second live ruleset.
