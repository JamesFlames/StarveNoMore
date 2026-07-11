"""
Build the Starve No More TTS save JSON with all Phase D + E components.
Run: python scripts/build_save.py
Output: saves/StarveNoMore.json + saves/StarveNoMore.pretty.json
"""

import json, csv, math, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
SAVES = os.path.join(ROOT, "saves")
LUA_DIR = os.path.join(ROOT, "lua")
XML_DIR = os.path.join(ROOT, "xml")
ART_DIR = os.path.join(ROOT, "art")

# ---------------------------------------------------------------------------
# Asset URL resolution — maps logical names to local file:/// URLs
# Replace with hosted URLs (imgur/Steam Workshop) for publication
# ---------------------------------------------------------------------------

ASSET_MAP = {
    # Board
    "main_board":          "board/main_board.png",
    # Location tiles
    "tile_james":          "tiles/jameshome.png",
    "tile_rayman":         "tiles/raymanhome.png",
    "tile_ellie_luca":     "tiles/ellielucahome.png",
    "tile_basketball":     "tiles/basketballcourt.png",
    "tile_badminton":      "tiles/badmintoncourt.png",
    # Path variants
    "path_compact":        "board/path_compact.png",
    "path_sprawl":         "board/path_sprawl.png",
    "path_linear":         "board/path_linear.png",
    "path_ring":           "board/path_ring.png",
    "path_star":           "board/path_star.png",
    # Deck atlases
    "phase1_face":         "decks/phase1_face.png",
    "phase1_back":         "decks/phase1_back.png",
    "phase2_face":         "decks/phase2_face.png",
    "phase2_back":         "decks/phase2_back.png",
    "phase3_face":         "decks/phase3_face.png",
    "phase3_back":         "decks/phase3_back.png",
    "phase4_face":         "decks/phase4_face.png",
    "phase4_back":         "decks/phase4_back.png",
    "market_face":         "decks/market_face.png",
    "market_back":         "decks/market_back.png",
    "recipe_face":         "decks/recipe_face.png",
    "recipe_back":         "decks/recipe_back.png",
    "threat_face":         "decks/threat_face.png",
    "threat_back":         "decks/threat_back.png",
    "visitor_face":        "decks/visitor_face.png",
    "visitor_back":        "decks/visitor_back.png",
    "trophy_face":         "decks/trophy_face.png",
    "trophy_back":         "decks/trophy_back.png",
    # Tokens
    "token_wood":          "tokens/resource_wood.png",
    "token_metal":         "tokens/resource_metal.png",
    "token_cloth":         "tokens/resource_cloth.png",
    "token_food":          "tokens/resource_food.png",
    "token_energy":        "tokens/resource_energy.png",
    "token_battery":       "tokens/resource_battery.png",
    "doom_marker":         "tokens/doom_marker.png",
    "telltale_heart":      "tokens/telltale_heart.png",
    "sanity_d8":           "tokens/sanity_d8.png",
    # Stat icons
    "icon_health":         "icons/icon_health.png",
    "icon_hunger":         "icons/icon_hunger.png",
    "icon_sanity":         "icons/icon_sanity.png",
    # Severity legend
    "severity_legend":     "legend/severity_legend.png",
    # Character standees
    "char_james_front":    "characters/james_front.png",
    "char_james_back":     "characters/james_back.png",
    "char_coco_front":     "characters/coco_front.png",
    "char_coco_back":      "characters/coco_back.png",
    "char_rayman_front":   "characters/rayman_front.png",
    "char_rayman_back":    "characters/rayman_back.png",
    "char_ellie_front":    "characters/ellie_front.png",
    "char_ellie_back":     "characters/ellie_back.png",
    "char_luca_front":     "characters/luca_front.png",
    "char_luca_back":      "characters/luca_back.png",
    # Player boards
    "board_james":         "characters/board_james.png",
    "board_coco":          "characters/board_coco.png",
    "board_rayman":        "characters/board_rayman.png",
    "board_ellie":         "characters/board_ellie.png",
    "board_luca":          "characters/board_luca.png",
    # Boss standees (front only — back reuses front for now)
    "boss_deerclops_front":    "bosses/deerclops.png",
    "boss_deerclops_back":     "bosses/deerclops.png",
    "boss_eyeofterror_front":  "bosses/eye_of_terror.png",
    "boss_eyeofterror_back":   "bosses/eye_of_terror.png",
    "boss_thesource_front":    "bosses/the_source.png",
    "boss_thesource_back":     "bosses/the_source.png",
    "boss_treeguard_front":    "bosses/treeguard.png",
    "boss_treeguard_back":     "bosses/treeguard.png",
    "boss_charlie_front":      "bosses/charlie.png",
    "boss_charlie_back":       "bosses/charlie.png",
}

def art(name):
    """Resolve an asset name to a file:/// URL for TTS local testing."""
    if name in ASSET_MAP:
        path = os.path.join(ART_DIR, ASSET_MAP[name]).replace("\\", "/")
        return f"file:///{path}"
    # Fallback: try to find the file directly
    print(f"  WARNING: Unknown asset '{name}' — using placeholder")
    return f"https://i.imgur.com/PLACEHOLDER_{name}.png"

# Alias for backward compatibility in the script
ph = art

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_guid_counter = [0]
def guid():
    _guid_counter[0] += 1
    return f"{_guid_counter[0]:06x}"

def tf(x=0, y=1, z=0, rx=0, ry=0, rz=0, sx=1, sy=1, sz=1):
    return {
        "posX": x, "posY": y, "posZ": z,
        "rotX": rx, "rotY": ry, "rotZ": rz,
        "scaleX": sx, "scaleY": sy, "scaleZ": sz
    }

