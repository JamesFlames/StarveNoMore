"""
Generate non-card art assets for Starve No More:
  - 6 resource tokens (256x256)
  - 3 stat marker tokens (256x256)
  - Doom marker (256x256)
  - Telltale Heart token (256x256)
  - Sanity d8 texture (256x256)
  - Severity legend card (600x800)
  - 5 player boards (1024x512)
  - Main board with doom track (4096x4096)

Run: python scripts/generate_assets.py
Output: art/tokens/, art/icons/, art/legend/, art/characters/, art/board/
"""

import math
import os

import board_geometry  # doom-track pixel geometry shared with build_save.py
import path_layouts  # the map graph, shared with the Lua adjacency table
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Output dirs
DIRS = {
    "tokens": os.path.join(ROOT, "art", "tokens"),
    "icons":  os.path.join(ROOT, "art", "icons"),
    "legend": os.path.join(ROOT, "art", "legend"),
    "chars":  os.path.join(ROOT, "art", "characters"),
    "board":  os.path.join(ROOT, "art", "board"),
}
for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

# ---------------------------------------------------------------------------
# Palette (shared with card atlas generator)
# ---------------------------------------------------------------------------
PAL = {
    "bg":       (30, 28, 26),
    "bg_light": (45, 42, 38),
    "border":   (80, 72, 60),
    "text":     (220, 210, 190),
    "gold":     (180, 150, 60),
    "red":      (200, 60, 50),
    "orange":   (210, 140, 50),
    "green":    (70, 160, 70),
    "blue":     (60, 120, 200),
    "purple":   (120, 80, 160),
    "teal":     (60, 160, 160),
    "grey":     (140, 140, 140),
    "white":    (220, 215, 200),
    "brown":    (140, 90, 50),
    "yellow":   (220, 200, 60),
    "dark_red": (100, 30, 30),
}

# Matches the seat scheme (CHARACTER_COLORS in lua/global.lua): a player's
# seat colour follows their character.
CHAR_COLORS = {
    "James":  PAL["blue"],
    "Coco":   PAL["white"],
    "Rayman": PAL["green"],
    "Ellie":  PAL["yellow"],
    "Luca":   PAL["red"],
}

RESOURCE_COLORS = {
    "wood":    PAL["brown"],
    "metal":   PAL["grey"],
    "cloth":   PAL["white"],
    "food":    PAL["red"],
    "energy":  PAL["yellow"],
    "battery": PAL["blue"],
}

# ---------------------------------------------------------------------------
# Font loading
# ---------------------------------------------------------------------------
def load_font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

FONT_XL    = load_font(36, bold=True)
FONT_LG    = load_font(24, bold=True)
FONT_MD    = load_font(18, bold=True)
FONT_SM    = load_font(14)
FONT_XS    = load_font(11)
FONT_TINY  = load_font(9)

# Board-specific fonts
FONT_BOARD_TITLE = load_font(72, bold=True)
FONT_BOARD_NAME  = load_font(120, bold=True)   # location names — readable from table height
FONT_BOARD_YIELD = load_font(52)               # yields line under each name
FONT_BOARD_LOC   = load_font(40, bold=True)
FONT_BOARD_LABEL = load_font(28)
FONT_BOARD_SM    = load_font(22)
FONT_BOARD_XS    = load_font(16)
FONT_BOARD_TINY  = load_font(13)
FONT_BOARD_NUM   = load_font(26, bold=True)    # doom-track step numbers
FONT_BOARD_RIB   = load_font(28, bold=True)    # doom-track threshold ribbons

# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def centered_text(draw, cx, cy, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2), text, fill=fill, font=font)

def draw_circle(draw, cx, cy, r, fill, outline=None, width=1):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline, width=width)

def draw_heart(draw, cx, cy, size, fill):
    """Draw a heart shape."""
    pts = []
    for deg in range(360):
        t = math.radians(deg)
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        pts.append((cx + x * size / 16, cy + y * size / 16))
    draw.polygon(pts, fill=fill)

def draw_star(draw, cx, cy, r_out, r_in, points, fill):
    """Draw a star polygon."""
    pts = []
    for i in range(points * 2):
        angle = math.radians(-90 + i * 180 / points)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(pts, fill=fill)

# ---------------------------------------------------------------------------
# RESOURCE TOKENS (6 x 256x256)
# ---------------------------------------------------------------------------
RESOURCE_SYMBOLS = {
    "wood":    "W",    # log
    "metal":   "M",    # gear
    "cloth":   "C",    # bolt
    "food":    "F",    # apple
    "energy":  "E",    # can
    "battery": "B",    # AA
}

RESOURCE_LABELS = {
    "wood": "WOOD",
    "metal": "METAL",
    "cloth": "CLOTH",
    "food": "FOOD",
    "energy": "ENERGY\nDRINK",
    "battery": "BATTERY",
}

