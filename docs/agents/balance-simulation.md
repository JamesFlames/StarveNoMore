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
```

## Policies (what each one tests)

| Policy | Behavior | Probes |
|---|---|---|
| `turtle` | Everyone stacks at Ellie & Luca's, day and night; ignores the mid-bosses; fights the Source (all policies must — it's mandatory) | Anti-stacking pressure (crowded floor, festering bosses) |
| `spread` | Gather by day, everyone sleeps at their own home; ignores the mid-bosses | The boss-avoidance line — the strategy items 1–2 of the 2026-07 retune exist to kill |
| `balanced` | Pairs at night; strike pair (Rayman+James) day-chips loose bosses; all hands converge on the Source; appeases the Treeguard, cleanses | Whether engaging the whole map is worth it |
| `court_camper` | Balanced + Rayman sleeps at a court for Moonlit Salvage (unless a boss is loose) | Whether the salvage gamble is a temptation or an exploit |

## Baseline results (2026-07 batch 4 calibration, 3000 sims, 4 players — diff future runs against this)

Ruleset in this baseline: **Source-mandatory victory**, **uncapped boss festering** (+2/dawn per phase boss, +1 Treeguard; threats +1 capped at +3), **no boss arrival Doom**, retuned per-count Doom rates (3p [1,1,1,1] / 4p [1,1,1,2] / 5p [1,1,2,2]), batch 1 (**Press the Attack**, **boss-kill rewards**), batch 2 (**Nothing Left to Lose**, **Signature Moves**, **Source split**, **Last Dawn**), batch 3 (**Sealed Basement**, **Wrongness token**; Night Sounds and Dawn Dares are playtest-only) — plus batch 4: **the Source retuned HP 10 → 8** (the W3 calibration knob) and the **3-player reliefs** (Big Appetite conditional + Loud needs 3+ tiles, `playerCount == 3` only).

| policy | win% new rules | win% old rules | loss:source (new) | loss:down (new) | late-loss% |
|---|---|---|---|---|---|
| turtle | 42% | 84% | 1% | 30% | 100% |
| spread | 42% | ~100% | 14% | 1% | 100% |
| balanced | 15% | 76% | 25% | 25% | 99% |
| court_camper | 14% | 72% | 24% | 26% | 100% |

Reading: **the §20.2 calibration target is met on the simulator** — the best lines sit at 42% (target band 40–50%) and ~100% of losses land on Days 6–7 (a near-miss finish, not a mid-week strangle). The single knob taken was the design's own §20.1 first choice: Source HP 10 → 8 (turtle 34→42, spread 27→42, fighting lines 10→14-15). Table confirmation is still required — the sim's known bias (Trophies unmodeled, fighters undervalued) means the human number may run higher. The batch-3 table (turtle 34/spread 27/balanced 11/court_camper 10) is preserved in git.

**3-player sweep after the W2 reliefs** (`--sweep3`): the cliff is gone but over-corrected in the sim — Rayman trios now top the turtle table (97–99%) because Loud is his only modeled cost against his fully-modeled combat value. Floor gate passes (worst trio 31% under its best policy; nothing near 0). Treat the sim's Rayman numbers as a bracket, not a measurement: the real tuning verdict belongs to the W2 table A/B.

## 3-character composition sweep (2026-07, `--sweep3`)

The policies are **composition-aware** (strike pair, weapon carriers, and night pairing adapt to whoever is on the roster; `FIGHTER_PRIORITY` resolves to Rayman+James on the full roster, so 4p/5p baselines are unaffected). `--sweep3` runs every 3-character team; results at 2000 sims (win% under `balanced` / under `turtle`):

| team | balanced | turtle |
|---|---|---|
| Coco+Ellie+Luca | 50% | **86%** |
| James+Coco+Luca | 0% | **75%** |
| James+Coco+Ellie | 5% | **73%** |
| James+Ellie+Luca | 37% | 34% |
| every team with Rayman (6 teams) | ≤0.1% | ≤6% |

Three readings, in confidence order. (1) **3p viability is strongly composition-dependent** — the spread between best and worst team is ~85 points, and every team above 7% carries Coco or Luca. The design's "any 3 of 5" claim (§6.6) is not supported by the model; this is logged as a §20.1 balance risk. (2) **At 3 players, turtling dominates** — splitting up (balanced's stationing) is wrong at this action economy; the best play for a trio is one shared camp. (3) **Every Rayman team collapses** (down-losses 44–99%) — but read this one with the bias warning below: Rayman's costs (Big Appetite, Loud, tank-takes-all-counters) are fully modeled while his value (Defend, Court Master, Speed, and Trophy rewards for the fights he enables) is mostly *not*. The sim systematically undervalues the fighters and fully values the support cast, so the Rayman cliff is a flag for playtesting, not a stat-change warrant on its own.

## Model assumptions (documented in the script's docstring)

- Resources are a **shared team pool** — over-models trading (the real same-tile restriction is looser here).
- Named bosses arrive **on schedule** (Deerclops D4, Eye D5, Source D6) rather than by deck luck; Treeguard wakes Dusk D4 as in the real rules.
- Market is abstracted to Flashlights + one Weapon per fighter; Dawn cards are a random minor-effect distribution.
- Bots are competent, not brilliant. Calibration lesson: early "terrible" results were **bot blunders, not rule problems** (Rayman sleeping alone with Loud, James never visiting his Stash, nobody reviving the fallen). When a result looks insane, run `--trace` and read the day-by-day log before blaming the rules.

## Maintenance rule

The sim mirrors constants from `lua/global.lua` and the design doc by hand (stats, Doom rates, thresholds, yields, boss schedule). **When a gameplay rule changes, update the sim to match and rerun both rulesets.** Keep `--rules old` frozen as the pre-2026-07 snapshot — it is the control group, not a second live ruleset.
