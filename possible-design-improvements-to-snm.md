# Possible Design Improvements to Starve No More

A design review of **Starve No More** against the expanded
[`Archive/PrinciplesOfGoodBoardGames.md`](Archive/PrinciplesOfGoodBoardGames.md),
particularly its new Part IV chapters — §20 (cooperative games), §21 (attrition
economies), §22 (onboarding), §23 (accessibility), §24 (digital implementation),
§25 (perceived fairness) and §26 (measurement). Those chapters were written
because the general theory in Parts I–III didn't cover the genres this game is
actually standing on: a *cooperative*, *attrition-economy*, *digitally-implemented*
horror game.

> ## ✅ SHIPPED — all 17 findings were implemented in the 2026-07 design pass.
>
> **This document is now the rationale record, not a proposal list.** Read it
> for *why* a rule looks the way it does; read [`docs/design/`](docs/design/README.md)
> for what the rule actually is. The change itself is summarised in
> [`CHANGELOG.md`](CHANGELOG.md).
>
> Three things came out differently from the proposal, and the differences are
> recorded where the rules live rather than edited into the text below:
>
> - **Finding 10** turned out to describe a *second*, worse problem: the Truth
>   Run could not fire under any draw, because nothing ever incremented the clue
>   counter. Also, "shuffle one Clue into each third of the deck" is not
>   expressible in TTS (no insert-at-index); the shipped rule achieves the same
>   observable property at the Market refill. See §16.2.
> - **Finding 13's** Badminton-Court prediction proved **untestable in the
>   simulator** — every policy hardcodes the Basketball Court, so the probe
>   encodes the assumption the prediction was meant to test. The Cleanse
>   prediction was confirmed strongly. See §20.2 item 8.
> - **Finding 8** was measured rather than assumed: it moves the best line from
>   42% to 51%, and free Flee carries essentially all of that. Standard was
>   deliberately **not** retuned to compensate — see the note under "Suggested
>   order of work" below, which turned out to be the most important paragraph
>   in this document. See §20.1.

**This document proposes; it does not decide.** *(As written. All of it was
subsequently decided in favour and implemented.)* Each item was a candidate for
the design's own change protocol
([PrinciplesOfGoodBoardGames.md §17](Archive/PrinciplesOfGoodBoardGames.md)):
delete → retune → change a trigger → merge → and only then add.

**Priority legend** (matching `structuralimprovements.md`):
**P1** = high value / low risk · **P2** = worth doing, needs a decision ·
**P3** = nice-to-have or speculative.

**Status legend:** 🐛 defect (the design contradicts itself) · 🔧 tuning knob ·
➕ addition (must clear the §3 bar) · 📋 process/measurement.

---

## Summary

| # | Finding | Kind | Priority | Shipped as |
|---|---|---|---|---|
| 1 | Pristine Run is unachievable at 3–4 players | 🐛 | **P1** | §16.2 + `checkBonusVictories` |
| 2 | The default victory condition is circularly worded | 🐛 | **P1** | §16.1 |
| 3 | Night Sounds carries gameable information on audio alone | 🐛 | **P1** | §15.8 + `bannerOmen` |
| 4 | Stale §-references to the principles doc throughout `docs/design/` | 📋 | **P1** | `tests/test_doc_section_refs.py` |
| 5 | The attrition ledger is never written down | 📋 | **P1** | §8.5 |
| 6 | Anti-alpha defenses are mostly optional or cosmetic | ➕ | **P2** | §11.3 Secret Dusk (toggle) + §19.5 regrade |
| 7 | Difficulty and length are the same dial | 🔧 | **P2** | §17.2 Story mode |
| 8 | No individual-level death-spiral valve | ➕ | **P2** | §10.1.1 Last Nerve |
| 9 | Haunted deletes the co-op layer exactly when it's needed | 🔧 | **P2** | §10.1 Witness |
| 10 | Truth Run is a lottery, not a strategy | 🔧 | **P2** | §16.2 + `lua/clues.lua` |
| 11 | No guided opening; the hardest turn is turn one | ➕ | **P2** | §15.9 First Dawn |
| 12 | The §19.6 self-audit over-claims on victory paths | 📋 | **P2** | §19.6 item 5 |
| 13 | Option-utilization is unmeasured; the Visitor question stays open | 📋 | **P2** | §20.2 item 8 |
| 14 | Downtime relief cheaper than the Rotation variant | ➕ | **P3** | §11.2 + §18.13.1 Reactions panel |
| 15 | The Week in Review reports but doesn't hook | ➕ | **P3** | §16.5 margin + hook |
| 16 | No accessibility standard anywhere in the design | 📋 | **P3** | §18.19 |
| 17 | Solo mode is nearly free and shelved as an expansion | ➕ | **P3** | §20.3 Solo toggle |

---

# Part 1 — Defects

These are places where the design contradicts itself or a rule cannot do what it
says. They are cheap and unambiguous.

## 1. 🐛 **P1** — Pristine Run is unachievable at 3–4 players

