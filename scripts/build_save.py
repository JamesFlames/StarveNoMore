"""
Build the Starve No More TTS save JSON with all Phase D + E components.

Run: python scripts/build_save.py
Output: saves/StarveNoMore.json + saves/StarveNoMore.pretty.json

Publish mode (hosted assets instead of file:/// + localhost):
    python scripts/build_save.py --publish https://your.cdn/starvenomore [--out path]
Output: saves/StarveNoMore.publish.json (or --out). The dev saves are not
touched. Upload the repo's art/, sounds/ and PlayerRules.html under the base
URL so the rewritten links resolve.
"""

import argparse
import json
import csv
import os
import glob

from generate_notebook import md_to_text   # shared md→text for the Quick Start notecard
import board_geometry                       # shared board image↔world geometry

_ap = argparse.ArgumentParser(description="Assemble the TTS save JSON.")
_ap.add_argument("--publish", metavar="BASE_URL", default=None,
                 help="use BASE_URL for every asset instead of file:/// art "
                      "and http://localhost:8080 sounds/rules; writes a "
                      "separate publish save")
_ap.add_argument("--out", default=None,
                 help="output path for the publish save "
                      "(default: saves/StarveNoMore.publish.json)")
ARGS = _ap.parse_args()

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
    "starting_face":       "decks/starting_face.png",
    "starting_back":       "decks/starting_back.png",
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

def served(relpath):
    """URL for a repo-root-relative path: the local dev server by default
    (scripts/serve_art.bat), the hosted base in --publish builds."""
    base = ARGS.publish or "http://localhost:8080"
    return base.rstrip("/") + "/" + relpath


def art(name):
    """Resolve an asset name to a URL: file:/// for local testing, the
    hosted base URL in --publish builds."""
    if name in ASSET_MAP:
        if ARGS.publish:
            return served("art/" + ASSET_MAP[name])
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
starting = read_csv("cards_starting.csv")

# ---------------------------------------------------------------------------
# Atlas manifest: NumWidth/NumHeight come from what the atlas generator
# actually rendered (art/decks/atlas_manifest.json), never hand-declared —
# and a card-count mismatch means the atlases are stale, which is a hard stop.
# ---------------------------------------------------------------------------
ATLAS_MANIFEST_PATH = os.path.join(ART_DIR, "decks", "atlas_manifest.json")
if not os.path.isfile(ATLAS_MANIFEST_PATH):
    raise SystemExit("art/decks/atlas_manifest.json missing - run scripts/generate_card_atlases.py first")
with open(ATLAS_MANIFEST_PATH, "r", encoding="utf-8") as _f:
    ATLAS_MANIFEST = json.load(_f)

def atlas_grid(csv_name, rows):
    entry = ATLAS_MANIFEST.get(csv_name)
    if not entry:
        raise SystemExit(f"atlas_manifest.json has no entry for {csv_name} - rerun scripts/generate_card_atlases.py")
    if entry["cards"] != len(rows):
        raise SystemExit(f"{csv_name}: atlas rendered for {entry['cards']} cards but CSV now has "
                         f"{len(rows)} - rerun scripts/generate_card_atlases.py")
    return entry["cols"], entry["rows"]

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

# Snap points for the main board.
# AttachedSnapPoints are stored in BOARD-LOCAL space; the board's transform
# scale is 12, so Lua's board.positionToWorld(snap.position) multiplies
# these by 12. Author in world units and divide by BOARD_SCALE here — the
# old world-authored values made moveDoomMarker fling the marker to
# (120, 72), far off the table.
BOARD_SCALE = board_geometry.BOARD_SCALE

def board_snap(wx, wz, tags):
    return {
        "Position": {"x": wx / BOARD_SCALE, "y": 0.02, "z": wz / BOARD_SCALE},
        "Rotation": {"x": 0, "y": 0, "z": 0},
        "Tags": tags,
    }

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
    board_snaps.append(board_snap(pos["x"], pos["z"], [f"Snap:Location:{name}"]))

