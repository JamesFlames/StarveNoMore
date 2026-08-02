# Starve No More — Components & Characters

> Part of the **Starve No More** design doc — [back to the index](../../StarveNoMoreDesignConcept.md).

## 5. Components List

Every component is sized, type-marked, and TTS-mappable. The "TTS Object" column references object types from [HowToCreateGamesInTabletopSimulator.md §5](../../Archive/HowToCreateGamesInTabletopSimulator.md).

| # | Component | Quantity | TTS Object | Notes |
|---|---|---|---|---|
| 1 | **Main Game Board** | 1 | `Custom_Board` (locked) | Background of the suburban map; location tiles attach to it. |
| 2 | **Location Tiles** | 5 | `Custom_Tile` (rounded square, large) | Snap-pointed onto the main board. |
| 3 | **Character Player Boards** | 5 | `Custom_Tile` (rectangle) | One per character; tracks Health/Hunger/Sanity, perks, constraints. |
| 4 | **Character Standees** | 5 | `Figurine_Custom` | Stand-up cardboard figure used as the player's pawn on the map. |
| 5 | **Health/Hunger/Sanity Markers** | 15 (3 per character) | `Custom_Token` (round) | Glide along tracks on the player board. |
| 6 | **Day Counter** | 1 | `Counter` | World clock, advances each round. |
| 7 | **Doom Track Marker** | 1 | `Custom_Token` | Slides along the Doom track on the main board. |
| 8 | **Phase Decks (Dawn cards)** | 4 decks of ~12 cards each | `DeckCustom` | One deck per phase: Dusk-of-Week, Strange Days, Long Nights, Final Hours. |
| 9 | **Item Cards (the Market)** | 49 unique cards | `DeckCustom` | The shared "Hogwarts Deck" of craftable items. |
| 10 | **Recipe Cards** | ~20 unique cards | `DeckCustom` | Crockpot recipes; reference cards more than draw deck. |
| 11 | **Resource Tokens** | ~120 in 6 types | `Custom_Token` (small) or `Infinite_Bag` | Wood, Metal, Cloth, Provisions, Energy Drink, Battery. |
| 12 | **Threat Cards** | 51 cards | `DeckCustom` | Enemies and hazards drawn during night phase or by Dawn cards (incl. sealed things — §13.5). |
| 13 | **Combat Dice (d6)** | 6 standard | `Die_6` | Rolled in handfuls during combat. |
| 14 | **Sanity d8 (custom)** | 1 | `Custom_Dice` (8 faces) | For sanity-loss events with variable severity. |
| 15 | **Boss Standees** | 4 | `Figurine_Custom` | One per phase boss. Larger silhouettes than characters (DST scale principle). |
| 16 | **Trophy Cards** | 4 | Loose `Card`s | Awarded for defeating phase bosses; provide passive bonuses. |
| 17 | **Telltale Heart Tokens** | 5 | `Custom_Token` | Used for revival rite (see §16.4). |
| 18 | **Character Reference Cards** | 5 | Loose `Card`s | Per-character cheat sheet. |
| 19 | **Rules Quick-Start Card** | 1 | `Notecard` | Onboarding aid. |

---

## 6. Characters

Each character is a **mechanical hook + a constraint + a starting hand of 5 cards**, of which **3 are laid out face up at Setup** and the remaining ones arrive on Days 2 and 3 (§17.1). Asymmetry follows the Cthulhu Wars principle (different rules, not just different stats; see InterestingGames.md §3.3.1).

### 6.1 James — The Gamer

- **Identity.** Caucasian male. Late teens. Insomniac. Lives at James's House.
- **Visual style.** Hoodie, dark circles under eyes, controller dangling from a pocket.
- **Base Stats.** Health **8**, Hunger **6**, Sanity **10**.
- **Perk: Gaming Reflexes.** Once per turn, may reroll one of his own dice (combat or event).
- **Perk: Pattern Recognition.** May peek at the top card of any deck once per day.
- **Signature: All-Nighter (once per game, §6.7).** Take 3 extra actions this turn; James loses 3 Sanity at the next Tick. The crash always comes.
- **Constraint: Wired.** James starts the game addicted to Energy Drinks. If he does not consume an Energy Drink token by the end of any day, he loses 2 Sanity that night.
- **Starting hand:** Energy Drink ×2, Pocketknife, Flashlight, Headphones (sanity buffer).
- **Plays best with:** Coco (sanity stability), Ellie (food independence).

