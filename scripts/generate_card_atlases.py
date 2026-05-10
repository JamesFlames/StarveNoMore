"""
Generate card atlas images for Starve No More from CSV data.
Produces face atlases (grid of individual cards) and back images for every deck.
Run: python scripts/generate_card_atlases.py
Output: art/decks/*.png
"""

import csv, os, textwrap, math
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
OUT = os.path.join(ROOT, "art", "decks")

# Card dimensions (TTS standard for custom decks)
CARD_W = 408
CARD_H = 585

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
}

# ---------------------------------------------------------------------------
# Font loading — try system fonts, fall back to default
# ---------------------------------------------------------------------------
def load_font(size, bold=False):
    """Try to load a readable font. Falls back to Pillow default."""
    candidates = [
        # Windows
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ]
    if bold:
        # Prefer bold variants first
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

FONT_TITLE = load_font(22, bold=True)
FONT_BODY = load_font(15)
FONT_SMALL = load_font(12)
FONT_SEVERITY = load_font(18, bold=True)
FONT_LABEL = load_font(11)

# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def draw_rounded_rect(draw, xy, radius, fill, outline=None):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)

def draw_severity_dots(draw, x, y, severity, max_dots=5):
    """Draw severity dots (filled=red, empty=grey)."""
    for i in range(max_dots):
        cx = x + i * 18
        cy = y
        color = PALETTE["severity_on"] if i < severity else PALETTE["severity_off"]
        draw.ellipse([cx, cy, cx + 12, cy + 12], fill=color)

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
    """Draw word-wrapped text, return final y position."""
    lines = wrap_text(text, font, max_width, draw)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:max(0, len(lines[-1])-3)] + "..."
    line_height = font.size + 4
    for line in lines:
        draw.text((x, y), line, fill=color, font=font)
        y += line_height
    return y

# ---------------------------------------------------------------------------
# Card renderers — one per deck type
# ---------------------------------------------------------------------------

def render_phase_card(row, phase_num):
    """Render a single Phase/Dawn card."""
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)

    phase_color = PALETTE.get(f"phase{phase_num}", PALETTE["border"])

    # Border
    draw.rectangle([0, 0, CARD_W-1, CARD_H-1], outline=phase_color, width=3)

    # Title bar
    draw_rounded_rect(draw, [8, 8, CARD_W-8, 52], 6, fill=PALETTE["title_bg"], outline=phase_color)

    # Phase label
    phase_names = {1: "PHASE I", 2: "PHASE II", 3: "PHASE III", 4: "PHASE IV"}
    draw.text((16, 12), phase_names.get(phase_num, "DAWN"), fill=phase_color, font=FONT_SMALL)

    # Title
    title = row.get("title", "Unknown")
    draw.text((16, 28), title, fill=PALETTE["title_text"], font=FONT_TITLE)

    # Severity dots (top right)
    sev = int(row.get("severity", 1))
    draw_severity_dots(draw, CARD_W - 108, 16, sev)

    # Divider line
    draw.line([16, 58, CARD_W-16, 58], fill=phase_color, width=1)

    # Immediate effect
    y = 70
    imm = row.get("immediate", "")
    if imm:
        draw.text((16, y), "IMMEDIATE:", fill=PALETTE["accent_red"], font=FONT_SMALL)
        y += 18
        y = draw_wrapped_text(draw, 16, y, imm, FONT_BODY, PALETTE["text"], CARD_W - 32, max_lines=8)
        y += 8

    # Ongoing effect
    ongoing = row.get("ongoing", "")
    if ongoing:
        draw.line([16, y, CARD_W-16, y], fill=PALETTE["border"], width=1)
        y += 8
        draw.text((16, y), "ONGOING:", fill=PALETTE["accent_gold"], font=FONT_SMALL)
        y += 18
        y = draw_wrapped_text(draw, 16, y, ongoing, FONT_BODY, PALETTE["cost_text"], CARD_W - 32, max_lines=6)

    # Card ID at bottom
    draw.text((16, CARD_H - 24), row.get("id", ""), fill=PALETTE["border"], font=FONT_LABEL)

    return img

