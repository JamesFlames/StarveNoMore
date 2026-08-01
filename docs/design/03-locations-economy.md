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

- **Yield.** Energy Drink ×1 per gather, Battery ×1 per two gathers, Junk Food (Provisions) ×1.
- **Special: The Den.** Players in this location may freely trade cards with each other once per day (no action cost).
- **Special: The Stash.** A Gather action here may take **2 Energy Drinks** instead of the normal random draw. This exists so James's Wired constraint is a logistics problem (stock up every other day), not a daily ritual that eats a third of his action budget.
- **Sanity modifier:** 0 (familiar but cluttered).
- **Defense:** +0.
- **House owner:** James gains +1 Sanity per night when sleeping at his own house.

### 7.2 Rayman's House

- **Yield.** Sports Equipment (improvised weapons; see §13), Sports Drink (Provisions), Athletic Tape (crafting).
- **Special: The Garage.** A Rest action here restores +1 Health (instead of +0).
- **Sanity modifier:** 0.
- **Defense:** +1 (lots of cover).
- **House owner:** Rayman gains +1 Health per night when sleeping at his own house.

### 7.3 Ellie & Luca's House

- **Yield.** Cooking Ingredients (Provisions), Cloth, Pantry items.
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
| **Provisions** | Red apple icon | All locations (esp. Ellie & Luca's, James's House) | Restore Hunger; cook into recipes for greater effect |
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
| **Eat uncooked food** | Hunger (1) | Sanity (−1) — DST raw-food penalty. |
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

### 8.5 The daily ledger (the maintenance tax)

§8.4 audits the *direction* of every restorative action. It never states the *magnitude* — and in an attrition design the guaranteed per-day drain against the realistic per-day restoration is the single most important number there is ([PrinciplesOfGoodBoardGames.md §21](../../Archive/PrinciplesOfGoodBoardGames.md) — Attrition and Negative Economies). It is also the number most often left implicit, which is how attrition games end up either trivial or unwinnable without anyone able to say which knob did it. So it is written down here, as a **stated target**, not a derived curiosity.

**The guaranteed drain, per character, per day:**

| Source | Cost | Certainty |
|---|---|---|
| Tick (§11.5) | −1 Hunger, −1 Sanity | Every day, unavoidable |
| Each Move (§11.2) | −1 Hunger | Per action taken |
| Dusk scramble, if taken (§11.3) | −1 Hunger | Optional |
| Sleeping at a court (§7.4/7.5) | −1 Sanity (location modifier) | Positional |
| First dark night — Charlie (§15.4) | −2 Sanity, −1 Health, escalating +1/+1 per consecutive night | Avoidable with light |
| Rayman's Big Appetite (§6.3) | −1 Hunger more | Character-specific |
| Doom 20 threshold (§15.2) | −1 Sanity more at Tick | Late-week, world-wide |

**The realistic restoration, per action spent:**

| Spend | Restores |
|---|---|
| Rest (1 action) | +2 Sanity **or** +1 Hunger; +1 Health at your own house |
| Sleeping in your own bed (free) | +1 Sanity, +1 Hunger, +1 Health |
| Sleeping in someone else's bed with company (free) | +1 Sanity |
| Eat uncooked food (free-ish) | +1 Hunger, −1 Sanity |
| A cooked recipe (1 action, shared) | +3 to +6 Hunger and +1 to +2 Sanity, **per character at the tile** |

**The resulting tax.** For a character solving their own upkeep alone, in their own bed: the bed covers the Tick's Sanity and Hunger exactly, and every Move, scramble, court night or dark night is unfunded. Once you actually play the map — one Move a day is the minimum for a team that isn't turtling — the ledger runs roughly:

- **Sanity: ~0.5 actions/day to maintain.** One Rest (+2) covers two days of Tick loss on its own.
- **Hunger: ~1.0 actions/day to maintain.** One Rest is +1, which is exactly one day of Tick — and it does not pay for the Move that got you anywhere.

**Target: a ~50% maintenance tax on a 3-action budget** for the self-sufficient player. That is the design's stated intent, and it is what makes the game a spending problem rather than an execution problem.

**The cooperation dividend, stated.** Recompute for a co-located team that cooks. Cooking is multiplicative (§13.2 — one player cooks, many benefit), so one action spent at the Crockpot pays a recipe's Hunger and Sanity to *everyone at the tile*. At four co-located characters, a single Hot Stew is ~4 Hunger and ~2 Sanity × 4 bodies for one action and 2 Provisions + 1 Wood — the Hunger side of the tax collapses from ~1.0 actions/character/day to well under 0.3, and Ellie's Crockpot Master and Comfort Food perks push it lower still.

That is the whole economic argument for cooperating, and it deserves to be stated rather than discovered: **the Crockpot is not merely a social magnet, it is the tax-reduction engine.** The incentive to gather at Ellie & Luca's kitchen is arithmetic, not thematic — which is exactly the property a co-op economy needs, because a purely thematic incentive is one an optimizing table will ignore.

**Why this is a regression check, not documentation.** Every future tuning knob moves this number: Charlie escalation, Big Appetite, the Tick, recipe yields, the Doom 20 threshold, the Last Nerve valve (§10.1). Before this section existed, nothing in the repo would have noticed a change that halved or doubled the maintenance tax. `scripts/simulate_balance.py` already carries the machinery to measure it — the figures above are the band it should keep reproducing, and a tuning change that moves the tax outside roughly 0.4–0.7 actions/character/day is a change to the *genre* of the game, not to its difficulty.

---

