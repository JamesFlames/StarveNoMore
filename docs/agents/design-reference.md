# Game Design Quick Reference

Characters, locations, phases, the Doom track and the win condition — the numbers a rules change has to stay consistent with.

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

## Characters
| Name   | Role             | Health | Hunger | Sanity | Home           |
|--------|------------------|--------|--------|--------|----------------|
| James  | The Gamer        | 8      | 6      | 10     | JamesHouse     |
| Coco   | The Angel        | 6      | 8      | 12     | (none)         |
| Rayman | Basketball Player| 12     | 10     | 6      | RaymanHouse    |
| Ellie  | The Cook         | 8      | 10     | 8      | EllieLucaHouse |
| Luca   | The Orator       | 7      | 8      | 10     | EllieLucaHouse |

Each character's starting items (`content/cards_starting.csv`, `S_*`) are a
small deck in the save, dealt into that player's hand by `dealStartingHands`
(setup.lua) at setup; James additionally gets 2 Energy Drink **tokens** by his
player board (his Wired economy runs on tokens, not cards). Weapon items with
"+N Attack die" text are counted automatically in combat via `WEAPON_DICE`
(best single carried weapon; no stacking).

## Locations
JamesHouse, RaymanHouse, EllieLucaHouse, BasketballCourt, BadmintonCourt

## Phases
1. **Dusk of Week** (Days 1–2) — Calm intro
2. **Strange Days** (Days 3–4) — Escalation, Deerclops arrives
2.5. **The Grove Wakes** (Dusk of Day 4, scheduled) — Treeguard mini-boss lairs at a random sport court: blocks Gather there, festers Doom; fight it (HP 5/Atk 2, drops 3 Wood) or appease it (2 Wood at its tile). `lua/treeguard.lua`
3. **Long Nights** (Day 5) — Eye of Terror arrives
4. **Final Hours** (Days 6–7) — The Source arrives, endgame. The Source's HP is script-tracked (`gameState.bossHP.source`); at ≤5 HP it splits into 2 Terror Beaks (once, `gameState.sourceSplit`). Day 7's Dawn is the fixed, scripted **Last Dawn** (no Phase-4 draw).

## Day Cycle
Dawn (Doom advance + Moonlit Salvage + Dawn card) → Day (player turns, 3 actions each) → Dusk (optional 1-tile scramble, 1 Hunger, then host clicks Resolve Night) → Night → Tick (stat decay)

## Doom Track
0–30. Advances each Dawn by phase rate **+1 per Threat/Boss still on the map (fester, cap +3)**, and **+1 whenever a character goes Down**. Thresholds at 10 (night threats +1), 15 (Scarcity: crafts +1 resource), 20 (−1 Sanity at Tick), 25 (bosses can appear in any phase + **Nothing Left to Lose**: +1 attack die for everyone, Rest heals +1 Health anywhere), 30 = defeat. Cleanse action (1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink) reduces Doom by 2.

## Night rules of note
- **Charlie attack** (no light source): 2 Sanity + 1 Health, +1 to each per consecutive dark night (`char.charlieStreak`, reset at Tick on a lit night). Coco immune.
- **Crowded floor**: a house sleeps 2 comfortably; sleepers beyond the second get no sleep regen (owners get beds first, then lowest-Sanity guests).
- **Moonlit Salvage**: survive a night at a sport court → gather 2 resources from that court's bag at Dawn.
- Ghosts do **not** drain ally Sanity (cut — positive feedback loop).

## Win Condition
Survive all 7 days with Doom < 30 and at least one character not Down — and if The Source has arrived, it must be destroyed before Day 7 ends (a standing Source at the Day-7 Tick is a defeat, whatever the Doom track says). Bonus achievements: **Pristine** (all 5 alive), **Truth** (3 Clue cards), **Hero** (all 3 phase bosses defeated — the Treeguard doesn't count).
