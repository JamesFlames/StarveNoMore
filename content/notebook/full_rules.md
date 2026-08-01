# Starve No More — Full Rules (Abridged)

This is the in-game reference. The full design intent is in `StarveNoMoreDesignConcept.md`. Day-to-day play is driven by the on-screen Phase Banner and the Help menu (?); this Notebook is your fallback.

## Setup

1. Click **Setup Game** on the main board (or on the Host Controls panel, top-left).
2. Pick a path graph (Compact / Sprawl / Linear).
3. Optional variants (both off = standard game): **Rotation turns** and **Random Scenario** (see Variants below).
4. Each player picks a character. Read your one-time character briefing — that tells you what makes you different.
5. Day 1 begins. The Phase Banner takes over.

## Turn Structure

### Dawn
- Day Counter advances.
- Doom advances by phase rate (adjusted by player count, see Help → Doom), **plus +1 for each Threat still on the map** (festering, max +3), **plus +2 for each Boss / +1 for the Treeguard** (no cap).
- **Moonlit Salvage:** anyone who survived the night at a sport court gathers 2 resources, delivered to their board automatically at Dawn.
- **Dares:** some early-week Dawn cards carry an *optional* temptation alongside their effect — extra loot for extra risk. The card states the terms; take it or leave it.
- **The Wrongness:** one Dawn card places a face-down, unresolved Threat on the map. Enter its tile to resolve it — or it resolves itself at the next Dawn, where it stands.
- Reveal top of the active Phase deck. Apply effects.