def render_market_card(row):
    """Render a single Market card."""
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    color = PALETTE["market"]

    draw.rectangle([0, 0, CARD_W-1, CARD_H-1], outline=color, width=3)

    # Title bar
    draw_rounded_rect(draw, [8, 8, CARD_W-8, 52], 6, fill=PALETTE["title_bg"], outline=color)

    # Category label
    cat = row.get("category", "Item")
    draw.text((16, 12), cat.upper(), fill=color, font=FONT_SMALL)

    # Name
    draw.text((16, 28), row.get("name", "?"), fill=PALETTE["title_text"], font=FONT_TITLE)

    # Persistent badge
    if row.get("persistent", "").upper() == "Y":
        badge_x = CARD_W - 80
        draw_rounded_rect(draw, [badge_x, 14, CARD_W-12, 34], 4, fill=PALETTE["accent_blue"])
        draw.text((badge_x + 4, 16), "PERSIST", fill=(200, 220, 255), font=FONT_LABEL)

    draw.line([16, 58, CARD_W-16, 58], fill=color, width=1)

    # Cost
    y = 68
    cost = row.get("cost", "")
    if cost:
        draw.text((16, y), "COST:", fill=PALETTE["accent_gold"], font=FONT_SMALL)
        draw.text((60, y), cost, fill=PALETTE["cost_text"], font=FONT_BODY)
        y += 24

    # Divider
    draw.line([16, y, CARD_W-16, y], fill=PALETTE["border"], width=1)
    y += 10

    # Effect
    effect = row.get("effect", "")
    if effect:
        y = draw_wrapped_text(draw, 16, y, effect, FONT_BODY, PALETTE["text"], CARD_W - 32, max_lines=10)

    # Tooltip at bottom (smaller, dimmer)
    tooltip = row.get("tooltip", "")
    if tooltip:
        draw.line([16, CARD_H - 60, CARD_W-16, CARD_H - 60], fill=PALETTE["border"], width=1)
        draw_wrapped_text(draw, 16, CARD_H - 52, tooltip, FONT_LABEL, PALETTE["border"], CARD_W - 32, max_lines=3)

    draw.text((16, CARD_H - 24), row.get("id", ""), fill=PALETTE["border"], font=FONT_LABEL)
    return img

def render_recipe_card(row):
    """Render a single Recipe card."""
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    color = PALETTE["recipe"]

    draw.rectangle([0, 0, CARD_W-1, CARD_H-1], outline=color, width=3)
    draw_rounded_rect(draw, [8, 8, CARD_W-8, 52], 6, fill=PALETTE["title_bg"], outline=color)

    draw.text((16, 12), "RECIPE", fill=color, font=FONT_SMALL)
    draw.text((16, 28), row.get("name", "?"), fill=PALETTE["title_text"], font=FONT_TITLE)

    draw.line([16, 58, CARD_W-16, 58], fill=color, width=1)

    y = 68

    # Ingredients
    ingredients = row.get("ingredients", "")
    if ingredients:
        draw.text((16, y), "INGREDIENTS:", fill=PALETTE["accent_gold"], font=FONT_SMALL)
        y += 18
        y = draw_wrapped_text(draw, 16, y, ingredients, FONT_BODY, PALETTE["cost_text"], CARD_W - 32, max_lines=3)
        y += 6

    # Cost (action/health)
    cost = row.get("cost", "")
    if cost:
        draw.text((16, y), "COST:", fill=PALETTE["accent_red"], font=FONT_SMALL)
        draw.text((60, y), cost, fill=PALETTE["text"], font=FONT_BODY)
        y += 24

    draw.line([16, y, CARD_W-16, y], fill=PALETTE["border"], width=1)
    y += 10

    # Effect
    effect = row.get("effect", "")
    if effect:
        y = draw_wrapped_text(draw, 16, y, effect, FONT_BODY, PALETTE["text"], CARD_W - 32, max_lines=10)

    draw.text((16, CARD_H - 24), row.get("id", ""), fill=PALETTE["border"], font=FONT_LABEL)
    return img

def render_threat_card(row):
    """Render a single Threat card."""
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    color = PALETTE["threat"]

    draw.rectangle([0, 0, CARD_W-1, CARD_H-1], outline=color, width=3)
    draw_rounded_rect(draw, [8, 8, CARD_W-8, 52], 6, fill=PALETTE["title_bg"], outline=color)

    # Type label
    ttype = row.get("type", "Hard")
    draw.text((16, 12), ttype.upper(), fill=color, font=FONT_SMALL)

    draw.text((16, 28), row.get("name", "?"), fill=PALETTE["title_text"], font=FONT_TITLE)

    # Severity dots
    sev = int(row.get("severity", 2))
    draw_severity_dots(draw, CARD_W - 108, 16, sev)

    draw.line([16, 58, CARD_W-16, 58], fill=color, width=1)

    y = 68

    # Stats bar (HP / Attack)
    hp = row.get("hp", "0")
    atk = row.get("attack", "0")
    if int(hp) > 0:
        draw_rounded_rect(draw, [16, y, 120, y + 28], 4, fill=(60, 30, 30))
        draw.text((24, y + 4), f"HP: {hp}", fill=(255, 100, 100), font=FONT_BODY)
        draw_rounded_rect(draw, [130, y, 250, y + 28], 4, fill=(60, 30, 30))
        draw.text((138, y + 4), f"ATK: {atk} dice", fill=(255, 150, 100), font=FONT_BODY)
        y += 38

    # Special
    special = row.get("special", "")
    if special:
        draw.text((16, y), "SPECIAL:", fill=PALETTE["accent_gold"], font=FONT_SMALL)
        y += 18
        y = draw_wrapped_text(draw, 16, y, special, FONT_BODY, PALETTE["text"], CARD_W - 32, max_lines=10)

    draw.text((16, CARD_H - 24), row.get("id", ""), fill=PALETTE["border"], font=FONT_LABEL)
    return img