**Evidence.** §16.2 defines the Pristine Run bonus victory as *"All five
characters are alive at game end."* But §6.6 states that a 3-player game uses
three characters and a 4-player game four, with the remainder becoming Visitor
NPCs who "depart at the next Dawn."

**The code agrees with the doc, which is the problem.**
[`lua/tick_victory.lua:400`](lua/tick_victory.lua) reads:

```lua
function checkBonusVictories()
    -- Pristine Run: all five characters alive (not Down)
    local allAlive = true
    local count = 0
    for color, char in pairs(gameState.activeChars) do
        count = count + 1
        if char.down then allAlive = false end
    end
    if allAlive and count >= 5 then
```

The `count >= 5` gate means the bonus **cannot fire at 3 or 4 players** — it is
not a documentation slip, it is live behaviour.

**Diagnosis.** At the recommended player count (4, per §3), one of the three
bonus victories is mathematically unreachable, and at the minimum count (3) it is
unreachable by two characters. A bonus victory nobody at the recommended count can
earn is dead content ([§16](Archive/PrinciplesOfGoodBoardGames.md) — dead
mechanic).

**Proposal.** Reword §16.2 to *"every character in play is alive at game end, with
no revivals,"* and drop the `count >= 5` gate (keeping a `count > 0` guard so an
empty roster can't trivially satisfy it). Then update the two generated-content
strings that repeat the claim — `lua/whatnow_hints.lua:98` and
`lua/notebook_data.lua:144,333` all say "all 5 alive" — at their **generator
sources**, not the generated files.

**Verification.** A 3-player sim run reaching Day 7 with nobody Down should now
report the bonus. Regenerate with `python scripts/generate_symbol_index.py`, then
`python -m pytest tests`.

---

## 2. 🐛 **P1** — The default victory condition is circularly worded

**Evidence.** §16.1: *"The team **wins** if all surviving characters are alive at
the end of Day 7."* Surviving characters are alive by definition. Meanwhile §16.3
gives the defeat condition as *"All characters are **simultaneously** Down."*

**Diagnosis.** Read together, the actual rule appears to be: *you win if at least
one character is not Down*, i.e. a team can win the campaign with four of five
players face-down in the ghost state. That may well be the intent — it is
consistent with the DST soft-permadeath model of §16.4, and Pristine Run exists
precisely to reward the alternative. But the rule as written doesn't say it, and
this is the single most important sentence in the rulebook.

Per [§25](Archive/PrinciplesOfGoodBoardGames.md), the victory condition is also
the sentence most likely to be misplayed *in the same direction* by every group,
which §17 identifies as a signpost worth reading.

**Proposal.** State it directly and pick a side. Two candidates:

- **Permissive (matches current text):** "The team wins if **at least one**
  character is not Down at the end of Day 7, the Doom marker is below 30, and The
  Source has been destroyed."
- **Strict:** "...if **no** character is Down at the end of Day 7..." — which
  makes Pristine Run redundant and the game considerably harsher.

**The code has already decided, permissively.**
`checkVictory()` in [`lua/tick_victory.lua:366`](lua/tick_victory.lua) tests only
three things — Day 7 reached at the Tick sub-phase, the Source dead, and
`gameState.doom < getDoomLimit()`. It never inspects any character's `down` flag.
A team wins with four of five in the ghost state, exactly as the permissive
reading says.

**Proposal.** Adopt the permissive wording in §16.1, since it is the shipped
behaviour and almost certainly the intent:

> The team **wins** if, at the end of Day 7, at least one character is not Down,
> the Doom marker is below 30, and The Source has been destroyed.

This is [§24](Archive/PrinciplesOfGoodBoardGames.md)'s fidelity drift in its
mildest form — the implementation quietly answered a rules question and became
the de facto rule. Here the answer is a good one; it just needs promoting from
code to document.

**Verification.** None needed for the doc change. Worth noting for the print
edition: this is a rule the TTS build enforces silently and a physical table
would have to adjudicate.

---

## 3. 🐛 **P1** — Night Sounds carries gameable information on audio alone

**Evidence.** §15.8: at Dusk, if the top Threat card is **Hard**, a distant growl
plays. The design explicitly argues it "reveals nothing gameable."

**Diagnosis.** It reveals exactly one gameable bit — *the next threat is Hard* —
and the section itself says veterans "learn to brace." That is information, and
it is delivered on a single channel
([§23](Archive/PrinciplesOfGoodBoardGames.md) — every audio cue needs a visual
twin). It is unavailable to deaf and hard-of-hearing players, and to anyone
playing muted, in voice chat, or with TTS audio misconfigured — a large fraction
of the actual audience for a virtual-tabletop mod.

This is the one place the game's otherwise strong double-coding discipline
(severity dots §15.5, boss standee scale §5, the red-bordered constraint panel
§10.2) lapses.

**Proposal.** Give the growl a visual twin that carries the same single bit and no
more: a brief board-wide dim, a moon icon that appears in the Phase Banner at
Dusk, or a one-frame flicker of the Doom track. It must be equally
non-specific — the design intent (dread without data) is good and should survive
the fix.

