# Starve No More — Locations & Economy

> Part of the **Starve No More** design doc — [back to the index](../../StarveNoMoreDesignConcept.md).

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

For replayability without scripting more rules, the path graph is **modular**: at game setup, players may shuffle the path-edge cards (3 standard configurations: "Compact," "Sprawl," "Linear") to slightly vary the movement geometry. This is the lightweight Catan-variability lever from InterestingGames.md §2.3.1.

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

Players in the same location may trade resources, cards, or both **freely on either's turn**, with no action cost. This is the Catan negotiation layer (InterestingGames.md §2.3.8) — open, social, deal-driven. The constraint that they must be in the same location is the design lever that makes location-choice a social decision, not just a logistical one.

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

