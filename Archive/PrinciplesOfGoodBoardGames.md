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

**Structure.** Parts I–III (§1–19) are the general theory — read them for any game. **Part IV (§20–26) holds specialist chapters** that Parts I–III only gesture at: cooperative design, attrition economies, onboarding, accessibility, digital implementation, player psychology, and measurement. Read the ones your game is standing on.

**A note on section numbers.** Numbers §1–19 are **stable and never renumbered** — other documents cite them. New material is appended with new numbers rather than inserted, and existing sections gain pointers to it. If a citation elsewhere looks off by a section or two, trust the *title* over the number and fix the citation.

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

**The third option everyone forgets: deterministic escalation.** Uncertainty and *randomness* are not the same thing. A rule that says "this gets worse every time you do it, by a fixed amount, announced in advance" produces dread, planning pressure, and a felt threat — with zero variance. Players still don't know what will happen, because they don't know what *they* will be forced to do. Deterministic escalation is the right tool whenever the design promises that losses will be legible: a fixed, published penalty that compounds reads to the player as *the world's rule*, while the same pressure delivered by dice reads as *the game cheated me*. Reach for it before reaching for a die, especially for punishments.

**Swinginess is not variance.** Two games can have identical total randomness and feel completely different. What players object to is *swing*: a single event that moves the outcome further than a turn of good play can move it back. Audit the largest single random delta in the game and compare it to a strong turn's output. If one draw is worth three turns, the game is swingy no matter how tame its average variance looks. See §25 for why the *feeling* of unfairness tracks swing and salience, not expected value.

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

> **This section assumes a growth economy** — sources exceed sinks and players get richer. Survival, crisis, and horror games run the opposite shape, and most of the advice above inverts when they do. See **§21 — Attrition and Negative Economies**.

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

**Cooperative games** create different dynamics: shared goals foster communication and empathy, but introduce the **alpha player problem** — one experienced player tells everyone what to do. Counter it structurally, not with etiquette: hidden hands with restricted communication, simultaneous decisions, asymmetric roles no one player can fully evaluate, or real-time pressure. Co-ops also need a tuned loss rate: a co-op players always beat is a chore.

> Co-op design has enough distinct failure modes to need its own chapter — including the win-rate question, which is more contested than the sentence above suggests. See **§20 — Cooperative Games Are a Different Genre**.

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
| One player narrates everyone else's turn | **Quarterbacking / alpha player** (§20) | Private hands; simultaneous commitment; asymmetric knowledge; per-player secret objectives — structural fixes only, never etiquette |
| The co-op group finds one line and repeats it every game | **Solved co-op** (§20) | Vary the pressure, not the board; hidden or shuffled threat order; make the optimal line depend on information revealed after commitment |
| A player who fell behind can't act meaningfully but isn't out | **Death spiral** (§21) | Individual-level catch-up valve; floor the penalty; convert the spiral into a countdown the *team* can spend resources on |
| Players win but describe it as "we just didn't die" | **Attrition with no crescendo** (§21) | Give the endgame a spend-it-all outlet; add a payoff the accumulated hardship unlocks |
| Everyone wins every time and stops caring | **Untuned difficulty** (§20) | Raise pressure before adding rules; add a difficulty axis independent of length |
| New group bounces off before their first full game | **Onboarding cliff** (§22) | Guided opening; scripted first round; intro mode at full length; move reference onto components |
| A player can't read the board from where they sit | **Single-channel information** (§23) | Double-code everything (color + shape + text); audit contrast and type size; give every audio cue a visual twin |

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

# Part IV — Specialist Chapters

Parts I–III apply to any game. These chapters go deep on situations that break the general advice, and are worth reading only when your game is standing on one of them.

## 20. Cooperative Games Are a Different Genre

A co-op is not a competitive game with the conflict removed. Removing opponents deletes the engine that made the design work — replayability from other humans (§10), balance from mutual pressure, arc from a tightening race — and every one of those has to be rebuilt from parts. Three problems are specific to the genre and are the ones that kill co-ops.

