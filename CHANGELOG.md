# Changelog — rule and tooling changes

*The diff of the **game**, not the code. One entry per batch; newest first. Sim win rates are the 3000-game 4-player baseline (see agents.md for the full tables).*

## Two Scenarios did nothing at all, and four more were half-inert (2026-07)

`gameState.scenarioFlags` is the twin of `ongoingDawnEffects`.
`tests/test_lua_effect_flags.py` has guarded the Dawn table since the
eleven-orphan audit — *"every ongoing rule the game announces must be a rule
something enforces"* — and the Scenario table sat outside it the whole time.
The identical rot ran unchecked for longer and got further: **twelve of the
seventeen flags the eight Scenario cards set were read by nothing.**

- **The Rotting Autumn** — `foodSpoilsAtDawn`, `recipeBonus`, `clothBonus`.
  All three dead. The scenario did **literally nothing**.
- **Strict Rationing** — `slowMarket`, `cheapRecipes`. Both dead. Likewise.
- **The Long Winter** — the food never froze (`foodGatherPenalty`).
- **The Scorching Summer** — Energy Drinks and courts were ordinary. Only the
  −2 max Hunger, applied inline at setup, ever happened: the scenario was
  its own downside with neither of its compensations.
- **Total Blackout** — Batteries were still on the shelves and in the ground.
- **The Full Moon** — Soft threats stayed soft.

A Scenario rots worse than a Dawn card. It is chosen once at setup and
announced once, so nobody re-reads it to check; and it lasts the whole game,
so its absence is seven days of a rule that never arrives, not one.

All twelve are wired now, each at the verb its clause names — the frozen
ground, the extra court resource, the +1 Sanity on a cold drink, the ration
that spoils overnight at each occupied tile, Cloth added to the draw table,
Batteries removed from it, anything needing a Battery refused at the Market
(derived from the cost table, not a hardcoded card id — that *is* the rule the
scenario states), the market's every-second-day restock, the one-ingredient
recipe discount that never takes the last ingredient, and the Full Moon's
Soft-to-Hard promotion.

**And two of the five that "worked" were on borrowed time.** Total Blackout
and The Full Moon put their rule in `ongoingDawnEffects` (`onlyFireLight`,
`charliePaused`) — a *per-Dawn scratchpad* that unrelated Dawn cards clear in
their `onCleanup`. `dawn_effects_phase4` nils `onlyFireLight`; `phase3` nils
`charliePaused`. Drawing either card would have handed flashlights back, or
brought Charlie back, for the rest of a week-long scenario, silently and with
no message. Both rules are read from `scenarioFlags` now, which nothing else
can touch.

The Full Moon's promotion is worth a note: it is applied in
`threatStatsForCard`, not at the draw, because `fightTargetsAt` filters out
`hp = 0`. Promoting only the *type* would have turned every atmospheric card
into an unfightable, undiscardable permanent Doom tax — the exact bug the last
three entries have been clearing out. It returns a copy, so the generated
`THREAT_STATS` rows are never mutated.

Guarded by `tests/test_scenarios.py`, and by a new half of
`test_lua_effect_flags.py` that applies the Dawn-flag check to `scenarioFlags`
— allowlist-staleness and promotion checks included, so the gap that let this
run for so long cannot reopen.

## Five rules the interface stated as fact (2026-07)

Not cards this time — the places you stand and the bosses you kill. Every one
of these was asserted to the player somewhere in the UI, and none of them
existed.

**"Its power is live."** The boss-kill broadcast says exactly that, twice,
about the Trophy it has just flipped face-up. `revealTrophy` turned a card over
and highlighted it in yellow; that was the entire implementation. The Trophy is
the whole reward for the hardest content in the game — §14.1's "a boss kill
should visibly rescue the week, not just remove a penalty" — and it was a
picture of a reward.

- **The Antler Sled** (Deerclops) now tows: once per turn, a character who
  Moves may bring one ally who was standing where they left. The offer comes
  up *after* the move lands, so the table has one decision (who comes) instead
  of two, and it reuses the Revive/Stabilize picker rather than adding a third
  five-button panel. The ally pays 1 Hunger and no action. Declining does not
  spend the once-per-turn window.
- **The Watching Jar** (Eye of Terror) now opens at Dusk — deliberately then,
  because the scramble window is open and knowing what tonight holds is only
  worth something while you can still move. The top 2 Threat cards are read out
  to everyone; the swap is announced as a one-drag table step rather than
  scripted, because reordering a live TTS deck through the API is the
  take-then-put dance `docs/tts-interface.md` exists to warn about.

**"Echoes: d6 on gather (6 = bonus, 1-2 = Sanity loss)"** — the Basketball
Court's board tooltip, and its What-now hint says it too, and Design §7.4
specifies it. No d6 was ever rolled. The court was a plain Gather wearing a
gamble's description, which is precisely what its −1 Sanity at sleep and its
threat draw rate are supposed to be the price of. It rolls now, after the haul
lands, so a bad roll that puts you Down still leaves you holding what you found.

**"The Net gives +1 defense die in combat"** — the Badminton Court's What-now
hint and its tooltip. There was no defence roll anywhere in the mod, and
`content/locations.csv` carried a `defense` column that nothing read. Location
defence is live: a positive value is dice the team rolls against an incoming
counter-attack (each 5-6 turns one hit aside), a negative one is extra swings
for the threat, because being caught on an open court is the same rule pointed
the other way. So the Net and Rayman's Garage shelter you, and the Basketball
Court costs you. `LOCATION_DEFENSE` mirrors the CSV under a cross-ref test —
drifted combat maths is invisible, since a lost block just looks like bad luck.

**"The Garage: Rest +1 Health"** — Rayman's House's tooltip, with no owner
qualifier, because §7.2 puts the bonus on the *place*. The code gave +1 Health
only at your own home, so the Garage did nothing for anybody except Rayman, for
whom it was already true. The one line that made it worth walking to was inert.
Non-stacking with the home bonus, exactly like Doom 25's.

Guarded by `tests/test_places_and_trophies.py`. One of these also flushed out a
flaky test: the rain-Gather test asserted an exact Sanity value after a
Basketball Court gather and had been relying on real randomness, which the
Echoes d6 turned into a one-in-three failure. Its dice are scripted now, as
this suite's own conventions require.

## Hard threats: seventeen printed specials that no code had ever read (2026-07)

The third and last threat kind to have its card text wired to anything.
Eighteen Hard cards carry a `special` line. `COMBAT_SPECIALS` held **one**
row — Your Roommate's Sanity cost — and that was the whole of it.

Two of the seventeen were worse than inert.

**The Grue has hp 0.** Its card reads "Cannot be fought. Resolves Charlie
attack at this tile (1d8 Sanity 1d6 Health). Discard after." `fightTargetsAt`
filters out hp 0, nothing else removed it, and `countFesteringThreats` counts
every Threat card near a tile — so it charged +1 Doom at every Dawn for the
rest of the week while the attack it prints never landed once. That is the
third distinct card family to fall into the same hole (Soft threats, the
hp-less Persistents, and now this), and the last one left. It bites and
discards itself now, Coco's Night Vision spares her from it, and it never
festers because it is never left standing.

