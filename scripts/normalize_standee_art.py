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

# ENCLOSED backdrop pockets: the gap between a standing figure's legs, and the
# slots between their arms and their body. The flood above only starts at the
# border by design, so it cannot reach anything the figure encloses — James
# stood on the table with a solid cream wedge between his shins, reading as a
# skirt, and cream slabs under both arms.
#
# The obvious fix (clear every enclosed backdrop-coloured pocket) is wrong
# here, and measurably so: this art paints skin highlights in the SAME
# parchment tone as the backdrop, so his face is itself an enclosed pocket
# whose mean colour is (236,223,190) against a backdrop of (231,215,176) — a
# distance of 14, well inside any threshold that catches the leg gap at
# (237,224,191). Colour cannot separate them. Height can: measured on
# james_front, the pockets are
#
#   face          y 304-517   centre 28% of height   KEEP
#   above hair    y 133-294   centre 15%             KEEP
#   arm/body gap  y 1021-1125 centre 74%             CUT
#   arm/body gap  y 1032-1117 centre 74%             CUT
#   between legs  y 1023-1376 centre 82%             CUT
#
# so the rule is "enclosed backdrop below this fraction of the image". Opt-in
# per character for the same reason CUT_BACKGROUND is: it is a claim about one
# piece of art, and it should be reviewable rather than inferred.
# Guard: tests/test_standee_art.py.
CUT_ENCLOSED_BELOW = {"james": 0.55}

# Ignore specks. A fraction of the canvas, not a pixel count, so it means the
# same thing whatever size the art arrives at.
MIN_POCKET_FRAC = 0.0003

# Much tighter than FLOOD_THRESH, and the pass runs on the ORIGINAL image
# rather than the flooded one. Both were learned the hard way in one go: at 60,
# on the post-flood image, "backdrop-coloured and still opaque" walked through
# the jacket's highlights and the skin and found ONE component covering 18% of
# the canvas, whose centroid happened to fall low. It cleared his jacket, his
# face and his shins and left the gap between his legs exactly as it was.
# At 25, on the original, the components come out clean and separate: the
# figure's own tones no longer bridge them.
POCKET_THRESH = 25


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


def _backdrop_colour(img):
    """The backdrop's colour: the median of the border ring, per channel."""
    band = _border_pixels(img)
    return tuple(sorted(c[i] for c in band)[len(band) // 2] for i in range(3))


def _cut_enclosed_pockets(original, cut_img, below_frac):
    """Clear backdrop-coloured pockets the border flood could not reach.

    `original` is the art BEFORE the flood — the connectivity question is
    "was this region enclosed by the figure", and the flooded image no longer
    answers it (everything outside is already gone, so nothing can touch the
    border any more). `cut_img` is the flooded RGBA the pixels are cleared in.

    Only pockets whose vertical centre sits below `below_frac` of the image —
    see CUT_ENCLOSED_BELOW for why height, and not colour, is the test.
    """
    rgb = original.convert("RGB")
    w, h = rgb.size
    bg = _backdrop_colour(rgb)
    src = list(rgb.getdata())

    def is_backdrop(i):
        c = src[i]
        return (abs(c[0] - bg[0]) <= POCKET_THRESH
                and abs(c[1] - bg[1]) <= POCKET_THRESH
                and abs(c[2] - bg[2]) <= POCKET_THRESH)

    seen = bytearray(w * h)
    min_px = max(1, int(MIN_POCKET_FRAC * w * h))
    pockets, clear_px = 0, []

    for start in range(w * h):
        if seen[start] or not is_backdrop(start):
            continue
        stack, cells, touches_edge = [start], [], False
        seen[start] = 1
        while stack:
            i = stack.pop()
            cells.append(i)
            y, x = divmod(i, w)
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                touches_edge = True
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    j = ny * w + nx
                    if not seen[j] and is_backdrop(j):
                        seen[j] = 1
                        stack.append(j)
        if touches_edge or len(cells) < min_px:
            continue          # outside, or a speck
        centre_y = sum(i // w for i in cells) / float(len(cells))
        if centre_y / h < below_frac:
            continue          # up in the figure's face — see the table above
        clear_px.extend(cells)
        pockets += 1

    out = cut_img.convert("RGBA")
    if clear_px:
        alpha = out.getchannel("A")
        opaque = list(alpha.getdata())
        for i in clear_px:
            opaque[i] = 0
        alpha.putdata(opaque)
        out.putalpha(alpha)
    return out, pockets, len(clear_px) / float(w * h)


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
        original = img.copy()          # the flood destroys the enclosure test
        img, frac = _cut_background(img)
        note = f"cut {frac * 100:.0f}% background"
        below = CUT_ENCLOSED_BELOW.get(name.split("_")[0])
        if below:
            img, pockets, pocket_frac = _cut_enclosed_pockets(original, img, below)
            if pockets:
                note += f" + {pockets} enclosed pocket(s) ({pocket_frac * 100:.1f}%)"
        out = _fit(img)
        note += ", content re-fitted"
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