### 20.1 Quarterbacking: the defining failure

The **alpha player** (or **quarterback**) problem: one player, usually the most experienced, solves the shared puzzle out loud and directs everyone else's turns. It is the most-cited complaint about co-op games, and the reason is structural rather than social — *if all information is public and the goal is shared, the game has exactly one optimal line, and the table's strongest calculator will find it.* Everyone else becomes a hand that moves pieces.

Treat this as a design defect, not a personality defect. Etiquette fixes ("please let people take their own turns," an optional timer) put the burden on the person being steamrolled and reliably fail. The structural fixes, roughly in order of cost:

- **Private hands.** The cheapest fix that does anything. Others can advise but cannot read your actual options, so the final call is genuinely yours. Weak on its own: if the hand is small and the board is everything, the alpha still drives.
- **Simultaneous commitment.** Everyone decides at once, reveals together. This kills the sequential window where advice is given, and it is usually a one-rule change. The most under-used lever in the genre.
- **Restricted communication.** *Hanabi* is the canonical extreme: the only legal communication is a formal clue. Extremely effective, but it fights the medium — the social table is why people are playing at all — so most games should reach for a partial version (e.g. communication only between co-located players, or only at specific moments) rather than a blanket gag.
- **Asymmetric roles no one player can fully evaluate.** If every character plays a different game with different constraints, one brain cannot compute the whole table's optimum. This is the fix that costs nothing at play time and everything at design time, and it is the one worth paying for.
- **Deliberate information overload.** Give the table more state than any single person can hold. The alpha can still *lead*, but must delegate — and delegation is what cooperation actually looks like. Roles plus time pressure produces this cheaply.
- **Roleplay and embodiment.** Rules and framing that make each player the authority on their own character ("only Rayman decides where Rayman sleeps") convert quarterbacking from optimal into rude. Soft, but it stacks well with the others.

**Diagnostic:** in a playtest, count the decisions per player that were *announced by someone else* before the owner spoke. If one player's suggestions precede a third of the table's turns, the structure is at fault.

### 20.2 The solved-co-op problem

A co-op is a puzzle, and puzzles get solved. Once a group finds the reliable line, the game is over forever — not lost, but finished, which is worse. Variability of setup (§15) delays this and does not prevent it, because a group that has solved the *system* re-solves each new layout in one play.

What actually resists solving:

- **Uncertainty that lands after commitment.** If the threat order is shuffled and revealed only after the team has committed, no fixed plan is correct. This is the one place a co-op *wants* some output randomness (§5) — but budget it, or losses stop feeling earned.
- **Pressure that adapts to the team's state.** A clock that advances faster when the team is doing well, or in response to what they leave undone, cannot be outrun by a memorized opening.
- **Asymmetric composition.** If the roster changes between plays, the optimal line changes with it. Three characters out of five is a different game from a different three.
- **Escalating difficulty dials the group chooses.** Solved at this level means "ready for the next one." This is the cheapest genuine answer and the reason nearly every modern co-op ships with one.

### 20.3 Tuning difficulty and the win rate

The most-argued number in co-op design, and the honest answer is that it depends on who you built it for.

- Surveyed players broadly say they want to win **50–75%** of the time and do not want to play ten times before their first win. A game that never rewards a group in its first evening loses that group.
- Meanwhile, the flagship difficult co-ops sit near **40%** win rates — *on their highest difficulty settings*, chosen deliberately by experienced groups.

Those two facts are not in conflict; they describe different players. The resolution is not to pick a number but to **ship an axis**, and the axis must be *independent of the game's length and arc*. A common and costly mistake is to implement "easy" as "shorter": length and difficulty are different dials, and collapsing them means a new group can never experience the full arc without also facing the full challenge. Separate them — scale the clock, the enemy numbers, or the loss threshold, and let the group choose.

Two findings worth holding together when picking the default:

- **Losing has to be genuinely possible or nothing else works.** Emotional investment and immersion measurably drop when players can handle every crisis comfortably — the danger has to be real for the tension to be real. In a co-op, the possibility that *everyone* loses together is what makes winning mean anything.
- **But losing has to leave the table wanting a rematch.** The design target is not "hard"; it is *"we nearly had it."* Near-misses drive replay far more strongly than either comfortable wins or thorough beatings — so tune for close finishes, and make sure the game's ending ritual shows the table *how* close it was.

**Design the loss, not just the difficulty.** Losses should arrive as a legible chain of decisions ("we left the Deerclops standing for three days"), land at the end rather than being obvious for the last hour, and take under a minute to resolve. A loss the table can narrate is a rematch; a loss they can only shrug at is a shelf.

### 20.4 Other co-op-specific notes

- **Traitor variants** solve quarterbacking almost completely — nobody trusts the alpha — at the cost of turning the game into a social-deduction game, which is a different aesthetic (§1). Add deliberately or not at all.
- **Player elimination is worse in a co-op**, not better: the eliminated player has no side to root for and nothing to do. Down/ghost states that keep the player at the table with a reduced but real role are near-mandatory in any co-op over 30 minutes — and note that a fully-informed, freely-talking ghost is a *promoted* alpha player, so constrain what the downed player may say.
- **Difficulty must scale with player count**, and rarely linearly. More players means more actions but also more targets, more downtime, and more quarterbacking surface. Test every advertised count against the win-rate band separately (§26).

---

## 21. Attrition and Negative Economies

§8 describes a growth economy: sources exceed sinks, players accumulate, the risk is a runaway leader. Survival, horror, crisis, and disaster games run the inverse — **sinks exceed sources by default, and the players' job is to lose slowly enough**. Almost every piece of §8 advice flips.

**What inverts:**

| In a growth economy | In an attrition economy |
|---|---|
| Positive feedback is the danger (runaway leader) | Positive feedback is the *reward* — the rare moment you get ahead |
| Negative feedback keeps the game close | Negative feedback is the **death spiral**, and it is the main threat to fun |
| Scarcity creates decisions | Scarcity is constant; the decision is *which* deficit to service |
| The arc rises toward a climax of power | The arc descends toward a climax of desperation |
| Balance question: can anyone run away with it? | Balance question: can a losing player still act? |

**The core number is the ledger.** Every attrition game has a per-round table of guaranteed drain versus maximum realistic restoration. Write it down explicitly — it is the single most important number in the design and the one most often left implicit. From it you get:

- **The maintenance tax:** what fraction of a player's resources (usually actions) is spoken for just to break even. A tax under ~25% reads as background pressure; over ~50% and the game is a treadmill where nothing but survival is ever affordable. Whatever number you choose, choose it on purpose.
- **The slack curve:** how much surplus a well-played round generates at each stage. Attrition games want this near zero and occasionally negative — but if it is *never* positive, players never get to do the interesting thing the drain is supposed to be interrupting.

**Design the escalation, not just the drain.** Crisis-shaped games run on four levers, and it is worth naming which one each rule pulls: **pressure** (constant background cost), **escalation** (the pressure grows over time), **attrition** (capability lost is not recoverable), and **loss conditions** (the visible cliff). A game that has only pressure feels flat; one that has only escalation feels scripted.

**The death spiral is the genre's signature bug.** A player low on a resource loses access to the actions that would restore it: too weak to fight means no food, means weaker still. This is positive feedback pointed downward, and it produces the co-op version of player elimination — someone still at the table, still nominally playing, with no meaningful decisions for the last third of the game. Fixes, cheapest first:

- **Floor the penalty.** Below a threshold, penalties stop compounding.
- **Give a valve at the bottom.** The desperate get one thing they didn't have: a free recovery action, a cheaper escape, a desperation bonus. Thematically this is adrenaline, and it costs one line of rules.
- **Make the spiral a team resource sink rather than a personal one.** If pulling someone out of the spiral is something the *others* can spend on, the spiraling player stays in the game socially even while weak — and the rescue is a story.
- **Convert the spiral into a countdown.** "You have three rounds before this becomes fatal" preserves agency where "you are now helpless" destroys it.