def base_obj(name, transform, nickname="", desc="", tags=None, locked=False, extra=None):
    o = {
        "Name": name,
        "Transform": transform,
        "Nickname": nickname,
        "Description": desc,
        "GMNotes": "",
        "ColorDiffuse": {"r": 1.0, "g": 1.0, "b": 1.0},
        "Tags": tags or [],
        "LayoutGroupSortIndex": 0,
        "Value": 0,
        "Locked": locked,
        "Grid": True,
        "Snap": True,
        "IgnoreFoW": False,
        "MeasureMovement": False,
        "DragSelectable": True,
        "Autoraise": True,
        "Sticky": True,
        "Tooltip": True,
        "GridProjection": False,
        "HideWhenFaceDown": False,
        "Hands": False,
        "LuaScript": "",
        "LuaScriptState": "",
        "XmlUI": "",
        "GUID": guid()
    }
    if extra:
        o.update(extra)
    return o

# ---------------------------------------------------------------------------
# read CSV data
# ---------------------------------------------------------------------------

def read_csv(filename):
    path = os.path.join(CONTENT, filename)
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

phase1 = read_csv("cards_phase1.csv")
phase2 = read_csv("cards_phase2.csv")
phase3 = read_csv("cards_phase3.csv")
phase4 = read_csv("cards_phase4.csv")
market = read_csv("cards_market.csv")
recipes = read_csv("cards_recipes.csv")
threats = read_csv("cards_threats.csv")
visitors = read_csv("cards_visitors.csv")
trophies = read_csv("cards_trophies.csv")

# ---------------------------------------------------------------------------
# deck builder
# ---------------------------------------------------------------------------

def make_deck(deck_id, face_url, back_url, num_w, num_h, cards_data,
              id_field, name_field, desc_func, tags_base, transform,
              nickname="", face_down=True):
    """Build a DeckCustom object from CSV rows."""
    custom_deck = {
        str(deck_id): {
            "FaceURL": face_url,
            "BackURL": back_url,
            "NumWidth": num_w,
            "NumHeight": num_h,
            "BackIsHidden": True,
            "UniqueBack": False,
            "Type": 0
        }
    }

    contained = []
    deck_ids = []
    for i, row in enumerate(cards_data):
        card_id = deck_id * 100 + i
        deck_ids.append(card_id)
        card = base_obj("Card", tf(),
                        nickname=row[name_field],
                        desc=desc_func(row),
                        tags=tags_base + [row[id_field]])
        card["CardID"] = card_id
        card["CustomDeck"] = dict(custom_deck)
        card["HideWhenFaceDown"] = True
        card["Hands"] = True
        contained.append(card)

    rz = 180 if face_down else 0
    t = dict(transform)
    t["rotZ"] = rz
    t["rotY"] = 180

    deck = base_obj("DeckCustom", t, nickname=nickname,
                    tags=[tags_base[0] + "Deck"] + tags_base)
    deck["DeckIDs"] = deck_ids
    deck["CustomDeck"] = custom_deck
    deck["ContainedObjects"] = contained
    deck["HideWhenFaceDown"] = True
    deck["Hands"] = False
    return deck

def phase_desc(row):
    s = f"Severity: {'●' * int(row['severity'])}{'○' * (5 - int(row['severity']))}\n"
    s += f"Immediate: {row['immediate']}"
    if row.get('ongoing'):
        s += f"\nOngoing: {row['ongoing']}"
    return s

def market_desc(row):
    s = f"Category: {row['category']}\nCost: {row['cost']}\n{row['effect']}"
    if row['persistent'] == 'Y':
        s += "\n(Persistent)"
    return s

def recipe_desc(row):
    return f"Ingredients: {row['ingredients']}\nCost: {row['cost']}\nEffect: {row['effect']}"

def threat_desc(row):
    s = f"Type: {row['type']}"
    if int(row['hp']) > 0:
        s += f"  HP: {row['hp']}  Atk: {row['attack']}"
    s += f"\nSeverity: {'●' * int(row['severity'])}{'○' * (5 - int(row['severity']))}"
    if row['special']:
        s += f"\nSpecial: {row['special']}"
    return s

def visitor_desc(row):
    return f"Trigger: {row['trigger']}\nImmediate: {row['immediate']}\n{row['departure']}"

def trophy_desc(row):
    return f"Boss: {row['boss']}\nBonus: {row['bonus']}"

# ---------------------------------------------------------------------------
# Phase D: scaffold (carried forward)
# ---------------------------------------------------------------------------

objects = []

# Hand zones from Phase D
hand_colors = [
    ("White", 0, -22, 0),
    ("Red", -21, -7, 72),
    ("Yellow", -13, 18, 144),
    ("Green", 13, 18, 216),
    ("Blue", 21, -7, 288),
]
for color, x, z, ry in hand_colors:
    objects.append({
        "Name": "HandTrigger",
        "Transform": tf(x, 4.5, z, ry=ry, sx=14, sy=6, sz=6),
        "Nickname": f"{color} Hand",
        "Description": f"Player hand zone ({color} seat). Cards placed here are private.",
        "Tags": ["HandZone", f"HandZone:{color}"],
        "Locked": True, "Grid": True, "Snap": True,
        "Autoraise": True, "Sticky": True, "Tooltip": True,
        "FogColor": color, "GUID": f"hand{color[:2].lower()}"
    })

# ---------------------------------------------------------------------------
# E.1  Main Board
# ---------------------------------------------------------------------------

# Snap points for the main board
board_snaps = []

# Location tile snap points (5 locations in the graph layout)
loc_positions = {
    "JamesHouse":     {"x": -8,  "y": 0.1, "z": -4},
    "EllieLucaHouse": {"x": 0,   "y": 0.1, "z": 0},
    "RaymanHouse":    {"x": 8,   "y": 0.1, "z": -4},
    "BasketballCourt":{"x": 0,   "y": 0.1, "z": -8},
    "BadmintonCourt": {"x": 0,   "y": 0.1, "z": 8},
}
for name, pos in loc_positions.items():
    board_snaps.append({
        "Position": pos, "Rotation": {"x": 0, "y": 0, "z": 0},
        "Tags": [f"Snap:Location:{name}"]
    })

