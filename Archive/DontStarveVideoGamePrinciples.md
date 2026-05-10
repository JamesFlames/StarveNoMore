# Don't Starve Together: Design Principles for a Board Game Adaptation

A deep look at the design DNA of Klei Entertainment's *Don't Starve Together* (DST) — what makes it distinctive as a video game, why those choices work, and which of them could be carried into a board game without losing what makes the experience itself.

This document is organized in two layers throughout. For each pillar of the game's design, the first part describes the principle as it exists in DST. The second part — flagged as **→ Board game translation** — explores how that principle could be expressed at a tabletop.

---

## 0. The Identity of *Don't Starve Together*

*Don't Starve Together* is a multiplayer survival game in which 1–6 players are dropped, with no explanation, into a procedurally generated wilderness that is actively trying to kill them. Players manage three core stats (Health, Hunger, Sanity), survive the rotation of four hostile seasons, build bases, craft tools, fight monsters, and most importantly — figure the entire thing out themselves. There is no tutorial. There is no quest log. There is, in the base experience, no win condition.

What makes it more than just another survival game is the unmistakable **tone**: a Tim-Burton-meets-Edward-Gorey gothic cartoon aesthetic, dry deadpan humour, an oppressive but oddly inviting atmosphere of dread, and a sense that the world is a malicious storyteller hiding secrets behind every screen edge.

The design problem that this document explores is: **what would it take to put that experience on a table?**

---

## 1. Tone and Aesthetic: The "Children's Book Gone Wrong"

### The principle in DST

Klei's art director Jeff Agala set the visual style as a "sketchy newspaper-cartoon" world directly inspired by Tim Burton, Edward Gorey, and Laika studios' stop-motion films (*Frankenweenie*, *The Nightmare Before Christmas*, *ParaNorman*). The world is rendered in a muted, ink-wash colour palette punctuated by sharp, jagged silhouettes. Characters have spindly limbs, vacant eyes, and exaggerated proportions.

The aesthetic does enormous work:

- It sets expectations. Players know within seconds that this game is not going to coddle them.
- It makes death funny. A cartoon-skeleton ragdoll dying horribly is darkly comic in a way a photoreal corpse never could be.
- It hides menace inside something that looks approachable. The art looks like a children's book; the rules behave like a horror story.
- It unifies wildly different content. Forests, deserts, ruins, monsters, and machines all feel like they belong to the same world.

### → Board game translation

Tone is the cheapest replayability multiplier a board game has. You can copy DST's mechanics verbatim and produce a forgettable game, or you can copy its *tone* and produce something memorable.

Specific moves a board game can make:

- **Commit to the visual identity.** Hand-drawn, scratchy, ink-on-yellowed-paper art across every component — board, cards, tokens, rulebook. The rulebook itself can be styled as an in-world journal.
- **Use a restricted palette.** DST uses muted browns, sickly greens, and sudden saturated reds for danger. A board game adopting the same restraint feels coherent at a glance.
- **Let the components be characters.** Player meeples should be silhouetted, gaunt, distinctive. Monster cards should *look* unsettling — over-toothed, off-proportioned, a little wrong.
- **Write rules in voice.** Where most rulebooks read like instructions, a DST-flavoured one can be narrated by an unreliable scientist. Mechanical clarity and tonal flavour are not in conflict if you separate the layout — flavour text in the margins, rules in the body.
- **Embrace dark humour.** Death in DST is sad and funny at once. A board game that lets a player flip their meeple onto its back with a printed flavour line ("...oh dear.") earns a story instead of a feel-bad moment.

The goal: a game that feels haunted on the table even before anyone reads a rule.

---

## 2. The Three-Stat System: Health, Hunger, Sanity

### The principle in DST

Survival is reduced to managing three meters at once:

- **Health** — physical damage from monsters, hazards, and starvation.
- **Hunger** — depletes constantly; reaching zero starts draining health.
- **Sanity** — depletes from darkness, monsters, weird foods, and isolation. Low sanity hallucinates Shadow Creatures into existence that become *real* attackers below 15%.

