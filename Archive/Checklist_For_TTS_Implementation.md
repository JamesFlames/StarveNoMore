# Checklist for TTS Implementation — Starve No More

> A concrete, complete, ordered build checklist for shipping the **Starve No More** mod in **Tabletop Simulator** (Berserk Games, app `286160`). Source design: [StarveNoMoreDesignConcept.md](StarveNoMoreDesignConcept.md). TTS reference: [docs/HowToCreateGamesInTabletopSimulator.md](docs/HowToCreateGamesInTabletopSimulator.md).
>
> **Design priority for this implementation:** *the game must be playable on first sit-down without reading the rules.* This is enforced by the UX program in [Design §18.10–18.18](StarveNoMoreDesignConcept.md). Every task below is gated on serving that goal.

---

## How to use this document

- Tasks are grouped into **Phases** (A through K). Phases are sequential; do not begin Phase B work before Phase A is complete unless the task explicitly says it can run in parallel.
- Within a phase, tasks are numbered. Numbering is the recommended execution order.
- Each task lists: **what** it produces, **how** to do it, **inputs** it depends on, and **done-when** acceptance criteria.
- Cross-references like `[TTS §5.1]` point at the section in `docs/HowToCreateGamesInTabletopSimulator.md` that explains the TTS API used.
- Cross-references like `[Design §6.2]` point at the section of `StarveNoMoreDesignConcept.md`.
- **No task is done until its done-when is satisfied.** "Done" means the system passes the acceptance test, not "the code is written."

---

## Phase summary

| Phase | Title | Order | Roughly when |
|---|---|---|---|
| **A** | Pre-production: design lock, content authoring, UX text | First | Before any TTS work |
| **B** | Asset production: art, icons, atlases, models | After A | Producible in parallel with C–D |
| **C** | Asset hosting and URL contract | After B begins | Required before any save uses real URLs |
| **D** | TTS scaffold: empty save, table, lighting, hand zones | After A | Can start once A is locked |
| **E** | Component placement: boards, decks, tokens, dice, standees, legends | After C, D | The bulk of build work |
| **F** | Lua scripting: gameplay loop (setup, day/night, combat, save/load) | After E | The brain |
| **G** | UX Layer 1: always-on UI (Phase Banner, Action Bar, tooltips, chat) | After F first pass | Self-teaching surface |
| **H** | UX Layer 2: onboarding (Setup walkthrough, character popup, Help menu, What-now hint) | After G | First-time-player path |
| **I** | UX Layer 3: feedback and safety nets (severity legend, threshold ribbon, phase mood, summary, confirms) | After H | Polish layer that completes the "playable without reading" goal |
| **J** | Performance, accessibility, final polish | After I | Final pre-publish pass |
| **K** | Playtest, publish, iterate | Last | Workshop release and beyond |

---

# Phase A — Pre-production

The cheapest fixes happen here. Do not start Phase B–E without a locked design and authored content.

## A.1 Lock the design brief

- **What.** A frozen v1 of [StarveNoMoreDesignConcept.md](StarveNoMoreDesignConcept.md) that no other phase will edit speculatively.
- **How.** Read the full design doc. Make a list of any open questions, ambiguous numbers, or unresolved rules. Resolve each with the design owner (or escalate to a "needs playtest" pile).
- **Inputs.** The design doc as written.
- **Done-when.**
  - Every numeric value in the design doc has a single canonical answer (Hunger ranges, Doom rates, recipe costs).
  - Every component in §5 has a final quantity.
  - Every character's stats, perks, constraints, and starting hand are signed off.
  - Open questions are tagged `[PLAYTEST]` or `[FROZEN]`.

## A.2 Author the full card content as a spreadsheet

- **What.** A canonical CSV/spreadsheet (one tab per deck) listing every Phase, Market, Recipe, Threat, Visitor, and Trophy card with all printed text. This is the source of truth that drives art production (Phase B), `CustomDeck` JSON (Phase E), and effect dispatch tables (Phase F).
- **How.** Create `content/cards.xlsx` with tabs:
  - `Phase1_Dawn`, `Phase2_Dawn`, `Phase3_Dawn`, `Phase4_Dawn` — columns: ID, Title, Severity dots (1–5), Immediate effect text, Ongoing effect text, Art notes.
  - `Market` — columns: ID, Name, Category, Craft Cost, Use Effect, Persistent? (Y/N), Tooltip text, Art notes.
  - `Recipes` — columns: ID, Name, Ingredients, Cost (Action/Health), Effect, Tooltip text, Art notes.
  - `Threats` — columns: ID, Name, Type (Soft/Hard/Persistent), HP, Attack dice, Special, Severity dots, Tooltip text, Art notes.
  - `Visitors` — columns: ID, Character, Trigger, Immediate effect, Departure rule.
  - `Trophies` — columns: ID, Boss defeated, Passive bonus, Art notes.
- **Inputs.** A.1.
- **Done-when.** Spreadsheet has the full card counts targeted by [Design §5](StarveNoMoreDesignConcept.md): ~40 Phase cards (10 per phase), ~50 Market, ~20 Recipes, ~30 Threats, ~6 Visitors, 4 Trophies. Effect text is plain-language (it should read as a sentence a new player can act on, not as legalese).

## A.3 Author the TTS-side content tables

- **What.** Three more spreadsheet tabs: `Locations`, `Resources`, and `Tooltips`.
- **How.**
  - `Locations` — mirror [Design §7](StarveNoMoreDesignConcept.md): name, yield list, special action text, sanity modifier, defense, house-owner, threat draw rate.
  - `Resources` — mirror [Design §8](StarveNoMoreDesignConcept.md): name, color, icon, tag string, source location list.
  - `Tooltips` — one row per tagged object type (resource, slider, action button, deck, marker), giving the 1–2 line hover text per [Design §18.14](StarveNoMoreDesignConcept.md). Will be loaded as a Lua table at runtime.
- **Inputs.** A.1.
- **Done-when.** All three tabs are populated; Tooltips covers every object class in the design.

## A.4 Author the iconography spec

- **What.** A 1-page spec for the visual vocabulary in [Design §18.15](StarveNoMoreDesignConcept.md): one icon per stat, per resource, per game keyword, plus the severity-dot system.
- **How.** Write `content/iconography.md` listing every icon, its symbolic meaning, and its rendering notes (silhouette-distinct so colorblind players can read them). Include the 5-tier severity-dot ladder.
- **Inputs.** A.1.
- **Done-when.** Every icon used anywhere in the game is on the list with an unambiguous meaning.

## A.5 Define the asset URL contract

- **What.** A document `content/asset_manifest.md` listing every asset file the game needs, with planned final URL.
- **How.** For each component (board, location tile faces, character standees, deck atlases, token icons, boss standees, icon set, severity legend, Help-menu graphics) write a row: `<asset_id> | <local file path during dev> | <final URL pattern>`.
- **Inputs.** A.1, A.4.
- **Done-when.** Manifest covers every visual asset referenced anywhere in the design doc. Dev paths exist as `file:///` URLs for local prototyping.

## A.6 Write the rules summary text (Notebook + Help-menu tabs)

- **What.** Markdown documents that populate the in-game Notebook (§18.7) and the Help-menu tabs (§18.17):
  - `content/notebook/quickstart.md` — 1-page summary.
  - `content/notebook/full_rules.md` — abridged rulebook (~6–8 pages).
  - `content/notebook/character_reference.md` — perks/constraints for all 5 characters.
  - `content/help/glossary.md` — every icon, every keyword, with one-line definitions.
  - `content/help/character_briefings.md` — per-character one-time popup text (the "you are Rayman..." copy).
  - `content/help/whatnow_hints.md` — context-aware hint strings keyed by phase, sub-phase, and character state.
