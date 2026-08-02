# scripts/ — build & generators

Python build pipeline. `build_save.py` is the single source of truth for what
gets packaged into the TTS save (`LUA_LOAD_ORDER` + `XML_LOAD_ORDER` + spawned
objects). The rest are generators (source → output) plus the standalone
`simulate_balance.py` (Monte Carlo, **not** on the build path).

The build load order (`lua[]` + `xml[]`) is data: [`load_order.json`](load_order.json).
The generator map below is mirrored machine-readably in [`generators.json`](generators.json)
(a freshness test keeps the two honest).

## Generator map — "what do I regenerate after editing X?"

| Edit this source | Run this generator | It writes |
|---|---|---|
| `sounds/…` | `generate_audio_manifest.py` | `lua/audio_manifest.lua` |
| `content/help/whatnow_hints.md` | `generate_whatnow_hints.py` | `lua/whatnow_hints.lua` |
| `content/cards_market.csv` + `cards_starting.csv` | `generate_market_data.py` | `lua/market_data.lua` |
| `content/cards_threats.csv` | `generate_threat_types.py` | `lua/threat_types.lua` |
| `content/cards_recipes.csv` | `generate_recipe_data.py` | `lua/recipe_data.lua` |
| `content/notebook/*.md` + `help/glossary.md` | `generate_notebook.py` | `lua/notebook_data.lua` |
| `content/help/character_briefings.md` | `generate_character_briefings.py` | `lua/character_briefings.lua` |
| `content/notebook/*.md` + `help/glossary.md` | `generate_player_rules.py` | `PlayerRules.md` + `.html` |
| `content/achievements.csv` | `generate_achievement_data.py` | `lua/achievement_data.lua` + `steam/achievements.json` |
| **any** `lua/*.lua` | `generate_symbol_index.py` | `SYMBOLS.md` + `symbols.json` + `.luacheckrc` |
| **any** `lua/*.lua` | `generate_gamestate_map.py` | `docs/gamestate.md` |

Generators are idempotent and order-independent; `tests/test_generated_freshness.py`
fails if any output is stale.

## The canonical pipeline

This is the one place the build sequence is written out in full. Everything else
in the repo links here rather than repeating it.

```bash
python scripts/check.py          # ← finish every task with this
```

`check.py` runs four stages, each gating the next, and prints a one-line verdict:

1. **`regenerate_all.py`** — every generator in `generators.json` order, then
   `build_save.py`. Reads the manifest so it can't drift; generators whose
   sources are absent (e.g. `sounds/` on a clean clone) are skipped rather than
   erroring. `--no-build` / `--list` are available on `regenerate_all.py` itself.
2. **`python -m pytest tests`** — the suite, including the freshness guards.
3. **`ruff check scripts tests`** — the Python linter, against the pinned rule
   set in [`../ruff.toml`](../ruff.toml).
4. **`luacheck lua/`** — against the generated `.luacheckrc`. Both linters are
   reported as *skipped*, not failed, when the tool is absent.

Afterwards it reports any tracked file a generator rewrote, so those changes go
into the same commit.

Flags: `--fast` (skip stage 1), `--no-lint` (skip stages 3–4).

**Stages 2–4 mirror the CI jobs one-for-one, and must stay that way.** They
did not once: `check.py` ran pytest and luacheck but not ruff, so ruff's job sat
red for a month while this command reported everything green. Add a job to
[`../.github/workflows/tests.yml`](../.github/workflows/tests.yml) and you add a
stage here.

Both linters are version-sensitive, so both are pinned: the ruff **rule set** in
`ruff.toml` and the ruff **version** in the workflow. An unpinned linter changes
its own defaults underneath you, which is exactly how the job went red without a
line of this repo changing.

Run a stage on its own only when you are debugging *that stage*.

## Derived art (not in generators.json — binary output, run when art changes)

| Edit this | Run this | It writes |
|---|---|---|
| `art/tiles/<name>.png` | `normalize_tile_art.py` | `art/tiles/<name>_tile.png` |
| `art/characters/<name>.png` | `normalize_standee_art.py` | `art/characters/<name>_standee.png` |
| `art/achievements/src/<base>.png` | `generate_achievement_icons.py` | `art/achievements/<base>.png` + `steam/*.jpg` |

`ASSET_MAP` loads the **derived** files, so new art that skips this step never
appears in the game. TTS reshapes both families before the player sees them (a
tile is cropped to a circle; a standee's whole image is multiplied by its
`ColorDiffuse` tint) — full rationale in
[`docs/agents/derived-art.md`](../docs/agents/derived-art.md).

## Debug / deploy tools (not generators)

- `inspect_save.py` — read any TTS save like a debugger: `--live` (newest
  autosave: gameState + object positions), `--band` (objects sunk in the
  tabletop), `--error N` (decode an in-TTS `<Global:N>` error to
  `lua/<file>:<line>`). See [`../docs/debugging.md`](../docs/debugging.md).
- `iwanttoplay.py` — regen → build → test → install save → **purge this
  mod's stale TTS asset cache** → asset server → launch TTS.

## Conventions

- **File-size budget:** if a file passes ~500 lines, split it before adding more.
- Never hand-edit a generated `lua/*.lua`; edit its source and rerun the generator.
- Asset/ComfyUI details: [`../docs/agents/comfyui.md`](../docs/agents/comfyui.md).
- Architecture and the file map: [`../docs/agents/architecture.md`](../docs/agents/architecture.md)
  and [`../docs/agents/file-structure.md`](../docs/agents/file-structure.md).
