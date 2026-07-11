# Principles of Good Board Games

A working reference for designing board games that are compelling on the first play and rewarding on the fiftieth — written to be used by an AI (or a human) that is **creating a new game** or **improving an existing one**. Synthesized from established design literature, designer essays, and analyses of games that have endured.

---

## How to Use This Document

**If designing a new game**, work top-down:

1. Name the target aesthetic (§1), audience, player count, and time budget (§14) *before* writing rules.
2. Build the smallest rule set that produces one meaningful choice per turn (§2, §3).
3. Layer in systems one at a time — economy (§8), interaction (§10), arc (§7) — checking after each addition that it *interacts* with what's already there (§6).
4. Choose victory conditions last-but-early: they retro-shape every other decision (§12).
5. Iterate per §16.

**If improving an existing game**, work bottom-up:

1. Observe or simulate play and collect *symptoms* (dead turns, foregone conclusions, ignored mechanics).
2. Look each symptom up in the diagnosis table (§15) and trace it to a root cause — symptoms usually live downstream of their cause.
3. Prefer the **minimal intervention**: delete or tune before adding. New rules are the most expensive fix and usually the wrong one.
4. Change one thing, re-test, and check the regression list (§17) before moving on.

**Limits of an AI designer.** An AI can verify math: expected values, dominant strategies, income curves, win rates under scripted policies. Use simulation aggressively for those. An AI cannot directly verify *feel*: tension, downtime boredom, table talk, the joy of a clever move. For those, this document provides proxies (measurable stand-ins), but proxies are hypotheses — flag them for human playtesting rather than declaring them solved.

---

# Part I — Foundations

## 1. Start With What You Want Players to Feel

Designers control mechanics. Players experience emotions. Everything else lives in between.

The **MDA framework** (Mechanics → Dynamics → Aesthetics) is the most useful model for the gap:

- **Mechanics** — the rules, components, and procedures you write down.
- **Dynamics** — the run-time behavior that emerges when players interact with the mechanics and each other.
- **Aesthetics** — the emotional response: tension, triumph, camaraderie, discovery, dread.

The designer works left-to-right (rules produce play produces feeling). The player experiences the game right-to-left (the feeling is real; the rules are something they tolerate to get there). **Design backwards from the aesthetic you want.** A negotiation game and a puzzle game can share 90% of their rules and still be different games because they aim at different feelings.

Before you write a rule, name the experience in one sentence: "Tense bluffing among friends." "Quiet, contemplative pattern-building." "A loud, ridiculous arc that ends in laughter." If you cannot name it, you do not yet know what you are designing.

**Every later decision is judged against this sentence.** When two fixes both work mechanically, pick the one that serves the stated aesthetic. When a mechanic is fun in isolation but pulls the game toward a different feeling, cut it.

---

## 2. Meaningful Choices Are the Atomic Unit of a Good Game

Sid Meier's definition — "a game is a series of interesting decisions" — is hard to improve on. A choice is meaningful when three things are true:

1. **Real trade-offs.** Picking option A means giving up option B. Strict upgrades are not choices; they are paperwork.
2. **Genuine uncertainty.** If the optimal play is computable from public state, you have a math problem, not a decision. Uncertainty can come from hidden information, opponent behavior, or (carefully) randomness.
3. **Context-dependence.** The best move should change based on board state, opponents, and long-term plan. If the same option is always best, the choice is fake.

Player agency — the felt sense that *your* decisions shaped the outcome — is the psychological payoff. It satisfies autonomy, competence, and (in multiplayer) relatedness. When agency is absent, players feel like they are watching the game play itself.

**Diagnostics:**

- *Fake-choice test.* In a playtest, did the player deliberate, or pattern-match to the obvious move? Repeated obvious moves mean rules without decisions.
- *Simulation test (AI-checkable).* If a trivial greedy policy wins nearly as often as a thoughtful one, the decisions aren't doing work.
- *Regret test.* After the game, can a losing player point to a decision they'd take back? If losses feel like pure variance, agency is too low. If wins feel inevitable from turn 3, agency ended too early.

---

## 3. Elegance: Maximum Depth for Minimum Complexity

Elegance is the depth-to-complexity ratio. **Easy to learn, hard to master.**

- **Complexity** is what the player must hold in their head: rules, exceptions, edge cases, fiddly upkeep.
- **Depth** is the strategic space the game opens up: viable strategies, interactions, long-term planning.

Tesler's Law applies: every system has an irreducible amount of complexity. The designer chooses where it lives — in the rulebook (the player suffers) or in the design process through ruthless iteration (you suffer, the player has fun). Choose the latter.

**Practical heuristics:**

