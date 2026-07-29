# Run book — generating the achievement icons with a local ComfyUI

**Hand this file to an AI agent running on the machine that has ComfyUI.**
It is written to be executed top to bottom with no further context: every
command is exact, every check has a pass/fail condition, and the failure modes
that actually happen are at the bottom.

What it produces: 24 achievement icons at 256×256 for the mod, plus 256×256
and 64×64 Steamworks variants, from
[`content/achievements.csv`](../content/achievements.csv). What the panel does
with them is [`achievements.md`](achievements.md).

---

## The one-paragraph version

Start ComfyUI on port 8000. Run `python scripts/generate_comfyui_assets.py
--achievements-only` from the repo root to queue 24 prompts. Wait for the
queue to drain. Run `python scripts/sync_comfyui_output.py`, then `python
scripts/generate_achievement_icons.py`, then `python scripts/build_save.py`,
then `python -m pytest tests`. Eyeball the 24 PNGs at thumbnail size and
requeue the ones that don't read. Everything below is that, with the checks.

---

## 0. Preconditions — verify before generating anything

Run these first. If any check fails, **stop and report it** rather than
working around it: a wrong model silently produces 24 usable-looking images in
the wrong style, which costs far more to discover later.

```bash
cd <repo root>                 # the directory containing scripts/ and content/
python -c "import PIL; print('Pillow', PIL.__version__)"
```

### Starting ComfyUI

This machine runs **ComfyUI Desktop**, which splits the install in two: the
data directory (`models/`, `output/`, `custom_nodes/`, `.venv/`) is
`C:\Users\GGPC\Documents\ComfyUI`, but the *code* is under
`%LOCALAPPDATA%\Programs\ComfyUI\resources\`. There is no `main.py` beside
`models/` — don't hunt for one. Launch the venv's Python against the Desktop
`main.py` and point it back at the data directory:

```powershell
& "C:\Users\GGPC\Documents\ComfyUI\.venv\Scripts\python.exe" -s "C:\Users\GGPC\AppData\Local\Programs\ComfyUI\resources\ComfyUI\main.py" --base-directory "C:\Users\GGPC\Documents\ComfyUI" --port 8000
```

Startup takes ~30 s. `To see the GUI go to: http://127.0.0.1:8000` is the ready
signal. These lines are **normal** and are not failures: `Failed to initialize
database … unable to open database file`, `Failed to check frontend version`,
and a DWPose/onnxruntime warning from `comfyui_controlnet_aux`.

### The checks

Confirm ComfyUI is up and that it can load the models this repo's workflow
names. Ask the *server* what it sees — listing model folders gives wrong
answers (see the `models/unet/` trap below):

```bash
curl -s http://127.0.0.1:8000/system_stats
python -c "import json,urllib.request; print(json.load(urllib.request.urlopen('http://127.0.0.1:8000/object_info/UnetLoaderGGUF'))['UnetLoaderGGUF']['input']['required']['unet_name'][0])"
```

| Check | Pass condition | If it fails |
|---|---|---|
| ComfyUI reachable | `/system_stats` returns JSON | Start it with the command above. **Port 8000, not ComfyUI's default 8188** — or change `COMFYUI_URL` at the top of `scripts/generate_comfyui_assets.py` |
| `UnetLoaderGGUF` exists | `/object_info/UnetLoaderGGUF` returns a node, not `{}` | Install the **ComfyUI-GGUF** custom node and restart ComfyUI |
| Models present | The `unet_name` list above contains `flux1-dev-Q8_0.gguf`; likewise `clip_l.safetensors` + `t5xxl_fp16.safetensors` (`DualCLIPLoader`), `ae.safetensors` (`VAELoader`), `flux\c4r1mj34.safetensors` (`LoraLoader`) | Fetch the missing file. Do **not** substitute a different checkpoint — the whole art set is one look |

