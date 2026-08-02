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

## CSV column dictionary

Every `content/*.csv`, its columns in file order, and its id prefix — so you
never have to open the CSV (or `tests/test_csv_schema.py`) just to learn what a
column is called. Columns in **bold** are required by the schema test; the rest
are optional. `art_notes` is the ComfyUI prompt hint and never reaches the game.

`tests/test_csv_schema.py::test_column_dictionary_matches_the_csv_headers` fails
if this table and the real headers disagree, so it cannot rot.

| File | id prefix | Columns | Consumed by |
|---|---|---|---|
| `achievements.csv` | `A_` | **id**, **api_name**, **name**, **description**, **hidden**, **category**, **condition**, **art_notes** | `generate_achievement_data.py`, `generate_achievement_icons.py` |
| `cards_market.csv` | `M_` | **id**, **name**, **category**, **cost**, **effect**, **persistent**, **tooltip**, art_notes | `generate_market_data.py`, `generate_card_atlases.py` |
| `cards_phase1.csv` | `P1_` | **id**, **title**, **severity**, **immediate**, **ongoing**, art_notes | `build_save.py` (Dawn deck) |
| `cards_phase2.csv` | `P2_` | **id**, **title**, **severity**, **immediate**, **ongoing**, art_notes | `build_save.py` (Dawn deck) |
| `cards_phase3.csv` | `P3_` | **id**, **title**, **severity**, **immediate**, **ongoing**, art_notes | `build_save.py` (Dawn deck) |
| `cards_phase4.csv` | `P4_` | **id**, **title**, **severity**, **immediate**, **ongoing**, art_notes | `build_save.py` (Dawn deck) |
| `cards_recipes.csv` | `R_` | **id**, **name**, **ingredients**, **cost**, **effect**, art_notes, script | `generate_recipe_data.py` (reads `script`) |
| `cards_scenarios.csv` | `SC_` | **id**, **name**, **season**, **effect**, **ongoing**, art_notes | `build_save.py` |
| `cards_starting.csv` | `S_` | **id**, **character**, **name**, **count**, **arrives**, **effect**, art_notes | `generate_market_data.py`, `generate_card_atlases.py` |
| `cards_threats.csv` | `T_` | **id**, **name**, **type**, **hp**, **attack**, **severity**, **special**, art_notes, pry_reward | `generate_threat_types.py` (reads `type`, `pry_reward`) |
| `cards_trophies.csv` | `TR_` | **id**, **boss**, **bonus**, art_notes | `build_save.py` |
| `cards_visitors.csv` | `V_` | **id**, **character**, **trigger**, **immediate**, **departure** | `build_save.py` |
| `locations.csv` | `L_` | **id**, **name**, **yields**, **special**, **sanity_modifier**, **defense**, **threat_rate**, **house_owner** | reference only — the live values are `LOCATION_YIELDS` (`lua/global.lua`) |
| `resources.csv` | `R_` | **id**, **name**, **color**, **icon**, **tag**, **sources**, **uses** | reference only — the live tags are the token bags in `build_save.py` |
| `tooltips.csv` | *(none — keyed by `tag`)* | tag, tooltip | `build_save.py` (`TOOLTIP_DATA`) |

Severity is 1–5 on Dawn cards. `cards_recipes.csv` and `resources.csv` share the
`R_` prefix, so a collision between them is its own test.

## Conventions

- CSV schemas are enforced by `tests/test_csv_schema.py` (required columns,
  unique ids, stat ranges). Card ids are prefixed by deck (`P1_`, `M_`, `T_`, …).
- `iconography.md` is authoritative for icon meaning; `asset_manifest.md` drives
  `lua/assets.lua`. Deep reference: [`../docs/agents/`](../docs/agents/README.md).
