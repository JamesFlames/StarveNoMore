# ComfyUI Workflow

Generating and syncing card/board art. The normalizer step that TTS depends on
afterwards is its own topic: [`derived-art.md`](derived-art.md).

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

All artwork in this project is generated locally via ComfyUI — no paid image-API
calls. The pipeline is fire-and-forget: queue prompts → wait for ComfyUI to
finish → sync output into `art/` → run the atlas builder.

## Locked art direction

**Don't Starve Together aesthetic with a modern, urban (North American suburban)
twist.** Hand-drawn ink-line gothic cartoon (Tim Burton / Edward Gorey / Laika
lineage), with contemporary suburban props — smartphones, gaming PCs, energy
drink cans, basketball hoops, badminton nets — rendered *inside* that style,
not as photoreal interjections. This applies to every asset: cards, location
tiles, character standees, bosses, path tiles. The canonical `STYLE` prompt
prefix lives at the top of `scripts/generate_comfyui_assets.py` — keep that
single source of truth in sync if the direction is ever revised.

**Hero art is not generated here.** Character standees and the three house
tiles are authored outside this pipeline at 1254×1254 — that size marks one
against a 1024² render. This model does not reach their sepia-parchment look at
any setting tried, so replace them with external art, never a prompt.

## Install

- **Data path:** `c:\Users\GGPC\Documents\ComfyUI` — models, `output/`,
  `custom_nodes/`, and the Python venv at `.venv/`.
- **Code path:** this machine runs **ComfyUI Desktop**, so the source is *not*
  in the data path — it lives at
  `%LOCALAPPDATA%\Programs\ComfyUI\resources\ComfyUI\main.py`. Don't go looking
  for a `main.py` next to `models/`; there isn't one. Launch by pointing the
  venv's Python at that `main.py` with `--base-directory`:
  ```powershell
  & "C:\Users\GGPC\Documents\ComfyUI\.venv\Scripts\python.exe" -s "C:\Users\GGPC\AppData\Local\Programs\ComfyUI\resources\ComfyUI\main.py" --base-directory "C:\Users\GGPC\Documents\ComfyUI" --port 8000
  ```
- **Server URL** the scripts assume: `http://127.0.0.1:8000`. ComfyUI's own
  default is **8188**, so `--port 8000` is mandatory, not decorative.
- **Models in use:**
  - Diffusion: `models/diffusion_models/flux1-dev-Q8_0.gguf` (loaded via `UnetLoaderGGUF`)
  - VAE: `models/vae/ae.safetensors`
  - CLIP: `models/clip/clip_l.safetensors` + `models/clip/t5xxl_fp16.safetensors`
  - LoRA: `models/loras/flux/c4r1mj34.safetensors` at strength 0.85 (model + clip)

  `UnetLoaderGGUF` reads `models/diffusion_models/` — that folder is the modern
  name for what older docs call `models/unet/`, and on this rig `models/unet/`
  is **empty**. An `ls models/unet/` therefore looks like a missing model when
  nothing is wrong; ask the running server instead (see below).
- **Sampler (cards):** `euler`, 30 steps, CFG 4.0, scheduler `normal`,
  denoise 1.0.
- **Sampler (location tiles):** as cards but `FluxGuidance` 6.0, **cfg 1.0**,
  LoRA `1.0` (the `LOC_*` constants). At cfg 4.0 open-air scenes render as flat
  monochrome-green vector with no linework — what both original court tiles
  were, on two seeds running. Full rationale sits with the constants.
- **Sampler (achievement icons):** the same, except a `FluxGuidance` node at
  `ICON_FLUX_GUIDANCE = 3.5` feeds the sampler and **cfg drops to 1.0**. This
  is the configuration Flux Dev is actually distilled for; the cards' true
  `cfg 4.0` is off-spec and, on single-object icon prompts, blows highlights
  into a glowing orb, produces pure black frames, and drifts off-prompt
  entirely. Cards stay on the 4.0 path because 200+ were rendered with it —
  changing that is an art-direction call, not a bug fix. Full write-up:
  [`../comfyui-achievement-icons.md`](../comfyui-achievement-icons.md).
