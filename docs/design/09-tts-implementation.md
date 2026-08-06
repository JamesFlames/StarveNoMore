# Starve No More — Tabletop Simulator Implementation

> Part of the **Starve No More** design doc — [back to the index](../../StarveNoMoreDesignConcept.md).

## 18. Tabletop Simulator Implementation

Sanity-checked against [HowToCreateGamesInTabletopSimulator.md](../../Archive/HowToCreateGamesInTabletopSimulator.md). Every component below maps to a documented TTS object type.

### 18.1 Component-to-TTS mapping

| Component | TTS object type | Reference §  |
|---|---|---|
| Main Board | `Custom_Board`, locked | TTS §5.3 |
| Location Tiles | `Custom_Tile` (rounded square) | TTS §5.3 |
| Path-edges between locations | Decorative `Custom_Tile` (small) — purely visual | TTS §5.3 |
| Character Player Boards | `Custom_Tile` (rectangle) | TTS §5.3 |
| Character Standees | `Figurine_Custom` | TTS §5.3 |
| Stat markers (H/H/S) | `Custom_Token` (small) | TTS §5.3 |
| Day Counter | `Counter` widget | TTS §4.2 |
| Doom Marker | `Custom_Token` along a snap-point track on the Main Board | TTS §5.6 |
| Phase Decks (4) | `DeckCustom`, one per phase | TTS §5.1 |
| Market Deck | `DeckCustom` | TTS §5.1 |
| Threat Deck | `DeckCustom` | TTS §5.1 |
| Visitor Deck | `DeckCustom` | TTS §5.1 |
| Recipe Cards | Loose `Card`s (face-up reference) | TTS §5.1 |
| Resource Tokens | `Infinite_Bag` per resource, plus `Custom_Token` instances | TTS §5.5 |
| Combat Dice (d6) | `Die_6` (built-in) | TTS §5.4 |
| Sanity d8 | `Custom_Dice` (8 faces) | TTS §5.4 |
| Boss Standees | `Figurine_Custom`, larger scale than character standees | TTS §5.3 |
| Trophy Cards | Loose `Card`s | TTS §5.1 |
| Telltale Heart Tokens | `Custom_Token` | TTS §5.3 |
| Hand Zones (1 per player) | `HandTrigger`, one per `Player.Color` | TTS §5.6 |
| Crockpot at Ellie & Luca's | `Custom_Model`, locked, decorative | TTS §5.2 |

### 18.2 Snap point structure

- Main Board has snap points for: 5 Location Tiles, the Day Counter, the Doom Marker (along a 31-step linear track), Market display (5 card slots), Threat-deck slot, Phase-deck slot, Visitor-deck slot, Trophy display (4 slots).
- Each Location Tile has snap points for: 4 character standees stacked vertically (so multiple characters in the same location remain visible), 1 boss standee slot, a "threat in play" slot.
- Each Player Board has snap points for the 3 stat markers along their tracks, plus 3 action cubes.

### 18.3 Lua scripting plan

The game does **not** require Lua to be playable — players can run rules manually. However, scripting reduces friction. Recommended scripted features:

| Feature | Implementation | TTS reference |
|---|---|---|
| **Setup button** | Global `Setup()` function: shuffles decks, deals starting hands, places standees on home locations, sets stat markers. | TTS §8.1 |
| **Day-advance button** | Global `AdvanceDay()` function: increments Day Counter, advances Doom by phase rate, draws and announces a Dawn card, applies Tick. | TTS §6.2, §8.3 |
| **Stat sliders** | Player-board buttons (`createButton`) with +/− for each stat, with a custom-XML mirrored display. | TTS §7.4 |
| **Doom marker auto-advance** | `setPositionSmooth` along snap-point track; trigger threshold scripts at 10/15/20/25/30. | TTS §6.3 |
| **Combat helper** | A "Roll Combat" XML button per player rolls their attack dice and reports hits in chat. | TTS §8.6 |
| **Save/Load state** | `onSave`/`onLoad` JSON-encoding of: day, doom, character stats, hands, decks-in-play, ongoing Dawn-card effects. | TTS §8.4 |
| **Hidden info** | Each player's hand zone is `HandTrigger` for their seat color. Cards in market and threat areas are face-up; cards in players' hands are private. | TTS §10 |