- Depth should come from the **interaction of many simple parts**, not from a few complex ones. Chess has six piece types and produces oceans of depth.
- A new mechanic must justify itself by opening *multiple* decisions, not one.
- If a rule exists to patch one weird case, the underlying system is probably wrong. Fix the system, delete the patch.
- Exceptions cost roughly double: players must learn the rule *and* remember when it applies. Two exceptions to one rule usually signal the rule is wrong.
- Target: the core game learnable in 10–15 minutes, with the rulebook as reference rather than required reading.

**Complexity budget audit (AI-checkable):** count the rules, exceptions, phases, resource types, and icon meanings a new player must know before their first turn. For each, ask: how many *distinct decisions* does this element enable across a game? Elements with a low decisions-per-rule ratio are cut candidates. Cutting is harder than adding — most designs become great when the designer finally deletes the third resource type or the variant scoring rule everyone politely tolerated.

---

## 4. Theme and Mechanics Should Reinforce Each Other

Theme is the *why*; mechanics are the *how*. When they agree, players learn faster, remember rules more easily, and care more about the outcome.

A useful spectrum:

- **Pasted-on theme.** The art says "space pirates," but you could swap it for "medieval merchants" without changing a rule. Players read the rulebook as pure procedure.
- **Thematic resonance.** The rules feel like consequences of the world. In a plague game, infection spreading to adjacent cities is not arbitrary — it is what a player *expects* a plague to do. The rule almost teaches itself.

Theme is expressed across **layers**: art, components, terminology, mechanics, and narrative arc. Strong games push theme into all of them; weak ones leave it floating on top of the box.

**Two working tests:**

- *Swap test.* Retheme the game mentally. Every rule that survives the swap unchanged is carrying no theme. Some of those are fine (turn order); if *most* are, the theme is pasted on.
- *Guess test.* Describe the theme and ask what a rule *should* be ("what happens when a farm floods?"). If a naive guess matches the actual rule, the mechanic is teaching itself. Rules that contradict thematic intuition are the most expensive rules in the game — players will misplay them repeatedly.

Theme also drives replayability: a mechanically tight game with a flat theme burns out faster than one where players feel they are living a story, even at similar strategic depth.

---

## 5. Randomness: Luck Is a Tool, Not a Flaw

Randomness is neither good nor bad; it is a dial with specific uses. Get this wrong and no amount of balance work saves the game.

**The core distinction — input vs. output randomness:**

- **Input randomness** happens *before* the decision: you draw a hand, roll for resources, reveal the market — *then* choose what to do with it. It creates variety and fresh puzzles while preserving agency. Almost always safe.
- **Output randomness** happens *after* the decision: you commit to the attack, *then* roll to see if it worked. It creates excitement and drama but taxes agency — the player did everything right and lost anyway.

Output randomness is not forbidden, but it must be **budgeted**: let players mitigate it (spend resources for rerolls or modifiers), see the odds before committing, and face it often enough that variance averages out across the game. One giant unmitigated die roll deciding the winner is a design failure; twenty small rolls with visible odds and mitigation options is a texture.

**Matching luck to audience and length:** more luck flattens the skill curve — weaker players win sometimes (good for family play, bad for tournament play). Longer games tolerate *less* deciding-roll variance: losing a 20-minute game to a die is funny, losing a 3-hour game to one is unforgivable.

**Diagnostics:**

- *Skill-luck check (AI-checkable):* pit a strong policy against a random-legal-move policy in simulation. Win rates near 50% mean the game is mostly luck; near 100% with no randomness levers means new players will be crushed. The right target depends on the stated audience.
- *Last-decision check:* identify the final swing that decides typical games. If it's a random event no player chose to expose themselves to, move the randomness earlier (convert output to input).

---

## 6. Information Design: What Players Know and Must Remember

Every piece of game state is either open, hidden, or *forgotten* — and each placement is a design decision.

- **Open information** enables deep planning but invites analysis paralysis (§15) and lets strong players dominate.
- **Hidden information** creates bluffing, tension, and comeback potential, and caps how far anyone can calculate — the cheapest AP fix that exists.
- **Memory as a mechanic** (remembering what was played or seen) should be deliberate. Accidental memory burden — where the player who happens to track discards has an advantage the design never intended — is a bug. Either make information openly visible or make remembering an explicit, themed skill.

**Legibility.** Players must be able to read the state that matters: whose position is strong, what's scarce, how close the end is. Catan printing probability pips on the number tokens is the canonical move — it lowered the cognitive cost of strategy without lowering the strategy. Audit: for each decision the game asks, is the information needed to make it well *visible at the table* without arithmetic gymnastics?