- **How.** Strip the design doc to play-relevant text only. Write in second person ("On your turn, you take 3 actions"). Test each by handing a single page to a non-player and asking what they'd do.
- **Inputs.** A.1.
- **Done-when.** A first-time player could read Quickstart in <5 minutes and play a turn. Each character briefing fits on one screen at default font size.

---

# Phase B — Asset production (art, icons, models)

Begins as soon as Phase A is locked. Runs in parallel with D and the early steps of E (placeholder rectangles work for layout).

## B.1 Define the visual style guide

- **What.** A 1–2 page art bible: palette, line weight, typography, lighting model.
- **How.** Mood-board from [Design §1.2](StarveNoMoreDesignConcept.md): Tim-Burton, Edward-Gorey, Laika stop-motion. Lock to a muted earth-tone palette with one saturated red for danger. Specify ink-line weight, body typeface, and a hand-drawn display face.
- **Done-when.** A test card and standee render in the locked style. Both look at-home together.

## B.2 Produce the icon set

- **What.** All icons from `content/iconography.md` rendered as transparent-background PNGs, sized 256×256. Stat icons (❤🍴🧠), resource icons (🪵⚙🧵🍎⚡🔋), action icons (🚶🤲🛠🍲⚔💤🛐), keyword icons (⚔🛡🔥🌑), severity dots (●○).
- **How.** Single artist, single style pass. Each icon has both color and silhouette identity (color-blind-safe by silhouette alone). Export at 256×256 with 1px transparent padding so they composite cleanly on cards and buttons.
- **Done-when.** All ~25 icons render correctly at 32×32 (button size) and 256×256 (card size) without losing identity.

## B.3 Produce the main board image

- **What.** One large image (4096×4096) of the suburban map background — paths, ambient cul-de-sac details, decorative dressing for the 5 location snap points, **and the 31-step Doom track with threshold ribbons printed on it** ([Design §18.15](StarveNoMoreDesignConcept.md)).
- **How.** Sketch first, ink, color flat, shade. The Doom track is part of the board art — at steps 10, 15, 20, 25, 30 print the threshold rule in small text inside a banner shape (e.g., "10: night threats +1"). Export as PNG.
- **Done-when.** Image is < 4 MB. Threshold ribbons are legible at default zoom.

## B.4 Produce the 5 location tile face images

- **What.** Five rounded-square images, one per location.
- **How.** Each tile has a clear illustration, the location name, and a small **icon strip** showing yield + defense + sanity-modifier using the icons from B.2. The icon strip is the at-a-glance "what does this place do" — see [Design §18.10 principle 1](StarveNoMoreDesignConcept.md).
- **Done-when.** A new player can read each tile and tell, without rules, what's there and how dangerous it is.

## B.5 Produce the character art

- **What.** Five **standee** images (front + back + ghost variant) and five **player board** layouts.
- **How.**
  - Standees: full-body, line + flat color, on white. Each character per [Design §6](StarveNoMoreDesignConcept.md) visual brief.
  - Player boards: rectangle layout exactly per [Design §10.2](StarveNoMoreDesignConcept.md) — top strip with name + portrait + tagline; left side three icon-driven stat tracks with shaded threshold zones; perks panel with icon-block-per-perk; constraint panel with red border; bottom Action Bar with the 7 action icons; Action Cube track; corner starting-hand legend.
  - Ghost variants: desaturated palette, semi-transparent.
- **Done-when.** All five characters render at standee + ghost + player board. Player boards are readable without reference to rulebook.

## B.6 Produce the deck atlases

- **What.** Card-face atlases for each deck. Each atlas is a single PNG arranged in a grid, [TTS §5.1].
- **How.** For each card in `content/cards.xlsx`, render at 408×585 px. Card layout per [Design §9.6](StarveNoMoreDesignConcept.md) sample cards:
  - Header bar: title + severity dots (top-right corner) where applicable.
  - Type tag line (Tool/Weapon/Spell/etc).
  - Cost line with resource icons.
  - Effect text in second-person plain language ("Restores 4 Hunger.").
  - Footer: pillar trace or flavor (small italic).
- **Atlases:**
  - 4 Phase atlases (~12 cells each).
  - Market atlas (~50 cells, 7×8).
  - Recipe atlas (~20 cells, 5×4).
  - Threat atlas (~30 cells, 6×5).
  - Visitor atlas (~6 cells, 3×2).
  - Trophy atlas (4 cells, 2×2).
- **Done-when.** Each atlas < 4 MB. Each card readable at default zoom in TTS without zooming in.

## B.7 Produce the Severity Legend card

- **What.** A single permanent reference card (large, ~600×800 px) showing the 5-tier severity-dot ladder ([Design §18.15](StarveNoMoreDesignConcept.md)).
- **How.** Five rows: dot rendering on the left, plain-language meaning on the right. Same visual style as cards.
- **Done-when.** Card is finished. It will be placed permanently next to the Threat deck in Phase E.

## B.8 Produce token and resource icons

- **What.** Six resource token images, Telltale Heart token, 15 stat marker tokens (3 per character, color-coded), Doom marker, Day Counter face graphic.
- **How.** Reuse the icon set from B.2. Tokens are circular with the icon centered.
- **Done-when.** All token images render at 64×64 in TTS without losing identity.

## B.9 Produce boss standee art

- **What.** 4 boss images (The Deerclops, The Eye of Terror, The Source, mid-tier Phase 2 boss) plus backs.
- **How.** Render at noticeably larger pixel dimensions than character standees ([Design §19 row 13](StarveNoMoreDesignConcept.md) — Cthulhu Wars scale-as-information).
- **Done-when.** Bosses tower visually over character standees in test renders.

## B.10 Produce optional 3D models

- **What.** Optional Crockpot model, Doom track marker model.
- **How.** Low-poly (< 5k tris), `.obj` + diffuse PNG. [TTS §5.2].
- **Done-when.** Models load in TTS at correct scale. Skip if schedule is tight — flat tiles work.

## B.11 Produce UI panel backgrounds

- **What.** Background images for the Phase Banner (top bar), Help menu side panel, and modal dialogs.
- **How.** Subtly textured dark backgrounds in the locked palette (B.1). Slight transparency so the table reads through.
- **Done-when.** Backgrounds composite cleanly behind UI elements at 1080p and 1440p.

---

# Phase C — Asset hosting and URL contract

Begins as soon as the first asset from Phase B is approved.

## C.1 Choose the hosting strategy

- **What.** A decision: Steam Workshop (default), CDN, or imgur direct.
- **How.** Pre-publish: use `file:///` URLs locally + an imgur direct-link mirror for any teammate testing. Publish: rely on Workshop's automatic asset upload.
- **Done-when.** A written one-paragraph note in `content/asset_manifest.md` declaring the strategy.

## C.2 Upload finalized assets

- **What.** All Phase B output uploaded to the chosen host.
- **How.** Upload images via host UI. Verify each URL returns the correct `Content-Type`. Update `content/asset_manifest.md` with resolved URLs.
- **Done-when.** Every asset row in the manifest has a live URL. Spot-check 5 random URLs in a browser.

## C.3 Set up the asset URL constants