Check the team-level and the individual-level separately. A game can have excellent team catch-up (a global comeback threshold) while an individual player spirals to irrelevance untouched by any of it.

**Give attrition a crescendo.** The failure mode of a well-tuned attrition game is that winning feels like *not losing* — technically a victory, emotionally a shrug. The cure is an endgame outlet that lets the accumulated hardship be spent: a burn-it-all mechanic, a payoff that only a battered team can reach, a final push where every hoarded resource has one last use. Players should end the game empty, not merely alive.

---

## 22. Onboarding: The First Play Decides Everything

Most games are judged, permanently, on one play by people who learned them badly. Onboarding is design work, not documentation work, and it belongs in the rules rather than downstream of them.

**The rulebook serves three different readers**, and most rulebooks serve only the first badly:

1. **The learner**, reading cold, who needs the big picture before any detail. Give the goal and the shape of a turn *first* — specific rules are unlearnable until the reader knows what they are for.
2. **The refresher**, returning after six months, who needs setup and the turn sequence findable in ten seconds.
3. **The referee**, mid-game, who needs one specific edge case findable by index. This reader is why the rulebook needs a *reference* section that is not the *teaching* section — the two structures are incompatible and should not be the same pages.

**Move rules onto components.** Every rule printed on the thing it governs is a rule nobody looks up. Player boards that state their own powers, cards that state their own timing, tracks annotated with what happens at each threshold, iconography consistent enough to be read rather than translated. This is the highest-leverage onboarding work available and it also serves §3 (complexity moved out of the player's head) and §23 (accessibility).

**Structure the first play specifically:**

- **A guided opening.** Scripted or strongly-suggested first turns that demonstrate the core loop and teach good habits before the player is on their own. Cheap, effective, and it prevents the classic disaster of a new player making an unrecoverable turn-one mistake — remember that the opening turn is the hardest in most games (widest options, least context; §9).
- **An intro mode at full length.** Simplified rules, not a shortened game. Cutting the length to make it easier means new players never see the arc — the thing the game is actually *about* (§20.3).
- **Progressive disclosure.** Introduce subsystems in the order the game will need them, not all at setup. A rule that first matters on round four can be taught on round three.
- **Foreshadow severity.** A visual grammar that tells a first-time player how bad something is before they read it (severity dots, size hierarchy, color temperature) lets a novice brace correctly and lets a veteran plan. The same component teaching at two skill levels is the mark of good information design (§6).

**Setup and teardown are part of the experience** (§14), and in a teaching context they are also the first ten minutes of the table's attention. Spend them on anticipation, not sorting.

---

## 23. Accessibility Is Design, Not Accommodation

Accessibility work is usually framed as a compliance pass at the end. It is more useful to treat it as an information-design constraint from the start, because nearly every accessibility fix is also a *legibility* fix (§6) that helps everyone at the table — the player reading the board upside down from across the table has the same problem as the player with low vision, and the same solution.

**Double-code everything.** This is the single rule that matters most. Any information carried by color must also be carried by something else: shape, icon, position, texture, or text. Color-blindness is common enough that color-only coding will exclude someone at a typical table, and the fix costs nothing if done at design time and is expensive after art is finished. The same principle generalizes:

- **Every audio cue needs a visual twin.** Sound-only information excludes deaf and hard-of-hearing players *and* everyone playing muted, in a noisy room, or with a broken speaker. If a sound conveys something gameable, something visible must convey it too.
- **Every visual cue that matters at a distance needs to survive being small.** Test components at the size and distance they will actually be read.

**The other axes, briefly:**

- **Visual.** Contrast ratios that survive dim rooms; type sizes that survive across-the-table distance; avoid text over busy art; avoid conveying essential state in fine detail.
- **Physical / dexterity.** Fiddly stacking, tiny tokens, cards that must be held fanned, and precise placement are all barriers. Prefer chunky components and tolerant placement.
- **Cognitive.** Rules overhead, memory burden (§6), and long turns are accessibility issues as much as design ones. Reference cards, printed reminders, and public state help everyone.
- **Communication.** Games requiring rapid speech, real-time coordination, or reading tone exclude some players. If communication is the mechanic, that is a legitimate design choice — but be aware you are making it (see the §20.1 note on restricted communication).
- **Emotional / content.** Horror, gore, betrayal, and elimination affect people unevenly. Content notes and opt-out variants cost nothing.
- **Representation.** Who appears in the art and fiction determines who feels invited. It rarely stops anyone from playing; it routinely stops them from feeling like the audience.

**Digital implementations get one free win and one new trap.** Free: scalable text, recolorable UI, and screen-reader-friendly labels are all achievable in ways cardboard cannot manage. Trap: dense on-screen UI, small hit targets, timed prompts, and information conveyed only through animation or sound are new barriers the physical version didn't have.

---

## 24. Digital Implementation Changes the Design

Porting a board game to a screen or a virtual tabletop is not a neutral act of transcription. Automation changes what the design can afford, what players learn, and what you can measure — and each of those cuts both ways.

**What automation buys:**

- **A larger complexity budget.** Arithmetic, upkeep, lookups, and multi-step resolution become free. Rules that were unacceptably fiddly on cardboard become viable — conditional modifiers, per-character exceptions, state that would be tedious to track by hand.
- **Cheap hidden information.** Simultaneous secret commitment, per-player private state, and shuffled-and-hidden decks are trivial digitally and awkward physically. Since hidden information is the cheapest fix for both analysis paralysis (§16) and quarterbacking (§20.1), this is a significant and under-used gift.
- **Enforcement.** Illegal moves become impossible rather than merely forbidden, which removes an entire class of rules-lawyering and misplay.
- **Presentation.** Sound, lighting, and timing can carry tone in ways components cannot — and can make a moment land as an *event* rather than a state change.
- **Instrumentation.** Every game logs itself. See §26.

**What automation costs — and this is the part that gets missed:**

- **Hidden upkeep is hidden teaching.** The bookkeeping players do by hand is how they learn the system: moving the marker yourself is what teaches you the track exists and what feeds it. Automate it and players stop building a mental model — they follow prompts competently for an hour and could not explain the game afterward. Automate the *arithmetic*; keep the *acknowledgement*. Show what the automation did and why.
- **Never automate a decision.** The line is sharp and worth policing: if a step has a choice in it, it belongs to the player even when the optimal answer is computable. Convenience automation that quietly resolves choices is how a game becomes something players watch.
- **Prompts substitute for understanding.** A game that walks itself is wonderful for a first play and a problem for a fifth, when players want to plan ahead and the interface only ever tells them the current step. Surface the *whole* round structure, not just the current prompt.
- **Physical legibility is lost.** Table presence — the boss that is visibly bigger, the pile of resources you can see from across the table, someone's dwindling stack — does real information-design work (§6) that a screen replaces with numbers. Rebuild it deliberately with scale, position, and animation.
- **Fidelity drift.** Every automation decision quietly answers a rules question, and those answers become the de facto rules. If a print edition is intended, log each one; if not, accept that the implementation *is* the design and update the design document to match.

**For virtual-tabletop implementations specifically**, automate what is trivial in real life but tedious virtually (dealing, sorting, precise placement, arithmetic) and leave alone what is satisfying in real life (the roll, the reveal, the choice). The test is whether removing the step removes a decision or a chore.

---

## 25. Perceived Fairness: What Players Feel vs. What the Math Says

Players do not experience expected value. They experience salience, loss, and near-misses — and a game tuned only on the math will be described as unfair by people who cannot point to anything wrong with it.

**Loss aversion.** Losing something hurts roughly twice as much as gaining the equivalent feels good. The design consequences are direct:

- A penalty of −X is felt about twice as hard as a bonus of +X, so they do not trade one-for-one when balancing.
- **Taking away something a player already has** is far more painful than never granting it. Costs paid up front sting less than the same cost extracted later, and "you lose the thing you built" is the most memorably unpleasant event a game can produce. Use it on purpose or not at all.
- Loss aversion is also a *tool*: it is why a visible threat to something owned generates more tension per rule than any equivalent opportunity.

**Near-misses drive replay.** Almost winning is one of the strongest motivators to play again — stronger than a comfortable win. Design endings that are close and *show* that they were close. A results ritual that reveals how near the margin was converts a loss into a rematch. (This is also why the gambling industry engineers near-misses deliberately, and worth noting where the ethical line sits: engineering a *perception* of near-miss that the underlying math did not produce is manipulation. Making genuine closeness legible is design.)

**The illusion of control is real and double-edged.** Players credit outcomes to their decisions when given even token input. This makes cheap agency (choosing which die to reroll, which of two bad options) disproportionately satisfying — and it makes fake agency (choices that don't affect outcomes) genuinely effective at feeling good, which is exactly why it should be used sparingly. A player who eventually notices their decisions were decorative feels cheated retroactively about the whole game.

**Legibility beats fairness.** A punishing deterministic rule that players can see coming is accepted; a milder random one that arrives without warning is resented. If the design promises that losses are earned, every major penalty needs a visible causal chain back to a decision. Randomness placed *before* decisions preserves this; randomness placed after destroys it (§5).

**Practical audit:** for each major negative event in the game, ask (a) could the player see it coming, (b) could they have done something about it, and (c) will they be able to name the decision that caused it afterward. Three yeses is a good rule. Zero is a rule players will call unfair regardless of its expected value.

---

## 26. Measuring a Design

Parts I–III scatter "AI-checkable" notes throughout. This is the consolidated list — the metrics worth instrumenting, whether from simulation or from logged real play. All of them are proxies (see the note at the top of this document): they detect problems reliably and certify fun never.

**Outcome metrics**

| Metric | How to read it |
|---|---|
| **Win rate by difficulty and player count** | Must be measured per count, not extrapolated. Compare against the band chosen in §20.3. |
| **Loss cause distribution** | If 90% of losses come from one condition, the others are decoration. |
| **Time-to-decided** | Simulate forward from each game state: when does the outcome stop changing? Anything before ~75% through the game is a broken arc (§9) or a runaway leader (§16). |
| **Margin distribution** | Clustered near the wire means near-misses (§25) and rematches. Bimodal blowouts mean the game decides early. |

**Decision metrics**

| Metric | How to read it |
|---|---|
| **Dead-turn rate** | Fraction of turns with zero or one legal-and-sensible option. Should be near zero (§11). |
| **Decision density** | Legal options per turn, and the value spread between best and worst. A flat spread means the choice is fake (§2). |
| **Greedy-vs-thoughtful gap** | Win rate of a trivial policy against a good one. Near-equal means the decisions aren't doing work (§2). |
| **Skill-vs-random gap** | Good policy against random-legal. Near 50% means the game is mostly luck (§5). |
| **Largest single random swing** | Compare to a strong turn's output. Bigger means swingy (§5). |

**Content metrics** — the ones most often skipped, and the cheapest to collect

| Metric | How to read it |
|---|---|
| **Option utilization** | What fraction of cards, items, recipes, actions, or locations is *ever* used across many games? Anything at zero is dead content (§16) — cut it or fix it. This is the single most actionable report a simulator or session log produces. |
| **Strategy diversity** | Cluster winning games by their action mix. One cluster means one viable path, whatever §12 claims. |
| **Component viability spread** | Win rate conditional on each character, faction, or starting position. Equal viability, not equal power (§13). |
| **Rules-question frequency** | From real play: which rules get looked up or misplayed, and in which direction. A consistent misplay is a signpost that the misplay is the better rule (§17). |

**Experience proxies** — weakest, and still worth logging

| Metric | How to read it |
|---|---|
| **Turn duration distribution** | The tail matters more than the mean; a long tail is analysis paralysis (§16). |
| **Downtime per player** | Wall-clock time between one player's decisions. The number that decides whether a player reaches for their phone (§11). |
| **Total play time vs. target** | Consistently over means a pacing problem, and the fix is usually cutting a third (§14). |
| **Retention question** | "Do you want to play again right now?" — asked once, unprompted, immediately. The only real test (§15), and no simulation substitutes for it. |

**Method notes.** Change one thing per run (§17). Enough games to separate signal from variance — hundreds, not dozens, for win rates. Beware certifying balance with a simulator whose model of a subsystem (usually combat) is cruder than the real rules: a simulator can *rank* options honestly while getting absolute rates wrong, so trust the ordering and playtest the magnitude.

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

**If it's cooperative** (§20)
- [ ] Is quarterbacking prevented *structurally* — private information, simultaneous commitment, or roles one brain can't evaluate — rather than by etiquette or an optional timer?
- [ ] Can a group that has played ten times still be surprised, or have they solved it?
- [ ] Is the difficulty axis independent of the game's length, so a new group can play the full arc without full difficulty?
- [ ] Do losses arrive late, legibly, and fast — and does the ending show the table how close it was?

**If it's an attrition or survival economy** (§21)
- [ ] Is the per-round ledger — guaranteed drain vs. realistic restoration — written down, and is the maintenance tax a number you chose on purpose?
- [ ] Can an individual player spiral into having no meaningful decisions while the team is fine? Is there a valve at the bottom?
- [ ] Does the endgame give the accumulated hardship something to spend itself on, or does winning just mean not losing?

**Onboarding, access, and implementation** (§22–24)
- [ ] Is there a guided opening, and does the intro mode preserve the arc rather than just shortening it?
- [ ] Is every color-coded and every audio-coded piece of information double-coded?
- [ ] If it's digital: is arithmetic automated but every *decision* still the player's, and does the automation show its work?

**Measurement** (§26)
- [ ] Do you know your option-utilization rate — which cards, actions, and locations are never used in practice?
- [ ] Do you know when the outcome typically stops changing?

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

### Cooperative design (§20)

- [Roleplaying as a Solution to the Quarterbacking Problem — Analog Game Studies](https://analoggamestudies.org/2021/06/roleplaying-as-a-solution-to-the-quarterbacking-problem-of-cooperative-and-educational-games/)
- [Benching the Quarterback: How to Deal with Alpha Players in Co-op Games — Meeple Mountain](https://www.meeplemountain.com/articles/benching-the-quarterback-how-to-deal-with-alpha-players-in-co-op-games/)
- [Mitigating Quarterbacking in Cooperative Games — Don't Eat the Meeples](https://www.donteatthemeeples.com/mitigating-quarterbacking-cooperative-games/)
- [Board Game Quarterbacking: Player Problem or Game Problem? — Gideon's Gaming](https://gideonsgaming.com/board-game-quarterbacking-player-problem-or-game-problem/)
- [Reducing or Eliminating Quarterback Syndrome in Co-Op Games — Board Game Designers Forum](https://www.bgdf.com/forum/game-creation/mechanics/challenge-reducing-or-eliminating-quarterback-syndrome-co-op-games)
- [Difficulty in Cooperative Games — The City of Games](https://thecityofkings.com/news/difficulty-in-cooperative-games/)
- [The Allure of Struggle and Failure in Cooperative Board Games — Analog Game Studies](https://analoggamestudies.org/2016/05/the-allure-of-struggle-and-failure-in-cooperative-board-games/)
- [How to Design Cooperative Board Games: 6 Key Tips — Minifiniti](https://minifiniti.com/blogs/game-talk/how-to-design-cooperative-board-games-6-key-tips)

### Attrition, crisis, and survival economies (§21)

- [Escalating Disaster in Crisis Management Games — Skeleton Code Machine](https://www.skeletoncodemachine.com/p/crisis-management)
- [Survival Game Design: Principles, Examples, Template — Game Design Skills](https://gamedesignskills.com/game-design/survival/)
- [A 7-Step Framework for Game Economy Design — Game Dev Essentials](https://gamedevessentials.com/a-7-step-framework-for-game-economy-design/)
- [Philosophy of Tabletop Game Design: Engine Building — Vibrant Bliss](https://vibrantbliss.wordpress.com/2020/08/21/philosophy-of-tabletop-game-design-engine-building/)

### Onboarding and rulebooks (§22)

- [13 Ways Board Game Designers Can Make Games Easier to Learn and Teach — Tabletop Bellhop](https://tabletopbellhop.com/gaming-advice/boardgame-design-tips/)
- [How to Make the Perfect Board Game Rule Book — Brandon the Game Dev](https://brandonthegamedev.com/how-to-make-the-perfect-board-game-rule-book/)
- [How to Write a Board Game Rulebook — Hero Time](https://herotime1.com/design/how-to-write-a-rulebook-for-your-board-game/)
- [Nine Tips for Teaching Board Games — Don't Eat the Meeples](https://donteatthemeeples.substack.com/p/nine-tips-for-teaching-board-games)
- [Games UX: Building the Right Onboarding Experience — UX Collective](https://uxdesign.cc/games-ux-building-the-right-onboarding-experience-a6e99cf4aaea)

### Accessibility (§23)

- [Eighteen Months of Meeple Like Us: The State of Board Game Accessibility — Game Developer](https://www.gamedeveloper.com/audio/eighteen-months-of-meeple-like-us-an-exploration-into-the-state-of-board-game-accessibility)
- [Recommended Board Games for Colour Blindness — Meeple Like Us](https://www.meeplelikeus.co.uk/board-games-colour-blindness/)
- [How to Develop Visually and Physically Accessible Board Games — Brandon the Game Dev](https://brandonthegamedev.com/how-to-develop-visually-and-physically-accessible-board-games/)
- [Everyone at the Table: Accessibility and Universal Design in Board Games — Board Game Academics](https://boardgameacademics.com/everyone-at-the-table-accessibility-and-universal-design-in-board-games/)
- [Accessible Board Game Design: Tips for Inclusion — Rawstone Games](https://rawstone.net/2025/05/15/accessible-board-games-design-tips-for-inclusion/)

### Digital implementation (§24)

- [Exploring Automation in Digital Tabletop Board Games (PDF) — ResearchGate](https://www.researchgate.net/publication/220878919_Exploring_automation_in_digital_tabletop_board_game)
- [The Benefits of Digital Board Games Are Hurting the Medium — CBR](https://www.cbr.com/board-games-netplay-automation-tabletop-simulator/)
- [Board Game Design on Tabletop Simulator — TTS Blog](https://blog.tabletopsimulator.com/blog/board-game-design-on-tabletop-simulator-indie-game-lab-part-1)

### Player psychology (§25)

- [Board Game Design and the Psychology of Loss Aversion — GDC Vault](https://www.gdcvault.com/play/1024238/Board-Game-Design-Day-Board)
- [The Psychology of the Near Miss (PDF) — R. L. Reid](https://www.stat.berkeley.edu/~aldous/157/Papers/near_miss.pdf)
- [5 Cognitive Biases to Avoid in Board Games — The Thoughtful Gamer](https://thethoughtfulgamer.com/2017/05/12/5-cognitive-biases-avoid-board-games/)

### Emergent narrative and measurement (§7, §26)

- [Emergent Narrative & Storytelling in Board Games — Nerdlab Games](https://nerdlab-games.com/005-emergent-narrative-storytelling-in-board-games/)
- [Design Diary 2: Boardgame Narrative — Mighty Boards](https://mighty-boards.blog/design-diaries/design-diary-2-boardgame-narrative/)
- [Tabletop Game Playtesting: How to Playtest Your Board Game — Boardssey](https://boardssey.com/blog/board-game-playtesting-why-most-designers-fail)
- [Solo Modes in Board Games, Part Two: Automa — Punchboard](https://punchboard.co.uk/blog-solo-modes-in-board-games-part-two-automa/)
