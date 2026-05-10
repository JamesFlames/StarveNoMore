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

1. **Dawn (event)** — Reveal the day's **Dawn card** from the current Phase deck. Resolve immediately. (See §15.)
2. **Day Phase (player actions)** — Each player takes a fixed number of actions in turn order. Default: **3 actions per player**.
3. **Dusk (declaration)** — Each player declares which location they will spend the night at. This is committed publicly.
4. **Night Phase (resolution)** — All players resolve night events at their chosen location. Players outside their declared location, or alone in dangerous spaces, suffer additional consequences.
5. **Tick (decay)** — Every player loses 1 Hunger and 1 Sanity (modified by location and character traits). Day counter advances. Doom counter advances by current rate.

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
- **Constraint: Wired.** James starts the game addicted to Energy Drinks. If he does not consume an Energy Drink token by the end of any day, he loses 2 Sanity that night.
- **Starting hand:** Energy Drink ×2, Pocketknife, Flashlight, Headphones (sanity buffer).
- **Plays best with:** Coco (sanity stability), Ellie (food independence).

### 6.2 Coco — The Angel

- **Identity.** Asian female. Calm presence. Spiritual core. Visiting from out of town — does not have her own house tile.
- **Visual style.** Soft sweater, pale halo motif faintly visible in her shadow on the map.
- **Base Stats.** Health **6**, Hunger **8**, Sanity **12**.
- **Perk: Calming Presence.** All allies in Coco's location lose 1 less Sanity at the night Tick (minimum 0).
- **Perk: Touch of Hope (once per game).** Heal any character on the map by 4 Health, regardless of distance.
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
- **Constraint: Big Appetite.** Loses 2 Hunger per day Tick (other characters lose 1).
- **Constraint: Loud.** When Rayman moves to a new location, draw 1 extra threat card during Night.
- **Starting hand:** Basketball (improvised weapon), Sports Drink ×2, Athletic Tape, Whistle.
- **Plays best with:** Ellie (food management), Luca (Sanity).

### 6.4 Ellie — The Cook

- **Identity.** Caucasian female. Calm under pressure. Lives at Ellie & Luca's House (with Luca).
- **Visual style.** Apron over a sweatshirt, hair tied back, a wooden spoon as habitual gesture.
- **Base Stats.** Health **8**, Hunger **10**, Sanity **8**.
- **Perk: Crockpot Master.** Recipes Ellie cooks require 1 fewer ingredient (minimum 1).
- **Perk: Comfort Food.** When Ellie shares cooked food with another character, that character gains +1 extra Hunger and +1 extra Sanity.
- **Perk: Knows the Pantry.** When at Ellie & Luca's House, Ellie may search the resource bag for a specific Food or Cooking Ingredient (does not draw randomly).
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
- **Constraint: Needs an Audience.** Luca regenerates Sanity only when at least one other player is in his location. Alone, his Sanity does not regenerate.
- **Starting hand:** Notebook, Loud Whistle, Pep-Talk (single-use card), Reading Lamp, Toolbox.
- **Plays best with:** Anyone with low Sanity (he supports them).

### 6.6 Character Selection and Group Composition

- Players choose characters in any order (suggest reverse-age, alphabet, or draft).
- A **3-player game** uses 3 characters. The remaining two are **Visitor NPCs** that can be encountered at houses (drawn into the active group via a Dawn event card around Day 3 — they offer one-time aid then leave or join the party mechanically).
- A **4-player game** plays the same way but with one Visitor NPC.
- A **5-player game** has all five active.

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
- **Sanity modifier:** −1 (creepy at night, the building groans).
- **Defense:** −1 (open court, exposed).
- **Rayman bonus:** Court Master perk applies.

### 7.5 The Badminton Court

- **Yield.** Cloth (nets), Wood (rackets, posts), Metal (fittings).
- **Special: The Net.** When defending in combat at this location, the team rolls +1 die (the nets entangle attackers).
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

