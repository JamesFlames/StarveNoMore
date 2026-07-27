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
import math
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
    # Location tiles - the _tile variants are content-centred squares
    # (scripts/normalize_tile_art.py) so the CIRCULAR tile crops centred
    # inside the printed ring instead of showing an off-centre slice.
    "tile_james":          "tiles/jameshome_tile.png",
    "tile_rayman":         "tiles/raymanhome_tile.png",
    "tile_ellie_luca":     "tiles/ellielucahome_tile.png",
    "tile_basketball":     "tiles/basketballcourt_tile.png",
    "tile_badminton":      "tiles/badmintoncourt_tile.png",
    # Empty card-shaped frame marking each of the 5 Market slots
    "market_slot":         "board/market_slot.png",
    # Path variants
    "path_compact":        "board/path_compact.png",
    "path_sprawl":         "board/path_sprawl.png",
    "path_linear":         "board/path_linear.png",
    "path_ring":           "board/path_ring.png",
    "path_star":           "board/path_star.png",
    # Deck atlases
    "phase1_face":         "decks/phase1_face.jpg",
    "phase1_back":         "decks/phase1_back.png",
    "phase2_face":         "decks/phase2_face.jpg",
    "phase2_back":         "decks/phase2_back.png",
    "phase3_face":         "decks/phase3_face.jpg",
    "phase3_back":         "decks/phase3_back.png",
    "phase4_face":         "decks/phase4_face.jpg",
    "phase4_back":         "decks/phase4_back.png",
    "market_face":         "decks/market_face.jpg",
    "market_back":         "decks/market_back.png",
    "recipe_face":         "decks/recipe_face.jpg",
    "recipe_back":         "decks/recipe_back.png",
    "threat_face":         "decks/threat_face.jpg",
    "threat_back":         "decks/threat_back.png",
    "visitor_face":        "decks/visitor_face.jpg",
    "visitor_back":        "decks/visitor_back.png",
    "trophy_face":         "decks/trophy_face.jpg",
    "trophy_back":         "decks/trophy_back.png",
    "starting_face":       "decks/starting_face.jpg",
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
    # Character standees — the _standee variants (scripts/normalize_standee_art.py)
    # are cut to transparent where the source is a figure on a plain backdrop
    # and sized to a common 512x1024. ColorDiffuse multiplies the standee's tint
    # over the WHOLE image, so an opaque backdrop turns the figurine into a
    # tinted rectangle; the same reason ASSET_MAP points at tiles/*_tile.png.
    "char_james_front":    "characters/james_front_standee.png",
    "char_james_back":     "characters/james_back_standee.png",
    "char_coco_front":     "characters/coco_front_standee.png",
    "char_coco_back":      "characters/coco_back_standee.png",
    "char_rayman_front":   "characters/rayman_front_standee.png",
    "char_rayman_back":    "characters/rayman_back_standee.png",
    "char_ellie_front":    "characters/ellie_front_standee.png",
    "char_ellie_back":     "characters/ellie_back_standee.png",
    "char_luca_front":     "characters/luca_front_standee.png",
    "char_luca_back":      "characters/luca_back_standee.png",
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

# The glass table's playing surface sits at world y ≈ 1.55 (measured from
# object resting heights in live saves), and the main board's top surface is
# roughly flush with it. Anything authored below this line starts EMBEDDED
# in the tabletop: locked objects stay invisible inside the glass, unlocked
# flat ones fall through the table's partial-hull collider ("player boards
# were invisible until I picked them up"). Every surface-level spawn height
# below is authored relative to this.
TABLE_SURFACE_Y = 1.55
SURFACE_Y = TABLE_SURFACE_Y + 0.05  # flat pieces ON THE TABLE. Locked objects
                                    # never settle, so the old +0.1 left them
                                    # visibly hovering at a low camera angle.