What makes this design brilliant is not that there are three meters — many games have meters — it is that the three are **in tension with each other**. Eating raw or rotten food fills hunger but costs sanity and sometimes health. Sleeping restores sanity but uses time and food. Fighting monsters costs health but defeating them often restores sanity. Wearing certain hats keeps you warm but lowers sanity. Every meaningful action has a cost paid in a *different* currency than the one you are trying to fill.

This produces the core decision rhythm of the game: *I am low on X, the easy fix costs me Y, am I willing to pay?*

### → Board game translation

This is the single most portable mechanic in DST. A three-track personal economy where each track has different decay sources, different replenishment options, and crucially **costs paid in a different track than the one you are filling** is mechanically rich, thematically tight, and forces meaningful decisions every turn.

Concrete tabletop expression:

- **Three personal dials, sliders, or token tracks** on each player board, ranging 0–25 (or wherever the math lands).
- **Asymmetric costs and gains.** Cooking food at the campfire might cost 1 Sanity (the witch-hour vibes) but restore 4 Hunger. Fighting a spider costs 2 Health but restores 3 Sanity (a little victory).
- **Threshold effects, not just zero-out.** Below 5 Sanity, a player draws Hallucination cards each turn that act like "phantom" enemies. Below 5 Hunger, they cannot run actions that need stamina. Health hitting zero is the only true death state.
- **Decay that ticks on the world clock**, not on the player's turn. Each game-day, every player loses some Hunger and some Sanity automatically — a baseline pressure that prevents passive play.

The trick, and the part that many imitators get wrong, is that the meters must **interact**. Three meters that decay independently and refill from independent sources are just three timers. The DST design is that they *trade* — and that's where the game lives.

---

## 3. Seasons: Time as a Scheduled Antagonist

### The principle in DST

The DST year is 70 in-game days long, divided into four seasons:

- **Autumn** (20 days) — the gentle teacher. Resources are abundant, the weather is mild. Players who are paying attention know this is the prep window.
- **Winter** (15 days) — long nights, freezing temperatures, plants stop growing, the Deerclops boss appears. Players who didn't prep in autumn die here.
- **Spring** (20 days) — constant rain, lightning, frogs raining from the sky, sanity drops from being wet, the Moose/Goose boss.
- **Summer** (15 days) — overheating, spontaneous wildfires that can burn down an unprotected base, the Antlion boss.

Seasons are predictable in *structure* but unpredictable in *detail*. You always know summer is coming. You don't always know exactly when the wildfire will start, or where the boss will spawn.

The brilliance is that **each season changes the rules of play**. Strategies that worked in autumn fail in winter. The game forces players through repeated transitions, each requiring new adaptations.

### → Board game translation

Few mechanics drive replayability and pacing as cheaply as a season system. A board game adopting this idea gets:

- A built-in **arc** (Section 7 of *PrinciplesOfGoodBoardGames.md*).
- A built-in **timer** (the world clock).
- Built-in **variability** (different hazards each season).
- Built-in **strategic obsolescence** (forces players to adapt instead of optimizing one strategy forever).

Implementation:

- **A round track of 16–24 turns**, divided into 4 seasonal phases. Visible to all players from turn one — the game's clock is honest about what's coming.
- **A season deck per season.** Each turn within a season, draw an event from that season's deck. Autumn events are mild ("Bumper crop — gain 1 food"), winter events are punishing ("Cold snap — every player loses 2 Hunger unless next to a fire"), summer events are explosive ("Wildfire — roll for each wood structure").
- **Seasonal bosses as deterministic but variable threats.** "On the third turn of winter, the Deerclops appears at a random map edge." Always coming, never quite the same.
- **Mechanics that flip.** Some resources are only gatherable in certain seasons; some structures only function in certain seasons; some recipes require ingredients that exist only in narrow windows. The map *changes shape* with the seasons.

The deeper design lesson: **the game's hostility should be on a schedule.** Pure randomness feels arbitrary. A predictable schedule of escalating threats lets players plan, and lets them feel clever when they survive — and ashamed when they didn't prep.