**Hidden scores** deserve special note: they suppress runaway-leader targeting and kingmaking (nobody knows whom to beat down) at the cost of a less legible race. Games that want a tense visible race need other leader controls (§13).

---

# Part II — Systems

## 7. Emergence Beats Scripting

Scripted content (specific scenarios, predetermined events, branching narrative) is expensive to author and finite — once seen, it's spent. **Emergent content is generated by the system every time you play.**

Emergence comes from a small number of well-chosen rules that interact richly. You never wrote "the player who controls the river will dominate the late game" — but it happens, every game, differently. That is what players mean when they say a game has "stories."

To design for emergence:

- Prefer general rules over special cases.
- Make sure mechanics **touch** each other. If two systems run in parallel without interacting, you have two shallow games stacked on top of each other. Audit: for each pair of systems, name a decision where they trade off against each other. Pairs with no such decision are candidates for fusing or cutting.
- Let players co-author outcomes through their choices and interactions rather than railroading the experience.

---

## 8. Economies, Resources, and Feedback Loops

Most modern games have an economy: sources (where resources enter), conversions (what they become), and sinks (where they leave). The economy's shape determines the game's shape.

**Design rules of thumb:**

- **Every resource needs pressure.** A resource players always have enough of is not a resource; it's a token you make players push around. Scarcity is what makes spending a decision.
- **Every resource needs at least two competing uses**, or acquiring it is paperwork, not strategy.
- **Conversion chains create planning depth** (wood → boards → house → points), but each additional link adds turns of setup before payoff. Long chains suit long games; a 30-minute game supports one or two links.
- **Watch the ratio of "building" turns to "doing" turns.** If players spend 80% of the game constructing an engine and 20% using it, the payoff window may be too short to feel earned — or the game should embrace it and end on the crescendo.

**Feedback loops** are the economy's dynamics:

- **Positive (reinforcing)** — winning helps you win more. Creates momentum and the addictive engine-builder feel, but produces runaway leaders if uncapped.
- **Negative (balancing)** — falling behind helps you catch up. Keeps games close but can punish good play and reward sandbagging.

Healthy designs use both, sequenced: positive feedback dominates early (snowballing feels rewarding), negative feedback gains weight late (the leader is a target; scoring turns to diminishing returns). Common dampeners for positive loops: diminishing returns on repeated purchases, escalating costs, scoring that rewards diversification, and end conditions that arrive before the engine goes exponential.

**AI-checkable:** plot per-player income/points per turn from simulated or logged games. A healthy curve rises and then bends (dampening visible). An exponential curve that never bends means the game ends by clock, not by climax — whoever entered the exponential first won at that moment.

---

## 9. Pacing and the Game Arc

A good game has a shape. Players describing a game as "having a great arc" or "feeling flat" are describing the emotional curve of play.

Borrowing from drama (Freytag) and Japanese theatrical pacing (**Jo-Ha-Kyu** — beginning, break, rapid):

- **Opening (Jo).** Calm, expansive. Players survey options, set goals, plant seeds. Decisions are wide and slow.
- **Middle (Ha).** Strategies clarify; conflict crystallizes. Choices narrow as commitments lock in. Tension rises.
- **Endgame (Kyu).** Fast, sharp, climactic. Resources are scarce, every action matters, the winner emerges through a final flurry.

Tension is built through four levers: **escalating stakes** (later actions matter more), **shrinking options** (commitments accumulate), **information revelation** (hidden things come out), and **visible timers** (the end is approaching and everyone can see it).

Symptoms of a broken arc:

- The game is decided long before it ends. → Cut the back half, or add a real climax (end-game scoring, revealed objectives).
- Every turn feels like every other turn. → The decision space isn't evolving; add state that accumulates and changes what's possible.
- The endgame is upkeep, not climax. → Front-load bookkeeping; back-load drama.
- The first turns are the hardest of the game (widest options, least context). → Constrain early turns: fewer starting options, a guided opening, or asymmetric starting positions that suggest a direction.

**AI-checkable proxy:** track "decision weight" per turn in simulation — number of legal moves and the spread of their evaluated values. A healthy arc typically narrows options while raising the stakes-gap between good and bad moves. A flat line predicts a flat game.

---

## 10. Player Interaction Is the Free Replayability Engine

Solo puzzles eventually get solved. Other humans never do.

Forms of interaction, from low to high:

- **Indirect.** Drafting from a shared pool, racing to objectives, scoring on the same axes. Players affect each other only through scarcity.
- **Spatial.** Sharing a board where positions matter: blocking, area control, adjacency.
- **Direct.** Attacking, stealing, denying. High stakes; risks "feel-bad" moments if not designed carefully.
- **Negotiation and table talk.** Trading, alliances, betrayal. The most generative form because it brings players' personalities into the game.
- **Bluffing and hidden information.** Players read each other, not just the board.