# The board is a thin Custom_Tile resting ON the table, so its surface height
# is DERIVED from its own thickness rather than guessed. Anything standing on
# the board must clear BOARD_SURFACE_Y or the board swallows it — the location
# tiles and the Doom marker both vanished that way when this was assumed
# instead of computed.
# A Custom_Tile's Thickness is scaled by scaleY, NOT by the XZ transform
# scale. This cost a bug: BOARD_WORLD_THICKNESS used to multiply by
# BOARD_TRANSFORM_SCALE (12.12), overstating the board's thickness by 12x, so
# BOARD_SURFACE_Y sat 0.13 above the board's real top face and every piece
# authored against it hung in the air.
#
# The observation that settled it: "almost everything is levitating above the
# board, apart from the quickstart note". The Quick Start is on the FELT, via
# SURFACE_Y, which never had the bogus factor; everything on the BOARD went
# through BOARD_SURFACE_Y, which did. One factor, exactly that split.
BOARD_TILE_THICKNESS = 0.012          # tile-local
BOARD_WORLD_THICKNESS = BOARD_TILE_THICKNESS * 1.0   # scaleY of the board is 1
BOARD_Y = TABLE_SURFACE_Y + BOARD_WORLD_THICKNESS / 2     # rests on the table
BOARD_SURFACE_Y = TABLE_SURFACE_Y + BOARD_WORLD_THICKNESS  # its top face
# Rounded: DOOM_MARKER_Y in lua/setup.lua mirrors this exactly and a test
# compares them, so it must be a value you can write down.
# Flat pieces resting ON the board. The clearance is an anti-z-fight hair,
# not a cushion: at the old +0.06 the location tiles visibly hovered over the
# board from a low camera ("I would rather they sit on top of the board rather
# than very slightly levitating over it"). Keep the pieces themselves thin
# (BOARD_PIECE_THICKNESS) so the gap can't come back as bulk instead.
BOARD_PIECE_Y = round(BOARD_SURFACE_Y + 0.01, 3)   # flat pieces on the board

# Thickness for a flat tile lying on the board. 0.1 rendered the location
# tiles as chunky pucks with a visible white rim; they are printed artwork,
# so they should read as ink on the board, not as counters standing on it.
BOARD_PIECE_THICKNESS = 0.02

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

def hide_from_pointer(obj):
    """Stop an out-of-play object answering the mouse. Everything parked below
    the table is still a physical object: hovering the board raised its tooltip
    and drew a ghost outline of a card that is not in play."""
    obj["Tooltip"] = False
    obj["DragSelectable"] = False
    obj["GridProjection"] = False
    return obj


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
# Seats sit square to the board's edges, not on a pentagon: one south, two
# west, two east. The north edge is left clear because the table runs out of
# felt there. Each player's board (below) uses the same side and angle, so
# hand and board are together in front of them.
HAND_ZONE_OUT   = 22    # distance from the table centre to a zone's centre
HAND_ZONE_LEN   = 14    # along the table edge
HAND_ZONE_DEPTH = 6     # toward the table centre
# The edge of the zone that faces the map. Nothing that is meant to stay ON
# the table may cross it: a card dropped past this line joins that seat's
# private hand instead of lying face up where the other players can read it.
HAND_ZONE_INNER = HAND_ZONE_OUT - HAND_ZONE_DEPTH / 2

