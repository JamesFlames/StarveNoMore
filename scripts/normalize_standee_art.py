"""Cut the background out of each character standee and size it consistently.

The sibling of `normalize_tile_art.py`, for the other content-shaped asset.

Two problems it solves, both invisible in the source file:

**The background is multiplied by the standee's tint.** build_save gives each
`Figurine_Custom` a `ColorDiffuse` from STANDEE_COLORS, and TTS applies it as a
MULTIPLY over the whole image — not just the plastic holder. James's tint is a
strong blue (0.12, 0.53, 1.00); over his cream parchment background that lands
on roughly (29, 127, 220), i.e. a solid blue rectangle with a figure faintly
visible in it. Cut the background to transparent and the tint only colours the
holder, which is what it is for.

**The canvas is whatever the generator produced.** Standees are authored at
512x1024 (2:1). Art arriving at 720x1456 is 0.4945 — close enough to look fine
and wrong enough to squash the figure ~1% vertically, and it drifts further
every time someone generates at a new size. Fitting the *content* to a fixed
canvas also makes every character the same height on the table, which eyeballing
the canvas does not.

Background removal is **opt-in per character** (CUT_BACKGROUND), not
auto-detected. The obvious heuristic — "is the border a uniform colour?" — does
not work: the older standees are full illustrated cards (Rayman stands in a
forest under the game's title, Luca has a name banner) and those card borders
are uniform too, so the flood leaks inward and eats the artwork. Trying it that
way chewed the background out of ellie_back and both Luca faces while leaving
ellie_front intact, i.e. it broke a matched front/back pair. An explicit list
is reviewable and cannot silently damage art someone drew by hand.

Add a character here when their art is a figure on a plain backdrop rather
than a designed card. Everything not listed passes through untouched.

Source art is never modified: output goes to `<name>_standee.png` alongside it,
and build_save.py's ASSET_MAP points at those.

Run: python scripts/normalize_standee_art.py
"""

import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = os.path.join(ROOT, "art", "characters")

CHARACTERS = ["james", "coco", "rayman", "ellie", "luca"]
FACES = ["front", "back"]

# Characters whose art is a FIGURE ON A PLAIN BACKDROP, so the backdrop can be
# flooded away. Everything else is a designed card and is copied through
# untouched — see the module docstring for why this is a list and not a test.
CUT_BACKGROUND = {"james"}

# The canvas every standee ends up on. 2:1 is the shape build_save authors
# against (Figurine_Custom stretches its image to its own aspect).
OUT_W, OUT_H = 512, 1024

# Fraction of the canvas height the figure fills. Slightly under 1 so nobody
# is cropped at the ankles by a rounding error.
FILL = 0.96

# Max spread across sampled border pixels for "this is a plain background".
# Measured: James's parchment spreads 63; Rayman's illustrated forest 115.
UNIFORM_MAX_SPREAD = 90

# Flood-fill tolerance. Below the spread of a plain background (so the fill
# crosses its gradient) and well below the step onto the figure.
FLOOD_THRESH = 60

SENTINEL = (255, 0, 255)


def _border_pixels(img, step=4):
    px = img.load()
    w, h = img.size
    out = []
    for x in range(0, w, step):
        out += [px[x, 0][:3], px[x, h - 1][:3]]
    for y in range(0, h, step):
        out += [px[0, y][:3], px[w - 1, y][:3]]
    return out


def _uniform_border(img):
    """True when the frame around the art is a plain backdrop rather than a
    drawn scene — i.e. safe to flood away."""
    band = _border_pixels(img)
    spread = max(max(c) - min(c) for c in zip(*band))
    return spread < UNIFORM_MAX_SPREAD, spread


def _cut_background(img):
    """RGBA copy with the border-connected backdrop made transparent.

    Flood fill from the edges rather than keying on colour: a colour key also
    erases anything on the figure that happens to match the backdrop (skin and
    pale parchment are close), while a fill only removes what is actually
    connected to the outside.
    """
    rgb = img.convert("RGB")
    seeds = []
    w, h = rgb.size
    for x in (0, w // 2, w - 1):
        seeds += [(x, 0), (x, h - 1)]
    for y in (0, h // 2, h - 1):
        seeds += [(0, y), (w - 1, y)]

    for seed in seeds:
        if rgb.getpixel(seed) == SENTINEL:
            continue
        ImageDraw.floodfill(rgb, seed, SENTINEL, thresh=FLOOD_THRESH)

    out = img.convert("RGBA")
    src, cut = rgb.load(), out.load()
    cleared = 0
    for y in range(h):
        for x in range(w):
            if src[x, y] == SENTINEL:
                cut[x, y] = (0, 0, 0, 0)
                cleared += 1
    return out, cleared / float(w * h)


def _fit(img):
    """Scale the visible content to FILL of the canvas height and centre it,
    preserving aspect. Bottom-aligned so every character stands on the same
    line rather than floating at a different height."""
    box = img.getbbox()          # bbox of non-transparent pixels for RGBA
    content = img.crop(box) if box else img

    scale = (OUT_H * FILL) / content.height
    if content.width * scale > OUT_W:
        scale = OUT_W / float(content.width)
    new = (max(1, int(round(content.width * scale))),
           max(1, int(round(content.height * scale))))
    content = content.resize(new, Image.LANCZOS)

    canvas = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    canvas.paste(content,
                 ((OUT_W - new[0]) // 2, OUT_H - new[1] - int(OUT_H * (1 - FILL) / 2)),
                 content)
    return canvas


def normalize(name, cut):
    src = os.path.join(CHARS, name + ".png")
    if not os.path.isfile(src):
        print(f"  SKIP {name}: no source")
        return None

    img = Image.open(src)
    src_size = img.size
    had_alpha = img.mode == "RGBA" and img.getchannel("A").getextrema()[0] < 255

    if cut and not had_alpha:
        uniform, spread = _uniform_border(img)
        if not uniform:
            print(f"  {name:16s} REFUSED: listed for background removal but its "
                  f"border is not plain (spread {spread}) — check the art")
            return None
        img, frac = _cut_background(img)
        out = _fit(img)
        note = f"cut {frac * 100:.0f}% background, content re-fitted"
    elif had_alpha:
        out = _fit(img.convert("RGBA"))
        note = "already transparent, content re-fitted"
    elif src_size == (OUT_W, OUT_H):
        # Nothing to do. Copy the pixels through rather than round-tripping
        # them: re-fitting an opaque card has no bbox to work from, so it
        # would shrink the whole illustration by the FILL margin and add a
        # border that was never in the art. Keep the source MODE too — an
        # opaque card promoted to RGBA just carries a dead alpha channel and
        # grew every existing standee by ~80 KB.
        out = img
        note = "unchanged (already 512x1024, designed card)"
    else:
        out = img.resize((OUT_W, OUT_H), Image.LANCZOS)
        note = "resized whole canvas (composition preserved)"

    dest = os.path.join(CHARS, name + "_standee.png")
    out.save(dest, optimize=True)
    kb = os.path.getsize(dest) / 1024.0
    print(f"  {name:16s} {src_size[0]}x{src_size[1]} -> {OUT_W}x{OUT_H}  "
          f"{kb:6.0f} KB  [{note}]")
    return dest


def main():
    print(f"Normalizing standee art in {CHARS}")
    for char in CHARACTERS:
        # Decided per CHARACTER, never per image: front and back must get the
        # same treatment or the figurine is a cutout on one side and a card on
        # the other.
        cut = char in CUT_BACKGROUND
        for face in FACES:
            normalize(f"{char}_{face}", cut)


if __name__ == "__main__":
    main()
