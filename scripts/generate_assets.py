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

import os, math
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

CHAR_COLORS = {
    "James":  PAL["blue"],
    "Coco":   PAL["red"],
    "Rayman": PAL["yellow"],
    "Ellie":  PAL["green"],
    "Luca":   PAL["purple"],
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
FONT_BOARD_LOC   = load_font(40, bold=True)
FONT_BOARD_LABEL = load_font(28)
FONT_BOARD_SM    = load_font(22)
FONT_BOARD_XS    = load_font(16)
FONT_BOARD_TINY  = load_font(13)

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
    "James":  {"hp": 8, "hu": 6, "sa": 10, "seat": "White",
               "perks": ["Gaming Reflexes: reroll 1 die/turn",
                         "Pattern Recognition: peek deck top/day"],
               "flaw": "Wired: 1 Energy Drink/day or -2 Sanity",
               "hand": "Energy Drink x2, Pocketknife, Flashlight, Headphones"},
    "Coco":   {"hp": 6, "hu": 8, "sa": 12, "seat": "Red",
               "perks": ["Calming Presence: allies -1 Sanity loss",
                         "Touch of Hope (1x): heal any +4 HP",
                         "Light in the Dark: immune to Charlie"],
               "flaw": "No Home: alone non-house at night = -3 Sanity",
               "hand": "First Aid Kit, Comfort Blanket, Hopeful Tea, Spare Battery, Bracelet"},
    "Rayman": {"hp": 12, "hu": 10, "sa": 6, "seat": "Yellow",
               "perks": ["Speed: move 2 tiles per Move",
                         "Court Master: +1 atk at Basketball",
                         "Backboard Block: Defend shields adj."],
               "flaw": "Big Appetite: -2 Hunger/Tick. Loud: +1 Threat on move.",
               "hand": "Basketball, Sports Drink x2, Athletic Tape, Whistle"},
    "Ellie":  {"hp": 8, "hu": 10, "sa": 8, "seat": "Green",
               "perks": ["Crockpot Master: -1 ingredient (min 1)",
                         "Comfort Food: shared meal +1 Hu/Sa",
                         "Knows the Pantry: pick resource at home"],
               "flaw": "Particular Eater: can't eat raw food",
               "hand": "Crockpot, Soup Recipe, Cooking Knife, Pantry Key, Apron"},
    "Luca":   {"hp": 7, "hu": 8, "sa": 10, "seat": "Blue",
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

    img.save(os.path.join(DIRS["chars"], f"board_{char_name.lower()}.png"))
    print(f"  Player board: board_{char_name.lower()}.png")

# ---------------------------------------------------------------------------
# MAIN BOARD (4096x4096)
# ---------------------------------------------------------------------------
def generate_main_board():
    S = 4096
    img = Image.new("RGB", (S, S), (35, 32, 28))
    draw = ImageDraw.Draw(img)

    # Subtle background texture - concentric rings
    for r in range(100, S, 200):
        draw.ellipse([S//2 - r, S//2 - r, S//2 + r, S//2 + r],
                     outline=(38, 35, 31), width=1)

    # --- LOCATION NODES ---
    locations = {
        "James's House":       (1200, 1400, PAL["blue"],   "JH"),
        "Ellie & Luca's House":(2048, 2048, PAL["green"],  "EL"),
        "Rayman's House":      (2900, 1400, PAL["yellow"], "RH"),
        "Basketball Court":    (2048, 900,  PAL["orange"], "BC"),
        "Badminton Court":     (2048, 3200, PAL["purple"], "BD"),
    }

    # --- PATH EDGES (connections) ---
    paths = [
        ("James's House", "Ellie & Luca's House"),
        ("James's House", "Basketball Court"),
        ("Rayman's House", "Ellie & Luca's House"),
        ("Rayman's House", "Basketball Court"),
        ("Ellie & Luca's House", "Basketball Court"),
        ("Ellie & Luca's House", "Badminton Court"),
        ("James's House", "Badminton Court"),
        ("Rayman's House", "Badminton Court"),
    ]

    # Draw paths first (behind nodes)
    for loc_a, loc_b in paths:
        xa, ya = locations[loc_a][0], locations[loc_a][1]
        xb, yb = locations[loc_b][0], locations[loc_b][1]
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

    # Draw location nodes
    node_r = 220
    for name, (cx, cy, color, abbr) in locations.items():
        # Outer glow ring
        draw_circle(draw, cx, cy, node_r + 15, fill=None,
                    outline=(color[0]//3, color[1]//3, color[2]//3), width=6)
        # Main circle
        draw_circle(draw, cx, cy, node_r, fill=(40, 38, 34), outline=color, width=8)
        # Inner ring
        draw_circle(draw, cx, cy, node_r - 30, fill=None, outline=(50, 48, 42), width=2)

        # Location name (multi-line if needed)
        words = name.split()
        if len(words) <= 2:
            centered_text(draw, cx, cy - 20, name, FONT_BOARD_LOC, color)
        else:
            line1 = " ".join(words[:len(words)//2 + 1])
            line2 = " ".join(words[len(words)//2 + 1:])
            centered_text(draw, cx, cy - 35, line1, FONT_BOARD_LOC, color)
            centered_text(draw, cx, cy + 15, line2, FONT_BOARD_LOC, color)

        # Abbreviated tag
        centered_text(draw, cx, cy + 70, f"[ {abbr} ]", FONT_BOARD_SM, PAL["border"])

        # House vs Court indicator
        is_court = "Court" in name
        tag = "COURT" if is_court else "HOUSE"
        tag_color = PAL["orange"] if is_court else PAL["green"]
        centered_text(draw, cx, cy + 105, tag, FONT_BOARD_XS, tag_color)

        # Yield / defense info
        yield_info = {
            "James's House":       ("Energy, Battery, Junk", "Def +0  Sa +0"),
            "Ellie & Luca's House":("Food, Cloth, Pantry",   "Def +0  Sa +1"),
            "Rayman's House":      ("Sports, Drink, Tape",   "Def +1  Sa +0"),
            "Basketball Court":    ("Wood, Metal, Cloth",    "Def -1  Sa -1"),
            "Badminton Court":     ("Cloth, Wood, Metal",    "Def +1  Sa -1"),
        }
        yield_text, stat_text = yield_info.get(name, ("", ""))
        centered_text(draw, cx, cy + 140, yield_text, FONT_BOARD_TINY, PAL["text"])
        centered_text(draw, cx, cy + 165, stat_text, FONT_BOARD_TINY, tag_color)

    # --- DOOM TRACK (right side, vertical) ---
    doom_x = 3600
    doom_top = 300
    doom_bot = 3800
    step_h = (doom_bot - doom_top) / 30

    # Track background
    draw.rounded_rectangle([doom_x - 80, doom_top - 60, doom_x + 80, doom_bot + 60],
                           radius=20, fill=(35, 25, 25), outline=(100, 40, 40), width=4)

    # Title
    centered_text(draw, doom_x, doom_top - 30, "D O O M", FONT_BOARD_LOC, PAL["red"])

    # Steps 0-30
    thresholds = {10: "Threats +1", 15: "Market 1/day", 20: "+1 Sa loss", 25: "Bosses any", 30: "DEFEAT"}
    for step in range(31):
        sy = doom_top + int(step * step_h)
        # Color gradient: cool to warm
        t = step / 30
        r_val = int(40 + t * 180)
        g_val = int(60 - t * 40)
        b_val = int(80 - t * 60)
        step_color = (r_val, g_val, b_val)

        # Step marker
        draw.rounded_rectangle([doom_x - 55, sy, doom_x - 10, sy + int(step_h) - 2],
                               radius=3, fill=step_color)
        # Number
        draw.text((doom_x - 50, sy + 2), str(step), fill=PAL["text"], font=FONT_BOARD_TINY)

        # Threshold ribbons
        if step in thresholds:
            draw.rounded_rectangle([doom_x + 5, sy - 5, doom_x + 78, sy + int(step_h) + 3],
                                   radius=4, fill=(80, 25, 25), outline=PAL["red"], width=2)
            draw.text((doom_x + 10, sy), thresholds[step], fill=(255, 200, 150), font=FONT_BOARD_TINY)

    # --- TITLE ---
    centered_text(draw, S // 2, 200, "STARVE NO MORE", FONT_BOARD_TITLE, PAL["gold"])
    centered_text(draw, S // 2, 280, "Survive 7 Nights. Hold the Doom.", FONT_BOARD_LABEL, PAL["text"])

    # --- DAY COUNTER area (top left) ---
    draw.rounded_rectangle([100, 100, 500, 280], radius=15, fill=(40, 38, 34), outline=PAL["border"], width=3)
    centered_text(draw, 300, 140, "DAY COUNTER", FONT_BOARD_SM, PAL["gold"])
    centered_text(draw, 300, 180, "1  2  3  4  5  6  7", FONT_BOARD_LOC, PAL["text"])
    centered_text(draw, 300, 240, "Phase: I   II   III   IV", FONT_BOARD_XS, PAL["border"])

    # --- MARKET DISPLAY area (bottom) ---
    market_y = 3650
    draw.rounded_rectangle([400, market_y - 30, 2700, market_y + 200],
                           radius=15, fill=(40, 38, 34), outline=PAL["green"], width=3)
    centered_text(draw, 1550, market_y, "MARKET  ( 5 face-up cards )", FONT_BOARD_SM, PAL["green"])
    for i in range(5):
        sx = 520 + i * 400
        draw.rounded_rectangle([sx, market_y + 30, sx + 280, market_y + 170],
                               radius=8, fill=(30, 28, 26), outline=PAL["border"], width=2)
        centered_text(draw, sx + 140, market_y + 100, f"Slot {i+1}", FONT_BOARD_XS, PAL["border"])

    # --- DECK SLOTS (top, near day counter) ---
    deck_y = 350
    deck_labels = ["Phase\nDeck", "Threat\nDeck", "Visitor\nDeck", "Market\nDeck"]
    for i, label in enumerate(deck_labels):
        dx = 150 + i * 250
        draw.rounded_rectangle([dx, deck_y, dx + 180, deck_y + 250],
                               radius=8, fill=(30, 28, 26), outline=PAL["border"], width=2)
        lines = label.split("\n")
        for j, ln in enumerate(lines):
            centered_text(draw, dx + 90, deck_y + 100 + j * 30, ln, FONT_BOARD_XS, PAL["border"])

    # --- LEGEND REMINDER (bottom right) ---
    draw.rounded_rectangle([3300, 3650, 3980, 3950], radius=12, fill=(40, 38, 34), outline=PAL["border"], width=2)
    draw.text((3320, 3670), "SEVERITY DOTS:", fill=PAL["gold"], font=FONT_BOARD_XS)
    sev_info = ["1 dot = Flavor", "2 dots = Minor", "3 dots = Combat",
                "4 dots = Phase-shift", "5 dots = Boss"]
    for i, si in enumerate(sev_info):
        # Dots
        for d in range(i + 1):
            draw_circle(draw, 3340 + d * 18, 3718 + i * 46, 6, fill=PAL["red"])
        for d in range(i + 1, 5):
            draw_circle(draw, 3340 + d * 18, 3718 + i * 46, 6, fill=PAL["border"])
        draw.text((3445, 3708 + i * 46), si, fill=PAL["text"], font=FONT_BOARD_TINY)

    img.save(os.path.join(DIRS["board"], "main_board.png"))
    print(f"  Main board: main_board.png ({S}x{S})")

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
    generate_main_board()

    print("\nGenerating path tiles...")
    generate_path_tiles()

    print("\n=== DONE ===")
    print(f"Tokens:  {DIRS['tokens']}")
    print(f"Icons:   {DIRS['icons']}")
    print(f"Legend:  {DIRS['legend']}")
    print(f"Boards:  {DIRS['chars']}")
    print(f"Board:   {DIRS['board']}")

if __name__ == "__main__":
    main()