> **The `models/unet/` trap.** On this rig `models/unet/` is empty and the Flux
> checkpoint lives in `models/diffusion_models/` — the modern name for the same
> folder, which `UnetLoaderGGUF` reads. An `ls models/unet/` looks exactly like
> a missing model when nothing is wrong. Trust `/object_info`, not the folder.
> Note also that the LoRA is referenced with a **backslash**
> (`flux\c4r1mj34.safetensors`), matching what ComfyUI reports on Windows.
| Output path correct | `COMFYUI_OUTPUT_DIR` at the top of `scripts/generate_comfyui_assets.py` and `scripts/sync_comfyui_output.py` matches this machine's ComfyUI `output/` folder | Edit both constants to the real path |

Free disk: 24 × 1024×1024 PNGs is roughly 40 MB. Not a concern, but the
ComfyUI output folder may already hold ~150 card renders.

## 1. Queue the prompts

```bash
python scripts/generate_comfyui_assets.py --achievements-only
```

Expected output: `Starve No More — queueing 24 assets`, then 24 lines of
`snm_ach_<name> (1024x1024) — queued (<id>)`, then `Done: 24/24 queued.`

Useful variants:

```bash
# one achievement only, by its CSV id
python scripts/generate_comfyui_assets.py --achievements-only --only A_HERO

# skip any whose render already exists (safe to re-run after an interruption)
python scripts/generate_comfyui_assets.py --achievements-only --skip-existing
```

**Do not** run the bare `python scripts/generate_comfyui_assets.py` unless the
whole art set is being rebuilt — it queues ~180 prompts including every card.

## 2. Wait for the queue to drain

```bash
curl -s http://127.0.0.1:8000/queue
```

Poll until `queue_running` and `queue_pending` are both empty. Measured on the
RTX 4070 Ti (12 GB): Flux Dev Q8 at 1024×1024 / 30 steps samples at **~4 s per
step, so ~2 minutes per image** — about **50 minutes** for all 24, plus a
one-off minute or two while the first job loads the model. (An earlier draft of
this run book claimed 20–40 s/image and 10–15 minutes total; that was
optimistic. Nothing is wrong if you see 2 min/image.) Poll every 60 s; do not
busy-wait, and do not start step 3 early — a half-written PNG syncs as a
corrupt file.

## 3. Sync, process, build, test

```bash
python scripts/sync_comfyui_output.py       # renders  -> art/achievements/src/
python scripts/generate_achievement_icons.py # src     -> art/achievements/ + steam/
python scripts/build_save.py                 # repackage the TTS save
python -m pytest tests                       # must be green
```

`sync_comfyui_output.py` strips ComfyUI's `_00001_` suffix and files
`snm_ach_hero_00001_.png` as `art/achievements/src/hero.png`. It skips
anything whose destination is already newer; add `--force` to overwrite, and
`--dry-run` to see what it would do first.

`generate_achievement_icons.py` is the step that matters: it centre-crops each
render to square, resizes to 256, vignettes it, applies the category-coloured
frame, and writes the Steam jpgs alongside. **It only rebuilds an icon whose
source render is newer than the output** — pass `--force` to rebuild
everything, or `--only A_HERO` for one.

Expected: `from ComfyUI art: 24`, `placeholders: 0`.
If it still says `placeholders: N`, N renders never landed in
`art/achievements/src/` — go back to step 2.

## 4. Quality pass — the part that needs judgement

Open `art/achievements/` and view the PNGs **at 64 px**, not full size. That
is the size they are read at in the panel (46 px) and in the Steam overlay
(64 px). Reject and requeue any icon where:

- you can't tell what the object is at 64 px — usually means the render came
  out as a *scene* instead of a single object;
- the subject is off-centre or cropped by the frame — the square crop takes
  the centre, so a subject sitting low or left loses its head;
- it is mostly dark — a black object on a black field disappears at thumbnail
  size;
- there is legible text, a border, or a UI element in the image (Flux will
  occasionally invent all three despite the negative prompt).

To redo one:

```bash
python scripts/generate_comfyui_assets.py --achievements-only --only A_HERO
# wait for the queue, then:
python scripts/sync_comfyui_output.py --force
python scripts/generate_achievement_icons.py --only A_HERO --force
```