More interaction means more replayability, but also more potential for negative experiences (kingmaking, ganging up, hurt feelings). Two guardrails for direct interaction: attacks should cost the attacker something (no free griefing), and being attacked should leave the victim *decisions*, not just losses. A game with strong negotiation needs strong incentives for cooperation *and* for self-interest, so deals feel earned rather than forced.

**Multiplayer solitaire check:** if a player could take their whole turn without looking at anyone else's board, interaction is near zero — fine only if the stated aesthetic (§1) is contemplative parallel puzzling, in which case make turns simultaneous and short.

**Cooperative games** create different dynamics: shared goals foster communication and empathy, but introduce the **alpha player problem** — one experienced player tells everyone what to do. Counter it structurally, not with etiquette: hidden hands with restricted communication, simultaneous decisions, asymmetric roles no one player can fully evaluate, or real-time pressure. Co-ops also need a tuned loss rate: a co-op players always beat is a chore, and roughly a 30–50% win rate for a group at the intended difficulty keeps tension alive.

---

## 11. Turn Structure, Action Economy, and Downtime

The turn is the game's unit of experience. Most "boring game" complaints are turn-structure problems, not content problems.

- **Downtime** — time between my decisions — is the silent killer. Budget it: in an N-player game, a player waits roughly (N−1) × turn length between moves. Long, complex turns in a 5-player game multiply into minutes of dead time. Fixes: shorter turns with more of them, simultaneous phases, decisions that occur on *other* players' turns (reactions, trades, card play), and planning that can be done while waiting.
- **Turn atomicity.** Prefer turns that are one crisp decision ("place a worker") over turns that are a paragraph of upkeep plus three sub-decisions. Many short turns keep everyone engaged and shrink the AP surface.
- **Action selection is a genre-defining choice.** The main patterns and what they buy:
  - *Fixed action menu* — simplest to learn; depth must come from board state.
  - *Action points* — flexible; high AP risk (players optimize allocation every turn).
  - *Worker placement* — actions are scarce and blockable; interaction built in.
  - *Card-driven / deckbuilding* — hand as constraint; input randomness creates fresh turns.
  - *Role selection / drafting (Puerto Rico, Citadels)* — choosing also gives to or denies others; interaction through selection itself.
  - *Rondel / time-track* — cheap actions cost future tempo; pacing built in.
  Choose the one whose built-in properties match the aesthetic target rather than bolting properties on later.
- **Kill dead turns.** A turn where the player has nothing meaningful to do (forced pass, pure upkeep, "draw and discard") should be automated, fused into other turns, or deleted.

---

## 12. Victory Conditions Frame Everything

How a game ends determines how it is played. Players reverse-engineer their behavior from the win condition, so the win condition is a steering wheel: **whatever you attach points to is what the game is about**, regardless of the theme.

Common structures:

- **Race** — first to X. Sharp and tense; rewards focus; risks degenerate strategies if X is reachable in only one way.
- **Accumulation** — most points at game end. Flexible, supports multiple paths; risks devolving into point-salad where everything scores and nothing matters.
- **Elimination** — last one standing. Strong drama; severe risks of player elimination and kingmaking.
- **Objective-based** — secret or public goals. Encourages varied play; gives trailing players hidden lifelines.
- **Idiosyncratic** — game-specific conditions (e.g., highest *minimum* across tracks in *Ingenious*). Forces unfamiliar shapes of play.

Design considerations:

1. **End-game scoring** converts a tight game into a dramatic finale: revealed objectives, bonuses for long-term commitments, set-collection multipliers. Size the swing carefully — big enough that no one checks out early, small enough that in-game play still mattered.
2. **Multiple paths to victory** are a major replayability driver. Three viable strategies is three games in the box; one is one. Verify viability by simulation or dedicated playtests where each path is forced — "technically possible but always loses" is not a path.
3. **End triggers** should be visible and player-influenceable. The best endings are ones a player *chose* to trigger at a moment that favored them — that's one more meaningful decision.
4. **Ties and near-ties** need clean, thematic tiebreakers decided in advance, not errata.

---

## 13. Balance: Fairness Without Sameness

Balance does not mean every option is equal. It means **no option is dominant and every option is viable in the right context.**

### First-player advantage

Most turn-based games structurally favor whoever goes first (or last). Fixes: compensation (later players start with more resources or points — Catan-style snake drafts, extra coins), auctions for turn order, or making turn order itself a dynamic resource players can spend position to change.

### Asymmetric factions

