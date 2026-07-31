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

Ruleset: **Source-mandatory victory**, **uncapped boss festering**, **no boss arrival Doom**, retuned per-count Doom rates, batches 1–3 (Press the Attack, boss-kill rewards, Nothing Left to Lose, Signature Moves, Source split, Last Dawn, Sealed Basement, Wrongness), batch 4 (**Source HP 10 → 8**, the 3-player reliefs), batch 5 (**the Last Nerve valve**, **per-location defence**, **4p Phase 4 Doom +2 → +3**). Under `--rules old` the same policies win 72–100% — that control group is frozen and unaffected by anything below.

Earlier tables are in git: batch 3 turtle 34 / spread 27 / balanced 11, batch 4 turtle 42 / spread 42 / balanced 15.

| policy | win% (defence on) | win% (`--no-defence`) | Δ | loss:doom | loss:down | late-loss% |
|---|---|---|---|---|---|---|
| turtle | **40.3%** | 40.3% | 0.0 | 44% | 15% | 100% |
| spread | **42.0%** | 41.5% | +0.5 | 54% | 0% | 100% |
| balanced | 16.2% | 16.9% | −0.7 | 46% | 18% | 100% |
| court_camper | 13.9% | 16.8% | −2.9 | 49% | 19% | 100% |
| net_camper | 8.2% | 8.6% | −0.4 | 58% | 20% | 100% |

Standard error at 3000 sims is ~0.9 points. Two live calibration facts:

1. **The band is met**: the best lines sit at 40–42%, inside §20.2's 40–50%. They sat at 50–52% before batch 5's Phase-4 knob — the Last Nerve valve is worth ~+9 points (`LAST_NERVE_THRESHOLD = 0` reproduces the batch-4 row: turtle 41.4 / spread 42.1 / balanced 14.1), a number §20.1 measured and accepted at the time rather than a regression anyone missed. The knob answers it; the valve keeps its §25 agency fix.
2. **Losses still land on Days 6–7 ~100% of the time**, and are now mostly Doom rather than the Source — a clock that runs out on a team still standing, which is the near-miss shape §20.1's gate asks for.

The `--no-defence` column is the control for batch 5's location-defence rule; the probe that reads it apart is [balance-location-defence.md](balance-location-defence.md).

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