hand_colors = [
    ("White",   0, -HAND_ZONE_OUT,   0),   # south
    ("Red",   -HAND_ZONE_OUT,  -7,  90),   # west
    ("Yellow",-HAND_ZONE_OUT,   7,  90),   # west
    ("Green",  HAND_ZONE_OUT,   7, 270),   # east
    ("Blue",   HAND_ZONE_OUT,  -7, 270),   # east
]
for color, x, z, ry in hand_colors:
    objects.append({
        "Name": "HandTrigger",
        "Transform": tf(x, 4.5, z, ry=ry,
                        sx=HAND_ZONE_LEN, sy=6, sz=HAND_ZONE_DEPTH),
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
# AttachedSnapPoints are stored in BOARD-LOCAL space and TTS multiplies them
# by the board's Transform scale, so Lua's board.positionToWorld(snap.position)
# returns the world value again. Author in world units and convert with
# board_geometry.world_to_local — the old world-authored values made
# moveDoomMarker fling the marker to (120, 72), far off the table.
BOARD_TRANSFORM_SCALE = board_geometry.BOARD_TRANSFORM_SCALE

def board_snap(wx, wz, tags):
    return {
        "Position": {"x": board_geometry.world_to_local(wx), "y": 0.02,
                     "z": board_geometry.world_to_local(wz)},
        "Rotation": {"x": 0, "y": 0, "z": 0},
        "Tags": tags,
    }

board_snaps = []

# Location tile snap points (5 locations in the graph layout)
# From path_layouts: the same table the board art draws its rings from, so a
# tile and its printed ring can never drift apart.
import path_layouts
loc_positions = {
    k: {"x": v[0], "y": 0.1, "z": v[1]}
    for k, v in path_layouts.LOCATION_WORLD.items()
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

# Market display (5 slots) — a column down the board's WEST flank, entirely
# off the printed map.
#
# Every number here is derived, because guessing them is what put the column
# on the board in the first place. A dealt TTS card is ~2.3 x 3.2 world units;
# the old column sat at x=-12.5, so each card reached x=-11.35 and lay across
# the map ("the market slots are covering the board up"). The frame markers
# (E.9) are a shade bigger than a card, and the column is pushed west until
# the frame's east edge clears BOARD_WORLD_HALF.
MARKET_CARD_W, MARKET_CARD_L = 2.3, 3.2   # a dealt TTS card, world units
MARKET_SLOT_W = MARKET_CARD_W + 0.2       # frame peeks out around the card
MARKET_SLOT_L = MARKET_CARD_L + 0.5
MARKET_COLUMN_X = -(board_geometry.BOARD_WORLD_HALF + MARKET_SLOT_W / 2 + 0.2)
# Separation: the frames must clear each other AND leave room for the slot's
# 3DText title between them (_slotOccupied in setup.lua also matches a card to
# a slot within 2 units, so keep centres well over 4 apart).
MARKET_SLOT_DZ = MARKET_SLOT_L + 0.7
MARKET_SLOT_POSITIONS = [(MARKET_COLUMN_X, 2 * MARKET_SLOT_DZ - i * MARKET_SLOT_DZ)
                         for i in range(5)]
# Title sits just north of its frame, clear of the card laid on top.
MARKET_LABEL_DZ = MARKET_SLOT_L / 2 + 0.35
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
# A Custom_TILE, not a Custom_Board: the board object always frames the image
# in a brown border that cannot be turned off, so its bounds (and therefore
# every snap point and object position derived from them) describe the FRAME
# while the art only covers the inner area. The printed rings and the DAY
# COUNTER frame could never line up with the pieces as a result. A tile has no
# border and the image fills it exactly.
#
# posY is chosen so the board's TOP lands at the same 1.79 the pieces are
# already authored against: 1.79 - (thickness * scale)/2.
#
# rotY stays 0. The board is on the PNG-pre-rotated side of the two rotation
# conventions (docs/tts-runtime.md "Rotations"): generate_main_board already
# rotates the finished image 180 degrees, so adding ry=180 here applies the
# compensation TWICE. That turns the printed art 180 degrees about the board
# centre — the DAY COUNTER frame moves to the south-east while the gadget
# stays at (-8, 8), and every location ring swaps sides with its tile. Worse,
# AttachedSnapPoints are board-LOCAL, so the object rotation negates them too:
# Snap:Doom:0 lands at (+10.9, +11.5) and moveDoomMarker walks the marker up
# the wrong edge. Rotate the IMAGE, never the board.
main_board = base_obj("Custom_Tile",
                      tf(0, BOARD_Y, 0,
                         sx=BOARD_TRANSFORM_SCALE, sy=1, sz=BOARD_TRANSFORM_SCALE),
                       nickname="Starve No More — Main Board",
                       desc="The suburban map. Doom threshold ribbons are printed on the board.",
                       tags=["Board", "MainBoard"],
                       locked=True,
                       extra={"Tooltip": False})
main_board["CustomImage"] = {
    "ImageURL": ph("main_board"),
    "ImageSecondaryURL": "",
    "WidthScale": 0,
    "CustomTile": {
        "Type": 0,               # square
        "Thickness": BOARD_TILE_THICKNESS,
        "Stackable": False,
        "Stretch": True,
    },
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
                    tf(pos["x"], BOARD_PIECE_Y, pos["z"], ry=180, sx=2.5, sy=1, sz=2.5),
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
            "Thickness": BOARD_PIECE_THICKNESS,
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
# Everything hidden must sit INSIDE the board footprint (+/-12 world units,
# board_geometry.BOARD_WORLD_HALF): the opaque board and table then cover it
# from every seat. Parked further out (the old +/-25..28) it sat beyond the
# table edge in plain sight — which is what the glass table exposed.
LIBRARY_Y = -2.5             # resting height for hidden components
SUPPLY_SHELF_X = 9.0         # resource bags / dice / hearts / boss pool
SUPPLY_SHELF_X2 = 5.5        # decorative path-variant trays, one row inward
LIBRARY_X = -9.0             # decks / trophies / legend (west column)
LIBRARY_X2 = -5.5            # trophy cards + starting decks
BENCH_X = -2.0               # unused character standees (see lua/helpers.lua)

for variant in ["Compact", "Sprawl", "Linear", "Ring", "Star"]:
    bag = base_obj("Bag",
                   tf(SUPPLY_SHELF_X2, LIBRARY_Y, -8 + ["Compact","Sprawl","Linear","Ring","Star"].index(variant) * 4),
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
# (setup.lua) moves it — players can't drag it. y=1.68 mirrors
# DOOM_MARKER_Y in moveDoomMarker (above the ~1.55 table surface; the old
# 1.2 left the marker buried inside the glass tabletop).
_doom_x, _doom_z = board_geometry.doom_step_world(0)
# Scale 0.3375 (three quarters of 0.45): a Doom step cell is only ~0.73
# world units wide, so the original
# 1.6 (sized when the board was rendering nine times too big) covered four
# cells at once — "the doom marker is ridiculously large".
doom = base_obj("Custom_Token", tf(_doom_x, BOARD_PIECE_Y, _doom_z, sx=0.3375, sy=0.3375, sz=0.3375),
                nickname="Doom Marker",
                desc="Doom track marker. Moves itself each time Doom changes — you never place it by hand.",
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
# (unlike flat tiles/cards, whose art needs the 180 treatment). y=1.8
# keeps the whole gadget above the ~1.55 playing surface, inside the
# printed DAY COUNTER frame — spawned lower, it clipped into the surface
# and was half-invisible. The script alone advances it: onLoad /
# lockdownCriticalObjects set interactable=false so players can't click
# the counter's +/- buttons.
_dc_x, _dc_z = board_geometry.DAY_COUNTER_WORLD
day_counter = base_obj("Counter", tf(_dc_x, BOARD_SURFACE_Y + 0.03, _dc_z),
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
#
# These were full-size TTS Notecards printing the whole "use the Craft action
# to buy it" paragraph. A notecard is much wider than a card, so the column
# lay across the printed map and hid it. Now each slot is an empty card-shaped
# frame (art/board/market_slot.png) barely bigger than the card that lands on
# it, the paragraph rides on the CARD's own tooltip (addMarketHelp,
# lua/crafting.lua), and the slot number is a flat 3DText just north of the
# frame so it stays readable once a card covers the frame.
#
# Locked: physics can never wedge them under the board, and the Lua contract
# stays "card lands at the slot's own position" (_slotOccupied in setup.lua,
# _spawnCraftButtons in ui_actionbar_targets.lua both key off that).
# ry=180 + un-rotated art: the flat-art convention the location tiles use
# (docs/tts-runtime.md "Rotations"). The frame is 2-fold symmetric anyway.
MARKET_SLOT_MESH = board_geometry.BOARD_MESH_HALF * 2   # world units per scale
for i, (msx, msz) in enumerate(MARKET_SLOT_POSITIONS):
    slot = base_obj("Custom_Tile",
                    tf(msx, SURFACE_Y, msz, ry=180,
                       sx=MARKET_SLOT_W / MARKET_SLOT_MESH, sy=1,
                       sz=MARKET_SLOT_L / MARKET_SLOT_MESH),
                    nickname=f"Market Slot {i+1}",
                    desc="Shared Market slot. Hover the card on it for what it does "
                         "and how to buy it.",
                    tags=["MarketSlot", f"MarketSlot:{i}"],
                    locked=True)
    slot["CustomImage"] = {
        "ImageURL": ph("market_slot"),
        "ImageSecondaryURL": "",
        "WidthScale": 0,
        # 0.1 thick: SURFACE_Y is TABLE_SURFACE_Y + half of exactly that, so
        # the frame's bottom face lands flat on the felt instead of hovering.
        "CustomTile": {"Type": 0, "Thickness": 0.1,
                       "Stackable": False, "Stretch": True},
    }
    objects.append(slot)

# Table labels for the two unowned face-up card rows — playtest: "who do
# these cards belong to?". Flat 3DText (rx=90, ry=0: the gadget-text
# convention, same as the Day Counter digits).
def table_label(x, z, text, guid_tag, font_size=64, color=(0.85, 0.78, 0.55)):
    lbl = base_obj("3DText", tf(x, TABLE_SURFACE_Y + 0.05, z, rx=90, ry=0),
                   nickname="", desc="",
                   tags=[guid_tag], locked=True,
                   extra={"Tooltip": False})
    lbl["Text"] = {
        "Text": text,
        "colorstate": {"r": color[0], "g": color[1], "b": color[2]},
        "fontSize": font_size,
    }
    return lbl

# 3DText renders CENTRED on its position and is far wider than the column it
# titles, so anything but a very short string spills east over the board —
# where the board, being taller, simply covers it ("the title with description
# MARKET - shared etc is covered up by the board"). Park the header NORTH of
# the board's edge instead, where it has the whole width of the felt.
objects.append(table_label(
    MARKET_COLUMN_X, board_geometry.BOARD_WORLD_HALF + 2.0,
    "MARKET — shared shop.\nBuy with the Craft action.",
    "Label:Market", 40))

# One title per slot, north of its frame. Deliberately terse: it only has to
# identify which slot the Craft action means, and it has to fit inside a
# 2.5-unit column without reaching the board — "Market Slot 1" did not.
for i, (msx, msz) in enumerate(MARKET_SLOT_POSITIONS):
    objects.append(table_label(msx, msz + MARKET_LABEL_DZ,
                               f"SLOT {i+1}", f"Label:MarketSlot:{i}", 28))
# (No RECIPES label: the printed reference row it pointed at now lives in
# the hidden library - recipes are read from the Notebook tab, the Help
# panel, and the Cook action's own list.)

# ---------------------------------------------------------------------------
# E.10  Recipe cards (face-up reference)
# ---------------------------------------------------------------------------

_rw, _rh = atlas_grid("cards_recipes.csv", recipes)
for i, row in enumerate(recipes):
    # In the hidden library, not on the table: 20 face-up cards filled the
    # whole south bank of the board from turn one ("all the recipe cards are
    # just sitting there"). Cook picks ingredients automatically and every
    # recipe is in the Notebook tab, the Help panel and the Cook list.
    card = base_obj("Card", tf(LIBRARY_X2 - 2.0, LIBRARY_Y, 9 - (i % 10) * 2.0, rz=0, ry=180),
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
    # rz omitted (0) = FACE UP. Dealt from a face-DOWN deck, a player saw a
    # row of "STARTING" card backs fanned in their own hand instead of the
    # items they were given.
    start_deck = base_obj("DeckCustom",
                          tf(LIBRARY_X2, LIBRARY_Y, -1 - si * 2.2, ry=180),
                          nickname=f"{start_char}'s Starting Hand",
                          desc=f"{start_char}'s personal items. Dealt to {start_char}'s player automatically during Setup.",
                          tags=["StartingHandDeck", f"StartingHand:{start_char}"])
    start_deck["DeckIDs"] = deck_ids
    start_deck["CustomDeck"] = dict(starting_custom_deck)
    start_deck["ContainedObjects"] = contained
    start_deck["HideWhenFaceDown"] = False
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
    ("Battery",      ph("token_battery"), "Blue",  SUPPLY_SHELF_X, LIBRARY_Y, 11.0),
]

for res_name, token_url, color, x, y, z in resources:
    # Create the token template
    # Scale 0.4: at scale 1 a token is roughly a fifth of a location tile —
    # "the energy drink token is too large" once the board was fixed.
    token = base_obj("Custom_Token", tf(sx=0.4, sy=0.4, sz=0.4),
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

# bx spacing is 9 units: the boards are scale-3 (~6 units wide), so the old
# 3-unit spacing overlapped them heavily — at load the physics engine flung
# the stack across the table (boards ended up 20+ units from home, which
# then broke the old board-relative resource counting). 9 units clears them.
# Unused boards are benched under the table at setup (benchUnusedBoards).
# Player boards line up SQUARE with the game board: parallel to its edges,
# tops facing in, evenly spaced. They used to sit on a pentagon at angles like
# 294.3 and 215.1, which read as scattered next to a square board -- and the
# two northern ones hung off the felt.
#
# BOARD_EDGE (12) + half the board's depth + a margin puts each one just
# outside the printed board. West clears the Market column (cards centred at
# x=-12.5, so ~-13.7 at their widest).
PLAYER_BOARD_SX = 2.6
PLAYER_BOARD_SZ = 1.8

# How wide the board actually renders, which is NOT mesh * scaleX.
#
# board_*.png is 1024x512 (2:1) while the transform is 2.6 x 1.8 (1.44:1), and
# a Custom_Tile with Stretch on renders at its IMAGE's aspect. James and Rayman
# sat 8.0 apart with a nominal 5.15-wide board — a 2.85-unit gap on paper — and
# still overlapped on the table (playtest screenshot, 2026-07-27). Take the
# widest reading the ambiguity allows and space the flanks from that: every
# other reading is narrower, so this cannot overlap either way.
#
# auditObjectFootprints (lua/audit.lua) now measures the real thing in a live
# game and prints "PlayerBoard size WxD" plus the true edge-to-edge gap into
# the Message Log; tighten this once that number is in hand.
_pb_art_aspect = 2.0           # art/characters/board_*.png, 1024x512
PLAYER_BOARD_W = (PLAYER_BOARD_SX * board_geometry.BOARD_MESH_HALF * 2
                  * _pb_art_aspect)
# Half the board's depth (the dimension that faces the map on the east/west
# seats, where the board is turned 90 degrees).
_pb_half_depth = PLAYER_BOARD_SZ * board_geometry.BOARD_MESH_HALF

# West/east column, pushed as far out as the hand zones allow. The west flank
# has to hold the map (+/-12), then the Market column, then the player board,
# and it only just does: at the old 16.0 the board's inner edge sat at -14.22
# while the market frames reach -14.70, so the two overlapped once the Market
# moved off the map. Shuffling the Market along z instead is not an option —
# five 3.7-long slots need 18.5 units and the player boards chop the 29-unit
# flank into 7.9 / 2.9 / 7.9 bands. Pushing the boards out any FURTHER is not
# an option either: past HAND_ZONE_INNER they stick into the seat's private
# hand. East matches west so the table stays symmetrical.
_side_x = round(HAND_ZONE_INNER - _pb_half_depth, 1)
_market_west = -MARKET_COLUMN_X + MARKET_SLOT_W / 2
assert _side_x - _pb_half_depth > _market_west, (
    f"player boards at {_side_x} overlap the Market column (which reaches "
    f"{_market_west:.2f}) — the west flank is out of room")
_south_z = -(board_geometry.BOARD_WORLD_HALF + PLAYER_BOARD_SZ + 0.5)

# The flank boards are turned 90 degrees, so it is their WIDTH that runs
# along z: each needs half a board from the centre line, plus a margin. The
# old +/-4.0 was set from the nominal 5.15 width and left them overlapping.
_flank_z = round(PLAYER_BOARD_W / 2 + 0.65, 1)
assert 2 * _flank_z > PLAYER_BOARD_W, "the two boards on a flank still overlap"

# (name, colour, x, z, ry, stats) - ry turns the printed top toward the board:
# 0 = faces north, 90 = faces east, 270 = faces west.
characters = [
    ("James",  "White",  _side_x, -_flank_z, 270, {"health": 8, "hunger": 6, "sanity": 10}),  # Blue, east
    ("Rayman", "Yellow", _side_x,  _flank_z, 270, {"health": 12,"hunger": 10,"sanity": 6}),   # Green, east
    ("Coco",   "Red",        0.0, _south_z,    0, {"health": 6, "hunger": 8, "sanity": 12}),  # White, south
    ("Luca",   "Blue",  -_side_x, -_flank_z,  90, {"health": 7, "hunger": 8, "sanity": 10}),  # Red, west
    ("Ellie",  "Green", -_side_x,  _flank_z,  90, {"health": 8, "hunger": 10,"sanity": 8}),   # Yellow, west
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

for char_name, color, bx, bz, bry, stats in characters:
    # Standee
    _home = loc_positions[CHAR_HOME_TILE[char_name]]
    standee = base_obj("Figurine_Custom",
                       tf(_home["x"] + CHAR_SLOT_X[char_name],
                          SURFACE_Y + 0.35,
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

    # SURFACE_Y, not SURFACE_Y+0.1: SURFACE_Y is already TABLE_SURFACE_Y plus
    # half a 0.1-thick tile, i.e. the height at which a tile's BOTTOM FACE
    # rests exactly on the felt. The extra +0.1 was left over from when the
    # boards spawned at an absolute 1.1, inside the glass tabletop, and fell
    # through its partial-hull collider; at the current SURFACE_Y it just
    # parked the board 0.1 in the air, and because the board is locked it
    # never settles — it hung there visibly from a seated camera angle
    # ("the player card describing James is levitating off the table").
    # Locked: the board is a fixed reference dock (stats live in the UI;
    # resource tokens are laid beside it). Locking stops players dragging it
    # into a pile and stops physics shoving the row apart at load.
    pboard = base_obj("Custom_Tile",
                      tf(bx, SURFACE_Y, bz, ry=bry,
                         sx=PLAYER_BOARD_SX, sy=1, sz=PLAYER_BOARD_SZ),
                      nickname=f"{char_name}'s Player Board",
                      desc=f"{char_name}'s reference board. Stats are tracked automatically "
                           f"(left panel + Party roster); resource tokens are delivered beside this board.",
                      tags=["PlayerBoard", f"PlayerBoard:{char_name}"],
                      locked=True)
    pboard["CustomImage"] = {
        "ImageURL": ph(f"board_{char_name.lower()}"),
        "ImageSecondaryURL": "",
        "WidthScale": 0,
        "CustomTile": {"Type": 0, "Thickness": 0.1, "Stackable": False, "Stretch": True}
    }
    pboard["AttachedSnapPoints"] = board_snaps_pb
    objects.append(pboard)

    # (No stat markers or action cubes: every stat and action is tracked by
    # the automated UI — the three tokens per board only made players ask
    # what they were supposed to do with them.)

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

boss_pool = base_obj("Bag", tf(SUPPLY_SHELF_X, LIBRARY_Y, -10.5),
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
#
# Placed against the tile's WEST edge, inside the printed ring: at the old
# (-3.5, -3.5) it sat 4.95 units out — beyond the 3.8-unit ring, reading as
# part of no location at all. 3.0 units puts it just off the 5x5 tile art
# and clearly inside Ellie & Luca's circle. West rather than south because
# the location's name/yields text is printed in the southern annulus, and
# north-west of the standee row (z = -1.7).
# LOCKED: it is scenery belonging to a location, not a component anybody is
# meant to pick up. Unlocked it drifted off its tile and fell through the
# tabletop's partial-hull collider — a live autosave had it at (-3.18, 1.21),
# i.e. inside the table, where Pry's "is there a Sealed Basement at your
# tile?" check could still find it but no player could see it.
#
# Its resting height is derived, not padded: a BlockSquare's mesh is 1 unit
# tall, so at scaleY it stands BASEMENT_H high and its centre must sit half
# of that above the board's top face to rest ON the board.
_elh = loc_positions["EllieLucaHouse"]
BASEMENT_SCALE_Y = 0.5
BASEMENT_H = 1.0 * BASEMENT_SCALE_Y
basement = base_obj("BlockSquare",
                    tf(_elh["x"] - 3.0, round(BOARD_SURFACE_Y + BASEMENT_H / 2, 3), _elh["z"],
                       sx=1.4, sy=BASEMENT_SCALE_Y, sz=1.4),
                    nickname="The Sealed Basement",
                    desc="A padlocked hatch under Ellie & Luca's House. Someone stocked it before the week began.\n\nPry (free action + Crowbar / Lockpick / Pry Bar): a free Market Item, plus 2 Food + 1 Wood + 1 Battery.",
                    tags=["SealedBasement"],
                    locked=True)
basement["ColorDiffuse"] = {"r": 0.28, "g": 0.22, "b": 0.15}
objects.append(basement)

heart_bag = base_obj("Bag", tf(SUPPLY_SHELF_X, LIBRARY_Y, -8),
                     nickname="Telltale Heart Supply",
                     desc="5 Telltale Hearts. Cook to create; spend to revive a Down character.",
                     tags=["TelltaleHeartSupply"],
                     locked=True)
heart_bag["ContainedObjects"] = []
for hi in range(5):
    heart = base_obj("Custom_Token", tf(sx=0.4, sy=0.4, sz=0.4),
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
legend = base_obj("Card", tf(LIBRARY_X, LIBRARY_Y, -11, rz=0, ry=180, sx=1.5, sy=1, sz=1.5),
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

# A TTS Notecard renders one fixed-size page and CLIPS the overflow silently.
# This used to carry the whole of content/notebook/quickstart.md (~1900
# chars); the card cut off mid-word and the player never saw the day loop, the
# stats, or the light rule ("The Quick Start note is too small to fit all the
# text"). The long version lives where it can scroll: the Notebook tab and the
# ? panel, both rendered from that same markdown by generate_notebook.py.
#
# refreshQuickStartCard (lua/ui_help.lua) re-stamps this with the
# difficulty-aware wording at setup; this is what the card says before then,
# and it must fit the same budget (QUICKSTART_CARD_BUDGET).
quickstart_text = (
    "GOAL: survive 7 nights, keep Doom under 30, don't all go Down, "
    "and kill The Source.\n"
    "\nDAY: Dawn - Day (3 actions each) - Dusk - Night - Tick.\n"
    "STATS: Health / Hunger / Sanity. Any at 0 = Down.\n"
    "DARK: no light at night = Charlie attacks.\n"
    "TRADE: free, on your tile, any time.\n"
    "\nHover anything for its rule. '?' = full rules.\n"
    "'What now?' tells you your next move."
)

# On the board's clear SE patch — it used to sit at the board's very edge,
# where it slid under the board and turned invisible. ry=0: a Notecard's
# printed text follows the gadget convention (like the Day Counter), so
# the old ry=180 rendered it upside down in the default view.
# On the TABLE south of the board, not on it: sitting on the board it
# covered printed art and read as a game component.
notecard = base_obj("Notecard", tf(14.5, SURFACE_Y + 0.1, -14.0, ry=0),
                    nickname="Quick Start",
                    desc=quickstart_text,
                    tags=["QuickStart"])
objects.append(notecard)

# (No Discard Tray any more: resources are virtual — held counts live in
# gameState and every cost is auto-paid — so there is nothing to drop on a
# tray. The old tray only added table clutter and a payment step players
# didn't need.)

# Catch shelf under the west library column: unlocked objects (decks shed
# their container at one card left) rest here instead of falling forever.
shelf = base_obj("BlockSquare",
                 tf(-7.5, -3.6, 0, sx=8, sy=0.4, sz=23),
                 nickname="",
                 desc="",
                 tags=["LibraryShelf"],
                 locked=True,
                 extra={"Tooltip": False})
shelf["ColorDiffuse"] = {"r": 0.1, "g": 0.1, "b": 0.1}
objects.append(shelf)

# (No in-TTS Player Rules tablet: it defaulted to Google whenever the local
# asset server wasn't running — a broken first impression — and duplicated
# the rules already in the Notebook tab, the Help panel, and the Quick Start
# notecard. Players who want the browser page can open PlayerRules.html.)

# ---------------------------------------------------------------------------
# Assemble the full save
# ---------------------------------------------------------------------------

# Anything parked below the table is out of play: silence its tooltip so
# hovering the board doesn't raise ghost cards (guarded by
# test_regression_guards.py::test_hidden_objects_do_not_answer_the_pointer).
def _silence_hidden(objs):
    for o in objs:
        if o.get("Transform", {}).get("posY", 1) < 0:
            hide_from_pointer(o)
        for child in o.get("ContainedObjects", []) or []:
            hide_from_pointer(child)


_silence_hidden(objects)

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
    # Opaque, not glass: the glass top made the entire under-table library
    # (decks, supply bags, benched boards) visible from every seat once the
    # board shrank to its correct size. Valid TTS tables are Table_Circular /
    # Custom / Glass / Hexagon / None / Octagon / Plastic / Poker / RPG /
    # Square — RPG is the large opaque one. Everything hidden is parked
    # inside the board footprint below, so the board hides it too.
    "Table": "Table_RPG",
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
    # Baseline lighting shown before the first BeginDay (setup / PreGame),
    # where players pick characters and read the standees. Raised ~45% from
    # the original dim values (playtest: standees read too dark against the
    # night-suburb board). ui_mood.LIGHTING_PRESETS override this per phase
    # once play starts — those were lifted to match.
    "Lighting": {
        "LightIntensity": 0.80,
        "LightColor": {"r": 1.0, "g": 0.95, "b": 0.85},
        "AmbientIntensity": 1.3,
        "AmbientType": 1,
        "AmbientSkyColor": {"r": 0.5, "g": 0.54, "b": 0.66},
        "AmbientEquatorColor": {"r": 0.55, "g": 0.5, "b": 0.45},
        # Brighter ground bounce lifts the underside of the standees.
        "AmbientGroundColor": {"r": 0.38, "g": 0.33, "b": 0.30},
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
