"""
Build the achievement icon set from content/achievements.csv.

Two modes, decided per achievement, automatically:

  ComfyUI art present   art/achievements/src/<base>.png exists (put there by
                        scripts/sync_comfyui_output.py after a ComfyUI run)
                        -> cropped square, resized, vignetted, framed.

  No art yet            -> a procedural placeholder in the game's palette:
                        the category's colour, the achievement's initials, a
                        hand-drawn-ish frame. Deliberately plain, so it is
                        obvious at a glance which icons still need art.

Either way every icon ends up at the same three sizes, so the mod, the panel
and a future Steamworks upload all read from one build:

  art/achievements/<base>.png              256x256  in-game (CustomUIAssets)
  art/achievements/steam/<base>.jpg        256x256  Steamworks "icon"
  art/achievements/steam/<base>_gray.jpg    64x64   Steamworks "icon_gray"

Plus art/achievements/locked.png — the placeholder the XML ships with, shown
before the Lua swaps in a real row icon.

Run: python scripts/generate_achievement_icons.py [--only A_ID] [--force]
"""

import argparse
import csv
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(REPO_ROOT, "content", "achievements.csv")
OUT_DIR = os.path.join(REPO_ROOT, "art", "achievements")
SRC_DIR = os.path.join(OUT_DIR, "src")
STEAM_DIR = os.path.join(OUT_DIR, "steam")

ICON_SIZE = 256
GRAY_SIZE = 64

# Palette shared with scripts/generate_assets.py — the icons have to sit next
# to the tokens and the board without looking like a different game.
PAL = {
    "bg":       (30, 28, 26),
    "bg_light": (45, 42, 38),
    "border":   (80, 72, 60),
    "text":     (220, 210, 190),
    "gold":     (180, 150, 60),
}

# One accent per category, so a page of the panel reads as a group.
CATEGORY_COLORS = {
    "Progress": (60, 120, 200),
    "Mastery":  (180, 150, 60),
    "Bosses":   (200, 60, 50),
    "Habits":   (70, 160, 70),
    "Secret":   (120, 80, 160),
}
DEFAULT_ACCENT = (140, 140, 140)


def load_font(size, bold=True):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def icon_base(aid):
    return aid[2:].lower()


def initials(name):
    """'Down to the Wire' -> 'DW'; 'Timber' -> 'TI'. Two characters, so the
    placeholder stays legible at 46px in the panel."""
    words = [w for w in name.replace("'", "").split() if w[:1].isalnum()]
    big = [w for w in words if w.lower() not in ("the", "a", "of", "to", "my", "in", "and")]
    src = big or words
    if len(src) >= 2:
        return (src[0][0] + src[1][0]).upper()
    if src:
        return src[0][:2].upper()
    return "??"


def centered(draw, cx, cy, text, font, fill):
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (r - l) / 2 - l, cy - (b - t) / 2 - t), text, fill=fill, font=font)


