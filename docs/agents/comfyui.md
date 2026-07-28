# ComfyUI Workflow

Generating and syncing card/board art, and the derived-art step that TTS depends on.

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
- **Sampler:** `euler`, 30 steps, CFG 4.0, scheduler `normal`, denoise 1.0
- **Rig:** RTX 4070 Ti, 12 GB VRAM, ComfyUI 0.20.1 — Flux Dev Q8 at 1024²
  fits in VRAM at roughly 20–40 s/image.
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
| `snm_char_<base>` | **Hand-drawn — never auto-generate.** | `art/characters/<base>.png` is authoritative and the generator and sync script both skip this prefix, so drop standee art in by hand. The build loads `<base>_standee.png` — run `normalize_standee_art.py` after. |
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
6. **Build card atlases:**
   ```bash
   python scripts/generate_card_atlases.py
   ```
   Composites `art/decks/illustrations/<id>.png` into the top region of each card and renders the text panel beneath. Missing illustrations fall back to a flat accent rectangle — partial generations don't break the build.
7. **Build the TTS save:**
   ```bash
   python scripts/build_save.py
   ```

## Derived art: `_tile.png` and `_standee.png`

Two asset families are **not** used as generated. The generator writes
`<name>.png`; a normalizer derives `<name>_tile.png` / `<name>_standee.png`
beside it, and `ASSET_MAP` loads the derived file. Sources are never modified,
so both scripts are safe to re-run and safe to iterate against.

They exist because TTS reshapes these two objects before you ever see them:

| Family | What TTS does | What the normalizer fixes |
|---|---|---|
| **Location tiles** (`art/tiles/`) | `CustomTile Type 2` is a **circle** — TTS crops a disc from the centre of the square image | Generated art is not reliably centred (`jameshome.png` once had 945×645 of picture sitting 96px below centre between black bars, so the disc showed an off-centre letterboxed slice). Takes the largest square centred on the *content*. |
| **Character standees** (`art/characters/`) | `ColorDiffuse` is applied as a **multiply over the whole image**, not just the holder | An opaque backdrop becomes a solid tinted rectangle — James's blue `(0.12, 0.53, 1.00)` over cream parchment lands on ≈`(29, 127, 220)`. Cuts the backdrop to transparent so the tint colours only the holder, and fits every figure to 512×1024 so characters are the same height. |

**Background removal is opt-in**, via `CUT_BACKGROUND` in
`normalize_standee_art.py`. Do not replace it with a "is the border a uniform
colour?" test — that was tried and it fails, because the hand-drawn standees are
designed *cards* (Rayman in a forest under the game title, Luca with a name
banner) whose borders are uniform too, so the flood leaks inward and eats the
artwork. It chewed the background out of `ellie_back` and both Luca faces while
leaving `ellie_front` intact — breaking a matched front/back pair. Add a name to
the list when their art is a figure on a plain backdrop; the decision is made
per **character**, never per image, so front and back always match.

Framing rules that follow, for anyone generating new art:

- **Tiles:** keep the subject centred and nothing important in the corners —
  the disc throws away ~21% of the canvas.
- **Standees:** a plain, even backdrop is what makes a clean cutout possible.
  Generate at 2:1 if you can; other aspects are re-fitted, not stretched.

## Iteration tip

To regenerate a single card with a tweaked prompt:

1. Edit the `art_notes` column for that row in `content/cards_*.csv`.
2. Delete `c:\Users\GGPC\Documents\ComfyUI\output\snm_card_<id>_00001_.png`.
3. Run `python scripts/generate_comfyui_assets.py --only <id> --skip-existing`.
4. Rerun the sync + atlas builder.