### 6.2 Coco — The Angel

- **Identity.** Asian female. Calm presence. Spiritual core. Visiting from out of town — does not have her own house tile.
- **Visual style.** Soft sweater, pale halo motif faintly visible in her shadow on the map.
- **Base Stats.** Health **6**, Hunger **8**, Sanity **12**.
- **Perk: Calming Presence.** All allies in Coco's location lose 1 less Sanity at the night Tick (minimum 0).
- **Signature: Touch of Hope (once per game, §6.7).** Heal any character on the map by 4 Health, regardless of distance.
- **Perk: Light in the Dark.** Coco never triggers Charlie attacks (see §15.4).
- **Constraint: No Home.** Coco does not have a house tile. Each night she must declare a location that contains another player; if she ends the night alone in a non-house tile she loses 3 Sanity.
- **Starting hand:** First Aid Kit, Comfort Blanket, Hopeful Tea, Spare Phone Battery (Day 2), Friendship Bracelet (Day 3).
- **Plays best with:** Anyone — Coco is a glue character.

### 6.3 Rayman — The Basketball Player

- **Identity.** Asian male. Athletic, kinetic, the team's muscle. Lives at Rayman's House.
- **Visual style.** Jersey, gym shorts, basketball under one arm even in monster fights.
- **Base Stats.** Health **12**, Hunger **10**, Sanity **6**.
- **Perk: Speed.** Moves 1 extra space per Move action.
- **Perk: Court Master.** When Rayman fights at the Basketball Court, he gains +1 attack die.
- **Perk: Backboard Block.** Can spend an action to "Defend": adjacent allies cannot be targeted by enemies until Rayman's next turn.
- **Signature: Posterize (once per game, §6.7).** Instantly defeat one non-boss threat at his tile — no roll, no counter. The noise: his tile draws +1 Threat tonight.
- **Constraint: Big Appetite.** Loses 2 Hunger per day Tick (other characters lose 1).
- **Constraint: Loud.** If Rayman moved at all today (any Move, his Speed bonus step, or a Dusk scramble), the location where he spends the Night draws **1 extra Threat card**. It triggers at most once per night and follows him — the noise comes home with him. Tiles he merely passed through are unaffected. A day spent standing still is a quiet one, which makes "does Rayman move today?" a real team decision rather than a per-step tax.
- **Starting hand:** Basketball (improvised weapon), Sports Drink ×2, Athletic Tape (Day 2), Whistle (Day 3).
- **Plays best with:** Ellie (food management), Luca (Sanity).

### 6.4 Ellie — The Cook

- **Identity.** Caucasian female. Calm under pressure. Lives at Ellie & Luca's House (with Luca).
- **Visual style.** Apron over a sweatshirt, hair tied back, a wooden spoon as habitual gesture.
- **Base Stats.** Health **8**, Hunger **10**, Sanity **8**.
- **Perk: Crockpot Master.** Recipes Ellie cooks require 1 fewer ingredient (minimum 1).
- **Perk: Comfort Food.** When Ellie shares cooked food with another character, that character gains +1 extra Hunger and +1 extra Sanity.
- **Perk: Knows the Pantry.** When at Ellie & Luca's House, Ellie may search the resource bag for a specific Provisions or Cooking Ingredient (does not draw randomly).
- **Signature: The Feast (once per game, §6.7).** Cook any number of recipes in a single action (ingredients still required, at a Crockpot); consumes **all** her held Provisions.
- **Constraint: Particular Eater.** Ellie cannot eat uncooked food. (Other characters can spend a Provisions token uncooked for partial Hunger; Ellie cannot.)
- **Starting hand:** Crockpot, Cooking Knife, Apron, Soup Recipe (Day 2), Pantry Key (Day 3).
- **Plays best with:** Rayman (he eats a lot), Luca (housemate synergy).

### 6.5 Luca — The Orator