def render_visitor_card(row):
    """Render a single Visitor card."""
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    color = PALETTE["visitor"]

    draw.rectangle([0, 0, CARD_W-1, CARD_H-1], outline=color, width=3)
    draw_rounded_rect(draw, [8, 8, CARD_W-8, 52], 6, fill=PALETTE["title_bg"], outline=color)

    draw.text((16, 12), "VISITOR", fill=color, font=FONT_SMALL)
    draw.text((16, 28), row.get("character", "?"), fill=PALETTE["title_text"], font=FONT_TITLE)

    draw.line([16, 58, CARD_W-16, 58], fill=color, width=1)

    y = 68

    # Trigger
    trigger = row.get("trigger", "")
    if trigger:
        draw.text((16, y), "TRIGGER:", fill=color, font=FONT_SMALL)
        y += 18
        y = draw_wrapped_text(draw, 16, y, trigger, FONT_BODY, PALETTE["text"], CARD_W - 32, max_lines=2)
        y += 8

    # Immediate
    imm = row.get("immediate", "")
    if imm:
        draw.text((16, y), "IMMEDIATE:", fill=PALETTE["accent_green"], font=FONT_SMALL)
        y += 18
        y = draw_wrapped_text(draw, 16, y, imm, FONT_BODY, PALETTE["text"], CARD_W - 32, max_lines=6)
        y += 8

    # Departure
    dep = row.get("departure", "")
    if dep:
        draw.line([16, y, CARD_W-16, y], fill=PALETTE["border"], width=1)
        y += 8
        draw.text((16, y), "DEPARTURE:", fill=PALETTE["accent_red"], font=FONT_SMALL)
        y += 18
        y = draw_wrapped_text(draw, 16, y, dep, FONT_BODY, PALETTE["text"], CARD_W - 32, max_lines=4)

    draw.text((16, CARD_H - 24), row.get("id", ""), fill=PALETTE["border"], font=FONT_LABEL)
    return img

def render_trophy_card(row):
    """Render a single Trophy card."""
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    color = PALETTE["trophy"]

    draw.rectangle([0, 0, CARD_W-1, CARD_H-1], outline=color, width=3)
    draw_rounded_rect(draw, [8, 8, CARD_W-8, 52], 6, fill=PALETTE["title_bg"], outline=color)

    draw.text((16, 12), "TROPHY", fill=color, font=FONT_SMALL)
    draw.text((16, 28), row.get("boss", "?"), fill=PALETTE["title_text"], font=FONT_TITLE)

    draw.line([16, 58, CARD_W-16, 58], fill=color, width=1)

    y = 80
    bonus = row.get("bonus", "")
    if bonus:
        draw.text((16, y), "BONUS:", fill=PALETTE["accent_gold"], font=FONT_SMALL)
        y += 18
        y = draw_wrapped_text(draw, 16, y, bonus, FONT_BODY, PALETTE["text"], CARD_W - 32, max_lines=10)

    draw.text((16, CARD_H - 24), row.get("id", ""), fill=PALETTE["border"], font=FONT_LABEL)
    return img

