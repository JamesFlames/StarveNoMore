# Starve No More — Stats & Turn Structure

> Part of the **Starve No More** design doc — [back to the index](../../StarveNoMoreDesignConcept.md).

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
3. **Charlie check.** Any player whose location has no light source (no Flashlight, no Fire, no Battery-powered item) suffers a "Charlie attack" — **2 Sanity and 1 Health**. For each consecutive night a character spends in darkness, Charlie grows bolder: **+1 Sanity and +1 Health more than the night before**. A night with light resets her interest. (DST night-darkness translation; see [DontStarveVideoGamePrinciples.md §4](../../Archive/DontStarveVideoGamePrinciples.md). Deterministic on purpose: a first slip is survivable and legible — *the world's rules*, not a die spike — but darkness as a habit is lethal.)
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

