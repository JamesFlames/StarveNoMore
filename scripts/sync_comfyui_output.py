"""
Sync ComfyUI output PNGs into the StarveNoMore repo's art/ tree.

ComfyUI writes generated images to its own output folder with names like
`snm_card_P1_QUIET_EVENING_00001_.png`. This script strips the `_00001_`
suffix and copies each file into the appropriate art/ subfolder, keyed off
the `snm_<category>_` prefix.

Usage:
  python scripts/sync_comfyui_output.py            # copy everything
  python scripts/sync_comfyui_output.py --dry-run  # show what would happen
  python scripts/sync_comfyui_output.py --force    # overwrite even if dest is newer

Idempotent: by default, skips files whose destination is newer than the
ComfyUI source PNG.
"""

import argparse
import glob
import os
import re
import shutil
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMFYUI_OUTPUT_DIR = r"c:\Users\GGPC\Documents\ComfyUI\output"

# Map snm_<category>_ → art/<subdir>/
#
# Achievement renders land in art/achievements/**src**/, not in
# art/achievements/ itself: the icons the game loads are the *processed*
# versions (square-cropped, vignetted, framed, resized, plus the Steam jpgs)
# that scripts/generate_achievement_icons.py builds from these. Writing the
# raw render straight into art/achievements/ would put a 1024px unframed image
# where the mod expects a 256px framed one.
CATEGORY_DIRS = {
    "snm_card_":  os.path.join(REPO_ROOT, "art", "decks", "illustrations"),
    "snm_loc_":   os.path.join(REPO_ROOT, "art", "tiles"),
    "snm_path_":  os.path.join(REPO_ROOT, "art", "board"),
    "snm_boss_":  os.path.join(REPO_ROOT, "art", "bosses"),
    "snm_ach_":   os.path.join(REPO_ROOT, "art", "achievements", "src"),
}

# Hero art — never overwritten from ComfyUI output. Files matching any of these
# prefixes are skipped with a note.
#
# Character standees (snm_char_) are hand-drawn.
#
# The three house tiles are authored outside this pipeline too, and the repo
# copies are the authoritative ones: art/tiles/jameshome.png is 1254x1254 and
# byte-matches the external source, while ComfyUI's snm_loc_jameshome_00001_.png
# is a different, worse 1024x1024 render that is still sitting in the output
# directory. Only the mtime check stopped a sync from clobbering the good art,
# and `--force` skips that check — so name them explicitly instead of trusting
# file timestamps. The courts are NOT hero art: they are generated, and
# art/tiles/basketballcourt.png is byte-identical to its ComfyUI original.
SKIP_PREFIXES = (
    "snm_char_",
    "snm_loc_jameshome",
    "snm_loc_raymanhome",
    "snm_loc_ellielucahome",
)

# ComfyUI's SaveImage tail: "<prefix>_<5-digit>_.png"
SUFFIX_RE = re.compile(r"_\d{5}_(?:\.png)$")


def categorize(filename):
    """Return (dest_dir, base) for a known prefix, or (None, None)."""
    for prefix, dest in CATEGORY_DIRS.items():
        if filename.startswith(prefix):
            base = filename[len(prefix):]
            base = SUFFIX_RE.sub(".png", base)
            if not base.endswith(".png"):
                # e.g. user already renamed; just trust it.
                return dest, base
            return dest, base
    return None, None


def main():
    parser = argparse.ArgumentParser(description="Copy ComfyUI output into art/.")
    parser.add_argument("--dry-run", action="store_true",
                        help="List actions without copying.")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite even if destination is newer.")
    parser.add_argument("--source", default=COMFYUI_OUTPUT_DIR,
                        help=f"ComfyUI output directory (default: {COMFYUI_OUTPUT_DIR})")
    args = parser.parse_args()

    if not os.path.isdir(args.source):
        print(f"ERROR: source directory not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    pattern = os.path.join(args.source, "snm_*.png")
    sources = sorted(glob.glob(pattern))
    if not sources:
        print(f"No snm_*.png files found in {args.source}")
        return

    print(f"Found {len(sources)} candidate file(s) in {args.source}")

    copied = 0
    skipped_uptodate = 0
    skipped_unknown = 0
    skipped_hero = 0
    by_category = {}

    for src in sources:
        fname = os.path.basename(src)
        if any(fname.startswith(p) for p in SKIP_PREFIXES):
            skipped_hero += 1
            continue
        dest_dir, dest_name = categorize(fname)
        if dest_dir is None:
            skipped_unknown += 1
            continue

        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, dest_name)

        if (not args.force) and os.path.exists(dest):
            if os.path.getmtime(dest) >= os.path.getmtime(src):
                skipped_uptodate += 1
                continue

        rel_dest = os.path.relpath(dest, REPO_ROOT)
        if args.dry_run:
            print(f"  would copy {fname} -> {rel_dest}")
        else:
            shutil.copy2(src, dest)
            print(f"  copied {fname} -> {rel_dest}")
        copied += 1
        by_category[dest_dir] = by_category.get(dest_dir, 0) + 1

    print()
    print(f"Copied: {copied}")
    print(f"Skipped (up to date): {skipped_uptodate}")
    if skipped_hero:
        print(f"Skipped (hero art — never auto-generated): {skipped_hero}")
    if skipped_unknown:
        print(f"Skipped (unknown prefix): {skipped_unknown}")
    if by_category:
        print("By destination:")
        for d, n in sorted(by_category.items()):
            print(f"  {os.path.relpath(d, REPO_ROOT)}: {n}")


if __name__ == "__main__":
    main()