**Cost.** Small TTS UI change. No rules change.

---

## 4. 📋 **P1** — Stale §-references to the principles doc throughout `docs/design/`

**Evidence.** The design docs cite `PrinciplesOfGoodBoardGames.md` by section
number, and several have drifted against the current numbering:

| Citation | Cited as | Actually |
|---|---|---|
| Jo-Ha-Kyu / game arc (§14) | §7 | §9 |
| Alpha player problem (§19.5) | §8 | §10, now §20 |
| Runaway leader / dead turns (§14) | §10 | §8, §16 |
| Multiple victory paths (§19) | §11 | §12 |

**Diagnosis.** The references were presumably correct against an earlier draft of
the principles doc. Nothing catches this, because
`tests/test_doc_links.py` guards markdown *links* and
`tests/test_doc_file_refs.py` guards inline *filenames* — neither validates a
`§N` claim against the target document's headings. This is the same class of
drift as `structuralimprovements.md` §1.1/§1.2, one layer up.

Note that the Part IV additions to the principles doc were deliberately
**appended as §20–26 rather than inserted**, precisely so that no existing
citation drifted further.

**Proposal.** Two options, cheapest first:

1. Fix the four citations by hand (ten minutes).
2. Add `tests/test_doc_section_refs.py`: for each `<file>.md §N` reference in the
   docs, assert the target file has a heading numbered `N`. This matches the
   repo's existing enforcement-test convention and prevents recurrence.

Doing (1) without (2) means the same drift in six months.

---

# Part 2 — The economy and the difficulty curve

## 5. 📋 **P1** — The attrition ledger is never written down

**Evidence.** §8.4's mismatched-currency map is the best table in the design doc:
it audits every restorative action against the cross-currency it pays in, and it
is the mechanism that makes the theme into a decision game. But it audits
*direction*, never *magnitude*. Nowhere does the design state the per-day
guaranteed drain against the per-day realistic restoration.

**Diagnosis.** [§21](Archive/PrinciplesOfGoodBoardGames.md) argues this is the
single most important number in an attrition design and the one most often left
implicit. Reconstructing it from the rules:

| Per player, per day | Cost |
|---|---|
| Tick (§11.5) | −1 Hunger, −1 Sanity |
| Each Move (§11.2) | −1 Hunger |
| Dusk scramble if taken (§11.3) | −1 Hunger |
| Court sleep (§7.4/7.5) | −1 Sanity (location modifier) |
| Charlie, first dark night (§15.4) | −2 Sanity, −1 Health, escalating |
| Rayman's Big Appetite (§6.3) | −1 Hunger more |

Against restoration: Rest is 1 action for +2 Sanity **or** +1 Hunger; sleeping in
your own bed is +1/+1/+1.

So the floor is roughly: **Sanity costs ~0.5 actions/day to maintain; Hunger
costs ~1.0.** That is a **~50% maintenance tax** on a 3-action budget for a
player who solves their own upkeep alone — and the tax rises with every Move,
dark night, and court sleep.

**This is very probably the correct design**, and it is elegant: the tax collapses
when players co-locate and cook, because cooking is multiplicative (§13.2 — one
player cooks, many benefit). The Crockpot isn't just a social magnet, it is *the
tax-reduction engine*, and that is why the game's incentive to cooperate is
economic rather than merely thematic. That deserves to be stated rather than
discovered.

**Proposal.** Add a §8.5 "The daily ledger" to
[`docs/design/03-locations-economy.md`](docs/design/03-locations-economy.md):
the drain table above, the realistic restoration table beside it, the resulting
maintenance-tax figure as a **stated target**, and the same figures recomputed
for a co-located cooking team to make the cooperation dividend explicit.

**Why it matters beyond documentation.** Once the number is written down it
becomes a regression check. Every future tuning knob — Charlie escalation, Big
Appetite, the Tick, recipe yields — moves it, and right now nothing would notice.

**Verification.** `scripts/simulate_balance.py` already has the machinery; this is
a report, not new instrumentation.

---

## 6. ➕ **P2** — Anti-alpha defenses are mostly optional or cosmetic

**Evidence.** §19.5 lists five fronts against the alpha-player problem. Graded
against [§20.1](Archive/PrinciplesOfGoodBoardGames.md):

| Front | Assessment |
|---|---|
| Private item hands | ✅ Real, but thin — 5 cards hidden against a fully public board, Doom track, stat set and threat map |
| Asymmetric perks + constraints | ✅ **The strongest one.** Five genuinely different games is the fix that costs nothing at the table |
| Ghost word-limit | ✅ Excellent, and unusually well-targeted — a freely-talking ghost is a *promoted* alpha |
| Soft turn timer | ❌ Optional, and etiquette-shaped. §20.1 is explicit that optional social fixes reliably fail |
| Trade-not-give | ❌ A formality. The alpha announces the trade and it happens |

