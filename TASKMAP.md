# TASKMAP — job → files to open

The routing table for "which file do I touch?". Find your job, open **only** the
listed files. For "where is function X?" use [`SYMBOLS.md`](SYMBOLS.md) instead
(function → `file:line`). Deep reference: [`docs/agents/`](docs/agents/README.md)
(one topic per file), indexed from [`agents.md`](agents.md).

Anything under `content/` that feeds a generated `lua/*.lua` needs a regenerate
step — see the **Regenerate** column and [`scripts/CLAUDE.md`](scripts/CLAUDE.md).

| Job | Open | Regenerate after |
|---|---|---|
| Change a card's stats/text | `content/cards_*.csv` | `generate_card_atlases.py` (art); `generate_market_data.py`/`generate_threat_types.py`/`generate_recipe_data.py` if it's a market/threat/recipe card |
| Add/adjust a player action | `lua/actions.lua` + `lua/ui_actionbar*.lua` | `generate_symbol_index.py` |
| Change combat math | `lua/combat.lua` | `generate_symbol_index.py`; mirror constants in `scripts/simulate_balance.py` |
| Change a Dawn event | `lua/effects/dawn_effects*.lua` + `content/cards_phase*.csv` | `generate_symbol_index.py` |
| Change the day/night flow | `lua/day_loop.lua`, `lua/night.lua` | `generate_symbol_index.py` |
| Change what a threat card DOES | Soft: `lua/threat_effects.lua`; Persistent: `lua/threat_persistent.lua`; Hard riders: `lua/threat_hard.lua`; the type lookup itself: `identifyThreatType` in `lua/night.lua` | `generate_threat_types.py`, `generate_symbol_index.py` |
| Change victory/defeat | `lua/tick_victory.lua` | `generate_symbol_index.py`; mirror in `scripts/simulate_balance.py` |
| Add/change an achievement | `content/achievements.csv` + `lua/achievement_rules.lua` (read [`docs/achievements.md`](docs/achievements.md)) | `generate_achievement_data.py`, `generate_achievement_icons.py`, `generate_symbol_index.py` |
| Regenerate the achievement art | [`docs/comfyui-achievement-icons.md`](docs/comfyui-achievement-icons.md) | `generate_achievement_icons.py` |
| Change in-game rules text | `content/notebook/*.md` + `content/help/*.md` | `generate_notebook.py`, `generate_player_rules.py` |
| Add/change a What-now hint | `content/help/whatnow_hints.md` **and** its condition in `onWhatNowClick` (`lua/ui_help.lua`) — an unreached hint fails `test_whatnow_hints.py` | `generate_whatnow_hints.py`, `generate_symbol_index.py` |
| Change the in-game Rulebook tab / Help paging | `lua/ui_help_pages.lua` + `lua/ui_help.lua` + `xml/dialogs.xml` | `generate_symbol_index.py` |
| Add an off-turn (reaction) action | `lua/ui_reactions.lua` + `xml/hud.xml` | `generate_symbol_index.py` |
| Change a UI panel | matching `lua/ui_*.lua` + `xml/*.xml` | `generate_symbol_index.py` |
| Change a Scenario (the week-long twist) | `lua/setup.lua` (`SCENARIOS`) + the verb each flag names; every flag needs a reader or `test_lua_effect_flags.py` fails | `generate_symbol_index.py` |
| Rebalance | `scripts/simulate_balance.py`, `content/cards_*.csv` | rerun sim both rulesets; update `test_sim.py` bands |
| Add/adjust a Signature Move | `lua/signatures.lua` | `generate_symbol_index.py` |
| Change crafting/cooking | `lua/crafting.lua`, `content/cards_recipes.csv` | `generate_recipe_data.py`, `generate_symbol_index.py` |
| Change a boss arrival/beat | `lua/effects/dawn_effects*.lua`, `lua/combat.lua`, `lua/treeguard.lua` | `generate_symbol_index.py` |
| Change a boss Trophy power | `lua/trophies.lua` + `content/cards_trophies.csv` | `generate_symbol_index.py` |
| Change a location's special/yield/defence | `lua/global.lua` (`LOCATION_YIELDS`, `LOCATION_DEFENSE`) + the verb that reads it (`lua/actions.lua`, `lua/combat_resolve.lua`) + `content/locations.csv` | `generate_symbol_index.py` |
| Add/change a sound | `sounds/...` | `generate_audio_manifest.py` |
| Change setup/character assignment | `lua/setup.lua`, `lua/ui_setup.lua`, `xml/setup.xml` | `generate_symbol_index.py` |
| Change turn order / action economy / idle nudge | `lua/turns.lua` | `generate_symbol_index.py` |
| Add/rename/find a `gameState` field | [`docs/gamestate.md`](docs/gamestate.md) (who writes it, who reads it, its default), then `lua/global.lua` (`migrateGameState` — declare the default there, not in a literal) | `generate_gamestate_map.py` |
| Change what gets packaged in the save | `scripts/build_save.py` | `build_save.py` |
| Place/move an object on the table (heights, rotations) | `scripts/build_save.py` (`SURFACE_Y`) + read [`docs/tts-runtime.md`](docs/tts-runtime.md) first | `build_save.py` |
| Change the Message Log / What-now panel | `lua/ui_msglog.lua`, `lua/ui_help.lua`, `xml/msglog.xml` | `generate_symbol_index.py` |
| Debug a live session / decode a `<Global:N>` error | [`docs/debugging.md`](docs/debugging.md) + `scripts/inspect_save.py` | — |
| Deploy to TTS for play | `iwanttoplay` (regen+build+test+install+cache purge+launch) | — |

**Always finish with:** `python scripts/check.py`. It runs every generator in the
**Regenerate after** column for you, rebuilds the save, runs the suite and lints
the Lua — so you never have to match your edit to the right generator by hand.

Run a single stage only when you are debugging that stage:
`python scripts/regenerate_all.py`, `python scripts/build_save.py`,
`python -m pytest tests`. A stale generated file (or a Lua move without a fresh
`SYMBOLS.md`) fails the suite either way.