### 9.5 The Visitor Deck (small)

A small deck of ~6 cards used in 3- and 4-player games, representing the absent characters arriving for limited support. Triggered by a specific Dawn card mid-game.

When a Visitor card resolves:

1. The drawing player chooses one of the **inactive characters** (those not played by a human at the table) and places their standee at a house location indicated on the card.
2. The Visitor takes a one-shot signature action immediately (e.g., "Coco arrives. Heal one Down ally to 1 Health.") then leaves at the next Dawn unless adopted (see step 3).
3. **Adoption.** If a player has fewer than 3 active items in hand, they may "adopt" the Visitor: the Visitor stays as a controlled NPC, takes 1 free Move + 1 free Gather per round under the adopter's direction, but their **Hunger and Sanity decay against the adopter's stats** (the adopter spiritually carries them). This is the bounded social-deduction-free version of "more characters in play."

This keeps Visitor mechanics from sprawling into a full sixth player slot while still rewarding 3-player tables with mid-game flavor.

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
│ Flee: Move 2 spaces away on your next turn,  │
│ paying 1 Hunger.                             │
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
│ Then: Coco departs at next Dawn unless       │
│ adopted (see §9.5).                          │
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
- **Low Hunger (<3):** Cannot fight. Cannot use any action card with the [Effort] tag.
- **Low Sanity (<3):** Each Dawn, draw a Hallucination card from the threat deck, *resolve as if it were a real enemy*. Other players see the hallucination as a card; only the affected player knows it's not real (until it deals damage, which is real).

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
2. **Reveal Dawn Card.** Draw the top card of the current Phase deck and read it aloud. Resolve all immediate effects.
3. **Doom check.** Doom advances by the current rate (1, then 2 in Phase 3, then 3 in Phase 4).
4. **Note ongoing effects.** Place the Dawn card face-up if it has lingering rules; remove it at the next Dawn unless its text says otherwise.

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

### 11.3 Phase 3 — Dusk (1–2 minutes)

Each player **declares** which location they will spend the night at. Declaration is **public** and **simultaneous** (or in clockwise order; player choice).

A character can only sleep at the location their standee is currently on. If a character's standee is en-route or alone in a location they don't want, this is the time to scramble.

### 11.4 Phase 4 — Night (5–10 minutes)

For each location with players in it (in order from least populated to most):

1. **Threat draw.** Draw a number of Threat cards equal to the location's threat rate (0 for safe house tiles, 1 for sport courts, +1 if anyone "called attention" with a noisy action).
2. **Resolve threats.** Combat rolls happen as needed. Players may use items.
3. **Charlie check.** Any player whose location has no light source (no Flashlight, no Fire, no Battery-powered item) suffers a "Charlie attack" — 1 d8 Sanity damage and 1 d6 Health damage. (DST night-darkness translation; see [DontStarveVideoGamePrinciples.md §4](Archive/DontStarveVideoGamePrinciples.md).)
4. **Storytelling at the campfire.** Players together at a house location may use Comfort/Music/Photo items for collective Sanity gain.
5. **Sleep.** Each character regenerates per the table below. Coco's, Luca's, and Ellie's location perks resolve in addition.

   | Sleeping at... | Regenerates |
   |---|---|
   | Your own house | +1 Sanity, +1 Hunger, +1 Health |
   | Someone else's house, with at least one other character present | +1 Sanity |
   | Someone else's house, alone | nothing |
   | A sport court (Basketball or Badminton), any company | nothing — courts are not safe spaces |
   | A sport court, alone | nothing AND draw 1 extra Threat card |

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

**Dusk.** Declarations: Ellie at her House, James at Ellie's House (with her), Rayman at Basketball Court (alone), Coco at Badminton Court (alone — *uh oh*, her No Home constraint will trigger).

**Night.**
Resolution order: Coco → Rayman → Ellie & James (most populated last).

