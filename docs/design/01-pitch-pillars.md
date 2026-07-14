# Starve No More — Pitch, Pillars, Audience & Core Loop

> Part of the **Starve No More** design doc — [back to the index](../../StarveNoMoreDesignConcept.md).

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

Working backwards through the MDA framework ([PrinciplesOfGoodBoardGames.md §1](../../Archive/PrinciplesOfGoodBoardGames.md)) — mechanics produce dynamics produce *aesthetics*. The aesthetics this game targets, ranked by priority:

1. **Cozy dread.** The single emotion the game is built around. The kitchen with friends, the thing in the basement. If a rule makes the table feel like neither cozy nor dreadful, it's wrong.
2. **Clever desperation.** Players survive by being smart, not by being lucky. Wins should feel earned, even close ones. Losses should feel like a chain of small visible mistakes — never unfair.
3. **Storied collaboration.** Every play should produce one moment the table will retell. "Remember when Rayman went out alone." "Remember the night Ellie cooked the last Battery Acid Soup." Stories are the replayability engine.
4. **Personal asymmetry.** Each character should *feel* different to play, not just have different numbers. A James player and an Ellie player should describe their game in different language at the end of the night.

If a candidate rule does not clearly serve at least one of (1)–(4), it does not earn its place in the rulebook.

---

## 2. Design Pillars

The five non-negotiable principles that all rules decisions must serve. Drawn from the Don't Starve translation work in [DontStarveVideoGamePrinciples.md](../../Archive/DontStarveVideoGamePrinciples.md) and the design theory in [PrinciplesOfGoodBoardGames.md](../../Archive/PrinciplesOfGoodBoardGames.md).

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