# Doom track snap points — 31 steps down the printed vertical track on the
# board's right side (drawn by generate_assets.generate_main_board; geometry
# shared via board_geometry so art and snaps can't drift apart). Consumed by
# moveDoomMarker (setup.lua), which slides the locked Doom marker along them.
for step in range(31):
    lx, lz = board_geometry.doom_step_local(step)
    board_snaps.append({
        "Position": {"x": lx, "y": 0.02, "z": lz},
        "Rotation": {"x": 0, "y": 0, "z": 0},
        "Tags": [f"Snap:Doom:{step}"]
    })

# Day Counter snap
board_snaps.append(board_snap(-10, 8, ["Snap:DayCounter"]))

# Market display (5 slots) — a column down the board's left flank.
# TTS cards are ~2.3 units wide/3.2 long, so slots need ~3.6 units of
# separation or the dealt cards physically shove each other (and anything
# nearby — they used to bury the Day Counter and clip the board edge).
MARKET_SLOT_POSITIONS = [(-12.5, 9.0 - i * 3.6) for i in range(5)]
for i, (msx, msz) in enumerate(MARKET_SLOT_POSITIONS):
    board_snaps.append(board_snap(msx, msz, [f"Snap:Market:{i}"]))

# Deck slots
for deck_name, xoff in [("PhaseDeck", -7), ("ThreatDeck", -4), ("VisitorDeck", -1), ("MarketDeck", 2)]:
    board_snaps.append(board_snap(xoff, 12, [f"Snap:{deck_name}"]))

# Trophy display (4 slots)
for i in range(4):
    board_snaps.append(board_snap(5 + i * 1.5, 12, [f"Snap:Trophy:{i}"]))

# Severity Legend snap
board_snaps.append(board_snap(-3.5, 13, ["Snap:SeverityLegend"]))

# Help button anchor
board_snaps.append(board_snap(10, -10, ["Snap:HelpButton"]))