- **What.** A Lua module `lua/assets.lua` that lists every URL by ID.
- **How.** Generate from `content/asset_manifest.md`. Example:
  ```lua
  return {
    BOARD_MAIN     = "https://i.imgur.com/xxx.png",
    TILE_JAMES     = "https://i.imgur.com/yyy.png",
    DECK_PHASE1_FACE = "https://i.imgur.com/zzz.png",
    ICON_HEALTH    = "https://i.imgur.com/aaa.png",
    UI_BG_BANNER   = "https://i.imgur.com/bbb.png",
    -- etc.
  }
  ```
- **Done-when.** Module exists, referenced by all Phase E placement scripts.

---

# Phase D — TTS scaffold

Can start as soon as Phase A is locked. Independent of B/C if `file:///` URLs are used during scaffolding.

## D.1 Create the empty save

- **What.** A blank save file `saves/StarveNoMore.json`.
- **How.** In TTS: *Create → Single Player → Classic*. Save as "Starve No More". Set `GameMode = "Starve No More"`.
- **Done-when.** File exists; reloading produces an empty table.

## D.2 Choose the table and sky

- **What.** Final table and sky.
- **How.** Recommend `Table_Hexagon` or `Table_Custom` with wood texture (cozy half of cozy-dread). Sky: `Sky_Museum` or `Sky_Indoor`.
- **Done-when.** Save reflects the chosen `Table` and `Sky` in JSON.

## D.3 Configure base lighting

- **What.** Mood lighting — dim, cool, with faint warm fill. **Note:** lighting will dynamically shift by phase in Phase I.16; this task sets the Day-phase baseline.
- **How.** `LightIntensity ≈ 0.55`, `AmbientIntensity ≈ 1.0`, `AmbientSkyColor` to a desaturated blue.
- **Done-when.** Test load looks like a candlelit kitchen, not an office.

## D.4 Place player hand zones

- **What.** Five `HandTrigger` zones, one per active seat color.
- **How.** Pick five `Player.Color` (suggest White, Red, Yellow, Green, Blue). Drop `HandTrigger` per seat with the gizmo, set color, position, scale. [TTS §5.6, §10].
- **Done-when.** Cards placed in each are private to that seat from a second client.

## D.5 Disable Turns API for now

- **What.** Turns API is **off** at scaffold; turn order is enforced by Phase G's Phase Banner + Lua.
- **How.** `Turns.Enable = false` in JSON.
- **Done-when.** No turn indicator appears on load.

---

# Phase E — Component placement

Uses the URLs from C and the spreadsheet from A.2.

## E.1 Place the main board

- **What.** A locked `Custom_Board` showing the suburban map (with Doom threshold ribbons baked in, B.3).
- **How.** *Objects → Components → Custom → Board*. Image URL = `BOARD_MAIN`. Scale ≈ `(12, 1, 12)`. Lock.
- **Done-when.** Board visible at center, locked.

## E.2 Attach snap points to the main board

- **What.** Snap points for: 5 location tiles, 31-step Doom track, Day Counter, 5 Market slots, Threat-deck slot, Phase-deck slot, Visitor-deck slot, 4 Trophy slots, Severity Legend, Help button anchor.
- **How.** Right-click → Toggle Gizmos → Snap Points. Tag each (`Snap:Location:JamesHouse`, etc.). [TTS §16.4].
- **Done-when.** Test object dropped near each anchor snaps cleanly.

## E.3 Place the 5 location tiles

- **What.** Five locked `Custom_Tile` (rounded square) objects.
- **How.** Image URLs from manifest. Tag `Location:<Name>`. Lock.
- **Done-when.** All 5 tiles placed and locked.

## E.4 Place per-location snap points

- **What.** Each tile gets snap points for: 5 character slots, 1 boss slot, 1 active-threats slot.
- **How.** Gizmo workflow attached to the tile. [TTS §6.3].
- **Done-when.** Standees on a tile snap to one of 5 slots.

## E.5 Place path-edge variant cards

- **What.** Three small decorative tile sets (Compact / Sprawl / Linear) per [Design §7.6](StarveNoMoreDesignConcept.md).
- **How.** Each variant is a tagged group of small `Custom_Tile` decorations between locations. Stored in a tray off-board; setup script (Phase F) activates one.
- **Done-when.** Each variant set is a tagged container reachable from Lua.

## E.6 Place the Doom track marker

- **What.** One `Custom_Token` on the Doom track step 0.
- **How.** URL from manifest. Tag `DoomMarker`. `Snap = true`.
- **Done-when.** Marker rests on step 0.

## E.7 Place the Day Counter

- **What.** One `Counter` widget on its snap point.
- **How.** *Objects → Tools → Counter*. Initial value 1. Tag `DayCounter`. Lock. [TTS §4.2].
- **Done-when.** Counter shows "1".

## E.8 Build and place the Phase decks (4)

- **What.** Four `DeckCustom` objects, ~10 cards each.
- **How.** Hand-edit save JSON to splice `DeckCustom` entries with `ContainedObjects` arrays referencing each phase's atlas. Tag every card `PhaseCard:<phase>`, deck `PhaseDeck:<phase>`. [TTS §5.1].
- **Done-when.** All 4 decks load. Each card displays correctly.

## E.9 Build and place the Market deck and 5-slot display

- **What.** One `DeckCustom` (~50 cards) + 5 face-up snap points.
- **How.** Same pattern as E.8. Setup script (Phase F) deals 5 face-up to the display. Tag `MarketCard` / `MarketDeck`.
- **Done-when.** Deck spawns face-down; 5 cards face-up after setup.

## E.10 Place the Recipe cards

- **What.** ~20 loose `Card` objects, face-up, on a "reference rack" off main play.
- **How.** Spawn individually. Tag `RecipeCard`.
- **Done-when.** All 20 visible in a row, readable.

## E.11 Build and place the Threat deck

- **What.** One `DeckCustom` (~30 cards), face-down.
- **How.** Same pattern. Tag `ThreatDeck` / `ThreatCard`. Persistent threats sub-tagged `Persistent`.
- **Done-when.** Deck spawns face-down with all 30.

## E.12 Build and place the Visitor deck

- **What.** Small `DeckCustom` (~6 cards) for 3- and 4-player games.
- **How.** Same pattern. Tag `VisitorDeck` / `VisitorCard`.
- **Done-when.** Lua can `takeObject` from it.

## E.13 Build and place the Trophy cards

- **What.** 4 loose `Card` objects in a Trophy display row, face-down at start.
- **How.** Spawn individually. Tag `TrophyCard`.
- **Done-when.** 4 trophy cards in their display row.

## E.14 Place the resource Infinite Bags

- **What.** Six `Infinite_Bag` objects (Wood, Metal, Cloth, Food, Energy Drink, Battery). [TTS §5.5].
- **How.** Spawn one `Custom_Token` per resource, drop into a tagged `Infinite_Bag` (`ResourceBag:<Type>`).
- **Done-when.** Each bag dispenses tokens of its type.

## E.15 Place the dice

- **What.** 6 `Die_6` and 1 `Custom_Dice` (8-faced Sanity d8).
- **How.** Spawn into a "combat dice tray" snap zone. d8 from a `Custom_Dice` definition. Tag `SanityD8`. [TTS §5.4].
- **Done-when.** All dice roll cleanly.

## E.16 Place character standees and player boards

- **What.** Five `Figurine_Custom` standees + five `Custom_Tile` player boards.
- **How.** Standees from per-character atlases. Player boards as rectangle tiles in trays near each hand zone, with stat-marker tokens at starting values, action cube tracks visible. Tag standees `Character:<Name>`, boards `PlayerBoard:<Name>`. Add per-board snap points for stat markers + action cubes.
- **Done-when.** All 5 character kits exist as complete units.

## E.17 Place boss standees off-board

