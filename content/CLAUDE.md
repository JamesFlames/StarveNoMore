# content/ — in-game text & card data

The source of truth for cards, rules text, hints, and audio metadata. Most files
here **feed a generated `lua/*.lua` table** — editing them without rerunning the
matching generator leaves the game out of sync (and fails a freshness test).

## Regenerate after editing

| Edit | Run |
|---|---|
| `cards_market.csv` / `cards_starting.csv` | `generate_market_data.py` |
| `cards_threats.csv` | `generate_threat_types.py` |
| `cards_recipes.csv` | `generate_recipe_data.py` |
| `notebook/*.md`, `help/glossary.md` | `generate_notebook.py` + `generate_player_rules.py` |
| `help/whatnow_hints.md` | `generate_whatnow_hints.py` |
| `help/character_briefings.md` | `generate_character_briefings.py` |
| any `cards_*.csv` (art/text) | `generate_card_atlases.py` |
| `achievements.csv` | `generate_achievement_data.py` + `generate_achievement_icons.py` |

**Or just run `python scripts/check.py`** — it runs every generator above, in
dependency order, then rebuilds and tests. The table is what to run when you are
debugging one generator; `check.py` is what to run when you are finishing a task.
Generator map: [`../scripts/CLAUDE.md`](../scripts/CLAUDE.md).

## Conventions

- CSV schemas are enforced by `tests/test_csv_schema.py` (required columns,
  unique ids, stat ranges). Card ids are prefixed by deck (`P1_`, `M_`, `T_`, …).
- `iconography.md` is authoritative for icon meaning; `asset_manifest.md` drives
  `lua/assets.lua`. Deep reference: [`../docs/agents/`](../docs/agents/README.md).
