"""inspect_art.py — measure art the way the pipeline sees it.

The questions that come up every single time art is dropped into this repo,
answered in one command instead of a throwaway `python -c` with Pillow in it:

  - what size / mode / file size is this, really?
  - does it carry a DEAD alpha channel (RGBA whose alpha is 255 everywhere)?
    That is pure file-size overhead, and it is what arrives from most
    generators. Converting to RGB cut ~26% off James's source art.
  - how plain is the border? This is what normalize_standee_art measures to
    decide whether it will PERMIT a background cut (>= UNIFORM_MAX_SPREAD and
    it refuses outright). Reported as "cut permitted / refused" rather than
    "plain / card" on purpose: a permissive number is not a recommendation.
    Luca's art is a designed card whose border measures 7, and flooding it ate
    the artwork — which is why CUT_BACKGROUND is a hand-maintained claim about
    each character's art and not a threshold.
  - is the derived `_standee.png` / `_tile.png` older than the source beside
    it, i.e. is the game still showing the previous art?

That last one is the expensive failure. `ASSET_MAP` loads the DERIVED file, so
new art that never got normalized is invisible in-game with nothing failing —
see docs/agents/derived-art.md.

The plain-border verdict is imported from normalize_standee_art rather than
recomputed here, deliberately. Two implementations of "is this backdrop plain"
would drift, and this tool would then confidently report the opposite of what
the normalizer actually does.

Usage (repo root):
    python scripts/inspect_art.py --standees          # characters + derived, staleness
    python scripts/inspect_art.py --tiles             # location tiles + derived
    python scripts/inspect_art.py PATH [PATH ...]     # any images (globs ok)
"""

import argparse
import glob
import os

# Same-directory import: the normalizer owns UNIFORM_MAX_SPREAD and the border
# measurement. Importing the private helper is intentional — see the docstring.
from normalize_standee_art import (
    CHARACTERS,
    FACES,
    UNIFORM_MAX_SPREAD,
    _uniform_border,
)
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = os.path.join(ROOT, "art", "characters")
TILES = os.path.join(ROOT, "art", "tiles")


def opaque_fraction(img):
    """Fraction of pixels with any opacity. 1.0 for images without alpha."""
    if img.mode not in ("RGBA", "LA"):
        return 1.0
    a = img.getchannel("A")
    lo, hi = a.getextrema()
    if lo == 255:
        return 1.0                      # fully opaque, no need to count
    if hi == 0:
        return 0.0
    return sum(1 for p in a.get_flattened_data() if p > 0) / float(a.size[0] * a.size[1])


def describe(path):
    """One row of measurements, or None if the file isn't there."""
    if not os.path.isfile(path):
        return None
    img = Image.open(path)
    frac = opaque_fraction(img)
    dead_alpha = img.mode == "RGBA" and img.getchannel("A").getextrema()[0] == 255
    plain, spread = _uniform_border(img)
    return {
        "path": path,
        "size": img.size,
        "mode": img.mode,
        "kb": os.path.getsize(path) / 1024.0,
        "opaque": frac,
        "dead_alpha": dead_alpha,
        "plain": plain,
        "spread": spread,
    }


def format_row(row, label):
    mode = row["mode"] + ("!" if row["dead_alpha"] else "")
    # What the number GATES, not what the art IS — see the banner in main().
    cut = "cut permitted" if row["plain"] else "cut refused  "
    return (f"  {label:24s} {str(row['size']):12s} {mode:6s} {row['kb']:7.0f} KB  "
            f"opaque {row['opaque'] * 100:5.1f}%  border {row['spread']:3d} {cut}")


def report(pairs):
    """pairs: (label, source_path, derived_path or None)."""
    stale, dead = [], []
    for label, src, derived in pairs:
        row = describe(src)
        if row is None:
            print(f"  {label:24s} (missing)")
            continue
        print(format_row(row, label))
        if row["dead_alpha"]:
            dead.append(label)

        if derived is None:
            continue
        drow = describe(derived)
        if drow is None:
            print(f"  {'  -> derived':24s} MISSING — run the normalizer")
            stale.append(label)
            continue
        print(format_row(drow, "  -> " + os.path.basename(derived)))
        if os.path.getmtime(derived) < os.path.getmtime(src):
            print(f"  {'':24s} ^^ STALE: older than its source")
            stale.append(label)
    return stale, dead


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="*", help="image files (globs allowed)")
    ap.add_argument("--standees", action="store_true",
                    help="every character source + its derived _standee.png")
    ap.add_argument("--tiles", action="store_true",
                    help="every location tile source + its derived _tile.png")
    args = ap.parse_args()

    pairs = []
    if args.standees:
        for char in CHARACTERS:
            for face in FACES:
                base = f"{char}_{face}"
                pairs.append((base,
                              os.path.join(CHARS, base + ".png"),
                              os.path.join(CHARS, base + "_standee.png")))
    if args.tiles:
        for src in sorted(glob.glob(os.path.join(TILES, "*.png"))):
            base = os.path.splitext(os.path.basename(src))[0]
            if base.endswith("_tile"):
                continue                # the derived file, listed under its source
            pairs.append((base, src, os.path.join(TILES, base + "_tile.png")))

    for raw in args.paths:
        # Expand globs ourselves: PowerShell does not expand them for python.
        for p in sorted(glob.glob(raw)) or [raw]:
            pairs.append((os.path.basename(p), p, None))

    if not pairs:
        ap.error("nothing to inspect — pass paths, or --standees / --tiles")

    print(
        "mode with '!' = dead alpha channel (RGBA but fully opaque; convert to RGB)\n"
        f"border = border spread. At >= {UNIFORM_MAX_SPREAD} normalize_standee_art\n"
        "REFUSES a background cut. Below it the cut is PERMITTED, which is NOT the\n"
        "same as wanted: Luca's designed card measures 7, and flooding it ate the\n"
        "artwork. Whether to cut is a per-character claim in CUT_BACKGROUND about\n"
        "whether the art is a figure on a backdrop — never read it off this number.\n")
    stale, dead = report(pairs)

    if dead:
        print(f"\n{len(dead)} file(s) carry a dead alpha channel: "
              f"{', '.join(dead)}")
    if stale:
        print(f"\n{len(stale)} derived file(s) STALE or missing: "
              f"{', '.join(stale)}\n  the game loads the DERIVED file — rerun "
              "scripts/normalize_standee_art.py (or normalize_tile_art.py)")
    if not stale and not dead:
        print("\nnothing to flag.")


if __name__ == "__main__":
    main()