- **What.** 4 `Figurine_Custom` boss standees in a "Boss pool" tray.
- **How.** Spawn locked from atlases. Tag `Boss:<Name>` and `Boss`.
- **Done-when.** All 4 standees exist, visibly larger than character standees, tagged.

## E.18 Place Telltale Heart supply

- **What.** A small `Bag` containing 5 `Custom_Token` Hearts.
- **How.** Spawn 5 identical heart tokens, drop into a bag tagged `TelltaleHeartSupply`.
- **Done-when.** Bag holds exactly 5; test cook can remove + return one.

## E.19 Place the Severity Legend card

- **What.** The card produced in B.7, placed permanently beside the Threat deck.
- **How.** Spawn as a single locked `Card`. Tag `SeverityLegend`.
- **Done-when.** Legend is visible and readable beside the Threat deck.

## E.20 Place the Rules Quick-Start card

- **What.** A `Notecard` near the table edge labeled "Quick Start".
- **How.** Paste text from `content/notebook/quickstart.md`. Tag `QuickStart`.
- **Done-when.** Notecard visible and readable.

## E.21 Pretty-print the save JSON

- **What.** Pretty-printed copy for diffing.
- **How.** `jq . StarveNoMore.json > StarveNoMore.pretty.json`. Commit both to git.
- **Done-when.** Pretty save committed; diff is human-readable.

---

# Phase F — Lua scripting (gameplay loop)

The brain. Begins after Phase E components exist (placeholder content is fine while scripting is in progress).

## F.1 Set up the Global script skeleton

- **What.** A `LuaScript` block with `onLoad`, `onSave`, and `gameState` table.
- **How.** Open the Scripting window. Paste:
  ```lua
  gameState = {
    day = 1, phase = 1, doom = 0, started = false,
    activeChars = {}, ongoingDawnEffects = {}, activeColor = nil,
    subPhase = "Dawn", -- Dawn / Day / Dusk / Night / Tick
  }
  function onLoad(savedState)
    if savedState and savedState ~= "" then gameState = JSON.decode(savedState) end
    initButtons(); refreshPhaseBanner()
  end
  function onSave() return JSON.encode(gameState) end
  ```
  [TTS §6.1, §8.4].
- **Done-when.** `gameState` survives save/load.

## F.2 Implement tag-based lookup helpers

- **What.** Helpers that find objects by tag, not GUID. [TTS §13 pitfall 2].
- **How.** Add `findOneByTag`, `findAllByTag`, plus typed convenience wrappers (`getMarketSlot(n)`, `getActivePlayerBoard()`, etc.).
- **Done-when.** Test calls return correct objects.

## F.3 Implement the Setup() flow (without UX walkthrough)

- **What.** A bare-bones Setup that initializes a full game in one shot.
- **How.** This is the *gameplay* setup. The *guided UX walkthrough* that wraps it is built in Phase H.1. For now:
  1. Pick a path-edge variant at random.
  2. Shuffle each Phase deck.
  3. Shuffle Market deck. Deal 5 face-up to the display.
  4. Shuffle Threat deck.
  5. For each seated `Player.Color`: place a default character, deal starting hand.
  6. Set Day Counter = 1, Doom = 0.
  7. `gameState.started = true`.
- **Done-when.** Pressing a temporary "Quick Setup" button deals everything correctly.

## F.4 Implement the Day Advance flow

- **What.** A `BeginDay()` function callable from a button.
- **How.** Increments Day Counter, advances Doom by phase rate ([Design §15.6](StarveNoMoreDesignConcept.md)), checks thresholds, draws and reveals top Phase card, applies effects via dispatch table (F.5). Updates `gameState.subPhase = "Dawn"` then `"Day"`.
- **Done-when.** Pressing button reveals the next Dawn card; Doom marker animates to its new step; ongoing effects persist on save/reload.

## F.5 Implement the Dawn-card effect dispatch table

- **What.** Lua table mapping each Dawn card ID to a function with `onReveal` / `onCleanup` callbacks.
- **How.**
  ```lua
  dawnEffects = {
    P2_PORCH_LIGHT = {
      onReveal = function()
        forEachActivePlayer(function(c) modSanity(c, -1) end)
        gameState.ongoingDawnEffects.flashlightsDisabled = true
      end,
      onCleanup = function() gameState.ongoingDawnEffects.flashlightsDisabled = nil end,
    },
    -- ~40 entries
  }
  ```
- **Done-when.** Every Phase card has an entry; card text matches what the function does.

## F.6 Implement the Tick (decay) flow

- **What.** A `Tick()` function for Phase 5 ([Design §11.5](StarveNoMoreDesignConcept.md)).
- **How.** Apply decay per character (Rayman -2 Hunger), apply Coco/Luca/Ellie perks, pass First Player marker, check victory/defeat (F.10).
- **Done-when.** All 5 characters decay correctly on a button press.

## F.7 Implement combat dice rolling

- **What.** A `Combat()` resolver invoked from each player board's Fight button.
- **How.** Determine attacker, take attack-die count from `gameState`, roll d6s, `Wait.condition` until resting, tally hits/fumbles, pre-resolve fumble damage, prompt target selection for hits.
- **Done-when.** Combat resolves end-to-end without manual intervention.

## F.8 Implement crafting and cooking

- **What.** Click handlers for the Market and the Crockpot.
- **How.**
  - Crafting: clicking a Market card → confirm dialog → discard resources → move card to clicker's hand → deal new market card.
  - Cooking: clicking a Recipe at a Crockpot location → confirm ingredients → discard them → apply Recipe effect.
- **Done-when.** A test craft + cook sequence runs without manual cleanup.

## F.9 Implement the night-phase resolver

- **What.** A `ResolveNight()` function for Phase 4 ([Design §11.4](StarveNoMoreDesignConcept.md)).
- **How.** For each location with players, least-populated first: compute threat count, draw threats, resolve via dispatch (similar to F.5), Charlie check, storytelling, sleep regen per [Design §11.4 step 5 table](StarveNoMoreDesignConcept.md).
- **Done-when.** A scripted night resolves all threats and applies sleep correctly across 5 locations.

## F.10 Implement victory and defeat detection

- **What.** Functions tested every Tick.
- **How.** Defeats: Doom ≥ 30; all characters Down; Day 7 + Source not stopped. Victories: Day 7 survival + check Pristine/Truth/Hero achievements.
- **Done-when.** Test scenarios trigger the correct banner.

## F.11 Implement the Cleanse Doom action

- **What.** A "Cleanse" button that consumes the bundle and reduces Doom by 2.
- **How.** Per-board button handler. Validate resources, return to bags, reduce `gameState.doom` by 2, animate marker.
- **Done-when.** A complete Cleanse runs without errors.

## F.12 Implement the Telltale Heart Recipe

- **What.** A Crockpot button that runs the heart-cook flow.
- **How.** Validate ingredients (1 Cloth + 1 Battery + 1 Food + 2 Health from cook). Pull Heart from supply bag (E.18). Error if supply empty.
- **Done-when.** Cook + consume + respawn cycles correctly.

## F.13 Implement Down/Ghost state and revival

- **What.** Character flip-to-ghost + revival button.
- **How.** When Health = 0 or Sanity = 0: flip standee, mark `gameState.activeChars[color].down = true`, restrict actions. Revive button at any location with a Down character: requires Heart + 2 reviver Health, restores half-max.
- **Done-when.** Kill → ghost → revive cycles cleanly.

## F.14 Implement save/load persistence

- **What.** All `gameState` fields survive a save/reload.
- **How.** Verify by: starting game, advancing 3 days, saving, quitting, reloading. Check Day, Doom, ongoing effects, character stats.
- **Done-when.** All test cases pass.

