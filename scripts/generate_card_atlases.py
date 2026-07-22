"""
Generate card atlas images for Starve No More from CSV data.
Produces face atlases (grid of individual cards) and back images for every deck.

Each card face = top art region (full-bleed illustration) + bottom text panel.
Illustrations come from `art/decks/illustrations/<card_id>.png`, populated by:
  1. python scripts/generate_comfyui_assets.py
  2. python scripts/sync_comfyui_output.py

If an illustration is missing, the art region falls back to a flat colored
rectangle so partial generations don't break the atlas build.

Run: python scripts/generate_card_atlases.py
Output: art/decks/*_face.jpg (atlases) + art/decks/*_back.png (backs)
"""

import csv
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
OUT = os.path.join(ROOT, "art", "decks")
ILLUSTRATIONS_DIR = os.path.join(OUT, "illustrations")

# Card dimensions (TTS standard for custom decks)
CARD_W = 408
CARD_H = 585

# Layout split: top region holds the illustration, bottom holds the text panel.
ART_H = 380
TEXT_Y = ART_H              # text panel starts here
TEXT_H = CARD_H - ART_H     # 205

# ---------------------------------------------------------------------------
# Color palette — Tim Burton / Edward Gorey muted earth tones
# ---------------------------------------------------------------------------
PALETTE = {
    "bg":          (30, 28, 26),       # near-black card bg
    "bg_light":    (45, 42, 38),       # slightly lighter panel
    "border":      (80, 72, 60),       # warm brown border
    "title_bg":    (55, 48, 40),       # title bar background
    "text":        (220, 210, 190),    # warm off-white body text
    "title_text":  (255, 230, 180),    # warm gold title
    "cost_text":   (180, 200, 160),    # muted green for costs
    "severity_on": (200, 60, 50),      # filled dot (red)
    "severity_off":(70, 65, 58),       # empty dot
    "accent_red":  (180, 50, 40),      # danger accent
    "accent_blue": (60, 100, 140),     # cool accent
    "accent_green":(70, 130, 70),      # gain accent
    "accent_gold": (180, 150, 60),     # gold accent
    "phase1":      (70, 85, 100),      # Dusk of the Week — slate blue
    "phase2":      (90, 70, 90),       # Strange Days — muted purple
    "phase3":      (50, 60, 80),       # Long Nights — dark navy
    "phase4":      (100, 50, 40),      # Final Hours — dark red
    "market":      (60, 75, 55),       # Market — forest green
    "recipe":      (90, 70, 45),       # Recipe — warm brown
    "threat":      (85, 40, 40),       # Threat — blood red
    "visitor":     (55, 75, 90),       # Visitor — sky blue
    "trophy":      (90, 80, 40),       # Trophy — burnished gold
    "starting":    (70, 65, 90),       # Starting item — dusk violet
}

# ---------------------------------------------------------------------------
# Font loading — try system fonts, fall back to default
# ---------------------------------------------------------------------------
def load_font(size, bold=False):
    """Try to load a readable font. Falls back to Pillow default."""
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ]
    if bold:
        candidates = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ] + candidates
    for path in candidates:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

FONT_TITLE   = load_font(24, bold=True)
FONT_BODY    = load_font(16)
FONT_SMALL   = load_font(13)
FONT_LABEL   = load_font(12)

# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def draw_rounded_rect(draw, xy, radius, fill, outline=None):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)

def draw_severity_dots(draw, x, y, severity, max_dots=5, size=10, gap=14):
    """Draw severity dots (filled=red, empty=grey) horizontally."""
    for i in range(max_dots):
        cx = x + i * gap
        color = PALETTE["severity_on"] if i < severity else PALETTE["severity_off"]
        draw.ellipse([cx, y, cx + size, y + size], fill=color)

def wrap_text(text, font, max_width, draw):
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def draw_wrapped_text(draw, x, y, text, font, color, max_width, max_lines=None):
    lines = wrap_text(text, font, max_width, draw)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:max(0, len(lines[-1])-3)] + "..."
    line_height = font.size + 3
    for line in lines:
        draw.text((x, y), line, fill=color, font=font)
        y += line_height
    return y