**Fight Together turned the Roommate off.** "1 Sanity per attack die rolled"
was charged only when `#participants == 1`, so the group-fight button — right
next to the solo one — bought off the entire printed cost of the one card in
the deck whose point is that hitting it hurts. Every participant is billed
now, each on their own dice, so Rayman's two base dice cost him two.

The rest are wired through a new `lua/threat_hard.lua`, one declarative row per
card. **Inside a fight:** A Child's Shadow charges a flat 1 Sanity per attacker
(a different, cheaper shape than the Roommate's per-die bill, so it is a
separate key); the Spider Thing's multi-attack counters with 2 dice instead of
its printed 1; the Doppelganger makes you roll Sanity d8 before you can swing,
and a hesitation costs the action and 1 Sanity; the Thing in the Attic refuses
to be fought anywhere but a house tile, refused *before* the action is spent.
**On the draw:** the Hollow Spectator's entry cost and the Wall Crawler's free
first hit. **While it stands:** the Shadow Stalker's extra Sanity at Tick, the
Scarecrow's toll on every Gather, the Glass Child's 2 Sanity a Night — all
three now listed in the Rules panel with the tile they are on. **On its
death:** the Black Dog hunts in pairs, so killing it draws another Threat.

Four are declared **inert with the reason** rather than left blank, which is
what made seventeen of these invisible in the first place: "cannot be attacked
at range" has nothing to act on (ranged combat is not a mechanic here — the
Slingshot is declared unwired for the same reason), the Terror Beak's
"removed if the Eye is restored" has no state that can fire it, The Door is
already wired through `SEALED_REWARDS`, and the Crawling Hand's "attacks the
Down player first" would make it *weaker*, since damage to a Down character
does nothing in this engine. Two more (the Mimic's disguise, the Swarm's
split) are announced as table steps.

Guarded by `tests/test_hard_threats.py`, which fails on a printed special with
no row, a row naming a non-Hard card, a row that says nothing at all, and a
scripted key the test module has never heard of.

## Persistent threats did nothing, and six of them could never be removed (2026-07)

Two bugs, and the first is why the second went unnoticed for so long.

**Nothing was ever classified.** `identifyThreatType` decided Soft/Hard/
Persistent by reading `ThreatType:<type>` tags and GMNotes. The built save has
neither — a threat card carries `["ThreatCard", "<CSV id>"]`, and *every*
object's GMNotes is the empty string. So every card ever drawn fell through to
the `return "Hard"` default. That means the Soft-threat fix in the entry below
was **dead code in the shipped mod**: the branch that resolves and discards a
Soft card could not be reached, so the twenty printed effects still never
happened and the cards still festered +1 Doom a Dawn. It also announced *"must
be fought or fled"* over all thirteen Persistent cards, eleven of which have
0 HP and cannot be fought at any price.

The card's own id is now the lookup, against a generated `THREAT_TYPE_BY_ID`
straight from `cards_threats.csv`, so the card face and its classification
cannot drift; the build also stamps a real `ThreatType:` tag on every card so
the save is readable on its own.

**Then the Persistents themselves.** Thirteen cards whose printed rule — "Move
actions out of this tile cost 1 extra Hunger", "No Food can be gathered at this
tile", "each Tick eats 1 Food at this tile", "At each Night spawns 1 additional
Hard threat" — had no code anywhere. And of the seven with 0 HP, only four are
Sealed (openable with Pry). The other **six had no removal path at any price**
while `countFesteringThreats` charged +1 Doom for each of them at every Dawn:
the same permanent, un-payable Doom tax as the Soft cards, except a Persistent
card is *meant* to stay on the tile, so nothing was ever going to take it off.

New `lua/threat_persistent.lua` gives each card one declarative row and hooks
those rows into the verbs that own them: Cracked Floor charges Hunger to leave,
Fog Bank charges an action, Contaminated Water strips Food from the tile's
yields and doubles the Sanity cost of eating raw there, Roots blocks Barricade
and makes Rest restore nothing, The Watcher stops trades, The Nest adds a
Threat to its tile's Night draw, the Hungry Dog eats at Tick, and the Stairway
announces its Risk step. Every one of them is now on the Rules panel while it
stands, naming the tile and the way out.

The way out is the second half: **Fight it** if it has HP, **Pry it** if it is
sealed, and otherwise **Clear it** — a new action, 2 actions + 1 Wood at that
tile. That price is not invented: it is what The Nest's own card prints
("Destroy with 2 actions + 1 Wood"), generalised to the cards that print
nothing rather than picking a second number. Two actions is most of a turn, so
clearing stays a real decision against the Doom the card would otherwise charge
every Dawn — but it is a decision the table can now actually make.

Guarded by `tests/test_persistent_threats.py`, which fails on a Persistent card
with no rule row, on a row naming a non-Persistent card, on a `fought`/`sealed`
flag that disagrees with the card's HP or pry reward (that would advertise a
verb that refuses), and on a built save missing a type tag. As with the Soft
module, one test asserts an *uncleared* card still festers, so the rest keeps
meaning something.

Also fixed here: the Wrongness (the face-down Dawn-card threat) printed
"resolve it and discard" and did neither. It now runs the revealed card through
the same resolvers as one drawn at Night.

## Soft threats never resolved, and never left (2026-07)

`drawThreatsAt` announced it on every draw: *"X is a soft threat — resolves
and discards."* It did neither. The first half is twenty printed effects that
never happened. The second half is worse, and compounds:

* a Soft card has `hp = 0`, and `fightTargetsAt` filters those out — so it
  could never be fought;
* nothing else removed it, so it stayed on its tile for the rest of the week;
* and `countFesteringThreats` counts every Threat card near a tile — so each
  one charged **+1 Doom at every Dawn, for ever**, with no counterplay
  available at any price.

Soft threats were the cheapest cards in the deck and they were quietly the
most expensive: a permanent Doom tax, pinned at the +3 fester cap within a
couple of nights, that no action in the game could clear.