Each run uses a fresh random seed, so re-queueing the same prompt gives a
different image. If three attempts all fail the same way, the prompt is the
problem, not the seed — edit that row's `art_notes` in
`content/achievements.csv` (see the prompt rules below), then
`python scripts/generate_achievement_data.py` and requeue.

### What makes a good `art_notes` for an icon

The script wraps every row with the icon framing and the project's locked
style, so `art_notes` should be **one object, concrete, no scene**:

- Good: `a snapped antler half-buried in cracked asphalt`
- Good: `a stitched cloth heart with a battery sewn into it`
- Bad: `the team celebrates on the basketball court at sunrise` — several
  figures, a horizon, no readable silhouette
- Bad: `victory` — abstractions render as mud

Style, negative prompt and the icon framing live in
`scripts/generate_comfyui_assets.py` (`STYLE`, `NEGATIVE`,
`ACHIEVEMENT_PREFIX`, `ACHIEVEMENT_QUALIFIER`). Change those only to change
*every* icon; per-icon changes belong in the CSV.

### The cfg trap — read this before touching a prompt

**If icons come back as glowing orbs, pure black frames, or images with no
relation to their prompt, it is the sampler configuration, not the prompt.**
This cost a full day in July 2026; the whole diagnosis is below so it doesn't
have to be repeated.

Flux Dev is *guidance-distilled*: it expects a `FluxGuidance` node carrying the
guidance scale and `KSampler` at **cfg 1.0**. `build_workflow` originally ran
true `cfg 4.0` with a real negative prompt, which is off-spec. On the card
prompts it mostly got away with it. On single-object icon prompts it did not —
it produced, from identical settings:

- an amber orb or glowing streetlight painted as the subject in ~20 of 24 icons;
- pure black frames (7 of 24 in one batch);
- straightforwardly off-prompt images — "a wall calendar with the first three
  days crossed out" rendering as a glowing green sphere held by a hand.

Because the failures varied seed to seed, they *look* like seed variance, and
because they varied with wording they *look* like prompt faults. They were
neither. Four rounds of prompt rewriting and a LoRA-strength reduction all
failed to shift the orb; adding `FluxGuidance` fixed every symptom at once.

Icons therefore opt into the correct configuration
(`ICON_FLUX_GUIDANCE = 3.5`, cfg 1.0) while **cards stay on the original
cfg 4.0 path** — 200+ card illustrations were rendered that way and re-rendering
them is an art-direction decision, not a bug fix.

Only after the sampler is right is it worth blaming a prompt. Genuine
prompt-level faults reproduce across *different subjects* and *different seeds*.

**The control test.** Before blaming the prompt *or* the environment, re-render
a card that already looks right in the repo:

```bash
python scripts/generate_comfyui_assets.py --cards-only --only M_BAT
```

If it comes back matching `art/decks/illustrations/M_BAT.png`, the model, LoRA,
VAE and sampler are all healthy and you are chasing prompt or seed. If it comes
back as mush, the fault is environmental — stop and fix that instead.
**Delete the control render from ComfyUI's `output/` afterwards**, or the next
sync will copy it over the committed card.

Three prompt-level faults that were real, and are fixed in the script:

- **`STYLE` furnishes a scene the icon doesn't have.** `STYLE` enumerates props
  — "suburban houses and streetlights", "gaming PCs", "basketball hoops" —
  because a *card* is a scene that needs furnishing. An icon has no scene, so
  Flux attaches the prop to the only thing in frame and paints a **streetlight
  as the subject**. Icons therefore append `ICON_STYLE`, which keeps the
  aesthetic and drops the furniture. Never append plain `STYLE` to an icon.
- **The glow trap.** An early prefix asked for `a plain dark background,
  dramatic single warm light source, heavy contrast`. Flux made the subject
  itself the light source and shrank it to a fifth of the frame. Don't name a
  light source inside the frame; prefer `moody desaturated backdrop` over
  `plain dark background`.
