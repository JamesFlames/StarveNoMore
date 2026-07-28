# Working With This Project

Day-to-day conventions for making a change here.

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

## To build the TTS save:
```bash
python scripts/build_save.py                                   # dev save (file:/// art, localhost sounds/rules)
python scripts/build_save.py --publish https://your.cdn/snm    # shareable save, hosted URLs only
```

## To regenerate card atlases:
```bash
python scripts/generate_card_atlases.py
```

## To regenerate tokens/boards/etc:
```bash
python scripts/generate_assets.py
```

## To queue illustration generation (requires ComfyUI running):
```bash
python scripts/generate_comfyui_assets.py
# Useful flags:
python scripts/generate_comfyui_assets.py --cards-only --skip-existing
python scripts/generate_comfyui_assets.py --deck phase1
python scripts/generate_comfyui_assets.py --only P1_QUIET_EVENING
python scripts/generate_comfyui_assets.py snm_boss   # backward-compatible substring filter
```

## To copy ComfyUI outputs into the repo art/ tree:
```bash
python scripts/sync_comfyui_output.py            # idempotent
python scripts/sync_comfyui_output.py --dry-run  # preview
```

## To regenerate the auto-loaded Lua data tables:
```bash
python scripts/generate_audio_manifest.py    # sounds/  → lua/audio_manifest.lua
python scripts/generate_whatnow_hints.py     # whatnow_hints.md → lua/whatnow_hints.lua
python scripts/generate_market_data.py       # cards_market.csv + cards_starting.csv → lua/market_data.lua (costs + weapon dice)
python scripts/generate_threat_types.py      # cards_threats.csv → lua/threat_types.lua (types + sealed rewards)
python scripts/generate_recipe_data.py       # cards_recipes.csv → lua/recipe_data.lua
python scripts/generate_notebook.py          # notebook/help markdown → lua/notebook_data.lua
python scripts/generate_player_rules.py      # notebook/glossary markdown → PlayerRules.md + PlayerRules.html
python scripts/generate_symbol_index.py      # lua/ → SYMBOLS.md + .luacheckrc
```

## To aggregate playtest session logs:
```bash
python scripts/analyze_sessions.py           # reads playtest/sessions/*.json
```

## To sanity-check a rule change against the balance sim:
```bash
python scripts/simulate_balance.py --sims 3000              # current rules
python scripts/simulate_balance.py --sims 3000 --rules old  # control group
# then compare against the baseline table in the "Balance Simulation" section
```

## To test in TTS:
```bat
iwanttoplay
```
(repo root) — regenerate everything → build → full pytest gate → copy the save
to the TTS saves folder → ensure the asset server is up → launch TTS via Steam.
`--skip-tests` / `--no-launch` to trim the ends. Driver: `scripts/iwanttoplay.py`.

Manually, the same steps are:
1. Run `python scripts/build_save.py`.
2. Start `scripts/serve_art.bat` so `http://localhost:8080/art/...` and `/sounds/...` resolve.
3. Copy `saves/StarveNoMore.json` to your TTS saves folder.
4. Load the save in TTS, click **Setup Game**.