### Day
Each player has **3 actions**, taken as one turn (default) — or, with the **Rotation turns variant**, you take 1 action and play passes to the next player, circling the table until everyone has used all 3 (pass after acting = keep the rest for your next go; pass without acting = forfeit them). Choose any:
- **Move (1)** — adjacent tile. Costs 1 Hunger. Rayman moves 2 spaces.
- **Gather (1)** — take 1 resource at this tile; it's delivered to your board automatically. At the Basketball Court you also roll the **Echoes** d6: 6 = a bonus Item, 1–2 = lose 1 Sanity.
- **Craft (1)** — buy an Item from the Market.
- **Cook (1)** — at a Crockpot, prepare a Recipe.
- **Fight (1)** — attack a Threat at this tile.
- **Rest (1)** — +1 Hunger or +2 Sanity. Own house: also +1 Health — and so does Rayman's House for anyone (the Garage).
- **Pry (free)** — with a Crowbar, Lockpick, or Pry Bar: open a sealed thing at your tile for its printed reward (sealed Threat cards; the Sealed Basement at Ellie & Luca's House).
- **Clear (2)** — pay 2 actions + 1 Wood to remove a **Persistent** threat that can be neither fought (0 HP) nor pried open. Its rule stops, and so does its +1 Doom every Dawn.
- **Cleanse (1)** — pay 1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink → Doom -2.
- **Trade (free)** — same tile, both consent.

### Dusk
Last chance to move: each character may **scramble 1 tile** (costs 1 Hunger, once per character), or stay. You sleep where you stand. Declarations are public — argue it out.

*Secret Dusk variant (off by default):* argue as normal, then commit your scramble privately. Everyone's move lands at once when Night begins, and the Hunger is charged then. Nobody can verify that you did what you said.

### Night
For each occupied tile, least-populated first:
- Draw threats per the location's threat rate (modified by Doom thresholds).
- Resolve combat or damage. Each drawn card is one of three kinds:
  - **Soft** — it does its printed thing once and is discarded. Nothing to fight.
  - **Hard** — it must be fought or fled. Left standing, it festers at Dawn. Read its Special: several charge Sanity for attacking them, hit the moment they arrive, tax the tile they stand on, or call in help when they die.
  - **Persistent** — it *stays on that tile* and its rule applies to everyone there until it is removed: Fight it if it has HP, Pry it if it is sealed, otherwise **Clear** it (2 actions + 1 Wood). It festers every Dawn it stands, so leaving one alone is a running Doom cost.
- Charlie check: no light source = **2 Sanity + 1 Health**. Each consecutive night in darkness, +1 to both. A night with light resets her.
- Storytelling: Comfort Items used here for shared Sanity gain.
- Sleep — a house sleeps **two** comfortably; each sleeper beyond the second gets the floor (no regen):
  - Own house: +1 Sanity, +1 Hunger, +1 Health.
  - Someone else's house with company: +1 Sanity.
  - Alone in a non-house: nothing (often worse) — but court survivors salvage 2 resources at Dawn.

### Tick
- Every character loses 1 Hunger and 1 Sanity.
- Rayman loses 2 Hunger.
- Coco's allies lose 1 less Sanity here. Luca's allies gain +1 Sanity. Ellie's house gains +1 Sanity.
- Pass First Player.
- Check victory/defeat.

## Combat

- Attacker rolls dice = base attack + weapon + modifiers.
- Each 5 or 6 = 1 hit (1 damage to enemy).
- Fumble: a 1 costs 1 Health **only if the roll had no hits** (max 1 per roll).
- **Press the Attack:** landed a hit? You may pay **1 Sanity** to roll one bonus die — 5–6 deals 1 more damage and you may press again; 1–4 ends the streak. Press dice never fumble. The enemy doesn't strike back until you stop. Pressing can drop you to 0 Sanity — you go Lost, mid-fight.
- When you stop (or whiff), the enemy attacks back: roll its attack dice; each 5–6 = 1 damage.
- Group combat sums dice; return damage rotates highest-Health first. Each fighter may press, paying their own Sanity.
- **Flee** (always legal, even starving): move 1 tile away, pay 1 Sanity. The threat stays — and festers at Dawn. **Free** while you are on your Last Nerve (see below).
- **Last Nerve:** while *any* of your stats is below 3, your Flee costs no Sanity and your Rest restores 1 extra. It switches off the moment you recover. Being cornered makes you run better.
- **Boss kills pay out:** Deerclops **Doom −2**, Eye of Terror **Doom −3**, plus 3 resources spill at the tile and the boss's Trophy (a unique team power).
- **Signature Moves:** every character has one once-per-game named move (see the Character Reference tab) — fired from the Signature button, each paying an off-stat cost.
- **The Source splits:** the final boss's HP is script-tracked; the first time it drops to 5 HP or below, two Terror Beaks peel off to adjacent tiles (ordinary threats — they fight, flee, and fester normally).

## The Treeguard (Phase 2.5)

At Dusk of Day 4 — every game — a Treeguard (HP 5, Atk 2) wakes at a random sport court. While it stands, no one may Gather at its court, and it festers Doom +1 each Dawn. Fight it (defeat: +1 Sanity each, salvage 3 Wood) or appease it (1 action + 2 Wood at its tile — it sleeps, no reward).

## Death and Revival

- Health 0 = Down. Sanity 0 = Lost (also Down).
- Going Down feeds the dark: **Doom +1**.
- Flip standee to ghost. Cannot act. Drifts 1 tile per round. May whisper one word per round.
- To revive: a Telltale Heart token (cooked at the Crockpot for 1 Cloth + 1 Battery + 1 Provisions + 2 Health from the cook).
- Revived character returns at half maximums.

## Doom

The Doom track runs 0–30. At 30, the team loses. It advances each Dawn by the phase rate, +1 per festering threat left on the map (max +3), +2 per boss / +1 for the Treeguard (no cap — bosses charge interest every Dawn they stand), and +1 whenever a character goes Down. Thresholds:
- 10: night threats +1
- 15: Scarcity — crafts cost +1 extra resource (your choice of type)
- 20: all -1 Sanity at Tick
- 25: **Nothing Left to Lose** — everyone gets +1 attack die, and Rest heals +1 Health anywhere (non-stacking with the at-home bonus). Go down swinging.
- 30: defeat

Push back Doom by Cleansing — or by killing a phase boss (Deerclops −2, Eye −3).

## Victory

At the end of Day 7: **at least one character still standing**, Doom under 30, **and The Source destroyed**. If the final boss still stands at the end of Day 7, the team loses, whatever the Doom track says.

You can win with most of the team in the ghost state — that is deliberate, not a loophole. Bringing everyone through instead is the Pristine Run.

Day 7 opens on **The Last Dawn** — a fixed Dawn with no penalty ("the sky is trying to lighten; survive until it's over"). No card is drawn.

Bonus achievements:
- **Pristine** — every character in play still standing, nobody revived.
- **Truth** — 3 Clue cards collected. One is behind the Sealed Basement; the Market surfaces the others as the week goes on; James can pull one he peeks. Not a lottery — plan for it.
- **Hero** — defeat all 3 phase bosses (Deerclops, Eye of Terror, The Source).

## Variants (optional, chosen at setup)

- **Rotation turns** — changes how Day turns are dealt out. Standard: on your turn you take all 3 of your actions, then the next player goes. Rotation: you take just 1 action and play passes to the next player, going around the table until everyone has used all 3 — shorter waits between your decisions at 4–5 players. Pass after acting keeps your remaining actions for your next go; pass without acting forfeits them.
- **Random Scenario** — one week-long twist revealed at setup and shown in the "Rules in effect" panel all game: The Long Winter (hunger is brutal), The Scorching Summer, The Rotting Autumn, The False Spring, Total Blackout (Fire is the only light), Strict Rationing, The Full Moon (no Charlie, harder threats), The Shortcut. Recommended after your first game.