- **Negations don't work in the positive prompt.** `no horizon, no background
  scenery, nothing in the corners` mostly just reinforced the emptiness —
  Flux's T5 encoder barely honours negation. Exclusions belong in `NEGATIVE`.

The reliable reference is the `market` deck prefix (`a single object portrait
... soft warm side-light`), which produced 200+ good card illustrations on this
exact model and LoRA. When in doubt, mirror it.

**What was *not* the cause**, each disproved by experiment, so nobody repeats
them: the LoRA (dropping `c4r1mj34` from 0.85 to 0.35 changed nothing about the
orb, and only cost the DST ink line); the model, VAE or custom nodes (the M_BAT
control below reproduced the committed card exactly); and the seed (the same
failure survived dozens of fresh seeds).

## 5. Commit

```bash
git add art/achievements content/achievements.csv lua/achievement_data.lua \
        steam/achievements.json saves/
git commit -m "Achievement icons: real art from ComfyUI"
```

---

## Hard rules

- **Never run `playwright install`-style model downloads or swap the model.**
  The whole art set is one look; a different checkpoint makes the icons
  visibly not belong.
- **Never write into `art/characters/`.** Character standees are hand-drawn by
  the project owner; `sync_comfyui_output.py` already refuses `snm_char_*`,
  and that guard stays.
- **Never hand-edit `lua/achievement_data.lua` or `steam/achievements.json`.**
  Both are generated from the CSV and a freshness test fails if they drift.
- **Never edit files under `art/achievements/` by hand.** They are rebuilt
  from `art/achievements/src/`; edit the source render or the prompt.
- **Finish with `python -m pytest tests` green.** The suite checks every
  achievement has all three icon files on disk and that the CSV, the Lua
  roster and the Steam manifest agree.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `urlopen error [Errno 111] Connection refused` | ComfyUI isn't running, or is on 8188 | Start it with the launch command in §0, or edit `COMFYUI_URL` |
| No `main.py` anywhere in `Documents\ComfyUI` | ComfyUI Desktop keeps the code in `%LOCALAPPDATA%\Programs\ComfyUI\resources\ComfyUI\` and only the data here | Use the `--base-directory` launch command in §0 |
| `models/unet/` is empty — looks like the model is missing | The Flux checkpoint is in `models/diffusion_models/`, which is the same folder under its modern name | Nothing to fix; verify with `/object_info/UnetLoaderGGUF` instead |
| `Failed to initialize database … unable to open database file` at startup | ComfyUI's optional sqlite user-data DB; unrelated to rendering | Ignore — it still serves and renders normally |
| Queue accepts prompts but nothing renders; ComfyUI log says `UnetLoaderGGUF` unknown | ComfyUI-GGUF custom node missing | Install it, restart ComfyUI, requeue |
| `ERROR: source directory not found` from the sync script | `COMFYUI_OUTPUT_DIR` points somewhere else on this machine | Edit the constant, or pass `--source <path>` |
| Sync reports `Skipped (up to date)` for everything | Outputs older than the copies already in the repo | `python scripts/sync_comfyui_output.py --force` |
| Icons still look like the flat lettered placeholders | `art/achievements/src/<base>.png` never arrived | Re-run steps 1–3; check the sync script's per-file log |
| `test_lua_achievements.py::test_every_achievement_has_an_icon_on_disk` fails | An icon or a Steam variant wasn't written | `python scripts/generate_achievement_icons.py --force` |
| `test_generated_freshness.py` fails on `achievement_data.lua` | The CSV changed without regenerating | `python scripts/generate_achievement_data.py` |
| Out of VRAM mid-queue | Flux Dev Q8 at 1024² needs ~12 GB | Restart ComfyUI, then `--achievements-only --skip-existing` to resume |
| Icons look right but the panel shows blank squares in TTS | The save wasn't rebuilt, or TTS cached the old asset | `python scripts/build_save.py`, then use `iwanttoplay` (it purges this mod's stale TTS asset cache) |
