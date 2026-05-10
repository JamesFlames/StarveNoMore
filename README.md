# Starve No More

A cooperative survival board game for 3–5 players, built as a [Tabletop Simulator](https://store.steampowered.com/app/286160/Tabletop_Simulator/) mod. Suburban friends caught when something cosmic descends on their neighborhood must scavenge, cook, fight, and hold their sanity together for seven nights. Tone modeled on *Don't Starve Together*; mechanical DNA drawn from DST, *Hogwarts Battle*, *Catan*, and *Cthulhu Wars*.

> **Status:** pre-playtest. The design is locked in [`StarveNoMoreDesignConcept.md`](StarveNoMoreDesignConcept.md); content authoring and asset generation are in progress; the Lua/XML scaffold for TTS exists but has not been blind-tested yet.

## Where to start reading

| If you want… | Open |
|---|---|
| The 5-minute pitch | [`content/notebook/quickstart.md`](content/notebook/quickstart.md) |
| A high-level orientation to the repo | [`agents.md`](agents.md) |
| The canonical rules and design intent | [`StarveNoMoreDesignConcept.md`](StarveNoMoreDesignConcept.md) |
| The phased build plan (A–K) | [`Checklist_For_TTS_Implementation.md`](Checklist_For_TTS_Implementation.md) |
| TTS API reference | [`docs/HowToCreateGamesInTabletopSimulator.md`](docs/HowToCreateGamesInTabletopSimulator.md) |

## Repository layout

```
StarveNoMore/
├── lua/         TTS Lua scripts (concatenated by build_save.py into the save JSON)
├── xml/         TTS UI XML
├── content/     Card CSVs, in-game text (notebook/, help/), iconography, asset manifest
├── art/         Generated image assets (board, tiles, decks, tokens, characters, bosses)
├── scripts/     Build + asset generation (Python)
├── saves/       Built TTS save (StarveNoMore.json + pretty-printed copy)
└── docs/        Design references (board game theory, DST, TTS, related games)
```

See [`agents.md`](agents.md) for the file-by-file breakdown.

## Building

Requires Python 3 with `Pillow` (for image generation). Asset illustrations need a local [ComfyUI](https://github.com/comfyanonymous/ComfyUI) instance running Flux Dev.

```bash
# Build the TTS save (concatenates lua/ + xml/global_ui.xml into saves/StarveNoMore.json)
python scripts/build_save.py

# Regenerate card atlases from content/cards_*.csv
python scripts/generate_card_atlases.py

# Regenerate boards / tokens / player boards / legends
python scripts/generate_assets.py

# Queue illustration generation against a local ComfyUI server
python scripts/generate_comfyui_assets.py
# Optional prefix filter: python scripts/generate_comfyui_assets.py snm_boss
```

## Loading in Tabletop Simulator

1. Run `python scripts/build_save.py`.
2. Copy `saves/StarveNoMore.json` to your TTS saves folder
   (`%USERPROFILE%\Documents\My Games\Tabletop Simulator\Saves\` on Windows).
3. In TTS, *Games → Save & Load*, select the save, and click **Setup Game** on the table.

During local development, set `LOCAL_DEV = true` in `lua/assets.lua` and run `scripts/serve_art.bat` to serve `art/` over `http://localhost:8080`.

## Design pillars

The five non-negotiables every rule must serve:

1. **Tone over polish** — coherent gothic-cartoon visual identity over asset volume.
2. **Decisions paid in mismatched currencies** — every action costs in a stat *adjacent* to the one it fills.
3. **The world acts first** — every round opens with a hostile Dawn card.
4. **Specialization beats parallelism** — characters are rule-distinct, not stat-distinct.
5. **Emergent stories, not scripted narrative** — systems interact; players write the lore.

## Reference

- [`StarveNoMoreRequirements.md`](StarveNoMoreRequirements.md) — original commission brief (frozen).
- [`docs/PrinciplesOfGoodBoardGames.md`](docs/PrinciplesOfGoodBoardGames.md) — design theory.
- [`docs/DontStarveVideoGamePrinciples.md`](docs/DontStarveVideoGamePrinciples.md) — DST translation pillars.
- [`docs/InterestingGames.md`](docs/InterestingGames.md) — mechanical tear-downs of HPHB / Catan / Cthulhu Wars.