# Doom track snap points (31 steps along the right edge)
for step in range(31):
    board_snaps.append({
        "Position": {"x": 10 + (step % 10) * 0.4, "y": 0.1, "z": 6 - (step // 10) * 1.5},
        "Rotation": {"x": 0, "y": 0, "z": 0},
        "Tags": [f"Snap:Doom:{step}"]
    })

# Day Counter snap
board_snaps.append({
    "Position": {"x": -10, "y": 0.1, "z": 8},
    "Rotation": {"x": 0, "y": 0, "z": 0},
    "Tags": ["Snap:DayCounter"]
})

# Market display (5 slots)
for i in range(5):
    board_snaps.append({
        "Position": {"x": -10 + i * 1.5, "y": 0.1, "z": 10},
        "Rotation": {"x": 0, "y": 0, "z": 0},
        "Tags": [f"Snap:Market:{i}"]
    })

# Deck slots
for deck_name, xoff in [("PhaseDeck", -7), ("ThreatDeck", -4), ("VisitorDeck", -1), ("MarketDeck", 2)]:
    board_snaps.append({
        "Position": {"x": xoff, "y": 0.1, "z": 12},
        "Rotation": {"x": 0, "y": 0, "z": 0},
        "Tags": [f"Snap:{deck_name}"]
    })

# Trophy display (4 slots)
for i in range(4):
    board_snaps.append({
        "Position": {"x": 5 + i * 1.5, "y": 0.1, "z": 12},
        "Rotation": {"x": 0, "y": 0, "z": 0},
        "Tags": [f"Snap:Trophy:{i}"]
    })

# Severity Legend snap
board_snaps.append({
    "Position": {"x": -3.5, "y": 0.1, "z": 13},
    "Rotation": {"x": 0, "y": 0, "z": 0},
    "Tags": ["Snap:SeverityLegend"]
})

# Help button anchor
board_snaps.append({
    "Position": {"x": 10, "y": 0.1, "z": -10},
    "Rotation": {"x": 0, "y": 0, "z": 0},
    "Tags": ["Snap:HelpButton"]
})

main_board = base_obj("Custom_Board", tf(0, 0.96, 0, sx=12, sy=1, sz=12),
                       nickname="Starve No More — Main Board",
                       desc="The suburban map. Doom threshold ribbons are printed on the board.",
                       tags=["Board", "MainBoard"],
                       locked=True)
main_board["CustomImage"] = {
    "ImageURL": ph("main_board"),
    "ImageSecondaryURL": "",
    "WidthScale": 0
}
main_board["AttachedSnapPoints"] = board_snaps
objects.append(main_board)

# ---------------------------------------------------------------------------
# E.3  Location tiles (5)
# ---------------------------------------------------------------------------

loc_data = {
    "JamesHouse":      ("James's House",       ph("tile_james"),    loc_positions["JamesHouse"]),
    "RaymanHouse":     ("Rayman's House",       ph("tile_rayman"),   loc_positions["RaymanHouse"]),
    "EllieLucaHouse":  ("Ellie & Luca's House", ph("tile_ellie_luca"), loc_positions["EllieLucaHouse"]),
    "BasketballCourt": ("Basketball Court",     ph("tile_basketball"), loc_positions["BasketballCourt"]),
    "BadmintonCourt":  ("Badminton Court",      ph("tile_badminton"),  loc_positions["BadmintonCourt"]),
}

tooltips = {
    "JamesHouse": "Yields: Energy Drink, Battery, Junk Food. Special: The Den — free trade once/day. James +1 Sanity at night.",
    "RaymanHouse": "Yields: Sports Equipment, Sports Drink, Athletic Tape. Special: The Garage — Rest +1 Health. Rayman +1 Health at night. Defense +1.",
    "EllieLucaHouse": "Yields: Food, Cloth, Pantry items. Special: The Kitchen — permanent Crockpot. Ellie/Luca +1 Sanity at night. Sanity mod +1.",
    "BasketballCourt": "Yields: Wood, Metal, Cloth. Special: Echoes — roll d6 on gather (6=bonus item, 1-2=lose 1 Sanity). Rayman +1 attack die. Sanity -1. Defense -1.",
    "BadmintonCourt": "Yields: Cloth, Wood, Metal. Special: The Net — +1 die defending. Highest threat draw. Sanity -1. Defense +1.",
}

for loc_key, (name, url, pos) in loc_data.items():
    # Per-location snap points (E.4): 5 character slots + 1 boss + 1 threat
    tile_snaps = []
    for ci in range(5):
        tile_snaps.append({
            "Position": {"x": -0.8 + ci * 0.4, "y": 0.3, "z": -0.3},
            "Rotation": {"x": 0, "y": 0, "z": 0},
            "Tags": [f"Snap:CharSlot:{ci}"]
        })
    tile_snaps.append({
        "Position": {"x": 0, "y": 0.3, "z": 0.5},
        "Rotation": {"x": 0, "y": 0, "z": 0},
        "Tags": ["Snap:BossSlot"]
    })
    tile_snaps.append({
        "Position": {"x": 0.8, "y": 0.3, "z": 0.5},
        "Rotation": {"x": 0, "y": 0, "z": 0},
        "Tags": ["Snap:ThreatSlot"]
    })

    tile = base_obj("Custom_Tile",
                    tf(pos["x"], 1.05, pos["z"], sx=2.5, sy=1, sz=2.5),
                    nickname=name,
                    desc=tooltips[loc_key],
                    tags=["Location", f"Location:{loc_key}"],
                    locked=True)
    tile["CustomImage"] = {
        "ImageURL": url,
        "ImageSecondaryURL": "",
        "WidthScale": 0,
        "CustomTile": {
            "Type": 2,  # rounded square
            "Thickness": 0.1,
            "Stackable": False,
            "Stretch": True
        }
    }
    tile["AttachedSnapPoints"] = tile_snaps
    objects.append(tile)

# ---------------------------------------------------------------------------
# E.5  Path-edge variant cards (3 sets stored in trays off-board)
# ---------------------------------------------------------------------------

for variant in ["Compact", "Sprawl", "Linear", "Ring", "Star"]:
    bag = base_obj("Bag",
                   tf(-16, 2, 12 + ["Compact","Sprawl","Linear","Ring","Star"].index(variant) * 3),
                   nickname=f"Path Edges: {variant}",
                   desc=f"Path-edge decorative tiles for the {variant} layout. Setup script activates one set.",
                   tags=["PathVariant", f"PathVariant:{variant}"])
    bag["ContainedObjects"] = []
    # 3 decorative path tiles per variant
    for pi in range(3):
        pt = base_obj("Custom_Tile", tf(sx=0.8, sy=1, sz=0.8),
                      nickname=f"{variant} Path {pi+1}",
                      tags=["PathEdge", f"PathVariant:{variant}"])
        pt["CustomImage"] = {
            "ImageURL": ph(f"path_{variant.lower()}"),
            "ImageSecondaryURL": "",
            "WidthScale": 0,
            "CustomTile": {"Type": 2, "Thickness": 0.05, "Stackable": False, "Stretch": True}
        }
        bag["ContainedObjects"].append(pt)
    objects.append(bag)

# ---------------------------------------------------------------------------
# E.6  Doom track marker
# ---------------------------------------------------------------------------

doom = base_obj("Custom_Token", tf(10, 1.5, 6),
                nickname="Doom Marker",
                desc="Doom: 0 / 30. Next threshold at 10: night threats +1.",
                tags=["DoomMarker"])
doom["CustomImage"] = {
    "ImageURL": ph("doom_marker"),
    "ImageSecondaryURL": "",
    "WidthScale": 0,
    "CustomToken": {"Thickness": 0.2, "MergeDistancePixels": 15, "StandUp": False, "Stackable": False}
}
objects.append(doom)

# ---------------------------------------------------------------------------
# E.7  Day Counter
# ---------------------------------------------------------------------------

day_counter = base_obj("Counter", tf(-10, 1.2, 8),
                       nickname="Day Counter",
                       desc="Current day. Advances each Dawn.",
                       tags=["DayCounter"],
                       locked=True)
day_counter["Value"] = 1
objects.append(day_counter)

# ---------------------------------------------------------------------------
# E.8  Phase Decks (4)
# ---------------------------------------------------------------------------

phase_decks = [
    (1, phase1, "Phase 1: Dusk of the Week", 4, 4),
    (2, phase2, "Phase 2: Strange Days", 4, 4),
    (3, phase3, "Phase 3: Long Nights", 4, 4),
    (4, phase4, "Phase 4: Final Hours", 4, 4),
]

for pi, (deck_num, cards, name, nw, nh) in enumerate(phase_decks):
    deck = make_deck(
        deck_id=deck_num,
        face_url=ph(f"phase{deck_num}_face"),
        back_url=ph(f"phase{deck_num}_back"),
        num_w=nw, num_h=nh,
        cards_data=cards,
        id_field="id", name_field="title",
        desc_func=phase_desc,
        tags_base=["PhaseCard", f"PhaseCard:P{deck_num}"],
        transform=tf(-7, 1.5, 12),
        nickname=name,
        face_down=True
    )
    # Stack the phase decks on top of each other (Phase 1 on top)
    deck["Transform"]["posY"] = 1.5 + (3 - pi) * 0.4
    objects.append(deck)

# ---------------------------------------------------------------------------
# E.9  Market deck + 5 face-up display slots
# ---------------------------------------------------------------------------

market_deck = make_deck(
    deck_id=10,
    face_url=ph("market_face"),
    back_url=ph("market_back"),
    num_w=7, num_h=8,
    cards_data=market,
    id_field="id", name_field="name",
    desc_func=market_desc,
    tags_base=["MarketCard"],
    transform=tf(2, 1.5, 12),
    nickname="Market Deck",
    face_down=True
)
objects.append(market_deck)

# 5 placeholder face-up market display cards (the setup script deals these)
# For now, place 5 Notecard placeholders at the market slots
for i in range(5):
    slot = base_obj("Notecard", tf(-10 + i * 1.5, 1.2, 10),
                    nickname=f"Market Slot {i+1}",
                    desc="A Market card will be dealt here during Setup.",
                    tags=["MarketSlot", f"MarketSlot:{i}"])
    objects.append(slot)

# ---------------------------------------------------------------------------
# E.10  Recipe cards (face-up reference)
# ---------------------------------------------------------------------------

for i, row in enumerate(recipes):
    card = base_obj("Card", tf(-14 + (i % 10) * 1.5, 1.2, -10 - (i // 10) * 2.2, rz=0, ry=180),
                    nickname=row["name"],
                    desc=recipe_desc(row),
                    tags=["RecipeCard", row["id"]])
    card["CardID"] = 2000 + i
    card["CustomDeck"] = {
        "20": {
            "FaceURL": ph("recipe_face"),
            "BackURL": ph("recipe_back"),
            "NumWidth": 5, "NumHeight": 4,
            "BackIsHidden": True, "UniqueBack": False, "Type": 0
        }
    }
    card["HideWhenFaceDown"] = False
    card["Hands"] = False
    objects.append(card)

# ---------------------------------------------------------------------------
# E.11  Threat deck
# ---------------------------------------------------------------------------

threat_deck = make_deck(
    deck_id=30,
    face_url=ph("threat_face"),
    back_url=ph("threat_back"),
    num_w=7, num_h=8,
    cards_data=threats,
    id_field="id", name_field="name",
    desc_func=threat_desc,
    tags_base=["ThreatCard"],
    transform=tf(-4, 1.5, 12),
    nickname="Threat Deck",
    face_down=True
)
# Sub-tag persistent threats
for card in threat_deck["ContainedObjects"]:
    for row in threats:
        if row["id"] in card["Tags"] and row["type"] == "Persistent":
            card["Tags"].append("Persistent")
            break
objects.append(threat_deck)

# ---------------------------------------------------------------------------
# E.12  Visitor deck
# ---------------------------------------------------------------------------

visitor_deck = make_deck(
    deck_id=40,
    face_url=ph("visitor_face"),
    back_url=ph("visitor_back"),
    num_w=3, num_h=2,
    cards_data=visitors,
    id_field="id", name_field="character",
    desc_func=visitor_desc,
    tags_base=["VisitorCard"],
    transform=tf(-1, 1.5, 12),
    nickname="Visitor Deck",
    face_down=True
)
objects.append(visitor_deck)

# ---------------------------------------------------------------------------
# E.13  Trophy cards (4, face-down in display row)
# ---------------------------------------------------------------------------

for i, row in enumerate(trophies):
    card = base_obj("Card", tf(5 + i * 1.5, 1.2, 12, rz=180, ry=180),
                    nickname=row["boss"] if "boss" in row else row.get("id",""),
                    desc=trophy_desc(row),
                    tags=["TrophyCard", row["id"]])
    card["CardID"] = 5000 + i
    card["CustomDeck"] = {
        "50": {
            "FaceURL": ph("trophy_face"),
            "BackURL": ph("trophy_back"),
            "NumWidth": 2, "NumHeight": 2,
            "BackIsHidden": True, "UniqueBack": False, "Type": 0
        }
    }
    card["HideWhenFaceDown"] = True
    card["Hands"] = False
    objects.append(card)

# ---------------------------------------------------------------------------
# E.14  Resource Infinite Bags (6)
# ---------------------------------------------------------------------------

resources = [
    ("Wood",         ph("token_wood"),    "Brown", 14, 1.5, -4),
    ("Metal",        ph("token_metal"),   "Grey",  14, 1.5, -2),
    ("Cloth",        ph("token_cloth"),   "White", 14, 1.5,  0),
    ("Food",         ph("token_food"),    "Red",   14, 1.5,  2),
    ("EnergyDrink",  ph("token_energy"),  "Yellow",14, 1.5,  4),
    ("Battery",      ph("token_battery"), "Blue",  14, 1.5,  6),
]

for res_name, token_url, color, x, y, z in resources:
    # Create the token template
    token = base_obj("Custom_Token", tf(),
                     nickname=res_name.replace("EnergyDrink", "Energy Drink"),
                     desc=f"{res_name} resource token.",
                     tags=["Resource", f"Resource:{res_name}"])
    token["CustomImage"] = {
        "ImageURL": token_url,
        "ImageSecondaryURL": "",
        "WidthScale": 0,
        "CustomToken": {"Thickness": 0.15, "MergeDistancePixels": 15, "StandUp": False, "Stackable": True}
    }

    bag = base_obj("Infinite_Bag", tf(x, y, z),
                   nickname=f"{res_name.replace('EnergyDrink', 'Energy Drink')} Supply",
                   desc=f"Infinite supply of {res_name.replace('EnergyDrink', 'Energy Drink')} tokens. Take as needed.",
                   tags=["ResourceBag", f"ResourceBag:{res_name}"])
    bag["ContainedObjects"] = [token]
    objects.append(bag)

# ---------------------------------------------------------------------------
# E.15  Dice
# ---------------------------------------------------------------------------

# 6 standard d6 in a combat tray
dice_tray = base_obj("Bag", tf(14, 1.5, -8),
                     nickname="Combat Dice Tray",
                     desc="6 combat d6. Roll for attacks.",
                     tags=["DiceTray"])
dice_tray["ContainedObjects"] = []
for di in range(6):
    d6 = base_obj("Die_6", tf(),
                  nickname=f"Combat d6 #{di+1}",
                  tags=["CombatDie"])
    dice_tray["ContainedObjects"].append(d6)
objects.append(dice_tray)

# Sanity d8 (custom)
sanity_d8 = base_obj("Custom_Dice", tf(14, 1.5, -10),
                     nickname="Sanity d8",
                     desc="Roll for Sanity-loss events. Face value = damage dealt.",
                     tags=["SanityD8"])
sanity_d8["CustomImage"] = {
    "ImageURL": ph("sanity_d8"),
    "ImageSecondaryURL": "",
    "WidthScale": 0,
    "CustomDice": {"Type": 1}  # d8
}
objects.append(sanity_d8)

# ---------------------------------------------------------------------------
# E.16  Character standees + player boards
# ---------------------------------------------------------------------------

characters = [
    ("James", "White", -6, -16, {"health": 8, "hunger": 6, "sanity": 10}),
    ("Coco",  "Red",   -3, -16, {"health": 6, "hunger": 8, "sanity": 12}),
    ("Rayman","Yellow", 0, -16, {"health": 12,"hunger": 10,"sanity": 6}),
    ("Ellie", "Green",  3, -16, {"health": 8, "hunger": 10,"sanity": 8}),
    ("Luca",  "Blue",   6, -16, {"health": 7, "hunger": 8, "sanity": 10}),
]

# Per-character standee tint applied to the figurine's card holder / base
# (TTS Figurine_Custom uses ColorDiffuse for the stand and as a multiply on
# the cardboard image; transparent-background character art ensures the
# standee silhouette stays close to the source while the holder picks up
# this colour).
STANDEE_COLORS = {
    "James":  {"r": 1.00, "g": 1.00, "b": 1.00},   # White
    "Coco":   {"r": 0.92, "g": 0.32, "b": 0.32},   # Red
    "Rayman": {"r": 0.35, "g": 0.78, "b": 0.40},   # Green
    "Ellie":  {"r": 0.62, "g": 0.82, "b": 0.95},   # Light Blue
    "Luca":   {"r": 1.00, "g": 0.60, "b": 0.20},   # Orange
}

for char_name, color, bx, bz, stats in characters:
    # Standee
    standee = base_obj("Figurine_Custom",
                       tf(loc_positions.get(
                           {"James":"JamesHouse","Rayman":"RaymanHouse",
                            "Ellie":"EllieLucaHouse","Luca":"EllieLucaHouse",
                            "Coco":"EllieLucaHouse"}[char_name],
                           {"x":0,"y":0.1,"z":0})["x"],
                          1.5,
                          loc_positions.get(
                           {"James":"JamesHouse","Rayman":"RaymanHouse",
                            "Ellie":"EllieLucaHouse","Luca":"EllieLucaHouse",
                            "Coco":"EllieLucaHouse"}[char_name],
                           {"x":0,"y":0.1,"z":0})["z"]),
                       nickname=char_name,
                       desc=f"{char_name} — character standee. Health {stats['health']} / Hunger {stats['hunger']} / Sanity {stats['sanity']}.",
                       tags=["Character", f"Character:{char_name}"])
    standee["CustomImage"] = {
        "ImageURL": ph(f"char_{char_name.lower()}_front"),
        "ImageSecondaryURL": ph(f"char_{char_name.lower()}_back"),
        "WidthScale": 0,
        "CustomFigurine": {"Type": 0}  # default figurine
    }
    # Per-character standee holder color
    if char_name in STANDEE_COLORS:
        standee["ColorDiffuse"] = STANDEE_COLORS[char_name]
    objects.append(standee)

    # Player board
    board_snaps_pb = []
    # Stat marker snaps (3 stats)
    for si, stat_name in enumerate(["Health", "Hunger", "Sanity"]):
        board_snaps_pb.append({
            "Position": {"x": -1.2, "y": 0.2, "z": -0.6 + si * 0.6},
            "Rotation": {"x": 0, "y": 0, "z": 0},
            "Tags": [f"Snap:Stat:{stat_name}"]
        })
    # Action cube snaps (3)
    for ai in range(3):
        board_snaps_pb.append({
            "Position": {"x": -0.3 + ai * 0.4, "y": 0.2, "z": 0.8},
            "Rotation": {"x": 0, "y": 0, "z": 0},
            "Tags": [f"Snap:ActionCube:{ai}"]
        })

    pboard = base_obj("Custom_Tile",
                      tf(bx, 1.1, bz, sx=3, sy=1, sz=2),
                      nickname=f"{char_name}'s Player Board",
                      desc=f"Health {stats['health']} | Hunger {stats['hunger']} | Sanity {stats['sanity']}",
                      tags=["PlayerBoard", f"PlayerBoard:{char_name}"])
    pboard["CustomImage"] = {
        "ImageURL": ph(f"board_{char_name.lower()}"),
        "ImageSecondaryURL": "",
        "WidthScale": 0,
        "CustomTile": {"Type": 0, "Thickness": 0.1, "Stackable": False, "Stretch": True}
    }
    pboard["AttachedSnapPoints"] = board_snaps_pb
    objects.append(pboard)

    # Stat markers (3 per character)
    for si, (stat_name, stat_val) in enumerate(stats.items()):
        marker = base_obj("Custom_Token",
                         tf(bx - 1.2, 1.4, bz - 0.6 + si * 0.6, sx=0.3, sy=0.3, sz=0.3),
                         nickname=f"{char_name} {stat_name.title()}",
                         desc=f"{stat_name.title()}: {stat_val}",
                         tags=["StatMarker", f"StatMarker:{char_name}:{stat_name}"])
        marker["CustomImage"] = {
            "ImageURL": ph(f"icon_{stat_name}"),
            "ImageSecondaryURL": "",
            "WidthScale": 0,
            "CustomToken": {"Thickness": 0.1, "MergeDistancePixels": 15, "StandUp": False, "Stackable": False}
        }
        objects.append(marker)

# ---------------------------------------------------------------------------
# E.17  Boss standees (off-board in a tray)
# ---------------------------------------------------------------------------

bosses = [
    ("Deerclops", 6, 3),
    ("EyeOfTerror", 8, 3),
    ("TheSource", 8, 3),   # retuned 10 -> 8 (batch 4 W3 calibration)
    ("Charlie", 4, 2),
    ("Treeguard", 5, 2),   # Phase 2.5 mini-boss — wakes at Dusk of Day 4 (lua/treeguard.lua)
]

boss_pool = base_obj("Bag", tf(16, 2, 10),
                     nickname="Boss Pool",
                     desc="Boss standees. Placed on the map by Dawn card effects.",
                     tags=["BossPool"])
boss_pool["ContainedObjects"] = []

for boss_name, hp, atk in bosses:
    boss = base_obj("Figurine_Custom", tf(sx=1.5, sy=1.5, sz=1.5),
                    nickname=boss_name.replace("EyeOfTerror","Eye of Terror").replace("TheSource","The Source"),
                    desc=f"Boss. HP {hp}, Attack {atk}. Larger than character standees.",
                    tags=["Boss", f"Boss:{boss_name}"],
                    locked=True)
    boss["CustomImage"] = {
        "ImageURL": ph(f"boss_{boss_name.lower()}_front"),
        "ImageSecondaryURL": ph(f"boss_{boss_name.lower()}_back"),
        "WidthScale": 0,
        "CustomFigurine": {"Type": 0}
    }
    boss_pool["ContainedObjects"].append(boss)
objects.append(boss_pool)

# ---------------------------------------------------------------------------
# E.18  Telltale Heart supply (Bag of 5 tokens)
# ---------------------------------------------------------------------------

# Sealed Basement (Design §13.5 / design_batch3.md §3): a fixed Pry
# destination under Ellie & Luca's House, visible from setup — the map's
# guaranteed early-game goal for whoever crafts a Pry tool.
_elh = loc_positions["EllieLucaHouse"]
basement = base_obj("BlockSquare",
                    tf(_elh["x"] - 3.5, 1, _elh["z"] - 3.5, sx=1.4, sy=0.5, sz=1.4),
                    nickname="The Sealed Basement",
                    desc="A padlocked hatch under Ellie & Luca's House. Someone stocked it before the week began.\n\nPry (free action + Crowbar / Lockpick / Pry Bar): a free Market Item, plus 2 Food + 1 Wood + 1 Battery.",
                    tags=["SealedBasement"])
basement["ColorDiffuse"] = {"r": 0.28, "g": 0.22, "b": 0.15}
objects.append(basement)

heart_bag = base_obj("Bag", tf(14, 1.5, 8),
                     nickname="Telltale Heart Supply",
                     desc="5 Telltale Hearts. Cook to create; spend to revive a Down character.",
                     tags=["TelltaleHeartSupply"])
heart_bag["ContainedObjects"] = []
for hi in range(5):
    heart = base_obj("Custom_Token", tf(),
                     nickname="Telltale Heart",
                     desc="Use at a Down character's location to revive them. Reviver pays 2 Health. Revived returns at half max stats.",
                     tags=["TelltaleHeart"])
    heart["CustomImage"] = {
        "ImageURL": ph("telltale_heart"),
        "ImageSecondaryURL": "",
        "WidthScale": 0,
        "CustomToken": {"Thickness": 0.2, "MergeDistancePixels": 15, "StandUp": False, "Stackable": True}
    }
    heart_bag["ContainedObjects"].append(heart)
objects.append(heart_bag)

# ---------------------------------------------------------------------------
# E.19  Severity Legend card
# ---------------------------------------------------------------------------

legend = base_obj("Card", tf(-3.5, 1.2, 13, rz=0, ry=180, sx=1.5, sy=1, sz=1.5),
                  nickname="Severity Legend",
                  desc="●○○○○ Atmospheric\n●●○○○ Minor stat hit\n●●●○○ Combat/lasting\n●●●●○ Phase-shift\n●●●●● Boss/apocalyptic",
                  tags=["SeverityLegend"],
                  locked=True)
legend["CardID"] = 9900
legend["CustomDeck"] = {
    "99": {
        "FaceURL": ph("severity_legend"),
        "BackURL": ph("severity_legend"),
        "NumWidth": 1, "NumHeight": 1,
        "BackIsHidden": False, "UniqueBack": False, "Type": 0
    }
}
legend["HideWhenFaceDown"] = False
objects.append(legend)

# ---------------------------------------------------------------------------
# E.20  Rules Quick-Start notecard
# ---------------------------------------------------------------------------

quickstart_text = """STARVE NO MORE — QUICK START

GOAL: Survive 7 nights. Doom < 30. Don't all go Down.

EACH DAY:
1. Dawn — flip a Dawn card. Read it. Doom advances.
2. Day — 3 actions each: Move, Gather, Craft, Cook, Fight, Rest, Cleanse. Trade is free.
3. Dusk — declare where you sleep.
4. Night — threats drawn. Fight or suffer. Charlie attacks the lightless.
5. Tick — lose 1 Hunger, 1 Sanity. Day advances.

STATS: Health 0 = Down. Hunger 0 = starve. Sanity 0 = Lost.
Below 3 in any stat = Bad Things Happen.

HOVER anything for its rule. Press ? for Help. Click "What now?" if stuck.
"""

notecard = base_obj("Notecard", tf(12, 1.2, -14),
                    nickname="Quick Start",
                    desc=quickstart_text.strip(),
                    tags=["QuickStart"])
objects.append(notecard)

# ---------------------------------------------------------------------------
# Assemble the full save
# ---------------------------------------------------------------------------

save = {
    "SaveName": "Starve No More",
    "GameMode": "Starve No More",
    "Date": "",
    "VersionNumber": "v13.x",
    "GameType": "",
    "GameComplexity": "",
    "Tags": ["Card Games", "Strategy", "Cooperative", "Survival"],
    "Gravity": 0.5,
    "PlayArea": 1.0,
    "Table": "Table_Hexagon",
    "Sky": "Sky_Museum",
    "Note": "Starve No More — cooperative survival board game for 3-5 players.",
    "TabStates": {},
    "LuaScript": "",  # populated below from lua/ files
    "LuaScriptState": "",
    "XmlUI": "",  # populated below from xml/ files
    "Grid": {
        "Type": 0, "Lines": False, "Color": {"r": 0, "g": 0, "b": 0},
        "Offset": False, "BothSnapping": False, "xSize": 2, "ySize": 2
    },
    "Lighting": {
        "LightIntensity": 0.55,
        "LightColor": {"r": 1.0, "g": 0.95, "b": 0.85},
        "AmbientIntensity": 1.0,
        "AmbientType": 1,
        "AmbientSkyColor": {"r": 0.35, "g": 0.4, "b": 0.55},
        "AmbientEquatorColor": {"r": 0.45, "g": 0.4, "b": 0.35},
        "AmbientGroundColor": {"r": 0.25, "g": 0.2, "b": 0.18},
        "ReflectionIntensity": 0.5,
        "LutIndex": 0,
        "LutContribution": 1.0
    },
    "Hands": {"Enable": True, "DisableUnused": False, "Hiding": 0},
    "Turns": {
        "Enable": False, "Type": 0, "TurnOrder": [], "Reverse": False,
        "SkipEmpty": False, "DisableInteractions": False, "PassTurns": True, "TurnColor": ""
    },
    "ObjectStates": objects,
    "DecalPallet": [],
    "MusicPlayer": {
        "RepeatSong": False, "PlaylistEntry": 0,
        "CurrentAudioTitle": "", "CurrentAudioURL": "", "AudioLibrary": []
    },
    "ComponentTags": {
        "labels": []
    }
}

# ---------------------------------------------------------------------------
# Concatenate Lua files into the save's LuaScript field
# Order matters: helpers first, then global, then the rest.
# ---------------------------------------------------------------------------

LUA_LOAD_ORDER = [
    "helpers.lua",
    "global.lua",
    "audio_manifest.lua",   # auto-gen by scripts/generate_audio_manifest.py — defines AUDIO
    "audio.lua",            # defines Audio.* (depends on AUDIO)
    "whatnow_hints.lua",    # auto-gen by scripts/generate_whatnow_hints.py — defines WHATNOW_HINTS
    "market_data.lua",      # auto-gen by scripts/generate_market_data.py — defines MARKET_COSTS
    "threat_types.lua",     # auto-gen by scripts/generate_threat_types.py — defines THREAT_TYPE_BY_NAME
    "setup.lua",
    "day_loop.lua",
    "effects/dawn_effects.lua",
    "combat.lua",
    "crafting.lua",
    "night.lua",
    "tick_victory.lua",
    "actions.lua",
    "treeguard.lua",        # Phase 2.5 mini-boss (wake/appease/defeat)
    "signatures.lua",       # Signature Moves (§6.7) — once-per-game per-character actions
    "telemetry.lua",        # Session log: chronicle setup/turns/beats + Copy Session Log export (batch 4 W0)
    "ui_banner.lua",
    "ui_actionbar.lua",
    "ui_controls.lua",
    "ui_setup.lua",
    "ui_help.lua",
    "ui_rules.lua",         # "Rules in effect" panel + day-cycle strip
    "ui_mood.lua",
    "audit.lua",
    "selftest.lua",         # runSelfTest() — scripted in-TTS smoke test (J.11)
]

lua_parts = []
for lua_file in LUA_LOAD_ORDER:
    lua_path = os.path.join(LUA_DIR, lua_file)
    if os.path.isfile(lua_path):
        with open(lua_path, "r", encoding="utf-8") as f:
            lua_parts.append(f"-- ========== {lua_file} ==========")
            lua_parts.append(f.read())
    else:
        print(f"WARNING: Lua file not found: {lua_file}")

# Also pick up any extra .lua files not in the explicit order
for lua_path in sorted(glob.glob(os.path.join(LUA_DIR, "**", "*.lua"), recursive=True)):
    rel = os.path.relpath(lua_path, LUA_DIR).replace("\\", "/")
    if rel not in LUA_LOAD_ORDER:
        with open(lua_path, "r", encoding="utf-8") as f:
            lua_parts.append(f"-- ========== {rel} ==========")
            lua_parts.append(f.read())
        print(f"NOTE: Extra Lua file included: {rel}")

save["LuaScript"] = "\n\n".join(lua_parts)
print(f"Lua script assembled: {len(LUA_LOAD_ORDER)} files, {len(save['LuaScript'])} chars")

# ---------------------------------------------------------------------------
# Load XML UI from xml/ directory
# ---------------------------------------------------------------------------

XML_LOAD_ORDER = [
    "global_ui.xml",
]

xml_parts = []
for xml_file in XML_LOAD_ORDER:
    xml_path = os.path.join(XML_DIR, xml_file)
    if os.path.isfile(xml_path):
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_parts.append(f.read())
    else:
        print(f"WARNING: XML file not found: {xml_file}")

# Also pick up any extra .xml files not in the explicit order
for xml_path in sorted(glob.glob(os.path.join(XML_DIR, "*.xml"))):
    rel = os.path.relpath(xml_path, XML_DIR).replace("\\", "/")
    if rel not in XML_LOAD_ORDER:
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_parts.append(f.read())
        print(f"NOTE: Extra XML file included: {rel}")

save["XmlUI"] = "\n".join(xml_parts)
print(f"XML UI assembled: {len(XML_LOAD_ORDER)} files, {len(save['XmlUI'])} chars")

# Collect all unique tags used across all objects
all_tags = set()
def collect_tags(obj_list):
    for o in obj_list:
        for t in o.get("Tags", []):
            all_tags.add(t)
        if "AttachedSnapPoints" in o:
            for sp in o["AttachedSnapPoints"]:
                for t in sp.get("Tags", []):
                    all_tags.add(t)
        if "ContainedObjects" in o:
            collect_tags(o["ContainedObjects"])

collect_tags(objects)
save["ComponentTags"]["labels"] = [
    {"displayed": t, "normalized": t.lower()} for t in sorted(all_tags)
]

# Write outputs
os.makedirs(SAVES, exist_ok=True)

with open(os.path.join(SAVES, "StarveNoMore.json"), "w", encoding="utf-8") as f:
    json.dump(save, f, separators=(",", ":"))

with open(os.path.join(SAVES, "StarveNoMore.pretty.json"), "w", encoding="utf-8") as f:
    json.dump(save, f, indent=2, ensure_ascii=False)

# Stats
total_objects = len(objects)
contained = sum(len(o.get("ContainedObjects", [])) for o in objects)
print(f"Save built: {total_objects} top-level objects, {contained} contained objects")
print(f"Files written: saves/StarveNoMore.json, saves/StarveNoMore.pretty.json")