---

## 4. The Day/Night Cycle: A Fast Inner Clock

### The principle in DST

Inside each day there is a smaller cycle: day → dusk → night. Day is for working, dusk is for hurrying back to base, and night is for huddling around a fire because the darkness itself will kill you (the unseen entity Charlie attacks anything caught without a light source). At night many monsters become more aggressive, vision shrinks, and most useful work becomes impossible.

This creates a **double-pulse rhythm**: the slow pulse of seasons measured in many days, the fast pulse of day/night measured within each day. Every in-game day forces players to be productive, then forces them to retreat. The forced retreat is the heart of the experience — it's when conversation happens, when plans are made, when sanity ticks back up by the fire, and when the next day's goals are decided.

### → Board game translation

A within-round phase split mirrors this beautifully and adds **rhythm** to a game's pacing.

- **Each round = one day.** Day Phase: players take exploration/gathering/combat actions out on the map. Night Phase: players resolve a forced "return to camp" effect. Players caught off-camp at night suffer a sanity hit, a damage roll, or a "Charlie" attack draw.
- **Camp as a safe state.** Sitting at the campfire during the night phase regenerates sanity, allows trading between players, and is when story/event cards get read. Camp is mechanically valuable *and* socially valuable — it's the table-talk window.
- **A light economy.** Torches burn out. Fires need fuel. A camp can run out of light. Players in the dark are vulnerable in concrete ways.

The aesthetic payoff: even in a strategic euro, the moment everyone gathers their tokens back to the fire feels like a story beat.

---

## 5. The Three-Tier Tech Tree: Science, Magic, Ancient/Shadow

### The principle in DST

Crafting in DST is gated by **prototypers** — workbenches that unlock new recipes:

- **Science Machine** (Tier 1) and **Alchemy Engine** (Tier 2) for Science crafting.
- **Prestihatitator** (Tier 1) and **Shadow Manipulator** (Tier 2) for Magic crafting.
- **Ancient Pseudoscience Station** (deep in the ruins) for the ancient/shadow tier.

The progression isn't linear. Magic recipes often cost sanity to use; ancient items are powerful but require descent into the Ruins (a separate, far more dangerous biome). Crafting the *prototyper* itself gives a sanity bonus — discovery is *literally* good for your mind.

The genius is that progression happens through **the world**, not a menu. You don't pick "Tier 2 Combat" from a dropdown; you walk into a dangerous biome, find an ancient station, mine the materials, and crucially survive the trip back.

### → Board game translation

Tech trees on cards or boards are common — and usually boring. The DST version is interesting because:

- Progression is **spatial**. You unlock the next tier by physically reaching a location.
- Progression is **costly in stats**, not just resources. Magic costs sanity. Ancient tech requires a dangerous expedition.
- Progression is **shared in some forms, private in others**. In DST, prototyping a recipe is once-per-world, so the first player to build the Alchemy Engine effectively unlocks it for the team.

For a board game:

- **Three crafting decks** (Science, Magic, Ancient) accessed via three different built structures.
- **Prototyper structures placed on the map.** Building one requires materials and an action; once built, anyone at that location can craft from the corresponding deck.
- **Magic items have a sanity cost to use** but powerful effects. Players choose how much of their psyche to spend.
- **The Ancient/Ruins tier is deep in a hostile biome.** Reaching it requires expedition planning, multiple players, and is risky enough that returning successfully is a story unto itself.
- **First-time prototyping rewards.** When a recipe is first unlocked in the game, the player who unlocked it gains a sanity bonus or scoring bonus, modeling the DST joy of discovery.

This solves the "dry tech tree" problem by making progression a **journey** instead of a checkbox.

---

## 6. Asymmetric Characters

### The principle in DST

DST has 20+ playable characters, each with substantially different abilities, stats, and constraints:

- **Wilson** — the default. Balanced stats, no quirks. Grows a beard over time that insulates him from cold.
- **Wendy** — summons her ghost twin sister Abigail as a permanent combat ally; deals 25% less weapon damage; takes less sanity loss in the dark.
- **Wickerbottom** — librarian; starts with all Tier 1 science recipes pre-unlocked; can craft and read magical books (which drain her sanity) that have powerful effects; cannot eat stale food; cannot sleep.
- **Wolfgang** — combat powerhouse whose damage and HP scale with hunger; ravenous appetite; cowardly at low health.
- **Webber** — child-spider hybrid; spiders are friendly to him and pigs are hostile; can sleep in spider dens.
- **Winona** — engineer; builds faster; has access to unique mechanical structures.
- **Warly** — chef; can only eat food cooked at the crockpot; cooks better than anyone else.
- **Wigfrid** — Valkyrie; can only eat meat; gains health and sanity from combat.

These are not skin-deep variants. Each character forces a different *playstyle* and creates complementary roles in a group.

### → Board game translation

Character asymmetry is one of the great accelerators of replayability — but expensive to balance (Section 9 of *PrinciplesOfGoodBoardGames.md*). DST's design offers a useful model:

- **Build asymmetry around a single mechanical hook.** Wendy's hook is Abigail. Wickerbottom's hook is books. Each character is a small package of related abilities that all reinforce one identity.
- **Pair every advantage with a constraint.** Strong combat → ravenous hunger. Permanent ally → weaker weapons. Pre-unlocked tech → can't sleep. The constraints prevent dominance and create unique decision puzzles.
- **Asymmetry should produce different *plays*, not just different *numbers*.** A character with "+1 Health" is a stat tweak. A character who *cannot eat raw food* and must stand by the campfire to do anything plays a different game.
- **Character abilities should reward the cooperation of the rest of the team.** Warly's cooking benefits everyone. Winona's structures help defend the base. Wigfrid's combat covers Wendy's weakness.

For a board game: 6–10 starting characters is plenty. Each has a unique starting hand, one or two passive abilities, and one constraint. Different group compositions then produce different table dynamics, which is more replayability than 100 different scenario tiles.

---

## 7. Permadeath and the Cost of Failure

### The principle in DST