def generate_resource_token(name, color, symbol):
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Circular token with border
    draw_circle(draw, 128, 128, 120, fill=PAL["bg"], outline=color, width=6)
    draw_circle(draw, 128, 128, 100, fill=None, outline=(color[0]//2, color[1]//2, color[2]//2), width=2)

    # Symbol shapes based on resource type
    if name == "wood":
        # Log cross-section (concentric rings)
        draw_circle(draw, 128, 118, 50, fill=(100, 65, 35), outline=(80, 50, 25), width=2)
        draw_circle(draw, 128, 118, 35, fill=None, outline=(70, 45, 20), width=1)
        draw_circle(draw, 128, 118, 22, fill=None, outline=(70, 45, 20), width=1)
        draw_circle(draw, 128, 118, 10, fill=(60, 35, 15))
    elif name == "metal":
        # Gear shape
        for i in range(8):
            angle = math.radians(i * 45)
            x1 = 128 + 35 * math.cos(angle)
            y1 = 118 + 35 * math.sin(angle)
            x2 = 128 + 55 * math.cos(angle)
            y2 = 118 + 55 * math.sin(angle)
            draw.line([x1, y1, x2, y2], fill=color, width=12)
        draw_circle(draw, 128, 118, 38, fill=PAL["grey"], outline=(100, 100, 100), width=3)
        draw_circle(draw, 128, 118, 15, fill=PAL["bg"])
    elif name == "cloth":
        # Folded bolt (rectangle with fold lines)
        draw.rounded_rectangle([78, 83, 178, 153], radius=8, fill=(190, 185, 170), outline=(160, 155, 140), width=2)
        draw.line([78, 103, 178, 103], fill=(160, 155, 140), width=1)
        draw.line([78, 123, 178, 123], fill=(160, 155, 140), width=1)
        draw.line([78, 143, 178, 143], fill=(160, 155, 140), width=1)
    elif name == "food":
        # Apple shape
        draw_circle(draw, 120, 125, 35, fill=(180, 40, 40))
        draw_circle(draw, 140, 125, 35, fill=(200, 50, 50))
        # Stem
        draw.line([130, 90, 135, 75], fill=(80, 50, 20), width=4)
        # Leaf
        draw.ellipse([136, 72, 160, 88], fill=(60, 130, 50))
    elif name == "energy":
        # Can shape with lightning bolt
        draw.rounded_rectangle([93, 78, 163, 158], radius=6, fill=(200, 190, 40), outline=(180, 170, 30), width=2)
        # Tab on top
        draw.rectangle([108, 70, 148, 82], fill=(180, 170, 30))
        draw.ellipse([118, 66, 138, 78], fill=(160, 150, 20))
        # Lightning bolt
        bolt = [(128, 90), (118, 120), (130, 118), (122, 150), (142, 112), (130, 114), (138, 90)]
        draw.polygon(bolt, fill=(40, 30, 10))
    elif name == "battery":
        # AA battery
        draw.rounded_rectangle([98, 82, 158, 158], radius=5, fill=(50, 100, 180), outline=(40, 80, 150), width=2)
        # Positive terminal
        draw.rectangle([113, 72, 143, 85], fill=(180, 180, 160))
        # Label stripe
        draw.rectangle([98, 108, 158, 130], fill=(40, 80, 150))
        # Plus/minus
        draw.text((104, 134), "-", fill=(200, 200, 200), font=FONT_MD)
        draw.text((142, 86), "+", fill=(80, 80, 80), font=FONT_SM)

    # Label below symbol
    label = RESOURCE_LABELS[name]
    centered_text(draw, 128, 192, label, FONT_SM, color)

    img = img.rotate(180)   # tokens at rotY=0 render 180° in the default view

    img.save(os.path.join(DIRS["tokens"], f"resource_{name}.png"))
    return img

# ---------------------------------------------------------------------------
# STAT MARKER TOKENS (3 x 256x256)
# ---------------------------------------------------------------------------
def generate_stat_tokens():
    stats = [
        ("health", PAL["red"],    "heart"),
        ("hunger", PAL["orange"], "fork"),
        ("sanity", PAL["teal"],   "spiral"),
    ]
    for name, color, shape in stats:
        size = 256
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        draw_circle(draw, 128, 128, 120, fill=PAL["bg"], outline=color, width=5)

        if shape == "heart":
            draw_heart(draw, 128, 115, 48, color)
        elif shape == "fork":
            # Fork and knife crossed
            # Fork (left)
            draw.line([100, 80, 100, 155], fill=color, width=5)
            draw.line([100, 80, 100, 100], fill=color, width=3)
            draw.line([90, 80, 90, 100], fill=color, width=3)
            draw.line([110, 80, 110, 100], fill=color, width=3)
            # Knife (right)
            draw.line([155, 80, 155, 155], fill=color, width=5)
            draw.polygon([(148, 80), (162, 80), (155, 110)], fill=color)
        elif shape == "spiral":
            # Abstract brain spiral
            for i in range(0, 720, 5):
                t = math.radians(i)
                r = 10 + i * 0.06
                x = 128 + r * math.cos(t)
                y = 118 + r * math.sin(t)
                draw_circle(draw, int(x), int(y), 2, fill=color)

        label = name.upper()
        centered_text(draw, 128, 200, label, FONT_SM, color)

        img = img.rotate(180)   # tokens at rotY=0 render 180° in the default view

        img.save(os.path.join(DIRS["icons"], f"icon_{name}.png"))
        print(f"  Stat token: icon_{name}.png")

# ---------------------------------------------------------------------------
# DOOM MARKER (256x256)
# ---------------------------------------------------------------------------
def generate_doom_marker():
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark ominous circle with red glow ring
    draw_circle(draw, 128, 128, 120, fill=(40, 15, 15), outline=(160, 30, 30), width=6)
    draw_circle(draw, 128, 128, 100, fill=None, outline=(120, 20, 20), width=2)

    # Skull-ish icon (simplified)
    # Cranium
    draw.ellipse([88, 70, 168, 145], fill=(180, 170, 150))
    # Eye sockets
    draw.ellipse([100, 95, 122, 118], fill=(40, 15, 15))
    draw.ellipse([134, 95, 156, 118], fill=(40, 15, 15))
    # Nose
    draw.polygon([(124, 118), (132, 118), (128, 130)], fill=(40, 15, 15))
    # Jaw line teeth
    draw.rectangle([104, 135, 152, 150], fill=(180, 170, 150))
    for tx in range(108, 150, 8):
        draw.line([tx, 135, tx, 150], fill=(40, 15, 15), width=1)

    centered_text(draw, 128, 200, "DOOM", FONT_MD, (200, 50, 40))

    # The marker is locked at rotY=0 by moveDoomMarker, so its art carries
    # the 180° pre-rotation (same convention as the board).
    img = img.rotate(180)

    img.save(os.path.join(DIRS["tokens"], "doom_marker.png"))
    print("  Doom marker: doom_marker.png")

# ---------------------------------------------------------------------------
# TELLTALE HEART (256x256)
# ---------------------------------------------------------------------------
def generate_heart_token():
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Warm glow circle
    draw_circle(draw, 128, 128, 120, fill=(50, 20, 25), outline=(160, 60, 70), width=4)

    # Glowing red heart
    draw_heart(draw, 128, 110, 55, (200, 40, 50))
    # Inner highlight
    draw_heart(draw, 122, 105, 20, (230, 80, 90))

    centered_text(draw, 128, 195, "TELLTALE", FONT_SM, (200, 150, 100))
    centered_text(draw, 128, 215, "HEART", FONT_SM, (200, 150, 100))

    img = img.rotate(180)   # tokens at rotY=0 render 180° in the default view

    img.save(os.path.join(DIRS["tokens"], "telltale_heart.png"))
    print("  Heart token: telltale_heart.png")

# ---------------------------------------------------------------------------
# SANITY d8 TEXTURE (256x256) — a custom die face atlas is not needed for
# TTS custom dice; it uses a single token image. We render a d8-shaped icon.
# ---------------------------------------------------------------------------
def generate_sanity_d8():
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Diamond/octahedron face
    pts = [(128, 30), (225, 128), (128, 226), (31, 128)]
    draw.polygon(pts, fill=(40, 30, 60), outline=PAL["teal"], width=3)

    # Spiral in center
    for i in range(0, 540, 8):
        t = math.radians(i)
        r = 5 + i * 0.08
        x = 128 + r * math.cos(t)
        y = 128 + r * math.sin(t)
        draw_circle(draw, int(x), int(y), 2, fill=PAL["teal"])

    centered_text(draw, 128, 200, "d8", FONT_MD, PAL["teal"])

    img.save(os.path.join(DIRS["tokens"], "sanity_d8.png"))
    print("  Sanity d8: sanity_d8.png")

# ---------------------------------------------------------------------------
# SEVERITY LEGEND (600x800)
# ---------------------------------------------------------------------------
def generate_severity_legend():
    W, H = 600, 800
    img = Image.new("RGB", (W, H), PAL["bg"])
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W-1, H-1], outline=PAL["border"], width=3)

    # Title
    draw.rounded_rectangle([20, 20, W-20, 70], radius=8, fill=(45, 42, 38), outline=PAL["border"])
    centered_text(draw, W//2, 45, "SEVERITY LEGEND", FONT_LG, PAL["gold"])

    rows = [
        (1, "Atmospheric", "Flavor only. No mechanical effect."),
        (2, "Minor stat hit", "Small Sanity/Hunger loss. Manageable."),
        (3, "Combat or lasting", "Fight required or ongoing penalty."),
        (4, "Phase-shift event", "Major change. Boss approaching."),
        (5, "Boss / Apocalyptic", "Boss arrives. Game-changing threat."),
    ]

    y = 100
    for severity, label, desc in rows:
        # Severity dots
        for i in range(5):
            cx = 40 + i * 24
            cy = y + 15
            if i < severity:
                draw_circle(draw, cx, cy, 9, fill=PAL["red"])
            else:
                draw_circle(draw, cx, cy, 9, fill=(50, 48, 44), outline=PAL["border"], width=1)

        # Label
        draw.text((170, y), label, fill=PAL["gold"], font=FONT_MD)
        draw.text((170, y + 28), desc, fill=PAL["text"], font=FONT_SM)

        # Divider
        y += 70
        draw.line([30, y, W-30, y], fill=PAL["border"], width=1)
        y += 15

    # Footer
    centered_text(draw, W//2, H-40, "STARVE NO MORE", FONT_SM, PAL["border"])

    # Detailed rules at bottom
    y_bottom = 520
    draw.text((30, y_bottom), "How to read severity on cards:", fill=PAL["gold"], font=FONT_SM)
    y_bottom += 24
    tips = [
        "Dots appear in the top-right corner of Dawn and Threat cards.",
        "Higher severity = more dangerous. Plan accordingly.",
        "Phase 1 cards are mostly 1-2 dots (mild).",
        "Phase 4 cards include 4-5 dot events (boss-level).",
        "Threat cards with 3+ dots usually require combat.",
        "When multiple high-severity cards stack, prioritize survival.",
    ]
    for tip in tips:
        draw.text((40, y_bottom), "- " + tip, fill=PAL["text"], font=FONT_XS)
        y_bottom += 22

    img.save(os.path.join(DIRS["legend"], "severity_legend.png"))
    print("  Severity legend: severity_legend.png")

# ---------------------------------------------------------------------------
# PLAYER BOARDS (5 x 1024x512)
# ---------------------------------------------------------------------------
CHARACTER_DATA = {
    "James":  {"hp": 8, "hu": 6, "sa": 10, "seat": "Blue",
               "perks": ["Gaming Reflexes: reroll 1 die/turn",
                         "Pattern Recognition: peek deck top/day"],
               "flaw": "Wired: 1 Energy Drink/day or -2 Sanity",
               "hand": "Energy Drink x2, Pocketknife, Flashlight, Headphones"},
    "Coco":   {"hp": 6, "hu": 8, "sa": 12, "seat": "White",
               "perks": ["Calming Presence: allies -1 Sanity loss",
                         "Touch of Hope (1x): heal any +4 HP",
                         "Light in the Dark: immune to Charlie"],
               "flaw": "No Home: alone non-house at night = -3 Sanity",
               "hand": "First Aid Kit, Comfort Blanket, Hopeful Tea, Spare Battery, Bracelet"},
    "Rayman": {"hp": 12, "hu": 10, "sa": 6, "seat": "Green",
               "perks": ["Speed: move 2 tiles per Move",
                         "Court Master: +1 atk at Basketball",
                         "Backboard Block: Defend shields adj."],
               "flaw": "Big Appetite: -2 Hunger/Tick. Loud: +1 Threat on move.",
               "hand": "Basketball, Sports Drink x2, Athletic Tape, Whistle"},
    "Ellie":  {"hp": 8, "hu": 10, "sa": 8, "seat": "Yellow",
               "perks": ["Crockpot Master: -1 ingredient (min 1)",
                         "Comfort Food: shared meal +1 Hu/Sa",
                         "Knows the Pantry: pick resource at home"],
               "flaw": "Particular Eater: can't eat raw food",
               "hand": "Crockpot, Soup Recipe, Cooking Knife, Pantry Key, Apron"},
    "Luca":   {"hp": 7, "hu": 8, "sa": 10, "seat": "Red",
               "perks": ["Rally: free ally action/turn",
                         "Calm Words: d6 4+= negate Sanity loss",
                         "Storyteller: allies +1 Sanity at Night"],
               "flaw": "Needs an Audience: no solo Sanity regen",
               "hand": "Notebook, Loud Whistle, Pep Talk, Reading Lamp, Toolbox"},
}

def draw_stat_bar(draw, x, y, w, h, current, maximum, color, label, font):
    """Draw a labeled stat bar with threshold zone."""
    # Label
    draw.text((x, y - 20), f"{label}: {current}/{maximum}", fill=color, font=font)
    # Background
    draw.rounded_rectangle([x, y, x + w, y + h], radius=4, fill=(25, 23, 21), outline=PAL["border"], width=1)
    # Threshold zone (first 3 units) in dark red
    thresh_w = int(w * min(3, maximum) / maximum)
    draw.rounded_rectangle([x+1, y+1, x + thresh_w, y + h - 1], radius=3, fill=(60, 25, 25))
    # Filled portion
    fill_w = int(w * current / maximum)
    if fill_w > 0:
        draw.rounded_rectangle([x+1, y+1, x + fill_w, y + h - 1], radius=3, fill=color)
    # Tick marks
    for i in range(1, maximum):
        tx = x + int(w * i / maximum)
        draw.line([tx, y+1, tx, y + h - 1], fill=(40, 38, 36), width=1)

def generate_player_board(char_name, data):
    W, H = 1024, 512
    img = Image.new("RGB", (W, H), PAL["bg"])
    draw = ImageDraw.Draw(img)

    color = CHAR_COLORS[char_name]

    # Border
    draw.rectangle([0, 0, W-1, H-1], outline=color, width=4)

    # Name bar
    draw.rounded_rectangle([10, 10, W-10, 60], radius=8, fill=(45, 42, 38), outline=color, width=2)
    draw.text((24, 16), char_name.upper(), fill=PAL["gold"], font=FONT_XL)
    draw.text((24, 42), f"Seat: {data['seat']}", fill=PAL["border"], font=FONT_XS)

    # Portrait placeholder (left side)
    draw.rounded_rectangle([14, 70, 180, 300], radius=8, fill=(40, 38, 36), outline=PAL["border"], width=2)
    centered_text(draw, 97, 185, char_name[0], load_font(80, True), color)

    # Stat bars (right of portrait)
    bar_x = 200
    bar_w = 350
    bar_h = 28

    draw_stat_bar(draw, bar_x, 100, bar_w, bar_h, data["hp"], data["hp"], PAL["red"], "HEALTH", FONT_SM)
    draw_stat_bar(draw, bar_x, 160, bar_w, bar_h, data["hu"], data["hu"], PAL["orange"], "HUNGER", FONT_SM)
    draw_stat_bar(draw, bar_x, 220, bar_w, bar_h, data["sa"], data["sa"], PAL["teal"], "SANITY", FONT_SM)

    # Action cubes placeholder
    draw.text((bar_x, 270), "ACTIONS: 3 per turn", fill=PAL["text"], font=FONT_SM)
    for i in range(3):
        cx = bar_x + 160 + i * 32
        draw.rounded_rectangle([cx, 268, cx + 24, 292], radius=4, fill=PAL["green"], outline=(50, 100, 50))

    # Perks panel (right column)
    px = 600
    draw.text((px, 75), "PERKS:", fill=PAL["green"], font=FONT_MD)
    py = 100
    for perk in data["perks"]:
        draw.text((px + 8, py), "+ " + perk, fill=PAL["text"], font=FONT_XS)
        py += 22

    # Constraint panel (red border)
    draw.rounded_rectangle([px - 4, py + 8, W - 14, py + 55], radius=6, fill=(45, 25, 25), outline=PAL["red"], width=2)
    draw.text((px + 4, py + 12), "CONSTRAINT:", fill=PAL["red"], font=FONT_XS)
    draw.text((px + 4, py + 30), data["flaw"], fill=PAL["text"], font=FONT_XS)

    # Starting hand (bottom)
    draw.line([14, 320, W-14, 320], fill=PAL["border"], width=1)
    draw.text((20, 330), "STARTING HAND:", fill=PAL["gold"], font=FONT_SM)
    draw.text((20, 352), data["hand"], fill=PAL["text"], font=FONT_SM)

    # Threshold reminder
    draw.line([14, 390, W-14, 390], fill=PAL["border"], width=1)
    draw.text((20, 400), "THRESHOLD WARNINGS  (below 3):", fill=PAL["red"], font=FONT_SM)
    warnings = [
        ("Health < 3:", "Movement costs +1 action"),
        ("Hunger < 3:", "Cannot Fight or use Effort actions"),
        ("Sanity < 3:", "Hallucinate at next Dawn"),
    ]
    wy = 422
    for wlabel, wtext in warnings:
        draw.text((30, wy), wlabel, fill=PAL["orange"], font=FONT_XS)
        draw.text((130, wy), wtext, fill=PAL["text"], font=FONT_XS)
        wy += 20

    # Footer
    centered_text(draw, W//2, H - 16, "STARVE NO MORE", FONT_TINY, PAL["border"])

    # Custom_Tile at rotY=0 renders its image rotated 180 degrees in the
    # default table view (same convention as the main board) — rotate the
    # finished image once so the board reads upright in play.
    img = img.rotate(180)

    img.save(os.path.join(DIRS["chars"], f"board_{char_name.lower()}.png"))
    print(f"  Player board: board_{char_name.lower()}.png")

# ---------------------------------------------------------------------------
# MAIN BOARD (4096x4096)
# ---------------------------------------------------------------------------
def generate_main_board(variant=None, doom_limit=None):
    """Render the board for a path variant and a Doom limit.

    The printed lines ARE the map: whatever this draws, LOCATION_ADJACENCY
    must allow (path_layouts.py). The printed Doom track is the same promise
    for the difficulty: Long Weekend halves the track, so it gets its own
    board whose track ends — and says DEFEAT — at 15. Drawing 31 cells for a
    15-Doom game left the marker stranded halfway down a track labelled up to
    30 while the HUD counted to 15.
    """
    variant = variant or path_layouts.DEFAULT_VARIANT
    doom_limit = doom_limit or board_geometry.DEFAULT_DOOM_LIMIT
    nights = board_geometry.DOOM_LIMIT_DAYS[doom_limit]
    S = 4096
    img = Image.new("RGB", (S, S), (35, 32, 28))
    draw = ImageDraw.Draw(img)

    # Subtle background texture - concentric rings
    for r in range(100, S, 200):
        draw.ellipse([S//2 - r, S//2 - r, S//2 + r, S//2 + r],
                     outline=(38, 35, 31), width=1)

    # --- LOCATION NODES ---
    # Authored from the location tiles' WORLD positions (loc_positions in
    # build_save.py) via board_geometry.world_to_px/py, so the printed
    # rings sit exactly under the physical tiles. Each ring is larger than
    # its 5x5-unit tile, and the name is printed OUTSIDE the tile footprint
    # in a big font — that's what makes the location names readable on the
    # table (the tile itself is pure illustration).
    #   (world x, world z, ring colour, label side)
    _ring_colors = {
        "JamesHouse":      (PAL["blue"],   "below"),
        "EllieLucaHouse":  (PAL["orange"], "below"),
        "RaymanHouse":     (PAL["green"],  "below"),
        "BasketballCourt": (PAL["grey"],   "below"),   # was "above": it collided with Ellie & Luca's label
        "BadmintonCourt":  (PAL["teal"],   "below"),
    }
    locations = {
        k: (path_layouts.LOCATION_WORLD[k][0], path_layouts.LOCATION_WORLD[k][1],
            c, side)
        for k, (c, side) in _ring_colors.items()
    }
    node_px = {
        name: (int(board_geometry.world_to_px(wx)), int(board_geometry.world_to_py(wz)))
        for name, (wx, wz, _c, _side) in locations.items()
    }

    # --- PATH EDGES (connections) ---
    # THE PRINTED LINES ARE THE MAP. Drawn from the shared layout table so the
    # board can never show a route the Move action refuses (path_layouts.py).
    paths = path_layouts.PATH_LAYOUTS[variant]

    # Draw paths first (behind nodes)
    for loc_a, loc_b in paths:
        xa, ya = node_px[loc_a]
        xb, yb = node_px[loc_b]
        # Thick path line
        draw.line([xa, ya, xb, yb], fill=(55, 50, 42), width=18)
        # Dotted center line
        steps = 30
        for i in range(0, steps, 2):
            t1 = i / steps
            t2 = (i + 1) / steps
            px1 = int(xa + (xb - xa) * t1)
            py1 = int(ya + (yb - ya) * t1)
            px2 = int(xa + (xb - xa) * t2)
            py2 = int(ya + (yb - ya) * t2)
            draw.line([px1, py1, px2, py2], fill=(75, 68, 58), width=4)

    # Draw location nodes. The tile (5x5 world units) covers the ring
    # centre, so everything readable goes in the ring's annulus (between
    # the 2.5-unit tile half-width and the 3.8-unit ring): the name sits
    # on the arc nearest the open side, the yields line just outside it.
    PX_PER_UNIT = S / (2.0 * board_geometry.BOARD_WORLD_HALF)
    node_r = int(path_layouts.LOCATION_RING_R * PX_PER_UNIT)   # peeks out around the tile
    name_off = int((path_layouts.LOCATION_RING_R - 0.50) * PX_PER_UNIT)  # name, in the annulus
    info_off = int((path_layouts.LOCATION_RING_R - 0.10) * PX_PER_UNIT)  # yields, just inside the ring

    yield_info = {
        "JamesHouse":      "Energy, Battery, Food",
        "EllieLucaHouse":  "Food, Food, Cloth + Crockpot",
        "RaymanHouse":     "Metal, Battery, Food",
        "BasketballCourt": "Wood, Metal, Cloth",
        "BadmintonCourt":  "Cloth, Wood, Metal",
    }

    for name, (wx, wz, color, side) in locations.items():
        cx, cy = node_px[name]
        # Outer glow ring
        draw_circle(draw, cx, cy, node_r + 15, fill=None,
                    outline=(color[0]//3, color[1]//3, color[2]//3), width=6)
        # Main circle
        draw_circle(draw, cx, cy, node_r, fill=(40, 38, 34), outline=color, width=10)
        # Inner ring
        draw_circle(draw, cx, cy, node_r - 34, fill=None, outline=(50, 48, 42), width=3)

        # Name + yields on the open side ("above" = north, for the
        # Basketball Court whose south side is the board edge). The name
        # always reads first (higher on the table) with yields under it.
        if side == "above":
            ny, iy = cy - info_off, cy - name_off
        else:
            ny, iy = cy + name_off, cy + info_off
        centered_text(draw, cx, ny, path_layouts.LOCATION_LABELS[name],
                      FONT_BOARD_NAME, color)
        centered_text(draw, cx, iy, yield_info.get(name, ""), FONT_BOARD_YIELD, PAL["text"])

    # --- DOOM TRACK — horizontal strip along the SOUTH edge (the only band
    # clear of rings and labels). Pixel geometry comes from board_geometry
    # so the Doom-marker snap points in build_save.py always land on the
    # printed track. ---
    # The strip is always the same length; doom_limit only decides how many
    # cells it is cut into. Long Weekend ends at 15, so its board gets 16
    # fatter cells rather than a half-used 31-cell track.
    _px1, _ = board_geometry.doom_step_px(1, doom_limit)
    step_w = _px1 - board_geometry.DOOM_STEP0_PX_X
    doom_y = int(board_geometry.DOOM_TRACK_PX_Y)
    x0 = int(board_geometry.DOOM_STEP0_PX_X - step_w / 2)
    x30 = int(board_geometry.doom_step_px(doom_limit, doom_limit)[0] + step_w / 2)
    cell_h = int(0.4 * PX_PER_UNIT)   # slimmer: the track sits close to the board edge

    # Track background
    draw.rounded_rectangle([x0 - 30, doom_y - cell_h - 30, x30 + 30, doom_y + cell_h + 30],
                           radius=20, fill=(35, 25, 25), outline=(100, 40, 40), width=4)

    # Title above the quiet west end of the track
    centered_text(draw, int(board_geometry.world_to_px(-9)),
                  doom_y - cell_h - 120, "D O O M", FONT_BOARD_LOC, PAL["red"])

    # Steps 0..doom_limit. Ribbons come from board_geometry (which mirrors
    # DOOM_THRESHOLDS in lua/global.lua) so the board can only ever promise
    # rules the game actually applies at this limit.
    thresholds = board_geometry.doom_thresholds_for(doom_limit)
    for step in range(doom_limit + 1):
        sx = int(board_geometry.doom_step_px(step, doom_limit)[0])
        # Color gradient: cool to warm
        t = step / doom_limit
        r_val = int(40 + t * 180)
        g_val = int(60 - t * 40)
        b_val = int(80 - t * 60)
        step_color = (r_val, g_val, b_val)

        # Step cell
        half = int(step_w / 2) - 3
        draw.rounded_rectangle([sx - half, doom_y - cell_h, sx + half, doom_y + cell_h],
                               radius=3, fill=step_color)
        # Number
        centered_text(draw, sx, doom_y, str(step), FONT_BOARD_NUM, PAL["text"])

        # Threshold ribbons above their step
        if step in thresholds:
            ribbon_y = doom_y - cell_h - 96
            tw = draw.textbbox((0, 0), thresholds[step], font=FONT_BOARD_RIB)[2]
            draw.rounded_rectangle([sx - tw // 2 - 14, ribbon_y - 26, sx + tw // 2 + 14, ribbon_y + 26],
                                   radius=6, fill=(80, 25, 25), outline=PAL["red"], width=2)
            centered_text(draw, sx, ribbon_y, thresholds[step], FONT_BOARD_RIB, (255, 200, 150))

    # --- TITLE (north-west corner, clear of the Badminton ring) ---
    t_x = int(board_geometry.world_to_px(-7.5))
    t_y = int(board_geometry.world_to_py(11.0))
    centered_text(draw, t_x, t_y, "STARVE NO MORE", FONT_BOARD_TITLE, PAL["gold"])
    centered_text(draw, t_x, t_y + 80, f"Survive {nights} Nights. Hold the Doom.",
                  FONT_BOARD_LABEL, PAL["text"])
    centered_text(draw, t_x, t_y + 130, variant.upper() + " LAYOUT", FONT_BOARD_LABEL, PAL["border"])

    # --- DAY COUNTER frame — drawn around the physical Day Counter's real
    # position (world (-10, 8), see build_save.py) so the printed frame and
    # the object actually line up on the table. ---
    _dcx, _dcz = board_geometry.DAY_COUNTER_WORLD
    dc_x = int(board_geometry.world_to_px(_dcx))
    dc_y = int(board_geometry.world_to_py(_dcz))
    # Sized to the Counter gadget's MEASURED footprint (2.97 x 1.95 world
    # units, auditObjectFootprints) plus margin: the old 600x280px frame was
    # 3.52 x 1.64 world, shorter than the counter, so the gadget overhung it.
    _dc_w = int((2.97 / 2 + 0.30) / (2 * board_geometry.BOARD_WORLD_HALF) * S)
    _dc_h = int((1.95 / 2 + 0.30) / (2 * board_geometry.BOARD_WORLD_HALF) * S)
    draw.rounded_rectangle([dc_x - _dc_w, dc_y - _dc_h, dc_x + _dc_w, dc_y + _dc_h],
                           radius=15, fill=None, outline=PAL["border"], width=4)
    centered_text(draw, dc_x, dc_y + _dc_h + 55, "DAY COUNTER", FONT_BOARD_YIELD, PAL["gold"])

    # --- DAWN EVENTS — the one card the whole table reads each morning, and
    # the pile of spent ones. Printed because an unmarked card on bare board
    # reads as litter: today's Dawn used to land on the Day Counter's frame
    # and across the title, and nothing said what it was. ---
    _bx0, _bz0, _bx1, _bz1 = board_geometry.DAWN_BOX
    draw.rounded_rectangle(
        [board_geometry.world_to_px(_bx0), board_geometry.world_to_py(_bz1),
         board_geometry.world_to_px(_bx1), board_geometry.world_to_py(_bz0)],
        radius=18, fill=(28, 30, 36), outline=PAL["border"], width=3)
    centered_text(draw, int(board_geometry.world_to_px((_bx0 + _bx1) / 2)),
                  int(board_geometry.world_to_py(_bz1 - 0.5)),
                  "DAWN EVENTS", FONT_BOARD_LOC, PAL["gold"])

    _slot_hw = board_geometry.DAWN_SLOT_W / 2
    _slot_hl = board_geometry.DAWN_SLOT_L / 2
    for _cx, _cz, _caption in (
            board_geometry.DAWN_REVEAL_WORLD + ("TODAY",),
            board_geometry.DAWN_DISCARD_WORLD + ("ALREADY PLAYED",)):
        draw.rounded_rectangle(
            [board_geometry.world_to_px(_cx - _slot_hw),
             board_geometry.world_to_py(_cz + _slot_hl),
             board_geometry.world_to_px(_cx + _slot_hw),
             board_geometry.world_to_py(_cz - _slot_hl)],
            radius=10, fill=(20, 21, 25), outline=PAL["border"], width=2)
        centered_text(draw, int(board_geometry.world_to_px(_cx)),
                      int(board_geometry.world_to_py(_cz - _slot_hl - 0.35)),
                      _caption, FONT_BOARD_LABEL, PAL["text"])

    # (No printed market/deck boxes: the Market slots are physical notecards
    # west of the board and the decks sit on the north edge; the old printed
    # frames pointed at empty felt and just confused people.)

    # --- LEGEND REMINDER (north-east corner) ---
    lg_x0 = int(board_geometry.world_to_px(7.0))
    lg_y0 = int(board_geometry.world_to_py(11.6))
    draw.rounded_rectangle([lg_x0, lg_y0, lg_x0 + 680, lg_y0 + 300],
                           radius=12, fill=(40, 38, 34), outline=PAL["border"], width=2)
    draw.text((lg_x0 + 20, lg_y0 + 20), "SEVERITY DOTS:", fill=PAL["gold"], font=FONT_BOARD_XS)
    sev_info = ["1 dot = Flavor", "2 dots = Minor", "3 dots = Combat",
                "4 dots = Phase-shift", "5 dots = Boss"]
    for i, si in enumerate(sev_info):
        # Dots
        for d in range(i + 1):
            draw_circle(draw, lg_x0 + 40 + d * 18, lg_y0 + 68 + i * 46, 6, fill=PAL["red"])
        for d in range(i + 1, 5):
            draw_circle(draw, lg_x0 + 40 + d * 18, lg_y0 + 68 + i * 46, 6, fill=PAL["border"])
        draw.text((lg_x0 + 145, lg_y0 + 58 + i * 46), si, fill=PAL["text"], font=FONT_BOARD_TINY)

    # A Custom_Board at rotY=0 renders its image rotated 180 degrees in the
    # default table view (see board_geometry docstring), so the finished
    # image is rotated here once — everything above reads upright in play.
    img = img.rotate(180)

    # One image per (variant, doom limit), plus main_board.png for the
    # default pair (the save ships that one; setup swaps to the picked
    # variant and difficulty at runtime).
    name = path_layouts.board_art_name(variant, doom_limit) + ".png"
    img.save(os.path.join(DIRS["board"], name))
    if (variant == path_layouts.DEFAULT_VARIANT
            and doom_limit == board_geometry.DEFAULT_DOOM_LIMIT):
        img.save(os.path.join(DIRS["board"], "main_board.png"))
    print(f"  Main board [{variant}, doom {doom_limit}]: {name} ({S}x{S})")


def generate_all_main_boards():
    for v in path_layouts.VARIANTS:
        for limit in board_geometry.DOOM_LIMITS:
            generate_main_board(v, limit)

# ---------------------------------------------------------------------------
# PATH DECORATION TILES (3 x 512x512)
# ---------------------------------------------------------------------------
def generate_path_tiles():
    variants = {
        "compact": ((70, 65, 55), "tight"),
        "sprawl":  ((60, 70, 55), "wide"),
        "linear":  ((55, 60, 70), "straight"),
    }
    for name, (tint, style) in variants.items():
        size = 512
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Decorative path segment
        draw.rounded_rectangle([20, 20, size-20, size-20], radius=30,
                               fill=tint, outline=(tint[0]+30, tint[1]+30, tint[2]+30), width=3)

        # Path texture lines
        if style == "tight":
            for y_off in range(40, size-40, 20):
                draw.line([40, y_off, size-40, y_off], fill=(tint[0]+15, tint[1]+15, tint[2]+15), width=1)
        elif style == "wide":
            for i in range(5):
                cx = size // 2 + (i - 2) * 80
                draw_circle(draw, cx, size // 2, 30, fill=None,
                           outline=(tint[0]+20, tint[1]+20, tint[2]+20), width=2)
        elif style == "straight":
            draw.line([size//2, 30, size//2, size-30], fill=(tint[0]+20, tint[1]+20, tint[2]+20), width=8)
            draw.line([size//2 - 40, 30, size//2 - 40, size-30], fill=(tint[0]+10, tint[1]+10, tint[2]+10), width=3)
            draw.line([size//2 + 40, 30, size//2 + 40, size-30], fill=(tint[0]+10, tint[1]+10, tint[2]+10), width=3)

        centered_text(draw, size//2, size//2, name.upper(), FONT_LG, (tint[0]+60, tint[1]+60, tint[2]+60))

        img.save(os.path.join(DIRS["board"], f"path_{name}.png"))
        print(f"  Path tile: path_{name}.png")

# ---------------------------------------------------------------------------
# MARKET SLOT FRAME (384x526)
# ---------------------------------------------------------------------------
def generate_market_slot_frame():
    """An empty card-shaped frame — the Market slot markers.

    They used to be full-size TTS Notecards printing the whole "use the Craft
    action to buy it" paragraph. A notecard is far bigger than a card, so the
    column lay across the printed map and hid it; the paragraph now rides on
    the card's own tooltip (addMarketHelp, lua/crafting.lua) and the marker is
    just this outline, a shade bigger than the card that sits on it. The slot
    NUMBER is a separate flat 3DText north of the frame (build_save.table_label)
    so it stays readable once a card covers the frame.

    No text and 2-fold symmetric, so it reads the same either way up — the
    tile still carries the ry=180 flat-art convention like the location tiles.
    Aspect ratio must match MARKET_SLOT_W:MARKET_SLOT_L in build_save.py.
    """
    W, H = 384, 526
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Recessed well: dark enough to read as "a card goes here" against the
    # felt, translucent so it never competes with the card laid on top.
    draw.rounded_rectangle([6, 6, W - 6, H - 6], radius=26,
                           fill=(22, 20, 18, 150),
                           outline=PAL["border"] + (210,), width=4)

    # Corner brackets — the "empty slot" read at a glance from table height.
    arm = 54
    for cx, cy, dx, dy in ((30, 30, 1, 1), (W - 30, 30, -1, 1),
                           (30, H - 30, 1, -1), (W - 30, H - 30, -1, -1)):
        draw.line([cx, cy, cx + dx * arm, cy], fill=PAL["gold"] + (230,), width=6)
        draw.line([cx, cy, cx, cy + dy * arm], fill=PAL["gold"] + (230,), width=6)

    img.save(os.path.join(DIRS["board"], "market_slot.png"))
    print(f"  Market slot frame: market_slot.png ({W}x{H})")

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("Generating resource tokens...")
    for name, color in RESOURCE_COLORS.items():
        symbol = RESOURCE_SYMBOLS[name]
        generate_resource_token(name, color, symbol)
        print(f"  Resource token: resource_{name}.png")

    print("\nGenerating stat tokens...")
    generate_stat_tokens()

    print("\nGenerating doom marker...")
    generate_doom_marker()

    print("\nGenerating telltale heart...")
    generate_heart_token()

    print("\nGenerating sanity d8...")
    generate_sanity_d8()

    print("\nGenerating severity legend...")
    generate_severity_legend()

    print("\nGenerating player boards...")
    for char_name, data in CHARACTER_DATA.items():
        generate_player_board(char_name, data)

    print("\nGenerating main board...")
    generate_all_main_boards()

    print("\nGenerating path tiles...")
    generate_path_tiles()

    print("\nGenerating market slot frame...")
    generate_market_slot_frame()

    print("\n=== DONE ===")
    print(f"Tokens:  {DIRS['tokens']}")
    print(f"Icons:   {DIRS['icons']}")
    print(f"Legend:  {DIRS['legend']}")
    print(f"Boards:  {DIRS['chars']}")
    print(f"Board:   {DIRS['board']}")

if __name__ == "__main__":
    main()
