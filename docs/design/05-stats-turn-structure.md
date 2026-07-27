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
- **Low Sanity (<3):** **Haunted.** At each Dawn, draw 1 Threat card at your location. It is real to you. Discard it once resolved (defeated or fled); it never festers on the Doom track, because it was never really there. (An earlier draft had a hidden-information hallucination rule — "only the affected player knows it's not real" — cut for being unrunnable at a physical table and unimplementable with the public-information model of §18.9. Haunted keeps the isolation horror with zero hidden state.)

  **Witness (the buy-in).** *An ally at your location may pay 1 Sanity to see what you see — and may then fight your Haunted threat alongside you.* Free, no action cost, once per ally per haunting.

  Haunted used to be absolute: only you could fight or flee it, because allies "cannot help with what they cannot see." As horror that is the best rule in the document. As co-op design it was the harshest: it stripped the cooperative layer from the one player who most needed it, at the worst moment, compounding daily — converting a struggling player into a *solo player inside a co-op game*. Per [§20](../../Archive/PrinciplesOfGoodBoardGames.md) — Cooperative Games Are a Different Genre — a player with a private unwinnable problem in a shared game is worse off than one who is simply behind. It also interacted badly with the Flee trap that §10.1.1 fixes: Haunted arrives at Sanity <3, and Flee was priced in Sanity.

  The buy-in preserves everything good about the rule and fixes what was wrong with it:

  - **The isolation horror survives.** Help is neither free nor automatic, and the helper *takes on the madness* to reach you.
  - **It is a textbook mismatched-currency trade** (§8.4), on the diagonal-*avoiding* side: you pay Sanity to solve someone else's Sanity problem.
  - **It restores agency to the table rather than to the haunted player**, which is the right place for it in a co-op — the decision becomes "who goes in after them," which is exactly the storied-collaboration beat §1.4 ranks third.
  - **It gives the haunted player something to negotiate about** instead of a private chore.

  It is priced in Sanity rather than in an action deliberately: pricing it in actions would make it compete with Fight, which is the very thing you are buying the right to do, and would turn a question about courage into a question about the action economy. The engine blocks the buy-in if it would put the witness Down — trading your own collapse for someone else's rescue is not a bargain the rule should offer silently. In the TTS build it appears in the **Reactions panel** (§18.13.1), because it must be available on the haunted player's turn, not only on the witness's own.

  *If it proves too generous* the alternative already on the balance list (§20.1) is to leave the isolation absolute and cap Haunted threats at 2 HP instead — cheaper, but it solves lethality rather than agency, which is the wrong one of the two.

### 10.1.1 Last Nerve (the individual death-spiral valve)

**While any of your stats is below 3: your Flee costs 0 Sanity, and your Rest restores 1 extra.**

That is the whole rule. It exists because all three threshold effects above are positive feedback pointed *downward* — the death spiral of [PrinciplesOfGoodBoardGames.md §21](../../Archive/PrinciplesOfGoodBoardGames.md) — Attrition and Negative Economies:

- Low Health → Movement costs +1 action → fewer effective actions → harder to reach food, allies, or safety → lower Health.
- Low Sanity → Haunted → you fight alone → you lose Sanity and Health → more Haunted draws.
- Hunger 0 → lose Health per Tick → see above.

The design had exactly one catch-up mechanism against that, and it is a good one: Doom 25's **Nothing Left to Lose** (§15.2). But it operates at the **team** level and triggers on the **shared** clock. An individual can spiral into irrelevance on Day 4 while the team's Doom sits comfortably at 12 — and receive nothing. §16.4 deliberately removed the one mechanism that made a Down character's plight the team's problem (the ghost Sanity drain), for good reasons; nothing replaced it on the way *down*. That leaves a player still at the table, still nominally playing, with no meaningful decisions left: the co-op form of player elimination ([§16](../../Archive/PrinciplesOfGoodBoardGames.md) — Pitfalls), and worse in a co-op than in a competitive game, because that player has no side left to root for.

The spiral was already **legible** — §1.4's "clever desperation" wants losses to read as a chain of visible mistakes, and a spiral is maximally visible. That defence holds for *fairness* and fails for *agency*. [§25](../../Archive/PrinciplesOfGoodBoardGames.md)'s audit asks three questions of every major negative event: could the player see it coming, could they have done something about it, could they name the decision afterward. The spiral scored two out of three, and the one it failed is the one that matters at the table.

Five properties make this the right shape:

- **It is the individual mirror of Doom 25**, using the design logic the team-level version already validated: catch-up that arrives as the *third act*, symmetric, and self-limiting — it switches off the instant you recover.
- **It cannot snowball.** It only ever triggers on a character who is nearly dead.
- **Mismatched currency is untouched** (§8.4): it changes prices, not directions. No row moves onto the diagonal.
- **It is thematically exact.** Adrenaline. Being cornered makes you run better.
- **It targets the specific trap.** Flee (§12.4) is the guaranteed-legal escape, and it costs 1 Sanity — so the escape hatch was priced in the currency most likely to be empty. A Sanity-2 character's only legal move used to cost a third of what they had left.

What it changes at the table: the calculus of Flee, of Rest, and of rescue priority. It adds no new component, no new phase, and no exception structure — it clears the §3 complexity bar on one sentence. **Balance watch (§20.1):** it softens the endgame, which must stay genuinely dangerous. Tune the magnitude down before cutting the rule — free Flee alone may be enough, and the Rest bonus is the half to drop first.

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

Detailed breakdown of a single round (one in-game day). In TTS, every step listed below is **prompted automatically by the Phase Banner** (§18.11) — the round walks itself, and a player who has never played can follow the on-screen prompts through all five phases. The design below is the rules for the table; the UX in §18.10–18.19 is how those rules become legible.

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

**Downtime: the cheapest cure first.** [PrinciplesOfGoodBoardGames.md §11](../../Archive/PrinciplesOfGoodBoardGames.md) — Turn Structure, Action Economy, and Downtime — lists four cures for waiting. The design was A/B-testing the two most disruptive (shorter turns, more of them — the Rotation variant below) and had never tried the cheapest: **decisions that occur on other players' turns.** It already had exactly one, free Trade (§8.2), and that one works. Two more now exist, both nearly free in rules cost:

1. **Luca's Rally fires on the recipient's turn** (§6.5). The orator acts *through* other people, so he is always partly engaged, and the gift arrives while the recipient can still spend it.
2. **The Haunted buy-in** (§10.1) is a decision any co-located ally can take at any point during the Day.

Both surface in the TTS build's **Reactions panel** (§18.13.1). Both should be measured *before* the Rotation A/B is decided, because they may reduce the problem Rotation exists to solve — and Rotation's acknowledged cost (fragmenting each player's 3-action plan) is a real one.

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

