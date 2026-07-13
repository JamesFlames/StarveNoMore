"""
Generate the save-file cover art: saves/StarveNoMore.png.

Tabletop Simulator's Save & Load browser shows a PNG that sits next to the
save JSON with the same basename — that PNG *is* the mod's cover art for
anyone browsing their saves. Coco's hand-drawn front standee is the face
of the mod (per direction 2026-07): the full framed portrait, centered on
a dark 16:9 suburban-night backdrop with the title split around it.

The output is committed; iwanttoplay.py copies it next to the save it
installs into the TTS saves folder. Deterministic — rerun only when the
cover should change (new standee art, new title treatment).

Run: python scripts/generate_cover.py
Output: saves/StarveNoMore.png
"""

import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COCO = os.path.join(ROOT, "art", "characters", "coco_front.png")
OUT = os.path.join(ROOT, "saves", "StarveNoMore.png")

W, H = 1280, 720

NIGHT_TOP = (10, 9, 16)
NIGHT_BOTTOM = (36, 29, 42)
GLOW = (196, 168, 110)      # parchment-warm halo behind the portrait
ROOF = (5, 4, 9)
WINDOW = (196, 160, 70)
TITLE = (222, 210, 185)
SUB = (150, 138, 120)
OUTLINE = (8, 6, 12)


def load_font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/georgiab.ttf" if bold else "C:/Windows/Fonts/georgia.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def main():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # Night-sky vertical gradient.
    for y in range(H):
        t = y / H
        draw.line([(0, y), (W, y)], fill=tuple(
            int(a + (b - a) * t) for a, b in zip(NIGHT_TOP, NIGHT_BOTTOM)))

    # Warm glow where the portrait will sit, so the parchment card reads
    # as lit from within against the night.
    glow = Image.new("L", (W, H), 0)
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([W // 2 - 300, 30, W // 2 + 300, H - 10], fill=110)
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img = Image.composite(Image.new("RGB", (W, H), GLOW), img, glow)
    draw = ImageDraw.Draw(img)

    # Suburban rooftop silhouette along the bottom (deterministic skyline).
    rng = random.Random(7)
    baseline = H - 84
    x = -20
    while x < W + 40:
        w = rng.randint(90, 170)
        h = rng.randint(40, 120)
        top = baseline - h
        if rng.random() < 0.7:
            draw.polygon([(x, baseline), (x, top + 24), (x + w // 2, top),
                          (x + w, top + 24), (x + w, baseline)], fill=ROOF)
        else:
            draw.rectangle([x, top, x + w, baseline], fill=ROOF)
        for _ in range(rng.randint(0, 2)):
            wx = x + rng.randint(12, max(13, w - 24))
            wy = top + rng.randint(18, max(19, h - 20))
            draw.rectangle([wx, wy, wx + 9, wy + 12], fill=WINDOW)
        x += w + rng.randint(6, 28)
    draw.rectangle([0, baseline, W, H], fill=ROOF)

    # Coco's framed standee portrait, centered. It is a finished card in
    # its own right (border, banner, name) — no cutout, just presence.
    coco = Image.open(COCO).convert("RGB")
    target_h = 664
    coco = coco.resize((int(coco.width * target_h / coco.height), target_h),
                       Image.LANCZOS)
    cx = (W - coco.width) // 2
    cy = (H - coco.height) // 2

    # Soft drop shadow behind the card.
    shadow = Image.new("L", (W, H), 0)
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rectangle([cx + 12, cy + 14, cx + coco.width + 12, cy + coco.height + 14],
                    fill=170)
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, shadow)
    img.paste(coco, (cx, cy))
    draw = ImageDraw.Draw(img)

    # Title split around the portrait: STARVE | NO MORE. Each side is
    # auto-fitted to the space beside the card so nothing ever clips.
    font_sub = load_font(24)

    def outlined(pos, text, font, fill):
        ox, oy = pos
        for dx in (-3, 0, 3):
            for dy in (-3, 0, 3):
                if dx or dy:
                    draw.text((ox + dx, oy + dy), text, font=font, fill=OUTLINE)
        draw.text(pos, text, font=font, fill=fill)

    def fitted_font(text, max_width, start=92):
        size = start
        while size > 24:
            font = load_font(size, bold=True)
            box = draw.textbbox((0, 0), text, font=font)
            if box[2] - box[0] <= max_width:
                return font
            size -= 4
        return load_font(24, bold=True)

    def centered_in(text, x0, x1, y):
        pad = 36
        font = fitted_font(text, (x1 - x0) - pad * 2)
        box = draw.textbbox((0, 0), text, font=font)
        outlined((x0 + (x1 - x0 - (box[2] - box[0])) // 2, y), text, font, TITLE)

    centered_in("STARVE", 0, cx, 150)
    centered_in("NO MORE", cx + coco.width, W, 150)

    tagline = "Five friends. Seven days. One neighborhood in the dark."
    box = draw.textbbox((0, 0), tagline, font=font_sub)
    outlined(((W - (box[2] - box[0])) // 2, H - 44), tagline, font_sub, SUB)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({W}x{H})")


if __name__ == "__main__":
    main()
