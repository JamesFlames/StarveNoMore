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
```

## Policies (what each one tests)

| Policy | Behavior | Probes |
|---|---|---|
| `turtle` | Everyone stacks at Ellie & Luca's, day and night; ignores the mid-bosses; fights the Source (all policies must — it's mandatory) | Anti-stacking pressure (crowded floor, festering bosses) |
| `spread` | Gather by day, everyone sleeps at their own home; ignores the mid-bosses | The boss-avoidance line — the strategy items 1–2 of the 2026-07 retune exist to kill |
| `balanced` | Pairs at night; strike pair (Rayman+James) day-chips loose bosses; all hands converge on the Source; appeases the Treeguard, cleanses | Whether engaging the whole map is worth it |
| `court_camper` | Balanced + Rayman sleeps at a court for Moonlit Salvage (unless a boss is loose) | Whether the salvage gamble is a temptation or an exploit |
| `net_camper` | court_camper with **one berth moved**: the salvage camp is the Badminton Court, not the Basketball Court | Whether The Net's +1 defence pays for the tile's threat rate — and the only policy that ever stands on the Badminton Court |

## Baseline results (2026-07 batch 5, 3000 sims, 4 players — diff future runs against this)

Ruleset: **Source-mandatory victory**, **uncapped boss festering**, **no boss arrival Doom**, retuned per-count Doom rates, batches 1–3 (Press the Attack, boss-kill rewards, Nothing Left to Lose, Signature Moves, Source split, Last Dawn, Sealed Basement, Wrongness), batch 4 (**Source HP 10 → 8**, the 3-player reliefs), batch 5 (**the Last Nerve valve**, **per-location defence**). Under `--rules old` the same policies win 72–100% — that control group is frozen and unaffected by anything below.

Earlier tables are preserved in git: batch 3 was turtle 34 / spread 27 / balanced 11 / court_camper 10, batch 4 turtle 42 / spread 42 / balanced 15 / court_camper 14.

| policy | win% (defence on) | win% (`--no-defence`) | Δ | loss:source | loss:down | late-loss% |
|---|---|---|---|---|---|---|
| turtle | 50.4% | 50.4% | 0.0 | 5% | 12% | 100% |
| spread | 52.5% | 51.8% | +0.7 | 9% | 0% | 100% |
| balanced | 18.1% | 19.1% | −1.0 | 27% | 18% | 100% |
| court_camper | **15.0%** | 18.6% | **−3.6** | 25% | 19% | 100% |
| net_camper | 9.8% | 10.7% | −0.9 | 20% | 20% | 100% |

Standard error at 3000 sims is ~0.9 points, so only the court_camper row is comfortably outside noise. Two live calibration facts:

1. **The best lines now sit at 50–52%, above the 40–50% band** (§20.2) — where batch 4 recorded 42%. The cause is the **Last Nerve valve** (§10.1.1), which landed after that calibration and was never re-baselined; setting `LAST_NERVE_THRESHOLD = 0` reproduces the batch-4 row almost exactly (turtle 41.4 / spread 42.1 / balanced 14.1 / court_camper 14.2), which is what identifies the valve rather than model drift. It is worth ~+9 points, and it is the number to take to the next table session — not location defence.
2. **Losses still land on Days 6–7 ~100% of the time.** The near-miss shape survived both changes.

The `--no-defence` column is the control for batch 5's location-defence rule; the probe that reads it apart is [balance-location-defence.md](balance-location-defence.md).

### Knobs measured for the overshoot (none taken — a menu, not a decision)

§5 names the tuning path for the valve: *"free Flee alone may be enough, and the Rest bonus is the half to drop first."* **Measured, that order is backwards** (3000 sims/cell, 4p): free Flee carries the whole effect and the Rest bonus is worth nothing.

| valve variant | turtle | spread | balanced | court_camper |
|---|---|---|---|---|
| off | 42.0% | 42.6% | 14.4% | 11.8% |
| Rest bonus only | 42.7% | 42.7% | 15.3% | 12.6% |
| free Flee only | 50.7% | 52.5% | 17.0% | 14.5% |
| both (shipped) | 50.4% | 52.5% | 18.1% | 14.8% |

Dropping the Rest half costs the §25 agency fix and buys back ~0 points: the valve's magnitude *is* free Flee, and cutting that is cutting the rule.

§20.1's other sanctioned lever — *"if diligent teams cruise, raise Phase 3–4 rates by +1 before touching festering"* — lands the band on its smallest setting. Phase **4** alone, `DOOM_RATES[4]` `[1,1,1,2] → [1,1,1,3]`:

| rates | turtle | spread | balanced | court_camper |
|---|---|---|---|---|
| shipped `[1,1,1,2]` | 50.4% | 52.5% | 18.0% | 14.7% |
| **phase 4 +1 `[1,1,1,3]`** | **40.3%** | **42.0%** | 16.3% | 13.6% |
| phase 3+4 +1 `[1,1,2,3]` | 24.7% | 21.6% | 14.7% | 12.1% |
| phase 3 +1 `[1,1,2,2]` | 38.7% | 35.3% | 15.7% | 12.9% |

Losses stay ~100% on Days 6–7 in every row, so the gate holds throughout. Taking both phases overshoots well below the band; phase 3 alone undershoots it. Across counts the same +1 is worth −10 points at 4p and 5p and **nothing at 3p** (99.3 → 99.4) — at three players the game ends before the Doom clock is the binding constraint, which is §20.1's standing "3p is not fixed by tuning" result, now with a number on it. 5-player spread stays at 62% either way; it was out of band before this knob and is not what this knob is for.

Recommendation if the band matters: **one number, `DOOM_RATES[4][4]` 2 → 3**, valve kept whole. Not applied — taking a knob is a design decision §20.1 records with its rationale.

**3-player sweep after the W2 reliefs** (`--sweep3`): the cliff is gone but over-corrected in the sim — Rayman trios now top the turtle table (99–100%) because Loud is his only modeled cost against his fully-modeled combat value. Floor gate passes (worst trio 48% under its best policy; nothing near 0). Treat the sim's Rayman numbers as a bracket, not a measurement: the real tuning verdict belongs to the W2 table A/B.

## 3-character composition sweep (2026-07, `--sweep3`)

The policies are **composition-aware** (strike pair, weapon carriers, and night pairing adapt to whoever is on the roster; `FIGHTER_PRIORITY` resolves to Rayman+James on the full roster, so 4p/5p baselines are unaffected). `--sweep3` runs every 3-character team. Re-measured at batch 5, 2000 sims, ±1.1 — location defence changes no team's rank (every delta ≤3 points):

| team | balanced | turtle |
|---|---|---|
| Coco+Ellie+Luca | **81%** | **100%** |
| James+Ellie+Luca | **77%** | 73% |
| James+Coco+Ellie | 45% | 96% |
| Coco+Rayman+Ellie | 17% | **100%** |
| James+Coco+Luca | 13% | 99% |
| Rayman+Ellie+Luca | 9% | 99% |
| Coco+Rayman+Luca | 8% | **100%** |
| James+Rayman+Luca | 2% | 99% |
| James+Rayman+Ellie | 1% | 48% |
| James+Coco+Rayman | 0% | **100%** |

Three readings, in confidence order. (1) **At 3 players, turtling dominates, and now overwhelmingly** — eight of ten trios clear 96% under one shared camp while the same teams sit at 0–17% when they split up. That is a bigger gap than batch 4 recorded (75/86% at the top), because the Last Nerve valve pays out most to a team that never leaves a house. A strategy this dominant at one player count is a §20.1 risk in its own right. (2) **The batch-4 Rayman cliff was a policy artifact, not a roster verdict** — every Rayman trio now clears 99% under turtle where batch 4 measured ≤6%, so what collapses is Rayman *splitting up*, not Rayman. His costs (Big Appetite, Loud, tank-takes-all-counters) are fully modeled while his value (Defend, Court Master, Speed, Trophies) is mostly not, so read the `balanced` column as a floor for him. (3) **3p viability is still strongly composition-dependent under `balanced`** (0–81%), and every team above 17% there carries Coco or Luca. The design's "any 3 of 5" claim (§6.6) holds if the trio camps and fails if it spreads; the §20.1 risk is now about the strategy, not the roster.

## Model assumptions (documented in the script's docstring)

- Resources are a **shared team pool** — over-models trading (the real same-tile restriction is looser here).
- Named bosses arrive **on schedule** (Deerclops D4, Eye D5, Source D6) rather than by deck luck; Treeguard wakes Dusk D4 as in the real rules.
- Market is abstracted to Flashlights + one Weapon per fighter; Dawn cards are a random minor-effect distribution.
- Bots are competent, not brilliant. Calibration lesson: early "terrible" results were **bot blunders, not rule problems** (Rayman sleeping alone with Loud, James never visiting his Stash, nobody reviving the fallen). When a result looks insane, run `--trace` and read the day-by-day log before blaming the rules.

## Maintenance rule

The sim mirrors constants from `lua/global.lua` and the design doc by hand (stats, Doom rates, thresholds, yields, boss schedule). **When a gameplay rule changes, update the sim to match and rerun both rulesets.** Keep `--rules old` frozen as the pre-2026-07 snapshot — it is the control group, not a second live ruleset.