# ---------------------------------------------------------------------------
# Layout primitives — illustration paste + text panel chrome
# ---------------------------------------------------------------------------
def paste_card_art(img, card_id, accent_color):
    """Paste illustrations/<card_id>.png cover-cropped to (CARD_W, ART_H).

    Falls back to a flat colored rectangle if the illustration is missing.
    Returns True if a real illustration was used, False on fallback.
    """
    path = os.path.join(ILLUSTRATIONS_DIR, f"{card_id}.png")
    if os.path.isfile(path):
        try:
            art = Image.open(path).convert("RGB")
            # Cover-crop: scale so the shorter dimension fills, then center-crop.
            target_ratio = CARD_W / ART_H
            src_ratio = art.size[0] / art.size[1]
            if src_ratio > target_ratio:
                # Source is wider; scale by height, then crop sides.
                new_h = ART_H
                new_w = int(round(art.size[0] * (ART_H / art.size[1])))
                art = art.resize((new_w, new_h), Image.LANCZOS)
                left = (new_w - CARD_W) // 2
                art = art.crop((left, 0, left + CARD_W, ART_H))
            else:
                # Source is taller; scale by width, then crop top/bottom.
                new_w = CARD_W
                new_h = int(round(art.size[1] * (CARD_W / art.size[0])))
                art = art.resize((new_w, new_h), Image.LANCZOS)
                top = (new_h - ART_H) // 2
                art = art.crop((0, top, CARD_W, top + ART_H))
            img.paste(art, (0, 0))
            return True
        except Exception as e:
            print(f"  warn: failed to load {path}: {e}")
    # Fallback: flat colored rectangle in the deck's accent color.
    fallback = Image.new("RGB", (CARD_W, ART_H), accent_color)
    img.paste(fallback, (0, 0))
    return False

def draw_text_panel(img, draw, accent_color):
    """Paint the bottom text-panel background and a divider line."""
    draw.rectangle([0, TEXT_Y, CARD_W, CARD_H], fill=PALETTE["bg"])
    # Accent divider line where art meets panel.
    draw.line([0, TEXT_Y, CARD_W, TEXT_Y], fill=accent_color, width=2)

def draw_title_row(draw, title, accent_color, severity=None):
    """Title at left of panel, optional severity dots at right. Returns next y."""
    # Title text
    draw.text((12, TEXT_Y + 8), title, fill=PALETTE["title_text"], font=FONT_TITLE)
    # Severity dots, top-right of panel
    if severity is not None:
        draw_severity_dots(draw, CARD_W - 90, TEXT_Y + 14, severity)
    return TEXT_Y + 36  # next available y for sub-label or content

def draw_kicker(draw, text, color, y):
    """Small uppercase 'kicker' label like RECIPE / VISITOR / SOFT THREAT."""
    draw.text((12, y), text.upper(), fill=color, font=FONT_SMALL)
    return y + 16

def draw_card_id_footer(draw, card_id):
    """Footer card ID at bottom-left of card."""
    draw.text((12, CARD_H - 16), card_id, fill=PALETTE["border"], font=FONT_LABEL)

# ---------------------------------------------------------------------------
# Card renderers — one per deck type. Each:
#   1. Creates a blank card.
#   2. Pastes art on top.
#   3. Draws the text panel below.
# ---------------------------------------------------------------------------
def render_phase_card(row, phase_num):
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    accent = PALETTE.get(f"phase{phase_num}", PALETTE["border"])
    card_id = row.get("id", "")

    paste_card_art(img, card_id, accent)
    draw_text_panel(img, draw, accent)

    sev = int(row.get("severity") or 1)
    title = row.get("title", "Unknown")
    y = draw_title_row(draw, title, accent, severity=sev)
    y = draw_kicker(draw, f"PHASE {phase_num} • DAWN", accent, y)

    # Combine immediate + ongoing text, separated.
    imm = (row.get("immediate") or "").strip()
    ong = (row.get("ongoing") or "").strip()
    body_x = 12
    body_w = CARD_W - 24
    body_y = y + 4
    if imm:
        body_y = draw_wrapped_text(draw, body_x, body_y, imm,
                                   FONT_BODY, PALETTE["text"], body_w, max_lines=4)
    if ong:
        body_y += 2
        body_y = draw_wrapped_text(draw, body_x, body_y, "↻ " + ong,
                                   FONT_BODY, PALETTE["cost_text"], body_w, max_lines=3)

    draw_card_id_footer(draw, card_id)
    return img

