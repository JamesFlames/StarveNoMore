# Starve No More — The Card Decks

> Part of the **Starve No More** design doc — [back to the index](../../StarveNoMoreDesignConcept.md).

## 9. The Card Decks

The game has five distinct decks. All are listed in §5; this section covers their content and design intent.

### 9.1 The Phase Decks (Dawn cards)

Four decks, played in order across the seven-day campaign:

- **Phase 1: Dusk of the Week** (15 cards) — Days 1–2. Mild events: minor sanity blips, lost items, weather — several carrying optional Dares.
- **Phase 2: Strange Days** (16 cards) — Days 3–4. Escalating threats: monsters glimpsed, food spoils, the Wrongness.
- **Phase 3: Long Nights** (16 cards) — Day 5. Boss event. Heavy disruption.
- **Phase 4: Final Hours** (15 cards) — Day 6 only draws from it; Day 7 is the fixed Last Dawn (§15.7). Survival sprint.

Each Dawn card has:
- A **flavor headline** ("The streetlights flicker. Something on the porch.")
- An **immediate effect** ("All players lose 1 Sanity.")
- Sometimes an **ongoing effect** ("Until the next Dawn, all gathers cost 1 extra Hunger.")
- Sometimes a **Dare** — an *optional* hook alongside the mandatory effect ("DARE: the first player to Gather at a house today may take 3 resources instead of 1 — and lose 2 Sanity from what they see through the window."). Roughly a third of the **Phase 1–2** cards carry one; the late-week decks stay lean and lethal. The world acting first (Pillar 3) is more interesting when it sometimes acts as a *tempter*, not only a mugger: each dare is a mismatched-currency gamble (§8.4) the table argues over, which is exactly the texture the quiet *Jo* days were missing. Dares are never imposed — scripted ones are offered via a confirm or opt-in behaviour (sleeping at the glowing court); the rest appear as optional checklist steps.

The Phase deck order is fixed, but card draw within a deck is shuffled — same shape, different details. (DST seasons principle: predictable structure, unpredictable details.)

### 9.2 The Market Deck (Item cards, "the Hogwarts deck")

A face-up market of 5 cards (a "shop" displayed on the table) drawn from a shuffled deck of 49 unique items. Players spend resources on their turn to **craft** an item — claim it from the market into their hand. A new card is drawn from the deck to refill the market slot.

Item categories:

- **Tools** (Flashlight, Crowbar, First Aid Kit, Bandage)
- **Weapons** (Improvised Bat, Sharpened Spoon, Slingshot, Toy Bow)
- **Comfort items** (Stuffed Animal, Photo Album, Music Player) — restore Sanity
- **Foods** (Cooked Stew, Energy Bar, Hot Cocoa) — restore Hunger
- **Special** (Telltale Heart for revival, Circle of Salt for boss combat)

Each item has a craft cost (resources), a use effect, and notes whether it's single-use or persistent. The market refresh creates the same "store rotation" energy as a deckbuilder's market row (InterestingGames.md §1.3).

### 9.3 The Recipe Cards

Permanent reference cards (not a draw deck) showing what can be cooked at a Crockpot. Examples:

- **Hot Stew** — 2 Provisions + 1 Wood. Restores 4 Hunger + 2 Sanity to all eaters.
- **Energy Drink Cocktail** — 2 Energy Drink + 1 Provisions. Restores 5 Sanity, 2 Hunger.
- **Comfort Soup** — 3 Provisions + 1 Cloth (for napkins). Restores 3 Hunger + 3 Sanity.
- **Battery Acid Soup** (don't) — 1 Battery + 2 Provisions. Restores 6 Hunger but loses 2 Health.

Recipes embody the **mismatched-currency** principle: cooking costs raw ingredients to produce more potent restoration than raw eating, but always with some trade-off (an action spent, a wood burned, a chance of bad outcomes for risky recipes).

### 9.4 The Threat Deck

51 cards, drawn during the Night phase based on each location's threat rate. Threat cards include:

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

The five-pip **severity dot** is the Catan-probability-dots pattern (InterestingGames.md §2.3.2) ported to event cards: at-a-glance signal of how punishing this Dawn will be, so players can read pressure visually without parsing rules text.

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
│ Ingredients: 2 Provisions + 1 Wood (fuel).         │
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