So two and a half of five hold up. The design's own summary — "what is hidden is
the room to maneuver inside one player's options" — is the right partition, but
the maneuvering room is small.

**The unexploited lever is Dusk.** §11.3 makes the sleep declaration sequential
and public, and explicitly celebrates it: *"the declaration is the table-talk
moment where the group argues geometry."* That argument is the single highest-stakes
decision of the round — and a sequential public argument over a shared optimum is
precisely the stage an alpha player performs on.

**Proposal — simultaneous secret commitment at Dusk.** Keep the argument; change
only the commitment. The table discusses freely, then every player *simultaneously*
commits their sleep tile face-down, and all reveal together.

This is a strong candidate because it is one rule and it pays four ways:

1. **Anti-alpha, structurally.** §20.1 names simultaneous commitment as the most
   under-used lever in the genre. The alpha can still argue; they can no longer
   confirm that everyone complied.
2. **It creates the game's best stories.** "I thought you were coming with me" is
   a better Week in Review headline than any threat draw. §1.4 ranks storied
   collaboration third among the target aesthetics, and this generates it from a
   single rule ([§7](Archive/PrinciplesOfGoodBoardGames.md) — emergence over
   scripting).
3. **It is thematically exact.** People scatter in the dark. They mean to
   regroup. They don't.
4. **It is nearly free in TTS.** Hidden zones already exist; §24 notes that
   simultaneous secret commitment is trivial digitally and awkward physically —
   this is exactly the kind of thing a digital implementation should be spending
   its budget on.

**Risk, stated plainly.** It cuts against §11.3's explicit intent, and it can
produce a genuinely bad outcome — Coco's No Home constraint (§6.2) punishes her
−3 Sanity for ending the night alone, which under secret commitment could happen
through miscoordination rather than choice. That is either the best moment in the
game or an unfair one, and which it is depends on the table.

**Proposal shape.** Ship it as a **setup toggle A/B, exactly like the Rotation
variant (§11.2)** — the design already has this pattern and the telemetry to
evaluate it. Do not make it the default before table data.

**Verification.** Same protocol as the existing turn-structure A/B (§20.2 item 6):
one group, two games. Measure decisions announced by another player before the
owner spoke; ask whether the Dusk argument got better or worse.

---

## 7. 🔧 **P2** — Difficulty and length are the same dial

**Evidence.** §17.2 offers three difficulty variants. "Easy" *is* "Long Weekend":
3 days instead of 7, Doom track halved to 15.

**Diagnosis.** [§20.3](Archive/PrinciplesOfGoodBoardGames.md) identifies this as
a common and costly conflation: **length and difficulty are different dials**, and
collapsing them means a new group can never experience the full arc without also
facing the full challenge.

This bites harder here than in most games, because the arc *is* the design. §14
maps seven days onto Jo-Ha-Kyu with four phases, three bosses and a scripted Last
Dawn; §14.1 tunes boss rewards to "rescue the week"; §6.7 tunes all five
Signatures "for the finale, Days 5–7." A group playing Easy gets Phase 1 and half
of Phase 2 — they never meet the Eye of Terror, never fight the Source, never
reach Doom 25's "Nothing Left to Lose," and never use a Signature at the moment it
was designed for. **The Easy mode omits everything the design is proudest of.**

Meanwhile Standard targets 40–50% for *experienced* groups (§20.2 item 5), which
per §20.3 is roughly where flagship co-ops put their *highest* difficulty setting.
Survey data puts what players generally want nearer 50–75%, and a first group's
win rate at a setting calibrated for experienced play will be well under 40%.

**Proposal.** Add a difficulty axis orthogonal to day count. The cheapest knobs
already exist as named quantities:

| Setting | 7-day arc | Doom limit | Source HP | Phase rate |
|---|---|---|---|---|
| **Story** (new) | ✅ | 35 | 6 | as Standard |
| **Standard** | ✅ | 30 | 8 | §15.6 table |
| **Nightmare** | ✅ | 30 | 8 | +1 all phases |
| **Long Weekend** | 3 days | 15 | — | — |

Reframe Long Weekend as what it actually is — a **short mode**, the teaching
format and the weeknight option — and let Story be the *easy* mode that still
delivers the full week. `DIFFICULTY_PARAMS` in `global.lua` already
parameterises this; the numbers above are placeholders for the simulator to
settle.

**Verification.** `scripts/simulate_balance.py` can bracket the ordering directly.
Per §26, trust the ordering and playtest the magnitude — §15.6 already
acknowledges the probe's combat model is too crude to certify absolute rates.

---

## 8. ➕ **P2** — No individual-level death-spiral valve

**Evidence.** §10.1's threshold effects:

- **Low Health (<3):** Movement costs +1 action → fewer effective actions → harder
  to reach food, allies, or safety → lower Health.
- **Low Sanity (<3):** Haunted — draw a Threat card at every Dawn that only you
  can fight → fight alone → lose Sanity and Health → more Haunted draws.
- **Hunger 0:** lose 1 Health per Tick → Health falls → see above.

