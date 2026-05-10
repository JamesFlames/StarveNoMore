# Interesting Games: A Mechanical Tear-Down for Designers

A systematic look at three commercially successful, mechanically distinctive board games — broken down so a designer (human or agent) can isolate reusable patterns, identify what each game does *uniquely well*, and spot opportunities to remix elements into a new design.

The three games covered:

1. **Harry Potter: Hogwarts Battle** — a cooperative deck-builder with progressive difficulty across seven boxes.
2. **The Settlers of Catan** — the canonical resource-trading, network-building Eurogame.
3. **Cthulhu Wars** — an asymmetric area-control war game with deeply differentiated factions.

For each game this document covers:
- **Core identity** — what the game is, in one paragraph.
- **The play loop** — what a turn actually feels like.
- **Key mechanical systems** — broken down individually.
- **Notable design patterns** — patterns worth lifting.
- **Pitfalls and trade-offs** — what each design costs.
- **Reusable elements** — explicit, transplantable ideas.

A final synthesis section identifies cross-cutting patterns and remix opportunities.

---

# Part 1: Harry Potter: Hogwarts Battle

**Designers:** Kami Mandell, Andrew Wolf  
**Publisher:** USAopoly / The Op (2016)  
**Players:** 2–4 (cooperative)  
**Time:** 30 min (early games) → 2 hours (late games)  
**Category:** Cooperative deck-builder with campaign progression

---

## 1.1 Core Identity

Hogwarts Battle (HPHB) is a **cooperative deck-builder** packaged as a **seven-box campaign** that escalates across the Harry Potter book series. Players take on Harry, Ron, Hermione, or Neville, each starting with their own pre-built mini-deck. They face a shared villain row, a randomized "Dark Arts" event each turn, and a sequence of locations that the villains progressively corrupt. Lose all locations → players lose. Defeat all villains → players win.

The genius of the design is that each successive box (Year 1 through Year 7) **opens a sealed envelope of new cards and rules** that permanently expand the game. The mechanics ramp from "introductory deck-builder" in Year 1 to "complex tactical puzzle" by Year 7, mirroring the increasing darkness of the source material.

**The hook:** "Dominion meets a campaign," with a beloved IP doing the heavy lifting on theme.

---

## 1.2 The Play Loop

A single turn for an active player is:

1. **Reveal Dark Arts.** Flip cards from the Dark Arts event deck equal to the count specified by the current villain(s). Resolve each immediately — these are bad things happening to the team.
2. **Resolve Villain abilities.** Each active villain has a passive or triggered effect. Some hit the active player; some hit everyone.
3. **Play Hogwarts cards.** The active player plays cards from their hand, generating two currencies:
   - **Influence** — used to buy new cards from the central market.
   - **Attack** — used to damage villains.
   - Some cards also generate Health (heals) or special effects.
4. **Spend.** Buy cards from the market (they go to your discard), and/or assign Attack to villains.
5. **Cleanup.** When a villain reaches zero HP, defeat it (rewards! a new villain replaces it). When you finish, discard your hand and draw 5.
6. **Add a control token to the active location.** When the location's threshold is hit, it flips — adding setbacks and pushing toward defeat.

What makes this loop interesting is that **every turn the world acts before you do**. The Dark Arts deck guarantees pressure, regardless of how well you played last turn. The villain row guarantees ongoing menace. You are always reacting and building simultaneously.

---

## 1.3 Key Mechanical Systems

### 1.3.1 Personal asymmetric starting decks

Each of the four heroes starts with the same *size* deck (10 cards) but with **different starting compositions** themed to that character:
- Harry has Invisibility Cloak (lets him take an extra action).
- Hermione has the Time-Turner (gain extra Influence).
- Ron has more Attack-oriented cards.
- Neville has a healing-focused deck.

The asymmetry is small but felt. It's enough to give players a role identity from turn one without requiring deep balance work — because the starting decks are all weaker than the cards in the market, the asymmetry erodes naturally as the deck evolves.

### 1.3.2 Three card types in the market: Spells, Allies, Items

The market (the "Hogwarts" deck) has three card types, with mechanically meaningful differences:
- **Spells** — single-use effects, trigger and go to discard.
- **Allies** — single-use, but typically more powerful (they "leave" in fiction; mechanically identical to spells).
- **Items** — same, but a few have ongoing effects.