Default settings have permadeath. When you die, you're a ghost — you can wander, you can lower other players' sanity by hovering near them, but you cannot interact with the world. Other players can revive you, but it costs significant resources (a Telltale Heart, made from spider silk, ash, and a chunk of the reviver's own health).

Permadeath does several things simultaneously:

- It makes every decision **weighty**. You can't just respawn and try again.
- It produces **stories**. Every long-lived character in DST has a saga players remember.
- It puts the cost of recklessness on **other people**. If you die stupidly, your teammates have to bleed to revive you.
- It creates the game's central emotional contract — survival is not assumed.

DST softens this just enough: ghosts can be revived, server settings allow respawn touchstones, and death isn't strictly the end of a player's session. The mood is "death is bad and rare, not death is final and disconnects you."

### → Board game translation

Pure permadeath in a board game is a player elimination problem (Section 10 of *PrinciplesOfGoodBoardGames.md*) — devastating in long games. DST shows the workaround: **soft permadeath**.

- **Death has consequences but doesn't end participation.**
- **Dead players become "ghosts"** with a different, restricted action set: hovering near monsters to weaken them, whispering hints to the living (with limits), or dragging down the morale meter of a teammate.
- **Revival is possible but costly.** A revival rite requires rare materials and a personal Health/Sanity sacrifice from the reviver. This is what makes revival meaningful — it's not free.
- **End-of-game scoring counts everything.** Even a dead player's accomplishments (resources gathered, monsters defeated, prototypes unlocked) count toward the team's overall score.

The aesthetic outcome: death feels significant without being a punishment that excludes a player from the table for an hour.

---

## 8. Procedural Worlds and Exploration

### The principle in DST

Each DST world is procedurally generated from a system of "Tasks" (mini-region templates) connected by "Locks and Keys" (logical constraints — you must reach Region A to find the resources needed to enter Region B). Biomes are randomly placed: forests, savannas, marshes, deserts, rocklands, mosaic, oasis, ruins.

The map starts entirely black except for the area around the player. Exploration *is* progress. Finding a new biome is exciting because it means new resources, new threats, and new options. The fog of war isn't a UI affordance — it's the central engine of curiosity.

### → Board game translation

Modular hex/tile maps are the standard tabletop translation, and they work because they capture this exact feeling.

- **The world is built by tile placement, not pre-printed.** Players draw biome tiles from a shuffled stack and place them as they explore.
- **Hidden until discovered.** Tiles are face-down on the map until a player physically reaches their edge — turning them face-up is the game's primary "yay" moment.
- **Locks and keys.** Some biomes require specific items, characters, or tech to enter — the swamp tile is impassable without machetes; the ruins are only reachable through a cave entrance that itself requires explosives. The map's geography enforces a soft progression order without scripting.
- **Hidden landmarks.** Pre-shuffled into the biome stack are special tiles (Pig King's grove, the Touchstone, an Ancient station). Finding them is a lottery that creates run-to-run variation without requiring different rules.

This converts a static board into a story-generator without any new mechanical complexity.

---

## 9. Cooperative Specialization

### The principle in DST

DST's multiplayer design diverged from "scale enemy HP with player count" — instead, *everything in the world is the same* whether one player or four are present. More players means more hands, but also more mouths, more sanity to manage, and more potential for cascading failure.

This means cooperation isn't a power-up; it's a coordination problem. The optimal play emerges naturally:

- One player fights and kites the boss.
- One player hauls resources back to base.
- One player keeps the food economy running at the crockpot.
- One player explores and maps new biomes.

Specialization is *more* efficient than parallel duplication. Four people all chopping trees is less productive than one chopper, one cook, one fighter, one scout.

### → Board game translation

This is the gold standard for designing a cooperative game that resists the **alpha-player problem**.

- **The world doesn't scale.** The map, the seasons, the boss HP, the food spoilage rate — none of these change with player count. The only thing that changes is how many actions per round are available across the team.
- **Roles emerge from characters.** Asymmetric characters (Section 6) make specialization the obvious play.
- **Information should be partly private.** If every player can see every other player's hand, the loudest player runs the table. Private hands of "Ideas" or "Knowledge" cards limit alpha-player domination — the cook *knows* something about cooking that the fighter doesn't.
- **Communication budget.** Limiting what can be said ("you may show one card per round") slows the game down and forces players to make their own decisions, instead of waiting for the alpha player to plan everyone's turn.
- **Time pressure beats puzzle pressure.** Real-time elements — even gentle ones, like a 2-minute sand timer for the Day Phase — short-circuit the alpha-player problem because there isn't time to optimize for everyone.

When this works, four players around the table feel like four characters around a campfire, each contributing what they uniquely can.

---

## 10. Bosses and Scheduled Drama

### The principle in DST

The seasonal giants — Deerclops in winter, Bearger in autumn, Moose/Goose in spring, Antlion in summer — are scheduled events that arrive after Day 20 and recur. Their arrival is announced (Deerclops famously roars for several seconds before appearing), and they are catastrophic if unprepared. Each has a unique pattern: Deerclops smashes structures, Bearger sleeps the camp and devours food stockpiles, Moose/Goose lays eggs that hatch into a flock, Antlion sinks the ground.

These bosses serve the **game arc** beautifully. They're spaced evenly, signaled in advance, and force a transition: from the steady-state of survival into a sudden burst of preparation, fear, and combat. They are the game's punctuation marks.

### → Board game translation

Scheduled climactic events are how a long board game stays engaging across its arc.

- **Boss arrivals are deterministic in timing, variable in detail.** "On the seventh turn, the Bearger arrives. Roll a die for spawn location."
- **Pre-warning gives players prep time.** "On the fifth turn, an event card is revealed: 'Distant rustling — a Bearger approaches in two turns.'" This gives players an explicit window to fortify.
- **Bosses change the rules temporarily.** While the Deerclops is on the map, every player loses double Sanity per turn from the cold; every wood structure has a chance of being smashed if the boss is adjacent.
- **Defeating a boss yields commensurate reward.** A trophy that gives a permanent ability, a unique craftable item, or a substantial scoring bonus.

The point is **rhythm**. Quiet, build-up, climax, recovery, repeat. The same shape as any good story — and DST's success at it on a video-game canvas is directly transferable.

---

## 11. Emergent Storytelling Through Constraint

### The principle in DST

DST has almost no scripted narrative. There is lore in the background — the trickster demon Maxwell, the entity Charlie, the Constant — but it is not delivered through cutscenes or quest text. Instead, the game's "story" emerges from the interaction of:

- The world's harsh rules.
- The character's quirks.
- The player's choices.
- The other players' choices.
- A few rare scripted set-pieces players might stumble onto.

Players come away talking about **the time Wendy died to a hound pack while Wilson was off-screen growing a beard**, or **the spring we lost the entire crockpot stockpile to a Bearger we forgot about**. These stories are unique to that group, that world, that run.

This is the design payoff of all the previous mechanics combined: hostile environment + asymmetric characters + co-op specialization + scheduled disasters + permadeath = a story-generator. Klei doesn't write the stories. The systems do.

### → Board game translation

Section 6 of *PrinciplesOfGoodBoardGames.md* covers emergence. DST is a model implementation: a small number of clear rules that interact richly to produce shared moments.

For a board game, lean on:

- **Persistent state.** A single play should leave a trail of memorable events — first kill, first death, longest expedition, biggest disaster. Even small components like a shared "Chronicle" sheet players scribble on can capture this.
- **Naming.** Allow players to name their characters at the start. A nameless meeple dying is a token; "Wesley the Cartographer" dying in a wildfire is a story.
- **Failure as content.** Make sure failures *do* something interesting. A dead player becomes a ghost; a destroyed structure leaves rubble that affects future turns; a lost expedition leaves bones for the next group to find. Failure should ramify, not just subtract.
- **Don't over-script.** Resist the urge to write 200 event cards with bespoke flavor. Write 30 cards whose rules interact richly with the rest of the game. Emergence beats scripting in shelf-life.

---

## 12. The Economy of Trade-Offs (Synthesis)

The thread running through every DST mechanic is **the same idea expressed at different scales**:

- **Stat level:** trade Sanity for Hunger, Hunger for Health.
- **Action level:** trade time-now for food-later, exposed travel for new resources.
- **Day level:** trade productive day-time for the safety of night-time camp.
- **Season level:** trade autumn comfort for winter prep.
- **Boss level:** trade your normal routine for a frantic combat scramble.
- **Death level:** trade resources to revive a teammate, taking on their cost.

Every interesting decision in DST is a trade. The currencies just keep changing.

A board game inheriting this design DNA inherits its decision-making heart: **never let the player gain something for nothing, and always force them to pay in a currency adjacent to the one they want.** This is the engine that turns a survival theme into an actually compelling game.

---

## 13. The Aesthetic Commitments DST Makes (and a Board Game Could)

Distilled into a list of design *commitments* — choices that the designers refused to compromise — that any DST-flavored board game ought to consider keeping:

1. **The world is hostile, not balanced for the player.** Difficulty is a feature, not a bug.
2. **The game does not explain itself.** A short rulebook plus an in-world reference card; learning is part of the experience.
3. **Death is real but not final.** Soft permadeath, with cost.
4. **Failure is funny when it's drawn cartoonishly.** Tone protects the game from being grim.
5. **The world keeps moving.** The clock advances regardless of whether players act efficiently.
6. **Resources spoil.** Standing still is not free. Hoarding is punished.
7. **Discovery is the primary reward.** Map reveals, recipe unlocks, and first-time encounters are higher-status than raw VP.
8. **Cooperation is incentivized but not enforced.** Players *can* hoard, betray, or freelance. The game doesn't punish that, but the world will.
9. **Each play tells a different story.** Emergence over scripted narrative.
10. **The aesthetic is the game.** Tone, art, voice are not packaging — they are the experience.

---

## 14. A Concept Sketch: What a DST Board Game Might Look Like

To make the above concrete, here is a back-of-napkin sketch of how a DST-inspired board game could fit together. This is illustrative, not prescriptive.

### Setup

- Each of 1–4 players picks an asymmetric Survivor (e.g., Scientist, Librarian, Hunter, Engineer, Cook, Lonely Child).
- Each Survivor has a personal player board with three dials: **Health (20)**, **Hunger (15)**, **Sanity (15)**.
- The map is built on the table by placing 4 starting hex tiles (the spawn area) face-up. The remaining tile stack is shuffled face-down to be drawn during exploration.
- A round track of 20 turns, divided: Autumn (5) → Winter (5) → Spring (5) → Summer (5).

### Each round (one in-game day)

1. **Dawn phase** — reveal the day's event card from the current season's deck.
2. **Day phase** — turn order is simultaneous; each player has 4 actions: move, gather, craft, fight, prototype, cook.
3. **Dusk phase** — players must declare whether they are returning to camp.
4. **Night phase** — players at camp regenerate Sanity and may trade. Players away from camp must expose a torch or lose Health and Sanity. The Charlie deck triggers if anyone is in true darkness.
5. **Tick** — every player loses 1 Hunger; world clock advances.

### Crafting

- Three structure types unlock three crafting decks: Science Machine, Magic Workshop, Ruins Station.
- Recipes require specific resources gathered from biomes.
- First-time prototyping a recipe gives the discovering player +3 Sanity.

### Bosses

- One per season, deterministic timing, variable spawn position, unique disruption behaviour while present.
- Defeating a boss gives the team a permanent Trophy card with passive benefits.

### Death and revival

- A player at 0 Health flips their meeple to Ghost side.
- Ghosts can move, lower nearby living players' Sanity passively (negative aura), and whisper one word per turn to the team.
- Revival requires a Telltale Heart (rare materials + 4 Health from the reviver) crafted at camp.

### End conditions

- The game ends after 20 days **survived as a group**, OR when all Survivors die.
- End-game scoring counts: days survived, biomes discovered, recipes prototyped, bosses defeated, base structures built, end-game stat bonuses. Players collectively have a "Saga Score" that they're trying to beat next time.

This is *not* a finished design — it's a sketch showing how the pillars combine. The actual design would emerge from playtesting (Section 12 of *PrinciplesOfGoodBoardGames.md*).

---

## 15. Closing: Why DST Is Worth Stealing From

Most survival video games are punishing, systemic, atmospheric — but they don't translate cleanly to a board because they rely on twitch reactions, real-time pressure, and overwhelming sensory input.

*Don't Starve Together* is unusual because its core experience is built almost entirely from **decisions**, not reflexes. Should I gather one more stack of grass before night, or play it safe? Should I fight the spider queen now or wait until I have a better weapon? Should I share my food with the dying teammate or save it for myself? Every one of those questions translates to a card, a token, or a track.

That's why DST is one of the better candidates for tabletop adaptation in the survival genre: its design is already, almost accidentally, the design of a board game. The job is to keep the *tone*, simplify the *systems*, preserve the **trade-offs**, and trust the players to generate their own stories.

---

## Sources

- [Don't Starve — Wikipedia](https://en.wikipedia.org/wiki/Don't_Starve)
- [Don't Starve Together — Don't Starve Wiki (Fandom)](https://dontstarve.fandom.com/wiki/Don't_Starve_Together)
- [Game Design Analysis: Don't Starve — Anna Malecki](https://annamalecki.medium.com/game-design-analysis-dont-starve-50d06561097d)
- [Don't Starve Together is a Great Example of Core Mechanics Balancing Multiplayer — Game Rant](https://gamerant.com/dont-starve-together-multiplayer-balance-survival-elements-difficulty/)
- [Don't Starve Together, with a Little Help from My Friends — CJ Leo](https://cjleo.com/blog/dont-starve-together-with-a-little-help-from-my-friends/)
- [Don't Starve: A Tim Burton take on Minecraft — Game Developer](https://www.gamedeveloper.com/design/-i-don-t-starve-i-a-tim-burton-take-on-i-minecraft-i-)
- [The Art of Tim Burton & Don't Starve — Rose W Blog](https://rosewblog.wordpress.com/2018/02/18/the-art-of-tim-burton-dont-starve/)
- [Tim Burton's Don't Starve? Survival Game's Gothic Flair Unwrapped — DST Fans](https://dstfans.com/post/tim_burtons_dont_starve_survival_games_gothic_flair_unwrapped)
- [Sanity — Don't Starve Wiki](https://dontstarve.fandom.com/wiki/Sanity)
- [Health — Dont Starve Together Wiki (FextraLife)](https://dontstarvetogether.wiki.fextralife.com/Health)
- [Hunger — Dont Starve Together Wiki (FextraLife)](https://dontstarvetogether.wiki.fextralife.com/Hunger)
- [Don't Starve Together: Beginner's Sanity Guide — At The Minute](https://www.attheminute.com/article/dont-starve-beginners-sanity-guide)
- [Seasons — Don't Starve Wiki](https://dontstarve.fandom.com/wiki/Seasons)
- [Seasons/Winter — Don't Starve Wiki](https://dontstarve.fandom.com/wiki/Seasons/Winter)
- [Seasons/Summer — Don't Starve Wiki](https://dontstarve.wiki.gg/wiki/Seasons/Summer)
- [Day-Night Cycle — Don't Starve Wiki](https://dontstarve.fandom.com/wiki/Day-Night_Cycle)
- [Crafting — Don't Starve Wiki](https://dontstarve.fandom.com/wiki/Crafting)
- [Crafting/Don't Starve Together — Don't Starve Wiki](https://dontstarve.wiki.gg/wiki/Crafting/Don't_Starve_Together)
- [Don't Starve Together Characters Guide — Switchblade Gaming](https://www.switchbladegaming.com/dont-starve-together/characters-guide/)
- [Don't Starve Together Characters Guide — BisectHosting](https://www.bisecthosting.com/blog/dont-starve-together-characters-stats-perks-quirks-birthdays-how-to-unlock)
- [Wickerbottom — Don't Starve Wiki](https://dontstarve.fandom.com/wiki/Wickerbottom)
- [Don't Starve Together Character Synergies Guide — Basically Average](https://basicallyaverage.com/dst-character-synergies-best-team-compositions/)
- [Don't Starve Together: Best Strategies For Team Survival — TheGamer](https://www.thegamer.com/dont-starve-together-team-strategy-tips/)
- [Beginner's Guide 2026: How to Survive Your First Winter — Switchblade Gaming](https://www.switchbladegaming.com/dont-starve-together/beginners-guide-2026/)
- [Don't Starve Together Guide — GameHelper](https://www.gamehelper.io/games/dont-starve-together/articles/dont-starve-together-guide-perfecting-your-survival)
- [Biomes/Don't Starve Together — Don't Starve Wiki](https://dontstarve.fandom.com/wiki/Biomes/Don't_Starve_Together)
- [World Generation — Don't Starve Wiki](https://dontstarve.fandom.com/wiki/World_Generation)
- [Map/DST — Don't Starve Wiki](https://dontstarve.wiki.gg/wiki/Map/DST)
- [Guides/Base Camp Guide — Don't Starve Wiki](https://dontstarve.fandom.com/wiki/Guides/Base_Camp_Guide)
- [Don't Starve Together Base Building Guide — BisectHosting](https://www.bisecthosting.com/blog/dont-starve-together-base-building-tips-tricks-locations-buildings)
- [Guides/Combatting Bosses — Don't Starve Wiki](https://dontstarve.fandom.com/wiki/Guides/Combatting_Bosses)
- [The Best Bosses In Don't Starve Together, Ranked — TheGamer](https://www.thegamer.com/dont-starve-together-best-bosses/)
- [Survival Game Design — GameDesignSkills](https://gamedesignskills.com/game-design/survival/)