def render_market_card(row):
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    accent = PALETTE["market"]
    card_id = row.get("id", "")

    paste_card_art(img, card_id, accent)
    draw_text_panel(img, draw, accent)

    name = row.get("name", "?")
    y = draw_title_row(draw, name, accent)

    cat = (row.get("category") or "Item").upper()
    persistent = (row.get("persistent") or "").upper() == "Y"
    sub = f"{cat} • PERSIST" if persistent else cat
    y = draw_kicker(draw, sub, accent, y)

    cost = (row.get("cost") or "").strip()
    if cost:
        draw.text((12, y), "Cost:", fill=PALETTE["accent_gold"], font=FONT_SMALL)
        draw.text((46, y - 1), cost, fill=PALETTE["cost_text"], font=FONT_BODY)
        y += 16

    effect = (row.get("effect") or "").strip()
    if effect:
        draw_wrapped_text(draw, 12, y, effect,
                          FONT_BODY, PALETTE["text"], CARD_W - 24, max_lines=5)

    draw_card_id_footer(draw, card_id)
    return img

def render_recipe_card(row):
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    accent = PALETTE["recipe"]
    card_id = row.get("id", "")

    paste_card_art(img, card_id, accent)
    draw_text_panel(img, draw, accent)

    y = draw_title_row(draw, row.get("name", "?"), accent)
    y = draw_kicker(draw, "RECIPE", accent, y)

    ing = (row.get("ingredients") or "").strip()
    if ing:
        draw.text((12, y), "Ingredients:", fill=PALETTE["accent_gold"], font=FONT_SMALL)
        y += 14
        y = draw_wrapped_text(draw, 12, y, ing,
                              FONT_BODY, PALETTE["cost_text"], CARD_W - 24, max_lines=2)
        y += 2

    cost = (row.get("cost") or "").strip()
    if cost:
        draw.text((12, y), "Cost:", fill=PALETTE["accent_red"], font=FONT_SMALL)
        draw.text((46, y - 1), cost, fill=PALETTE["text"], font=FONT_BODY)
        y += 16

    effect = (row.get("effect") or "").strip()
    if effect:
        draw_wrapped_text(draw, 12, y, effect,
                          FONT_BODY, PALETTE["text"], CARD_W - 24, max_lines=4)

    draw_card_id_footer(draw, card_id)
    return img

def render_threat_card(row):
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    accent = PALETTE["threat"]
    card_id = row.get("id", "")

    paste_card_art(img, card_id, accent)
    draw_text_panel(img, draw, accent)

    sev = int(row.get("severity") or 2)
    y = draw_title_row(draw, row.get("name", "?"), accent, severity=sev)

    ttype = (row.get("type") or "Hard").upper()
    hp = (row.get("hp") or "0").strip()
    atk = (row.get("attack") or "0").strip()
    sub = ttype
    if hp != "0" or atk != "0":
        sub += f"  •  HP {hp}  •  ATK {atk}"
    y = draw_kicker(draw, sub, accent, y)

    special = (row.get("special") or "").strip()
    if special:
        draw_wrapped_text(draw, 12, y, special,
                          FONT_BODY, PALETTE["text"], CARD_W - 24, max_lines=6)

    draw_card_id_footer(draw, card_id)
    return img