### 18.4 Performance considerations

Per [HowToCreateGamesInTabletopSimulator.md §11](../../Archive/HowToCreateGamesInTabletopSimulator.md):

- Total active object count target: <500 (well under the 1500 ceiling). Resource tokens are the biggest concern; using `Infinite_Bag` per resource keeps the active token count low.
- Card atlases: Each deck (~50 cards max) fits one 10×7 atlas at 408×585 per cell.
- Standees: 5 character + 4 boss + 5 visitor = 14 figurines, well within budget.
- Custom dice: 1 (the Sanity d8).

### 18.5 Asset hosting

All custom assets (card faces, board image, location tiles, standee art) must be hosted on a stable HTTPS source. Recommended: Steam Workshop upload (cached automatically) or a dedicated CDN. Local file URLs (`file:///`) are acceptable during prototyping but must be replaced before publication. ([HowToCreateGamesInTabletopSimulator.md §3](../../Archive/HowToCreateGamesInTabletopSimulator.md).)

### 18.6 Tagging convention

Per [HowToCreateGamesInTabletopSimulator.md §16.4](../../Archive/HowToCreateGamesInTabletopSimulator.md), prefer tags over GUIDs:

- Tag every card with its deck (`PhaseCard`, `MarketCard`, `ThreatCard`, `RecipeCard`, `VisitorCard`, `TrophyCard`).
- Tag every standee with `Character` or `Boss`.
- Tag every resource token with `Resource:<Type>`.
- Tag location tiles `Location:<Name>`.

Lua scripts query by tag, not GUID, so duplication and re-spawning don't break them.

### 18.7 Notebook tabs

The TTS Notebook is a fallback reference for players who prefer text. Day-to-day play is driven by the in-game **Help menu** (§18.17), which is more discoverable. Provide three Notebook tabs as a backup:

1. **Quick Start** — 1-page summary of the game loop and victory conditions.
2. **Full Rules** — abridged from this document.
3. **Character Reference** — perks/constraints for all five characters.

These tabs are populated from the `content/notebook/*.md` files at load time so they stay in sync with this design doc.

### 18.8 First-time-load checklist

When a player first loads the mod, the host should see:

- All custom assets cached (no broken images).
- A "Setup Game" button on the table.
- A welcome message in chat: "Welcome to Starve No More. Choose your survivor and click Setup."

### 18.9 Information hierarchy (what's hidden, what's public)

Per [HowToCreateGamesInTabletopSimulator.md §2](../../Archive/HowToCreateGamesInTabletopSimulator.md), step 3, the **information model** is the design decision most expensive to fix late. For Starve No More:

| Element | Visibility | TTS realization |
|---|---|---|
| Player Item cards (in hand) | Private to the holder | Hand zone, per-color `HandTrigger` |
| Player resource counts | **Public** | Resource tokens placed openly on the player board (not hidden) |
| Player stat values (H/H/S) | Public | Sliders/markers on the open player board |
| Phase deck top card | Hidden until revealed | Face-down `DeckCustom` |
| Phase deck contents | Hidden | Inside the deck, not searchable |
| Threat deck top card | Hidden until drawn | Face-down |
| Discard piles (any deck) | Public, browseable | Face-up adjacent to the deck |
| Market display | **Public** | Face-up, 5 slots |
| Recipe cards | Public reference | Loose face-up cards on the table |
| Doom marker | Public | On the visible track |
| Day Counter | Public | Counter widget |
| Boss standees | Public | On the map when active |
| GM-only setup notes | Hidden | `GMNotes` field on relevant objects |