Different powers create variety — and require enormous testing to balance. The goal is not equal power but **equal viability**: each faction has a credible path to victory that exploits its strengths and survives its weaknesses. Balance through trade-offs, not by making everyone equally good at everything. Asymmetry also multiplies the learning burden (you must learn *every* faction to play against them well) — spend it where it pays.

### Costing and the numbers

Most balance work is arithmetic, and an AI is well-suited to it:

- **Cost everything in a common currency.** Estimate each card/action/upgrade's value in a base unit (points, or the resource everything converts to) and compare price to value. Outliers in either direction are the first things playtesters will find; find them first.
- **Price flexibility.** An effect that is *sometimes* usable should cost less than an always-usable one; an effect that combos widely should cost more than its standalone value.
- **Beware false precision.** If two costs differ by amounts smaller than one turn of income, the difference is noise — round to values players can feel. Small integers beat decimals; a 6/5/4 spread reads, a 6.5/6/5.5 spread doesn't.
- **Simulate before tabling.** Scripted policies playing thousands of games will find dominant strategies, dead cards, and degenerate openings faster than any playtest group. Simulation cannot tell you the game is *fun* — only that it is not *broken*.

### Feedback-loop tuning

See §8. The sequencing rule bears repeating: positive feedback early for momentum, negative feedback late for tension. A leader who can never be caught and a leader who can never stay ahead are both failures.

---

## 14. Fit: Player Count, Length, and Audience

A game is designed *for* someone, and misfit here defeats good mechanics.

