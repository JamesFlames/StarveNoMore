# Derived Art: `_tile.png` and `_standee.png`

Why location tiles and character standees are normalized before the build sees
them, and the framing rules that follow for anyone making new art.

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

Two asset families are **not** used as generated. The source is `<name>.png`;
a normalizer derives `<name>_tile.png` / `<name>_standee.png` beside it, and
`ASSET_MAP` loads the derived file. Sources are never modified, so both scripts
are safe to re-run and safe to iterate against.

```bash
python scripts/normalize_tile_art.py
python scripts/normalize_standee_art.py
```

Skipping this is the classic "I added new art and nothing changed in the game"
— `ASSET_MAP` points at the derived files, not at what you dropped in. Where
this sits in the wider art pipeline: [`comfyui.md`](comfyui.md).

## Why they exist

TTS reshapes these two objects before you ever see them:

| Family | What TTS does | What the normalizer fixes |
|---|---|---|
| **Location tiles** (`art/tiles/`) | `CustomTile Type 2` is a **circle** — TTS crops a disc from the centre of the square image | Generated art is not reliably centred (`jameshome.png` once had 945×645 of picture sitting 96px below centre between black bars, so the disc showed an off-centre letterboxed slice). Takes the largest square centred on the *content*. |
| **Character standees** (`art/characters/`) | `ColorDiffuse` is applied as a **multiply over the whole image**, not just the holder | An opaque backdrop becomes a solid tinted rectangle — James's blue `(0.12, 0.53, 1.00)` over cream parchment landed on ≈`(29, 127, 220)`. Cuts the backdrop to transparent so the tint colours only the holder, and fits every figure to 512×1024 so characters are the same height. |

## Background removal is opt-in

Via `CUT_BACKGROUND` in `normalize_standee_art.py`. Do not replace it with a
"is the border a uniform colour?" test — that was tried and it fails, because
the hand-drawn standees are designed *cards* (Rayman in a forest under the game
title, Luca with a name banner) whose borders are uniform too, so the flood
leaks inward and eats the artwork. It chewed the background out of `ellie_back`
and both Luca faces while leaving `ellie_front` intact — breaking a matched
front/back pair. Add a name to the list when their art is a figure on a plain
backdrop; the decision is made per **character**, never per image, so front and
back always match.

**The list is currently empty.** James was the one entry until his art was
redrawn (2026-08) into a designed card like the others, at which point the
flood would have eaten it. The machinery stays for the next
figure-on-a-backdrop.

### The failure mode when art and list disagree

An opt-in list is a claim about a *specific piece of art*, and art gets
redrawn underneath it. When a listed character's new art is not plain,
`normalize()` prints `REFUSED`, returns `None`, and **leaves the previous
`_standee.png` on disk** — new art in the repo, old art on the table, and a
green build, because nothing downstream can tell the difference.
`tests/test_standee_art.py` is the guard: it fails when a listed character's
border is not plain, when a designed card comes back partly transparent, or
when any `_standee.png` is older than the source beside it.

## Framing rules for new art

- **Tiles:** keep the subject centred and nothing important in the corners —
  the disc throws away ~21% of the canvas.
- **Standees:** a plain, even backdrop is what makes a clean cutout possible.
  Generate at 2:1 if you can; other aspects are re-fitted, not stretched.