def render_visitor_card(row):
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    accent = PALETTE["visitor"]
    card_id = row.get("id", "")

    paste_card_art(img, card_id, accent)
    draw_text_panel(img, draw, accent)

    y = draw_title_row(draw, row.get("character", "?"), accent)
    y = draw_kicker(draw, "VISITOR", accent, y)

    trig = (row.get("trigger") or "").strip()
    if trig:
        y = draw_wrapped_text(draw, 12, y, "Trigger: " + trig,
                              FONT_BODY, PALETTE["text"], CARD_W - 24, max_lines=2)
        y += 2

    imm = (row.get("immediate") or "").strip()
    if imm:
        y = draw_wrapped_text(draw, 12, y, imm,
                              FONT_BODY, PALETTE["accent_green"], CARD_W - 24, max_lines=3)
        y += 2

    dep = (row.get("departure") or "").strip()
    if dep:
        draw_wrapped_text(draw, 12, y, "Leaves: " + dep,
                          FONT_BODY, PALETTE["cost_text"], CARD_W - 24, max_lines=2)

    draw_card_id_footer(draw, card_id)
    return img

def render_starting_card(row):
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    accent = PALETTE["starting"]
    card_id = row.get("id", "")

    paste_card_art(img, card_id, accent)
    draw_text_panel(img, draw, accent)

    y = draw_title_row(draw, row.get("name", "?"), accent)
    y = draw_kicker(draw, f"STARTING ITEM • {row.get('character', '?')}", accent, y)

    effect = (row.get("effect") or "").strip()
    if effect:
        draw_wrapped_text(draw, 12, y, effect,
                          FONT_BODY, PALETTE["text"], CARD_W - 24, max_lines=6)

    draw_card_id_footer(draw, card_id)
    return img

def render_trophy_card(row):
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    accent = PALETTE["trophy"]
    card_id = row.get("id", "")

    paste_card_art(img, card_id, accent)
    draw_text_panel(img, draw, accent)

    y = draw_title_row(draw, row.get("boss", "?"), accent)
    y = draw_kicker(draw, "TROPHY", accent, y)

    bonus = (row.get("bonus") or "").strip()
    if bonus:
        draw_wrapped_text(draw, 12, y, bonus,
                          FONT_BODY, PALETTE["text"], CARD_W - 24, max_lines=6)

    draw_card_id_footer(draw, card_id)
    return img