- **Player count changes the game.** Scarcity, downtime, negotiation dynamics, and kingmaking all scale with player count. Test every advertised count; the count where interaction collapses (often 2) or downtime explodes (often 5+) needs either dedicated rules or removal from the box. Beware mechanics that only work at one count (voting at 2, negotiation at 2, area control at high counts diluting to nothing).
- **Length must match decision density.** The game should end while players still want one more turn. A common failure: the mechanics support 45 minutes of interesting decisions inside a 90-minute structure. Cutting a game's length by a third is the single most frequent improvement in development.
- **Complexity must match audience.** A family game with a hidden 30-minute rules overhead, or a gamer's game with nothing to master, are both misfits regardless of quality. Name the audience in the concept sentence (§1) and audit against it.
- **Setup and teardown count.** A brilliant 20-minute game with 15 minutes of setup gets played once. Design components and state toward fast setup (player boards that start identical, decks that don't need sorting, no fiddly sorting-by-type).

---

## 15. Replayability Is Not Variability

The single most-misunderstood concept in modern design:

- **Variability** — the game presents different starting conditions, components, or scenarios each play.
- **Replayability** — players want to play again.

These are correlated but independent. Chess and Go have **zero** variability — identical setup every time — and have been replayed for centuries. Plenty of games with huge decks and modular boards get repetitive in five plays.

What actually drives replayability:

1. **Decision depth** — enough strategic space that you keep finding new ideas.
2. **Player interaction** — other humans are an infinite novelty source in a way random tile draws are not.
3. **Emergent gameplay** — simple rules combining into situations the designer never authored.
4. **A skill curve** — you can see yourself getting better; new layers reveal themselves on play 5, 20, 100.
5. **Variability as a multiplier, not a substitute** — it extends the life of a game that is already good and rescues nothing.

Design the depth first. Add variability last.

---

# Part III — Diagnosis and Process

## 16. Pitfalls: Symptom → Diagnosis → Fix

The recurring failure modes. Most great games are partly defined by which one they decided to solve. Note the dependencies: kingmaking is usually downstream of runaway leaders, and player elimination is a special case of losing agency before losing the game.

| Symptom (what you observe) | Likely diagnosis | Fixes, cheapest first |
|---|---|---|
| Winner is obvious with 30%+ of the game left | **Runaway leader** — uncapped positive feedback (§8) | End the game sooner; add end-game scoring swings; hidden scores; diminishing returns on the leading strategy; leader-becomes-target dynamics |
| A player who can't win decides who does | **Kingmaker** — usually downstream of runaway leader | Fix the leader problem first; keep standings tight; give trailing players their own goals to the end; avoid mechanics where one player's cheap choice decides another's fate |
| One player takes minutes per turn while others stew | **Analysis paralysis** — decision space too wide/flat, all information public | Hidden information (caps calculability); fewer-but-more-distinct options; simultaneous or shorter turns; timers as a last resort |
| Someone is out of the game and watching | **Player elimination** | Avoid elimination in games over ~30 minutes; end the game shortly after first elimination; convert elimination to a comeback state or a meaningful side role |
| Game decided in first few turns; rest is execution | **Snowballing engine** — compounding returns with no dampener | Diminishing returns; scoring that rewards diversification; end-game scoring on axes the engine doesn't feed |
| Players consult rulebook more than each other | **Rules overhead** — complexity mislocated (§3) | Cut, fuse, generalize; move info onto components (icons, printed reminders); delete exception rules by fixing their parent rule |
| Everyone plays their own board; no one looks up | **Multiplayer solitaire** (§10) | Shared pools and drafting; shared scoring axes; spatial contention — or embrace it: simultaneous turns, shorter game |
| Players ignore a mechanic entirely | **Dead mechanic** — costs more attention than it pays out | Delete it; if it's load-bearing for theme, fuse it into a mechanic players already touch |
| New players lose badly and don't ask for a rematch | **Brutal skill curve** — no luck valve, open info, deep calculation | Add input randomness; hide some information; add catch-up scoring; provide a guided opening |
| Wins feel arbitrary; strong play isn't rewarded | **Excess output randomness** (§5) | Convert output randomness to input; add mitigation (rerolls, modifiers); many small rolls instead of few big ones |
| The end arrives as a surprise or a relief | **Broken arc** (§9) | Visible end timer; escalating stakes toward the end; cut the flat back half |

---

## 17. Improving an Existing Game: A Protocol

Improving is not designing backwards — the constraint is that players (or a codebase, or printed components) already embody the current rules. Every change has a blast radius.

1. **Re-derive the aesthetic sentence (§1) from the game as it is.** If you can't, that's finding #1: the game doesn't know what it wants to be, and no mechanical tuning fixes that.
2. **Collect symptoms before proposing changes.** From playtests, reviews, or simulation logs: where do turns go dead, when does the winner become known, which options are never taken, which rules are always looked up or misplayed. A rule that is repeatedly misplayed *in the same direction* is a signpost — the misplay is often the better rule.
3. **Diagnose via §16 and trace to root cause.** Resist fixing symptoms in place; a catch-up mechanic bolted onto a runaway-leader economy treats the fever, not the infection.
4. **Generate the fix list in this order:** delete a rule → retune a number → change a trigger/timing → merge two mechanics → *and only then* add a new rule. Additions must clear the §3 bar (multiple new decisions, no new exceptions).
5. **One change per test cycle.** Five simultaneous changes means zero attributable results.
6. **Run the regression list after each change:**
   - Does the fix contradict the aesthetic sentence?
   - Did it break a balance elsewhere (a cost that was fair under the old rule)?
   - Did it lengthen the game, the teach, or the setup?
   - Did it remove a decision players loved along with the problem?
7. **Know when you're polishing vs. rebuilding.** If the same root cause survives three different fixes, the problem is structural — the economy, the win condition, or the interaction model — and honest work means redesigning that layer, not sanding it.

---

## 18. The Design Process Is Iteration

You will not design a great game on paper. You will design a **playable mediocre version of a great game**, then iterate until it is good.

The honest version of the process:

1. **Concept.** Name the experience, audience, player count, and time budget.
2. **Paper prototype.** Ugly, index cards, made to be thrown away. Functionality, not aesthetics.
3. **Solo, simulated, and friend testing.** Find catastrophic problems first — broken loops, unclear rules, dead turns. This is where AI simulation earns its keep: dominant strategies and degenerate math should die here, before humans spend an evening on them.
4. **Blind playtesting.** Strangers read the rules and play without you in the room. This is where you learn what your rulebook actually says.
5. **Wide playtesting.** Different counts, skill levels, demographics. Look for who *isn't* having fun and why.
6. **Polishing.** Balancing, trimming, smoothing the on-ramp, refining components.

Principles for iteration:

- **Iterate fast and cheaply.** A pretty prototype is harder to throw away than an ugly one.
- **Watch, don't ask.** Players rationalize their experience; their faces during the game are more honest than their words after it.
- **Distinguish bug reports from design suggestions.** The reported *problem* is nearly always real. The proposed *fix* is data, not gospel.
- **Kill darlings.** The mechanic you are most excited about is the most likely one ruining the game.
- **One change at a time.** Five changed rules between playtests means you can't tell which fix worked.

A good game emerges from dozens of plays, not from a clever idea. Plan accordingly.

---

## 19. Lessons from Games That Lasted

Durable games across centuries and modern history show the same patterns:

- **Chess, Go, Mancala.** Zero variability, tiny rule sets, inexhaustible depth. Depth lives in the *interaction* of mechanics, not the *number* of mechanics.
- **Catan.** Made resource strategy legible to non-gamers via probability pips printed on components — lowered the cognitive cost of strategy without lowering the strategy.
- **Ticket to Ride, Carcassonne.** Simple core, clear objectives, gentle interaction, fast onboarding: the gateway-game template.
- **Twilight Struggle, Through the Ages, Pax Pamir.** Deep strategy from the interaction of relatively few systems, themed so tightly the rules feel like history rather than mechanics.
- **Spirit Island, Pandemic Legacy.** Cooperative designs that resist the alpha player structurally, through asymmetric powers and information hiding.

Different paradigms, same principles underneath: meaningful choices, elegance, thematic coherence, an arc, and depth that emerges from interacting parts.

---

## A Designer's Checklist

Run a candidate design against this list before declaring it ready. Each item cites the section to consult on a "no."

**Concept and choices**
- [ ] Can you state the target emotion, audience, player count, and length in one sentence? (§1, §14)
- [ ] Does each turn present at least one meaningful choice with real trade-offs? (§2)
- [ ] Would a greedy/random policy lose convincingly to a thoughtful one in simulation? (§2, §5)

**Elegance and theme**
- [ ] Is there a rule you're keeping out of fondness that could be cut? (Cut it.) (§3)
- [ ] Do mechanics and theme reinforce each other — would a new player *guess* most rules correctly from the theme? (§4)

**Systems**
- [ ] Is randomness predominantly input-side, with mitigation for any output randomness? (§5)
- [ ] Is the information players need for good decisions visible at the table? (§6)
- [ ] Does every resource have pressure and at least two competing uses? (§8)
- [ ] Do positive feedback loops have late-game dampeners? (§8, §13)
- [ ] Does the game have an arc — a different feel in early, mid, and endgame — with a visible, influenceable end? (§7, §9, §12)
- [ ] Is downtime bounded — could every player at max count stay engaged between turns? (§11, §14)
- [ ] Are there 2–3 victory paths that actually win in testing, not just in theory? (§12)

**Failure modes and process**
- [ ] Stress-tested for runaway leaders, kingmaking, AP, elimination, and multiplayer solitaire? (§16)
- [ ] Has the rulebook been read cold by someone who wasn't in the room when you wrote it? (§18)
- [ ] Does play generate stories players retell afterward? (§7, §10)
- [ ] Have you played it enough to be sick of it — and do you still want one more game? (§15)

If all are yes, you may have something good. The only way to find out is to put it on a table with strangers.

---

## Sources

### Books (canonical references)

- *Characteristics of Games* — George Skaff Elias, Richard Garfield, K. Robert Gutschera (MIT Press)
- *Uncertainty in Games* — Greg Costikyan (MIT Press)
- *The Art of Game Design: A Book of Lenses* — Jesse Schell
- *Building Blocks of Tabletop Game Design* — Geoffrey Engelstein & Isaac Shalev
- *Thematic Integration in Board Game Design* — Sarah Shipp (Routledge)

### Articles and essays

- [MDA: A Formal Approach to Game Design and Game Research (PDF) — Hunicke, LeBlanc, Zubek](https://users.cs.northwestern.edu/~hunicke/MDA.pdf)
- [MDA Framework — Wikipedia](https://en.wikipedia.org/wiki/MDA_framework)
- [Meaningful Choices — University XP](https://www.universityxp.com/blog/2019/8/6/meaningful-choices)
- [Meaningful Choices in Board Games — BoardBrain Labs](https://boardbrainlabs.com/meaningful-choices-in-board-games/)
- [Player Agency — Ludogogy](https://ludogogy.professorgame.com/article/what-is-player-agency/)
- [The Art of Player Agency: A Game Designer's Guide — Number Analytics](https://www.numberanalytics.com/blog/art-of-player-agency-game-design)
- [What Makes a Game System Elegant? — Léo Lesêtre](https://leolesetre.medium.com/what-makes-a-game-system-elegant-5c73b4e9b50e)
- [Elegance in Game Design (PDF) — Cameron Browne](http://cambolbro.com/cv/publications/browne-elegance.pdf)
- [Elegance — Andrew Fischer Games](https://andrewfischergames.com/blog/elegance)
- [Tesler's Law — BG-PX](https://bg-px.com/2025/10/30/teslers-law/)
- [Defining Complexity and Depth in Game Design — BoardGameGeek](https://boardgamegeek.com/blogpost/108921/defining-complexity-and-depth-in-game-design)
- [The Depth:Complexity Ratio — daniel.games](https://daniel.games/the-depth-complexity-ratio/)
- [Layers of Theme — Skeleton Code Machine](https://www.skeletoncodemachine.com/p/layers-of-theme)
- [Variable Replayability — There Will Be Games](https://therewillbe.games/articles-essays/8942-variable-replayability)
- [The Variability of Replayability — The Giant Brain](https://giantbrain.co.uk/2023/02/11/the-variability-of-replayability/)
- [Repeatable Replay — Tabletop Games Blog](https://tabletopgamesblog.com/2024/02/20/repeatable-replay-the-importance-of-replayability-of-board-games-topic-discussion/)
- [The Art of Replayability: Designing Games that Endure — BG Games](https://bggames.medium.com/the-art-of-replayability-designing-games-that-endure-063eea47541f)
- [Emergent Gameplay — Grokipedia](https://grokipedia.com/page/Emergent_gameplay)
- [Jo-Ha-Kyu and the Art of Game Design — Engagement Game Lab](https://engagementgamelab.wordpress.com/2013/12/13/jo-ha-kyu-and-the-art-of-game-design/)
- [Freytag's Pyramid and the Importance of a Game Arc — Skeleton Code Machine](https://www.skeletoncodemachine.com/p/game-arcs)
- [Board Game Pacing — Brandon the Game Dev](https://brandonthegamedev.com/board-game-pacing-keeping-your-game-interesting/)
- [How to Create Tension in Your Game — Board Game Design Course](https://boardgamedesigncourse.com/game-mechanics-how-to-create-tension-in-your-game/)
- [Game Elements: Interaction — League of Gamemakers](https://www.leagueofgamemakers.com/game-elements-interaction/)
- [Creating Engaging Player Interactions — Mahtgician Games](https://mahtgiciangames.com/blogs/the-creative-workshop-game-design-blueprints/creating-engaging-player-interactions-in-games)
- [Cooperative vs. Competitive Board Games (study) — PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8248432/)
- [The Runaway Leader "Problem" — University XP](https://www.universityxp.com/news/2023/11/28/the-runaway-leader-problem)
- [Is Kingmaking a Problem to Be Solved? — Skeleton Code Machine](https://www.skeletoncodemachine.com/p/kingmaking)
- [Analysis Paralysis (Common Problem #1) — Board Game Designers Forum](https://www.bgdf.com/forum/archive/archive-game-creation/topics-game-design/tigd-analysis-paralysis-common-problem-1)
- [14 Ways of Reducing Analysis Paralysis — Make Them Play / The Game Crafter](https://news.thegamecrafter.com/post/156270446929/14-ways-of-reducing-analysis-paralysis-in-your)
- [Catch-Up Mechanisms — The Thoughtful Gamer](https://thethoughtfulgamer.com/2017/03/28/catch-up-mechanisms/)
- [Feedback Loops in Games — Systems and Us](https://systemsandus.com/2015/01/04/the-feedback-loops-in-games-what-makes-monopoly-world-of-warcraft-and-mario-kart-so-much-fun/)
- [Game Systems: Feedback Loops — Machinations.io](https://machinations.io/articles/game-systems-feedback-loops-and-how-they-help-craft-player-experiences)
- [What Is an Asymmetric Board Game? — Meeples Corner](https://meeplescorner.co.uk/blogs/boardgame-glossary/what-is-an-asymmetric-board-game)
- [Thoughts on Asymmetry — The Thoughtful Gamer](https://thethoughtfulgamer.com/2022/07/01/thoughts-on-asymmetry-part-1-classification/)
- [Losing Balance — Tabletop Games Blog](https://tabletopgamesblog.com/2025/12/02/losing-balance-the-role-of-balance-in-board-games-topic-discussion/)
- [How Victory Conditions Frame Play — Ludogogy](https://ludogogy.professorgame.com/article/how-victory-conditions-frame-play/)
- [Late Game Structures: End Conditions — Games Precipice](https://www.gamesprecipice.com/endings/)
- [Victory Conditions Other Than Victory Points — Game Developer](https://www.gamedeveloper.com/game-platforms/victory-conditions-in-board-games-other-than-victory-points)
- [Tabletop Game Prototyping, Playtesting, and Development — Stonemaier Games](https://stonemaiergames.com/tabletop-game-prototyping-playtesting-and-development/)
- [The Four Stages of Board Game Prototyping — Pine Island Games](https://www.pineislandgames.com/blog/four-stages-of-prototyping)
- [Prototyping, Playtesting, Iteration & Fun — Myk Eff](https://medium.com/understanding-games/prototyping-playtesting-iteration-fun-18d002c500b2)
- [Explore Guiding Principles in Board Game Design — McMeeple Publishing](https://mcdavittpublishing.com/blog-posts/my-guiding-principles)
- [Essential Principles for Mastering Board Game Design — Asia Pack](https://asiapack.com/essential-principles-for-mastering-board-game-design/)
- [Board Game Design Lab — Design Theory](https://boardgamedesignlab.com/design-theory/)
- [Board Games with Great Lessons for Accessible Design — Meeple Like Us](https://www.meeplelikeus.co.uk/games-with-great-design-lessons-for-accessibility/2/)