- **Coco at Badminton Court (alone).** Threat draw rate 2 (+1 because the Court is high-threat). She draws *Shadow Stalker* (the one James saw) and *The Wind in the Net* (atmospheric, −1 Sanity). The Stalker attacks: 2 dice → one 5 = 1 damage. Coco at 5 Health. She has no Flashlight; the Dawn card disabled them anyway. **Charlie attack:** roll d8 + d6 → 5 Sanity, 3 Health. Coco at 2 Health, 3 Sanity. Her No Home penalty: −3 Sanity for ending the night alone in a non-house tile. Coco is now Down (Sanity 0) — flip to ghost side.
- **Rayman at Basketball Court (alone).** Threat draw rate 2. Draws *Echoes* (already in play) and *The Hollow Spectator* (HP 3). He fights — 2 attack dice + 1 Court Master + 1 Toy Bow = 4 dice. Roll: 5,6,4,1. Two hits, one fumble. Spectator at 1 HP, Rayman at 11 Health. Spectator returns: 1 die, 5 = 1 hit. Rayman at 10. He has a Flashlight and a Battery: **no Charlie attack**, even with the Dawn card, because his Battery is paired with a *Lantern* (Fire-equivalent — he crafted it on Day 2; the Dawn card disables Flashlights only).
- **Ellie & James at Ellie's House.** Threat draw rate 0 (safe). They play Comfort items (James equips the Comfort Blanket Coco gave him — +1 Sanity). Sleep: Ellie at her own house → +1 Sanity, +1 Hunger, +1 Health. James at someone else's house with company → +1 Sanity. James drinks his Energy Drink (+2 Sanity, addiction satisfied).

**Tick.** Everyone loses 1 Hunger and 1 Sanity. Rayman loses 2 Hunger (Big Appetite). Coco's ghost lowers Ellie's and James's Sanity by 1 next round if she's still in their location at next Tick.

**Outcome.** The team gained ground on resources and a craft, but Coco is Down and the Doom is still climbing. They'll need to dispatch a Telltale Heart kit to her location tomorrow to revive her, costing real Health and a precious Cloth/Battery/Food bundle.

This is the rhythm of the game: a round is rarely catastrophic and rarely free. Survival is paid for in scattered small currencies all spent on the same night.

---

## 12. Combat

Combat is **fast and dice-based** ([InterestingGames.md §3.3.6](Archive/InterestingGames.md)). It has to be — combat happens often.

### 12.1 The roll

When a character fights an enemy:
- **Attacker rolls** dice equal to their **base attack value** (typically 1 die, +1 per equipped weapon, ±character/location modifiers).
- Each die showing **5 or 6** = 1 hit. Each hit does 1 damage to the enemy.
- Each die showing **1** = 1 self-hit (you fumble): take 1 Health damage.
- The enemy then attacks back: roll its **attack die count** (printed on the threat card). Each 5 or 6 = 1 damage to the attacker. (Defenders may use shield/cover items to negate hits.)

### 12.2 Group combat

If multiple characters are at the same location, they may fight cooperatively. They sum their attack dice, but each character takes return damage based on a shared pool divided by the GM-equivalent rule (highest-Health takes the first, then rotate).

Rayman's Defend action redirects all return damage to him for one round.

### 12.3 Death and Unconsciousness

If Health hits 0, the character is **Down** (see §16.4). Other characters at the same location may spend their next action to **Stabilize** (returning the character to 1 Health), but only if they have a Bandage item. Otherwise the character must wait for revival or stay Down.

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

---

## 14. The Week Arc and Pacing

Seven in-game days, divided into four narrative phases. This is the DST season structure ported to a tighter session length ([DontStarveVideoGamePrinciples.md §3](Archive/DontStarveVideoGamePrinciples.md)), explicitly mapped to the **Jo-Ha-Kyu** dramatic arc ([PrinciplesOfGoodBoardGames.md §7](Archive/PrinciplesOfGoodBoardGames.md)).