def frame(img, accent):
    """The common furniture: inner vignette + a two-tone border. Applied to
    generated art and placeholders alike so the set looks like a set."""
    d = ImageDraw.Draw(img)
    s = img.size[0]

    vignette = Image.new("L", (s, s), 0)
    ImageDraw.Draw(vignette).ellipse(
        (-s * 0.15, -s * 0.15, s * 1.15, s * 1.15), fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(s * 0.12))
    shade = Image.new("RGB", (s, s), PAL["bg"])
    img.paste(Image.composite(img, shade, vignette))

    edge = max(2, s // 64)
    d.rectangle((0, 0, s - 1, s - 1), outline=PAL["border"], width=edge)
    d.rectangle((edge + 1, edge + 1, s - edge - 2, s - edge - 2),
                outline=accent, width=max(1, edge // 2))
    return img


def from_source(path, accent):
    """Centre-crop the ComfyUI render to square and dress it."""
    img = Image.open(path).convert("RGB")
    w, h = img.size
    side = min(w, h)
    img = img.crop(((w - side) // 2, (h - side) // 2,
                    (w - side) // 2 + side, (h - side) // 2 + side))
    img = img.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
    return frame(img, accent)


def placeholder(name, category, accent):
    img = Image.new("RGB", (ICON_SIZE, ICON_SIZE), PAL["bg_light"])
    d = ImageDraw.Draw(img)

    # A soft accent wash from the bottom, so the flat fill has some depth.
    for y in range(ICON_SIZE):
        t = (y / ICON_SIZE) ** 2 * 0.35
        d.line(
            [(0, y), (ICON_SIZE, y)],
            fill=tuple(int(PAL["bg_light"][i] * (1 - t) + accent[i] * t) for i in range(3)),
        )

    d.ellipse((44, 40, ICON_SIZE - 44, ICON_SIZE - 60), outline=accent, width=3)
    centered(d, ICON_SIZE // 2, 118, initials(name), load_font(84), PAL["text"])
    centered(d, ICON_SIZE // 2, 214, category.upper(), load_font(20), accent)
    return frame(img, accent)


def write_variants(img, base):
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(STEAM_DIR, exist_ok=True)
    img.save(os.path.join(OUT_DIR, f"{base}.png"))
    img.save(os.path.join(STEAM_DIR, f"{base}.jpg"), quality=92)
    gray = img.convert("L").convert("RGB").resize((GRAY_SIZE, GRAY_SIZE), Image.LANCZOS)
    gray = Image.blend(gray, Image.new("RGB", gray.size, PAL["bg"]), 0.45)
    gray.save(os.path.join(STEAM_DIR, f"{base}_gray.jpg"), quality=92)


def write_locked_placeholder():
    """The one icon the XML names literally: what a row shows before the Lua
    has swapped in a real achievement's art."""
    img = Image.new("RGB", (ICON_SIZE, ICON_SIZE), PAL["bg"])
    d = ImageDraw.Draw(img)
    cx = ICON_SIZE // 2
    d.rounded_rectangle((cx - 46, 122, cx + 46, 200), radius=10,
                        outline=PAL["border"], width=6)
    d.arc((cx - 32, 66, cx + 32, 158), start=180, end=360,
          fill=PAL["border"], width=12)
    d.ellipse((cx - 10, 148, cx + 10, 168), fill=PAL["border"])
    frame(img, PAL["border"])
    img.save(os.path.join(OUT_DIR, "locked.png"))


def main():
    ap = argparse.ArgumentParser(description="Build achievement icons.")
    ap.add_argument("--only", default=None, help="one achievement id (e.g. A_HERO)")
    ap.add_argument("--force", action="store_true",
                    help="rebuild even when the output is newer than its source")
    args = ap.parse_args()

    if not os.path.isfile(CSV_PATH):
        raise SystemExit(f"missing source: {CSV_PATH}")

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(SRC_DIR, exist_ok=True)

    from_art, from_placeholder, skipped = 0, 0, 0
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            aid = (row.get("id") or "").strip()
            if not aid or (args.only and aid != args.only):
                continue
            base = icon_base(aid)
            accent = CATEGORY_COLORS.get((row.get("category") or "").strip(), DEFAULT_ACCENT)
            src = os.path.join(SRC_DIR, f"{base}.png")
            dest = os.path.join(OUT_DIR, f"{base}.png")

            if os.path.isfile(src):
                if (not args.force and os.path.isfile(dest)
                        and os.path.getmtime(dest) >= os.path.getmtime(src)):
                    skipped += 1
                    continue
                write_variants(from_source(src, accent), base)
                from_art += 1
            else:
                if not args.force and os.path.isfile(dest):
                    # A placeholder already stands in; leave it. --force
                    # rebuilds it (e.g. after a palette or wording change).
                    skipped += 1
                    continue
                write_variants(
                    placeholder(row.get("name", aid), (row.get("category") or "").strip(), accent),
                    base)
                from_placeholder += 1

    write_locked_placeholder()

    print(f"wrote {os.path.relpath(OUT_DIR, REPO_ROOT)}/")
    print(f"  from ComfyUI art: {from_art}")
    print(f"  placeholders:     {from_placeholder}")
    print(f"  up to date:       {skipped}")
    if from_placeholder:
        print()
        print("Placeholders are stand-ins. To replace them with real art:")
        print("  1. python scripts/generate_comfyui_assets.py --achievements-only")
        print("  2. python scripts/sync_comfyui_output.py")
        print("  3. python scripts/generate_achievement_icons.py")
        print("  See docs/comfyui-achievement-icons.md for the whole run book.")


if __name__ == "__main__":
    main()