**Why resources are public.** This is a deliberate co-op design choice. Public resources prevent hoarding-as-secret and force the social trade layer to operate on shared information — the Catan-style negotiation pattern. It also reduces the alpha-player advantage by making the team's combined inventory visible to everyone, so juniors can argue from the same data the experienced player sees.

**Why hands are private.** Item card combos can be a private creative engine. Keeping cards hidden lets each player retain a strategic pocket, and prevents the alpha player from optimizing every player's hand for them — see §19.5.

### 18.10 UX design: playable on first sit-down

The game's stated goal in §1.4 is "cozy dread" — but the implementation also has a stated *operational* goal: **a new player should be able to sit down, click around, and play meaningfully without reading the rulebook first**. A player learns the game by playing it, not by studying it.

This subsection codifies the UX choices that make that possible. They are not nice-to-haves; they are the design.

#### 18.10.1 The seven UX principles

1. **The component teaches.** Every card, tile, button, and token has its rule printed on it in plain language. A player should never have to consult an external doc to understand what an object does — the object says.
2. **The phase prompts.** The screen always tells the active player what to do next. There is never a moment of "what now?"
3. **Costs are visible before commitment.** No button consumes resources without first showing what it will cost and asking for confirmation.
4. **Errors explain themselves.** A failed action says *why* it failed and what to fix.
5. **State is broadcast.** Whenever a rule fires (Doom threshold crossed, ongoing Dawn effect active, character goes Down), it announces itself in chat *and* in a visible banner.
6. **Symbols repeat.** The same icon for "Hunger" is used everywhere — on cards, sliders, action buttons, recipes, threats. Once a player learns one icon, they have it everywhere.
7. **The first decision is small.** Setup walks each player through one choice at a time. They are never confronted with the whole rulebook at once.

A rule of thumb when reviewing any new component: **show it to a player who has never read the rules. If they cannot make a sensible first decision with it, the component is wrong.**

### 18.11 The Phase Banner (the persistent on-screen guide)

A panel anchored to the top of the screen, visible to all seated players at all times. It always shows five fields:

| Field | Example | Source |
|---|---|---|
| Day | "Day 3 of 7" | `gameState.day` / Day Counter |
| Phase | "Phase 2: Strange Days" with a 4-segment progress bar | `gameState.phase` |
| Doom | "Doom 9 / 30 — next threshold at 10: night threats +1" | `gameState.doom` + lookup |
| Active player | "Ellie is acting" with her color border | `Turns.turn_color` |
| Next action | "Take an action" / "Resolve threats at Badminton Court" / "Click Begin Day" | Phase + sub-phase state |

This panel is the single most important UI element for new players. It tells them what is happening and what is about to happen, at all times. A player who reads only this panel and clicks where it suggests can play the entire game.

The banner has one button: **? (Help)**. See §18.16.

### 18.12 The Active-Player Indicator (multi-channel)

Whose turn it is is signaled in four redundant channels — overkill is the point, because new players in TTS often miss subtle cues:

1. **Phase banner** field updates with the active player's name and color.
2. **Hand zone glow.** The active player's `HandTrigger` zone gets a colored border (Lua-driven `setColorTint` on the zone).
3. **Standee bounce.** The active character's standee gently bobs every 4 seconds via `setRotationSmooth`.
4. **Other boards dim.** Inactive players' boards get `ColorDiffuse` set to ~0.7 brightness; the active board is full brightness.

When all four channels point at the same player, no one needs to ask whose turn it is.

### 18.13 The per-player Action Bar

Each player board has a horizontal bar of seven labeled icon buttons. Each button shows its **action cost** in brackets and its **icon**:

| Button | Label | Visible state when unusable |
|---|---|---|
| 🚶 | **Move (1)** | Dim if no adjacent location is reachable. |
| 🤲 | **Gather (1)** | Dim if location's resource bag is empty. |
| 🛠 | **Craft (1)** | Dim if no Market card is affordable; tooltip lists the cheapest. |
| 🍲 | **Cook (1)** | Dim if no Crockpot here. Tooltip: "Move to a Crockpot location first." |
| ⚔ | **Fight (1)** | Dim if no enemy at this location. |
| 💤 | **Rest (1)** | Always available. |
| 🛐 | **Cleanse (1)** | Dim if missing the Cleansing bundle. Tooltip lists what's missing. |

Three **Action Cubes** sit next to the bar. Each click of an action button consumes one cube, animating it from "available" to "spent". When all 3 are spent, the bar greys out and the banner shows "End of Day actions — click Pass to finish your turn."

The bar gives the new player two things at once: a **menu** of legal moves and a **vocabulary** for understanding the game.

#### 18.13.1 The Reactions panel (off-turn decisions)

The Action Bar cannot host an off-turn move, and the reason is structural rather than stylistic: it is a **single shared XML panel**. A button's enabled state is global, not per-seat, and every handler runs through `validateActivePlayer`, so a non-active player's click is rejected by construction. Any rule that says "you may do this on someone else's turn" therefore needs a different home.

The **Reactions panel** is that home — a small panel, bottom-right, that appears only when something is actually available and hides itself otherwise. It carries the free off-turn decisions of §11.2:

| Reaction | Who | Cost | Why it is off-turn |
|---|---|---|---|
| **Witness** (§10.1) | any ally at a Haunted character's tile | 1 Sanity | The haunting is resolved on the *haunted* player's turn; the helper is by definition not the active player. |
| **Rally** (§6.5) | Luca | free, once per round | The gift has to arrive while the recipient can still spend it. |

**The pattern that makes a shared panel safe:** every row **names its actor** ("Rayman: see what Coco sees — pay 1 Sanity"), and the click handler verifies that the clicking player *is* that actor. This matters more here than for an ordinary button, because both reactions spend the actor's own stat — a shared panel must never let one player spend another player's Sanity. Rows are rebuilt on every state change and re-validated on click, so a row whose preconditions expired between render and click says so instead of firing.

Naming the actor also does onboarding work for free: the panel is a public, readable statement that *this player has a live option right now*, which is exactly the table-talk prompt the two rules were added to create.

### 18.14 Component teaching: tooltips, confirms, broadcasts

Three patterns ensure that every interaction is self-teaching.

**Tooltips on every interactable.** Hovering any object shows a 1–2 line description plus the object's relevant rule:
- Resource tokens: "Wood — found at Basketball/Badminton Courts. Used in crafting and as fuel."
- Stat sliders: "Hunger — depletes 1 per day. Below 3 you cannot Fight."
- Doom marker: "Doom 9. Next threshold at 10: night threats +1."
- Threat cards: their own rules text in larger type.

**Confirm-before-spend dialogs.** Any action that consumes resources first shows a dialog:

> **Craft Crowbar?** Cost: 2 Metal + 1 Wood. You have: 3 Metal, 2 Wood.
> [✓ Confirm] [✗ Cancel]

Players never accidentally commit a cost. New players also learn the cost mechanic just by seeing it surfaced.

**Chat broadcast log with color coding.** Every game-state change is announced in chat:

| Color | Meaning | Example |
|---|---|---|
| 🔴 Red | Damage / loss event | "Coco loses 3 Sanity from isolation." |
| 🟡 Yellow | Warning / threshold crossing | "Doom reaches 15 — Scarcity: crafts cost +1 extra resource." |
| 🟢 Green | Positive event / gain | "Rayman gathered Wood. Echoes 6: bonus Item drawn." |
| 🔵 Cyan | Phase change | "Phase 3: Long Nights begins. Doom rate +2/day." |
| ⚪ Gray | Procedural | "Day Counter: 3. First Player passes to Rayman." |

The chat log is scrollable, so a player who arrives mid-game (or stepped away) can recover state by scrolling back. This is the implicit "save game replay" that TTS does not natively provide.

### 18.15 Iconography and the severity legend