**Diagnosis.** All three are positive feedback pointed downward — the death
spiral of [§21](Archive/PrinciplesOfGoodBoardGames.md). The design has exactly one
catch-up mechanism, Doom 25's "Nothing Left to Lose" (§15.2), and it is excellent:
negative feedback arriving as the third act, symmetric, non-snowballing, and it
turns the most dreaded number on the board into one desperate teams play toward.

But it operates at the **team** level and triggers on the **shared** clock. An
individual player can spiral into irrelevance on Day 4 while the team's Doom sits
comfortably at 12 — and receive nothing. §16.4 explicitly removed the one
mechanism that made a Down character's plight the team's problem (the ghost Sanity
drain), for good reasons; nothing replaced it on the way down.

This is the co-op version of player elimination
([§16](Archive/PrinciplesOfGoodBoardGames.md)): someone still at the table, still
nominally playing, with no meaningful decisions left. §20 notes it is *worse* in a
co-op, because that player has no side to root for.

**Fairness note.** The design's response to this would reasonably be that the
spiral is *legible* — §1.4's "clever desperation" wants losses to read as a chain
of visible mistakes, and a spiral is maximally visible. That defence holds for
**fairness** and fails for **agency**. §25's audit asks three questions of every
major negative event: could the player see it coming, could they have done
something about it, could they name the decision afterward. The spiral scores two
out of three, and the one it fails is the one that matters at the table.

**Proposal — "Last Nerve."** One line: *while any of your stats is below 3, your
Flee costs 0 Sanity and your Rest restores 1 extra.*

Why this shape:

- It is the **individual-level mirror of Doom 25**, using the same design logic
  the team-level version already validated: catch-up that arrives as the third
  act, symmetric, self-limiting (it switches off the moment you recover).
- It cannot snowball: it only ever triggers on a player who is nearly dead.
- It is **thematically exact** — adrenaline. Being cornered makes you run better.
- It targets the specific trap: Flee is §12.4's guaranteed-legal escape, but it
  costs 1 Sanity, which means *the escape hatch is priced in the currency most
  likely to be empty*. A Sanity-2 character's only legal move currently costs them
  a third of what they have left.

**Cost.** One sentence; no new components; no new phase. Clears the §3 bar (it
changes the calculus of Flee, Rest, and rescue priority — multiple decisions, no
new exception structure).

**Risk.** It softens the endgame, which §20.1's own note says must stay genuinely
dangerous. Tune the magnitude down before cutting it — free Flee alone may be
enough.

---

## 9. 🔧 **P2** — Haunted deletes the co-op layer exactly when it's needed

**Evidence.** §10.1: *"**Haunted.** At each Dawn, draw 1 Threat card at your
location. It is real to you: only *you* may fight or flee it — allies cannot help
with what they cannot see."*

**Diagnosis.** As horror, this is the best rule in the document. As co-op design,
it is the harshest: it strips the cooperative layer from the one player who most
needs it, at the worst moment, and compounds daily. It converts a struggling
player into a solo player inside a co-op game — and per §20, a player with a
private unwinnable problem in a shared game is worse off than one who is simply
behind.

It also interacts badly with finding 8: Haunted arrives at Sanity <3, and Flee
costs Sanity.

**Proposal — let allies buy in.** *An ally at your location may pay 1 Sanity to
see what you see, and may then fight your Haunted threat alongside you.*

This preserves everything good about the rule and fixes what's wrong with it:

- The isolation horror survives — help is not free and not automatic, and the
  helper *takes on the madness* to reach you.
- It is a textbook mismatched-currency trade (§8.4), on the diagonal-avoiding side:
  you pay Sanity to solve someone else's Sanity problem.
- It restores agency to the **table** rather than to the haunted player, which is
  the right place for it in a co-op — the decision becomes "who goes in after
  them," which is exactly the storied-collaboration beat §1.4 ranks third.
- It gives the Haunted player something to negotiate about instead of a private
  chore.

**Alternative if that's too generous:** cap Haunted threats at 2 HP (already
floated in §20.1's risk list) and leave the isolation absolute. Cheaper, but it
solves lethality rather than agency.

---

## 10. 🔧 **P2** — Truth Run is a lottery, not a strategy

**Evidence.** §16.2: *"**Truth Run** — the team finds and reads all 3 Clue cards
(special items in the Market deck) before Day 7."* The Market deck is 49 cards
(§5) shown through a 5-card display (§13.1).

**Diagnosis.** Drawing three specific cards from a 49-card deck through a
slot-refresh display over seven days is dominated by shuffle luck. A team can play
perfectly and never see a Clue. That makes Truth Run **output randomness applied
to a goal** ([§5](Archive/PrinciplesOfGoodBoardGames.md)) — the player did
everything right and lost the achievement anyway — and per §12 an alternate goal
that is "technically possible but usually unreachable" is not a path.

It also under-uses a good idea: §16.2 says the Truth Run *changes the ending
narrative*, which is the strongest replayability hook in the bonus set (§15 —
players want to play again to see the other ending).