New `lua/threat_effects.lua` resolves them and takes the card off the map.
Sixteen of the twenty are scripted — the Sanity and Health hits, Voices
(1 per ally standing somewhere else), Buzzing's d8, the Roaches and Food Gone
Wrong taking Food, Lights Out / Power Flicker / Fire Out / Moth Cloud riding
the light flags the night check already reads, and The Clock Stops borrowing
P3_LONG_NIGHT's shortened day. The four that ask the table for a judgement the
script has no basis to make (which house is "front-most", which Item to
discard, Friend's Blood's choice, the Echo's memory) announce that step
instead. **Every Soft card is discarded either way** — that is the half that
was doing the damage, so no card can leak back into the fester count by being
forgotten in a table.

Guarded by `tests/test_soft_threats.py`, which fails on a Soft card in neither
table, on either table naming a Hard or Persistent card (those are fought, or
stay on the tile by design), and on a card in both. It also pins the mechanism
itself: one test asserts an *unresolved* card still festers, so if that ever
stops being true the rest of the module stops meaning anything.

Also fixed here: **the Fire Starter Kit was free.** Its card says "Reusable.
Needs 1 Wood per use" and nothing charged the Wood, so a 1 Wood + 1 Cloth +
1 Metal craft bought permanent immunity to Charlie — strictly better than the
Lantern it is meant to trade against (pricier to craft, genuinely free to
run). It burns its Wood now, and with none left it simply doesn't light.

## The Deerclops finally costs something (2026-07)

"While Deerclops is on the map, all Sanity costs are doubled" — announced on
arrival, repeated in the Active Rules panel, and promised back on its death
("Sanity costs return to normal"). The Lua did nothing with the flag.

The interesting part: **`simulate_balance.py` has been modelling this rule
since the baseline was measured.** It doubles the Tick Sanity loss while the
boss stands. So the win rates every band in `test_sim.py` is checked against
already assume a Deerclops that hurts, and the game has been quietly easier
than its own balance model for as long as both have existed. Wiring it up
moves the game *toward* the sim, which is why the bands did not budge.

Doubled at Tick, after the Doom-20 surcharge and before Coco's Calming
Presence — the sim's order, so the two agree digit for digit. The card and
panel text now say "double Sanity at Tick" instead of the broader "all Sanity
costs", because that is the reading the balance model validates. Killing it
clears the flag immediately rather than at the next Dawn, so the death
broadcast's promise is true the same night.

Also settled, with the same "does anything actually run this?" test:

- **Doom 25's "boss-level threats can appear in any phase" is gone from the
  player-facing text.** It described a mechanic the mod does not have — one
  un-phased Threat deck, bosses placed by scripted Dawn cards that Doom never
  touches. Nothing read it and nothing could. Nothing Left to Lose (+1 attack
  die, Rest heals anywhere) is real and stays. The `anyPhaseBosses` constant
  keeps its name with a note, since the sim mirrors it.
- **P3_ALLY_MISSING's +1 action is scripted.** It was left to the table as
  "the player with the fewest items", which sounded unknowable — except
  `getPlayerCarriedObjects` has always answered exactly that for weapons,
  lights, pry tools and the Bandage. The vanished ally is picked at reveal and
  banked on `gameState.missingAlly`, because `beginDayPhase` resets the action
  budget *after* Dawn resolves; a flag read later would hand the adrenaline to
  whoever happened to ask.

Two guards grew a check they were missing. `test_lua_effect_flags.py` now
ejects a flag from `DISPLAY_ONLY` the moment a rule reads it — and caught that
`eyeActive` had been misfiled there all along, since the Eye's each-Dawn extra
threat has always read it. `docs/agents/combat-and-actions.md`, which had
reached its 2500-token budget *exactly*, is split into it and
`economy-and-session.md`; both now have over a thousand tokens of headroom.

## Items you could craft and could not use (2026-07)

There was no Use Item verb. None. Not a hidden one, not a manual one — the
action bar's twenty-one buttons are all specific verbs, there is no stat
editor anywhere, and stats live in `gameState` where a player cannot reach
them. So a crafted **First Aid Kit** ("Single-use. Restore 4 Health to any
player at your location") was a card in your hand that could not do the thing
printed on its face, by any means the mod provided. Same for the Protein Bar,
Energy Bar, Hot Cocoa, Sports Drink, Friendship Bracelet and School Bell.

Eight consumables now work, through one **Use Item** button (free — the action
economy already charged you for the Craft that made them). Healing auto-targets
whoever at your tile needs it most and says so, the way the Scarcity surcharge
picks a resource and James's reroll picks a die; a prompt would have been a
third target dialog for a decision that is nearly always forced. The card is
spent.

**The other 24 are now a written-down list, not a silence.**
`tests/test_market_wiring.py` fails on any Market card that nothing reads and
nothing explains. Each unwired card carries its reason — Circle of Salt needs
boss-movement bans, the Toolbox needs a discount seam in `doCraft`, Reinforced
Door wants a "defense" stat the game doesn't have, the Notebook is a prop. The
failure this prevents is the one that happened: 33 cards quietly doing nothing,
indistinguishable from 33 cards deliberately left to the table. A companion
check ejects a card from the list the moment the Lua starts reading it, and a
third asserts `USE_ITEMS` still matches the numbers printed on the cards.

`M_BANDAGE` is the worked example of why the split needed writing down: its
effect line went unimplemented for the whole project, and separately
`doStabilize` charged a Bandage it never checked for. Two halves of one card,
both missing, neither visible.

## Stabilize was free (2026-07)

§12.3 Stabilize costs a Bandage. Four UI strings said so — the button tooltip,
the target dialog's note, the module header, the design reference. The code
said `-- Requires Bandage item (manual check)` and checked nothing.

So Stabilize was a free, unlimited, one-action un-Down, standing next to
Revive — which costs a *cooked* Telltale Heart (1 Cloth + 1 Battery + 1 Food +
2 Health to make) plus 2 more Health to use. Nobody would ever pay for Revive.
`reviveCharacter` guards its own cost for exactly this reason, with a comment
saying so: "without this, a caller with an empty supply revives for free".
Its neighbour didn't.

It now requires a carried Bandage and consumes it, which also makes `M_BANDAGE`
the first of the inert Market cards to do something. Both halves are checked —
the precondition, so the button hides, and `doStabilize` itself, so a direct
call can't skip it.

Also routed through the shared `adjacentLocations()`: **Luca's Rally** (which
couldn't reach an ally across the Shortcut road), the **Source's split** and
the **Eye's Terror Beaks** (which couldn't place them down it), and Iced Tea's
new adjacent-allies reach. That is every "one tile away" question in the game
answered in one place.

## Flee had no button (2026-07)

The escape valve. §12.4, the rule Last Nerve exists to protect — "the escape
hatch is priced in the currency most likely to be empty", as `helpers.lua` puts
it — and there was no way to use it. `doFlee` was implemented, correct, and
called by nothing outside the test suite: no button, no handler, no XML.

Six places told players to use it anyway: `canFight`'s refusal ("Too hungry to
fight (Hunger < 3). Flee is always legal: 1 tile, 1 Sanity"), the same line from
`doFightTarget`, the threat-draw warning every Night, the Hunger tooltip on the
HUD, the notebook, and the Active Rules panel. A starving player was told four
ways to run and given no way to do it — the exact failure the eight-rules audit
was about, hiding behind the one loophole in its guard: `tests/` counts as a
reference, so two test calls made it look reachable.

Flee is now a situational verb beside Barricade and Appease, appearing whenever
something fightable shares your tile. It costs 1 Sanity and *no action* (0 on
Last Nerve), because "always legal, even starving" is the point of the rule. It
picks its destination with the same tile buttons Move uses.

Two things fell out of wiring it:

- **Flee was the one movement verb that didn't know about the Shortcut.** Move
  and the Dusk scramble each open-coded LOCATION_ADJACENCY *plus* SC_SHORTCUT's
  extra road; Flee open-coded only the first half, so on a variant that doesn't
  print that road you could walk it and scramble down it but not run down it.
  All four now go through one `adjacentLocations()`.
- **`clearActionTargets` had a hand-maintained list of pending-action types**
  and neither `flee` nor `drift` was in it, so Flee's click-again-to-cancel
  could not cancel and a ghost's pending drift outlived the turn that armed it.

Also removed: **`onSetupClick`**, dead since the 3D setup button was deleted.
Its own comment claimed it "remains as the handler for that panel button" —
never true; the panel has always called `onHostSetupGuided`. What was left was a
strict duplicate plus a `clearButtons()` on an object that no longer exists.
**`applyScenario`** is declared a console tool, which is what it is: the only
way to play a chosen scenario twice on purpose.

**The guard:** `test_lua_reachability.py` now also fails on any function only
the *suite* calls, with a short reviewed `TEST_SEAMS` list (and a check that an
entry leaves it the moment the game gains a real caller). A test calling a rule
is not the game running it.

Fixed in passing: Coco's **Wanderer's Gift** is "+1 Sanity every time she
Moves"; the briefing, notebook and PlayerRules all said "to a *new* location",
a restriction the code has never had and which would have had players
under-using the perk.

## Eleven ongoing effects that were never wired up (2026-07)

The reachability audit below caught rules that were *functions* nothing called.
This one caught the same bug one level down: rules that were *flags* nothing
read. Eleven Dawn cards set an `ongoingDawnEffects` flag, announced the rule in
chat, listed it in the Active Rules panel — and no action, phase step or
resolver had ever heard of it. The card said it, the panel said it, the table
played around it, and the day played out exactly like any other.

Now enforced: **P3_LONG_NIGHT** (`reducedActions`) really does cut the day to 2
actions each; **P3_GRAVITY_WRONG** (`moveCostPlus1`, `restNoHealth`) charges the
extra action to move and suspends Rest's Health; **P2_STRANGER_WAVES**
(`sportCourtHungerCost`) bills +1 Hunger on every step to or from a court —
including Rayman's free second step and the Dusk scramble, so it can't be walked
around by picking a different verb; **P2_RAIN_STARTS** (`rainSanityCost`,
`rainFireDisabled`) costs 1 Sanity to Gather at a court and drowns fire there,
flames only, batteries fine; **P3_WALLS_CLOSE** (`reducedCapacity`) really does
take a bed out of every house; **P4_LAST_MEAL** (`recipeBonusHunger`) adds its
+2 to the Hunger a recipe restores; **P4_MEMORY_FLOOD** (`homeSanityBonus`)
doubles the sanity of your own bed.

**P4_HOPE_REMAINS and P4_DAWN_BREAKS could not have worked as written.** Both
name *this* Dawn's Doom advance, and `BeginDay` advances Doom before it reveals
the card — so a flag set at reveal always missed the read it was for, and would
have applied to tomorrow's advance instead, the one Dawn neither card is about.
They now hand the points back on reveal: -1 for Hope Remains, the whole phase
rate for Dawn Breaks (festering is not refunded — that is the map's bill, not
the calendar's).

Also fixed, same audit:

- **Iced Tea's second line** ("Adjacent allies +1 Sanity"): `adjacentAllies` was
  generated into `RECIPE_DATA` from the CSV and read by nothing.
- **Gumbo's Crockpot requirement** (`requiresCrockpot`) was never checked, and
  the **Portable Crockpot** — craftable, "allows cooking at any tile" — did
  nothing. Both go through one new `crockpotAt()`, which the Cook button, the
  Cook handler and the recipe flag now all read, so they can't disagree about
  where the pot is.
- **A full Telltale Heart supply used to charge you anyway.** The max-5 check
  ran *after* the recipe's 2 Health cook penalty, so cooking against a full
  supply cost 2 Health, three resources and an action for nothing.
- **Birthday Cake (2 actions) with 1 action left** spent that action inside the
  loop and then bailed. Multi-action recipes are all-or-nothing now.
- **Luca alone under P2_HUNGRY rested for the Hunger the card had banned:**
  Needs an Audience redirected him sanity → hunger *past* the `restNoHunger`
  check that had already run. Both bans are re-checked after any redirect; if
  both halves are shut, the Rest is refused rather than silently granted.
- **Undo left Rayman's tile count ticking.** `snapshotForUndo` captured
  `raymanMovedToday` but not `raymanTilesMovedToday`, which carries two
  thresholds of its own — the 3-player Loud relief (< 3 tiles) and the 3-player
  Big Appetite relief (< 2). An undone move counted against both.
- **The Shortcut scenario duplicated a road it shared with the map.** Ring (the
  default variant) and Sprawl already print JamesHouse↔BadmintonCourt, so
  `_adjacentLocations` returned that neighbour twice: two overlapping MOVE HERE
  buttons on one tile.

**The guard:** `tests/test_lua_effect_flags.py` fails on any flag `EFFECT_RULES`
promises that no non-`ui_` file reads — and in the other direction, on any flag
a Dawn card sets that the Active Rules panel never shows. `ui_` files are
excluded on purpose: printing a rule is what the panel is for, and printing it
is exactly what all eleven were doing instead of happening.

## Eight rules that were never wired up (2026-07)

A reachability audit of the Lua bundle found nine global functions that nothing
called. Eight of them were *rules*, fully implemented, with their state
consumers already in place — and no button, dialog or phase step anywhere that
would run them. Nothing errored; the rules were simply absent while the UI went
on describing them.

**Revive was the worst.** `cookTelltaleHeart` worked, so `gameState.heartCount`
went up and never down: Hearts could be cooked and never spent, while four
places in the UI told players to "use a Telltale Heart at this tile to revive".
The only revive path in the game had no caller.

Also restored: **Stabilize** (§12.3, the Bandage revive), **Defend** (Rayman's
Backboard Block — `combat_resolve` had always redirected counters on
`raymanDefending`; nothing set it), **Energy Drink** (James's Wired constraint
was a pure penalty: four files read `jamesEnergyDrinkUsed`, one reset it
nightly, nothing ever made it true, so the -2 Sanity was unavoidable for the
whole week), **Eat Raw** (§8.4, and with it Ellie's Particular Eater, which
could never be bumped into), **Barricade** (day_loop already subtracted it from
the night threat rate), **Appease Treeguard**, and **Ghost Drift** — §16.4's
one-tile-per-round move, which is the only decision a Down player has, and
whose absence is the co-op player-elimination failure §05 spends a page on.

The seven Day-phase verbs are situational, so they follow the Peek/Rally
pattern rather than taking permanent bar space: hidden until their `canX`
precondition holds. Ghost Drift rides the Reactions panel, since a ghost is
never the active player.

**The guard:** `tests/test_lua_reachability.py` now fails on any global
function nothing calls, allowlisting only TTS engine callbacks and console
tools, plus a companion check that bans `_G[name]` — dynamic dispatch would
make an orphan indistinguishable from a live handler.

## Nightmare is winnable now (2026-07)

Follow-up to the design pass, which had made Nightmare's problem visible for the
first time: a flat Doom +1 in every phase measured at **0-6%** for the best lines
at 4 players. That is a broken mode, not a hard one.

The cause is compounding. Most Doom pressure is already *responsive* (§15.1 -
festering threats, festering bosses, fallen friends), so a flat surcharge from
Day 1 taxes the exploratory half of the week §14 deliberately wants calm, and
runs the clock out before the arc reaches its climax. The losses were mid-week
strangulation, which is exactly what §20.1's calibration gate exists to catch.

**Retuned:** the surcharge moved to **Phases 3-4 only**, and the Source went to
**9 HP** (one above Standard's calibrated 8), so Nightmare's finale is a harder
*fight* rather than the same fight on a shorter fuse. Best line **20.3%** over
3000 games with **100% of losses on Days 6-7** - a near-miss finish. Roughly one
win in five, and the real table number is lower: the probe cannot model
`minPhase` (phases 1 and 2 share a Doom rate), so it never sees that Nightmare
opens on the Strange Days deck instead of the gentle Phase 1 one.

`doomDelta` therefore accepts a per-phase table as well as a flat number, read
through the new `getDoomDelta(phase)` / `describeDoomDelta(diff)`. The setup
announcement used to do `(diff.doomDelta or 0) > 0`, which throws "attempt to
compare table with number" the moment the surcharge went per-phase - fixed, and
a test now describes every mode's delta to keep that from coming back.

Also recorded honestly in §17.2: **the probe is only trustworthy at 4 players.**
At 3 players every mode reads >=98% including Standard, because `ROSTERS[3]` is
the strongest trio by construction; at 5 players every mode reads high because
five bodies clear festering faster than the extra phase rate charges for it.
Neither spread is caused by the difficulty settings and neither is fixed by
tuning them - establishing real 3p/5p bands is §20.1's open composition work.
*(This also makes the achievements batch's **Nightmare win** unlock earnable —
it shipped against a mode measuring 0-6%.)*

## Achievements (2026-07)

24 achievements, a Steam-style panel in the mod, and a Steamworks manifest for
a future standalone app. Full detail: [`docs/achievements.md`](docs/achievements.md).

**What players see:** a *Trophies* button beside Hide UI opens a paged panel —
icon, name, description, and when it was earned. Unlocks raise a toast bottom
right and a chat line. Three of the 24 are hidden and show as `???` until they
happen. The roster spans the week's shape: living through Day 1, winning at
all, winning on Nightmare / Long Weekend / solo, each boss, the ten-meal cook,
the fifteen-kill week, the three-press finisher, everyone spending their
Signature, and the two endings that are worth the retelling (winning with two
Doom left, winning with one character standing).

**What it does not do, and why:** a Tabletop Simulator Workshop mod runs inside
someone else's Steam app. It has no appid and no Steamworks surface, so it
cannot set a real Steam achievement — nothing can, from inside TTS. The panel
is the working half; `steam/achievements.json` is generated from the same CSV
so that a future port is a copy-paste, not a redesign.

**Where unlocks live:** `gameState.achievements`, which rides the mod's saved
script state — the only store TTS gives a mod. It is deliberately *not* cleared
by Restart: it records what the table has done, not what this week did. A fresh
load from the Workshop starts empty (a TTS limit), so the panel's *Copy my
code* button writes a `SNM-ACH-1:` string to the Notes panel that restores
every unlock at another table.

**Nothing new is recorded at the table.** Every number the unlock rules read
was already tracked for the Week in Review (§16.5) or the session telemetry
(§20.2). The rules are pure reads of `gameState`, re-tested at four checkpoints
(a kill, end of turn, end of day, game over), each `pcall`-ed so a broken rule
costs its own achievement and nothing else.

**Adding one is a CSV row plus a predicate.** `content/achievements.csv` feeds
the in-game roster, the Steam manifest and the ComfyUI art prompt;
`lua/achievement_rules.lua` holds the condition. A row without a rule, or a
rule without a row, fails the test suite. Art comes from the same ComfyUI
pipeline as the cards ([`docs/comfyui-achievement-icons.md`](docs/comfyui-achievement-icons.md)
is the run book) and falls back to a procedural placeholder so the build is
never blocked waiting on a render.

## Design review pass — all 17 findings (2026-07)

The batch that shipped `possible-design-improvements-to-snm.md` (retired to git
history once all 17 landed), a review against
`Archive/PrinciplesOfGoodBoardGames.md` §1–26 (especially its
Part IV co-op / attrition / onboarding / accessibility / measurement chapters).
That document is now the *rationale record*, not a proposal list.

**Defects — three rules didn't do what they said, and one couldn't run at all:**

- **Pristine Run was unreachable at 3–4 players.** `checkBonusVictories` gated
  on `count >= 5`, but §6.6 turns spare characters into Visitor NPCs, so the
  *recommended* player count could never earn it. Now "every character in play,
  nobody revived".
- **The Truth Run could not fire under any draw.** Nothing in the mod ever
  incremented `gameState.clueCount` — three Clue cards, a Trophy and a Dawn card
  all pointed at a counter stuck on zero.
- **The default victory condition was circular** ("all *surviving* characters
  are alive"). §16.1 now states the permissive rule `checkVictory()` always
  enforced: one survivor, Doom under the limit, Source dead.
- **Night Sounds was audio-only** while carrying a gameable bit. The Dusk growl
  now ships with a moon glyph in the Phase Banner.

**Rules changes:**

- **Last Nerve** (§10.1.1) — while any stat is below 3, Flee costs 0 Sanity and
  Rest restores 1 extra. The individual mirror of Doom 25, closing the gap where
  a player could spiral into irrelevance on a healthy team clock. *Measured:
  best line 42% → 51%, collapse-losses 27.3% → 11.8%.*
- **Witness** (§10.1) — an ally at a Haunted character's tile may pay 1 Sanity
  to see their threat and fight it with them. Haunted stops deleting the co-op
  layer for the player who most needs it.
- **Rally is once per round and fires off-turn** (§6.5) — the cheapest downtime
  cure (§11) and the one that makes Luca's identity land. Retuned from per-turn,
  which off-turn would have made +4 actions a day at five players.
- **Truth Run is findable by decision** (§16.2) — a guaranteed Clue behind the
  Sealed Basement, Market checkpoints on Days 3 and 5, and James can *take* a
  Clue he peeks.
- **Difficulty and length are separate dials** (§17.2) — new **Story** mode
  (full 7-day arc, Doom 35, a 6 HP Source that splits at 4) is the new default;
  **Long Weekend** is reframed as a *short* mode and listed last. The old "Easy"
  was Long Weekend, so easy mode omitted the Eye, the Source, Doom 25 and every
  Signature's intended moment. *Measured ordering: Story 67/80%, Standard
  51/50%, Nightmare 0/2%.*
- **A guided opening** (§15.9) — Day 1's Dawn is fixed like Day 7's, and each
  player gets one concrete three-action plan on their first turn.
- **Two new off-by-default toggles:** **Secret Dusk** (§11.3 — argue freely,
  commit privately, all revealed at once) and **Solo** (§20.3, promoted from an
  expansion hook to an official mode: 3 characters, anti-alpha rules suspended).

**Measurement and documentation:**

- **§8.5 states the daily attrition ledger** — the per-day drain, the realistic
  restoration, a ~50% maintenance-tax target, and the cooperation dividend that
  makes the Crockpot the tax-reduction engine. It is a regression check.
- **Option utilization** (§20.2 item 8) — session logs (schema 2) now record
  every craft, cook, action, location, Visitor and Trophy, and
  `analyze_sessions.py` scores them against the authored catalog so unused
  content shows as explicit zeros. `simulate_balance.py --utilization` covers
  the action mix. *Confirmed: Cleanse is ≤1.5% of actions and 0.00/game for two
  of four policies. Not confirmed: the Badminton-Court prediction is untestable
  in the sim, because every policy hardcodes the Basketball Court.*
- **§18.19 states the accessibility floor** as six checkable rules, and
  **§19.6 item 5** now audits strategies (two measured lines) rather than
  claiming four victory paths.
- **The Week in Review ends on a margin and a hook**, not on statistics.
- **The whole rulebook is readable in-game** — a paged Rulebook tab in the Help
  panel, carrying the same four sections as `PlayerRules.md`. Paging also fixed
  a silent clip: the Glossary was ~7,000 characters in a body that holds ~2,000.

**Not done, deliberately:** Standard is *not* retuned to absorb the gentler
rules. Last Nerve, the Haunted buy-in, Secret Dusk and the difficulty axis all
push the same way, and §17's regression list forbids evaluating them together.
The knobs are named in §20.1 in the order to spend them.

## Cheaper, safer AI workflow (2026-07)

Tooling/tests only — no rule changes, with one exception noted below. The third
and last pass at making this repo cheap to work in (after the compartmentalise
and structural programs, both already retired here). Those two built the
*navigation* layer; this one attacked the three costs navigation could not
touch: session bootstrap, the untested interactive surface, and the size of the
two files an agent is told to consult. `GoodForAiPlan.md` is retired with it.

**Bootstrap — paid once per session, before any useful work.**
- `.claude/` is committed now (only `settings.local.json` is ignored), so what
  an agent learns about *how to work here* survives the container. A
  `SessionStart` hook installs `pytest lupa Pillow ruff` + `luacheck`; a
  `PostToolUse` hook reruns `generate_symbol_index.py` after any `lua/` edit; a
  permission allowlist covers the routine loop. `/verify` and `/newtask` are
  committed slash commands.
- **`python scripts/check.py` is the one command to finish a task** —
  regenerate → build → test → lint, one verdict line, ~22 s. The three-step
  ritual is demoted to a "debugging that stage" note in all six `CLAUDE.md`
  files, and the pipeline is written out in exactly one place
  (`scripts/CLAUDE.md`) instead of five.
- `./iwanttoplay` works on Linux (it used to die at step 4 after a good
  regenerate/build/test, because `os.startfile` is Windows-only).

**The interactive surface, which nothing tested.** 58 of 73 XML click handlers
were never named in a test — every action button in the game. That is where the
playtest bug reports came from, because nothing else could find them.
- `tests/test_ui_handlers_smoke.py` clicks **every** handler across six game
  states (PreGame, Day as the active seat, Day as a *wrong* seat, Dusk, Night,
  GameOver), asserting no Lua error escapes — *including one swallowed by
  `safecall`*, which is the "button silently does nothing" failure TTS is worst
  at — that invariants hold, and that out-of-turn clicks are refused rather
  than merely survived. Handlers, element ids and arguments are all parsed from
  `xml/`, so a new button is covered the moment it is added and nothing can be
  skipped. **0/73 uncovered**, in ~1 s.
- It immediately found a real one: the ghost-panel guard added to `onPickChar`
  after a human hit it in a playtest was never applied to the other setup
  steps, so clicking Continue on a leftover variants panel re-applied a
  difficulty — and a different Doom limit — after the game had ended. Now a
  shared `isGhostSetupClick()` on all nine step handlers. *(The one rule-facing
  change in this batch.)*
- `tests/test_lua_setup_walkthrough.py` walks guided setup for 1–5 players plus
  the paths real tables take: duplicate picks, a player leaving mid-pick, a
  seat change between steps, the hotseat path, and every stale click a
  disconnected client could still send.

**`gameState` had no schema.** 71 fields across 41 of 46 Lua files, and a
misspelling read as `nil`, silently, at runtime, in TTS.
- One initialiser instead of two: the Restart path was a hand-copied literal
  that had **already drifted** — a Restart produced a `gameState` missing
  `resources`, `dailyAlerts`, `lastInteractionAt`, `idleNudgedThisTurn` and
  `schemaVersion`. Both paths go through `migrateGameState()` now, which also
  hardens old-save migration.
- `docs/gamestate.md` (generated) maps every field to its default, its writers
  and its readers; `tests/test_gamestate_schema.py` fails if any
  `gameState.<name>` is neither declared nor on the reviewed transient list.
  36 declared, 36 transient, **0 unaccounted**.

**Drift pairs closed.** `CHAR_BRIEFINGS` is generated from
`content/help/character_briefings.md` (they had diverged — the markdown told
James about his house, the game never did). An unlisted `lua/`/`xml/` file now
**fails the build** instead of printing a note nothing checked; `assets.lua`
joined the manifest. `content/CLAUDE.md` carries a per-CSV column dictionary
bound to the schema test.

**Context bill.** `agents.md` 18.6k → **3.0k tokens**, split into ten topic
files under `docs/agents/`, each under a 2.5k budget a test enforces.
`symbols.json` + `python scripts/sym.py NAME` answers "where is X?" with
location, signature and call sites in one call, instead of grepping a 17k-token
index and opening the file anyway.

**Two real bugs found while building the above**, neither of them the thing
being worked on:
- A stale `saves/StarveNoMore.json` made the suite *hang for over four minutes*
  — `test_committed_save_is_fresh` asserted equality of two 1.2 MB strings, so
  pytest tried to build a character-level diff. It reports in 0.47 s now,
  naming the byte offset.
- Ambient track durations in the audio manifest were estimated from file size
  and wrong by up to **65%** (25.2 s recorded for a 72.0 s track). Those
  durations schedule the next track, so every one was a clip cut short.
  `generate_audio_manifest.py` now reads the exact duration out of the Ogg
  stream itself.

**Also:** the 17 MB WAV that escaped the earlier audio compression pass is OGG
q4 (1.0 MB); tracked media 286.7 → 270.2 MB, with a test capping any new
binary at 4 MB. `luacheck` **hard-fails in CI** now — the soft-fail was there
"until the first run has been reviewed", the review happened, and all five
warnings are fixed rather than whitelisted (one was a genuine fragility: a
file-local helper called from another file, working only because the bundle is
one concatenated chunk).

**And the CI job nobody could see was broken.** `ruff` had been failing on
every run for weeks — not from anything in this repo, but because the job
installed ruff unpinned and inherited each release's widening defaults, until
166 findings accumulated and a permanently-red job stopped meaning anything.
The rule set is now pinned in `ruff.toml` (ruff's own documented default plus
import sorting — real defects only; the 88 refactor-opinion findings are listed
there as deliberately unselected, with counts) and the version is pinned in the
workflow. All four CI jobs are green.

The root cause was closer to home: **`scripts/check.py` ran pytest and luacheck
but not ruff**, so the one command that says "everything green" could not see
it. Its stages now mirror the CI jobs one-for-one, and both files say so.
Fixing it turned up two genuinely dead imports in `build_save.py` — one of
which, `md_to_text`, README and `architecture.md` still described as the shared
source for the physical Quick Start notecard. It has not been for some time;
that notecard is hand-written text, and both docs now say so.

Suite: 683 → **812 tests**, still ~20 s (~26 s including both linters).

## Repo structure follow-ups (2026-07)

Tooling/docs only — no rule changes. The next layer after the completed
compartmentalise program (now retired to `Archive/compartmentaliseplan.md`):

- **One-command rebuild.** `scripts/regenerate_all.py` runs every generator (in
  `generators.json` order) then `build_save.py`, so you no longer have to
  remember which generator matches your edit. Generators whose sources are
  absent (e.g. `sounds/` on a clean clone) are skipped instead of erroring.
- **Doc-map self-healing.** `tests/test_doc_file_refs.py` fails if a
  navigation-layer doc (agents.md / README / TASKMAP / CLAUDE stubs) names a
  `lua/*.lua` file that doesn't exist — the gap that had left four stale
  `ui_actionbar.lua` references in agents.md after that file was split. Those
  references are now fixed.
- **Retired the finished plan.** `compartmentaliseplan.md` (all phases shipped)
  moved to `Archive/`; the standing improvement punch-list is
  `structuralimprovements.md`.

## The briefing promises, delivered (2026-07)

Every perk and constraint the character briefings advertise is now actually scripted — plus the Fight action itself, which had been a broadcast-only stub:

- **Fight is click-to-complete** like Move/Craft/Cook: the Fight button spawns a FIGHT button on every fightable thing at your tile (threat cards with real statlines from `cards_threats.csv` via the new generated `THREAT_STATS`, boss standees via their baked statlines), plus a TOGETHER button that pulls in every standing ally with Hunger 3+ (summed dice, shared counters — §12.2). Chip damage on threat cards persists between fights and across saves (`gameState.threatDamage`); a defeated card discards itself beside the Threat deck.
- **Bosses really arrive.** The arrival Dawn cards now pull the standee out of the Boss Pool onto the map (Deerclops → Basketball Court, Eye → a random house, Source → the center), seed script-tracked HP for every boss (not just the Source), and a defeated boss's standee returns to the pool — so festering, the Source's victory gate, and the Eye's each-Dawn extra-Threat stare (now scripted) all key off reality.
- **Character perks, implemented as briefed:** James's Gaming Reflexes (auto-reroll of his lowest failed die, once per turn on his turn) and Pattern Recognition (Peek button: top card of any deck, privately, once per day); Coco's Calming Presence (allies at her tile lose 1 less Sanity at Tick); Rayman's Court Master (+1 die at the Basketball Court, matching the sim) and Backboard Block (Defend now actually redirects counter-attack damage to him until his next turn); Ellie's Particular Eater (raw food refused); Luca's Rally (Rally button: a nearby ally gains a free non-movement action, once per turn), Calm Words (auto d6 on scripted group Sanity-loss events — 4+ spares his tile), and Needs an Audience (no solo Sanity regen from Rest, sleep, or storytelling).
- **Host Controls are contextual**: only the buttons valid in the current sub-phase show (Setup pre-game; Begin Day between days; Resolve Night at Dusk/Night; End Turn during the Day; Restart once started), and Begin Day refuses to re-run mid-day. Setup now parks the game in `PreDawn`, so the banner and CTA point at Begin Day instead of implying a Dawn is resolving.
- **Cover art**: `scripts/generate_cover.py` renders `saves/StarveNoMore.png` (Coco's hand-drawn standee on a night-suburb backdrop); `iwanttoplay` installs it beside the save so the TTS Save & Load browser shows real cover art.
- Fixed in passing: the Speed second-step message no longer mislabels itself "Court Master"; Wanderer's Gift (Coco, +1 Sanity on Move — implemented and briefed in-game all along) is now also in the briefing/notebook markdown; the supply-bag tooltip no longer claims Gather is fully automated.

## Player rulebook, publishable saves, structure pass (2026-07)

- **Player Rules on the table.** `scripts/generate_player_rules.py` assembles `PlayerRules.md` + `PlayerRules.html` from the same `content/` markdown as the in-game Notebook (Quick Start → Full Rules → Characters → Glossary — can't drift). A **Player Rules tablet** object on the table shows the HTML in-game via the local asset server; the same file opens in any desktop browser. Freshness-tested like every other generated artifact.
- **`--publish` builds.** `build_save.py --publish BASE_URL` writes a separate shareable save with every `file:///` and `localhost` URL rewritten to the hosted base — and refuses to write one that still contains a local URL. `test_publish_build.py` proves it end-to-end.
- **UI XML split** into `xml/hud.xml` / `xml/setup.xml` / `xml/dialogs.xml` (was one ~1,300-line `global_ui.xml`); the build and the whole test suite read the files in `XML_LOAD_ORDER`.
- **Adversarial tests**: undo spam refunds exactly once; all three setup entry points refuse re-entry on a running game; restart-through-the-confirm then re-setup yields a clean Day 1.
- Housekeeping: the robustness tracking file was implemented out and removed (its live pieces now live in the test suite + agents.md); the retired `Archive/Checklist_For_TTS_Implementation.md` and `Archive/InterestingGames.md` were deleted (git history keeps them; the design doc's citations became plain-text provenance notes, and code comments' phase codes are explained in agents.md).

## Starting hands + robustness program (2026-07)

- **Starting hands are real now.** Each character's personal items (design §6: Pocketknife/Flashlight/Headphones, First Aid Kit/Comfort Blanket/…, Basketball/Sports Drinks/…, Crockpot/Cooking Knife/…, Notebook/Pep Talk/…) exist as cards — authored in `content/cards_starting.csv`, rendered into a 10th deck atlas, built into per-character decks in the save, and dealt into each player's hand at setup (`dealStartingHands`). James's Energy Drink ×2 arrive as resource **tokens** by his board (Wired runs on tokens). His starting Flashlight counts for the night light check (nickname match).
- **Printed weapon dice are script-rolled.** `getAttackDice` had a TODO where equipment should have counted; `WEAPON_DICE` is now generated from "+N Attack die" card text (market + starting CSVs) and combat adds the best single carried weapon automatically.
- **Robustness program** (tracked in `robustnessimprovements.md` at the time; since implemented and removed — the enforced-mirrors list lives in agents.md): new test gates for XML well-formedness, literal `\n`, TTS-parseable colors (the white-panel bug class, checked in XML *and* Lua), image↔CustomUIAssets↔disk, dynamic per-character UI ids, luacheck (skips if not installed; CI runs it), TOOLTIP_DATA↔save tags, standee-slot constant mirror, starting-decks↔CSV; `onLoad` survives a corrupt saved state (pcall + fresh start); the dead bare-setup handler is gone; the hand+board "carried objects" scan is one shared helper for lights and weapons.

## Playtest UX fixes — first live-table feedback (2026-07)

No rule changes. Everything below came out of the first real sit-down:

- **Every UI color fixed at the root**: the XML/Lua wrote colors as `rgba(30,40,30,0.9)`-style 0–255 values, but TTS parses rgba() components as 0–1 floats — so every "dark" panel and button clamped to white and its pale text was unreadable ("What now?", "End Turn / Pass", the entire setup walkthrough). All 123 occurrences converted to `#RRGGBBAA` hex; the HUD is now actually dark.
- **Setup walkthrough restyled** as light "rulebook pages" with dark text. Step 2 became portrait cards (standee art, big bold name, role/stats/abilities/constraint); hovering a card shows that character's full briefing; literal `\n`s in labels render as real line breaks. The briefing page gained **Go Back — change character**.
- **The board's 3D Setup button now runs the guided walkthrough.** It used to fire the bare seat-order `Setup()`, which re-dealt the Market and silently replaced the picked party with the default seat assignment (the "picked Rayman/Coco/James, roster says James/Ellie/Luca" bug). Both setup paths now refuse to run on a started game and wipe the previous party before assigning.
- **Physical setup untangled**: every character owns a fixed standee slot on each tile (no more stacked standees at Ellie & Luca's); the market display is a spaced, locked column on the board's left flank (dealt cards no longer shove each other around, bury the Day Counter, or clip the board edge); the market deal skips occupied slots; unpicked characters move to an off-board bench.
- **Smaller reads**: the Party roster sizes itself to the actual party; the phase banner sits below the TTS menu bar; HP/HU/SA labels explain the stats on hover; supply bags say that Gather draws from them automatically.

## Framework improvements (2026-07)

No rule changes. Workshop hardening (the framework-improvements pass; planning doc since retired — this entry is its record): constant-mirror tests (bosses, thresholds, Cleanse, difficulty), `RECIPE_DATA`/`SEALED_REWARDS` now generated from CSV columns, atlas grids derived from card counts via `art/decks/atlas_manifest.json`, the `gameRoll` RNG seam, a TTS-stub divergence ledger, `SYMBOLS.md` + luacheck config, full-campaign bot/fuzz tests, save `SCHEMA_VERSION` + migration + frozen fixture, session-log analyzer, CI lint/artifact jobs. Fixed in passing: a malformed `T_CLOCK_STOPS` CSV row that had shifted its art note out of column. Follow-up: the in-game Notebook/Help text is now generated from `content/` markdown (`generate_notebook.py`) — previously three hand-copied versions, two of them stale.

## Batch 4 — validation & hardening (2026-07)

- **The Source: HP 10 → 8** (calibration knob, §20.1's first choice). Sim best line moved into the 40–50% target band (turtle 42%, spread 42%) with ~100% of losses on Days 6–7.
- **3-player reliefs** (both behind `playerCount == 3`; table A/B pending): Big Appetite costs 2 Hunger only on days Rayman fought or moved 2+ tiles; Loud requires 3+ tiles moved.
- **Difficulty modes** (§17.2, now real): Long Weekend (3 days, phases 1/1/2, Doom track to 15), Standard, Nightmare (Doom +1/phase, starts on Strange Days). Selectable at setup.
- **Session telemetry**: the chronicle records setup facts, per-turn seconds, and batch beats; **Copy Session Log** on the Week in Review panel exports JSON to the Notes panel.
- **Playtest protocol**: `playtest/facilitator_script.md` + `feedback_form.md`.

## Batch 3 — mid-week texture & dread (2026-07)

- **Night Sounds**: a low growl at Dusk when the top Threat card is Hard (generated `THREAT_TYPE_BY_NAME`). Deliberately unexplained.
- **Dawn Dares**: 5 Phase 1–2 cards gained optional hooks — scripted: court floodlights (`P1_LIGHTS_FLICKER`: courts +2 threats, survivors claim 2 Market cards) and porch light (`P2_PORCH_LIGHT`: first house Gather may take 3 resources for 2 Sanity); checklist offers on `P1_STRANGE_RADIO`, `P1_SOMETHING_WATCHED`, `P2_FOOD_SPOILS`.
- **Sealed Rooms**: the **Pry** verb coded (free action + Crowbar/Lockpick/Pry Bar); 3 new sealed threats (Shed, Locker, Car); the **Sealed Basement** placed at Ellie & Luca's House every game (free Market Item + 2 Food/1 Wood/1 Battery). Threat atlas grew 6×8 → 7×8 (now manifest-derived).
- **The Wrongness**: `P2_BASKETBALL_BOUNCE` converted to a deferred face-down threat at the court — resolves on tile entry or at the next Dawn; doesn't fester while face-down.
- Balance-neutral by design (turtle 34%, spread 27%, balanced 11%).

## Batch 2 — the climax & identity (2026-07)

- **Nothing Left to Lose** (Doom 25): +1 attack die for everyone; Rest heals +1 Health anywhere (non-stacking with home).
- **Signature Moves** (once per game, per character): James **All-Nighter** (+3 actions, −3 Sanity at next Tick), Coco **Touch of Hope** (+4 Health, any tile), Rayman **Posterize** (delete a non-boss threat at his tile; +1 draw there tonight), Ellie **The Feast** (1 action, cook freely, all held Food consumed), Luca **The Speech** (+2 Sanity to all; only while an ally is Down or below 3 Sanity).
- **Source phases**: boss HP script-tracked (`gameState.bossHP`); at ≤5 HP the Source splits into two Terror Beaks at adjacent tiles (once).
- **The Last Dawn**: Day 7's Dawn is fixed and toneless — no Phase-4 draw.
- Baseline: turtle 35%, spread 27% — win-rate-neutral, loss profile shifted late (as intended).

## Batch 1 — combat is the center (2026-07)

- **Press the Attack** (§12.5): after a hit, pay 1 Sanity per bonus die until you miss; the enemy waits. Press dice never fumble.
- **Boss-kill rewards**: Deerclops Doom −2, Eye −3, 3-resource spill, Trophy; kill narrations + lighting flash.
- **Week in Review**: the persistent chronicle, narrated at game end.
- Baseline: turtle 32%, spread 27% — unfought-Source losses collapsed 33%→8%.

## Pre-batch retune (2026-07)

Source-mandatory victory; uncapped boss festering (+2/dawn, Treeguard +1); no boss-arrival Doom; per-count Doom rates 3p [1,1,1,1] / 4p [1,1,1,2] / 5p [1,1,2,2]; whiff-only fumbles; escalating deterministic Charlie; crowded floor; Moonlit Salvage; the Treeguard; Scarcity at Doom 15.