A standard icon set is used across all printed components and all UI panels. New players learn each icon once and recognize it everywhere.

| Icon | Meaning |
|---|---|
| ❤ | Health |
| 🍴 | Hunger |
| 🧠 | Sanity |
| 🪵 | Wood |
| ⚙ | Metal |
| 🧵 | Cloth |
| 🍎 | Provisions |
| ⚡ | Energy Drink |
| 🔋 | Battery |
| ⚔ | Combat damage |
| 🛡 | Defense / cover |
| 🔥 | Light source / fire |
| 🌑 | Darkness — Charlie risk |
| ●●●○○ | Severity rating (Dawn/Threat cards) |

A small **Severity Legend** card sits permanently next to the Threat deck:

> ●○○○○ — Atmospheric flavor only.
> ●●○○○ — Minor stat hit.
> ●●●○○ — Combat or lasting effect.
> ●●●●○ — Phase-shift event.
> ●●●●● — Boss arrival / apocalyptic.

The dots that appear on Dawn and Threat cards are now legible at a glance. A new player sees ●●●●● and braces; they don't need rules text to feel the threat.

The Doom track also has its **threshold ribbon printed on the board itself** beside the relevant step:

```
Doom track:
[start] 5 [10: Night threats +1] 15 [Crafts +1 cost] 20 [-1 Sanity Tick]
        25 [Bosses any phase]   30 [DEFEAT]
```

The looming pressure is concrete, not abstract.

### 18.16 Onboarding: setup walkthrough and character introduction

The Setup button does not just deal cards — it walks players through a guided sequence that doubles as a tutorial.

**Step 1 — Pick a path graph.** A modal: "Pick a starting layout." Three buttons (Compact / Sprawl / Linear), each with a small preview image. Click → that variant's path edges spawn between the location tiles. Other two are removed.

**Step 1.5 — Optional variants.** A small host-only modal with two toggles, both OFF by default, and a Continue button: **Rotation turns** (§11.2 — one action per visit) and **Random Scenario** (§17.3 — revealed after characters are chosen). The modal says explicitly: "Both off = the standard game. First game? Just click Continue." — the §18.10.7 principle (the first decision is small) means new tables must be able to click straight through.

**Step 2 — Pick characters.** Each seated `Player.Color` gets a pop-up showing all five character cards (front + back), with one-line plain-language strengths under each:
- *James — fast learner; reads cards before drawing them.*
- *Coco — heals, calms, immune to the dark.*
- *Rayman — strongest fighter; loud and hungry.*
- *Ellie — feeds the team; everyone benefits.*
- *Luca — boosts allies; charisma at the campfire.*

A player picks one. Picked characters turn unavailable for other seats. Coco starts at Ellie & Luca's House (handled by the script).

**Step 3 — Read your character briefing.** Each player gets a one-time popup, visible only to them:

> **You are Rayman, the Basketball Player.**
>
> **Strengths**
> - Move 1 extra space per Move action.
> - +1 attack die at the Basketball Court.
> - Defend: shield adjacent allies for one round.
>
> **Constraint**
> - Big Appetite: lose 2 Hunger per day (others lose 1).
> - Loud: if you moved today, wherever you sleep draws +1 Threat tonight.
>
> **Try first:** Move to the Basketball Court and gather Wood — your Court Master perk applies there.
>
> [I understand]

This single popup is the on-ramp. New players read it, dismiss it, and they have the gist of their character without having opened the rulebook.

**Step 4 — Day 1 begins.** Phase banner takes over; "Reveal Dawn" button is the only highlighted action. The team is in the river of play.

### 18.17 The Help menu and the "What next?" hint

A floating **Help (?)** button on the Phase Banner opens a side panel with six tabs. The panel is read-only (no game state changes); it stays open while the game continues.