# Tooltip=False: no hover text on the board itself — players can see what
# it is, and the popup got in the way of hovering pieces on top of it.
main_board = base_obj("Custom_Board", tf(0, 0.96, 0, sx=12, sy=1, sz=12),
                       nickname="Starve No More — Main Board",
                       desc="The suburban map. Doom threshold ribbons are printed on the board.",
                       tags=["Board", "MainBoard"],
                       locked=True,
                       extra={"Tooltip": False})
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

    # ry=180: a Custom_Tile at rotY=0 renders its illustration rotated 180°
    # in the default view (the day-counter/cards convention) — this keeps
    # the house/court art upright for the players.
    tile = base_obj("Custom_Tile",
                    tf(pos["x"], 1.05, pos["z"], ry=180, sx=2.5, sy=1, sz=2.5),
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

# Everything players never touch lives UNDER the table (playtest: "players
# should not see decks/tokens unless actively relevant"). Scripts find
# objects by tag wherever they sit, and every card reveal/discard position
# is authored in absolute board coordinates, so the machinery works from
# down there. Unlocked objects (a deck sheds its container when it shrinks
# to one card) rest on a locked catch shelf so nothing falls into the void.
LIBRARY_Y = -2.5             # resting height for hidden components
SUPPLY_SHELF_X = 25.0        # resource bags / dice / hearts / boss pool
SUPPLY_SHELF_X2 = 28.0       # decorative path-variant trays, one row further out
LIBRARY_X = -25.0            # decks / trophies / legend (west column)
LIBRARY_X2 = -28.0           # trophy cards + starting decks
BENCH_X = -23.0              # unused character standees (see lua/helpers.lua)

for variant in ["Compact", "Sprawl", "Linear", "Ring", "Star"]:
    bag = base_obj("Bag",
                   tf(SUPPLY_SHELF_X2, LIBRARY_Y, 2 + ["Compact","Sprawl","Linear","Ring","Star"].index(variant) * 3),
                   nickname=f"Path Edges: {variant}",
                   desc=f"Decorative path tiles for the {variant} map layout. Purely cosmetic — safe to ignore during play.",
                   tags=["PathVariant", f"PathVariant:{variant}"],
                   locked=True)
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

# Spawns locked on step 0 of the printed Doom track; only moveDoomMarker
# (setup.lua) moves it — players can't drag it. y=1.2 mirrors the marker
# rest height in moveDoomMarker.
_doom_x, _doom_z = board_geometry.doom_step_world(0)
doom = base_obj("Custom_Token", tf(_doom_x, 1.2, _doom_z),
                nickname="Doom Marker",
                desc="Doom: 0 / 30. Next threshold at 10: night threats +1.",
                tags=["DoomMarker"],
                locked=True)
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

# ry=0: playtest showed the Counter's digits render right-side-up at 0
# (unlike flat tiles/cards, whose art needs the 180 treatment). y=1.4
# keeps it clear of the board's top surface — spawned lower, it clipped
# into the board and was invisible until physics nudged it out. The
# script alone advances it: onLoad / lockdownCriticalObjects set
# interactable=false so players can't click the counter's +/- buttons.
day_counter = base_obj("Counter", tf(-10, 1.4, 8),
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
    (1, phase1, "Phase 1: Dusk of the Week"),
    (2, phase2, "Phase 2: Strange Days"),
    (3, phase3, "Phase 3: Long Nights"),
    (4, phase4, "Phase 4: Final Hours"),
]

for pi, (deck_num, cards, name) in enumerate(phase_decks):
    nw, nh = atlas_grid(f"cards_phase{deck_num}.csv", cards)
    deck = make_deck(
        deck_id=deck_num,
        face_url=ph(f"phase{deck_num}_face"),
        back_url=ph(f"phase{deck_num}_back"),
        num_w=nw, num_h=nh,
        cards_data=cards,
        id_field="id", name_field="title",
        desc_func=phase_desc,
        tags_base=["PhaseCard", f"PhaseCard:P{deck_num}"],
        # In the under-table library — the drawn Dawn card appears at the
        # fixed DAWN_REVEAL_POS on the board (day_loop.lua).
        transform=tf(LIBRARY_X, LIBRARY_Y, 8 - pi * 3),
        nickname=name,
        face_down=True
    )
    objects.append(deck)

# ---------------------------------------------------------------------------
# E.9  Market deck + 5 face-up display slots
# ---------------------------------------------------------------------------

_mw, _mh = atlas_grid("cards_market.csv", market)
market_deck = make_deck(
    deck_id=10,
    face_url=ph("market_face"),
    back_url=ph("market_back"),
    num_w=_mw, num_h=_mh,
    cards_data=market,
    id_field="id", name_field="name",
    desc_func=market_desc,
    tags_base=["MarketCard"],
    transform=tf(LIBRARY_X, LIBRARY_Y, -10),
    nickname="Market Deck",
    face_down=True
)
objects.append(market_deck)

# 5 market display slots (the setup script deals a face-up card onto each).
# Locked notecards so physics can never wedge them under the board.
for i, (msx, msz) in enumerate(MARKET_SLOT_POSITIONS):
    slot = base_obj("Notecard", tf(msx, 1.05, msz),
                    nickname=f"Market Slot {i+1}",
                    desc="A Market card is dealt face-up here during Setup. Craft claims the card; the deck refills the slot.",
                    tags=["MarketSlot", f"MarketSlot:{i}"],
                    locked=True)
    objects.append(slot)

# ---------------------------------------------------------------------------
# E.10  Recipe cards (face-up reference)
# ---------------------------------------------------------------------------

_rw, _rh = atlas_grid("cards_recipes.csv", recipes)
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
            "NumWidth": _rw, "NumHeight": _rh,
            "BackIsHidden": True, "UniqueBack": False, "Type": 0
        }
    }
    card["HideWhenFaceDown"] = False
    card["Hands"] = False
    objects.append(card)