## F.15 Add error handling and broadcast diagnostics

- **What.** Every script-driven action either succeeds or posts a clear error in chat (per [Design §18.10 principle 4](StarveNoMoreDesignConcept.md)).
- **How.** Wrap public functions; on invalid input post `broadcastToColor("Cannot Cleanse — missing 1 Battery", clickerColor, {1, 0.4, 0.4})`.
- **Done-when.** Misclicked button produces a useful chat error, never silent failure.

---

# Phase G — UX Layer 1: always-on UI

The self-teaching surface. After this phase, a player can see what's happening, whose turn it is, and what they can do — without consulting any external rules. Builds [Design §18.11–18.15](StarveNoMoreDesignConcept.md).

## G.1 Build the Phase Banner

- **What.** A persistent panel anchored to the top of the screen showing Day / Phase / Doom / Active player / Next action ([Design §18.11](StarveNoMoreDesignConcept.md)).
- **How.** Global XML UI:
  ```xml
  <Panel id="phaseBanner" position="0 350 0" width="1400" height="60" color="#0009">
    <HorizontalLayout childForceExpandWidth="true" spacing="20" padding="10">
      <Text id="dayField" fontSize="22">Day: 1 of 7</Text>
      <Text id="phaseField" fontSize="22">Phase: Dusk of the Week</Text>
      <Text id="doomField" fontSize="22">Doom: 0 / 30</Text>
      <Text id="activeField" fontSize="22">— pre-game —</Text>
      <Text id="nextField" fontSize="22">Click Setup to begin</Text>
      <Button id="helpBtn" onClick="openHelp">?</Button>
      <Button id="hintBtn" onClick="whatNow">What now?</Button>
    </HorizontalLayout>
  </Panel>
  ```
  Lua function `refreshPhaseBanner()` is called whenever `gameState` changes; it pushes new strings via `UI.setAttribute`.
- **Done-when.** All 5 fields update live during a test playthrough. ?-button and What-now button are clickable (handlers stubbed in H.4 and H.5).

## G.2 Implement the Active-Player Indicator (4 channels)

- **What.** Four redundant signals of whose turn it is ([Design §18.12](StarveNoMoreDesignConcept.md)).
- **How.**
  1. Phase banner `activeField` updates with the player's name (G.1).
  2. Hand zone tint: `getObjectFromGUID(handZoneGUID).setColorTint(activeColor)`; reset others to neutral.
  3. Standee bobs every 4 seconds: `Wait.time` loop calling `setRotationSmooth` ±5° on the active standee.
  4. Inactive boards dim: `setColorTint({0.7, 0.7, 0.7})` on inactive boards; full brightness on active.
- **Done-when.** During a test turn pass, all 4 channels track the active player without lag.

## G.3 Build the per-player Action Bar

- **What.** Seven labeled icon buttons + 3 Action Cubes per board ([Design §18.13](StarveNoMoreDesignConcept.md)).
- **How.** Per-board XML UI:
  ```xml
  <Panel id="actionBar" position="0 80 0" width="900" height="120" color="#0006">
    <HorizontalLayout childForceExpandWidth="true" spacing="5">
      <Button id="moveBtn" onClick="doAction(self,'move')" image="ICON_WALK">Move (1)</Button>
      <Button id="gatherBtn" onClick="doAction(self,'gather')" image="ICON_HAND">Gather (1)</Button>
      <Button id="craftBtn" onClick="doAction(self,'craft')" image="ICON_TOOLS">Craft (1)</Button>
      <Button id="cookBtn" onClick="doAction(self,'cook')" image="ICON_POT">Cook (1)</Button>
      <Button id="fightBtn" onClick="doAction(self,'fight')" image="ICON_SWORD">Fight (1)</Button>
      <Button id="restBtn" onClick="doAction(self,'rest')" image="ICON_BED">Rest (1)</Button>
      <Button id="cleanseBtn" onClick="doAction(self,'cleanse')" image="ICON_PURIFY">Cleanse (1)</Button>
    </HorizontalLayout>
  </Panel>
  <Panel id="actionCubes" position="0 -80 0" width="600" height="40">
    <HorizontalLayout>
      <Image id="cube1" image="CUBE_FULL" />
      <Image id="cube2" image="CUBE_FULL" />
      <Image id="cube3" image="CUBE_FULL" />
    </HorizontalLayout>
  </Panel>
  ```
  Each click calls `doAction(self, name)` which:
  1. Validates the action is legal (resources, position, sub-phase).
  2. If illegal, dims the button via `UI.setAttribute("xxxBtn", "interactable", "false")` and posts the "why" tooltip.
  3. If legal, opens the confirm-spend dialog (G.6).
- **Done-when.** Action Bar correctly enables/disables based on game state. Test each button per character / per location; legal/illegal states match design.

## G.4 Implement Action Cube animation

- **What.** Cubes deplete from full → spent visually as actions are taken; auto-reset at next Day.
- **How.** `setActionCubes(color, n)` updates the 3 `Image` elements: cube N+1 onward becomes `CUBE_SPENT`. On `BeginDay()` reset all to `CUBE_FULL`.
- **Done-when.** A 3-action turn visibly burns 3 cubes; next day shows 3 fresh cubes.

## G.5 Stat sliders with threshold shading

- **What.** Per-board +/− buttons for Health/Hunger/Sanity ([Design §10.2](StarveNoMoreDesignConcept.md)) with the <3 threshold zone shaded.
- **How.** XML for each stat row: −, current value, +, current cap, with a horizontal `ProgressBar` whose first 3 cells render in red. Clicking +/− calls `modStat(self, "H", ±1)` which updates `gameState.activeChars[color].health`, moves the marker token via `setPositionSmooth`, and broadcasts the change.
- **Done-when.** All three stats update on click. Threshold zone visibly red. Damage broadcasts in chat.

## G.6 Confirm-before-spend dialogs

- **What.** Modal confirmation for every action that consumes resources ([Design §18.14](StarveNoMoreDesignConcept.md)).
- **How.** A reusable `showConfirm(title, costStr, onConfirm)` function. It populates a hidden modal `<Panel id="confirmDialog">` with the action name + cost + current resources, sets visibility to active player only, and on click resolves the callback. Cancel hides the dialog.
- **Done-when.** Crafting, cooking, cleansing, and revival all show a confirm dialog before committing resources. Clicking ✗ reliably cancels with no state change.

## G.7 Tooltips on every interactable

- **What.** Hover descriptions on every clickable object ([Design §18.14](StarveNoMoreDesignConcept.md)).
- **How.** Lua sweep at end of setup: for each tagged object, call `obj.setDescription(tooltipsTable[obj.tag])`. The `tooltipsTable` is loaded from `content/cards.xlsx` Tooltips tab (A.3). Set `Tooltip = true` on every interactable.
- **Done-when.** Hovering any non-decorative object shows the right rule text. Sample test: hover the Doom marker → it reads current Doom value and next threshold.

## G.8 Chat broadcast log with color coding

- **What.** Every state change broadcasts to chat with the right color ([Design §18.14](StarveNoMoreDesignConcept.md)).
- **How.** A `broadcastEvent(category, message)` helper that maps:
  - `damage` → red `{1, 0.4, 0.4}`
  - `warn` → yellow `{1, 0.85, 0.4}`
  - `gain` → green `{0.5, 1, 0.5}`
  - `phase` → cyan `{0.5, 0.9, 1}`
  - `proc` → gray `{0.7, 0.7, 0.7}`
  Replace every `print` and `broadcastToAll` in F.* with calls to `broadcastEvent`.
