# Starve No More — Victory, Defeat & Setup

> Part of the **Starve No More** design doc — [back to the index](../../StarveNoMoreDesignConcept.md).

## 16. Victory and Defeat Conditions

### 16.1 Default victory

The team **wins** if all surviving characters are alive at the end of Day 7 (after the Day 7 night phase fully resolves), the Doom marker is at less than 30, **and The Source has been destroyed** (if it arrived — see §16.3, condition 3). The final boss is not optional: a team that spends the Final Hours hiding from The Source has not won, whatever the Doom track says. (This clause is enforced, not flavor — simulation showed that if survival alone wins, the dominant strategy is to ignore every boss.)

### 16.2 Bonus victories

- **Pristine Run** — All five characters are alive at game end. (No revivals counted; all five must have reached the end on their feet.) Awarded a "Story Card" to keep.
- **Truth Run** — The team finds and reads all 3 Clue cards (special items in the Market deck) before Day 7. The ending narrative changes.
- **Hero Run** — Defeat all three phase bosses: the Deerclops, the Eye of Terror, and the Source. (The Treeguard mini-boss doesn't count — §14.2. The Source is already mandatory for any win; the Hero Run is for felling the other two as well.)

These are not separate goals — they are achievements layered on top of survival, encouraging replay.

### 16.3 Defeat conditions

The team **loses** if any of:

1. The Doom marker reaches 30.
2. All characters are simultaneously Down (Health 0 or Sanity 0) at any moment.
3. The Source boss reaches the Final Hours and is not stopped on Day 7.

### 16.4 Down state and revival

When a character is Down (Health 0 or Sanity 0):

- **Doom +1**, immediately. The dark feeds on collapse (§15.1). This is deliberately the *only* systemic penalty for being Down — the pressure lands on the shared clock the team can fight, not on the survivors' stat tracks.
- Flip the standee to its **ghost side**. The character cannot take actions, cannot gather, cannot fight.
- Ghost characters drift between locations (1 free move per round).
- A ghost can whisper a single word to the team per round (literally — the ghost player may say one word per round to advise; this both flavors the experience and limits the alpha-player problem).

(Design note: an earlier draft had ghosts drain −1 Sanity from co-located living players at Tick. Cut — it was a positive feedback loop that punished the team hardest exactly when they were already losing, and it discouraged the survivors from gathering around the body, which is where the story is.)

To **revive** a Down character:

- Another character must be at the same location.
- Spend a **Telltale Heart** token (cooked per the §13.4 recipe).
- The revived character returns at half their starting maximums (e.g., James returns at 4 Health, 3 Hunger, 5 Sanity).

This is the DST soft permadeath ([DontStarveVideoGamePrinciples.md §7](../../Archive/DontStarveVideoGamePrinciples.md)) — death is meaningful but not eliminating.

### 16.5 The Week in Review

When the game ends — victory or defeat — the table gets the week read back to it: one headline per day ("Day 3 — the night Coco slept alone"), the darkest night, the best kill, who kept everyone fed, the longest run of dark nights survived, the Doom high-water mark, and the fallen and the saved. In the TTS build this is generated automatically from the game's own event log (nothing new is tracked at the table); in a print edition it is a one-minute ritual of flipping back through the week aloud.

Why it's a rule and not a nicety: **storied collaboration (§1.4 #3) is a stated aesthetic, and the retelling is the actual replayability engine** ([PrinciplesOfGoodBoardGames.md §15](../../Archive/PrinciplesOfGoodBoardGames.md)). The Week in Review hands the table a script to retell from — the week becomes a story with a shape, which is exactly what makes "one more game" happen.

---

## 17. Setup

### 17.1 Component layout

1. Place the **Main Board** in the center.
2. Place the 5 **Location Tiles** on their snap points; insert path-edge cards between them per the chosen variant (Compact / Sprawl / Linear).
3. Each player chooses a **Character**, takes the matching player board, standee, stat markers, and starting hand.
4. Place each character standee at their own house. Coco starts at Ellie & Luca's House.
5. Set Health/Hunger/Sanity sliders to each character's starting values.
6. Shuffle each Phase deck separately. Stack them in order (Phase 1 on top).
7. Shuffle the Market deck. Deal 5 cards face-up to the Market display.
8. Shuffle the Threat deck.
9. Place all resource tokens in the **Resource Bag** (or Infinite Bags per type for TTS clarity).
10. Place **the Sealed Basement** at Ellie & Luca's House (fixed map feature — §13.5). Its tooltip states the cost and hints the reward.
11. Set Day Counter to 1, Doom marker to 0.
12. First player is the player whose real-life kitchen is currently most cluttered. (Theme.)

### 17.2 Difficulty variants

Implemented (batch 4 W3): selectable in the setup Variants step, driven by `DIFFICULTY_PARAMS` (global.lua).

- **Easy / Long Weekend** — 3 days only, Phase 1 + half of Phase 2 (day-phase map 1/1/2). Doom track halved: defeat at **15**. Good for teaching; the final day still gets the Last Dawn.
- **Standard** — 7 days, full rules. Calibrated 2026-07: sim best line 40–50% with Days 6–7 losses (§20.1 boss-HP knob).
- **Nightmare** — 7 days, Doom rate +1 in every phase, no Phase 1 (the day-phase map starts on Strange Days).

Long Weekend and Nightmare are derived offsets from the tuned Standard, not separately balanced.

### 17.3 Scenarios (optional variant)

A **Scenario** is a single week-long modifier revealed at setup — the DST seasons idea compressed into one card: the same neighborhood, but this week the *world* is different. Scenarios are the game's coarse replayability lever on top of the fine-grained ones (map layouts §7.6, character composition §6.6): variability as a multiplier on an already-working game, never a substitute for depth ([PrinciplesOfGoodBoardGames.md §15](../../Archive/PrinciplesOfGoodBoardGames.md)).

The eight Scenarios (authored in `content/cards_scenarios.csv`; rules applied by `lua/setup.lua`):

| Scenario | The week's twist |
|---|---|
| **The Long Winter** | Hunger decay doubled; food gathering -1; houses give +1 Sanity at sleep (everyone huddles). |
| **The Scorching Summer** | Everyone starts -2 max Hunger; Energy Drinks +1 Sanity; courts yield +1 resource. |
| **The Rotting Autumn** | 1 Food spoils per location at Dawn; recipes yield +1 Hunger; Cloth easier to find. |
| **The False Spring** | Days 1–3: no Charlie at all. Day 4+: Charlie hunts everywhere, every night. |
| **Total Blackout** | No Batteries in the game; Flashlights uncraftable; Fire is the only light. |
| **Strict Rationing** | Market restocks 1 card per 2 days; recipes cost 1 fewer ingredient. |
| **The Full Moon** | Charlie never attacks — but all Soft threats become Hard (+2 HP, +1 attack). |
| **The Shortcut** | A free path between James's House and the Badminton Court… that draws +1 Threat at both ends each night. |

Rules of use:

1. **Off by default.** The setup walkthrough offers "Random Scenario" as a toggle (§18.16); recommend it only after a group's first game — a Scenario on a first play muddies which rules are "the game" and which are "this week."
2. **Revealed at setup, in force all week.** The active Scenario is announced at setup and mirrored in the "Rules in effect" panel for the whole game, so nobody has to remember it.
3. **One at a time.** Scenarios are balanced individually, not in combination.
4. **Physical edition note.** In the TTS build the Scenario is applied digitally (no physical deck is spawned); for a print edition, `cards_scenarios.csv` is the authoring source for an 8-card deck — draw 1 at setup, leave it face-up by the Doom track.

---

