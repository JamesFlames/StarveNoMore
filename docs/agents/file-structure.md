# File Structure

The repo tree, annotated — what lives where and which files are generated.

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

```
StarveNoMore/
├── lua/
│   ├── helpers.lua             # Utility functions (safecall, tag-based getters)
│   ├── global.lua              # gameState, lifecycle, onLoad/onSave, dailyAlerts
│   ├── audio_manifest.lua      # AUTO-GENERATED — track URLs + durations (AUDIO table)
│   ├── audio.lua               # Audio.startDayAmbience / playBossLoop / playChime / playWalk / playMeet / playTradeChat / playDeath / playSFX
│   ├── whatnow_hints.lua       # AUTO-GENERATED — WHATNOW_HINTS table from markdown
│   ├── market_data.lua         # AUTO-GENERATED — MARKET_COSTS + WEAPON_DICE from cards_market.csv + cards_starting.csv
│   ├── threat_types.lua        # AUTO-GENERATED — THREAT_TYPE_BY_NAME + SEALED_REWARDS from cards_threats.csv
│   ├── recipe_data.lua         # AUTO-GENERATED — RECIPE_DATA from cards_recipes.csv (script column)
│   ├── notebook_data.lua       # AUTO-GENERATED — Notebook/Help text from content/notebook/*.md + glossary.md
│   ├── setup.lua               # Bare gameplay setup (deals/shuffles/places)
│   ├── day_loop.lua            # Day lifecycle: Dawn advance (Doom/fester/reveal), Dusk, Night trigger
│   ├── turns.lua               # Turn engine: beginDayPhase, advanceToNextPlayer, endPlayerTurn, spendAction, dusk ready-check, idle nudge
│   ├── effects/
│   │   ├── dawn_effects.lua           # Core: DAWN_EFFECTS table + shared helpers + boss standee placement
│   │   ├── dawn_effects_phase1..4.lua # Per-phase Dawn card effects (add to DAWN_EFFECTS)
│   │   └── dawn_effects_dispatch.lua  # Anti-stacking cards + DAWN_MANUAL_STEPS + dispatchDawnEffect
│   ├── combat.lua              # Dice roll + boss/Source HP lifecycle + rewards/trophies (SOURCE_MAX_HP etc.)
│   ├── combat_resolve.lua      # Fight resolution flow (beginCombat..finishCombat, Charlie); calls Audio.stopBossLoop on defeat
│   ├── crafting.lua            # Market craft + Crockpot cook handlers
│   ├── threat_effects.lua      # Soft threats: printed effect + discard (SOFT_THREAT_EFFECTS/MANUAL_SOFT)
│   ├── threat_persistent.lua   # Persistent threats: PERSISTENT_THREAT_RULES, per-tile effect hooks, the Clear verb
│   ├── night.lua               # Night-phase resolver (threat draw, Charlie, sleep)
│   ├── tick_victory.lua        # Tick decay, victory/defeat, Down state + revival hint
│   ├── actions.lua             # Player actions core: undo/snapshot, move, dusk-move, gather, rest
│   ├── actions_combat.lua      # Combat verbs: threat/boss statlines, fight, flee
│   ├── actions_social.lua      # Trade, energy drink, eat-raw, pass, barricade, defend, peek, rally, pry, stabilize
│   ├── treeguard.lua           # Phase 2.5 mini-boss (wakes Dusk D4; fight/appease/defeat)
│   ├── signatures.lua          # Signature Moves (§6.7) — once-per-game per-character actions + button/dialog UX
│   ├── telemetry.lua           # Session log (batch 4 W0): chronicle setup/turns/beats, exportSessionLog, Copy Session Log
│   ├── ui_banner.lua           # Phase Banner + recommendNext + CTA pulse + active-player indicator
│   ├── ui_actionbar_core.lua      # Resource helpers (getPlayerResources, verifyAndPayResources, canAfford) + Move adjacency + highlight duration
│   ├── ui_actionbar_targets.lua   # Target-button plumbing + move/craft/cook/fight target spawns, click handlers, highlights
│   ├── ui_actionbar_handlers.lua  # onActX action-bar handlers, Press-the-Attack panel, trade/peek/rally/undo/dusk handlers
│   ├── ui_actionbar_situational.lua # Situational verbs: Revive, Stabilize, Defend, Energy Drink, Eat Raw, Barricade, Appease, Clear (+ canX preconditions); Ghost Drift rides ui_reactions
│   ├── ui_actionbar_display.lua   # Validate, action-bar refresh + cubes, per-button enable/reasons, stat display, action tooltips
│   ├── ui_controls.lua         # Host controls (contextual — only valid buttons show), confirm dialogs, tooltips
│   ├── ui_setup.lua            # Guided setup walkthrough (path → variants → characters → briefing) + welcome
│   ├── ui_help.lua             # Help panel tabs + What-now dispatch (fills the whatNowPanel)
│   ├── ui_msglog.lua           # Persistent Message Log panel (fed by broadcastEvent)
│   ├── ui_rules.lua            # "Rules in effect" panel + day-cycle strip
│   ├── ui_mood.lua             # Phase lighting presets, safety-net confirms, camera nudges
│   ├── audit.lua               # auditTooltips / auditHintCoverage / auditFirstLoad
│   ├── selftest.lua            # runSelfTest() — scripted in-TTS smoke test (see Test Suite)
│   └── assets.lua              # ASSETS table — image URL constants (LOCAL_DEV switch)
├── xml/
│   ├── hud.xml                 # Persistent HUD: banner, cycle strip, host controls, action bar, stats, roster
│   ├── setup.xml               # Guided setup walkthrough panels + character briefing
│   ├── dialogs.xml             # Modal dialogs: confirm / summary / week review / help / trade / combat / dusk
│   └── msglog.xml              # Message Log panel + per-player What-now panel
├── content/
│   ├── cards_phase1.csv ... cards_phase4.csv   # Dawn cards per phase
│   ├── cards_market.csv        # Source of truth for MARKET_COSTS
│   ├── cards_recipes.csv
│   ├── cards_threats.csv
│   ├── cards_visitors.csv
│   ├── cards_trophies.csv
│   ├── cards_scenarios.csv     # 8 optional week-long Scenarios (design §17.3) — applied digitally by setup.lua; no physical deck yet
│   ├── cards_starting.csv      # Per-character starting items (S_*) — dealt to hands by dealStartingHands at setup
│   ├── locations.csv
│   ├── resources.csv
│   ├── tooltips.csv
│   ├── iconography.md
│   ├── asset_manifest.md
│   ├── notebook/               # Quickstart + Full rules + Character reference
│   └── help/
│       ├── glossary.md         # Icon and keyword glossary (Help-menu tab)
│       ├── character_briefings.md  # Source of truth for CHAR_BRIEFINGS (setup popup)
│       └── whatnow_hints.md    # Source of truth for WHATNOW_HINTS
├── art/
│   ├── board/  tiles/  characters/  bosses/  decks/  icons/  ui/  legend/  tokens/
│   └── decks/illustrations/    # Per-card art from ComfyUI (sync target)
├── sounds/
│   ├── ambient/{suburban,varied}/   # Day-music tracks
│   ├── creatures/{bearger,deerclops,eye_of_terror,treeguard}/   # Boss roar libraries
│   └── sfx/tick_chime.wav      # Synthesized two-note bell
├── playtest/                   # Blind-playtest protocol (batch 4 W4): facilitator_script.md + feedback_form.md
│   └── sessions/               # Committed Copy-Session-Log exports; aggregate with scripts/analyze_sessions.py
├── saves/                      # Built TTS save JSON (StarveNoMore.json + .pretty.json)
│   └── fixtures/               # Frozen mid-game save (midgame_v1.json) for the save-compat test
├── scripts/                    # Build + asset/data generation (Python) + simulate_balance.py (Monte Carlo balance probe)
└── Archive/                    # Superseded reference docs (frozen — no live links)
```