- **Done-when.** A scripted full-day playthrough fills chat with appropriately-colored events. No raw `print` calls remain in player-facing paths.

## G.9 Glow border on active hand zone

- **What.** A visible colored glow on whose-turn-it-is hand zone (channel 2 of G.2).
- **How.** Already wired in G.2 step 2; this is the polish task. Verify color values are saturated enough to read against the table backdrop. Add a brief 0.5s pulse animation at turn change.
- **Done-when.** Visual is unmistakable from across the table.

## G.10 The central control panel (host buttons)

- **What.** Host-only buttons: Begin Day / Resolve Night / End Tick / Restart / Setup ([Design §18.11](StarveNoMoreDesignConcept.md) implies these but we add explicit affordance).
- **How.** XML Panel restricted to `visibility="Black|<host_color>"`. Each button calls the global function. Ensures non-host players cannot trigger phase advancement.
- **Done-when.** Buttons are visible only to host; they advance the game phases reliably.

---

# Phase H — UX Layer 2: onboarding (the path for first-time players)

After this phase, a never-played-before player can sit down, click Setup, and play their first round without anyone explaining anything. Builds [Design §18.16–18.17](StarveNoMoreDesignConcept.md).

## H.1 The Setup walkthrough

- **What.** The Setup button is replaced with a guided 4-step modal sequence ([Design §18.16](StarveNoMoreDesignConcept.md)).
- **How.** Replace the bare Setup() from F.3 with `SetupGuided()`:
  - **Step 1 — Pick path graph.** Modal with three preview-image buttons (Compact/Sprawl/Linear). On click: `activatePathVariant(name)`.
  - **Step 2 — Pick characters.** Each seated player gets a per-color modal showing all 5 characters as portraits with one-line strengths (text from `content/help/character_briefings.md`). Player clicks one. That character becomes unavailable for others. Continues until all seats picked.
  - **Step 3 — Briefing.** Per-player popup with `content/help/character_briefings.md` text. One [I understand] button dismisses it.
  - **Step 4 — Day 1.** Phase Banner takes over; "Reveal Dawn" highlighted.
- **Done-when.** A new player who has never seen the game can complete setup and reach Day 1 without help, in under 3 minutes.

## H.2 The character introduction popup

- **What.** A one-time per-player popup with the "you are X" briefing ([Design §18.16](StarveNoMoreDesignConcept.md)).
- **How.** This is Step 3 of H.1. The popup is a per-color modal Panel populated by Lua from `content/help/character_briefings.md`. After dismissal, store `gameState.activeChars[color].briefed = true` so it never re-shows.
- **Done-when.** Each new character pick shows the popup once. A reload mid-game does not re-trigger it.

## H.3 The Help menu side panel (5 tabs)

- **What.** A side panel opened by the ? button on the Phase Banner ([Design §18.17](StarveNoMoreDesignConcept.md)).
- **How.** XML side Panel anchored right side, 5 tabs:
  - **Quick Start** — content from `content/notebook/quickstart.md`.
  - **Your character** — dynamic, shows the active player's perks/constraints/suggested moves from `content/help/character_briefings.md` augmented with current state.
  - **Active Dawn** — pulls `gameState.activeDawn` and prints text + ongoing effects.
  - **Doom** — current value, next threshold, all thresholds and rules.
  - **Glossary** — content from `content/help/glossary.md` (icons and keywords).

  Tab switching is via XML `Toggle` group. Read-only; no game actions in this panel.
- **Done-when.** Pressing ? opens the panel. All 5 tabs render. Closing ? closes the panel cleanly. Help opens on top of game without blocking inputs.

## H.4 Implement the openHelp() handler

- **What.** Wire the ? button in the Phase Banner to the Help panel.
- **How.** Function `openHelp()` toggles the Help panel's `active` attribute. Refreshes the dynamic tabs (Your character, Active Dawn, Doom) at open time.
- **Done-when.** Help opens/closes reliably; dynamic tabs reflect current state on open.

## H.5 Implement the "What now?" hint

- **What.** A context-aware suggestion shown on click of the What-now button ([Design §18.17](StarveNoMoreDesignConcept.md)).
- **How.** Function `whatNow()`:
  1. Read current `gameState.subPhase`, `gameState.activeColor`, character state.
  2. Look up the matching hint string in `content/help/whatnow_hints.md` (loaded as a Lua table at setup).
  3. Substitute placeholders (`{name}`, `{actionsLeft}`, `{location}`, etc.).
  4. Display via a brief 5-second floating banner OR `printToColor` to the active player.
- **Done-when.** Pressing What-now during 5 different game states yields 5 different correct hints.

## H.6 Welcome sequence on first load

- **What.** A one-time chat message + camera tween ([Design §18.10](StarveNoMoreDesignConcept.md) onboarding).
- **How.** In `onLoad`, if `gameState.started == false` AND no `welcomed` flag: `broadcastToAll("Welcome to Starve No More. Click 'Setup Game' on the table to begin. Hover anything to see what it does. Press '?' anytime for help.", {0.9, 0.7, 0.3})`. Camera tweens to point at the Setup button via `Player.lookAt`. Set `gameState.welcomed = true`.
- **Done-when.** On a fresh load, the welcome appears and the camera highlights the Setup pedestal. On reload, it does not repeat.

## H.7 Tooltips on action buttons that explain why-disabled

- **What.** When an Action Bar button is dimmed, hovering it explains *why*.
- **How.** Function `disableActionButton(boardObj, action, reason)` sets the button's interactable to false AND sets its tooltip to the reason ("No Crockpot at this location — move to Ellie & Luca's House to cook"). On state change, recompute and refresh.
- **Done-when.** A test player gets a useful explanation for every dim button.

## H.8 Notebook tab population

- **What.** The TTS Notebook is populated as a fallback (per [Design §18.7](StarveNoMoreDesignConcept.md)).
- **How.** In `onLoad`: `Notes.setNotebookTabs({...})` from the markdown files in `content/notebook/`.
- **Done-when.** All three tabs are readable in the Notebook even with the Help panel closed.

---

# Phase I — UX Layer 3: feedback, mood, and safety nets

After this phase, the implementation matches the full UX vision: phase mood, end-of-round summary, severity legend, threshold ribbons, confirm-risky-actions, and fail-friendly defaults. Builds [Design §18.15, §18.18](StarveNoMoreDesignConcept.md).

## I.1 Verify the Severity Legend card placement and tooltip

- **What.** The card from B.7/E.19 is correctly placed and has a useful tooltip.
- **How.** Spot-check from a fresh save: legend is beside Threat deck, locked, has tooltip "Severity dot legend — see how punishing a card is at a glance."
- **Done-when.** A new player can find and read the legend within 5 seconds of looking at the table.

## I.2 Verify the Doom threshold ribbon

- **What.** The threshold rules baked into the board art (B.3) are legible.
- **How.** Test at default zoom level. If labels at 25/30 are not crisp, request a board art revision.
- **Done-when.** All five thresholds are readable at default zoom on 1080p.

## I.3 Phase-specific lighting transitions

- **What.** The visual environment subtly changes by phase ([Design §18.18](StarveNoMoreDesignConcept.md)).
- **How.** A `setPhaseMood(phaseName)` function that adjusts `Lighting.LightIntensity` and `Lighting.AmbientSkyColor`:
  - `Dawn`: brief 0.5s flash (intensity briefly ↑10%).
  - `Day`: baseline (set in D.3).
  - `Dusk`: ambient slightly cooler, intensity ↓5%.
  - `Night`: intensity ↓25%, ambient blue, 1-second smooth transition.
  - `Tick`: brief soft chime; baseline restored.
  Hooked to `gameState.subPhase` changes.