This subdivision exists more for **theme** than for mechanical depth — but it does serve the purpose of letting iconic objects (the Sword of Gryffindor, the Marauder's Map, Hedwig) feel categorically distinct on the table.

### 1.3.3 The Dark Arts deck — automated antagonist

The Dark Arts deck is the engine of the game's pressure. Every turn it fires off random bad effects:
- "Lose 1 Health."
- "Discard a card."
- "Add a control token to the location."
- "All players lose 1 Health."

Crucially: villains *modify* how the Dark Arts deck fires. Some villains say "reveal an extra Dark Arts card per turn." This stacks pressure on the team without requiring an AI.

### 1.3.4 The villain row and shared HP pool

Up to three villains are out at any time. Each has hit points and an ability. Defeating one rewards the team and reveals the next. The villain row acts as a public objective and a public threat simultaneously — a clear "here is the boss; here is what they're doing to you."

Some villains can only be hit by certain cards or types of attack, forcing players to rotate which villain to focus.

### 1.3.5 Locations as a doom track

Locations are the team's loss condition. Each has a threshold (e.g., "4 control tokens here"). Dark Arts events and villain abilities place control tokens on the active location. When a location flips, it's gone — the game proceeds to the next one, but with the cumulative penalty that locations getting flipped is *how the team loses*.

This is mechanically the equivalent of a doom track (see Cthulhu Wars), but inverted — the doom is *against* the players. Smart design choice: the tokens accumulate visibly. Players can see disaster approaching.

### 1.3.6 The "envelope" campaign progression

The seven boxes are sealed when shipped. After completing a year, players physically open the next box and add its contents. Each box adds:
- New villains (added permanently to the villain stack going forward).
- New Hogwarts cards (added permanently to the market).
- New rules (sometimes minor — "Dark Arts now deals double damage in this Year"; sometimes substantial — Year 4 introduces the **Horcrux** mechanic).

Critically: **the game is reset-able.** Unlike a true legacy game (Pandemic Legacy, Risk Legacy), HPHB doesn't destroy components. New players can play through Year 1 without "spoiling" the box.

This is a hybrid design — campaign progression *without* permanent state — and it's one of the most reusable patterns in modern board game design. It captures most of legacy's emotional beats (anticipation, revelation, escalation) without legacy's hardest cost (one-shot components).

### 1.3.7 Difficulty scaling through accumulation

Year 7 is hard not because the rules are radically different, but because **everything from Years 1–6 is still in the box**. The Dark Arts deck is now thick. The villain stack is now huge. The market has dozens of options. Difficulty emerges from accumulated content, not from new sub-systems.

This is an elegant solution to escalating difficulty: don't redesign the game, just add more of it.

---

## 1.4 Notable Design Patterns

### Pattern: "Pressure-first" turn structure

Every player turn begins with the *world* acting. Dark Arts triggers before you play a card. This guarantees:
- No turn feels safe.
- Even a powerful deck can have a bad turn.
- The threat is always visible, never deferred.

Compare to many deckbuilders where the player builds their engine in peace until the boss fight at the end. HPHB collapses build-and-fight into every turn.

### Pattern: Dual-purpose cards

Most Hogwarts cards generate *both* Influence and Attack, in varying ratios. This means:
- Every turn presents a budget decision: spend on the present (kill a villain) or invest in the future (buy a better card)?
- The trade-off is permanent and self-correcting: too much investment = you lose to villains; too much present = you never improve.

A clean version of the "engine vs. action" tension.

### Pattern: Staggered information release across a campaign

By sealing later boxes, the designers create:
- A reason to come back. Even a satisfying win at Year 3 leaves Year 4 unopened.
- Anticipation. Players talk about what might be inside.
- Manageable rules complexity. Year 1's rulebook is simple; Year 7's is dense, but the player has been onboarded across hours of play.

This is the "tutorial as a campaign" pattern — and HPHB does it almost as well as a video game.

### Pattern: The IP is doing free design work

When you defeat a villain, the moment hits because you remember Quirrell from the books. When the Basilisk shows up, you don't need a flavor card to tell you it's scary. **The thematic work is outsourced to the player's prior emotional investment.** A non-IP game doing the same job has to build that resonance from scratch.

This is often a luxury, but designers can lean on shared cultural narratives even without a license — folk tales, public-domain mythology, archetypes the player already knows.

---

## 1.5 Pitfalls and Trade-Offs

- **Solvable in late game.** Once a strategy is found for Year 7, the optional difficulty modifiers (the Monster Box expansion adds them) are needed to keep it interesting.
- **Random Dark Arts can feel unfair.** A bad sequence of Dark Arts cards can lose a game on the first turn. The design accepts this; some players don't.
- **Alpha player problem.** All hands are open. Optimal play is computable. One experienced player can drive the table.
- **Turn time scales badly.** By Year 7, with thick decks, lots of card text, and complex villain interactions, turns become long.
- **The IP cuts both ways.** It carries the early game; it ages with the audience.

---

## 1.6 Reusable Elements (Explicit List)

A designer raiding HPHB for parts could lift any of these:

1. **The campaign-in-a-box pattern.** Sealed envelopes that unlock new mechanics across multiple play sessions, with reset-ability preserved.
2. **The "world acts first" turn structure.** Every turn opens with a forced random event from an antagonist deck.
3. **The doom-against-the-players track** (locations as failure timer, accumulating tokens).
4. **Dual-currency cards.** A single card generating two resource types in varying ratios, forcing budget decisions on play.
5. **Asymmetric starting hands** without asymmetric rules — a cheap way to give players role identity.
6. **Difficulty by accumulation.** Add content boxes that expand the existing deck, rather than redesigning the rules each tier.
7. **A villain row of 1–3 active threats**, each with HP and a passive ability, replaced from a stack on defeat.
8. **Categorical card subtypes** (Spells/Allies/Items) used primarily for theme but allowing for type-restricted effects when wanted.

---

# Part 2: The Settlers of Catan

**Designer:** Klaus Teuber  
**Publisher:** Kosmos / Catan Studio (1995)  
**Players:** 3–4 (base game; up to 6 with extension)  
**Time:** 60–90 minutes  
**Category:** Resource management, network-building, trading Eurogame

---

## 2.1 Core Identity

Catan is the canonical "gateway Eurogame" — the title that introduced an entire generation of players to designer board games. Its core systems have been imitated by dozens of successors. With 40+ million copies sold, it is one of the best-selling tabletop games of all time.

The game is about **settling an island**. Players place settlements at hex intersections, gather resources from adjacent hexes when their dice numbers come up, trade resources with each other, and spend resources to build roads, more settlements, cities, and development cards. First player to 10 victory points wins.

What makes Catan distinct from prior territorial games (Risk, Monopoly) is that **it is impossible to play without other players**. Trade is structural, not optional. The game mechanically forces interaction.

---

## 2.2 The Play Loop

A turn:

1. **Roll 2d6.** The number rolled triggers all hexes labeled with that number to produce. Every player with a settlement adjacent to a producing hex gets one of that resource (a city gets two). Note: production happens for *all* players simultaneously, not just the active one.
2. **(If 7 is rolled)** Special "robber" rules trigger — see below.
3. **Trade.** The active player can propose trades with any other player. Negotiation is open and verbal. Players can also use ports to trade with the bank at favorable rates.
4. **Build.** Spend resource cards to construct: roads, settlements, cities, or development cards.
5. **End turn.** Pass dice to the next player.

The most important thing about this loop is **everyone is engaged on every roll.** Even on someone else's turn, you might gain resources, lose resources to the robber, or be propositioned for a trade. There is no downtime.

---

## 2.3 Key Mechanical Systems

### 2.3.1 Variable hex board

The board is built from 19 hex tiles randomly arranged at the start of each game. Number tokens (2 through 12, except 7) are placed onto each hex. Two starting positions:
- **Beginner setup**: a fixed, balanced layout.
- **Variable setup**: tiles and numbers scrambled randomly.

This single design choice — variable setup — produces enormous replayability with zero additional rules. Each game presents a different geography of resources, different scarcities, different optimal placements.

### 2.3.2 The dice probability curve

2d6 produces a triangular distribution. Numbers 6 and 8 are the most common (5/36 each). 2 and 12 are the rarest (1/36 each). The numbers on the hexes are decorated with dots indicating their relative probability — a player-facing affordance that makes the math visible.

This is brilliant **scaffolded learning**. New players can read the dots and understand "more dots = better" without needing to compute probabilities. Experienced players know what the dots represent and use them analytically. The same component teaches at two different skill levels.

### 2.3.3 Five resources, asymmetric demand

Catan has five resources: **wood, brick, wheat, sheep, ore**. Building costs:
- Road = wood + brick
- Settlement = wood + brick + wheat + sheep
- City = 3 ore + 2 wheat (replaces a settlement)
- Development card = ore + wheat + sheep

This produces interesting demand curves. Wheat is in *every* recipe. Ore is needed only for cities and development cards (but in large quantities). Sheep is the "lightest" resource, often least valuable. Wood and brick are paired (road economy).

The demand asymmetry means **trade is essential**. No starting position covers all five resources well. Players must trade — and the relative scarcity of each resource on a given board fluctuates by what numbers came up that turn.

### 2.3.4 Settlement placement: the most important decision

The game effectively begins with two placement decisions per player. Each player places one settlement and one road, then in reverse order each player places a second settlement and road, **and immediately collects one resource per hex adjacent to that second settlement.**

Because settlement placement is permanent and frontloaded, the game is **partially decided before any dice are rolled.** Good placement = good production. Good production = exponential advantage. This creates enormous opening-game depth — a literature of Catan opening theory exists.

The reverse-order placement (snake draft) is a balance fix: the player going last gets last *and* first pick of the second settlement, partially compensating for late starting position.

### 2.3.5 The Robber and the 7 mechanic

When a 7 is rolled (the most common single roll, 6/36):
- All players holding 8+ resource cards must discard half (rounded down).
- The active player moves the **Robber** to any hex.
- That hex stops producing until the Robber is moved again.
- The active player steals one random card from any opponent with a settlement adjacent to that hex.

The 7 is the game's central "interesting" event. It creates:
- **A hand-size cap** that punishes hoarding (forcing trades).
- **A blocking tool** — players can park the Robber on an opponent's best hex.
- **A direct conflict point** — choosing which opponent to hurt is socially loaded.
- **A randomness shock** — your great economy can have a hex shut off for several turns.

The Robber is also movable via Knight development cards, making the conflict surface always-on.

### 2.3.6 Roads, cities, and the longest road

Roads cost wood + brick and serve two purposes:
1. They enable expansion — settlements can only be built on the end of roads.
2. The player with the longest unbroken road of 5+ length earns a 2-point bonus that can flip between players.

Roads are mechanically a network-building game inside the resource-management game. The longest-road bonus is a moveable target — players will spend resources to extend or break each others' roads.

### 2.3.7 Development cards

A separate stack of "Development Cards" can be purchased for ore + wheat + sheep. Mostly Knights (movers of the Robber), with a sprinkle of:
- Victory point cards (hidden — direct VP).
- Road Building (free roads).
- Year of Plenty (free resources).
- Monopoly (steal one resource type from all players).

The development deck adds:
- **Hidden information** (you don't know what others have).
- **Variance** in late-game scoring.
- **A "third path" alternative** to building when the resources you have don't fit a normal build.

### 2.3.8 Trading: the social heart of the game

On your turn, you can propose any trade with any other player. "I'll give you 2 sheep for 1 ore." Trades are open negotiation — players can demand more, offer less, refuse. There's also a 4:1 trade-with-the-bank fallback, and 3:1 or 2:1 ports for players whose settlements touch them.

This is the mechanical innovation that defined Catan. Trading is:
- **Public.** Everyone knows what's offered.
- **Combinatorial.** Multi-resource trades quickly explode into complex deal-making.
- **Self-balancing.** Players naturally avoid trading with the leader, providing organic catch-up.
- **The source of stories.** Long-after-the-game memories are about deals made, refused, betrayed.

### 2.3.9 Multiple paths to victory

10 victory points come from:
- Settlements (1 each, max 5) = up to 5
- Cities (2 each, max 4) = up to 8
- Longest Road = 2
- Largest Army (3+ Knights played) = 2
- Victory Point development cards = up to 5

There's no single recipe. A "city heavy" build leans on ore/wheat. A "road network" build prioritizes longest road and many cheap settlements. A "development card" build hides VP and gambles on the deck.

This multiplicity is a major replayability driver. The right path varies by board, by opponents, by what resources are produced.

---

## 2.4 Notable Design Patterns

### Pattern: Production while idle

Resources arrive on every dice roll, not just on your turn. This eliminates downtime — players are mentally engaged on opponents' turns, watching dice and counting cards. Cleanup is ambient.

### Pattern: Built-in catch-up via trade

Catan has *no explicit catch-up mechanic*. But trade naturally provides one: the leader is the player others refuse to trade with. The trailing players form informal coalitions. The result is a soft, social, self-balancing system that requires no special rules.

### Pattern: Two-phase setup as a strategic mini-game

The drafted placement of starting settlements is itself a deep, interesting game. Many players consider it the most important decision in Catan. This pattern — placing critical permanent things at the start — is reusable: it creates an opening-game structure that experienced players love, and a clean entry point for new players.

### Pattern: Component-as-tutorial (the dot system)

Probability dots on number tokens are a tiny piece of design that does enormous work — teaching probability without ever saying the word. Components that visually convey strategic information are a powerful pattern.

### Pattern: Always-relevant negotiation

Trade is not an action that happens *occasionally* — it happens on every active player's turn. The constant social interaction is what makes Catan replayable in a way that purely mechanical games are not.

### Pattern: Adjacency as the universal interaction

Hex adjacency does enormous work in Catan. It defines:
- Production (settlements adjacent to hex).
- Blocking (Robber adjacent to settlement).
- Stealing (Robber adjacent to settlement of victim).
- Expansion limits (settlements must be 2 edges apart).

A single geometric primitive carries most of the game's interactions. Elegant.

---

## 2.5 Pitfalls and Trade-Offs

- **Bad starting placement = lost game.** Players who don't understand the opening get crushed.
- **Variance in dice rolls.** A long stretch where your numbers don't come up is brutal and unfun.
- **The 7 punishes hoarding.** This is a feature for veterans, a frustration for new players.
- **Trade asymmetry.** A leading player can be effectively starved of trades, but a charismatic player has an outsized advantage that has nothing to do with the rules.
- **Kingmaker risk in trade.** A player who can't win can decide who does by choosing whom to deal with.
- **Player count: 3–4 is sweet.** 2 player has no functional trading layer; 5–6 (with extension) becomes long.

---

## 2.6 Reusable Elements (Explicit List)

1. **Variable modular hex maps.** Different setup each game with no rule changes.
2. **2d6 probability curve with dot annotations** — production probability scaffolded for the player.
3. **Production triggered by all players' actions** (not just active turn) — keeps everyone engaged.
4. **Resource recipes that force trade** — no starting position covers all needs.
5. **The "7 effect" pattern** — a probability-anchored disruption event with hand limit, blocker, and steal bundled.
6. **Adjacency as universal interaction primitive.**
7. **Snake-draft setup placement** — frontloaded permanent decisions with balance compensation.
8. **Multiple paths to victory through differentiated VP sources** — settlements, longest road, largest army, hidden VP.
9. **Open negotiation as a structural turn step.**
10. **Bonus tokens that change hands** (longest road, largest army) — moveable VP that creates dynamic competition.
11. **Hidden development card deck** as a third spending option that produces variance and information asymmetry.
12. **Tiered building progression** (road → settlement → city) within a single resource economy.

---

# Part 3: Cthulhu Wars

**Designer:** Sandy Petersen (of *Call of Cthulhu* RPG fame)  
**Publisher:** Petersen Games (2014)  
**Players:** 2–4 (base; expansions go to 8)  
**Time:** 60–120 minutes  
**Category:** Asymmetric area-control war game with miniatures

---

## 3.1 Core Identity

Cthulhu Wars is **the asymmetry game**. Four (or more, with expansions) cosmic horror factions battle for control of an Earth in the throes of the apocalypse. Each faction is **mechanically and thematically distinct** — different units, different spellbooks, different victory paths, different turn priorities. Where most asymmetric games tweak numbers between factions, Cthulhu Wars rewrites the rules.

The game is played on a hex map of the Earth (modular regions, not a literal globe). Players summon cultists, build gates, summon monsters and Great Old Ones, engage in battles, and accumulate **Doom points**. First to 30 Doom (with all spellbooks unlocked) wins.

---

## 3.2 The Play Loop

The game proceeds in repeating rounds. Each round has four phases:

1. **Action Phase.** Players take turns spending Power on actions until everyone passes. This is where the game lives.
2. **Gather Power.** Players gain Power from cultists they control, gates they own, and abandoned/captured cultists.
3. **Determine First Player.** Initiative is based on Power totals (usually).
4. **Doom Phase.** Each player advances on the Doom track by the number of gates they control. The Ritual of Annihilation track also advances.

Within the **Action Phase**, on your turn you take *one action* and then pass to the next player. Possible actions:
- Recruit a cultist (1 Power).
- Move (1 Power for one unit, or more for groups).
- Summon a monster (Power cost varies by monster — typically 2–6).
- Awaken a Great Old One (high Power cost — these are the cosmic horrors).
- Build a gate at a region you control (variable cost).
- Capture an opponent's defeated cultist.
- Battle (free if you have units in the area).
- Cast a spell (varies — usually free if condition is met).

You can take many actions in a phase if you have the Power. When you run out (or strategically pass), you're done until next round.

---

## 3.3 Key Mechanical Systems

### 3.3.1 Radical asymmetry

The base game has four factions. Each has:
- **A unique faction sheet** with unique unit costs, abilities, and spellbook requirements.
- **A unique Great Old One** with a unique special ability (Cthulhu can sleep/awaken; Nyarlathotep's Crawling Chaos has multiple forms).
- **Unique monsters** at different power levels.
- **Six unique spellbooks** that unlock when faction-specific conditions are met.

Examples of how different the factions play:
- **Great Cthulhu** — military powerhouse. Cheap, strong combat units. Wins by smashing.
- **Crawling Chaos** — opportunist. Mobile, evasive, raids the weak. Wins by being slippery.
- **Black Goat** — territorial. Stays in one region and proliferates. Wins by infesting.
- **Yellow Sign** — sneaky/mystical. Manipulates the play space and uses unconventional unit movement. Wins by alternative routes.

These are not stat differences. They are **fundamentally different games** played simultaneously on the same board.

### 3.3.2 Power as the sole currency

Every action costs Power (or is free under specific conditions). Power resets each round (you don't carry it over) and is regenerated based on board state in the Power Phase.

This is mechanically clean. Every decision is a Power decision: "Do I summon a monster (5) or recruit two cultists (2) and move my Old One (3)?"

The fact that Power is **earned from board position** (controlled gates and cultists yield more Power) creates a positive feedback loop: stronger position = more Power = stronger position. Mitigations exist (Doom rewards gates too, so a player who hoards Power is not advancing on the win condition), but fundamentally the game rewards momentum.

### 3.3.3 Gates: the central strategic resource

Gates are physical tokens placed on map regions. They:
- Generate 2 Power per round (vs. 1 for a cultist).
- Generate Doom points each round.
- Are required as the *only* way to summon Great Old Ones.
- Are destroyable in combat — when their controlling cultist is killed, the gate becomes "abandoned" and worth less.

This single mechanism does enormous work. Gates are simultaneously the engine of growth, the source of victory points, and the most contested map objects. **Every fight in Cthulhu Wars is, in some way, a fight over a gate.**

### 3.3.4 Spellbooks: faction-specific tech tree

Each faction has 6 spellbooks. To unlock one, the faction must meet a specific condition — examples:
- Cthulhu: Awaken the Great Cthulhu.
- Black Goat: Have a unit in 3 different regions.
- Crawling Chaos: Have 2 monsters of a specific type in play.
- Yellow Sign: Spend X Power.

Once a condition is met, that faction's player picks a spellbook (in any order) and gains its effect. Most spellbooks are **passive ongoing abilities** that fundamentally change how the faction plays.

This is two design ideas combined:
1. **Custom mission-style objectives per faction.** What you have to *do* to progress is unique to your faction's playstyle.
2. **Power that scales over the game.** Late-game you have all your spellbooks active; early-game you have none. The faction grows in capability across the arc.

The spellbook system is also a soft win-condition gate: you must have all 6 unlocked to win. So you can't ignore your spellbook conditions even if you're racing on Doom.

### 3.3.5 The Doom track and Ritual of Annihilation

The Doom track is the primary win condition. Each round during the Doom Phase, every player advances on the track equal to the number of gates they control. First to 30 with all spellbooks wins.

The Ritual of Annihilation track is a separate track players can spend Power on during the Action Phase to push, drawing **Elder Sign tokens** that accelerate Doom further. This is a parallel scoring mechanism.

The double-track system means:
- A player can win by territorial dominance (gate control → Doom).
- A player can win by ritual rushing (Power-into-ritual → Doom).
- A player can win by combat dominance (kill opponents' cultists → fewer enemy gates → relative Doom advantage).

Multiple paths to the same victory condition is a mature design choice — it forces players to play differently against different factions.

### 3.3.6 Combat: simple, fast, dramatic

Combat is intentionally lightweight:
- A battle happens when factions have units in the same region.
- Each side rolls dice equal to the **combined Combat values** of their units.
- Each 6 = 1 kill (other side picks who dies).
- Each 4–5 = 1 forced retreat.
- Apply pre-battle abilities (some factions modify dice), then post-battle abilities (some factions retaliate).

The simplicity is deliberate. Combat is *common* in Cthulhu Wars. If combat resolution were complex, the game would grind. By making it dice-and-modifier-fast, the game keeps pace.

### 3.3.7 Variable region values

The map has regions of varying value (Power yield, Gate cost). Some regions can hold gates more easily; some are pure thoroughfares. The map is **modular** — at game start, players combine board sections, allowing for different configurations and player counts.

### 3.3.8 The cultist economy

Cultists are 1-Power-cost weak units that:
- Generate 1 Power each round (hold the line).
- Are the only units that can build gates.
- Can be sacrificed for various spellbook effects.
- Can be captured by opponents (reducing your Power, increasing theirs).

Cultists are the backbone. You can lose Great Old Ones and recover; lose your cultist base and you're done. They're cheap, plentiful, and structurally critical.

---

## 3.4 Notable Design Patterns

### Pattern: True asymmetry (not stat-based)

Cthulhu Wars demonstrates that asymmetric design can go far beyond "different stats" into **different rules.** This is hard to balance but enormously powerful. Each faction creates a different game-within-the-game, dramatically increasing replayability.

### Pattern: Spend-everything-each-round economy

Power resets at round end (in practice — un-spent Power is mostly wasted because new Power is gained). This forces decisions: spend now or lose it. No analysis-paralysis-friendly hoarding.

### Pattern: Multi-track victory conditions

Two parallel tracks (Doom track + Ritual of Annihilation track) feeding into the same win condition. Players choose how to push each, leading to varied strategic profiles.

### Pattern: Custom faction objectives (spellbook conditions)

Each faction has its own list of "do-this-to-unlock-power." This is a way of asymmetrically guiding each player toward different optimal play patterns, *without writing different rules for everyone.*

### Pattern: Component visual hierarchy

Cthulhu Wars miniatures are visually distinct in scale: cultists are small, monsters bigger, Great Old Ones tower over the table. This is **physical information design** — at a glance, you can read the threat level of any region. This pattern (using component scale to communicate game-state importance) is rare and valuable.

### Pattern: Aggressive, lightweight combat

Combat is simple enough that you fight often. Compare to wargames where battle is so rules-heavy that players avoid initiating it. Cthulhu Wars *wants* you to fight, and the rules support it.

### Pattern: Action-economy turn order

Players take *one action* and pass. This avoids the long-turn problem of many strategy games (one player builds a 10-action turn while others wait), and keeps everyone engaged moment-to-moment.

---

## 3.5 Pitfalls and Trade-Offs

- **Asymmetric balance is hard.** Some factions are reputed to be stronger than others; expansions add factions whose balance is debated.
- **Steep learning curve.** Each faction must be learned individually. Playing your second faction is almost playing a new game.
- **Production cost.** The miniatures are central to the experience and expensive — the deluxe edition has retailed for hundreds of dollars.
- **Player count sensitivity.** 4-player games are different from 2-player games (different recommended factions, different map config).
- **Combat dice variance.** Sometimes a strong faction loses a battle on bad rolls and the snowball reverses. Players differ on whether this is bug or feature.
- **Mathematical openness.** Power, Doom, gate value, ritual track — Cthulhu Wars is not a light game. New players are overwhelmed.

---

## 3.6 Reusable Elements (Explicit List)

1. **Action-point Action Phase** with one-action-per-turn-then-pass cycling.
2. **Power as a unifying currency** spent on heterogeneous actions.
3. **Position-based Power generation** — gates and cultists yield Power, creating positive feedback.
4. **Faction-specific tech trees** (spellbooks) with **faction-specific unlock conditions**, ensuring different factions naturally evolve along different vectors.
5. **Truly asymmetric factions** that change *rules*, not just numbers.
6. **Multi-track scoring** — parallel tracks feeding the same win condition through different play styles.
7. **Lightweight, dice-based combat** designed to be initiated frequently.
8. **Modular hex map** that scales by player count.
9. **Component scale as information** — bigger miniatures for more important units; visible at a glance.
10. **Captured/abandoned cultists** as a recoverable resource — defeat doesn't delete a unit, it transforms it.
11. **Awakening mechanics for high-tier units** — Great Old Ones must be "summoned" with deliberate cost, making their appearance an event.
12. **Round-reset economy** — Power doesn't carry over, forcing decisions and preventing hoarding.

---

# Part 4: Cross-Game Synthesis — Patterns and Remix Opportunities

Three games, three eras, three categories. But several cross-cutting design patterns emerge that any new design can draw on.

## 4.1 Patterns That Appear in Multiple Games

### Multiple paths to victory
- **Catan**: settlements, cities, longest road, largest army, hidden VP cards.
- **Cthulhu Wars**: Doom from gates, Doom from rituals, Doom from spellbook completion.
- **HPHB**: cooperative — but the variation appears in *how* the team wins (which villains to kill in which order).

### Variable setup
- **Catan**: random hex placement, random number tokens.
- **Cthulhu Wars**: modular map sections.
- **HPHB**: shuffled Dark Arts and villain decks.

### Always-on engagement
- **Catan**: production happens for everyone on every roll.
- **Cthulhu Wars**: one-action turns mean you act often.
- **HPHB**: cooperative play means others' turns affect your decisions.

### Asymmetric starting positions
- **HPHB**: each hero has a different starting deck.
- **Cthulhu Wars**: each faction is fundamentally different.
- **Catan**: even with identical rules, settlement placement asymmetrizes positions immediately.

### Tracks as visible win conditions
- **Cthulhu Wars**: Doom track.
- **HPHB**: location control tokens (a doom track *against* the players).
- **Catan**: 10 VP target, with public progress.

## 4.2 Remix Opportunities (Hybrid Ideas)

### Remix 1: A cooperative deck-builder with Cthulhu Wars asymmetric factions

Take HPHB's structure (shared villain row, Dark Arts deck, locations) but replace the four similarly-shaped heroes with four **fundamentally different** heroes — one is a deck-builder, one builds a tableau, one rolls dice, one places workers. Each plays a different micro-game while contributing to the shared cooperative goal.

### Remix 2: Catan with a doom track

Instead of racing to 10 VP, players race the world clock. A doom track ticks up automatically. The first player to a VP threshold *before doom hits 30* wins; if doom hits first, everyone loses. Suddenly Catan is also a cooperative survival game.

### Remix 3: Cthulhu Wars with HPHB-style campaign progression

Six "Cycle" boxes, each unlocking new factions, new map regions, new spellbooks. Year 1 has 4 factions; Year 6 has 12 factions and a much larger map.

### Remix 4: HPHB's "world-acts-first" turn structure with Catan's resource economy

Every turn opens with a card flip from a "Crisis" deck — bad weather, raids, plague — that all players must respond to. Players then manage settlements and resources around the disruptions. The disruption deck escalates as the game proceeds.

### Remix 5: Catan trading + Cthulhu Wars action economy

Players have hex-based settlements producing resources. On their turn they take *one action* — gather, build, trade, attack — and pass. This gives Catan-style territoriality the pacing benefits of Cthulhu Wars.

## 4.3 Cross-Cutting Design Lessons

1. **Decision density beats turn length.** Cthulhu Wars and HPHB both keep individual turns short and force decisions at high frequency. Catan ensures even non-active turns generate decisions (trades, watching for the robber).

2. **Asymmetry is a replayability multiplier**, but its cost scales with how deep it goes (number tweaks are cheap, rule rewrites are expensive).

3. **A track is a story.** All three games use a visible track as their dramatic arc — VP in Catan, Doom in Cthulhu Wars, Locations in HPHB. The track isn't bookkeeping; it's *the plot*.

4. **Forced interaction is structural, not optional.** Catan forces trade through resource asymmetry. Cthulhu Wars forces battle through Power-from-position. HPHB forces cooperation through shared loss conditions. None of these games are *optionally* multiplayer — the player count is part of the design.

5. **Small components do big design work.** Catan's probability dots. Cthulhu Wars' miniature scale. HPHB's sealed envelopes. Each of these is a tiny physical detail that does outsized teaching, signaling, or anticipation work.

6. **Variability comes cheap; depth is earned.** Variable setup is the easy replayability lever. Real depth — the kind that survives play 50 — requires interaction-rich systems. All three games invest in both, but lean on depth as the long-term retention mechanism.

---

## Sources

### Harry Potter: Hogwarts Battle
- [Harry Potter Hogwarts Battle — Don't Starve Wiki style overview at GeekDad](https://geekdad.com/2016/12/harry-potter-hogwarts-battle/)
- [Harry Potter: Hogwarts Battle Game Review — Meeple Mountain](https://www.meeplemountain.com/reviews/harry-potter-hogwarts-battle/)
- [Harry Potter: Hogwarts Battle Review — Wolf's Gaming Blog](https://wolfsgamingblog.com/2018/01/18/harry-potter-hogwarts-battle-review-youre-a-deck-of-cards-harry/)
- [Harry Potter: Hogwarts Battle Rulebook (PDF)](https://cdn.1j1ju.com/medias/59/d8/64-harry-potter-hogwarts-battle-rulebook.pdf)
- [Welcome to Hogwarts! A Complete Guide to Vanquishing Voldemort — The Op](https://theop.games/blogs/theop/complete-guide-to-vanquishing-voldemort-in-harry-potter-hogwarts-battle)
- [Game Review: Harry Potter Hogwarts Battle — Martin Gonzalvez](https://medium.com/@g0nz/game-review-harry-potter-hogwarts-battle-e6bc4af7e8b6)
- [Harry Potter: Hogwarts Battle — Daily Worker Placement](https://dailyworkerplacement.com/2017/05/17/harry-potter-hogwarts-battle/)
- [Harry Potter: Hogwarts Battle – Boardgame Review — The Faithful Sidekicks](https://www.thefaithfulsidekicks.com/harry-potter-hogwarts-battle-review/)
- [Charms and Potions Expansion Review — Board Game Quest](https://www.boardgamequest.com/harry-potter-hogwarts-battle-charms-and-potions-expansion-review/)
- [The Monster Box of Monsters Expansion — BoardGameGeek](https://boardgamegeek.com/boardgame/223494/harry-potter-hogwarts-battle-the-monster-box-of-mo)

### Settlers of Catan
- [Catan — Wikipedia](https://en.wikipedia.org/wiki/Catan)
- [Catan — Britannica](https://www.britannica.com/sports/Catan-board-game)
- [How Settlers of Catan changed board games forever — GamesRadar+](https://www.gamesradar.com/tabletop-gaming/how-settlers-of-catan-changed-board-games-forever/)
- [How Settlers of Catan Works — HowStuffWorks](https://entertainment.howstuffworks.com/leisure/brain-games/settlers-of-catan.htm)
- [Thinking Virtually #62: Anatomy of a Game — RPGnet](https://www.rpg.net/columns/virtually/virtually62.phtml)
- [Playing the probabilities in Settlers of Catan — David Richeson](https://divisbyzero.com/2010/01/06/playing-the-probabilities-in-settlers-of-catan/)
- [Dice Odds for Settlers of Catan — Stanford CS](https://cs.stanford.edu/people/nick/settlers/DiceOddsSettlers.html)
- [Probability Theory in Catan — Kanak Singh](https://medium.com/@Singh314/probability-theory-in-catan-e302fed44532)
- [Settlers of Catan Initial Setup — UltraBoardGames](https://ultraboardgames.com/catan/initial-setup.php)
- [The Robber — World of Catan Wiki](https://catan.fandom.com/wiki/The_Robber)
- [Catan Game Strategies — The Robber & Rolling A 7](https://ruletheboard.com/catan-game-strategies-the-robber-and-rolling-a-7/)
- [Settlers of Catan Strategy Primer — Board Game Business](https://boardgame.business/2013/08/30/settlers-of-catan-strategy-primer/)
- [Mark's Settlers of Catan Strategy Guide](http://mark.random-article.com/settlers/)
- [Initial Settlement Placements — King of Catan](https://kingofcatan.net/initial-settlement-placements-production/)
- [Ultimate Strategy Guide to Starting Settlements — Noah Miller](https://medium.com/@noahmiller400/ultimate-strategy-guide-to-starting-settlements-in-catan-2a55be1819be)
- [Colonist Strategies: Best Catan Starting Strategies](https://blog.colonist.io/guide-to-catan-starting-strategies/)

### Cthulhu Wars
- [Cthulhu Wars — BoardGameGeek](https://boardgamegeek.com/boardgame/139976/cthulhu-wars)
- [Cthulhu Wars — H.P. Lovecraft Wiki](https://lovecraft.fandom.com/wiki/Cthulhu_Wars)
- [Cthulhu Wars Review — Board Game Quest](https://www.boardgamequest.com/cthulhu-wars-review/)
- [Cthulhu Wars: Best Dudes On A Map Game Ever? — Tabletop Tribe](https://www.tabletoptribe.com/review-cthulhu-wars/)
- [Cthulhu Wars — The Cardboard Herald](http://www.cardboardherald.com/reviews/2017/8/8/cthulhu-wars-)
- [Interview: Cthulhu Wars Creator Sandy Petersen — GrogHeads](https://grogheads.com/interviews/1168)
- [Cthulhu Wars Rulebook (PDF)](https://cdn.1j1ju.com/medias/6b/8b/42-cthulhu-wars-rulebook.pdf)
- [Cthulhu Wars BW PDF — Order of Gamers](https://www.orderofgamers.com/downloads/CthulhuWarsBW_v2.pdf)
- [Cthulhu Wars Rules Faq — Petersen Games](https://petersengames.freshdesk.com/support/solutions/articles/48000952254-cthulhu-wars-rules-faq)
- [Action Phase — Necronomicon](https://necronomicon.app/rulebook/action-phase)
- [Doom Phase — Necronomicon](https://necronomicon.app/rulebook/doom-phase)
- [Game Basics — Necronomicon](https://necronomicon.app/rulebook/game-basics)
- [Pre-Battle Abilities — Necronomicon](https://necronomicon.app/rulebook/battle)
- [Great Cthulhu — Cthulhu Wars Strategy Wiki](https://cthulhuwars.fandom.com/wiki/Great_Cthulhu)
- [Cthulhu Wars: Playing Great Cthulhu — Points of Light](https://daegames.blogspot.com/2015/02/cthulhu-wars-playing-great-cthulhu.html)
- [Cthulhu Wars is as Big and Epic as Its Name Suggests — Way Too Many Games](https://waytoomany.games/2021/01/19/cthulhu-wars-is-as-big-and-epic-as-its-name-suggests/)
- [Cthulhu Wars Game Review — Father Geek](https://fathergeek.com/cthulhu-wars/)
- [General Cthulhu Wars Strategy — Viktor Eikman](https://viktor.eikman.se/article/general-cthulhu-wars-strategy/)
- [Cthulhu Wars Faction & Lore Overview](https://www.scribd.com/document/509096997/Cthulhu-Wars-Lore-docx-Version-1)
