# UX Affordances

The rule that the next legal action is always visible, and the surfaces that implement it.

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

The design's stated UX goal (§18.10) is "playable on first sit-down without
reading the rulebook." The implementation layers six signals so the active
player never has to ask "what now?":

## 1. Phase Banner — text + pulse
- `lua/ui_banner.lua` `recommendNext()` writes a one-line "next thing to do" string into the banner every state change.
- `highlightCTA(ids)` pulses an outline around the actual XML control to click. Mapping (`getNextCTA()`):
  - PreGame → `btnSetup`
  - Day, has actions → `actionBar` panel
  - Day, no actions → `actPass`
  - Tick / PreDawn (between days) → `btnBeginDay`
  - Dusk → `btnResolveNight` (ends the scramble window and begins Night)
  - Night → `btnResolveNight`
  - GameOver → `btnRestart`

## 1b. Always-visible character roster + live standee tooltips
- `xml/hud.xml` `charRoster` panel (MiddleRight) shows every character's current Health / Hunger / Sanity as compact bars + numeric values. Each name uses that character's color (James blue / Coco white / Rayman green / Ellie yellow / Luca red).
- `lua/ui_banner.lua` `refreshCharRoster()` (called from `refreshPhaseBanner`) updates the bars, dims rows for Down characters, and hides rows for characters not in the current game.
- `lua/ui_banner.lua` `refreshStandeeTooltips()` rewrites each character standee's `Description` on every state change so hovering a standee shows live `Health/Hunger/Sanity • At <Location>` (or the revival hint if Down).
- `scripts/build_save.py` `STANDEE_COLORS` tints each character's `Figurine_Custom` `ColorDiffuse` so the card holders match the roster naming (James blue, Coco white, Rayman green, Ellie yellow, Luca red).
- **A player's seat colour is determined by the character they pick** (`CHARACTER_COLORS`, global.lua — mirrored by `STANDEE_COLORS`): the guided setup's `reseatPlayerForCharacter` (ui_setup.lua) moves each player onto their character's colour at pick time (anyone parked there is shifted to a spare seat); the bare `Setup()` assigns characters by the same colour scheme.

## 2. What-now hints — auto-loaded from markdown
- `content/help/whatnow_hints.md` is the **source of truth**. `scripts/generate_whatnow_hints.py` parses it into `lua/whatnow_hints.lua` (the `WHATNOW_HINTS` table).
- Group keys: `PreGame`, `Dawn`, `Day`, `Dusk`, `Night`, `Tick`, `PostGame`, `Stats`, `James`, `Coco`, `Rayman`, `Ellie`, `Luca`, `Location`, `Strategic`.
- Dispatch in `lua/ui_help.lua` `onWhatNowClick()` composes a multi-line hint by stacking: phase-base + char-specific + stat warnings + strategic + location.
- Adding a hint: edit the markdown, run `python scripts/generate_whatnow_hints.py`, rebuild.