# ---------------------------------------------------------------------------
# Card back renderers
# ---------------------------------------------------------------------------
def render_card_back(label, color_key):
    """Render a generic card back."""
    img = Image.new("RGB", (CARD_W, CARD_H), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    color = PALETTE.get(color_key, PALETTE["border"])

    # Outer border
    draw.rectangle([0, 0, CARD_W-1, CARD_H-1], outline=color, width=4)

    # Inner decorative border
    draw.rectangle([12, 12, CARD_W-12, CARD_H-12], outline=PALETTE["border"], width=2)

    # Diagonal cross pattern
    for offset in range(-CARD_H, CARD_W, 30):
        draw.line([offset, 0, offset + CARD_H, CARD_H], fill=(40, 38, 35), width=1)

    # Center label panel
    cx, cy = CARD_W // 2, CARD_H // 2
    panel_w, panel_h = 200, 80
    draw_rounded_rect(draw,
        [cx - panel_w//2, cy - panel_h//2, cx + panel_w//2, cy + panel_h//2],
        10, fill=PALETTE["title_bg"], outline=color)

    # Label text (centered)
    bbox = draw.textbbox((0, 0), label, font=FONT_TITLE)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw//2, cy - 18), label, fill=PALETTE["title_text"], font=FONT_TITLE)

    # Sub-label
    sub = "STARVE NO MORE"
    bbox2 = draw.textbbox((0, 0), sub, font=FONT_SMALL)
    tw2 = bbox2[2] - bbox2[0]
    draw.text((cx - tw2//2, cy + 10), sub, fill=color, font=FONT_SMALL)

    return img

# ---------------------------------------------------------------------------
# Atlas builder
# ---------------------------------------------------------------------------
def build_atlas(cards, num_w, num_h):
    """Stitch individual card images into an atlas grid."""
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

    # --- Phase decks (4 x 4x3 grid) ---
    for phase_num in range(1, 5):
        rows = read_csv(f"cards_phase{phase_num}.csv")
        cards = [render_phase_card(r, phase_num) for r in rows]
        atlas = build_atlas(cards, 4, 3)
        atlas.save(os.path.join(OUT, f"phase{phase_num}_face.png"))
        print(f"Phase {phase_num} face: {len(rows)} cards -> 4x3 atlas ({atlas.size[0]}x{atlas.size[1]})")

        back = render_card_back(f"PHASE {phase_num}", f"phase{phase_num}")
        back.save(os.path.join(OUT, f"phase{phase_num}_back.png"))

    # --- Market deck (7x8 grid) ---
    rows = read_csv("cards_market.csv")
    cards = [render_market_card(r) for r in rows]
    atlas = build_atlas(cards, 7, 8)
    atlas.save(os.path.join(OUT, "market_face.png"))
    print(f"Market face: {len(rows)} cards -> 7x8 atlas ({atlas.size[0]}x{atlas.size[1]})")

    back = render_card_back("MARKET", "market")
    back.save(os.path.join(OUT, "market_back.png"))

    # --- Recipe deck (5x4 grid) ---
    rows = read_csv("cards_recipes.csv")
    cards = [render_recipe_card(r) for r in rows]
    atlas = build_atlas(cards, 5, 4)
    atlas.save(os.path.join(OUT, "recipe_face.png"))
    print(f"Recipe face: {len(rows)} cards -> 5x4 atlas ({atlas.size[0]}x{atlas.size[1]})")

    back = render_card_back("RECIPE", "recipe")
    back.save(os.path.join(OUT, "recipe_back.png"))

    # --- Threat deck (6x5 grid) ---
    rows = read_csv("cards_threats.csv")
    cards = [render_threat_card(r) for r in rows]
    atlas = build_atlas(cards, 6, 5)
    atlas.save(os.path.join(OUT, "threat_face.png"))
    print(f"Threat face: {len(rows)} cards -> 6x5 atlas ({atlas.size[0]}x{atlas.size[1]})")

    back = render_card_back("THREAT", "threat")
    back.save(os.path.join(OUT, "threat_back.png"))

    # --- Visitor deck (3x2 grid) ---
    rows = read_csv("cards_visitors.csv")
    cards = [render_visitor_card(r) for r in rows]
    atlas = build_atlas(cards, 3, 2)
    atlas.save(os.path.join(OUT, "visitor_face.png"))
    print(f"Visitor face: {len(rows)} cards -> 3x2 atlas ({atlas.size[0]}x{atlas.size[1]})")

    back = render_card_back("VISITOR", "visitor")
    back.save(os.path.join(OUT, "visitor_back.png"))

    # --- Trophy deck (2x2 grid) ---
    rows = read_csv("cards_trophies.csv")
    cards = [render_trophy_card(r) for r in rows]
    atlas = build_atlas(cards, 2, 2)
    atlas.save(os.path.join(OUT, "trophy_face.png"))
    print(f"Trophy face: {len(rows)} cards -> 2x2 atlas ({atlas.size[0]}x{atlas.size[1]})")

    back = render_card_back("TROPHY", "trophy")
    back.save(os.path.join(OUT, "trophy_back.png"))

    print(f"\nAll atlases written to: {OUT}")
    print(f"Total: 9 face atlases + 9 back images = 18 files")

if __name__ == "__main__":
    main()