- **Identity.** Caucasian male. Articulate, persuasive, the team's morale officer. Lives at Ellie & Luca's House (with Ellie).
- **Visual style.** Round-frame glasses, a slightly worn cardigan, a paperback in his pocket.
- **Base Stats.** Health **7**, Hunger **8**, Sanity **10**.
- **Perk: Rally.** Once per **round**, give an ally at his tile or an adjacent one a free non-movement action — **and he may fire it on that ally's own turn**, not only during his. (Retuned from "once per turn": once Rally became firable off-turn, a per-turn window would have given Luca one rally per *player* turn, up to +4 actions a day at five players. Once per round keeps his old effective power and changes only *when* he spends it — which is the whole point: an interruption-shaped decision instead of a pre-allocation. See §11.2.)
- **Perk: Calm Words.** When a Sanity-loss event occurs in his location, Luca may roll a d6: on 4+, the entire group at his location ignores the loss.
- **Perk: Storyteller.** During Night, players in Luca's location regain +1 Sanity.
- **Signature: The Speech (once per game, §6.7).** Every character, anywhere, gains +2 Sanity. Only speakable while an ally is Down or below 3 Sanity — it has to *matter*.
- **Constraint: Needs an Audience.** Luca regenerates Sanity only when at least one other player is in his location. Alone, his Sanity does not regenerate.
- **Starting hand:** Notebook, Pep-Talk (single-use card), Reading Lamp, Toolbox (Day 2), Loud Whistle (Day 3).
- **Plays best with:** Anyone with low Sanity (he supports them).

### 6.6 Character Selection and Group Composition

- Players choose characters in any order (suggest reverse-age, alphabet, or draft).
- A **3-player game** uses 3 characters. The remaining two are **Visitor NPCs** that can be encountered at houses (drawn via a Dawn event card around Day 3 — they offer one-time aid, then depart at the next Dawn).
- A **4-player game** plays the same way but with one Visitor NPC.
- A **5-player game** has all five active.
- **3-player composition guidance (provisional, simulation-derived — see §20.1).** Any 3 characters is *legal*, but the compositions are not equally forgiving: the Monte Carlo sweep (`scripts/simulate_balance.py --sweep3`) found every strong trio carries a sanity-support character (Coco or Luca), and trios built around Rayman struggled badly at the 3-player action economy — his Big Appetite and Loud are fixed overheads that three players absorb much worse than five. Until playtests settle it, teach 3-player groups: *take Coco or Luca, and know that Rayman is hard mode.* If human play confirms the gap, the fix is character numbers (per-count constraint scaling), not roster restrictions.

### 6.7 Signature Moves

Each character has one **Signature** — a once-per-game, named, board-printed move. Passive perks make characters *play* differently; Signatures make players *remember* their character: the big move you saved all game for one perfect moment, and the story you retell afterward. Five properties are shared:

- **Once per game.** Fired from the character's Signature button (TTS) with an explicit confirm — these are irreversible one-shots (§18.14).
- **Mismatched currency (§8.4).** Every Signature pays in a stat *adjacent* to what it buys: All-Nighter buys actions with future Sanity; Posterize buys a kill with tonight's threat draw; The Feast buys a banquet with the whole pantry. No Health-for-Health.
- **A guaranteed story beat.** Five cards' worth of rules buy five retellable moments per campaign — Week in Review (§16.5) narrates them.
- **Tuned for the finale.** Signatures are at their best in Days 5–7, and the endgame (the split-phase Source, §12.6; Nothing Left to Lose, §15.2) is tuned assuming they exist.
- **Board print is legibility polish.** The mechanic ships on the button + confirm; printing the Signature line on the player boards is a follow-on art pass (§18.10).

| Character | Signature (once per game) | Cost (mismatched) |
|---|---|---|
| James | **All-Nighter** — take 3 extra actions this turn | −3 Sanity at the next Tick |
| Coco | **Touch of Hope** — heal any character on the map by 4 Health | Once per game; any distance |
| Rayman | **Posterize** — instantly defeat one non-boss threat at his tile | The noise: +1 Threat draw here tonight |
| Ellie | **The Feast** — cook any number of recipes in a single action | Consumes **all** her held Provisions |
| Luca | **The Speech** — every character, anywhere, +2 Sanity | Only while an ally is Down or below 3 Sanity |

*(Rayman's Speed and Luca's Rally both read as "once per turn" historically; Rally is now once per round and off-turn — §6.5.)*

*Interaction watch (intended drama, not a bug):* James can All-Nighter (−3 Sanity pending), press attacks (−1 Sanity each, §12.5), and go Down from his own aggression. Both costs are surfaced in the Rules panel and confirm dialogs so it is always a visible, chosen risk.

---