- **Done-when.** A full day's playthrough cycles the lighting through all 5 moods smoothly. Players can identify the phase from the lighting alone.

## I.4 The End-of-Round Summary panel

- **What.** A 6-second auto-dismissing panel after Tick ([Design §18.18](StarveNoMoreDesignConcept.md)).
- **How.** A modal Panel populated from a per-round event log Lua keeps in `gameState.dayLog`:
  ```
  End of Day {day} — {phaseName}
  - Doom: {prevDoom} → {newDoom}
  - Lost: {summary of damage}
  - Gained: {summary of crafts/discoveries}
  - Threats defeated: {list}
  Next: Day {day+1} Dawn — click Begin Day when ready.
  ```
  Panel auto-dismisses after 6s; can be dismissed manually with ✗. Reset `gameState.dayLog = {}` after dismissal.
- **Done-when.** Each Tick produces a correct summary. Test scenario: kill an enemy + cook + craft in one round → summary lists all three.

## I.5 Day log capture

- **What.** Every event broadcast in G.8 is also captured in `gameState.dayLog` for the I.4 summary.
- **How.** Modify `broadcastEvent(category, message)` to also push the event into `gameState.dayLog`.
- **Done-when.** I.4's summary correctly lists everything a player would have seen in chat.

## I.6 Safety-net confirmations on risky actions

- **What.** Second-confirm for irreversible / high-stakes actions ([Design §18.18](StarveNoMoreDesignConcept.md)).
- **How.** Wrap these handlers with a `showRiskyConfirm(title, body, onConfirm)`:
  - Ending Day Phase before all players have spent their actions.
  - Sleeping alone at a sport court (Dusk declaration handler).
  - Spending the last Telltale Heart (revival handler).
  - Moving an injured character into a high-threat zone at Dusk.
  The confirm displays the consequences plainly: "Sleep alone at the Badminton Court? You'll draw 1 extra Threat card and gain no regen. [Confirm] [Cancel]"
- **Done-when.** Each risky action triggers exactly one extra confirm. Cancelling reliably reverts.

## I.7 Fail-friendly defaults

- **What.** Edge cases the rules don't strictly cover are handled gracefully ([Design §18.18](StarveNoMoreDesignConcept.md)).
- **How.** Wrap every public action handler with a top-level `pcall`. On a Lua error: catch, broadcast in chat as `proc` color: "(Edge case — the rules don't strictly cover this. Continuing.)" and log full error to system console (`log()`). Never let an error leak as a red banner.
- **Done-when.** A deliberate error (e.g., calling a missing dispatch entry) produces a friendly chat note, not a script crash.

## I.8 Phase Banner "Next action" updates

- **What.** The `nextField` in G.1 dynamically reflects what the active player should do.
- **How.** A `recommendNext()` function called from `refreshPhaseBanner()`:
  - Sub-phase Dawn: "Click Reveal Dawn".
  - Sub-phase Day, active has actions: "Take an action ({n} left)".
  - Sub-phase Day, active no actions: "Click Pass to end your turn".
  - Sub-phase Dusk: "Declare your sleep location (click a tile)".
  - Sub-phase Night: "Click Resolve Night".
  - Sub-phase Tick: "End-of-round summary in progress…".
- **Done-when.** A new player following only the `nextField` text can complete a full round.

## I.9 Standee bob animation polish

- **What.** The active-player standee bob (G.2 channel 3) is gentle and not annoying.
- **How.** Tune the rotation amplitude and frequency. Default ±5° at 4-second period. Adjust if testers report distraction.
- **Done-when.** No tester complains about the bob.

## I.10 Hand zone glow color matching

- **What.** The G.2 channel-2 glow uses the player's seat color, not a generic highlight.
- **How.** `getColorTint()` queries the seat color from `Player[color]` and applies it. Test all 5 seats.
- **Done-when.** All 5 active states show distinguishable glows.

## I.11 Camera nudges at phase change

- **What.** Subtle camera attention at major moments.
- **How.** On Boss arrival: `Player.lookAt` for all clients to the boss standee briefly. On Dawn reveal of a ●●●●● severity card: same to the card. Use sparingly — overuse is jarring.
- **Done-when.** Boss arrivals and apocalyptic Dawns get a 2-second "everyone look at this" beat.

---

# Phase J — Performance, accessibility, polish

Final pass before publication.

## J.1 Object count audit

- **What.** Mid-game object count < 500 [TTS §11].
- **How.** `print(#getAllObjects())` in console mid-game. If higher: consolidate small tokens into Infinite Bags.
- **Done-when.** Mid-game count < 500.

## J.2 Texture memory audit

- **What.** No texture > 4096px; total mod < 250 MB.
- **How.** Inspect every URL. Resample anything over 4096px. Compress < 1024px assets.
- **Done-when.** Constraints met.

## J.3 First-load timing test

- **What.** Cold-cache load < 90s on 25 Mbps.
- **How.** Have a teammate clear their TTS Mods cache, load the published mod, time it.
- **Done-when.** Cold load < 90s. Warm < 10s.

## J.4 Multi-client hidden-info test

- **What.** Hidden info ([Design §18.9](StarveNoMoreDesignConcept.md)) actually hides.
- **How.** Host with a second client. Place a card in each hand zone in turn. Confirm from the other client. Confirm Phase deck top card hidden.
- **Done-when.** No information leak.

## J.5 Permission lockdown

- **What.** Restrict destructive permissions on critical objects.
- **How.** Right-click → Permissions on Main Board, Location Tiles, Doom Marker, Day Counter. Disable Delete and Spawn for non-host colors.
- **Done-when.** Non-host attempting to delete a critical object is blocked.

## J.6 Color-blind accessibility pass

- **What.** Resource and stat icons distinguishable in deutan/protan simulations.
- **How.** Run icons through CB simulators. If two are confusable, change silhouette.
- **Done-when.** Icons distinguishable by silhouette alone.

## J.7 Tooltip coverage audit

- **What.** Every interactable has a tooltip.
- **How.** Iterate `getAllObjects()`; flag any with `Tooltip = false` or empty `description`. Fix.
- **Done-when.** Zero interactables without tooltips.

## J.8 What-now hint coverage audit

- **What.** Every (sub-phase × character state) combination produces a useful hint.
- **How.** Brute-force test by walking through each sub-phase with each character state (full health, low health, Down, etc.). Note any hint that's missing or misleading.
- **Done-when.** All combinations produce a non-empty, helpful hint.

## J.9 Clean up debug output

- **What.** Remove dev `print` / `log` calls.
- **How.** Search across all scripts. Keep only error-path messages routed via `broadcastEvent`.
- **Done-when.** Clean playthrough produces only intentional player-facing chat output.

## J.10 First-time-load checklist

- **What.** First-load experience matches [Design §18.8](StarveNoMoreDesignConcept.md) + §18.16 walkthrough.
- **How.** Fresh-cache load test:
  - All assets cached, no broken images.
  - Welcome chat message appears.
  - Setup Game button is highlighted.
  - Help (?) button is visible.
- **Done-when.** All bullets verified.

## J.11 Pretty-print and commit the final save

- **What.** Reviewable, version-controlled save.
- **How.** `jq . StarveNoMore.json > StarveNoMore.pretty.json`. Diff against previous. Commit.
- **Done-when.** Pretty save committed.

---

# Phase K — Playtest, publish, iterate

The mod ships, then improves.