## 3. Action targets — highlights + click-to-complete buttons
- When the active player clicks an action button, `lua/ui_actionbar_targets.lua` highlights world objects via `obj.highlightOn(color, 8)` AND spawns a clickable 3D `createButton` on every legal target. Clicking the button consumes `gameState.pendingAction` and calls the matching `do*` handler:
  - **Move** → adjacent tiles glow Green with a MOVE HERE button → `doMove`. Rayman's Speed perk chains a second round of FREE MOVE buttons (`doRaymanBonusMove`).
  - **Craft** → Market deck + slots glow Yellow, **affordable** cards Green (see §4); each displayed card gets a CRAFT button → `doCraft(color, slotIndex)`.
  - **Cook** → Recipe cards glow Orange with a COOK button → `doCook(color, recipeId)` (recipe id read from the card's `R_*` tag).
  - **Fight** → fightable threats/bosses at the tile glow Red with FIGHT (and, when fed allies share the tile, TOGETHER) buttons → `doFightTarget(color, obj, together)`.
  - **Peek** (James) / **Rally** (Luca) → per-character bar buttons open the `peekDialog` / `rallyDialog` pickers → `doPeek` / `doRally`.
  - **Cleanse** → required resource bags glow White (confirm dialog, no world button).
  - **Trade** → `tradeDialog` XML panel listing valid partners with the free/1-action cost per row → `doTrade`.
  - **Undo** → `doUndo` (snapshot taken in `spendAction`; also restores `raymanMovedToday`/`raymanBonusMove`; cleared at turn end).
- Target buttons are cleared on completion, on cancel (click the same action button again), at turn end (`endPlayerTurn`/`beginDusk` call `clearActionTargets()`), or after a 30 s timeout.

## 4. Market affordability
- `lua/market_data.lua` (auto-loaded) defines `MARKET_COSTS[<id>] = {Wood=2, Metal=1, ...}` for every Market card.
- `getPlayerResources(color)` in `lua/ui_actionbar_core.lua` reads the authoritative held count from `gameState.resources[color]` (see "Held resources are virtual" above) — position-independent.
- `canAfford(color, cardId)` compares. Affordable Market cards get a Green highlight when Craft is selected, plus a `printToColor` summary of the player's bag contents.

## 5. Auto-broadcast urgent hints
- `gameState.dailyAlerts[color]` flags so each urgent broadcast fires only once per character per day; cleared in `BeginDay()`.
- Triggers:
  - Character goes Down → `tick_victory.lua` `checkDownState` broadcasts the Telltale-Heart cook recipe.
  - James end-of-Day with no Energy Drink consumed → `day_loop.lua` `beginDusk` reminds him before Tick.
  - Dusk per-player warnings (alone at sport court, Coco alone non-house, public Charlie reminder) — also in `beginDusk`.

## 6. Idle nudge
- `turns.lua` runs an idle watcher during the `Day` sub-phase: every 10s it checks `os.time() - gameState.lastInteractionAt`.
- After 45s of inactivity, the active player is `printToColor`'d a "click What next?" prompt — once per turn (`gameState.idleNudgedThisTurn`).
- `noteInteraction()` is called from `validateActivePlayer()` so any action click resets the timer.

## 6b. Dawn-card manual-steps checklist
- `DAWN_MANUAL_STEPS` (effects/dawn_effects.lua) lists the physical/manual steps for every Dawn card the script can't fully resolve (token moves, group choices, deck searches). `dispatchDawnEffect` copies them into `gameState.dawnChecklist`.
- `refreshDawnChecklist` (ui_rules.lua) renders them as tickable rows in the `dawnChecklist` XML panel (top right, max 4 rows); any player clicks to tick; the panel hides itself when all are done. Outstanding steps also appear as "DAWN CARD TO-DO" lines in the Rules panel.
- When adding a Dawn card with a manual instruction, add its steps to `DAWN_MANUAL_STEPS` — fully scripted cards stay out of the table.

## 7. "Rules in effect" panel + day-cycle strip
- `lua/ui_rules.lua`, refreshed from `refreshPhaseBanner()` on every state change. Broadcasts scroll away; this panel mirrors every rule *currently* modifying play into a persistent left-side panel (`rulesPanel` in the XML, collapsible):
  - current sub-phase rules (one line, `SUBPHASE_RULES`),
  - crossed Doom thresholds (`DOOM_THRESHOLD_RULES`),
  - ongoing Dawn-card effects (`EFFECT_RULES` maps every `gameState.ongoingDawnEffects` flag to player-readable text; add a label here whenever `dawn_effects.lua` gains a new ongoing flag),
  - Treeguard status, and per-character statuses (Down / Haunted / can't-Fight / injured / Charlie streak / James Wired pending / Rayman Loud).
- `refreshCycleStrip()` renders `Dawn ▸ Day ▸ Dusk ▸ Night ▸ Tick` under the Phase Banner (`cycleStrip`) with the current step lit, so players always see where they are in the loop.
- The `PreDawn` sub-phase (between Tick and the next Begin Day) is fully wired: banner text, `btnBeginDay` CTA pulse, and a `between_days` What-now hint (Tick group in `whatnow_hints.md`).

## 8. Message Log — nothing said is ever lost
- TTS broadcasts fade in seconds and render behind the Phase Banner, so `broadcastEvent` (global.lua) also appends every public message to `gameState.messageLog` (persists through save/load, capped at 40).
- `lua/ui_msglog.lua` renders the newest entries in the draggable `msgLog` panel (xml/msglog.xml), colour-coded by category; Clear/Hide buttons on the panel, "Log" toggle on the banner. What-now hints open the per-player `whatNowPanel` (visibility set to the asking player's colour) with a "Got it" dismiss.
