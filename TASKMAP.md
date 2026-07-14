# TASKMAP — job → files to open

The routing table for "which file do I touch?". Find your job, open **only** the
listed files. For "where is function X?" use [`SYMBOLS.md`](SYMBOLS.md) instead
(function → `file:line`). Deep reference: [`agents.md`](agents.md).

Anything under `content/` that feeds a generated `lua/*.lua` needs a regenerate
step — see the **Regenerate** column and [`scripts/CLAUDE.md`](scripts/CLAUDE.md).

| Job | Open | Regenerate after |
|---|---|---|
| Change a card's stats/text | `content/cards_*.csv` | `generate_card_atlases.py` (art); `generate_market_data.py`/`generate_threat_types.py`/`generate_recipe_data.py` if it's a market/threat/recipe card |
| Add/adjust a player action | `lua/actions.lua` + `lua/ui_actionbar*.lua` | `generate_symbol_index.py` |
| Change combat math | `lua/combat.lua` | `generate_symbol_index.py`; mirror constants in `scripts/simulate_balance.py` |
| Change a Dawn event | `lua/effects/dawn_effects*.lua` + `content/cards_phase*.csv` | `generate_symbol_index.py` |
| Change the day/night flow | `lua/day_loop.lua`, `lua/night.lua` | `generate_symbol_index.py` |
| Change victory/defeat | `lua/tick_victory.lua` | `generate_symbol_index.py`; mirror in `scripts/simulate_balance.py` |
| Change in-game rules text | `content/notebook/*.md` + `content/help/*.md` | `generate_notebook.py`, `generate_player_rules.py` |
| Change a UI panel | matching `lua/ui_*.lua` + `xml/*.xml` | `generate_symbol_index.py` |
| Rebalance | `scripts/simulate_balance.py`, `content/cards_*.csv` | rerun sim both rulesets; update `test_sim.py` bands |
| Add/adjust a Signature Move | `lua/signatures.lua` | `generate_symbol_index.py` |
| Change crafting/cooking | `lua/crafting.lua`, `content/cards_recipes.csv` | `generate_recipe_data.py`, `generate_symbol_index.py` |
| Change a boss arrival/beat | `lua/effects/dawn_effects*.lua`, `lua/combat.lua`, `lua/treeguard.lua` | `generate_symbol_index.py` |
| Add/change a sound | `sounds/...` | `generate_audio_manifest.py` |
| Change setup/character assignment | `lua/setup.lua`, `lua/ui_setup.lua`, `xml/setup.xml` | `generate_symbol_index.py` |
| Change what gets packaged in the save | `scripts/build_save.py` | `build_save.py` |

**Always finish with:** `python scripts/build_save.py` then `python -m pytest tests`.
A stale generated file (or a Lua move without a fresh `SYMBOLS.md`) fails the suite.
