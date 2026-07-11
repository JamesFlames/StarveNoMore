# Starve No More — Design Concept

> A cooperative survival board game for 3–5 players. Suburban friends caught when something cosmic descends on their neighborhood must scavenge, cook, fight, and hold their sanity together for seven nights. Aesthetic and tone modeled on *Don't Starve Together*; mechanical DNA drawn from *Don't Starve Together*, *Harry Potter: Hogwarts Battle*, *Settlers of Catan*, and *Cthulhu Wars*. Designed to be implemented in **Tabletop Simulator** (Berserk Games, app `286160`).

---

## Document Purpose

This is the design brief for **Starve No More**. It is intended as the single source of truth used to:

1. Communicate the game's vision, theme, and rules.
2. Drive prototype playtesting.
3. Hand off to the Tabletop Simulator implementation phase as a buildable spec.

The document references and is consistent with:
- [Archive/PrinciplesOfGoodBoardGames.md](Archive/PrinciplesOfGoodBoardGames.md) — general design theory.
- [Archive/DontStarveVideoGamePrinciples.md](Archive/DontStarveVideoGamePrinciples.md) — DST-derived design pillars.
- [Archive/InterestingGames.md](Archive/InterestingGames.md) — mechanical patterns from HPHB, Catan, Cthulhu Wars.
- [Archive/HowToCreateGamesInTabletopSimulator.md](Archive/HowToCreateGamesInTabletopSimulator.md) — implementation reference (frozen).

---

## Table of Contents

