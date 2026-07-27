"""Centre each location tile's artwork so the circular tile shows it centred.

The location tiles are Custom_Tile with CustomTile Type 2 = CIRCLE: TTS crops
the square source image to a disc centred on the image. The generated art is
square canvas, but the *content* inside it is not always centred or square —
jameshome.png, for instance, has 945x645 of picture sitting 96px below centre
with black bars above and below. Cropping that to a disc therefore shows an
off-centre, letterboxed slice, which is why the house art did not sit
concentric inside the printed ring on the board.

This takes the largest square that is centred on the actual content and
rescales it to the full canvas, so the disc TTS cuts is centred on the picture
and free of the bars. Source art is never modified: output goes to
<name>_tile.png alongside it, and build_save.py points ASSET_MAP at those.

Run: python scripts/normalize_tile_art.py
"""

import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILES = os.path.join(ROOT, "art", "tiles")

# The tiles the board places in its printed rings.
SOURCES = [
    "jameshome", "raymanhome", "ellielucahome",
    "basketballcourt", "badmintoncourt",
]

OUT_SIZE = 1024
CONTENT_THRESHOLD = 60      # sum(r,g,b) above this counts as picture, not bar


def content_bbox(img, step=2):
    """Bounding box of non-black content — the picture inside any letterbox."""
    px = img.load()
    w, h = img.size
    xs, ys = [], []
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b = px[x, y][:3]
            if r + g + b > CONTENT_THRESHOLD:
                xs.append(x)
                ys.append(y)
    if not xs:
        return (0, 0, w, h)
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


def normalize(name):
    src = os.path.join(TILES, name + ".png")
    if not os.path.isfile(src):
        print(f"  SKIP {name}: no source")
        return None
    img = Image.open(src).convert("RGB")
    w, h = img.size
    x0, y0, x1, y1 = content_bbox(img)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0

    # Largest square centred on the content that stays inside the canvas.
    side = min(x1 - x0, y1 - y0, w, h)
    left = max(0, min(w - side, int(round(cx - side / 2))))
    top = max(0, min(h - side, int(round(cy - side / 2))))

    out = img.crop((left, top, left + side, top + side)).resize(
        (OUT_SIZE, OUT_SIZE), Image.LANCZOS)
    dest = os.path.join(TILES, name + "_tile.png")
    # optimize: these are 1024px illustrations shipped in the save's asset
    # bundle, and the source PNGs arrive straight from the generator with no
    # compression pass at all.
    out.save(dest, optimize=True)
    print(f"  {name:16s} content {x1-x0}x{y1-y0} centred at ({cx:.0f},{cy:.0f}) "
          f"-> square {side}px -> {os.path.basename(dest)}")
    return dest


def main():
    print(f"Centring tile art in {TILES}")
    for name in SOURCES:
        normalize(name)


if __name__ == "__main__":
    main()