# ---------------------------------------------------------------------------
# E.11  Threat deck
# ---------------------------------------------------------------------------

_tw, _th = atlas_grid("cards_threats.csv", threats)
threat_deck = make_deck(
    deck_id=30,
    face_url=ph("threat_face"),
    back_url=ph("threat_back"),
    num_w=_tw, num_h=_th,
    cards_data=threats,
    id_field="id", name_field="name",
    desc_func=threat_desc,
    tags_base=["ThreatCard"],
    transform=tf(LIBRARY_X, LIBRARY_Y, -4),
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

_vw, _vh = atlas_grid("cards_visitors.csv", visitors)
visitor_deck = make_deck(
    deck_id=40,
    face_url=ph("visitor_face"),
    back_url=ph("visitor_back"),
    num_w=_vw, num_h=_vh,
    cards_data=visitors,
    id_field="id", name_field="character",
    desc_func=visitor_desc,
    tags_base=["VisitorCard"],
    transform=tf(LIBRARY_X, LIBRARY_Y, -7),
    nickname="Visitor Deck",
    face_down=True
)
objects.append(visitor_deck)

# ---------------------------------------------------------------------------
# E.13  Trophy cards (4, face-down in display row)
# ---------------------------------------------------------------------------

for i, row in enumerate(trophies):
    card = base_obj("Card", tf(LIBRARY_X2, LIBRARY_Y, 8 - i * 3, rz=180, ry=180),
                    nickname=row["boss"] if "boss" in row else row.get("id",""),
                    desc=trophy_desc(row),
                    tags=["TrophyCard", row["id"]])
    card["CardID"] = 5000 + i
    card["CustomDeck"] = {
        "50": {
            "FaceURL": ph("trophy_face"),
            "BackURL": ph("trophy_back"),
            "NumWidth": atlas_grid("cards_trophies.csv", trophies)[0],
            "NumHeight": atlas_grid("cards_trophies.csv", trophies)[1],
            "BackIsHidden": True, "UniqueBack": False, "Type": 0
        }
    }
    card["HideWhenFaceDown"] = True
    card["Hands"] = False
    objects.append(card)

# ---------------------------------------------------------------------------
# E.13b  Starting-hand decks — one small deck per character, stacked in a
# pile off the board's right edge. Setup deals each picked character's deck
# into that player's hand (dealStartingHands in lua/setup.lua). James's two
# Energy Drinks are resource tokens, granted by the same function.
# ---------------------------------------------------------------------------

_sw, _sh = atlas_grid("cards_starting.csv", starting)
starting_custom_deck = {
    "60": {
        "FaceURL": ph("starting_face"),
        "BackURL": ph("starting_back"),
        "NumWidth": _sw,
        "NumHeight": _sh,
        "BackIsHidden": True,
        "UniqueBack": False,
        "Type": 0
    }
}

for si, start_char in enumerate(["James", "Coco", "Rayman", "Ellie", "Luca"]):
    contained = []
    deck_ids = []
    for i, row in enumerate(starting):
        if row["character"] != start_char:
            continue
        for _copy in range(max(1, int(row.get("count") or 1))):
            card = base_obj("Card", tf(),
                            nickname=row["name"],
                            desc=row["effect"],
                            tags=["StartingItem", row["id"]])
            card["CardID"] = 6000 + i
            card["CustomDeck"] = dict(starting_custom_deck)
            card["HideWhenFaceDown"] = True
            card["Hands"] = True
            contained.append(card)
            deck_ids.append(6000 + i)
    # The StartingHand:<name> tag lives on the DECK only (not its cards), so
    # dealStartingHands can never mistake an already-dealt card for the deck.
    start_deck = base_obj("DeckCustom",
                          tf(LIBRARY_X2, LIBRARY_Y, -5 - si * 2.5, ry=180, rz=180),
                          nickname=f"{start_char}'s Starting Hand",
                          desc=f"{start_char}'s personal items. Dealt to {start_char}'s player automatically during Setup.",
                          tags=["StartingHandDeck", f"StartingHand:{start_char}"])
    start_deck["DeckIDs"] = deck_ids
    start_deck["CustomDeck"] = dict(starting_custom_deck)
    start_deck["ContainedObjects"] = contained
    start_deck["HideWhenFaceDown"] = True
    start_deck["Hands"] = False
    objects.append(start_deck)

# ---------------------------------------------------------------------------
# E.14  Resource Infinite Bags (6)
# ---------------------------------------------------------------------------

resources = [
    ("Wood",         ph("token_wood"),    "Brown", SUPPLY_SHELF_X, LIBRARY_Y,  0),
    ("Metal",        ph("token_metal"),   "Grey",  SUPPLY_SHELF_X, LIBRARY_Y,  2.5),
    ("Cloth",        ph("token_cloth"),   "White", SUPPLY_SHELF_X, LIBRARY_Y,  5),
    ("Food",         ph("token_food"),    "Red",   SUPPLY_SHELF_X, LIBRARY_Y,  7.5),
    ("EnergyDrink",  ph("token_energy"),  "Yellow",SUPPLY_SHELF_X, LIBRARY_Y, 10),
    ("Battery",      ph("token_battery"), "Blue",  SUPPLY_SHELF_X, LIBRARY_Y, 12.5),
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
                   desc=f"Supply of {res_name.replace('EnergyDrink', 'Energy Drink')} tokens. Fully automated — Gather, salvage, dawn deliveries, and scripted costs/rewards pay tokens in and out for you. No need to touch it.",
                   tags=["ResourceBag", f"ResourceBag:{res_name}"],
                   locked=True)
    bag["ContainedObjects"] = [token]
    objects.append(bag)

# ---------------------------------------------------------------------------
# E.15  Dice
# ---------------------------------------------------------------------------

# 6 standard d6 in a combat tray (decorative — combat is script-rolled)
dice_tray = base_obj("Bag", tf(SUPPLY_SHELF_X, LIBRARY_Y, -2.5),
                     nickname="Combat Dice Tray",
                     desc="6 combat d6. Combat rolls are automated — these are here for house rules.",
                     tags=["DiceTray"],
                     locked=True)
dice_tray["ContainedObjects"] = []
for di in range(6):
    d6 = base_obj("Die_6", tf(),
                  nickname=f"Combat d6 #{di+1}",
                  tags=["CombatDie"])
    dice_tray["ContainedObjects"].append(d6)
objects.append(dice_tray)

# Sanity d8 (custom; locked in the library — Sanity rolls are automated)
sanity_d8 = base_obj("Custom_Dice", tf(SUPPLY_SHELF_X, LIBRARY_Y, -5),
                     nickname="Sanity d8",
                     desc="Roll for Sanity-loss events. Face value = damage dealt.",
                     tags=["SanityD8"],
                     locked=True)
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
# Matches CHARACTER_COLORS in lua/global.lua — a player's seat colour is
# determined by the character they pick, and the standee holder wears the
# same colour.
STANDEE_COLORS = {
    "James":  {"r": 0.12, "g": 0.53, "b": 1.00},   # Blue
    "Coco":   {"r": 1.00, "g": 1.00, "b": 1.00},   # White
    "Rayman": {"r": 0.19, "g": 0.70, "b": 0.17},   # Green
    "Ellie":  {"r": 0.91, "g": 0.88, "b": 0.17},   # Yellow
    "Luca":   {"r": 0.86, "g": 0.10, "b": 0.09},   # Red
}

CHAR_HOME_TILE = {"James": "JamesHouse", "Rayman": "RaymanHouse",
                  "Ellie": "EllieLucaHouse", "Luca": "EllieLucaHouse",
                  "Coco": "EllieLucaHouse"}

# One slot per character across a tile's lower half so standees sharing a
# tile (Ellie, Luca and Coco all start at Ellie & Luca's House) never spawn
# stacked on each other. Keep in sync with CHAR_SLOT_INDEX /
# getCharSlotPosition in lua/helpers.lua.
CHAR_SLOT_X = {"James": -1.8, "Coco": -0.9, "Rayman": 0.0, "Ellie": 0.9, "Luca": 1.8}
CHAR_SLOT_Z = -1.7

for char_name, color, bx, bz, stats in characters:
    # Standee
    _home = loc_positions[CHAR_HOME_TILE[char_name]]
    standee = base_obj("Figurine_Custom",
                       tf(_home["x"] + CHAR_SLOT_X[char_name],
                          1.5,
                          _home["z"] + CHAR_SLOT_Z),
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

    # Player board. Its art is pre-rotated 180° by generate_assets (same
    # render convention as the main board), so the printed stat bars sit in
    # the board's north-west quadrant; snaps and markers are placed to match.
    board_snaps_pb = []
    # Stat marker snaps (3 stats, beside the printed Health/Hunger/Sanity bars)
    for si, stat_name in enumerate(["Health", "Hunger", "Sanity"]):
        board_snaps_pb.append({
            "Position": {"x": -0.69, "y": 0.2, "z": 0.555 - si * 0.235},
            "Rotation": {"x": 0, "y": 0, "z": 0},
            "Tags": [f"Snap:Stat:{stat_name}"]
        })
    # Action cube snaps (3, on the printed cube row)
    for ai in range(3):
        board_snaps_pb.append({
            "Position": {"x": -0.27 + ai * 0.06, "y": 0.2, "z": -0.09},
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

    # Stat markers (3 per character), on the printed bars (see snap comment)
    for si, (stat_name, stat_val) in enumerate(stats.items()):
        marker = base_obj("Custom_Token",
                         tf(bx - 2.06, 1.4, bz + 1.11 - si * 0.47, sx=0.3, sy=0.3, sz=0.3),
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

boss_pool = base_obj("Bag", tf(SUPPLY_SHELF_X, LIBRARY_Y, 17.5),
                     nickname="Boss Pool",
                     desc="Boss standees. Placed on the map by Dawn card effects — fully automated, no need to touch it.",
                     tags=["BossPool"],
                     locked=True)
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

heart_bag = base_obj("Bag", tf(SUPPLY_SHELF_X, LIBRARY_Y, 15),
                     nickname="Telltale Heart Supply",
                     desc="5 Telltale Hearts. Cook to create; spend to revive a Down character.",
                     tags=["TelltaleHeartSupply"],
                     locked=True)
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

# In the library: the same ladder is printed on the board's NE corner.
legend = base_obj("Card", tf(LIBRARY_X, LIBRARY_Y, -13, rz=0, ry=180, sx=1.5, sy=1, sz=1.5),
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

# The notecard body is content/notebook/quickstart.md — the same single
# source the Notebook tab and Help panel render (see generate_notebook.py).
with open(os.path.join(CONTENT, "notebook", "quickstart.md"), "r", encoding="utf-8") as _f:
    quickstart_text = md_to_text(_f.read())

# On the board's clear SE patch — it used to sit at the board's very edge,
# where it slid under the board and turned invisible. ry=180 so its text
# reads from the players' side (the card convention).
notecard = base_obj("Notecard", tf(10.5, 1.3, -9.2, ry=180),
                    nickname="Quick Start",
                    desc=quickstart_text,
                    tags=["QuickStart"])
objects.append(notecard)

# Discard Tray — the visible counterpart of the hidden supply: every
# honor-system payment (craft costs, cook ingredients) is made by dropping
# tokens here; a background sweep (startDiscardTraySweep, helpers.lua)
# returns them to the right supply bag.
tray = base_obj("BlockSquare",
                tf(9.5, 0.95, -15, sx=2.6, sy=0.18, sz=2.6),
                nickname="Discard Tray",
                desc="Spending resources? Drop the tokens here — they return to the supply by themselves.",
                tags=["DiscardTray"],
                locked=True)
tray["ColorDiffuse"] = {"r": 0.32, "g": 0.16, "b": 0.12}
objects.append(tray)

# Catch shelf under the west library column: unlocked objects (decks shed
# their container at one card left) rest here instead of falling forever.
shelf = base_obj("BlockSquare",
                 tf(-26.5, -3.6, -3, sx=9, sy=0.4, sz=30),
                 nickname="",
                 desc="",
                 tags=["LibraryShelf"],
                 locked=True,
                 extra={"Tooltip": False})
shelf["ColorDiffuse"] = {"r": 0.1, "g": 0.1, "b": 0.1}
objects.append(shelf)

# ---------------------------------------------------------------------------
# Player Rules tablet — an in-TTS browser showing PlayerRules.html (generated
# by scripts/generate_player_rules.py from the same markdown as the Notebook).
# Needs scripts/serve_art.bat running locally, or the hosted URL in --publish
# builds. The same page opens in any desktop browser.
# ---------------------------------------------------------------------------

tablet = base_obj("Tablet", tf(17, 1.2, -13.5, ry=180),
                  nickname="Player Rules",
                  desc="The full player rulebook, right here on the table.\n\n"
                       "Zoom in (hover + Z) to read; scroll with the tablet's own controls.\n\n"
                       "Prefer your own screen? Open PlayerRules.html from the repo in any "
                       "browser, or visit " + served("PlayerRules.html") + " while the "
                       "asset server is running.",
                  tags=["PlayerRules"],
                  locked=True)
tablet["PageURL"] = served("PlayerRules.html")
objects.append(tablet)

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
    # Flat table: the hexagon table's raised wooden rim served no purpose
    # and read as a game component ("what is that barrier for?").
    "Table": "Table_Glass",
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

# The Lua + XML load order lives in scripts/load_order.json (a small, diffable,
# machine-readable manifest) so an agent can read the build order without
# scanning this script. Order matters — a file that defines something used at
# load time must precede its consumers. See scripts/CLAUDE.md.
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "load_order.json"),
          "r", encoding="utf-8") as _f:
    _MANIFEST = json.load(_f)

LUA_LOAD_ORDER = _MANIFEST["lua"]

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

XML_LOAD_ORDER = _MANIFEST["xml"]  # from scripts/load_order.json (see above)

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

# Custom UI assets: images the global XML references by name (the setup
# walkthrough's Step 2 character portrait cards).
save["CustomUIAssets"] = [
    {"Type": 0, "Name": f"char_front_{n}", "URL": art(f"char_{n.lower()}_front")}
    for n in ["James", "Coco", "Rayman", "Ellie", "Luca"]
]

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

if ARGS.publish:
    # Publish build: swap every dev-server URL in the Lua bundle (assets.lua
    # art paths, audio_manifest.lua sound URLs) for the hosted base, then
    # write a SEPARATE save so the dev files stay byte-stable.
    base = ARGS.publish.rstrip("/")
    save["LuaScript"] = save["LuaScript"].replace("http://localhost:8080", base)
    leftovers = [u for u in ("file:///", "localhost") if u in json.dumps(save)]
    out_path = ARGS.out or os.path.join(SAVES, "StarveNoMore.publish.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(save, f, separators=(",", ":"))
    print(f"PUBLISH save written: {out_path} (assets under {base})")
    if leftovers:
        raise SystemExit(f"publish build still contains local URLs: {leftovers}")
else:
    with open(os.path.join(SAVES, "StarveNoMore.json"), "w", encoding="utf-8") as f:
        json.dump(save, f, separators=(",", ":"))

    with open(os.path.join(SAVES, "StarveNoMore.pretty.json"), "w", encoding="utf-8") as f:
        json.dump(save, f, indent=2, ensure_ascii=False)

# Stats
total_objects = len(objects)
contained = sum(len(o.get("ContainedObjects", [])) for o in objects)
print(f"Save built: {total_objects} top-level objects, {contained} contained objects")
print("Files written: saves/StarveNoMore.json, saves/StarveNoMore.pretty.json")