| Tab | Content | Source |
|---|---|---|
| **Rulebook** | **The complete player rulebook**, page by page | The four `content/` sections, in `PlayerRules.md` order |
| **Start** | 1-page summary of the loop and victory conditions | Notebook content, rewritten for the chosen difficulty |
| **You** | Active player's perks, constraints, suggested first move | Per-character data |
| **Dawn** | Full text of the current Dawn card and any ongoing effects | `gameState.activeDawn` |
| **Doom** | Current value, next threshold, all threshold rules | `gameState.doom` lookup |
| **Terms** | Every icon and keyword in the game | Static reference |

**The Rulebook tab is the answer to "where are the rules?"** It carries the same four sections in the same order as the browser rulebook (`PlayerRules.md` / `PlayerRules.html`) — Quick Start, Full Rules, The Characters, Glossary — assembled from the same `content/` markdown, so the book at the table and the book in the browser cannot drift. A rule a player can only read by leaving the game is a rule they will not read. (`tests/test_cross_refs.py::test_ingame_rulebook_mirrors_the_player_rulebook` fails if one gains a section the other lacks.)

**Every tab is paged, and this is not a nicety.** A TTS `Text` element renders what fits and **clips the rest silently** — no scrollbar, no ellipsis, no warning, no error. The Quick Start *notecard* taught this lesson once already (hence `QUICKSTART_CARD_BUDGET`), but the Help panel had the same defect at larger scale and unmeasured: the Glossary is ~7,000 characters against a body that holds roughly 2,000, so **two thirds of the game's own reference material was invisible** and the tab looked fine. Pagination (`lua/ui_help_pages.lua`) splits on line boundaries, keeps a heading with the text beneath it, and hides its own nav row on single-page tabs. Two tests hold the line: pagination must lose nothing, and no page may exceed the body's estimated line capacity — otherwise paging has merely relocated the clipping.

A second smaller button next to Help: **"What next?"** — context-aware advice. Click during:
- Day Phase: "It's your turn, Ellie. You have 2 actions left. Suggested: cook a recipe at the Kitchen — you have 2 Provisions and 1 Wood available."
- Dusk: "Last chance to move: scramble 1 tile (1 Hunger) via the Dusk panel, or stay put. You sleep where you stand."
- Night: "Resolving threats at Badminton Court. Coco is here; click Resolve to proceed."
- After a defeat: "The team lost on Day 6. Click Restart to try again with the same characters, or Setup for a fresh game."

The hint is generated from current state. It is the single most important new-player aid: the system does not assume they know anything.

### 18.18 Phase mood, end-of-round summary, and safety nets

**Phase mood.** The visual environment subtly changes by phase, providing a felt rhythm:

| Phase | Lighting / mood | UI cue |
|---|---|---|
| Dawn | A flash; the Phase Banner highlights for 3 seconds | "Reveal Dawn" prominent |
| Day | Normal warm lighting | Action Bar enabled |
| Dusk | Slight desaturation | "Scramble or stay" banner; Dusk panel offers the 1-tile scramble |
| Night | `Lighting.LightIntensity` lowered ~25%; cooler ambient | Threats pile face-up by location; "Resolve Night" prominent |
| Tick | Brief animated slide of stat tokens; soft chime | "End-of-Round Summary" panel shows |

These cues are not gameplay — they are *legibility*. Players know what phase they're in by the table's mood.

**End-of-Round Summary.** After Tick, a 6-second auto-dismissing panel summarizes:

> **End of Day 3 — Strange Days**
> - Doom: 8 → 9
> - Lost: Rayman 2 Hunger, Coco 3 Sanity → DOWN
> - Gained: Stew cooked, Crowbar crafted, Toy Bow drawn
> - Threats defeated: Shadow Stalker
>
> **Next:** Day 4 Dawn — click Begin Day when ready.

Players who looked away can catch up with one read. The panel is dismissable manually if everyone's already absorbed it.

**Safety nets.** Risky or irreversible actions get a second confirmation:
- Ending the Day Phase before all players have spent their actions.
- Sleeping alone at a sport court (the worst case in the game).
- Spending the last Telltale Heart.
- Moving an injured character into a high-threat zone at Dusk.