## K.1 Closed alpha (designer + 2)

- **What.** A 1-day playtest with the designer and two volunteers. **Critical: at least one volunteer has not read the design doc.**
- **How.** Run a Long Weekend variant first. The unread volunteer is the canary for the "playable without rules" goal: they sit down, click Setup, and play.
- **Done-when.** A bug list, a usability list, and an unread-volunteer report are written.

## K.2 Fix the unread-volunteer's confusion points

- **What.** Anywhere the canary said "I didn't know what to do" gets a UX fix.
- **How.** Each confusion → identify which UX layer should have prevented it (G/H/I) → patch.
- **Done-when.** A second canary playthrough has zero "I didn't know" moments.

## K.3 Fix critical bugs

- **What.** Address show-stoppers from K.1.
- **How.** Minimal repro → fix → re-test.
- **Done-when.** No script error fires during a clean Long Weekend playthrough.

## K.4 Open beta (3- and 5-player tests)

- **What.** Wider playtest with 3- and 5-player groups.
- **How.** Recruit two groups: 3 players, 5 players. Each runs a Standard 7-day game. Designer observes silently (Spectator).
- **Done-when.** Win rate at 3 ≈ win rate at 5 (within 15%). Onboarding works at both player counts.

## K.5 Publish to Steam Workshop

- **What.** Public release.
- **How.** *Games → Save & Load → Steam Workshop → Upload*. Title: "Starve No More". Description from [Design §1.1](StarveNoMoreDesignConcept.md). Tags: `Card Games`, `Strategy`, `Cooperative`, `Survival`. 512×512 thumbnail. Mark "Mod Caching".
- **Done-when.** Mod listed; subscriber's fresh download loads cleanly.

## K.6 Ship companion saves

- **What.** Two shareable saves alongside the Workshop entry.
- **How.**
  - `StarveNoMore_Setup.json` — pristine starting state.
  - `StarveNoMore_MidGame.json` — Day 4 state for tutorial purposes.
- **Done-when.** Both saves load without errors.

## K.7 Set up a feedback channel

- **What.** Bug-report and feedback channel attached to the Workshop page.
- **How.** Link to Discord, GitHub issues, or BoardGameGeek thread in the Workshop description. Triage weekly.
- **Done-when.** Channel live; first triage scheduled.

## K.8 Iterate

- **What.** Monthly patches based on feedback.
- **How.** Bugs first, balance second, features only when core is stable. Update mod and design doc together.
- **Done-when.** Continuous — post-launch lifecycle.

---

# Appendix A — Recommended folder layout

```
repo/
├── StarveNoMoreDesignConcept.md
├── StarveNoMoreRequirements.md
├── Checklist_For_TTS_Implementation.md         <-- this file
├── docs/
│   ├── HowToCreateGamesInTabletopSimulator.md
│   ├── PrinciplesOfGoodBoardGames.md
│   ├── DontStarveVideoGamePrinciples.md
│   └── InterestingGames.md
├── content/
│   ├── cards.xlsx                              <-- A.2
│   ├── iconography.md                          <-- A.4
│   ├── asset_manifest.md                       <-- A.5
│   ├── notebook/
│   │   ├── quickstart.md                       <-- A.6
│   │   ├── full_rules.md
│   │   └── character_reference.md
│   └── help/
│       ├── glossary.md                         <-- A.6
│       ├── character_briefings.md              <-- A.6
│       └── whatnow_hints.md                    <-- A.6
├── art/
│   ├── icons/                                  <-- B.2
│   ├── board/                                  <-- B.3
│   ├── tiles/                                  <-- B.4
│   ├── characters/                             <-- B.5
│   ├── decks/                                  <-- B.6
│   ├── legend/                                 <-- B.7
│   ├── tokens/                                 <-- B.8
│   ├── bosses/                                 <-- B.9
│   └── ui/                                     <-- B.11
├── lua/
│   ├── global.lua
│   ├── assets.lua                              <-- C.3
│   ├── setup.lua
│   ├── day_loop.lua
│   ├── combat.lua
│   ├── crafting.lua
│   ├── night.lua
│   ├── victory.lua
│   ├── ui_banner.lua                           <-- G.1, G.2
│   ├── ui_actionbar.lua                        <-- G.3, G.4
│   ├── ui_help.lua                             <-- H.3, H.4
│   ├── ui_whatnow.lua                          <-- H.5
│   ├── ui_summary.lua                          <-- I.4
│   ├── effects/
│   │   ├── dawn_effects.lua                    <-- F.5
│   │   └── threat_effects.lua                  <-- F.9
│   └── helpers.lua
├── xml/
│   ├── phase_banner.xml                        <-- G.1
│   ├── action_bar.xml                          <-- G.3
│   ├── help_panel.xml                          <-- H.3
│   └── confirm_dialog.xml                      <-- G.6
└── saves/
    ├── StarveNoMore.json
    ├── StarveNoMore.pretty.json                <-- E.21
    └── StarveNoMore_MidGame.json               <-- K.6
```

---

# Appendix B — Critical-path checklist (the minimum viable mod)

If schedule pressure forces a cut, the following are the only-must-do tasks. Everything else can ship in a v0.5 patch. **Note:** the UX program is *not* a polish-layer cut; it is what makes the game playable on first sit-down. Do not skip Phase G.

1. A.1, A.2, A.3, A.4, A.6 — design lock + content + iconography + help text.
2. B.1, B.2, B.3, B.4, B.5, B.6, B.7 — placeholder-acceptable art for board, tiles, characters, decks, icons, severity legend.
3. C.1, C.2, C.3 — assets hosted and addressable.
4. D.1, D.2, D.4 — empty save with table and hand zones.
5. E.1, E.3, E.6, E.7, E.8, E.9, E.11, E.14, E.15, E.16, E.18, E.19 — components incl. Severity Legend.
6. F.1, F.3, F.4, F.6, F.10, F.14 — global, setup, day advance, tick, victory, save/load.
7. **G.1, G.2, G.3, G.5, G.6, G.7, G.8** — Phase Banner, active player indicator, Action Bar, stat sliders, confirm dialogs, tooltips, chat broadcasts. *All G tasks are critical-path.*
8. **H.1, H.2, H.3, H.5, H.6, H.7** — guided setup, character popup, Help menu, What-now hint, welcome, why-disabled tooltips. *All onboarding is critical-path.*
9. I.4, I.6, I.7, I.8 — End-of-round summary, risky-action confirms, fail-friendly defaults, Next-action banner field.
10. J.7, J.8, J.10 — tooltip coverage, hint coverage, first-load checklist.
11. K.1, K.2, K.5 — closed alpha (with unread canary), fix the canary's confusion, publish.

The non-critical items (severity-legend polish, ribbon legibility nice-to-haves, phase mood lighting, camera nudges, color-blind audit, performance audits beyond a quick spot-check) can ship in patches.

---

# Appendix C — UX acceptance test (the canary protocol)

Before declaring the mod ready, run this test:

1. Recruit a tester who has not played Starve No More and has not read the design doc.
2. Sit them at the TTS table. Tell them only: "Click Setup Game and figure it out. I'll watch silently."
3. Time how long until they take their first **legal, intentional** action.
4. Note every moment they ask "what should I click?" or "what does this mean?"

**Pass criterion:** First legal action within 90 seconds. Fewer than 3 confusion moments in the first round.

If the test fails, the failed UX moments are the priority backlog. Do not publish until the canary passes.

---

*End of build plan. Treat this checklist as the contract from "design brief" to "playable mod on Workshop." The UX program (G/H/I) is what turns a working mod into a playable game.*
