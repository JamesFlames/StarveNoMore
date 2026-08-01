# Starve No More — Combat, Crafting & Cooking

> Part of the **Starve No More** design doc — [back to the index](../../StarveNoMoreDesignConcept.md).

## 12. Combat

Combat is **fast and dice-based** (InterestingGames.md §3.3.6). It has to be — combat happens often.

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
- Ingredients: 1 Cloth + 1 Battery + 1 Provisions.
- Cost: the cook pays 2 Health from their own track (the heart is *literally* part of them — the DST sacrifice mechanic, [DontStarveVideoGamePrinciples.md §7](../../Archive/DontStarveVideoGamePrinciples.md)).
- Yield: 1 Telltale Heart token, placed at the cook's location.

Telltale Hearts are the only way to revive a Down character (see §16.4). Carrying them is a strategic choice: they fill a tight inventory slot but they are the team's life insurance.

### 13.5 Pry and Sealed Things

**Pry** is a **free action**: a character holding a **Crowbar, Lockpick, or Pry Bar** may open a sealed thing at their tile and take its printed reward — guaranteed, no roll. Sealed things come in two forms:

- **Sealed Threat cards** (§9.4): drawn like any threat, but they don't fight — they wait. Each is a payoff for the team that invested in a tool.
- **The Sealed Basement** — a fixed object placed under Ellie & Luca's House **at setup, visible from turn one**. Behind it: a free Market Item plus a resource cache (2 Provisions + 1 Wood + 1 Battery). Because it is placed, not drawn, every game has it — the map's reliable early destination ("we need to get into the basement"), which makes crafting a Pry tool early a genuine plan instead of a rounding error. It is tuned to be worth a detour, never mandatory: a team can win ignoring it.

A guaranteed reward behind a tool gate is the cleanest excitement in the game: no randomness, a clear goal, a reason to specialise (clever desperation), and a shared objective the table organises around (storied collaboration). In the TTS build the verb is coded (`doPry`); the Pry button lights only when a sealed thing is co-located and the player holds a tool.

---