| Phase | Days | Jo-Ha-Kyu beat | Tone | Doom/Day | Phase Boss |
|---|---|---|---|---|---|
| 1 — Dusk of the Week | 1–2 | **Jo** (slow open) | Calm, exploratory. Resources are findable. Players learn the map. | +1 | None |
| 2 — Strange Days | 3–4 | **Ha** (break) | Pressure rises. Threats appear regularly. | +1 | The Deerclops (mid-tier; Day 4) |
| 3 — Long Nights | 5 | **Ha → Kyu** (pivot) | Boss night. Major disruption. | +2 | The Eye of Terror (heavy boss) |
| 4 — Final Hours | 6–7 | **Kyu** (rapid climax) | Survival sprint. Doom races. | +3 | The Source (final boss; Day 7 ending if not stopped) |

The pacing math is deliberate: roughly half the campaign is *Jo*-style exploration where players learn and plan, but the second half compresses sharply. This produces the felt arc players describe as "having a story," not just "having a session." Mid-game compression is the cure for the runaway-leader and dead-turn problems ([PrinciplesOfGoodBoardGames.md §10](Archive/PrinciplesOfGoodBoardGames.md)) — late-game decisions matter more than early ones, so a perfect early game cannot win the game alone.

### 14.1 Phase boss arrivals

Each phase boss is a Threat-card-style enemy that appears on a specific Dawn card during its phase. Bosses:

- **Pre-warn.** A Dawn card the day before announces them.
- **Disrupt rules.** While present, change the game state ("All Sanity costs are doubled while The Deerclops is on the map").
- **Reward when defeated.** Drop a Trophy card with a permanent passive bonus for the rest of the game.

Bosses are placed on a specific location determined by the Dawn card. The team must travel to or defend against them.

---

## 15. The Doom Track and Scheduled Threats