1. [Pitch and Premise](#1-pitch-and-premise)
2. [Design Pillars](#2-design-pillars)
3. [Player Count, Length, and Audience](#3-player-count-length-and-audience)
4. [The Core Loop](#4-the-core-loop)
5. [Components List](#5-components-list)
6. [Characters](#6-characters)
7. [Locations](#7-locations)
8. [Resources and the Economy](#8-resources-and-the-economy)
9. [The Card Decks](#9-the-card-decks)
10. [Stats and Player Boards](#10-stats-and-player-boards)
11. [Turn Structure](#11-turn-structure)
12. [Combat](#12-combat)
13. [Crafting and Cooking](#13-crafting-and-cooking)
14. [The Week Arc and Pacing](#14-the-week-arc-and-pacing)
15. [The Doom Track and Scheduled Threats](#15-the-doom-track-and-scheduled-threats)
16. [Victory and Defeat Conditions](#16-victory-and-defeat-conditions)
17. [Setup](#17-setup)
18. [Tabletop Simulator Implementation](#18-tabletop-simulator-implementation)
19. [Design Rationale Cross-Reference](#19-design-rationale-cross-reference)
20. [Balancing, Playtest Plan, Expansion Hooks](#20-balancing-playtest-plan-expansion-hooks)

---

## 1. Pitch and Premise

### 1.1 The pitch

> Five friends gathered on a perfectly ordinary suburban evening. Then the streetlights flickered out, the phones lost signal, and something began to move through the trees that didn't have a name in any language they knew. They have one week.

**Starve No More** is a cooperative survival board game that turns the players' familiar world — their houses, their school courts — into a haunted map. Players take on the roles of **James, Coco, Rayman, Ellie, and Luca**, each with unique abilities and constraints, and must keep their **Health, Hunger, and Sanity** above zero for seven in-game days while exploring five connected locations, scavenging resources, crafting items, fighting cosmic horrors that wear ordinary shapes, and pushing back the rising **Doom** that threatens to consume their neighborhood.

### 1.2 The tone

The aesthetic is **Don't Starve Together transplanted into a North American suburb**. Tim-Burton-meets-Edward-Gorey ink-line illustration, but the line draws cul-de-sacs and basketball hoops instead of Victorian forests. Comfortable spaces (a kitchen, a gaming chair) rendered just slightly wrong. Characters with spindly limbs and oversized eyes. Monsters that look like a friend's silhouette glimpsed through a screen door, but with too many teeth.

The game wants players to feel:
- **Cozy and dread at once.** Camp by the kitchen with friends, but listen for the thing in the basement.
- **Outmatched but determined.** The world is bigger than them. They survive by being clever and helping each other.
- **Storied.** Every play should leave a memory: the night Rayman went out to the badminton court alone and didn't come back; the dawn Ellie's crockpot fed the whole team back into fighting shape.

### 1.3 The hook

What makes Starve No More distinct from a generic co-op survival game:

- **The setting is small and personal.** Five named locations — three of them the players' own houses — make every map decision feel intimate.
- **Genuine character asymmetry.** The five characters play meaningfully different games: deck manipulation, healing, combat, cooking, leadership. Different group compositions feel different.
- **Three-meter trade-off economy.** Health, Hunger, Sanity. Every action pays in a different currency than the one it fills. Borrowed directly from the heart of DST.
- **Difficulty by escalation, not by tier.** Like HPHB years, each in-game day adds threats, never resets — but the experience is single-session, not legacy-locked.

### 1.4 The target aesthetic (what players should feel)

Working backwards through the MDA framework ([PrinciplesOfGoodBoardGames.md §1](Archive/PrinciplesOfGoodBoardGames.md)) — mechanics produce dynamics produce *aesthetics*. The aesthetics this game targets, ranked by priority:

1. **Cozy dread.** The single emotion the game is built around. The kitchen with friends, the thing in the basement. If a rule makes the table feel like neither cozy nor dreadful, it's wrong.
2. **Clever desperation.** Players survive by being smart, not by being lucky. Wins should feel earned, even close ones. Losses should feel like a chain of small visible mistakes — never unfair.
3. **Storied collaboration.** Every play should produce one moment the table will retell. "Remember when Rayman went out alone." "Remember the night Ellie cooked the last Battery Acid Soup." Stories are the replayability engine.
4. **Personal asymmetry.** Each character should *feel* different to play, not just have different numbers. A James player and an Ellie player should describe their game in different language at the end of the night.

If a candidate rule does not clearly serve at least one of (1)–(4), it does not earn its place in the rulebook.

---

## 2. Design Pillars

The five non-negotiable principles that all rules decisions must serve. Drawn from the Don't Starve translation work in [DontStarveVideoGamePrinciples.md](Archive/DontStarveVideoGamePrinciples.md) and the design theory in [PrinciplesOfGoodBoardGames.md](Archive/PrinciplesOfGoodBoardGames.md).

1. **Tone over polish.** A coherent gothic-cartoon visual identity matters more than asset volume. Hand-drawn ink art across every component, even if it means fewer components.
2. **Decisions paid in mismatched currencies.** Every meaningful action costs the player in a stat *adjacent* to the one they want to fill. No free lunches; no pure builders.
3. **The world acts first.** Every round opens with an event from a hostile deck. Nothing is ever safe.
4. **Specialization beats parallelism.** Characters are mechanically distinct enough that group success requires them to play complementary roles, not all do the same thing.
5. **Emergent stories, not scripted narrative.** The game generates memorable moments through systems interaction, not through a 200-card flavor-text deck.

A rule that violates any of these gets cut.

---

## 3. Player Count, Length, and Audience

| Attribute | Value |
|---|---|
| Player count | 3–5 (cooperative) |
| Recommended | 4 |
| Game length | 60–90 minutes (full 7-day campaign) |
| Shorter mode | "Long Weekend" — 3 in-game days, 25–35 minutes |
| Age | 12+ |
| Complexity (BGG-equivalent weight) | ~2.5 / 5 — medium. Comparable to *Pandemic* or *Spirit Island Beginner*. |
| Required players seated | At least 3 of the 5 characters must be in play. Unused characters become NPCs available as **Visitor cards** that can join the party mid-game. |

**Player count notes.** The minimum of 3 is a deliberate design choice — at 2 players the social/specialization layer collapses (one of *Starve No More*'s pillars). With 5 players, every character is in play and the table is full. Above 5 the game would lose its intimate feel; we cap there.

---

## 4. The Core Loop

A single round (one in-game day) cycles through:

1. **Dawn (event)** — Doom advances (by phase rate, plus festering: +1 per threat left on the map, +2 per boss — see §15.1). Court survivors collect their Moonlit Salvage (§7.4). Then reveal the day's **Dawn card** from the current Phase deck and resolve immediately. (See §15.)
2. **Day Phase (player actions)** — Each player takes a fixed number of actions in turn order. Default: **3 actions per player**.
3. **Dusk (scramble)** — Each character may make one last **1-tile move, paying 1 Hunger**, then declares publicly where they sleep. You sleep where you stand.
4. **Night Phase (resolution)** — All players resolve night events at their chosen location. Players alone in dangerous spaces suffer additional consequences — and are paid for surviving them.
5. **Tick (decay)** — Every player loses 1 Hunger and 1 Sanity (modified by location and character traits). Day counter advances.

The loop is **unrelenting**: even a perfectly executed day still costs the players something. The game is therefore not "make zero mistakes" but "spend wisely on the right things."

---

## 5. Components List

Every component is sized, type-marked, and TTS-mappable. The "TTS Object" column references object types from [HowToCreateGamesInTabletopSimulator.md §5](Archive/HowToCreateGamesInTabletopSimulator.md).

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
| 9 | **Item Cards (the Market)** | ~50 unique cards | `DeckCustom` | The shared "Hogwarts Deck" of craftable items. |
| 10 | **Recipe Cards** | ~20 unique cards | `DeckCustom` | Crockpot recipes; reference cards more than draw deck. |
| 11 | **Resource Tokens** | ~120 in 6 types | `Custom_Token` (small) or `Infinite_Bag` | Wood, Metal, Cloth, Food, Energy Drink, Battery. |
| 12 | **Threat Cards** | ~30 cards | `DeckCustom` | Enemies and hazards drawn during night phase or by Dawn cards. |
| 13 | **Combat Dice (d6)** | 6 standard | `Die_6` | Rolled in handfuls during combat. |
| 14 | **Sanity d8 (custom)** | 1 | `Custom_Dice` (8 faces) | For sanity-loss events with variable severity. |
| 15 | **Boss Standees** | 4 | `Figurine_Custom` | One per phase boss. Larger silhouettes than characters (DST scale principle). |
| 16 | **Trophy Cards** | 4 | Loose `Card`s | Awarded for defeating phase bosses; provide passive bonuses. |
| 17 | **Telltale Heart Tokens** | 5 | `Custom_Token` | Used for revival rite (see §16.4). |
| 18 | **Character Reference Cards** | 5 | Loose `Card`s | Per-character cheat sheet. |
| 19 | **Rules Quick-Start Card** | 1 | `Notecard` | Onboarding aid. |

---

## 6. Characters

Each character is a **mechanical hook + a constraint + a starting hand of 5 cards**. Asymmetry follows the Cthulhu Wars principle (different rules, not just different stats; see [InterestingGames.md §3.3.1](Archive/InterestingGames.md)).

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
- **Starting hand:** First Aid Kit, Comfort Blanket, Hopeful Tea, Spare Phone Battery, Friendship Bracelet.
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
- **Starting hand:** Basketball (improvised weapon), Sports Drink ×2, Athletic Tape, Whistle.
- **Plays best with:** Ellie (food management), Luca (Sanity).

### 6.4 Ellie — The Cook

- **Identity.** Caucasian female. Calm under pressure. Lives at Ellie & Luca's House (with Luca).
- **Visual style.** Apron over a sweatshirt, hair tied back, a wooden spoon as habitual gesture.
- **Base Stats.** Health **8**, Hunger **10**, Sanity **8**.
- **Perk: Crockpot Master.** Recipes Ellie cooks require 1 fewer ingredient (minimum 1).
- **Perk: Comfort Food.** When Ellie shares cooked food with another character, that character gains +1 extra Hunger and +1 extra Sanity.
- **Perk: Knows the Pantry.** When at Ellie & Luca's House, Ellie may search the resource bag for a specific Food or Cooking Ingredient (does not draw randomly).
- **Signature: The Feast (once per game, §6.7).** Cook any number of recipes in a single action (ingredients still required, at a Crockpot); consumes **all** her held Food.
- **Constraint: Particular Eater.** Ellie cannot eat raw food. (Other characters can spend a Food token raw for partial Hunger; Ellie cannot.)
- **Starting hand:** Crockpot, Soup Recipe, Cooking Knife, Pantry Key, Apron (item).
- **Plays best with:** Rayman (he eats a lot), Luca (housemate synergy).

### 6.5 Luca — The Orator

- **Identity.** Caucasian male. Articulate, persuasive, the team's morale officer. Lives at Ellie & Luca's House (with Ellie).
- **Visual style.** Round-frame glasses, a slightly worn cardigan, a paperback in his pocket.
- **Base Stats.** Health **7**, Hunger **8**, Sanity **10**.
- **Perk: Rally.** Once per turn, give an adjacent ally a free non-movement action.
- **Perk: Calm Words.** When a Sanity-loss event occurs in his location, Luca may roll a d6: on 4+, the entire group at his location ignores the loss.
- **Perk: Storyteller.** During Night, players in Luca's location regain +1 Sanity.
- **Signature: The Speech (once per game, §6.7).** Every character, anywhere, gains +2 Sanity. Only speakable while an ally is Down or below 3 Sanity — it has to *matter*.
- **Constraint: Needs an Audience.** Luca regenerates Sanity only when at least one other player is in his location. Alone, his Sanity does not regenerate.
- **Starting hand:** Notebook, Loud Whistle, Pep-Talk (single-use card), Reading Lamp, Toolbox.
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
| Ellie | **The Feast** — cook any number of recipes in a single action | Consumes **all** her held Food |
| Luca | **The Speech** — every character, anywhere, +2 Sanity | Only while an ally is Down or below 3 Sanity |

*Interaction watch (intended drama, not a bug):* James can All-Nighter (−3 Sanity pending), press attacks (−1 Sanity each, §12.5), and go Down from his own aggression. Both costs are surfaced in the Rules panel and confirm dialogs so it is always a visible, chosen risk.

---

## 7. Locations

Five tiles arranged on the main board. Connections between tiles form the movement graph. Each tile has: a **resource yield**, a **special action**, a **Sanity modifier** (during the night Tick), and a **defensive value** (combat modifier when fighting there).

The tile graph (paths between tiles):

```
                [The School's Basketball Court]
                          |
[James's House] -- [Ellie & Luca's House] -- [Rayman's House]
                          |
                [The Badminton Court]
```

Ellie & Luca's House is the central node (their kitchen feeds the team). The two sport courts are exposed dead-ends that extend the map.

### 7.1 James's House

- **Yield.** Energy Drink ×1 per gather, Battery ×1 per two gathers, Junk Food (Food) ×1.
- **Special: The Den.** Players in this location may freely trade cards with each other once per day (no action cost).
- **Special: The Stash.** A Gather action here may take **2 Energy Drinks** instead of the normal random draw. This exists so James's Wired constraint is a logistics problem (stock up every other day), not a daily ritual that eats a third of his action budget.
- **Sanity modifier:** 0 (familiar but cluttered).
- **Defense:** +0.
- **House owner:** James gains +1 Sanity per night when sleeping at his own house.

### 7.2 Rayman's House

- **Yield.** Sports Equipment (improvised weapons; see §13), Sports Drink (Food), Athletic Tape (crafting).
- **Special: The Garage.** A Rest action here restores +1 Health (instead of +0).
- **Sanity modifier:** 0.
- **Defense:** +1 (lots of cover).
- **House owner:** Rayman gains +1 Health per night when sleeping at his own house.

### 7.3 Ellie & Luca's House

- **Yield.** Cooking Ingredients (Food), Cloth, Pantry items.
- **Special: The Kitchen.** This location has a permanent Crockpot. Any player here may cook recipes; Ellie's perk applies if she's present.
- **Sanity modifier:** +1 (homey, warm).
- **Defense:** +0.
- **House owners:** Ellie and Luca gain +1 Sanity per night when sleeping at their own house.

### 7.4 The School's Basketball Court

- **Yield.** Wood (broken bleachers), Metal (hoops, fencing), Cloth (forgotten gym clothes).
- **Special: Echoes.** Each time a player gathers here, they roll a d6. On 6, draw a bonus item card. On 1–2, lose 1 Sanity.
- **Special: Moonlit Salvage.** A character who spends the night here and is still standing at Dawn gathers **2 resources** from this court's bag. The courts are richest when the world sleeps — sleeping out is a calculated gamble, not a blunder.
- **Sanity modifier:** −1 (creepy at night, the building groans).
- **Defense:** −1 (open court, exposed).
- **Rayman bonus:** Court Master perk applies.

### 7.5 The Badminton Court

- **Yield.** Cloth (nets), Wood (rackets, posts), Metal (fittings).
- **Special: The Net.** When defending in combat at this location, the team rolls +1 die (the nets entangle attackers).
- **Special: Moonlit Salvage.** Same as the Basketball Court (§7.4): survive a night here, gather 2 resources at Dawn.
- **Sanity modifier:** −1.
- **Defense:** +1 (the nets help).
- **Special hazard:** The Badminton Court has the highest threat-card draw rate at night (see §15).

### 7.6 Map Variability

For replayability without scripting more rules, the path graph is **modular**: at game setup, players may shuffle the path-edge cards (3 standard configurations: "Compact," "Sprawl," "Linear") to slightly vary the movement geometry. This is the lightweight Catan-variability lever from [InterestingGames.md §2.3.1](Archive/InterestingGames.md).

---

## 8. Resources and the Economy

Six resource types. Each has multiple uses; each is gathered from particular locations; each enters the game from a shared pool.

| Resource | Symbol/Color | Found at | Uses |
|---|---|---|---|
| **Wood** | Brown plank icon | Basketball Court, Badminton Court | Crafting weapons, structures, fuel for Crockpot |
| **Metal** | Grey gear icon | Basketball Court (hoops), Rayman's House (tools) | Weapon upgrades, Repair, advanced crafting |
| **Cloth** | White-thread icon | All locations (esp. Ellie & Luca's, Badminton Court) | Bandages, Insulation, Bedrolls |
| **Food** | Red apple icon | All locations (esp. Ellie & Luca's, James's House) | Restore Hunger; cook into recipes for greater effect |
| **Energy Drink** | Yellow can icon | James's House only | Restore 2 Sanity; James's daily addiction |
| **Battery** | Blue battery icon | James's House, Rayman's House | Powers Flashlights, Radios, electronic items |

### 8.1 Gathering

A **Gather** action costs 1 of the player's 3 daily actions and yields **1 randomly-drawn resource** from the resource bag of the current location. Some characters and items modify gathering (Ellie's "Knows the Pantry"; an Item card "Backpack" gathers 2 instead of 1).

### 8.2 Trading

Players in the same location may trade resources, cards, or both **freely on either's turn**, with no action cost. This is the Catan negotiation layer ([InterestingGames.md §2.3.8](Archive/InterestingGames.md)) — open, social, deal-driven. The constraint that they must be in the same location is the design lever that makes location-choice a social decision, not just a logistical one.

### 8.3 Hand Limit

Each player has a hand limit of **5 item cards** + **8 resources**. Excess must be dropped at the location they're currently in (becomes a free pickup for the next visitor).

This is the Catan 7-roll discipline ported in: it discourages hoarding, encourages crafting, and forces trades.

### 8.4 The mismatched-currency map

Pillar 2 — *every action pays in a different currency than the one it fills* — must be visible in the rules, not just claimed in the pitch. The table below is the audit: every restorative action and the cross-currency cost it pays. If a future rule edit puts a row on the diagonal (paying in the same stat it fills), the rule is wrong.

| Action | Restores | Pays in (the cross-currency) |
|---|---|---|
| **Eat raw food** | Hunger (1) | Sanity (−1) — DST raw-food penalty. |
| **Cook at the Crockpot** | Hunger + Sanity (large) | Action + 1 Wood (fuel) + ingredients. |
| **Battery Acid Soup** | Hunger (6) | Health (−2). High risk recipe. |
| **Rest at home** | Hunger or Sanity, +1 Health if own house | Action (no resource gain that turn). |
| **Use Comfort item** | Sanity | Item slot consumed (or charge spent). |
| **Energy Drink** | Sanity (2) | One Energy Drink token; James gets addicted (Sanity penalty if skipped). |
| **Defeat an enemy** | Sanity (small, story payoff) | Health (combat damage); fumble dice (1s). |
| **Cleanse the Doom track** | World safety (Doom −2) | 1 each: Wood, Cloth, Battery, Energy Drink + Action. |
| **Revive a Down ally** | Their Health/Sanity | Reviver's Health (−2) + Telltale Heart bundle. |
| **Move to a new location** | Spatial position (resources, allies) | Hunger (1) + risk of threat draws. |
| **Gather a resource** | Resource pool | Action + sometimes Sanity (Echoes at the Court). |

The pattern is intentional and total: there is no action in this game that lets you fill a stat using only that same stat's track. **All progress is paid for in adjacent currencies.** This is the engine that turns a survival theme into a decision game.

---

## 9. The Card Decks

The game has five distinct decks. All are listed in §5; this section covers their content and design intent.

### 9.1 The Phase Decks (Dawn cards)

Four decks, played in order across the seven-day campaign:

- **Phase 1: Dusk of the Week** (~10 cards) — Days 1–2. Mild events: minor sanity blips, lost items, weather.
- **Phase 2: Strange Days** (~10 cards) — Days 3–4. Escalating threats: monsters glimpsed, food spoils.
- **Phase 3: Long Nights** (~10 cards) — Day 5. Boss event. Heavy disruption.
- **Phase 4: Final Hours** (~10 cards) — Days 6–7. Survival sprint. Doom advances faster.

Each Dawn card has:
- A **flavor headline** ("The streetlights flicker. Something on the porch.")
- An **immediate effect** ("All players lose 1 Sanity.")
- Sometimes an **ongoing effect** ("Until the next Dawn, all gathers cost 1 extra Hunger.")
- Sometimes a **Dare** — an *optional* hook alongside the mandatory effect ("DARE: the first player to Gather at a house today may take 3 resources instead of 1 — and lose 2 Sanity from what they see through the window."). Roughly a third of the **Phase 1–2** cards carry one; the late-week decks stay lean and lethal. The world acting first (Pillar 3) is more interesting when it sometimes acts as a *tempter*, not only a mugger: each dare is a mismatched-currency gamble (§8.4) the table argues over, which is exactly the texture the quiet *Jo* days were missing. Dares are never imposed — scripted ones are offered via a confirm or opt-in behaviour (sleeping at the glowing court); the rest appear as optional checklist steps.

The Phase deck order is fixed, but card draw within a deck is shuffled — same shape, different details. (DST seasons principle: predictable structure, unpredictable details.)

### 9.2 The Market Deck (Item cards, "the Hogwarts deck")

A face-up market of 5 cards (a "shop" displayed on the table) drawn from a shuffled deck of ~50 unique items. Players spend resources on their turn to **craft** an item — claim it from the market into their hand. A new card is drawn from the deck to refill the market slot.

Item categories:

- **Tools** (Flashlight, Crowbar, First Aid Kit, Bandage)
- **Weapons** (Improvised Bat, Sharpened Spoon, Slingshot, Toy Bow)
- **Comfort items** (Stuffed Animal, Photo Album, Music Player) — restore Sanity
- **Foods** (Cooked Stew, Energy Bar, Hot Cocoa) — restore Hunger
- **Special** (Telltale Heart for revival, Circle of Salt for boss combat)

Each item has a craft cost (resources), a use effect, and notes whether it's single-use or persistent. The market refresh creates the same "store rotation" energy as a deckbuilder's market row ([InterestingGames.md §1.3](Archive/InterestingGames.md)).

### 9.3 The Recipe Cards

Permanent reference cards (not a draw deck) showing what can be cooked at a Crockpot. Examples:

- **Hot Stew** — 2 Food + 1 Wood. Restores 4 Hunger + 2 Sanity to all eaters.
- **Energy Drink Cocktail** — 2 Energy Drink + 1 Food. Restores 5 Sanity, 2 Hunger.
- **Comfort Soup** — 3 Food + 1 Cloth (for napkins). Restores 3 Hunger + 3 Sanity.
- **Battery Acid Soup** (don't) — 1 Battery + 2 Food. Restores 6 Hunger but loses 2 Health.

Recipes embody the **mismatched-currency** principle: cooking costs raw ingredients to produce more potent restoration than raw eating, but always with some trade-off (an action spent, a wood burned, a chance of bad outcomes for risky recipes).

### 9.4 The Threat Deck

~30 cards, drawn during the Night phase based on each location's threat rate. Threat cards include:

- **Enemies** that fight: "Shadow Stalker (HP 4, Atk 2)" — must be defeated.
- **Hazards**: "The Power Cuts. Lose 1 Battery if you have any; otherwise lose 1 Sanity."
- **Atmospheric**: "You hear something walking upstairs. Player here loses 1 Sanity."

Some threats are **soft** (a one-time penalty), some are **hard** (must be fought), and a few are **persistent** (stays on the location until cleared).

Two special threat shapes:

- **Sealed things** (`T_THE_DOOR`, `T_LOCKED_ROOM`, `T_SEALED_SHED`, `T_SEALED_LOCKER`, `T_SEALED_CAR`) — a *guaranteed* reward behind a tool gate: Pry them open (§13.5) for resources or a free Item. No dice, a clear goal, and a reason to have crafted the Crowbar.
- **The Wrongness** (deferred threat, placed by the Phase-2 Dawn card *A Basketball Bounces in the Dark*) — the top Threat card is placed **face-down** at the Basketball Court and does **not** resolve. It resolves when a character enters that tile (someone goes to look) or at the next Dawn (it comes to them), whichever first. Until then it sits there, visibly unresolved, and the table argues about who goes to check — an hour of dread from one card. While face-down it does not fester (it is unresolved, not fled-from); exactly one such card exists, because two loose "something is wrong" objects dilute dread into bookkeeping.

### 9.5 The Visitor Deck (small)

A small deck of ~6 cards used in 3- and 4-player games, representing the absent characters arriving for limited support. Triggered by a specific Dawn card mid-game.

When a Visitor card resolves:

1. The drawing player chooses one of the **inactive characters** (those not played by a human at the table) and places their standee at a house location indicated on the card.
2. The Visitor takes a one-shot signature action immediately (e.g., "Coco arrives. Heal one Down ally to 1 Health.") then departs at the next Dawn.

That's the whole mechanic: a knock at the door, one act of kindness, gone by morning. An earlier draft had an "adoption" rule that let a player keep the Visitor as a stat-shared NPC — cut, per the §19.6 self-audit. It was the most convoluted rule in the game, in service of the deck the design already flagged as its weakest. Visitors now reward 3- and 4-player tables with mid-game flavor at zero rules overhead.

### 9.6 Sample cards (concrete examples)

To make the rules above tangible, here are five fully-written sample cards — one per deck. The full design will exceed these examples but they fix the *shape* of each deck's content.

#### Sample Dawn card (Phase 2: Strange Days)

```
┌──────────────────────────────────────────────┐
│ THE PORCH LIGHT FLICKERS                     │
│ ─────────────────────────────                │
│ The bulbs on every porch click off, all at   │
│ once. Nobody flipped a switch.               │
│                                              │
│ IMMEDIATE: All players lose 1 Sanity.        │
│ ONGOING (until next Dawn):                   │
│   • Charlie checks at night ignore           │
│     Flashlights — only Fire counts as        │
│     a light source tonight.                  │
│                                              │
│ Severity: ●●○○○ (mild–moderate)              │
└──────────────────────────────────────────────┘
```

The five-pip **severity dot** is the Catan-probability-dots pattern ([InterestingGames.md §2.3.2](Archive/InterestingGames.md)) ported to event cards: at-a-glance signal of how punishing this Dawn will be, so players can read pressure visually without parsing rules text.

#### Sample Item card (Market deck)

```
┌──────────────────────────────────────────────┐
│ CROWBAR                                      │
│ ─────────────────────────────                │
│ Type: Tool / Weapon                          │
│ Craft cost: 2 Metal + 1 Wood                 │
│                                              │
│ Persistent. Equip to your Player Board.      │
│                                              │
│ • +1 Attack die in combat.                   │
│ • Free action: Pry. Open a sealed Threat,    │
│   Door, or Container at your location.       │
│ • Vulnerable: a natural 1 in combat does     │
│   not break the Crowbar (you're using it     │
│   wrong, but it's solid).                    │
└──────────────────────────────────────────────┘
```

#### Sample Recipe card

```
┌──────────────────────────────────────────────┐
│ HOT STEW                                     │
│ ─────────────────────────────                │
│ Cook at: Crockpot.                           │
│ Ingredients: 2 Food + 1 Wood (fuel).         │
│ Action cost: 1.                              │
│                                              │
│ Effect: All characters at this location      │
│ gain +4 Hunger and +2 Sanity.                │
│ (Ellie's Comfort Food perk: +1 each, every   │
│  ally she shares with.)                      │
│                                              │
│ Pillar trace: pays Action+Wood+ingredients   │
│ to fill Hunger+Sanity (mismatched currency). │
└──────────────────────────────────────────────┘
```

#### Sample Threat card

```
┌──────────────────────────────────────────────┐
│ SHADOW STALKER                               │
│ ─────────────────────────────                │
│ Type: Hard threat (must be fought or fled).  │
│ HP: 4    Attack dice: 2                      │
│ Spawn: Wherever this card was drawn.         │
│                                              │
│ Special: Edge of Vision.                     │
│ While the Stalker is in play, all players in │
│ its location lose 1 extra Sanity at Tick.    │
│                                              │
│ Defeat reward: 1 Sanity to each attacker.    │
│ Flee: move 1 tile away, paying 1 Sanity.     │
│ The Stalker stays — and festers at Dawn.     │
└──────────────────────────────────────────────┘
```

#### Sample Visitor card (3- and 4-player games)

```
┌──────────────────────────────────────────────┐
│ COCO ARRIVES                                 │
│ ─────────────────────────────                │
│ Trigger: Drawn at Dawn of Day 3.             │
│ Place Coco's standee at Ellie & Luca's       │
│ House.                                       │
│                                              │
│ Immediate: Heal one Down ally to 1 Health,   │
│ regardless of distance.                      │
│                                              │
│ Then: Coco departs at the next Dawn.         │
└──────────────────────────────────────────────┘
```

These five samples set the visual and mechanical template for the rest of each deck. Designers writing more cards should follow the same shape: headline, type, costs, immediate effect, ongoing/special, and (for severity-graded cards) the dot rating.

---

## 10. Stats and Player Boards

Each character has a personal player board with three sliders/tracks. The standard stat ranges are:

| Stat | Default Range | Restored By | Lost By |
|---|---|---|---|
| **Health** | 0–10 (varies by character) | Cooking, Bandages, Resting at home | Combat, starvation, cold, hazards |
| **Hunger** | 0–10 (varies) | Eating raw or cooked food | Daily Tick; movement; fighting |
| **Sanity** | 0–12 (varies) | Sleeping at home, Comfort items, Coco's perk, Luca's storytelling | Darkness, monsters, weird food, isolation |

### 10.1 Threshold effects

When any stat is below 25%, **Bad Things Happen**:

- **Low Health (<3):** Movement costs +1 action.
- **Low Hunger (<3):** Cannot fight. Cannot use any action card with the [Effort] tag. (Flee is still legal — §12.4. A starving character can always run.)
- **Low Sanity (<3):** **Haunted.** At each Dawn, draw 1 Threat card at your location. It is real to you: only *you* may fight or flee it — allies cannot help with what they cannot see. Discard it once resolved (defeated or fled); it never festers on the Doom track, because it was never really there. (An earlier draft had a hidden-information hallucination rule — "only the affected player knows it's not real" — cut for being unrunnable at a physical table and unimplementable with the public-information model of §18.9. Haunted keeps the isolation horror with zero hidden state.)

When a stat hits 0:

- **Health 0:** The character is **Down**. Flip the standee to its ghost side. (See §16.4.)
- **Hunger 0:** Lose 1 Health each Tick until fed.
- **Sanity 0:** The character is **Lost**. Flip ghost side. (Also a Down state.)

### 10.2 The player board

Each board is laid out so it can be read without reference to the rulebook (§18.10). Standard zones:

- **Top strip:** the character's name + portrait, plus a one-line "what you do" tagline ("Rayman — fights, moves fast, eats a lot").
- **Three stat tracks** down the left: ❤ Health, 🍴 Hunger, 🧠 Sanity, each with its full range printed and the threshold zones (<3 = Bad Things) shaded.
- **Perks panel:** each perk shown as a labeled icon block with one short sentence each. No flavor text — just the rule.
- **Constraint panel:** distinct visual treatment (red border) and a 1-line reminder of what the constraint costs.
- **Action Bar** along the bottom: 7 labeled action-icon buttons (§18.13).
- **Action Cubes** (3): physical track next to the bar, animated as cubes are spent.
- **Starting-hand legend** in the corner: the 5 cards the character begins with, printed small as a reference if the player wants to recall their starter.

The visual goal: any player at the table can glance at any other player's board and instantly see who they are, what their stats are, and what they can do this turn. No memorization required.

---

## 11. Turn Structure

Detailed breakdown of a single round (one in-game day). In TTS, every step listed below is **prompted automatically by the Phase Banner** (§18.11) — the round walks itself, and a player who has never played can follow the on-screen prompts through all five phases. The design below is the rules for the table; the UX in §18.10–18.18 is how those rules become legible.

### 11.1 Phase 1 — Dawn (2–4 minutes)

1. **Advance Day Counter.** Move the day token forward one step.
2. **Doom check.** Doom advances by the current phase rate (see the §15.6 player-count table), **plus festering** (§15.1): +1 for every Threat card still on the map (capped at +3), and +2 for every Boss (+1 for the Treeguard), uncapped.
3. **Moonlit Salvage.** Any character who spent the night at a sport court and is not Down gathers 2 resources from that court's bag (§7.4).
4. **Reveal Dawn Card.** Draw the top card of the current Phase deck and read it aloud. Resolve all immediate effects.
5. **Note ongoing effects.** Place the Dawn card face-up if it has lingering rules; remove it at the next Dawn unless its text says otherwise.

### 11.2 Phase 2 — Day (15–25 minutes)

Players take turns clockwise from the **First Player marker**. Each player has 3 actions to spend on:

- **Move (1 action)** — Travel to an adjacent location. Costs 1 Hunger. Rayman moves 2 spaces.
- **Gather (1 action)** — Draw 1 resource token from the current location's bag.
- **Craft (1 action)** — Spend resources to claim an Item card from the Market.
- **Cook (1 action)** — At a Crockpot location, prepare a Recipe.
- **Fight (1 action)** — Engage an enemy at the current location (see §12).
- **Rest (1 action)** — Recover 1 Hunger or 2 Sanity (player's choice). At your own house: also +1 Health.
- **Trade (free)** — Trade resources/cards with co-located players. No action cost.
- **Special (varies)** — Character-specific or location-specific actions (e.g., James's "Pattern Recognition," Rayman's "Defend").

Once every player has spent or passed all 3 actions, Day ends.

**Rotation variant (optional, chosen at setup).** Instead of spending all 3 actions in one sitting, each player spends **exactly 1 action per visit**, and priority cycles around the table until everyone's actions are gone. Passing *after* acting banks your remaining actions for your next visit; passing *without* acting forfeits them (so the day always ends). Free actions (Trade, character specials) are unaffected. Why it exists: with full turns at 5 players, a player can wait through 12 consecutive foreign actions between decisions — the Rotation variant caps that wait at 4, at the cost of chopping up each player's 3-action plan. Both modes are implemented in the TTS build (a setup toggle); which one *feels* better is an open playtest question (§20.2) — the design's default is full turns, because the §18.10 onboarding principle favors one coherent turn over four fragmented ones for a first game.

### 11.3 Phase 3 — Dusk (2–3 minutes)

Dusk is the round's last decision, and it is a real one:

1. **Scramble (optional).** Each character may make **one 1-tile move, paying 1 Hunger**. No action cost — all actions are spent by now. This is the last chance to reach a safer tile, join an ally, or deliberately stay out at a court for the Moonlit Salvage gamble (§7.4).
2. **Declare.** Each player declares publicly where they sleep. You sleep where you stand — the declaration is the table-talk moment where the group argues geometry: who pairs with whom, who takes the floor (§11.4), who risks the court.

The Hunger cost matters: a scramble is cheap insurance early in the week and a real price late, when Hunger is scarce. Groups that plan their Day-phase movement well rarely need to scramble; groups that didn't pay for it.

### 11.4 Phase 4 — Night (5–10 minutes)

For each location with players in it (in order from least populated to most):

1. **Threat draw.** Draw a number of Threat cards equal to the location's threat rate (0 for safe house tiles, 1 for sport courts, +1 if anyone "called attention" with a noisy action).
2. **Resolve threats.** Combat rolls happen as needed. Players may use items.
3. **Charlie check.** Any player whose location has no light source (no Flashlight, no Fire, no Battery-powered item) suffers a "Charlie attack" — **2 Sanity and 1 Health**. For each consecutive night a character spends in darkness, Charlie grows bolder: **+1 Sanity and +1 Health more than the night before**. A night with light resets her interest. (DST night-darkness translation; see [DontStarveVideoGamePrinciples.md §4](Archive/DontStarveVideoGamePrinciples.md). Deterministic on purpose: a first slip is survivable and legible — *the world's rules*, not a die spike — but darkness as a habit is lethal.)
4. **Storytelling at the campfire.** Players together at a house location may use Comfort/Music/Photo items for collective Sanity gain.
5. **Sleep.** Each character regenerates per the table below. Coco's, Luca's, and Ellie's location perks resolve in addition.

   **Crowded floor.** A house sleeps **two** comfortably. If more than two characters sleep at the same house, each character beyond the second gets the floor and regenerates **nothing** that night. Beds go to the house's owners first, then to whichever guests the table agrees need them most. (This is the anti-stacking pressure: the Crockpot pulls the team together by day; the beds push them apart by night. The nightly "who sleeps where" argument is the point.)

   | Sleeping at... | Regenerates |
   |---|---|
   | Your own house (in a bed) | +1 Sanity, +1 Hunger, +1 Health |
   | Someone else's house, in a bed, with at least one other character present | +1 Sanity |
   | Any house, on the floor (third sleeper onward) | nothing |
   | Someone else's house, alone | nothing |
   | A sport court (Basketball or Badminton), any company | nothing — but survivors salvage 2 resources at Dawn (§7.4) |
   | A sport court, alone | nothing AND draw 1 extra Threat card — but the same Dawn salvage applies |

### 11.5 Phase 5 — Tick (1 minute)

1. Every character loses 1 Hunger and 1 Sanity (modified per character).
2. Coco's, Luca's, and Ellie's location perks resolve.
3. Pass the First Player marker clockwise.
4. Check victory/defeat conditions.

If the round was Day 7 and the team is still alive, they win. Otherwise, return to Phase 1.

### 11.6 Worked example: Day 3 in a four-player game

To make the loop concrete, here is a narrated single round. Players: James, Coco, Rayman, Ellie. Phase 2 is active. Doom marker at 8.

**Dawn.**
Day Counter advances to 3. Doom advances by 1 (now 9 — still under the 10 threshold).
The team flips the top card of the **Strange Days** deck: *"The Porch Light Flickers"* (sample card §9.6). All four lose 1 Sanity. The card stays face-up — Flashlights are useless tonight.

**Day Phase.** Turn order: Ellie → Rayman → James → Coco.

- **Ellie** is at her own kitchen. She spends 1 action on **Cook (Hot Stew)** — pays 2 Food + 1 Wood, restores +4 Hunger and +2 Sanity to Rayman (who's standing next to her). Her Comfort Food perk adds +1 Hunger and +1 Sanity to Rayman on top. Action 2: **Gather** (Cooking Ingredients). Action 3: **Trade** (free, doesn't count) — hands Coco a spare Battery, then **Rest** for +2 Sanity, accepting the homey +1 Sanity bonus from her location.
- **Rayman** uses his +1 movement perk: **Move** James's House → Ellie's House → Basketball Court (2 actions, 2 Hunger lost — partially offset by the stew he just ate). Action 3: **Gather** Wood at the Court. He rolls the Echoes d6 → 6, draws a bonus Item card (a Toy Bow, persistent +1 attack die from range).
- **James** spends his **Pattern Recognition** ability (free) to peek at the top of the Threat deck. He sees a Shadow Stalker on top. Action 1: **Craft Flashlight** at the Market (irrelevant tonight — but useful tomorrow). Action 2: **Move** to Ellie's House. Action 3: **Rest** for +1 Hunger. He must consume an Energy Drink before night or take −2 Sanity (his Wired constraint); he plans to drink at end of round.
- **Coco** is at Ellie's House. Action 1: **Trade** — gives a Comfort Blanket to James. Action 2: **Move** to the Badminton Court to scout. Action 3: **Gather** Cloth.

**Dusk.** Scramble window: Coco *could* pay 1 Hunger to fall back to Ellie & Luca's House — but Ellie and James already have the two beds there, so she'd take the floor and regenerate nothing anyway. The team talks it over and Coco stays at the Badminton Court on purpose: eat the risk, collect the Moonlit Salvage at Dawn. Declarations: Ellie at her House, James at Ellie's House (with her), Rayman at Basketball Court (alone), Coco at Badminton Court (alone — her No Home constraint will bite).

**Night.**
Resolution order: Coco → Rayman → Ellie & James (most populated last).

- **Coco at Badminton Court (alone).** Threat draw rate 2 (+1 because the Court is high-threat). She draws *Shadow Stalker* (the one James saw) and *The Wind in the Net* (atmospheric, −1 Sanity). The Stalker attacks: 2 dice → one 5 = 1 damage. Coco at 5 Health. She has no Flashlight; the Dawn card disabled them anyway. **Charlie attack:** first night in darkness → −2 Sanity, −1 Health. Her No Home penalty: −3 Sanity for ending the night alone in a non-house tile. Coco ends the night at 4 Health, 5 Sanity — battered, frightened, standing. Every point she lost traces to a decision the table made at Dusk, and tomorrow the Stalker is still on her tile.
- **Rayman at Basketball Court (alone).** Threat draw rate 2, +1 because Rayman moved today (Loud — the noise followed him home). Draws *Echoes* (already in play), *The Hollow Spectator* (HP 3), and a soft atmospheric threat that resolves instantly. He fights the Spectator — 2 attack dice + 1 Court Master + 1 Toy Bow = 4 dice. Roll: 5,6,4,1. Two hits; the stray 1 doesn't matter (fumbles only bite on a complete whiff). Spectator at 1 HP. Spectator returns: 1 die, 5 = 1 hit. Rayman at 11. He has a Flashlight and a Battery: **no Charlie attack**, even with the Dawn card, because his Battery is paired with a *Lantern* (Fire-equivalent — he crafted it on Day 2; the Dawn card disables Flashlights only).
- **Ellie & James at Ellie's House.** Threat draw rate 0 (safe). Two sleepers, two beds — no one on the floor. They play Comfort items (James equips the Comfort Blanket Coco gave him — +1 Sanity). Sleep: Ellie at her own house → +1 Sanity, +1 Hunger, +1 Health. James at someone else's house with company → +1 Sanity. James drinks his Energy Drink (+2 Sanity, addiction satisfied).

**Tick.** Everyone loses 1 Hunger and 1 Sanity. Rayman loses 2 Hunger (Big Appetite).

**Outcome.** At the next Dawn the bill and the payoff both arrive: the wounded Spectator and the Shadow Stalker are still on the map, so Doom festers **+2** on top of the phase rate — the table now has a concrete reason to spend actions finishing fights. In exchange, Rayman and Coco each salvage **2 resources** from their courts. Coco is hurt but alive and needs an escort home; nobody is Down, but two threats are loose and the Doom track is visibly angrier.

This is the rhythm of the game: a round is rarely catastrophic and rarely free. Survival is paid for in scattered small currencies all spent on the same night — and every mess left standing overnight is charged interest at Dawn.

---

## 12. Combat

Combat is **fast and dice-based** ([InterestingGames.md §3.3.6](Archive/InterestingGames.md)). It has to be — combat happens often.

### 12.1 The roll

When a character fights an enemy:
- **Attacker rolls** dice equal to their **base attack value** (typically 1 die, +1 per equipped weapon, ±character/location modifiers).
- Each die showing **5 or 6** = 1 hit. Each hit does 1 damage to the enemy.
- **Fumble:** if the roll contains a **1** *and no hits at all*, take 1 Health damage (maximum 1 per roll, no matter how many 1s). A roll with any hit never fumbles — you connected; the stray swing doesn't matter. This keeps big dice pools from punishing the dedicated fighter: whiffing completely is what hurts, not rolling lots of dice.
- The enemy then attacks back: roll its **attack die count** (printed on the threat card). Each 5 or 6 = 1 damage to the attacker. (Defenders may use shield/cover items to negate hits.)

### 12.2 Group combat

If multiple characters are at the same location, they may fight cooperatively. They sum their attack dice, but each character takes return damage based on a shared pool divided by the GM-equivalent rule (highest-Health takes the first, then rotate).

Rayman's Defend action redirects all return damage to him for one round.

### 12.3 Death and Unconsciousness

If Health hits 0, the character is **Down** (see §16.4). Other characters at the same location may spend their next action to **Stabilize** (returning the character to 1 Health), but only if they have a Bandage item. Otherwise the character must wait for revival or stay Down.

### 12.4 Flee

Fighting is never compulsory. When a threat is at your location, you may **Flee** instead: move 1 tile away, paying **1 Sanity** (running in the dark is terrifying, not tiring). Three properties are deliberate:

- **Always legal.** Flee is available even at Hunger < 3, when Fight is blocked (§10.1), and at Night when actions are spent. A starving, cornered character always has a legal move — there is no rules deadlock, only a bad night.
- **Paid in Sanity.** Mismatched currency (§8.4): escaping the fight you couldn't win drains the stat that makes you hallucinate. A character who keeps running eventually breaks.
- **The threat stays.** A fled threat remains where it was — and festers at Dawn (§15.1). Fleeing converts a Health problem into a Doom problem; it is a loan, not an escape.

### 12.5 Press the Attack

After your attack roll lands **at least one hit** (and the threat survives), you may **pay 1 Sanity to roll one bonus attack die** — and the enemy does not strike back until you stop. On a **5–6** the press deals 1 more damage and you may pay and press again; on a **1–4** the streak ends and the enemy counter-attacks. Press dice **never fumble** (a stray 1 just ends the streak — no double jeopardy on a die you paid for). In group combat, each fighter may press in turn, paying their own Sanity.

Three properties are deliberate:

- **Pure push-your-luck.** One sentence of rules; the whole table watches every press ("stop while you're ahead!"). It is the highest tension-per-rule mechanic in the game.
- **Bloodlust costs your mind.** Mismatched currency again (§8.4) — and perfectly thematic: pressing the attack in the dark is how sanity goes. A press **may drop you to 0 Sanity and put you Down mid-fight** — a visible, chosen risk, gated by an explicit confirm in the TTS build (§18.14), never an accident.
- **It is the burst tool for the mandatory Source (§16.1).** The team spending its collective mind to end the final boss in one desperate flurry is the intended climax play. Sanity-as-ammunition against the thing eating your minds is the game's thesis in one mechanic. (Simulation-verified: unfought-Source losses fell from 33% to 8% of games for co-located teams once pressing existed.)

### 12.6 The Source's phases

The final boss is more than a statblock (HP 8, Atk 3 — retuned from 10 in the batch-4 calibration pass, §20.1's sanctioned knob): it has **one scripted beat**. The **first time the Source drops to 5 HP or below, it splits** — two **Terror Beaks** peel off to tiles adjacent to it. The Beaks are ordinary threats (they fight, flee, and fester normally, +1 each at Dawn under the cap); the Source keeps its remaining HP. Now the team must burst the boss down *and* handle adds mid-fight — the moment Press the Attack (§12.5) was built for.

Three properties are deliberate:

- **A boss with a beat is a story; a big HP pool is a chore.** This is the one place the "emergence over scripting" pillar (§2) deliberately bends — the climax earns one scripted card.
- **Deterministic and announced (§1.4).** The split threshold is public from the moment the Source arrives (the Rules panel shows its live HP and the coming split). The drama is in the situation, not a die spike.
- **The engine tracks boss HP.** From the Source's arrival, its HP is script-tracked (`gameState.bossHP`) — mid-fight, across actions, across saves. No honor-system counting on the final boss; a save mid-fight restores the real number.

A second beat at HP ≤ 2 was considered and deferred: one clean phase change reads as a climax; two risks a fiddly boss.

---

## 13. Crafting and Cooking

### 13.1 Crafting (the Market)

To craft, a player at any location spends an action and the listed resources to claim an Item card from the **5-card Market**. The card goes into the player's hand. A new card is drawn from the Market deck to refill the slot.

Crafting is the central engine of player power. Smart crafting choices accumulate; bad crafting wastes resources. The Market refresh ensures variety: the same items are not always available.

### 13.2 Cooking (the Crockpot)

Cooking is a separate sub-system available only at locations with a Crockpot (Ellie & Luca's House by default; players may craft a Portable Crockpot Item to enable it elsewhere).

To cook:
1. Choose a Recipe card.
2. Discard the listed ingredient resources.
3. Resolve the Recipe's effect — typically distributing Hunger and Sanity restoration to all characters at the location.

Cooking is **multiplicative** (one player cooks, many benefit), making the Crockpot location a **social magnet**. Compare to Catan trading: forcing players to gather for cooking creates the table-talk window where plans get made.

### 13.3 Improvised weapons

Some Sports Equipment items at Rayman's House count as weapons without being crafted: Basketball (1 attack die, single-use breakage on natural 1), Tennis Racket, Hockey Stick.

### 13.4 The Telltale Heart (special recipe)

Telltale Hearts are not Market items and are not part of any starting hand. They are a **Recipe** (printed on a permanent reference card) that can be cooked at any Crockpot location. The component pool of 5 tokens listed in §5 is the **maximum number of Telltale Hearts that can exist at any time** — when one is consumed (used for revival), the token returns to the supply.

Recipe — **Telltale Heart**:
- Cook at: Crockpot.
- Ingredients: 1 Cloth + 1 Battery + 1 Food.
- Cost: the cook pays 2 Health from their own track (the heart is *literally* part of them — the DST sacrifice mechanic, [DontStarveVideoGamePrinciples.md §7](Archive/DontStarveVideoGamePrinciples.md)).
- Yield: 1 Telltale Heart token, placed at the cook's location.

Telltale Hearts are the only way to revive a Down character (see §16.4). Carrying them is a strategic choice: they fill a tight inventory slot but they are the team's life insurance.

### 13.5 Pry and Sealed Things

**Pry** is a **free action**: a character holding a **Crowbar, Lockpick, or Pry Bar** may open a sealed thing at their tile and take its printed reward — guaranteed, no roll. Sealed things come in two forms:

- **Sealed Threat cards** (§9.4): drawn like any threat, but they don't fight — they wait. Each is a payoff for the team that invested in a tool.
- **The Sealed Basement** — a fixed object placed under Ellie & Luca's House **at setup, visible from turn one**. Behind it: a free Market Item plus a resource cache (2 Food + 1 Wood + 1 Battery). Because it is placed, not drawn, every game has it — the map's reliable early destination ("we need to get into the basement"), which makes crafting a Pry tool early a genuine plan instead of a rounding error. It is tuned to be worth a detour, never mandatory: a team can win ignoring it.

A guaranteed reward behind a tool gate is the cleanest excitement in the game: no randomness, a clear goal, a reason to specialise (clever desperation), and a shared objective the table organises around (storied collaboration). In the TTS build the verb is coded (`doPry`); the Pry button lights only when a sealed thing is co-located and the player holds a tool.

---

## 14. The Week Arc and Pacing

Seven in-game days, divided into four narrative phases. This is the DST season structure ported to a tighter session length ([DontStarveVideoGamePrinciples.md §3](Archive/DontStarveVideoGamePrinciples.md)), explicitly mapped to the **Jo-Ha-Kyu** dramatic arc ([PrinciplesOfGoodBoardGames.md §7](Archive/PrinciplesOfGoodBoardGames.md)).

| Phase | Days | Jo-Ha-Kyu beat | Tone | Doom/Day | Phase Boss |
|---|---|---|---|---|---|
| 1 — Dusk of the Week | 1–2 | **Jo** (slow open) | Calm, exploratory. Resources are findable. Players learn the map. | +1 | None |
| 2 — Strange Days | 3–4 | **Ha** (break) | Pressure rises. Threats appear regularly. | +1 | The Deerclops (mid-tier; Day 4) |
| 2.5 — The Grove Wakes | Dusk of Day 4 | **Ha** (aftershock) | Interlude mini-boss. The map itself pushes back. | — | The Treeguard (mini-boss; scheduled, not deck-drawn — §14.2) |
| 3 — Long Nights | 5 | **Ha → Kyu** (pivot) | Boss night. Major disruption. | +1 | The Eye of Terror (heavy boss) |
| 4 — Final Hours | 6–7 | **Kyu** (rapid climax) | Survival sprint. Doom races — mostly from what festers. Day 7 opens on the fixed **Last Dawn** (§15.7). | +2 | The Source (final boss; MUST be destroyed by end of Day 7 — §16.1; splits at 5 HP — §12.6) |

The pacing math is deliberate: roughly half the campaign is *Jo*-style exploration where players learn and plan, but the second half compresses sharply. This produces the felt arc players describe as "having a story," not just "having a session." Mid-game compression is the cure for the runaway-leader and dead-turn problems ([PrinciplesOfGoodBoardGames.md §10](Archive/PrinciplesOfGoodBoardGames.md)) — late-game decisions matter more than early ones, so a perfect early game cannot win the game alone.

### 14.1 Phase boss arrivals

Each phase boss is a Threat-card-style enemy that appears on a specific Dawn card during its phase. Bosses:

- **Pre-warn.** A Dawn card the day before announces them.
- **Disrupt rules.** While present, change the game state ("All Sanity costs are doubled while The Deerclops is on the map").
- **Reward when defeated.** A boss kill must feel like it *rescued the week*, not merely stopped a penalty (an earlier draft rewarded only a passive Trophy, and simulation showed boss-avoidance dominating — the reward side has to be loud). On defeat:
  - **Doom rolls back**: Deerclops **−2**, Eye of Terror **−3**. (The Source ends the game; no rebate needed.) The one moment all week the public track lurches the *right* way — let the table cheer.
  - **Spoils**: 3 resources shower onto the boss's tile.
  - **The Trophy** — a unique **build-around**, not a stat bump: the Antler Sled (Deerclops) lets a Move carry a co-located ally; the Watching Jar (Eye) lets the team preview and reorder the top 2 Threat cards each Dusk. A Trophy is a new verb the team plays with, and the retold loot of the campaign.
  - **Spectacle** (TTS build): the boss's roar loop cuts mid-roar, the lighting flashes, and a boss-specific kill line lands in chat — a kill is an event, not a log entry.

Bosses are placed on a specific location determined by the Dawn card. The team must travel to or defend against them.

### 14.2 The Treeguard (Phase 2.5 mini-boss)

Between the Deerclops and the Eye of Terror sits a smaller, stranger fight. At **Dusk of Day 4** — always, scheduled by the clock rather than drawn from a deck — a **Treeguard** unfolds itself at a random sport court. The neighborhood has been feeding on the courts all week: broken bleachers for Wood, hoops for Metal, nets for Cloth. On Day 4, the timber notices.

- **Stats:** HP 5, Attack 2 — tougher than any night threat, softer than a phase boss.
- **While it stands:** no one may **Gather at its court** (it guards the timber), and as a boss on the map it **festers Doom +1 at each Dawn** (§15.1).
- **Two outs, DST-style:**
  - **Fight it.** Standard combat (§12). Defeat: +1 Sanity to each attacker, and salvage **3 Wood** from where it stood.
  - **Appease it.** At its tile, spend an action and **2 Wood** to plant saplings. It watches, then folds back into stillness. No reward — but no wounds, and no more festering.
- **No Trophy.** It is a mini-boss; it does not count toward the Hero Run (§16.2).

Design intent, in order: (1) it is the mid-week **anti-turtling alarm** — a team camped at Ellie & Luca's kitchen must now march out to a court or eat +1 Doom per day; (2) the appeasement option is a pure **mismatched-currency** decision (pay the resource you were harvesting to keep harvesting it) and reads as instantly thematic to anyone who has played DST; (3) it is **scheduled, not deck-drawn**, so every campaign gets its Phase 2.5 beat — the shuffled Phase decks make the named bosses' arrival days wobble, and the Treeguard anchors the middle of the arc regardless.

While the Treeguard is awake, its roar library (26 sounds under `sounds/creatures/treeguard/`) loops in place of the ambient track.

---

## 15. The Doom Track and Scheduled Threats

The Doom track is the main visible loss timer, lifted directly from Cthulhu Wars ([InterestingGames.md §3.3.5](Archive/InterestingGames.md)) but inverted (it ticks against the players, like HPHB's location track).

### 15.1 The track

A 30-step linear track on the main board. The Doom marker advances each Dawn by the **phase rate** (4-player baseline; see §15.6 for the player-count table):

- Phase 1: +1 per day.
- Phase 2: +1 per day.
- Phase 3: +1 per day.
- Phase 4: +2 per day.

The fixed clock is deliberately gentle, because most of the Doom pressure is **responsive** (below): festering threats, festering bosses, and fallen friends. The world doesn't punish you for time passing nearly as much as it punishes you for what you leave undone. (Bosses also add **no Doom on arrival** — an earlier draft charged +1/+2/+3 as each boss appeared, which double-billed the fight on top of uncapped boss festering. A boss charges the track by *staying*, not by showing up.)

On top of the phase rate, Doom is **responsive to the state the players leave the world in**:

- **Festering threats.** At each Dawn, Doom advances **+1 for every ordinary Threat card still on the map**, capped at +3 per Dawn (a bad night can't cascade into an instant loss). A threat fled from, ignored, or left at 1 HP is not a saved action — it is a loan against the Doom track. This is what makes Fight, Cleanse, and finishing fights genuinely competitive with self-care actions.
- **Festering bosses.** Bosses are **exempt from the cap**: each phase boss on the map festers **+2 per Dawn** (the Treeguard mini-boss +1, §14.2). The cap exists so chaff can't snowball; bosses are not chaff. A team that decides to wait out the Deerclops is choosing to pay +2 Doom every single morning it stands — ignoring THE monster is never the cheap line. (Simulation showed that under a shared +3 cap, a boss-avoidance strategy comfortably out-performed engaging them; uncapped boss festering is what makes the boss fights economically real.)
- **Fallen friends.** Whenever a character goes Down, **Doom +1** immediately (§16.4). The dark feeds on collapse.

The clock is therefore partly in the players' hands: a clean map and a standing team hold Doom near the phase rate; a sloppy week compounds. If the marker reaches **30 before the team survives Day 7**, the team loses. Players can also push Doom back through specific "Cleanse" actions (see §15.3) — which the responsive sources make an actually-rational spend, not a theoretical one.

### 15.2 Doom thresholds (passive escalation)

The Doom track has annotated thresholds that change ongoing rules:

- **At 10:** The night phase threat draw is +1.
- **At 15:** **Scarcity** — every Market craft costs **+1 extra resource** of any type the crafter holds (their choice). (Replaced an earlier "refill 1 Market slot per day" rule, which reduced options without adding tension. Scarcity pressures instead of bores: players still see the full rotating market — they just can't quite afford it.)
- **At 20:** All characters lose +1 Sanity at the night Tick.
- **At 25:** Boss-level threats can appear in any phase — and **Nothing Left to Lose**: every character gains **+1 attack die** in all combat, and **Rest also restores +1 Health anywhere** (non-stacking with the at-home bonus). Every other threshold is a punishment; 25 is the moment the team *stops being afraid*. Doom 25 with the shared clock at 25/30 is already near-death — the buff is textbook negative feedback (catch-up that arrives as the *third act*), turning the most-dreaded number on the board into one desperate teams play toward. It cannot snowball: it only triggers when the co-op clock is nearly spent, and it helps everyone symmetrically.
- **At 30:** Game over.

### 15.3 Pushing back Doom

Players can spend an action and a specific resource bundle (typically: 1 of each: Wood, Cloth, Battery, Energy Drink — i.e., representative of community ritual) to do a **Cleansing**, reducing Doom by 2. This is rare, expensive, and a key strategic decision: do you spend this action on yourself, or on the world?

The other way to push Doom back is **violence**: phase-boss kills rebate the track directly (Deerclops −2, Eye −3 — §14.1). Cleansing is the quiet communal answer; the boss fight is the loud one. Both exist so the "spend on the world" decision has a fighter's path and a homebody's path.

### 15.4 Charlie attacks

Echoing DST's Charlie ([DontStarveVideoGamePrinciples.md §4](Archive/DontStarveVideoGamePrinciples.md)): any character at night without a light source suffers a Charlie attack — **2 Sanity + 1 Health**, escalating by **+1 to each for every consecutive night that character spends in darkness**. A night with light resets the escalation. Coco is immune. Some boss-phase rules disable certain light sources.

Deterministic by design (§1.4 "clever desperation"): losses must read as a chain of visible mistakes, not a die spike. One dark night is a survivable, legible lesson; making a habit of darkness is what kills. The escalation also makes light logistics a *week-long* plan rather than a nightly coin-flip.

### 15.5 Severity scaffolding (the dot system)

Borrowed from Catan's probability dots ([InterestingGames.md §2.3.2](Archive/InterestingGames.md)): Dawn cards and Threat cards print a **severity rating** as 1–5 dots in the top corner. The dots are not used in any rule — they are pure information design.

- ●○○○○ — atmospheric flavor only.
- ●●○○○ — minor stat hit (1 of one stat).
- ●●●○○ — combat-grade or lasting effect.
- ●●●●○ — phase-shift event (changes ongoing rules).
- ●●●●● — boss arrival or apocalyptic Dawn.

This solves the new-player problem: a new player can see a 5-dot Dawn card and instinctively brace, even before reading the text. Experienced players use the dots to plan inventory and movement. The same component teaches at two skill levels — Catan's probability-dots pattern, ported to a horror co-op.

### 15.6 Doom rate scaling by player count

The doom-per-day rate is balanced for the 4-player baseline. Player counts adjust the rate:

| Players | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|
| 3 | +1 | +1 | +1 | +1 |
| 4 (default) | +1 | +1 | +1 | +2 |
| 5 | +1 | +1 | +2 | +2 |

Rationale: more bodies at the table means more occupied tiles at night, more threat draws, and therefore more *responsive* Doom (festering) — so the fixed clock ticks slightly faster at higher counts to a lesser degree than it used to, not more. (Retuned 2026-07: the original table — 3p up to +2, 4p up to +3, 5p up to +3 — was calibrated before uncapped boss festering and the mandatory Source. Simulation showed it made 5-player games nearly unwinnable, with ~90% of losses to Doom, while the responsive sources now carry the late-game pressure the old flat rates were simulating. The Monte Carlo probe in `scripts/simulate_balance.py` validates the ordering; the exact 40–50% human win-rate target in §20.2 still needs playtests — the probe's combat model is too crude to certify it.)

### 15.7 The Last Dawn

Day 7's Dawn is **fixed**, not drawn: *"THE LAST DAWN — the sky is trying to lighten. Survive until it's over."* No penalty, no effect — pure tone, the first Dawn all week that isn't a threat. It is scheduled by the clock and bypasses the Phase 4 deck entirely (the same pattern as the Treeguard, §14.2 — the deck only ever has to cover Day 6). Predictable structure, unpredictable details — the DST seasons principle the Phase decks already follow, applied to the finish so every campaign lands on the same held breath. A physical `P4_LAST_DAWN` card for the print edition is deferred; the TTS build scripts it.

### 15.8 Night Sounds and the dread of information

Two batch-3 effects sharpen dread through *information design* alone — telegraphed unknowns, never new randomness (the legible-losses contract, §1.4, is untouched):

- **Night Sounds.** At Dusk, if the top card of the Threat deck is a **Hard** threat, a distant growl plays across the table. No rule text, no mechanical tell, deliberately unexplained — veterans learn to brace when they hear it; new players just feel the hair go up. It reveals nothing gameable (not *which* threat, not *where*) and adds zero randomness: it merely *voices* a draw that was already going to happen. The knowledge that something is coming, without knowing what, is the core of horror. Discipline: only on Hard, only at Dusk, once, at low volume — the silence between growls is what makes the growl land.
- **The Wrongness** (§9.4) applies the same principle to a physical object: a known-but-unresolved threat on the map converts a random Night draw into a *decision with anticipation* — the who-goes-to-look argument is the story.

---

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

This is the DST soft permadeath ([DontStarveVideoGamePrinciples.md §7](Archive/DontStarveVideoGamePrinciples.md)) — death is meaningful but not eliminating.

### 16.5 The Week in Review

When the game ends — victory or defeat — the table gets the week read back to it: one headline per day ("Day 3 — the night Coco slept alone"), the darkest night, the best kill, who kept everyone fed, the longest run of dark nights survived, the Doom high-water mark, and the fallen and the saved. In the TTS build this is generated automatically from the game's own event log (nothing new is tracked at the table); in a print edition it is a one-minute ritual of flipping back through the week aloud.

Why it's a rule and not a nicety: **storied collaboration (§1.4 #3) is a stated aesthetic, and the retelling is the actual replayability engine** ([PrinciplesOfGoodBoardGames.md §15](Archive/PrinciplesOfGoodBoardGames.md)). The Week in Review hands the table a script to retell from — the week becomes a story with a shape, which is exactly what makes "one more game" happen.

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

A **Scenario** is a single week-long modifier revealed at setup — the DST seasons idea compressed into one card: the same neighborhood, but this week the *world* is different. Scenarios are the game's coarse replayability lever on top of the fine-grained ones (map layouts §7.6, character composition §6.6): variability as a multiplier on an already-working game, never a substitute for depth ([PrinciplesOfGoodBoardGames.md §15](Archive/PrinciplesOfGoodBoardGames.md)).

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

## 18. Tabletop Simulator Implementation

Sanity-checked against [HowToCreateGamesInTabletopSimulator.md](Archive/HowToCreateGamesInTabletopSimulator.md). Every component below maps to a documented TTS object type.

### 18.1 Component-to-TTS mapping

| Component | TTS object type | Reference §  |
|---|---|---|
| Main Board | `Custom_Board`, locked | TTS §5.3 |
| Location Tiles | `Custom_Tile` (rounded square) | TTS §5.3 |
| Path-edges between locations | Decorative `Custom_Tile` (small) — purely visual | TTS §5.3 |
| Character Player Boards | `Custom_Tile` (rectangle) | TTS §5.3 |
| Character Standees | `Figurine_Custom` | TTS §5.3 |
| Stat markers (H/H/S) | `Custom_Token` (small) | TTS §5.3 |
| Day Counter | `Counter` widget | TTS §4.2 |
| Doom Marker | `Custom_Token` along a snap-point track on the Main Board | TTS §5.6 |
| Phase Decks (4) | `DeckCustom`, one per phase | TTS §5.1 |
| Market Deck | `DeckCustom` | TTS §5.1 |
| Threat Deck | `DeckCustom` | TTS §5.1 |
| Visitor Deck | `DeckCustom` | TTS §5.1 |
| Recipe Cards | Loose `Card`s (face-up reference) | TTS §5.1 |
| Resource Tokens | `Infinite_Bag` per resource, plus `Custom_Token` instances | TTS §5.5 |
| Combat Dice (d6) | `Die_6` (built-in) | TTS §5.4 |
| Sanity d8 | `Custom_Dice` (8 faces) | TTS §5.4 |
| Boss Standees | `Figurine_Custom`, larger scale than character standees | TTS §5.3 |
| Trophy Cards | Loose `Card`s | TTS §5.1 |
| Telltale Heart Tokens | `Custom_Token` | TTS §5.3 |
| Hand Zones (1 per player) | `HandTrigger`, one per `Player.Color` | TTS §5.6 |
| Crockpot at Ellie & Luca's | `Custom_Model`, locked, decorative | TTS §5.2 |

### 18.2 Snap point structure

- Main Board has snap points for: 5 Location Tiles, the Day Counter, the Doom Marker (along a 31-step linear track), Market display (5 card slots), Threat-deck slot, Phase-deck slot, Visitor-deck slot, Trophy display (4 slots).
- Each Location Tile has snap points for: 4 character standees stacked vertically (so multiple characters in the same location remain visible), 1 boss standee slot, a "threat in play" slot.
- Each Player Board has snap points for the 3 stat markers along their tracks, plus 3 action cubes.

### 18.3 Lua scripting plan

The game does **not** require Lua to be playable — players can run rules manually. However, scripting reduces friction. Recommended scripted features:

| Feature | Implementation | TTS reference |
|---|---|---|
| **Setup button** | Global `Setup()` function: shuffles decks, deals starting hands, places standees on home locations, sets stat markers. | TTS §8.1 |
| **Day-advance button** | Global `AdvanceDay()` function: increments Day Counter, advances Doom by phase rate, draws and announces a Dawn card, applies Tick. | TTS §6.2, §8.3 |
| **Stat sliders** | Player-board buttons (`createButton`) with +/− for each stat, with a custom-XML mirrored display. | TTS §7.4 |
| **Doom marker auto-advance** | `setPositionSmooth` along snap-point track; trigger threshold scripts at 10/15/20/25/30. | TTS §6.3 |
| **Combat helper** | A "Roll Combat" XML button per player rolls their attack dice and reports hits in chat. | TTS §8.6 |
| **Save/Load state** | `onSave`/`onLoad` JSON-encoding of: day, doom, character stats, hands, decks-in-play, ongoing Dawn-card effects. | TTS §8.4 |
| **Hidden info** | Each player's hand zone is `HandTrigger` for their seat color. Cards in market and threat areas are face-up; cards in players' hands are private. | TTS §10 |

### 18.4 Performance considerations

Per [HowToCreateGamesInTabletopSimulator.md §11](Archive/HowToCreateGamesInTabletopSimulator.md):

- Total active object count target: <500 (well under the 1500 ceiling). Resource tokens are the biggest concern; using `Infinite_Bag` per resource keeps the active token count low.
- Card atlases: Each deck (~50 cards max) fits one 10×7 atlas at 408×585 per cell.
- Standees: 5 character + 4 boss + 5 visitor = 14 figurines, well within budget.
- Custom dice: 1 (the Sanity d8).

### 18.5 Asset hosting

All custom assets (card faces, board image, location tiles, standee art) must be hosted on a stable HTTPS source. Recommended: Steam Workshop upload (cached automatically) or a dedicated CDN. Local file URLs (`file:///`) are acceptable during prototyping but must be replaced before publication. ([HowToCreateGamesInTabletopSimulator.md §3](Archive/HowToCreateGamesInTabletopSimulator.md).)

### 18.6 Tagging convention

Per [HowToCreateGamesInTabletopSimulator.md §16.4](Archive/HowToCreateGamesInTabletopSimulator.md), prefer tags over GUIDs:

- Tag every card with its deck (`PhaseCard`, `MarketCard`, `ThreatCard`, `RecipeCard`, `VisitorCard`, `TrophyCard`).
- Tag every standee with `Character` or `Boss`.
- Tag every resource token with `Resource:<Type>`.
- Tag location tiles `Location:<Name>`.

Lua scripts query by tag, not GUID, so duplication and re-spawning don't break them.

### 18.7 Notebook tabs

The TTS Notebook is a fallback reference for players who prefer text. Day-to-day play is driven by the in-game **Help menu** (§18.17), which is more discoverable. Provide three Notebook tabs as a backup:

1. **Quick Start** — 1-page summary of the game loop and victory conditions.
2. **Full Rules** — abridged from this document.
3. **Character Reference** — perks/constraints for all five characters.

These tabs are populated from the `content/notebook/*.md` files at load time so they stay in sync with this design doc.

### 18.8 First-time-load checklist

When a player first loads the mod, the host should see:

- All custom assets cached (no broken images).
- A "Setup Game" button on the table.
- A welcome message in chat: "Welcome to Starve No More. Choose your survivor and click Setup."

### 18.9 Information hierarchy (what's hidden, what's public)

Per [HowToCreateGamesInTabletopSimulator.md §2](Archive/HowToCreateGamesInTabletopSimulator.md), step 3, the **information model** is the design decision most expensive to fix late. For Starve No More:

| Element | Visibility | TTS realization |
|---|---|---|
| Player Item cards (in hand) | Private to the holder | Hand zone, per-color `HandTrigger` |
| Player resource counts | **Public** | Resource tokens placed openly on the player board (not hidden) |
| Player stat values (H/H/S) | Public | Sliders/markers on the open player board |
| Phase deck top card | Hidden until revealed | Face-down `DeckCustom` |
| Phase deck contents | Hidden | Inside the deck, not searchable |
| Threat deck top card | Hidden until drawn | Face-down |
| Discard piles (any deck) | Public, browseable | Face-up adjacent to the deck |
| Market display | **Public** | Face-up, 5 slots |
| Recipe cards | Public reference | Loose face-up cards on the table |
| Doom marker | Public | On the visible track |
| Day Counter | Public | Counter widget |
| Boss standees | Public | On the map when active |
| GM-only setup notes | Hidden | `GMNotes` field on relevant objects |

**Why resources are public.** This is a deliberate co-op design choice. Public resources prevent hoarding-as-secret and force the social trade layer to operate on shared information — the Catan-style negotiation pattern. It also reduces the alpha-player advantage by making the team's combined inventory visible to everyone, so juniors can argue from the same data the experienced player sees.

**Why hands are private.** Item card combos can be a private creative engine. Keeping cards hidden lets each player retain a strategic pocket, and prevents the alpha player from optimizing every player's hand for them — see §19.5.

### 18.10 UX design: playable on first sit-down

The game's stated goal in §1.4 is "cozy dread" — but the implementation also has a stated *operational* goal: **a new player should be able to sit down, click around, and play meaningfully without reading the rulebook first**. A player learns the game by playing it, not by studying it.

This subsection codifies the UX choices that make that possible. They are not nice-to-haves; they are the design.

#### 18.10.1 The seven UX principles

1. **The component teaches.** Every card, tile, button, and token has its rule printed on it in plain language. A player should never have to consult an external doc to understand what an object does — the object says.
2. **The phase prompts.** The screen always tells the active player what to do next. There is never a moment of "what now?"
3. **Costs are visible before commitment.** No button consumes resources without first showing what it will cost and asking for confirmation.
4. **Errors explain themselves.** A failed action says *why* it failed and what to fix.
5. **State is broadcast.** Whenever a rule fires (Doom threshold crossed, ongoing Dawn effect active, character goes Down), it announces itself in chat *and* in a visible banner.
6. **Symbols repeat.** The same icon for "Hunger" is used everywhere — on cards, sliders, action buttons, recipes, threats. Once a player learns one icon, they have it everywhere.
7. **The first decision is small.** Setup walks each player through one choice at a time. They are never confronted with the whole rulebook at once.

A rule of thumb when reviewing any new component: **show it to a player who has never read the rules. If they cannot make a sensible first decision with it, the component is wrong.**

### 18.11 The Phase Banner (the persistent on-screen guide)

A panel anchored to the top of the screen, visible to all seated players at all times. It always shows five fields:

| Field | Example | Source |
|---|---|---|
| Day | "Day 3 of 7" | `gameState.day` / Day Counter |
| Phase | "Phase 2: Strange Days" with a 4-segment progress bar | `gameState.phase` |
| Doom | "Doom 9 / 30 — next threshold at 10: night threats +1" | `gameState.doom` + lookup |
| Active player | "Ellie is acting" with her color border | `Turns.turn_color` |
| Next action | "Take an action" / "Resolve threats at Badminton Court" / "Click Begin Day" | Phase + sub-phase state |

This panel is the single most important UI element for new players. It tells them what is happening and what is about to happen, at all times. A player who reads only this panel and clicks where it suggests can play the entire game.

The banner has one button: **? (Help)**. See §18.16.

### 18.12 The Active-Player Indicator (multi-channel)

Whose turn it is is signaled in four redundant channels — overkill is the point, because new players in TTS often miss subtle cues:

1. **Phase banner** field updates with the active player's name and color.
2. **Hand zone glow.** The active player's `HandTrigger` zone gets a colored border (Lua-driven `setColorTint` on the zone).
3. **Standee bounce.** The active character's standee gently bobs every 4 seconds via `setRotationSmooth`.
4. **Other boards dim.** Inactive players' boards get `ColorDiffuse` set to ~0.7 brightness; the active board is full brightness.

When all four channels point at the same player, no one needs to ask whose turn it is.

### 18.13 The per-player Action Bar

Each player board has a horizontal bar of seven labeled icon buttons. Each button shows its **action cost** in brackets and its **icon**:

| Button | Label | Visible state when unusable |
|---|---|---|
| 🚶 | **Move (1)** | Dim if no adjacent location is reachable. |
| 🤲 | **Gather (1)** | Dim if location's resource bag is empty. |
| 🛠 | **Craft (1)** | Dim if no Market card is affordable; tooltip lists the cheapest. |
| 🍲 | **Cook (1)** | Dim if no Crockpot here. Tooltip: "Move to a Crockpot location first." |
| ⚔ | **Fight (1)** | Dim if no enemy at this location. |
| 💤 | **Rest (1)** | Always available. |
| 🛐 | **Cleanse (1)** | Dim if missing the Cleansing bundle. Tooltip lists what's missing. |

Three **Action Cubes** sit next to the bar. Each click of an action button consumes one cube, animating it from "available" to "spent". When all 3 are spent, the bar greys out and the banner shows "End of Day actions — click Pass to finish your turn."

The bar gives the new player two things at once: a **menu** of legal moves and a **vocabulary** for understanding the game.

### 18.14 Component teaching: tooltips, confirms, broadcasts

Three patterns ensure that every interaction is self-teaching.

**Tooltips on every interactable.** Hovering any object shows a 1–2 line description plus the object's relevant rule:
- Resource tokens: "Wood — found at Basketball/Badminton Courts. Used in crafting and as fuel."
- Stat sliders: "Hunger — depletes 1 per day. Below 3 you cannot Fight."
- Doom marker: "Doom 9. Next threshold at 10: night threats +1."
- Threat cards: their own rules text in larger type.

**Confirm-before-spend dialogs.** Any action that consumes resources first shows a dialog:

> **Craft Crowbar?** Cost: 2 Metal + 1 Wood. You have: 3 Metal, 2 Wood.
> [✓ Confirm] [✗ Cancel]

Players never accidentally commit a cost. New players also learn the cost mechanic just by seeing it surfaced.

**Chat broadcast log with color coding.** Every game-state change is announced in chat:

| Color | Meaning | Example |
|---|---|---|
| 🔴 Red | Damage / loss event | "Coco loses 3 Sanity from isolation." |
| 🟡 Yellow | Warning / threshold crossing | "Doom reaches 15 — Scarcity: crafts cost +1 extra resource." |
| 🟢 Green | Positive event / gain | "Rayman gathered Wood. Echoes 6: bonus Item drawn." |
| 🔵 Cyan | Phase change | "Phase 3: Long Nights begins. Doom rate +2/day." |
| ⚪ Gray | Procedural | "Day Counter: 3. First Player passes to Rayman." |

The chat log is scrollable, so a player who arrives mid-game (or stepped away) can recover state by scrolling back. This is the implicit "save game replay" that TTS does not natively provide.

### 18.15 Iconography and the severity legend

A standard icon set is used across all printed components and all UI panels. New players learn each icon once and recognize it everywhere.

| Icon | Meaning |
|---|---|
| ❤ | Health |
| 🍴 | Hunger |
| 🧠 | Sanity |
| 🪵 | Wood |
| ⚙ | Metal |
| 🧵 | Cloth |
| 🍎 | Food |
| ⚡ | Energy Drink |
| 🔋 | Battery |
| ⚔ | Combat damage |
| 🛡 | Defense / cover |
| 🔥 | Light source / fire |
| 🌑 | Darkness — Charlie risk |
| ●●●○○ | Severity rating (Dawn/Threat cards) |

A small **Severity Legend** card sits permanently next to the Threat deck:

> ●○○○○ — Atmospheric flavor only.
> ●●○○○ — Minor stat hit.
> ●●●○○ — Combat or lasting effect.
> ●●●●○ — Phase-shift event.
> ●●●●● — Boss arrival / apocalyptic.

The dots that appear on Dawn and Threat cards are now legible at a glance. A new player sees ●●●●● and braces; they don't need rules text to feel the threat.

The Doom track also has its **threshold ribbon printed on the board itself** beside the relevant step:

```
Doom track:
[start] 5 [10: Night threats +1] 15 [Crafts +1 cost] 20 [-1 Sanity Tick]
        25 [Bosses any phase]   30 [DEFEAT]
```

The looming pressure is concrete, not abstract.

### 18.16 Onboarding: setup walkthrough and character introduction

The Setup button does not just deal cards — it walks players through a guided sequence that doubles as a tutorial.

**Step 1 — Pick a path graph.** A modal: "Pick a starting layout." Three buttons (Compact / Sprawl / Linear), each with a small preview image. Click → that variant's path edges spawn between the location tiles. Other two are removed.

**Step 1.5 — Optional variants.** A small host-only modal with two toggles, both OFF by default, and a Continue button: **Rotation turns** (§11.2 — one action per visit) and **Random Scenario** (§17.3 — revealed after characters are chosen). The modal says explicitly: "Both off = the standard game. First game? Just click Continue." — the §18.10.7 principle (the first decision is small) means new tables must be able to click straight through.

**Step 2 — Pick characters.** Each seated `Player.Color` gets a pop-up showing all five character cards (front + back), with one-line plain-language strengths under each:
- *James — fast learner; reads cards before drawing them.*
- *Coco — heals, calms, immune to the dark.*
- *Rayman — strongest fighter; loud and hungry.*
- *Ellie — feeds the team; everyone benefits.*
- *Luca — boosts allies; charisma at the campfire.*

A player picks one. Picked characters turn unavailable for other seats. Coco starts at Ellie & Luca's House (handled by the script).

**Step 3 — Read your character briefing.** Each player gets a one-time popup, visible only to them:

> **You are Rayman, the Basketball Player.**
>
> **Strengths**
> - Move 1 extra space per Move action.
> - +1 attack die at the Basketball Court.
> - Defend: shield adjacent allies for one round.
>
> **Constraint**
> - Big Appetite: lose 2 Hunger per day (others lose 1).
> - Loud: if you moved today, wherever you sleep draws +1 Threat tonight.
>
> **Try first:** Move to the Basketball Court and gather Wood — your Court Master perk applies there.
>
> [I understand]

This single popup is the on-ramp. New players read it, dismiss it, and they have the gist of their character without having opened the rulebook.

**Step 4 — Day 1 begins.** Phase banner takes over; "Reveal Dawn" button is the only highlighted action. The team is in the river of play.

### 18.17 The Help menu and the "What now?" hint

A floating **Help (?)** button on the Phase Banner opens a side panel with five tabs. The panel is read-only (no game state changes); it stays open while the game continues.

| Tab | Content | Source |
|---|---|---|
| **Quick Start** | 1-page summary of the loop and victory conditions | Notebook content (§A.5) |
| **Your character** | Active player's perks, constraints, suggested first move | Per-character data |
| **Active Dawn** | Full text of the current Dawn card and any ongoing effects | `gameState.activeDawn` |
| **Doom** | Current value, next threshold, all threshold rules | `gameState.doom` lookup |
| **Glossary** | Every icon and keyword in the game | Static reference |

A second smaller button next to Help: **"What now?"** — context-aware advice. Click during:
- Day Phase: "It's your turn, Ellie. You have 2 actions left. Suggested: cook a recipe at the Kitchen — you have 2 Food and 1 Wood available."
- Dusk: "Last chance to move: scramble 1 tile (1 Hunger) via the Dusk panel, or stay put. You sleep where you stand."
- Night: "Resolving threats at Badminton Court. Coco is here; click Resolve to proceed."
- After a defeat: "The team lost on Day 6. Click Restart to try again with the same characters, or Setup for a fresh game."

The hint is generated from current state. It is the single most important new-player aid: the system does not assume they know anything.

### 18.18 Phase mood, end-of-round summary, and safety nets

**Phase mood.** The visual environment subtly changes by phase, providing a felt rhythm:

| Phase | Lighting / mood | UI cue |
|---|---|---|
| Dawn | A flash; the Phase Banner highlights for 3 seconds | "Reveal Dawn" prominent |
| Day | Normal warm lighting | Action Bar enabled |
| Dusk | Slight desaturation | "Scramble or stay" banner; Dusk panel offers the 1-tile scramble |
| Night | `Lighting.LightIntensity` lowered ~25%; cooler ambient | Threats pile face-up by location; "Resolve Night" prominent |
| Tick | Brief animated slide of stat tokens; soft chime | "End-of-Round Summary" panel shows |

These cues are not gameplay — they are *legibility*. Players know what phase they're in by the table's mood.

**End-of-Round Summary.** After Tick, a 6-second auto-dismissing panel summarizes:

> **End of Day 3 — Strange Days**
> - Doom: 8 → 9
> - Lost: Rayman 2 Hunger, Coco 3 Sanity → DOWN
> - Gained: Stew cooked, Crowbar crafted, Toy Bow drawn
> - Threats defeated: Shadow Stalker
>
> **Next:** Day 4 Dawn — click Begin Day when ready.

Players who looked away can catch up with one read. The panel is dismissable manually if everyone's already absorbed it.

**Safety nets.** Risky or irreversible actions get a second confirmation:
- Ending the Day Phase before all players have spent their actions.
- Sleeping alone at a sport court (the worst case in the game).
- Spending the last Telltale Heart.
- Moving an injured character into a high-threat zone at Dusk.

The system is not stopping bad plays — it is ensuring the player meant it.

**Fail-friendly defaults.** If a player does something the rules don't strictly cover, the game does *not* throw a script error. It silently allows it and posts a chat note: "(Edge case — the rules don't strictly cover this. Continuing.)" This means new players exploring the buttons cannot break the session.

### 18.19 What this UX program is not

This is not a list of polish items to ship in a v2 patch. **Every item in §18.10–18.18 is part of the v1 design**, because the design's stated player-experience goal is *playable on the table without a rulebook* (§1.4). A TTS implementation that omits these is not an implementation of *this* game — it is a different, harder-to-onboard game wearing the same components.

The original build plan that walked the implementation through Phases A–K is preserved in `Archive/Checklist_For_TTS_Implementation.md`; current build status lives in `agents.md` and `README.md`.

---

## 19. Design Rationale Cross-Reference

For traceability, every major design decision is tagged with its inspiration source. A second subsection (§19.5) self-audits against the Designer's Checklist from [PrinciplesOfGoodBoardGames.md](Archive/PrinciplesOfGoodBoardGames.md).

| Decision | Source | Rationale |
|---|---|---|
| Three-stat trade-off economy | DST §2 ([DontStarveVideoGamePrinciples.md](Archive/DontStarveVideoGamePrinciples.md)) | The heart of DST's decision-making. Mismatched currencies force interesting choices. |
| Day/night cycle with forced retreat | DST §4 | Built-in pacing rhythm; creates the campfire moment. |
| Phase-based week arc with bosses | DST §3, §10 | Game arc; rising tension; climactic punctuation. |
| Soft permadeath via ghost state | DST §7 | Death is meaningful but doesn't eliminate the player. |
| Asymmetric characters with hooks + constraints | DST §6, Cthulhu Wars §3.3.1 ([InterestingGames.md](Archive/InterestingGames.md)) | Each character plays a different game; cooperation requires complementary roles. |
| 5 unique location tiles with special actions | DST §1, Catan §2.3.1 | Suburban map as DST world; tiles as Catan-style modular geography. |
| Doom track | Cthulhu Wars §3.3.5 + HPHB §1.3.5 | Visible loss timer; the game's main dramatic arc. |
| Market deck of craftable items | HPHB §1.3, Cthulhu Wars (spellbook unlocks) | Engine-building progression; encourages varied strategies. |
| Crockpot recipes | DST §2 + Catan trading | Cooking is a social magnet; encourages co-location. |
| Open negotiation / trading | Catan §2.3.8 | The replayability engine: other humans are infinite content. |
| Multiple paths to victory (Pristine, Truth, Hero) | Catan §2.3.9 + general design theory ([PrinciplesOfGoodBoardGames.md §11](Archive/PrinciplesOfGoodBoardGames.md)) | Replayability through varied goals. |
| Dawn card "world acts first" | HPHB §1.3.3 | No turn is safe; pressure is constant. |
| Full 3-action turns (default) + one-action-then-pass **Rotation variant** (§11.2) | Cthulhu Wars §3.2 | The default keeps a new player's turn coherent (plan 3 actions as one thought); the Rotation variant is the Cthulhu Wars downtime cure — at 5 players it cuts the wait between your decisions from up to 12 consecutive foreign actions to 4. Which one the table prefers is an explicit playtest A/B (§20.2). |
| Visible component scale (boss standees larger) | Cthulhu Wars §3.4 | Information design through physical hierarchy. |
| Variable map setup (3 path configurations) | Catan §2.3.1 | Cheap replayability lever. |
| Hand limit forces trade | Catan §2.3.5 (the "7 effect") | Discourages hoarding; forces interaction. |

### 19.5 Anti-alpha-player design

In a co-op game with public boards, the most common failure mode is the **alpha player problem**: one experienced player optimizes every decision for the table while everyone else watches. Starve No More fights this on five fronts ([DontStarveVideoGamePrinciples.md §9](Archive/DontStarveVideoGamePrinciples.md), [PrinciplesOfGoodBoardGames.md §8](Archive/PrinciplesOfGoodBoardGames.md)):

1. **Private item hands.** Every character's Item cards are face-down in their hand zone. Other players can suggest plays but cannot read the actual options. The owner has a private creative space.
2. **Asymmetric perks and constraints.** A James player and an Ellie player are good at *different* things. The optimal play for one is rarely the optimal play for another, so a single brain cannot drive everyone correctly.
3. **Ghost word-limit.** Down players can speak only one word per round to the team (§16.4). This stops a "dead" alpha from quarterbacking the survivors. (It also produces some of the game's funniest moments.)
4. **Soft turn timer (optional).** Default rules suggest a 60-second sand timer per player turn during Day Phase. Strictly optional, but groups with a known alpha player should turn it on — it short-circuits over-optimization.
5. **Trade-not-give.** When a stronger player wants to "fix" a weaker player's hand, they must publicly trade for it. The transaction is visible and reciprocal, not unilateral.

The design does *not* hide the global game state. Resources, the Doom track, and stat values are all public — that is necessary for the co-op layer to function. What is hidden is *the room to maneuver inside one player's options*. That is the right partition.

### 19.6 Designer's Checklist self-audit

[PrinciplesOfGoodBoardGames.md](Archive/PrinciplesOfGoodBoardGames.md) closes with a 10-item Designer's Checklist. Running this design against it:

| # | Check | Status |
|---|---|---|
| 1 | Can you name the emotion the game targets in one sentence? | ✅ "Cozy dread" — §1.4. |
| 2 | Does each turn present at least one meaningful choice with real trade-offs? | ✅ The 3-action budget combined with the mismatched-currency map (§8.4) makes every action a choice. |
| 3 | Is there a rule you're keeping out of fondness? | ✅ Acted on — the Visitor **adoption** sub-rule was cut (§9.5); Visitors are now one-shot aid only. The deck itself stays, at near-zero rules cost. |
| 4 | Do mechanics and theme reinforce each other? | ✅ Hunger/Sanity/Health, the Crockpot social magnet, Charlie attacks, and Telltale Heart sacrifice all are *consequences* of the world, not arbitrary rules. |
| 5 | At least 2–3 viable paths to victory? | ✅ Survive (default), Pristine, Truth, Hero — four overlapping goals (§16.2). |
| 6 | Different feel in early/mid/end game? | ✅ Jo-Ha-Kyu mapping (§14). Early days are exploratory; Day 5+ is climactic. |
| 7 | Stress-tested for runaway leader, kingmaking, AP, elimination? | ✅ Co-op (no runaway leader); ghost word-limit (no kingmaking); soft turn timer (AP); ghost state (no elimination). |
| 8 | Does player interaction generate stories? | ✅ Mismatched currency forces visible deals; the worked example in §11.6 shows the table-talk window naturally. |
| 9 | Has the rulebook been read by someone who wasn't in the room while you wrote it? | ❌ Pending — everything a blind playtest needs is now built (batch 4): session telemetry with a one-click export, the facilitator script and feedback form in `playtest/`, and a calibrated Standard difficulty. Two independent blind groups completing a game flips this. |
| 10 | Have you played it enough to be sick of it and still want to play again? | ❌ Pending — the retention question ("do you want to play again right now?") is on the feedback form; yes-without-prompting is the only pass. |

Two ❌ marks are acceptable at v1 (this document is the brief, not a finished game). Item 3's ⚠️ is the single most actionable note: the Visitor deck must justify itself in playtests or be cut.

---

## 20. Balancing, Playtest Plan, Expansion Hooks

### 20.1 Known balance risks

- **Coco's lack of house** — penalty is strong; if it's too punishing, allow her to "claim" a temporary home each game.
- **Rayman's loud movement penalty** — needs tuning; could make him underplayed if too harsh.
- **Doom track rate** — retuned 2026-07 to the §15.6 table (3p [1,1,1,1] / 4p [1,1,1,2] / 5p [1,1,2,2], no boss arrival Doom) after simulation showed the old table made 5p nearly unwinnable. The residual risk has inverted: with a gentle fixed clock, most Doom is now responsive (festering) — if playtests show diligent teams cruising, raise Phase 3–4 rates by +1 before touching festering.
- **Boss lethality under the mandatory Source** — the Source must be killed to win, and the sim's crude combat model loses ~20–30% of games to it or to Downs accumulated across three boss fights in four days. **Knob taken (batch 4 W3, 2026-07): Source HP 10 → 8** — the single sanctioned change that put the sim's best line in the 40–50% band (turtle 34%→42%, spread 27%→41%) with losses still clustering on Days 6–7. Trophy healing remains the next knob if tables still find the Final Hours a meat grinder.
- **Hand limit (5 cards)** — may need to be 6 to allow comfortable crafting; playtest both.
- **Telltale Heart cost** — 2 Health from reviver is significant; if revival is too rare, lower to 1 Health.
- **Festering Doom (+1/threat cap +3; bosses +2 uncapped) and Down Doom (+1)** — target end-of-game Doom around 18–26 on a Standard win; if games routinely blow past 30 by Day 5, lower the ordinary-threat cap to +2 before touching phase rates. Do NOT re-cap boss festering — the uncapped boss rate is what keeps boss-avoidance from being the dominant strategy (simulation-verified; see §15.1).
- **Charlie escalation (2/1 base, +1/+1 per consecutive dark night)** — watch whether two consecutive dark nights is a death sentence for low-Health characters; if so, escalate Sanity only.
- **Crowded floor (2 beds per house)** — check the 5-player geometry (forced 2/2/1 split); if the floor rule reads as pure punishment, let a Bedroll item add a third bed.
- **Moonlit Salvage (2 resources)** — the court-sleep gamble should be tempting roughly once per game per team, not a camping strategy; if court-camping dominates, drop to 1 resource + 1 Echoes roll.
- **Loud (moved today = +1 Threat at Rayman's night tile)** — watch whether Rayman players simply never move; if so, the constraint is over-tuned — soften to "moved 3+ tiles today."
- **3-player composition inequality (simulation flag, 2026-07; reliefs implemented batch 4 W2)** — the `--sweep3` composition sweep found 3-character teams ranging from ~86% to ~0.5% win rate under their best scripted policy: every viable trio includes Coco or Luca, and all six Rayman trios collapsed (his Big Appetite + Loud overheads don't shrink with the team). **Both cheap knobs from the candidate menu are now implemented, behind a `playerCount == 3` guard:** Big Appetite costs 2 Hunger only on days Rayman fought or moved 2+ tiles, and Loud requires 3+ tiles moved. Sweep after: the floor gate passes (worst trio 31% under its best policy, nothing near 0) — but the sim *over-corrects*, putting Rayman trios at the top (97–99%), because Loud was the only Rayman cost it models against his fully-modeled combat value. The Big Appetite knob alone moved almost nothing (the collapse was Loud→Charlie→Sanity-6, not Hunger). **Verdict: the sim brackets the answer; the real tuning decision belongs to the W2 table A/B** — a Rayman trio must be confirmed fun at a real 3-player table before this is closed. Do not fix it with roster restrictions (§6.6).
- **Flee (1 tile, 1 Sanity, threat festers)** — watch for flee-chaining as a free evasion loop; the Sanity bleed plus fester Doom should make three flights in a week feel expensive. If not, raise to 2 Sanity.
- **The Stash (2 Energy Drinks per gather at James's)** — if James stops visiting home entirely after one mega-stock, cap held Energy Drinks at 4.
- **Haunted (personal Threat at Dawn, allies can't help)** — check it doesn't hard-kill low-Sanity + low-Health characters; if so, cap Haunted threats at 2 HP.

### 20.2 Playtest plan

1. **Solo paper test** (designer + 2 hands) — verify the loop works mechanically, identify dead turns. 3 days only.
2. **3-player teach-and-play** — 3 days, then 7 days. Watch for analysis paralysis.
3. **5-player full game** — confirm the table doesn't get overwhelmed; check that 5 characters all feel relevant.
4. **Blind playtest** — give the rules to a group with no designer present; observe what they get wrong. Fix the rulebook accordingly.
5. **Stress test difficulty** — repeat plays with the same group to find the win rate (target: 40–50% on Standard difficulty for experienced groups). *Status (batch 4 W3, 2026-07): calibrated on the simulator — best line 42% with ~100% of losses on Days 6–7, via the Source HP 10 → 8 knob; the three difficulty modes (§17.2) are selectable at setup. Table confirmation pending; each session's Copy Session Log export feeds this.*
6. **Turn-structure A/B (5 players)** — play one full game with default 3-action turns and one with the Rotation variant (§11.2), same group. Watch for: time between one player's decisions, phone-checking during others' turns, and whether Rotation fragments planning ("I forgot what my second action was for"). This decides whether Rotation stays a variant, becomes the 5-player default, or gets cut. *Status (batch 4 W0/W1): fully instrumented — the session log records `turnStyle` and per-turn durations in seconds, so the two games are directly comparable. Protocol in [playtest/facilitator_script.md](playtest/facilitator_script.md). Decision pending table data.*
7. **Scenario pass** — once the base game's win rate is settled, one game per Scenario (§17.3) to catch degenerate combinations (e.g., Total Blackout with a Coco-less team that can't survive dark nights).

### 20.3 Expansion hooks (post-launch)

- **More characters.** A Year 2 box adds 5 new survivors (e.g., a Musician, a Mechanic, a Dog).
- **More locations.** Extend the map to 8 locations: Library, Convenience Store, the Park.
- **The Source's Backstory** (campaign mode). A 5-game arc where decisions persist between sessions: which characters survived, which clues were found, what the Source actually was. (Borrowing HPHB's box-progression idea, [InterestingGames.md §1.3.6](Archive/InterestingGames.md).)
- **Co-op vs. Traitor variant.** One player secretly serves the Source. Raises the game's social-deduction layer.
- **Solo mode.** Single player controls 2–3 characters as a personal cast.

### 20.4 What's deliberately not in the design

In line with [PrinciplesOfGoodBoardGames.md §3](Archive/PrinciplesOfGoodBoardGames.md) (cut, fuse, generalize):

- **No tech tree beyond the Market.** A second tech progression would bloat the rules; the Market deck handles "tier" via card costs.
- **No weather system.** Already implemented via Dawn cards; a separate die or chart would duplicate.
- **No XP leveling.** Characters don't grow during a game; the Item cards are their progression.
- **No formal alliances/factions.** This is a co-op game; faction layers would dilute the cooperation pillar.
- **No resource market beyond player trade.** The Catan-style 4:1 bank trade tempted us, but adding it would weaken the social trade layer.

---

## Closing Notes

This document is the v1 design brief for Starve No More. It is written to be:

1. **Complete enough to playtest from.** A team could prototype on paper this week.
2. **Specific enough to implement in TTS.** Every component is mapped to a TTS object type.
3. **Open enough to iterate.** Numbers (stat values, costs, rates) are starting points, not gospel — playtesting will move them.

Next steps:
1. Build a paper prototype.
2. Run two solo playtests to debug the core loop.
3. Run a 3-player teach-and-play.
4. Refine, then begin asset production for the TTS implementation.
5. Once art and components are stable, build the TTS save per [HowToCreateGamesInTabletopSimulator.md §9](Archive/HowToCreateGamesInTabletopSimulator.md).

The game succeeds when: a group of three friends plays through a seven-day campaign, loses on Day 6 to the Eye of Terror, immediately resets, and starts over with different characters. That is the test. Everything in this document is in service of that outcome.

---

*Reference documents (archived; preserved for traceability):*
- [Archive/PrinciplesOfGoodBoardGames.md](Archive/PrinciplesOfGoodBoardGames.md) — design theory.
- [Archive/DontStarveVideoGamePrinciples.md](Archive/DontStarveVideoGamePrinciples.md) — DST translation.
- [Archive/InterestingGames.md](Archive/InterestingGames.md) — patterns from HPHB, Catan, Cthulhu Wars.
- [Archive/HowToCreateGamesInTabletopSimulator.md](Archive/HowToCreateGamesInTabletopSimulator.md) — TTS implementation guide.