The system is not stopping bad plays — it is ensuring the player meant it.

**Fail-friendly defaults.** If a player does something the rules don't strictly cover, the game does *not* throw a script error. It silently allows it and posts a chat note: "(Edge case — the rules don't strictly cover this. Continuing.)" This means new players exploring the buttons cannot break the session.

### 18.19 Accessibility standards (the floor)

The design's accessibility *instincts* are largely good, and it is worth saying so: resources are double-coded by icon and colour (§8 — "brown plank," "grey gear," "yellow can"), the severity rating is position-coded as well as counted (§15.5), boss standees use scale hierarchy (§5), and player boards are built for at-a-glance reading (§10.2). That is most of the work done by information-design discipline rather than by accessibility intent — a good sign, and not a substitute for a floor.

Because accessibility done by instinct has no floor, and the lapses instinct misses are exactly the ones this design had: the audio-only Night Sound (fixed — §15.8 now ships a visual twin) and the §10.2 constraint panel coded by "red border," a colour-only distinction against the perk panel beside it. Per [PrinciplesOfGoodBoardGames.md §23](../../Archive/PrinciplesOfGoodBoardGames.md) — Accessibility Is Design, Not Accommodation — this is a design-time constraint, not a post-production one, and the art for this game is not finished, which makes now the cheap moment.

**The floor, as a checkable list.** Every item is a pass/fail question about a specific component, not an aspiration:

1. **No colour-only distinctions.** Every colour-coded distinction is *also* coded by shape, icon, position, or label. (Open item: the §10.2 constraint panel needs a label or icon, not only a red border. The chat broadcast categories of §18.14 already carry a text prefix, so they pass.)
2. **Every audio cue has a visual twin.** Any sound that carries information is mirrored by something on screen carrying the *same* information and no more. (§15.8's Night Sound now pairs the growl with a moon glyph in the Phase Banner — deliberately just as non-specific, because the design intent is dread without data.)
3. **Text size and contrast, as numbers.** XML UI body text is **≥ 12 px** and panel titles **≥ 14 px** at TTS's default UI scale; text-on-panel contrast is **≥ 4.5:1** for body copy and **≥ 3:1** for large/bold text (WCAG AA). The dark panels (`#000000B2` and darker) with `#BBCCDD`-or-lighter body text clear this; the light "rulebook page" setup panels (`#F2E8D5F7` with `#3A362E` text) clear it comfortably.
4. **No information conveyed only by animation or timing.** The standee bob and hand-zone glow of §18.12 are *redundant* channels — the Phase Banner always carries the same fact in text. Nothing may be signalled by motion alone. (This is also why the End-of-Round Summary of §18.18 no longer auto-dismisses.)
5. **A content note at setup.** The game is cosmic-horror themed with body horror in its death narrations and a stalking-in-the-dark antagonist. The welcome sequence states this before characters are chosen, so nobody discovers it mid-game.
6. **Readable without audio, and playable muted.** A full campaign must be completable with sound off. This falls out of (2) but is worth stating as its own check, because virtual-tabletop players are frequently in voice chat with game audio down.

**Reviewing against this list** is a step in adding any component, in the same way §18.10's "show it to a player who has never read the rules" is. An item that fails one of these six is not shipped and then patched; it is redesigned.

### 18.20 What this UX program is not

This is not a list of polish items to ship in a v2 patch. **Every item in §18.10–18.19 is part of the v1 design**, because the design's stated player-experience goal is *playable on the table without a rulebook* (§1.4). A TTS implementation that omits these is not an implementation of *this* game — it is a different, harder-to-onboard game wearing the same components.

The original build plan that walked the implementation through Phases A–K (the source of the phase codes like `F.3` / `E.8` still cited in code comments) was retired in 2026-07 — recover it from git history if needed; current build status lives in `agents.md` and `README.md`.

---