The Doom track is the main visible loss timer, lifted directly from Cthulhu Wars ([InterestingGames.md §3.3.5](Archive/InterestingGames.md)) but inverted (it ticks against the players, like HPHB's location track).

### 15.1 The track

A 30-step linear track on the main board. The Doom marker advances each Dawn:

- Phase 1: +1 per day.
- Phase 2: +1 per day.
- Phase 3: +2 per day.
- Phase 4: +3 per day.

If the marker reaches **30 before the team survives Day 7**, the team loses. Players can also push Doom back through specific "Cleanse" actions (see §15.3).

### 15.2 Doom thresholds (passive escalation)

The Doom track has annotated thresholds that change ongoing rules:

- **At 10:** The night phase threat draw is +1.
- **At 15:** Crafting market refresh is slowed (refill 1 slot per day, not all).
- **At 20:** All characters lose +1 Sanity at the night Tick.
- **At 25:** Boss-level threats can appear in any phase.
- **At 30:** Game over.

### 15.3 Pushing back Doom

Players can spend an action and a specific resource bundle (typically: 1 of each: Wood, Cloth, Battery, Energy Drink — i.e., representative of community ritual) to do a **Cleansing**, reducing Doom by 2. This is rare, expensive, and a key strategic decision: do you spend this action on yourself, or on the world?

### 15.4 Charlie attacks

Echoing DST's Charlie ([DontStarveVideoGamePrinciples.md §4](Archive/DontStarveVideoGamePrinciples.md)): any character at night without a light source suffers a Charlie attack. Coco is immune. Some boss-phase rules disable certain light sources.

### 15.5 Severity scaffolding (the dot system)

Borrowed from Catan's probability dots ([InterestingGames.md §2.3.2](Archive/InterestingGames.md)): Dawn cards and Threat cards print a **severity rating** as 1–5 dots in the top corner. The dots are not used in any rule — they are pure information design.

- ●○○○○ — atmospheric flavor only.
- ●●○○○ — minor stat hit (1 of one stat).
- ●●●○○ — combat-grade or lasting effect.
- ●●●●○ — phase-shift event (changes ongoing rules).
- ●●●●● — boss arrival or apocalyptic Dawn.

This solves the new-player problem: a new player can see a 5-dot Dawn card and instinctively brace, even before reading the text. Experienced players use the dots to plan inventory and movement. The same component teaches at two skill levels — Catan's probability-dots pattern, ported to a horror co-op.

### 15.6 Doom rate scaling by player count

The +1 / +1 / +2 / +3 doom-per-day rate is balanced for the 4-player baseline. Player counts adjust the rate:

| Players | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|
| 3 | +1 | +1 | +1 | +2 |
| 4 (default) | +1 | +1 | +2 | +3 |
| 5 | +1 | +2 | +2 | +3 |

Rationale: 3-player teams have less action economy, so doom advances slower; 5-player teams move more total resources per round, so doom keeps pace. This is a **negative feedback knob** ([PrinciplesOfGoodBoardGames.md §9](Archive/PrinciplesOfGoodBoardGames.md)) on group capability — it equalizes pressure across player counts without rewriting any other rules.

---

## 16. Victory and Defeat Conditions

### 16.1 Default victory

The team **wins** if all surviving characters are alive at the end of Day 7 (after the Day 7 night phase fully resolves) and the Doom marker is at less than 30.

### 16.2 Bonus victories

- **Pristine Run** — All five characters are alive at game end. (No revivals counted; all five must have reached the end on their feet.) Awarded a "Story Card" to keep.
- **Truth Run** — The team finds and reads all 3 Clue cards (special items in the Market deck) before Day 7. The ending narrative changes.
- **Hero Run** — Defeat all four bosses, including the Source on Day 7.

These are not separate goals — they are achievements layered on top of survival, encouraging replay.

### 16.3 Defeat conditions

The team **loses** if any of:

1. The Doom marker reaches 30.
2. All characters are simultaneously Down (Health 0 or Sanity 0) at any moment.
3. The Source boss reaches the Final Hours and is not stopped on Day 7.

### 16.4 Down state and revival

When a character is Down (Health 0 or Sanity 0):

- Flip the standee to its **ghost side**. The character cannot take actions, cannot gather, cannot fight.
- Ghost characters drift between locations (1 free move per round).
- Ghost characters lower the Sanity of any living player they share a location with at the night Tick (−1 Sanity, the lurking presence).
- A ghost can whisper a single word to the team per round (literally — the ghost player may say one word per round to advise; this both flavors the experience and limits the alpha-player problem).

To **revive** a Down character:

- Another character must be at the same location.
- Spend a **Telltale Heart** token (cooked per the §13.4 recipe).
- The revived character returns at half their starting maximums (e.g., James returns at 4 Health, 3 Hunger, 5 Sanity).

This is the DST soft permadeath ([DontStarveVideoGamePrinciples.md §7](Archive/DontStarveVideoGamePrinciples.md)) — death is meaningful but not eliminating.

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
10. Set Day Counter to 1, Doom marker to 0.
11. First player is the player whose real-life kitchen is currently most cluttered. (Theme.)

### 17.2 Difficulty variants

- **Easy / Long Weekend** — 3 days only, Phase 1 + half of Phase 2. Doom track halved. Good for teaching.
- **Standard** — 7 days, full rules.
- **Nightmare** — 7 days, Doom rate +1 in every phase, no Phase 1 (start on Strange Days).

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
| 🟡 Yellow | Warning / threshold crossing | "Doom reaches 15 — Market refresh slowed to 1/day." |
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
[start] 5 [10: Night threats +1] 15 [Market 1/day] 20 [-1 Sanity Tick]
        25 [Bosses any phase]   30 [DEFEAT]
```

The looming pressure is concrete, not abstract.

### 18.16 Onboarding: setup walkthrough and character introduction

The Setup button does not just deal cards — it walks players through a guided sequence that doubles as a tutorial.

**Step 1 — Pick a path graph.** A modal: "Pick a starting layout." Three buttons (Compact / Sprawl / Linear), each with a small preview image. Click → that variant's path edges spawn between the location tiles. Other two are removed.

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
> - Loud: trigger an extra Threat draw when moving to a new location.
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
- Dusk: "Each player declares where to sleep. Click on a location tile to claim it for tonight."
- Night: "Resolving threats at Badminton Court. Coco is here; click Resolve to proceed."
- After a defeat: "The team lost on Day 6. Click Restart to try again with the same characters, or Setup for a fresh game."

The hint is generated from current state. It is the single most important new-player aid: the system does not assume they know anything.

### 18.18 Phase mood, end-of-round summary, and safety nets

**Phase mood.** The visual environment subtly changes by phase, providing a felt rhythm:

| Phase | Lighting / mood | UI cue |
|---|---|---|
| Dawn | A flash; the Phase Banner highlights for 3 seconds | "Reveal Dawn" prominent |
| Day | Normal warm lighting | Action Bar enabled |
| Dusk | Slight desaturation | "Declare sleep location" banner; tiles become click-targets |
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
| One-action-then-pass rotation (in Day phase) | Cthulhu Wars §3.2 | Fast pacing; reduces alpha-player problem. |
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
| 3 | Is there a rule you're keeping out of fondness? | ⚠️ The Visitor deck is the candidate to cut — it adds rules to support 3- and 4-player counts. Playtest will tell us if the value justifies the complexity. |
| 4 | Do mechanics and theme reinforce each other? | ✅ Hunger/Sanity/Health, the Crockpot social magnet, Charlie attacks, and Telltale Heart sacrifice all are *consequences* of the world, not arbitrary rules. |
| 5 | At least 2–3 viable paths to victory? | ✅ Survive (default), Pristine, Truth, Hero — four overlapping goals (§16.2). |
| 6 | Different feel in early/mid/end game? | ✅ Jo-Ha-Kyu mapping (§14). Early days are exploratory; Day 5+ is climactic. |
| 7 | Stress-tested for runaway leader, kingmaking, AP, elimination? | ✅ Co-op (no runaway leader); ghost word-limit (no kingmaking); soft turn timer (AP); ghost state (no elimination). |
| 8 | Does player interaction generate stories? | ✅ Mismatched currency forces visible deals; the worked example in §11.6 shows the table-talk window naturally. |
| 9 | Has the rulebook been read by someone who wasn't in the room while you wrote it? | ❌ Pending — first blind playtest scheduled (§20.2). |
| 10 | Have you played it enough to be sick of it and still want to play again? | ❌ Pending — at the design-brief stage. The next milestone is to clear this. |

Two ❌ marks are acceptable at v1 (this document is the brief, not a finished game). Item 3's ⚠️ is the single most actionable note: the Visitor deck must justify itself in playtests or be cut.

---

## 20. Balancing, Playtest Plan, Expansion Hooks

### 20.1 Known balance risks

- **Coco's lack of house** — penalty is strong; if it's too punishing, allow her to "claim" a temporary home each game.
- **Rayman's loud movement penalty** — needs tuning; could make him underplayed if too harsh.
- **Doom track rate** — the +3/day in Phase 4 may be too steep at 3 players; consider scaling Doom rate by player count.
- **Hand limit (5 cards)** — may need to be 6 to allow comfortable crafting; playtest both.
- **Telltale Heart cost** — 2 Health from reviver is significant; if revival is too rare, lower to 1 Health.

### 20.2 Playtest plan

1. **Solo paper test** (designer + 2 hands) — verify the loop works mechanically, identify dead turns. 3 days only.
2. **3-player teach-and-play** — 3 days, then 7 days. Watch for analysis paralysis.
3. **5-player full game** — confirm the table doesn't get overwhelmed; check that 5 characters all feel relevant.
4. **Blind playtest** — give the rules to a group with no designer present; observe what they get wrong. Fix the rulebook accordingly.
5. **Stress test difficulty** — repeat plays with the same group to find the win rate (target: 40–50% on Standard difficulty for experienced groups).

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
