# Location defence — the batch-5 balance probe

What the per-location defence roll (§7.1-7.5) did to the simulated campaign, measured before human playtesting.

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md). How to run the model at all: [balance-simulation.md](balance-simulation.md).*

## The rule under test

Positive defence = dice the team rolls against the counter-attack, each 5-6 turning one incoming hit aside. Negative = extra dice the threat swings, because being caught in the open is the same rule pointed the other way. Live at **three of five tiles**: Rayman's Garage **+1**, the Badminton Court **+1** (The Net), the Basketball Court **−1** (open court).

`LOCATION_DEFENSE` in `simulate_balance.py` mirrors `lua/global.lua`, which mirrors the `defense` column of `content/locations.csv`; `tests/test_sim.py` guards both hops, because a drifted defence table is invisible at the table — a lost block looks like bad luck.

Two things were added to the model for this probe: the counter-attack in `group_fight` now reads the tile (with `--no-defence` as the control group), and a fifth policy, **`net_camper`**, exists so that some policy stands on the Badminton Court at all. The four original policies all hardcode `COURTS[0]`, so before this the Net had never been tested in a simulated game.

## Headline: −1.0 to −3.6 points on the map lines, nothing on the camp

Full-rule vs `--no-defence`, 3000 sims, 4 players, ±0.9:

| policy | defence on | defence off | Δ |
|---|---|---|---|
| turtle | 50.4% | 50.4% | 0.0 |
| spread | 52.5% | 51.8% | +0.7 |
| balanced | 18.1% | 19.1% | −1.0 |
| court_camper | **15.0%** | 18.6% | **−3.6** |
| net_camper | 9.8% | 10.7% | −0.9 |

Splitting the rule into halves (4000 sims, ±0.6 — "cover" = the positive tiles only, "exposure" = the negative tile only):

| policy | off | cover only | exposure only | full rule |
|---|---|---|---|---|
| turtle | 51.2% | 51.2% | 51.2% | 51.2% |
| spread | 51.1% | 51.9% | 51.1% | 51.9% |
| balanced | 19.1% | 18.9% | 19.4% | 18.4% |
| court_camper | 18.1% | 19.2% | 16.0% | 15.3% |
| net_camper | 10.2% | 11.3% | 10.0% | 9.7% |

## Four readings

1. **The rule is a net tax, and exposure is about twice cover.** Per game the fighting teams take 2.7–4.9 extra swings and block only 0.7–1.2 hits. The −1 tile simply comes up more often than the +1 tiles do.
2. **The reason is the Deerclops, not the courts.** It always spawns on the Basketball Court (`BOSSES[4]`), the game's only −1 tile, so *every* boss-fighting line pays +1 counter die for the whole first boss fight — a 3-attack boss swinging 4. That is the rule's single largest effect and it lands on exactly the content the boss-kill rebates were written to encourage. Deerclops kills fall 0.33 → 0.30 per game for court_camper, and the attrition carries forward into the Eye (0.13 → 0.11) and the Source (0.21 → 0.19). Logged as a §20.1 interaction to watch, not a defect: "the first boss ambushes you where you have no cover" is a defensible beat, but it is currently un-priced — nothing else about the Deerclops was softened to pay for it.
3. **`turtle` is untouched** — 0.0 across every variant, because it never leaves the kitchen (0 defence). The rule therefore adds nothing to the anti-stacking pressure and does not widen the gap between camping and engaging; it narrows the map lines only, in the camper's favour.
4. **The Net does not pay for its tile — but the bots cannot say so.** `net_camper` is court_camper with exactly one berth moved, and it sits ~5 points *below* it both with the rule (9.8 vs 15.0) and without it (10.7 vs 18.6). The +1 block is worth about +1.1 points; the Badminton Court's +1 night threat rate and the loss of Rayman's Court Master die cost far more. Read this as a bracket: the policies never choose *where* to fight, so they cannot express the one strategy the Net is for — deliberately meeting a fight where you are covered. That is a human decision this model cannot make.

## What the rule did not change

- **Difficulty ordering stays monotonic** — story > standard > nightmare under `--sweep-difficulty`, with and without defence. The penalty is roughly constant in absolute terms across modes (court_camper: story −2.1, standard −1.8, nightmare −2.2).
- **No 3-character team changes rank** in `--sweep3`; every delta is ≤3 points, within noise at 2000 sims.
- **`--rules old` is untouched.** Location defence is gated to the new ruleset, so the frozen control group cannot silently acquire it — `test_old_rules_have_no_location_defence` pins that.

## Taking this to the table

The bigger finding of this pass is not the defence rule: **the best lines now win 50–52%, above the §20.2 target band of 40–50%**, and the cause is the Last Nerve valve, which landed after the batch-4 calibration and was never re-baselined. See [balance-simulation.md](balance-simulation.md). Location defence moves the fighting lines *down* by 1–4 points, which pushes in the right direction but is nowhere near large enough to be the knob.

The two questions this model genuinely cannot answer, and a table can:

- Does the −1 on the Basketball Court read as an *ambush* (tense, thematic) or as a *tax* on the boss you were told to go and kill?
- Does anyone ever choose to fight at the Badminton Court because of the Net? If nobody does across a session, the +1 is decoration and the tile still needs a reason to exist.
