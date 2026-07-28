# Character Briefings

**This file is the source of the in-game text.** `scripts/generate_character_briefings.py`
turns it into `lua/character_briefings.lua` (`CHAR_BRIEFINGS`), which the Setup
walkthrough shows once to each player after they pick (Step 3, Design §18.16),
and which also serves as the pick-card hover tooltip. Editing this file and
rerunning `python scripts/check.py` is the only way to change that text — a
freshness test fails if the two drift.

**Keep it short.** The briefing panel is 560×480 with a 352px body at font size
13 (`xml/setup.xml`), and the text must fit on one screen without scrolling.
This is the elevator pitch, not the manual: the full mechanical detail for each
character lives in [`../notebook/character_reference.md`](../notebook/character_reference.md),
which feeds the in-game Notebook and the player rulebook.

## Format

Each character is one `##` section, and the parser is strict about the shape:

- `**You are <Name>, the <Role>.**` — the opening line.
- A plain paragraph of flavour.
- `**Strengths**` or `**Constraint**` / `**Constraints**`, each followed by
  `- Name: text` bullets.
- `**Starting hand:** ...`
- `**First move:** ...`

The bold section labels are re-styled in the dialog by `formatBriefingBody`
(`lua/ui_setup.lua`), so do not add rich-text tags here — they would render
literally in the tooltip.

---

## James

**You are James, the Gamer.**

You know patterns. You see things before they happen. Home: James's House, where Energy Drinks and Batteries are plentiful.

**Strengths**
- Gaming Reflexes: once per turn, reroll one die.
- Pattern Recognition: once per day, peek any deck top.

**Constraint**
- Wired: consume 1 Energy Drink per day or lose 2 Sanity at night.

**Starting hand:** Energy Drink x2, Pocketknife, Flashlight, Headphones.

**First move:** Gather at home — The Stash lets you take 2 Energy Drinks at once. Stock up, then use Pattern Recognition to peek at the Phase deck.

---

## Coco

**You are Coco, the Angel.**

You are calm when the world isn't. You're visiting — no house of your own.

**Strengths**
- Calming Presence: allies at your tile lose 1 less Sanity at Tick.
- Touch of Hope (once per game): heal any character +4 Health.
- Light in the Dark: never triggers Charlie attacks.
- Wanderer's Gift: gain +1 Sanity each time you move to a new location.

**Constraint**
- No Home: alone at a non-house tile at night = -3 Sanity.

**Starting hand:** First Aid Kit, Comfort Blanket, Hopeful Tea, Spare Phone Battery, Friendship Bracelet.

**First move:** Keep moving — your Gift rewards travel. Stick with allies at night.

---

## Rayman

**You are Rayman, the Basketball Player.**

Fastest and toughest. You hit hard. You also eat a lot.

**Strengths**
- Speed: Move 2 tiles per Move action.
- Court Master: +1 attack die at the Basketball Court.
- Backboard Block: Defend action shields adjacent allies.

**Constraints**
- Big Appetite: lose 2 Hunger per Tick (others lose 1).
- Loud: if you moved at all today, wherever you spend the Night draws +1 Threat. A quiet day keeps the dark away.

**Starting hand:** Basketball, Sports Drink x2, Athletic Tape, Whistle.

**First move:** Head to the Basketball Court for Wood. Watch your Hunger.

---

## Ellie

**You are Ellie, the Cook.**

The kitchen is your domain. You feed the team.

**Strengths**
- Crockpot Master: recipes need 1 fewer ingredient (min 1).
- Comfort Food: shared meals give +1 extra Hunger and Sanity.
- Knows the Pantry: at your house, pick a specific resource.

**Constraint**
- Particular Eater: cannot eat raw food. Must cook first.

**Starting hand:** Crockpot, Soup Recipe, Cooking Knife, Pantry Key, Apron.

**First move:** Gather Food with Knows the Pantry, then cook Hot Stew for the team.

---

## Luca

**You are Luca, the Orator.**

Your words hold Sanity together when everything else falls apart.

**Strengths**
- Rally: once per turn, give an adjacent ally a free action.
- Calm Words: on Sanity-loss events at your tile, d6 — 4+ negates it.
- Storyteller: allies at your tile gain +1 Sanity at Night.

**Constraint**
- Needs an Audience: Sanity doesn't regen when alone.

**Starting hand:** Notebook, Loud Whistle, Pep Talk, Reading Lamp, Toolbox.

**First move:** Use Rally to give Ellie a free action. Stay with allies.