**Proposal.** Make the clues findable by *decision* rather than by draw. Options,
cheapest first:

1. **Seed one clue behind the Sealed Basement** (§13.5). That object is already
   placed at setup, visible from turn one, and explicitly designed as "the map's
   reliable early destination." A guaranteed clue there converts Truth Run from a
   lottery into a plan, using machinery that exists.
2. **Seed the deck**: shuffle one Clue into each third of the Market deck, so
   availability is spread rather than clumped.
3. **Let James find them.** His Pattern Recognition (§6.1) already peeks at deck
   tops; letting it *pull* a Clue seen this way gives one character a genuine
   claim on one of the three bonus victories, which serves the personal-asymmetry
   pillar (§1.4 #4).

(1) and (2) together are probably enough and cost nothing at the table.

---

## 11. ➕ **P2** — No guided opening; the hardest turn is turn one

**Evidence.** §19.6 item 9 is ❌ (no blind playtest yet). §17.1 has a 12-step
setup. A first-time player's turn one requires choosing among 8 action types
across a 5-tile map with a 3-action budget, a private hand of 5 cards, a personal
perk set, a constraint, and a Signature.

**Diagnosis.** [§9](Archive/PrinciplesOfGoodBoardGames.md) notes that first turns
are structurally the hardest in most games — widest options, least context — and
[§22](Archive/PrinciplesOfGoodBoardGames.md) identifies the guided opening as the
highest-value, lowest-cost onboarding intervention available.

The design already has excellent onboarding instincts: the severity dot system
(§15.5) is a genuinely good two-skill-level teaching component, the Phase Banner
(§11) walks the round, the player boards are built to be read without the
rulebook (§10.2), and the "Rules in effect" panel keeps Scenario state visible
(§17.3). What's missing is guidance on the *first decision*, which is the one
that has none of that context yet.

**Proposal.** A **scripted Day 1**, using the precedent the design already
established twice — the Last Dawn (§15.7) and the Treeguard (§14.2) are both
scheduled rather than drawn, on the stated logic that *predictable structure with
unpredictable details* is the DST seasons principle.

Two components:

1. **A fixed Day 1 Dawn card**, tutorial-shaped and low severity (●○○○○): no
   penalty, one sentence of tone, and a printed nudge — *"Gather what you can. The
   dark is eight hours away."* Bypasses the Phase 1 deck exactly as the Last Dawn
   bypasses Phase 4, meaning the Phase 1 deck only ever has to cover Day 2.
2. **A per-character suggested opening** on the player board or in the TTS action
   bar for turn one only: *"Ellie — try: Gather, Gather, Cook."* Demonstrates the
   loop, teaches the cooperation dividend from finding 5, and prevents the classic
   unrecoverable turn-one mistake.

**Cost.** One card's worth of content plus five one-line strings. No rules change.
**Risk.** Nearly none — a suggestion is not a constraint. The main cost is that
Day 1 stops being a surprise, which is precisely the trade §15.7 already made at
the other end of the week.

---

# Part 3 — Process and measurement

## 12. 📋 **P2** — The §19.6 self-audit over-claims on victory paths

**Evidence.** §19.6 item 5 asks "At least 2–3 viable paths to victory?" and
answers ✅ *"Survive (default), Pristine, Truth, Hero — four overlapping goals."*

**Diagnosis.** §16.2 states plainly that these "are not separate goals — they are
achievements layered on top of survival." Both statements can't be right. There is
exactly **one** victory path: survive seven days, keep Doom under 30, kill the
Source.

That is entirely normal for a co-op and not a flaw. But the checklist item it is
answering is about *strategic* diversity, and a co-op satisfies that requirement
with viable **strategies**, not alternate win conditions. The honest question is:
are there 2–3 genuinely different ways to survive the week?

The simulator suggests the answer is **two** — §17.2 and §20.1 name a "turtle"
line and a "spread" line, at 42% and 41% after the Source HP knob. Two is a pass,
narrowly, and it's a real result. It should be the answer given.

**Proposal.** Rewrite item 5 to audit strategies rather than win conditions, cite
the turtle/spread simulation figures as the evidence, and add the follow-up
question the current answer hides: *is there a third?* Candidate third lines the
design gestures at but has never measured — a Cleanse-heavy "hold the world back"
line (§15.3), and a Pry/Basement/craft-rush line (§13.5).

**Why this matters beyond bookkeeping.** §15's replayability argument rests on
decision depth, and "three viable strategies is three games in the box; one is
one" (§12). Knowing the true number is the difference between a replayability
claim and a replayability hypothesis.

---

## 13. 📋 **P2** — Option-utilization is unmeasured; the Visitor question stays open

**Evidence.** §19.6 item 3 flags the Visitor deck as the design's "single most
actionable note — the Visitor deck must justify itself in playtests or be cut."
The game ships 49 Market items, ~20 recipes, 51 threat cards, 8 scenarios, and 4
trophies. Session telemetry currently records `turnStyle`, per-turn durations, and
win/loss.

**Diagnosis.** [§26](Archive/PrinciplesOfGoodBoardGames.md) calls option
utilization "the single most actionable report a simulator or session log
produces" and notes it is the metric most often skipped. This repo is unusually
well-placed to collect it — it has a simulator, a session log, and a one-click
export — and doesn't.

The Visitor question is a perfect example: it has been sitting open as a judgement
call awaiting playtests, when it is substantially a *measurement* question. If
Visitors are drawn in 90% of 3-player games and change the outcome, they stay; if
they're drawn and ignored, they go.

**Proposal.** Add an **unused-content report** to the analysis tooling: across N
simulated or logged sessions, the fraction of games in which each Market item is
crafted, each recipe cooked, each action type taken, each location visited, each
trophy earned, and each Visitor used. Sort ascending. Everything near zero is a
cut candidate under §3's complexity-budget audit.

**Expected findings, as predictions to test** — worth recording now so the report
either confirms or refutes them:

- The Visitor deck is under-used (the design already suspects this).
- Several of the 49 Market items are never crafted at all.
- The Badminton Court is visited less than the Basketball Court (it has the same
  Moonlit Salvage but the highest threat rate §7.5 and no Rayman synergy) — if so,
  one of the five locations is doing less work than the other four.
- Cleanse (§15.3) is rarely used, because a 4-resource bundle plus an action for
  Doom −2 competes badly against boss rebates of −2/−3 that also yield spoils and
  a Trophy.

**Cost.** A report over existing data. Per §26, this is the cheapest high-value
instrumentation available.

---

# Part 4 — Smaller opportunities

## 14. ➕ **P3** — Downtime relief cheaper than the Rotation variant

**Evidence.** §11.2's Rotation variant exists because at 5 players a full-turn
structure can make a player wait through 12 consecutive foreign actions. The
variant fixes it at the acknowledged cost of fragmenting each player's 3-action
plan — and §19 notes the default was kept because coherent turns onboard better.

**Diagnosis.** [§11](Archive/PrinciplesOfGoodBoardGames.md) lists four downtime
cures; the design is A/B-testing the two most disruptive (shorter turns, more of
them) and has not tried the cheapest: **decisions that occur on other players'
turns**. It already has one — free Trade (§8.2) — and it works.

**Proposal.** Two more, both nearly free:

1. **Let Luca's Rally fire on another player's turn.** §6.5 gives Luca "once per
   turn, give an adjacent ally a free non-movement action." Allowing it during the
   ally's *own* turn makes Luca a player who is always partly engaged, and makes
   the Rally a genuine interruption-shaped decision rather than a pre-allocation.
   It also sharpens his identity (§1.4 #4): the orator acts *through* other
   people.
2. **Move the Dusk scramble to simultaneous resolution** — which finding 6 proposes
   anyway for different reasons. It converts a 5-player sequential phase into one
   shared beat.

Neither fragments a turn, and both should be measured before the Rotation A/B is
decided, because they may reduce the problem it exists to solve.

---

## 15. ➕ **P3** — The Week in Review reports but doesn't hook

**Evidence.** §16.5's Week in Review is one of the design's best ideas and is
correctly justified: storied collaboration is a stated aesthetic, and the
retelling is the replayability engine. It reports headlines per day, the darkest
night, the best kill, the Doom high-water mark, the fallen and the saved.

**Diagnosis.** [§25](Archive/PrinciplesOfGoodBoardGames.md): near-misses drive
replay more strongly than comfortable wins, and *"a results ritual that reveals how
near the margin was converts a loss into a rematch."* The current Review narrates
the week beautifully and then stops. The Closing Notes define the design's success
test as a group that "loses on Day 6 to the Eye of Terror, immediately resets, and
starts over with different characters" — the Review is the exact moment that
either happens or doesn't.

**Proposal.** Two lines added to the end of the Review:

1. **The margin.** *"You were 3 Doom from the end"* / *"The Source had 2 HP
   left."* Make the closeness legible — this is the near-miss, and the data is
   already in the event log.
2. **The hook.** One concrete, generated suggestion for the next game, drawn from
   what just went wrong: *"You lost three nights to the dark. Next time: try Coco,
   or take the Total Blackout scenario and plan for it."*

**Cost.** Both are computed from data the TTS build already tracks (§16.5 is
explicit that nothing new is tracked at the table). This is presentation, not
mechanics — and per §24 it is exactly what a digital implementation's budget
should be spent on.

---

## 16. 📋 **P3** — No accessibility standard anywhere in the design

**Evidence.** The design doc has no accessibility section. Searching for
contrast, type size, colour-blindness, or double-coding standards returns nothing
across `docs/design/`.

**Diagnosis.** The design's *instincts* are largely good and it is worth saying so:
resources are double-coded by icon and colour (§8's "brown plank," "grey gear,"
"yellow can"), the severity dots are position-coded (§15.5), boss standees use
scale hierarchy (§5), and player boards are built for at-a-glance reading (§10.2).
That is most of the work done by accident, which is a good sign about the design's
information-design discipline generally.

But per [§23](Archive/PrinciplesOfGoodBoardGames.md), accessibility done by
instinct has no floor, and the two documented lapses are exactly the kind instinct
misses: the audio-only Night Sound (finding 3) and the §10.2 constraint panel
coded by "red border" — a colour-only distinction against the perk panel beside
it.

**Proposal.** A short §18.x "Accessibility standards" in
[`docs/design/09-tts-implementation.md`](docs/design/09-tts-implementation.md),
stating the floor as a checkable list rather than an aspiration:

- Every colour-coded distinction is also coded by shape, icon, position or label.
- Every audio cue that carries information has a visual twin.
- Minimum text size and contrast ratio for XML UI, stated as numbers.
- No information conveyed only by animation or timing.
- Content note for horror themes at setup.

**Why it's P3 and not lower.** It costs an hour now and is expensive after the
art pass — §23's point is that this is a design-time constraint, not a
post-production one. The art for this game is not finished, which makes this
exactly the right moment.

---

## 17. ➕ **P3** — Solo mode is nearly free and shelved as an expansion

**Evidence.** §20.3 lists solo mode as a post-launch expansion hook: "single
player controls 2–3 characters as a personal cast."

**Diagnosis.** Multi-handed solo is the cheapest solo mode that exists, and this
game is unusually close to it already:

- The game state is fully public by design (§19.5) — the usual blocker for
  multi-handed solo is hidden information, and the only hidden state here is item
  hands, which a solo player simply holds.
- There is no opponent to automate. The Dawn deck, threat draws and Doom track
  *are* the opponent, and they already run themselves.
- `scripts/simulate_balance.py` is, functionally, already playing the game solo.
- §20.3 already sets the 3-player minimum on *social* grounds (§3: "at 2 players
  the social/specialization layer collapses") — which is an argument about a
  two-*player* game, not about one player running three characters.

The only real work is that every anti-alpha mechanism (finding 6) is anti-solo by
definition: the ghost word-limit, private hands, and any simultaneous commitment
from finding 6 all become meaningless or annoying with one brain.

**Proposal.** Add a **Solo** setup toggle that runs 3 characters with the
anti-alpha rules suspended: hands open, no ghost word-limit, no Dusk secrecy.
Document it as an official mode rather than an expansion.

**Why bother.** Solo play is a large and growing share of the tabletop audience,
it is the format in which a designer can most cheaply accumulate plays, and per
§18 the designer needs dozens of plays before this design is finished. A solo mode
is a *development tool* before it is a feature.

**Risk.** The win-rate band (finding 7) will differ for solo and needs its own
calibration; don't ship it claiming Standard means the same thing.

---

# What this review deliberately does *not* propose

Per [§17](Archive/PrinciplesOfGoodBoardGames.md) — "prefer the minimal
intervention; new rules are the most expensive fix and usually the wrong one" —
several tempting changes were considered and rejected:

- **Re-capping boss festering.** §15.1 records that uncapped boss festering is the
  only thing preventing boss-avoidance from dominating, verified by simulation.
  Leave it alone; §20.1's own risk list says the same.
- **Restricting 3-player rosters.** §6.6's composition inequality is real
  (simulation found trios from 86% to 0.5%), but the design's stated fix — tune
  character numbers, not legal rosters — is correct. Roster restrictions solve a
  balance problem by deleting content.
- **A traitor variant.** §20.3 lists it as an expansion hook. Per §20.4 it would
  solve quarterbacking almost completely and turn the game into a social-deduction
  game, which is a different aesthetic than §1.4's cozy dread. Correctly shelved.
- **A second Source phase.** §12.6 considered and deferred a second beat at HP ≤ 2
  on the grounds that one clean phase change reads as a climax and two read as
  fiddly. That reasoning is right.
- **More content of any kind.** The design's problem is not a shortage of cards;
  finding 13 suspects it already has cards nobody uses. Measure before adding.

---

# Suggested order of work

1. **Findings 1–4** — defects and doc hygiene. Hours, not days, and no design
   decisions required.
2. **Finding 5** (the ledger) and **13** (utilization report) — both are
   measurement, both make everything after them better-informed, and both use
   machinery that already exists.
3. **Finding 7** (difficulty axis) — the change most likely to affect whether a
   first group ever plays a second game.
4. **Findings 6, 8, 9** — the three rules changes worth arguing about. Each needs
   a table, not a simulator. One change per test cycle (§17).
5. **Findings 11, 15** — onboarding and the ending hook. Cheap, and they bracket
   the session at both ends.
6. **Findings 10, 14, 16, 17** — opportunistic.

Findings 6, 7, 8 and 9 all move the difficulty in the same direction (gentler), and
per §17's regression list they must not be evaluated together — the combined effect
would be much larger than any of them individually, and attributable to none.

---

*Written against `Archive/PrinciplesOfGoodBoardGames.md` §1–26 and
`docs/design/` §1–20. Findings cite the design doc's own section numbers; where
this document cites the principles doc, it links explicitly.*