- **Rig:** RTX 4070 Ti, 12 GB VRAM, ComfyUI 0.20.1 — Flux Dev Q8 at 1024² /
  30 steps runs at ~4 s/step, i.e. **~2 min per image** (~50 min for 24).
- **Benign startup noise**, not failures: `Failed to initialize database …
  unable to open database file`, `Failed to check frontend version`, and the
  DWPose/onnxruntime warning from `comfyui_controlnet_aux`. The line that
  matters is `To see the GUI go to: http://127.0.0.1:8000`.

## File-naming convention

ComfyUI writes `<prefix>_00001_.png` to `ComfyUI/output/`. Categories used by
the scripts:

| Prefix | Maps to | Sync destination |
|---|---|---|
| `snm_loc_<base>`  | Location tile scenes (1024×1024) | `art/tiles/<base>.png` |
| `snm_path_<base>` | Path-edge variants (1024×1024)   | `art/board/<base>.png` |
| `snm_char_<base>`, `snm_loc_{james,rayman,ellieluca}home` | **Hero art — never auto-generate.** | The `art/` copy is authoritative; generator and sync both skip these prefixes, so drop art in by hand. The build loads the derived file, so run `normalize_standee_art.py` / `normalize_tile_art.py` after. |
| `snm_boss_<base>` | Boss / creature standees (512×1024) | `art/bosses/<base>.png` |
| `snm_card_<id>`   | Card illustrations (1024×1024)   | `art/decks/illustrations/<id>.png` |

`<id>` for cards is the `id` column from `content/cards_*.csv`
(e.g. `P1_QUIET_EVENING`, `M_FLASHLIGHT`).

## End-to-end card-art workflow

1. **Start ComfyUI** with the Desktop launch command in "Install" above, then
   confirm `http://127.0.0.1:8000/system_stats` returns JSON. Verify the models
   by asking the server what it can actually load, rather than listing folders:
   ```bash
   python -c "import json,urllib.request; print(json.load(urllib.request.urlopen('http://127.0.0.1:8000/object_info/UnetLoaderGGUF'))['UnetLoaderGGUF']['input']['required']['unet_name'][0])"
   ```
   `flux1-dev-Q8_0.gguf` in that list is the real pass condition. An empty `{}`
   response means the **ComfyUI-GGUF** custom node didn't load.
2. **Queue prompts:**
   ```bash
   python scripts/generate_comfyui_assets.py
   ```
   By default queues every board asset *and* every card. Useful flags:
   - `--cards-only` — only the ~150 card illustrations
   - `--no-cards` — only the original 23 board assets
   - `--deck phase1` (repeatable) — limit cards to one deck
   - `--only P1_QUIET_EVENING` — single card by id
   - `--skip-existing` — skip prompts whose `ComfyUI/output/<prefix>_*.png` already exists (ideal for incremental reruns)
3. **Wait** for ComfyUI to drain its queue (watch its console or `output/` mtime). Roughly 30s/image at 1024×1024 on the current rig.
4. **Sync output into the repo:**
   ```bash
   python scripts/sync_comfyui_output.py
   ```
   Idempotent; renames `<prefix>_00001_.png` → `<base>.png` in the right `art/` subdir.
5. **Normalize the shaped assets** (only when tile or standee art changed):
   ```bash
   python scripts/normalize_tile_art.py
   python scripts/normalize_standee_art.py
   ```
   Skipping this is the classic "I added new art and nothing changed in the
   game" — `ASSET_MAP` points at the derived files, not what you dropped in.
   Why they exist and how to frame art for them: [`derived-art.md`](derived-art.md).
6. **Build card atlases:**
   ```bash
   python scripts/generate_card_atlases.py
   ```
   Composites `art/decks/illustrations/<id>.png` into the top region of each card and renders the text panel beneath. Missing illustrations fall back to a flat accent rectangle — partial generations don't break the build.
7. **Build the TTS save:**
   ```bash
   python scripts/build_save.py
   ```

## Iteration tip

To regenerate a single card with a tweaked prompt:

1. Edit the `art_notes` column for that row in `content/cards_*.csv`.
2. Delete `c:\Users\GGPC\Documents\ComfyUI\output\snm_card_<id>_00001_.png`.
3. Run `python scripts/generate_comfyui_assets.py --only <id> --skip-existing`.
4. Rerun the sync + atlas builder.