# ---------------------------------------------------------------------------
# Card back renderers — unchanged; cards still have a deck-themed back.
# ---------------------------------------------------------------------------
def render_card_back(label, color_key):
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    color = PALETTE.get(color_key, PALETTE["border"])

    draw.rectangle([0, 0, CARD_W-1, CARD_H-1], outline=color, width=4)
    draw.rectangle([12, 12, CARD_W-12, CARD_H-12], outline=PALETTE["border"], width=2)

    for offset in range(-CARD_H, CARD_W, 30):
        draw.line([offset, 0, offset + CARD_H, CARD_H], fill=(40, 38, 35), width=1)

    cx, cy = CARD_W // 2, CARD_H // 2
    panel_w, panel_h = 200, 80
    draw_rounded_rect(draw,
        [cx - panel_w//2, cy - panel_h//2, cx + panel_w//2, cy + panel_h//2],
        10, fill=PALETTE["title_bg"], outline=color)

    bbox = draw.textbbox((0, 0), label, font=FONT_TITLE)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw//2, cy - 18), label, fill=PALETTE["title_text"], font=FONT_TITLE)

    sub = "STARVE NO MORE"
    bbox2 = draw.textbbox((0, 0), sub, font=FONT_SMALL)
    tw2 = bbox2[2] - bbox2[0]
    draw.text((cx - tw2//2, cy + 10), sub, fill=color, font=FONT_SMALL)

    return img

# ---------------------------------------------------------------------------
# Atlas builder
# ---------------------------------------------------------------------------
def grid_for(n):
    """Smallest near-square grid that holds n cards.

    Derived, never declared: adding a card to a CSV can no longer overflow a
    hand-maintained grid. TTS CustomDeck constraints: 2..10 columns/rows.
    build_save.py reads the resulting atlas_manifest.json for NumWidth/NumHeight.
    """
    cols = min(10, max(2, math.ceil(math.sqrt(n))))
    rows = max(2, math.ceil(n / cols))
    if rows > 10:
        raise SystemExit(f"deck of {n} cards exceeds a 10x10 TTS atlas — split the deck")
    return cols, rows


def build_atlas(cards, num_w, num_h):
    atlas = Image.new("RGB", (num_w * CARD_W, num_h * CARD_H), (20, 18, 16))
    for i, card_img in enumerate(cards):
        col = i % num_w
        row = i // num_w
        if row >= num_h:
            break
        atlas.paste(card_img, (col * CARD_W, row * CARD_H))
    return atlas

# ---------------------------------------------------------------------------
# CSV reader
# ---------------------------------------------------------------------------
def read_csv(filename):
    path = os.path.join(CONTENT, filename)
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(ILLUSTRATIONS_DIR, exist_ok=True)

    art_present = 0
    art_missing = 0

    def render_with_count(render_fn, rows, *args):
        nonlocal art_present, art_missing
        out = []
        for r in rows:
            cid = r.get("id", "")
            if cid and os.path.isfile(os.path.join(ILLUSTRATIONS_DIR, f"{cid}.png")):
                art_present += 1
            else:
                art_missing += 1
            out.append(render_fn(r, *args))
        return out

    # --- All decks: grid derived from card count; manifest records it so
    # --- build_save.py can never disagree with the rendered atlas.
    manifest = {}

    def build_deck(csv_name, face_base, label, cards):
        cols, rows_n = grid_for(len(cards))
        atlas = build_atlas(cards, cols, rows_n)
        # JPEG at q88 with 4:4:4 chroma (no subsampling) keeps card text crisp
        # at ~1/5 the bytes of PNG; the atlases have no alpha so nothing is lost.
        atlas.save(os.path.join(OUT, f"{face_base}_face.jpg"),
                   quality=88, subsampling=0, optimize=True)
        manifest[csv_name] = {"cards": len(cards), "cols": cols, "rows": rows_n,
                              "face": f"{face_base}_face.jpg"}
        print(f"{label} face: {len(cards)} cards -> {cols}x{rows_n} atlas "
              f"({atlas.size[0]}x{atlas.size[1]})")

    for phase_num in range(1, 5):
        rows = read_csv(f"cards_phase{phase_num}.csv")
        build_deck(f"cards_phase{phase_num}.csv", f"phase{phase_num}", f"Phase {phase_num}",
                   render_with_count(render_phase_card, rows, phase_num))
        render_card_back(f"PHASE {phase_num}", f"phase{phase_num}").save(
            os.path.join(OUT, f"phase{phase_num}_back.png"))

    build_deck("cards_market.csv", "market", "Market",
               render_with_count(render_market_card, read_csv("cards_market.csv")))
    render_card_back("MARKET", "market").save(os.path.join(OUT, "market_back.png"))

    build_deck("cards_recipes.csv", "recipe", "Recipe",
               render_with_count(render_recipe_card, read_csv("cards_recipes.csv")))
    render_card_back("RECIPE", "recipe").save(os.path.join(OUT, "recipe_back.png"))

    build_deck("cards_threats.csv", "threat", "Threat",
               render_with_count(render_threat_card, read_csv("cards_threats.csv")))
    render_card_back("THREAT", "threat").save(os.path.join(OUT, "threat_back.png"))

    build_deck("cards_visitors.csv", "visitor", "Visitor",
               render_with_count(render_visitor_card, read_csv("cards_visitors.csv")))
    render_card_back("VISITOR", "visitor").save(os.path.join(OUT, "visitor_back.png"))

    build_deck("cards_trophies.csv", "trophy", "Trophy",
               render_with_count(render_trophy_card, read_csv("cards_trophies.csv")))
    render_card_back("TROPHY", "trophy").save(os.path.join(OUT, "trophy_back.png"))

    build_deck("cards_starting.csv", "starting", "Starting items",
               render_with_count(render_starting_card, read_csv("cards_starting.csv")))
    render_card_back("STARTING", "starting").save(os.path.join(OUT, "starting_back.png"))

    manifest_path = os.path.join(OUT, "atlas_manifest.json")
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Atlas manifest written: {manifest_path}")

    print()
    print(f"Illustrations: {art_present} present, {art_missing} missing (using fallback rectangles)")
    print(f"All atlases written to: {OUT}")
    print("Total: 10 face atlases + 10 back images = 20 files")

if __name__ == "__main__":
    main()
