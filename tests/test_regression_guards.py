"""Generic guards for the *classes* of bug that keep surfacing in playtests.

Each test here encodes a lesson from a real breakage so the whole family is
caught before the next one ships, not just the one instance that was fixed:

  - objects spawned overlapping (player boards spawned 3 units apart at
    scale 3 => physics flung the stack across the table);
  - text-gadget objects rotated 180 (the Quick Start notecard read upside
    down; the same convention trips cards vs. counters/notecards);
  - dark-on-dark / low-contrast button text (the recurring readability
    complaints);
  - object handles dereferenced in a takeObject callback without a pcall
    guard (the "cannot access field getNickname of userdata" crash, hit
    four separate times: pry, dawn reveal, threat reveal, gather);
  - a Transform scale set from a mesh-extent assumption instead of a
    measurement (the board painted its art across +/-110 world units while
    every piece was authored inside +/-12, heaping them in the middle);
  - "hidden" objects parked outside whatever is meant to cover them (the
    whole under-table library sat in plain sight beside a glass table).

See docs/tts-runtime.md for the underlying engine behaviours.
"""
import json
import os
import re

from conftest import LUA_DIR, ROOT, XML_DIR, all_lua_files, all_xml_files, read_text


def _load_save():
    path = os.path.join(ROOT, "saves", "StarveNoMore.json")
    assert os.path.isfile(path), "saves/StarveNoMore.json missing — run scripts/build_save.py"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _category(tags):
    """The functional group a laid-out object belongs to (PlayerBoard,
    Location, ...) — the namespaced tag, e.g. 'PlayerBoard:James' -> 'PlayerBoard'."""
    for t in tags:
        if ":" in t:
            return t.split(":", 1)[0]
    return None


# --------------------------------------------------------------------------
# 1. Objects laid out in a group must not overlap at spawn.
# --------------------------------------------------------------------------
# A Custom_Tile spans ~1.98 world units per unit of Transform scale (measured:
# the 2.5-scale location tiles come out 4.95 wide). Two more things decide
# whether neighbours actually clear each other, and missing them shipped
# overlapping player boards twice:
#
#   * ROTATION. A board turned 90 degrees puts its WIDTH along z. The flank
#     boards are at ry=270, so their 2.6 scaleX — not their 1.8 scaleZ — is
#     what has to fit in the gap between them.
#   * STRETCH. A stretched tile renders at its IMAGE's aspect ratio, so 2:1
#     art (board_*.png) on a 1.44:1 transform comes out wider than
#     mesh * scaleX. The exact rule is not measured — auditObjectFootprints
#     prints the real size and the real edge-to-edge gap from a live game —
#     so this takes the widest reading the ambiguity allows and then insists
#     on a real margin on top, rather than trusting arithmetic that a
#     playtest screenshot has already contradicted once.

_TILE_MESH = 1.98          # world units per unit of Transform scale (measured)
_MIN_CLEARANCE = 0.15      # of the larger footprint; 12% shipped overlapping


def _art_aspect(url):
    """width/height of the art behind an ImageURL, or None if not local."""
    import glob

    from PIL import Image  # test-only dependency
    name = os.path.basename(url.split("?")[0])
    hits = glob.glob(os.path.join(ROOT, "art", "**", name), recursive=True)
    if not hits:
        return None
    with Image.open(hits[0]) as im:
        return im.size[0] / im.size[1]


def _tile_footprint(o):
    """Widest plausible world (x, z) footprint of a Custom_Tile."""
    t = o["Transform"]
    w = t["scaleX"] * _TILE_MESH
    d = t["scaleZ"] * _TILE_MESH
    image = o.get("CustomImage", {})
    if image.get("CustomTile", {}).get("Stretch"):
        aspect = _art_aspect(image.get("ImageURL", ""))
        if aspect:
            w, d = max(w, d * aspect), max(d, w / aspect)
    if round(t.get("rotY", 0)) % 180 == 90:
        w, d = d, w
    return w, d


def test_grouped_tiles_do_not_overlap_at_spawn():
    save = _load_save()
    groups = {}
    for o in save["ObjectStates"]:
        if o.get("Name") != "Custom_Tile":
            continue
        cat = _category(o.get("Tags", []))
        if cat in ("PlayerBoard", "Location", "MarketSlot"):
            t = o["Transform"]
            w, d = _tile_footprint(o)
            groups.setdefault(cat, []).append(
                (o.get("Nickname") or o["Name"], t["posX"], t["posZ"], w, d))

    problems = []
    for cat, items in groups.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                na, xa, za, wa, da = items[i]
                nb, xb, zb, wb, db = items[j]
                gap = max(abs(xa - xb) - (wa + wb) / 2,
                          abs(za - zb) - (da + db) / 2)
                need = _MIN_CLEARANCE * max(wa, wb, da, db)
                if gap < need:
                    problems.append(
                        f"{cat}: '{na}' and '{nb}' clear each other by only "
                        f"{gap:.2f} world units (need {need:.2f}); footprints "
                        f"{wa:.1f}x{da:.1f} and {wb:.1f}x{db:.1f}")
    assert not problems, (
        "objects in a laid-out group are too close at spawn — they overlap on "
        "the table, and TTS physics shoves unlocked ones across it:\n  "
        + "\n  ".join(problems))


def test_player_board_width_constant_matches_the_art():
    """build_save sizes the flank spacing from the board art's aspect ratio.
    New art with a different shape has to move the boards with it."""
    import re as _re
    src = read_text(os.path.join(ROOT, "scripts", "build_save.py"))
    declared = float(_re.search(r"^_pb_art_aspect\s*=\s*([\d.]+)", src, _re.M).group(1))
    actual = _art_aspect("board_james.png")
    assert abs(declared - actual) < 0.01, (
        f"_pb_art_aspect is {declared} but art/characters/board_james.png is "
        f"{actual:.3f}:1 — the player boards are spaced from that number")


# --------------------------------------------------------------------------
# 2. Text-gadget objects must render upright (rotY ~ 0), not 180.
# --------------------------------------------------------------------------
# Notecards / Counters print engine text that reads right-side-up at rotY=0
# (unlike flat card/tile ART, which needs 180 or a pre-rotated image). The
# Quick Start notecard shipped at rotY=180 and read upside down for weeks.

def test_text_gadgets_are_upright():
    save = _load_save()
    bad = []
    for o in save["ObjectStates"]:
        if o.get("Name") in ("Notecard", "Counter"):
            ry = o["Transform"]["rotY"] % 360
            if not (ry < 1 or ry > 359):
                bad.append(f"{o.get('Nickname') or o['Name']} ({o['Name']}) has rotY={ry:.0f}")
    assert not bad, (
        "text-gadget objects rotated away from upright (they print engine text "
        "that reads right-side-up only at rotY=0):\n  " + "\n  ".join(bad))


# --------------------------------------------------------------------------
# 3. Button text must have enough contrast against its own background.
# --------------------------------------------------------------------------
_BUTTON_RE = re.compile(r"<Button\b[^>]*?>", re.S)
_MIN_CONTRAST = 3.0   # WCAG AA for large text; current lowest real button is 3.79


def _relative_luminance(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 8:
        h = h[:6]
    elif len(h) == 4:
        h = "".join(c * 2 for c in h[:3])
    elif len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _contrast(a, b):
    la, lb = _relative_luminance(a), _relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _alpha(hex_color):
    h = hex_color.lstrip("#")
    return int(h[6:8], 16) / 255 if len(h) == 8 else 1.0


def test_button_text_contrast():
    problems = []
    for filename in all_xml_files():
        src = read_text(os.path.join(XML_DIR, filename))
        for m in _BUTTON_RE.finditer(src):
            tag = m.group(0)
            text = re.search(r'\btext="([^"]*)"', tag)
            color = re.search(r'\bcolor="(#[0-9A-Fa-f]+)"', tag)
            tcolor = re.search(r'\btextColor="(#[0-9A-Fa-f]+)"', tag)
            idm = re.search(r'\bid="([^"]+)"', tag)
            # Skip invisible click-overlays (empty text or transparent paint).
            if not (text and text.group(1).strip() and color and tcolor):
                continue
            if _alpha(color.group(1)) < 0.25 or _alpha(tcolor.group(1)) < 0.25:
                continue
            c = _contrast(color.group(1), tcolor.group(1))
            if c < _MIN_CONTRAST:
                problems.append(
                    f"{filename}: button {idm.group(1) if idm else '?'} contrast "
                    f"{c:.2f} < {_MIN_CONTRAST} (bg {color.group(1)} / text {tcolor.group(1)})")
    assert not problems, (
        "buttons with text too low-contrast against their own background "
        "(dark-on-dark / light-on-light reads as disabled or unreadable):\n  "
        + "\n  ".join(problems))


# --------------------------------------------------------------------------
# 4. takeObject callbacks must guard the object handle with pcall/safecall.
# --------------------------------------------------------------------------
# A takeObject callback can fire with a DEAD handle (the object merged into a
# deck mid-flight); touching any field then throws "cannot access field X of
# userdata<LuaObject>". Every callback that dereferences its object param must
# wrap the access in pcall/safecall. This crash hit three times this session.

_CB_RE = re.compile(r"callback_function\s*=\s*function\s*\(\s*([A-Za-z_]\w*)\s*\)")
# Keywords that open an `end`/`until`-terminated block, and the closers.
_OPENERS = re.compile(r"\b(function|if|for|while|repeat)\b")
_CLOSERS = re.compile(r"\b(end|until)\b")


def _callback_body(src, start):
    """From the 'function(' at `start`, return the source of the callback body
    up to its matching close, by depth-counting block keywords."""
    depth = 0
    i = start
    seen_open = False
    while i < len(src):
        mo = _OPENERS.search(src, i)
        mc = _CLOSERS.search(src, i)
        if mo and (not mc or mo.start() < mc.start()):
            depth += 1
            seen_open = True
            i = mo.end()
        elif mc:
            depth -= 1
            i = mc.end()
            if seen_open and depth == 0:
                return src[start:i]
        else:
            break
    return src[start:i]


def test_takeobject_callbacks_guard_dead_handles():
    problems = []
    for rel in all_lua_files():
        src = read_text(os.path.join(LUA_DIR, rel))
        for m in _CB_RE.finditer(src):
            param = m.group(1)
            body = _callback_body(src, m.start())
            derefs = re.search(r"\b" + re.escape(param) + r"\s*\.\s*\w+", body)
            guarded = ("pcall" in body) or ("safecall" in body)
            if derefs and not guarded:
                line = src.count("\n", 0, m.start()) + 1
                problems.append(
                    f"{rel}:{line}: callback dereferences '{param}' without a "
                    "pcall/safecall guard (dead-handle crash risk)")
    assert not problems, (
        "takeObject callbacks touch their object handle unguarded — a handle "
        "that died mid-flight throws 'cannot access field ... of userdata':\n  "
        + "\n  ".join(problems)
        + "\n(wrap the body in pcall(function() ... end), like revealDawnCard)")


# --------------------------------------------------------------------------
# 5. Tag lookups must resolve against tags that exist in the built save.
# --------------------------------------------------------------------------
# Every object lookup goes through a tag (never a GUID), and a typo'd or
# renamed tag fails SILENTLY — findOneByTag just returns nil and the feature
# quietly does nothing. Checks both literal lookups, findOneByTag("DoomMarker"),
# and namespaced dynamic ones, findOneByTag("Location:" .. name).

_LITERAL_TAG_RE = re.compile(
    r'(?:findOneByTag|findAllByTag|getObjectsWithTag)\(\s*"([^"]+)"\s*\)')
_NAMESPACE_TAG_RE = re.compile(
    r'(?:findOneByTag|findAllByTag|getObjectsWithTag)\(\s*"([A-Za-z]+):"\s*\.\.')


def _save_tags():
    tags = set()

    def walk(objs):
        for o in objs:
            tags.update(o.get("Tags", []))
            for sp in o.get("AttachedSnapPoints", []) or []:
                tags.update(sp.get("Tags", []))
            if "ContainedObjects" in o:
                walk(o["ContainedObjects"])
    walk(_load_save()["ObjectStates"])
    return tags


def test_tag_lookups_resolve_in_the_save():
    tags = _save_tags()
    namespaces = {t.split(":", 1)[0] for t in tags if ":" in t}
    problems = []
    for rel in all_lua_files():
        src = read_text(os.path.join(LUA_DIR, rel))
        for i, line in enumerate(src.splitlines(), 1):
            if line.lstrip().startswith("--"):
                continue
            for tag in _LITERAL_TAG_RE.findall(line):
                if tag not in tags and tag.split(":", 1)[0] not in namespaces:
                    problems.append(f"{rel}:{i}: no object in the save carries tag {tag!r}")
            for ns in _NAMESPACE_TAG_RE.findall(line):
                if ns not in namespaces:
                    problems.append(f"{rel}:{i}: no save tag uses the namespace {ns + ':'!r}")
    assert not problems, (
        "Lua looks up tags that nothing in the built save carries — the lookup "
        "returns nil and the feature silently does nothing:\n  "
        + "\n  ".join(problems))


# --------------------------------------------------------------------------
# 6. Player-facing text must not name components that were removed.
# --------------------------------------------------------------------------
# When a physical component is deleted from the save, instructions that still
# tell players to use it become impossible to follow. A Dawn card kept saying
# "drop 2 Battery on the Discard Tray" for a whole release after the tray was
# removed. Keyed by tag: the check only fires once the component is really gone.

REMOVED_COMPONENTS = {
    # player-facing phrase : the save tag that would exist if it were still there
    "Discard Tray": "DiscardTray",
    "Player Rules tablet": "PlayerRules",
}


def test_no_instructions_reference_removed_components():
    tags = _save_tags()
    sources = [(rel, os.path.join(LUA_DIR, rel)) for rel in all_lua_files()]
    content = os.path.join(ROOT, "content")
    for dirpath, _dirs, files in os.walk(content):
        for fn in files:
            if fn.endswith(".md"):
                p = os.path.join(dirpath, fn)
                sources.append((os.path.relpath(p, ROOT).replace("\\", "/"), p))

    problems = []
    for label, path in sources:
        for i, line in enumerate(read_text(path).splitlines(), 1):
            if line.lstrip().startswith("--"):
                continue   # a comment explaining the removal is fine
            for phrase, tag in REMOVED_COMPONENTS.items():
                if phrase in line and tag not in tags:
                    problems.append(f"{label}:{i}: mentions {phrase!r}, which no "
                                    f"longer exists in the save: {line.strip()[:80]}")
    assert not problems, (
        "player-facing text still instructs players to use a component that was "
        "removed from the save:\n  " + "\n  ".join(problems))


# --------------------------------------------------------------------------
# 7. Day/Doom limits in player-facing strings must follow the difficulty.
# --------------------------------------------------------------------------
# getTotalDays() / getDoomLimit() exist because Long Weekend is 3 days with a
# 15-Doom track. Hardcoding "of 7" or "/ 30" in a string shows the wrong
# numbers on every non-Standard difficulty (the tooltips and the Doom help
# panel both did exactly this).

_HARDCODED_LIMIT_RE = re.compile(r'"[^"]*(?:\bof 7\b|/ ?30\b)[^"]*"')


def test_no_hardcoded_day_or_doom_limits_in_strings():
    problems = []
    for rel in all_lua_files():
        for i, line in enumerate(read_text(os.path.join(LUA_DIR, rel)).splitlines(), 1):
            if line.lstrip().startswith("--"):
                continue
            if _HARDCODED_LIMIT_RE.search(line):
                problems.append(f"{rel}:{i}: {line.strip()[:90]}")
    assert not problems, (
        "player-facing strings hardcode the Standard day count / Doom limit — "
        "these are wrong on Long Weekend (3 days, Doom 15) and Nightmare. Use "
        "getTotalDays() / getDoomLimit() (or the {totalDays} / {doomLimit} "
        "tooltip placeholders):\n  " + "\n  ".join(problems))


# --------------------------------------------------------------------------
# 8. gameState fields must be initialised before they are indexed.
# --------------------------------------------------------------------------
# Indexing a nil field ("attempt to index a nil value") is a hard crash. A
# field is safe if it has a default in the gameState literal, is defaulted in
# migrateGameState (which every loaded save runs through), or is lazily
# initialised (`gameState.x = gameState.x or {}`) earlier in the SAME function.
# (Function-scoped, not a line window: the idiom is to guard once at the top
# of a handler and index freely below.)

_FUNC_START_RE = re.compile(r"^\s*(?:local\s+)?function\b")


def _declared_gamestate_fields():
    src = read_text(os.path.join(LUA_DIR, "global.lua"))
    literal = src[src.index("gameState = {"):src.index("CHARACTER_STATS")]
    migrate = src[src.index("function migrateGameState"):src.index("function onLoad")]
    return (set(re.findall(r"^\s*(\w+)\s*=", literal, re.M))
            | set(re.findall(r"gs\.(\w+)", migrate)))


def test_gamestate_fields_initialised_before_indexing():
    declared = _declared_gamestate_fields()
    access_res = [
        re.compile(r"gameState\.(\w+)\s*\["),
        re.compile(r"\bi?pairs\(\s*gameState\.(\w+)\s*\)"),
        re.compile(r"#\s*gameState\.(\w+)\b"),
    ]
    problems = []
    for rel in all_lua_files():
        lines = read_text(os.path.join(LUA_DIR, rel)).splitlines()
        for i, line in enumerate(lines):
            if line.lstrip().startswith("--"):
                continue
            for rx in access_res:
                for m in rx.finditer(line):
                    name = m.group(1)
                    if name in declared:
                        continue
                    # Everything from the top of the enclosing function to here.
                    start = 0
                    for j in range(i, -1, -1):
                        if _FUNC_START_RE.match(lines[j]):
                            start = j
                            break
                    window = "\n".join(lines[start:i + 1])
                    # `gameState.x = gameState.x or {}` / `(gameState.x or {})`
                    if re.search(r"gameState\." + name + r"\s*=\s*gameState\."
                                 + name + r"\s+or\b", window):
                        continue
                    if re.search(r"gameState\." + name + r"\s+or\s*[{(]", window):
                        continue
                    if re.search(r"gameState\." + name + r"\s*=\s*[{(]", window):
                        continue
                    problems.append(f"{rel}:{i + 1}: gameState.{name} indexed with no "
                                    "default and no lazy init in the same function")
    assert not problems, (
        "gameState fields are indexed before anything guarantees they exist — "
        "a fresh setup or a loaded old save crashes with 'attempt to index a "
        "nil value'. Add the default to migrateGameState() (global.lua):\n  "
        + "\n  ".join(problems))


# --------------------------------------------------------------------------
# 8. The board art and the pieces must share one coordinate space.
# --------------------------------------------------------------------------
# 2026-07-25: every piece sat in a heap in the middle of the board while the
# printed rings / DAY COUNTER frame / Doom track sat far outside them. Nothing
# was misplaced — the Custom_Board mesh is ~9.14 local units per side at scale
# 1, not the 1.0 the build assumed, so Transform scale 12 painted the art
# across +/-110 world units while every object was authored inside +/-12.
# The pieces then occupied ~11% of the board. Guard the invariant that makes
# printed art and pieces line up: mesh_half * transform_scale == world_half.

def _board(save):
    for o in save["ObjectStates"]:
        if "MainBoard" in o.get("Tags", []):
            return o
    raise AssertionError("no object tagged MainBoard in the built save")


def test_board_art_spans_the_world_square_the_pieces_live_in():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import board_geometry as g

    board = _board(_load_save())
    t = board["Transform"]
    painted_half = g.BOARD_MESH_HALF * t["scaleX"]
    assert abs(painted_half - g.BOARD_WORLD_HALF) < 0.05, (
        f"the board paints its art across +/-{painted_half:.2f} world units but every "
        f"object position is authored inside +/-{g.BOARD_WORLD_HALF}. The pieces will "
        f"heap up in the middle {g.BOARD_WORLD_HALF / painted_half:.0%} of the board "
        f"while the printed rings/track sit outside them. Set the Custom_Board "
        f"Transform scale to BOARD_TRANSFORM_SCALE ({g.BOARD_TRANSFORM_SCALE:.5f}); "
        f"re-measure BOARD_MESH_HALF with auditBoardGeometry() if the mesh changed."
    )
    assert abs(t["scaleX"] - t["scaleZ"]) < 1e-6, "board must be square in x/z"


def test_board_snap_points_round_trip_to_world_coordinates():
    """AttachedSnapPoints are board-LOCAL; TTS multiplies them by the Transform
    scale. Authoring them in world units (or dividing by the wrong constant)
    sends moveDoomMarker to the wrong place — it once flung the marker to
    (120, 72), and the doom-track snaps must land back on the printed track."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import board_geometry as g

    save = _load_save()
    board = _board(save)
    scale = board["Transform"]["scaleX"]

    # Snap points are local, so the board's own ROTATION moves them too — a
    # ry=180 on the board negates every snap while the tiles it is supposed to
    # line up with stay at their absolute world coordinates. The board must
    # therefore stay at rotY=0 and compensate for TTS's flat-art convention in
    # the PNG instead (docs/tts-runtime.md "Rotations"); this once shipped with
    # ry=180 and rotated the whole printed map 180 degrees away from the pieces.
    assert board["Transform"]["rotY"] % 360 == 0, (
        f"the main board carries rotY={board['Transform']['rotY']}: that rotates the "
        f"printed art away from the pieces AND negates every AttachedSnapPoint. "
        f"Pre-rotate main_board.png in generate_assets instead.")

    def to_world(sp):
        """Board-local snap -> world. rotY is asserted 0 above, so this is a
        plain scale; keep it in one place so the two checks below can't drift."""
        return sp["Position"]["x"] * scale, sp["Position"]["z"] * scale

    # A few slots sit deliberately just off the board (the Market column runs
    # down its west flank), so allow a margin — this bound is here to catch an
    # order-of-magnitude error, not to police the edge.
    limit = g.BOARD_WORLD_HALF + 2.0
    problems = []
    for sp in board.get("AttachedSnapPoints", []) or []:
        wx, wz = to_world(sp)
        for tag in sp.get("Tags", []):
            if abs(wx) > limit or abs(wz) > limit:
                problems.append(
                    f"{tag}: local ({sp['Position']['x']:.3f}, {sp['Position']['z']:.3f}) "
                    f"-> world ({wx:.2f}, {wz:.2f}), way off a +/-{g.BOARD_WORLD_HALF} board")
    assert not problems, (
        "board snap points do not land near the board once TTS scales them:\n  "
        + "\n  ".join(problems))

    snaps = {tag: sp for sp in board["AttachedSnapPoints"]
             for tag in sp.get("Tags", [])}

    # The doom snaps must reproduce the printed track exactly. This is the
    # assertion that catches a wrong world->local divisor: scaling the snaps
    # by the wrong constant keeps them inside the board (so no bounds check
    # would fire) while sliding the marker off its printed cell.
    for step in (0, 15, 30):
        sp = snaps[f"Snap:Doom:{step}"]
        wx, wz = to_world(sp)
        ex, ez = g.doom_step_world(step)
        assert abs(wx - ex) < 0.01 and abs(wz - ez) < 0.01, (
            f"Snap:Doom:{step} lands at ({wx:.2f}, {wz:.2f}); the printed cell is "
            f"at ({ex:.2f}, {ez:.2f}) — the marker will sit off its track")

    # Every location snap must land on the tile it is supposed to hold.
    tiles = {t.split(":", 1)[1]: o["Transform"]
             for o in save["ObjectStates"] for t in o.get("Tags", [])
             if t.startswith("Location:")}
    for loc, tr in tiles.items():
        sp = snaps.get(f"Snap:Location:{loc}")
        assert sp, f"no Snap:Location:{loc} on the board"
        wx, wz = to_world(sp)
        assert abs(wx - tr["posX"]) < 0.01 and abs(wz - tr["posZ"]) < 0.01, (
            f"Snap:Location:{loc} lands at ({wx:.2f}, {wz:.2f}) but the tile sits at "
            f"({tr['posX']:.2f}, {tr['posZ']:.2f}) — the printed ring and the tile "
            f"have drifted apart")


# --------------------------------------------------------------------------
# 9. Hidden objects must actually be hidden.
# --------------------------------------------------------------------------
# Everything players never touch (decks, supply bags, benched boards) is
# parked below the table. That only reads as "hidden" while it sits under
# something opaque: the board covers +/-BOARD_WORLD_HALF, and the table
# covers a bit more. Parked further out it is in plain sight beside the
# table — which is exactly what showed up when the board was corrected from
# +/-110 world units down to +/-12, with a glass table on top.

def test_under_table_objects_stay_within_the_board_footprint():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import board_geometry as g

    save = _load_save()
    half = g.BOARD_WORLD_HALF
    strays = []
    for o in save["ObjectStates"]:
        t = o["Transform"]
        if t["posY"] >= 0:
            continue          # on the table, meant to be seen
        if abs(t["posX"]) > half or abs(t["posZ"]) > half:
            strays.append(
                f"{(o.get('Nickname') or o.get('Name'))!r} at "
                f"({t['posX']:.1f}, {t['posY']:.1f}, {t['posZ']:.1f})")
    assert not strays, (
        f"objects parked below the table but outside the board's +/-{half} "
        f"footprint — players see them sitting beside the table:\n  "
        + "\n  ".join(strays))


def test_the_table_is_not_see_through():
    """A glass top exposes the whole under-table library. Valid TTS tables:
    Table_Circular / Custom / Glass / Hexagon / None / Octagon / Plastic /
    Poker / RPG / Square."""
    table = _load_save().get("Table")
    assert table not in ("Table_Glass", "Table_None"), (
        f"Table is {table!r}: everything parked under the table is visible "
        "through it. Use an opaque table (Table_RPG).")


# --------------------------------------------------------------------------
# 10. Pieces on the board must sit ON it, not inside it.
# --------------------------------------------------------------------------
# The BOARD's top surface is higher than the TABLE's: measured in a live game
# at y ~ 1.79 against a 1.55 tabletop. Anything on the board authored at the
# table's surface height is swallowed by the board and simply not there —
# the location tiles (1.65) and the Doom marker (1.72) both vanished that way
# ("I can't see the graphics for each location", "the doom marker has gone
# missing"). Same class as the tabletop dead-band, one surface up.

def test_board_pieces_sit_above_the_board_surface():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import board_geometry as g

    # Read the real value out of build_save.py (it is derived from the board
    # tile's thickness, so a hardcoded copy here would silently rot).
    src = read_text(os.path.join(ROOT, "scripts", "build_save.py"))
    thickness = float(re.search(r"BOARD_TILE_THICKNESS\s*=\s*([\d.]+)", src).group(1))
    table_y = float(re.search(r"TABLE_SURFACE_Y\s*=\s*([\d.]+)", src).group(1))
    # A Custom_Tile's Thickness is scaled by scaleY (1 for the board), NOT by
    # the XZ transform scale. Multiplying by the latter here mirrored the same
    # error in build_save.py and put this "board top" 0.13 above the real one
    # — so the guard happily passed a board whose every piece hung in the air.
    BOARD_SURFACE_Y = table_y + thickness
    half = g.BOARD_WORLD_HALF

    save = _load_save()
    buried = []
    for o in save["ObjectStates"]:
        t = o["Transform"]
        tags = o.get("Tags", [])
        if "MainBoard" in tags or o.get("Name") == "HandTrigger":
            continue
        on_board = abs(t["posX"]) <= half and abs(t["posZ"]) <= half
        if on_board and 0 < t["posY"] < BOARD_SURFACE_Y:
            buried.append(
                f"{(o.get('Nickname') or o.get('Name'))!r} at y={t['posY']:.2f} "
                f"({t['posX']:.1f}, {t['posZ']:.1f})")
    assert not buried, (
        f"objects standing on the board below its top surface (y={BOARD_SURFACE_Y}) — "
        "the board swallows them and they are invisible in play. Author on-board "
        "spawns through BOARD_PIECE_Y in build_save.py:\n  " + "\n  ".join(buried))


# --------------------------------------------------------------------------
# 11. The printed map and the walkable map must be the same map.
# --------------------------------------------------------------------------
# A path variant exists in three places: the board art, the Lua Move graph,
# and the setup picker. They drifted — the board printed eight edges while
# LOCATION_ADJACENCY was a hard-coded star, so "Ring" was announced, a line
# from James's House to the Badminton Court was visible, and walking it was
# refused. scripts/path_layouts.py is now the single source; these tests are
# what stop it drifting again.

def _lua_path_layouts():
    src = read_text(os.path.join(LUA_DIR, "ui_actionbar_core.lua"))
    block = re.search(r"PATH_LAYOUTS\s*=\s*\{(.*?)\n\}", src, re.S)
    assert block, "PATH_LAYOUTS table not found in ui_actionbar_core.lua"
    out = {}
    for line in block.group(1).splitlines():
        m = re.match(r"\s*(\w+)\s*=\s*\{(.*)\},\s*$", line)
        if not m:
            continue
        edges = re.findall(r'\{"(\w+)"\s*,\s*"(\w+)"\}', m.group(2))
        out[m.group(1)] = sorted(tuple(sorted(e)) for e in edges)
    return out


def test_path_layouts_mirror_the_lua_table():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import path_layouts as pl

    lua = _lua_path_layouts()
    assert set(lua) == set(pl.PATH_LAYOUTS), (
        f"variant names differ — python {sorted(pl.PATH_LAYOUTS)} vs "
        f"lua {sorted(lua)}. Update PATH_LAYOUTS in ui_actionbar_core.lua.")
    for variant, edges in pl.PATH_LAYOUTS.items():
        assert lua[variant] == list(edges), (
            f"{variant}: the board is drawn with {edges} but Move allows "
            f"{lua[variant]}. Players walk the lines they can see — these must "
            "match exactly.")


def test_each_layout_is_the_shape_its_name_promises():
    """The setup panel sells these by name, so the name is a rule.

    "Ring (circular loop)" was a WHEEL for a long time: the four hub spokes
    plus a four-tile outer loop, eight roads, Ellie & Luca at degree four —
    and its own comment called it "the most open map", which is Sprawl's job.
    A player picked Ring and got a hub. Nothing checked the shape, only that
    the art and the Move table agreed on it, so both were consistently wrong.
    """
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import path_layouts as pl

    n = len(pl.LOCATIONS)

    def degrees(variant):
        return sorted(len(v) for v in pl.adjacency(variant).values())

    def connected(variant):
        adj = pl.adjacency(variant)
        seen, stack = set(), [pl.LOCATIONS[0]]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(adj[cur])
        return len(seen) == n

    # A ring is one closed loop through every tile: n tiles, n roads, and
    # every tile with exactly two neighbours.
    assert len(pl.PATH_LAYOUTS["Ring"]) == n, (
        f"Ring has {len(pl.PATH_LAYOUTS['Ring'])} roads; a ring of {n} "
        f"locations has exactly {n}")
    assert degrees("Ring") == [2] * n, (
        f"Ring degrees are {degrees('Ring')}; every tile on a ring has "
        "exactly two neighbours")

    # A star is one hub joined to every other tile and nothing else.
    assert degrees("Star") == [1] * (n - 1) + [n - 1], (
        f"Star degrees are {degrees('Star')}; a star is one hub and n-1 leaves")

    # A line has two ends and no branches.
    assert degrees("Linear") == [1, 1] + [2] * (n - 2), (
        f"Linear degrees are {degrees('Linear')}; a line has exactly two ends")

    # Sprawl is the open map: everything reaches everything in one move.
    assert degrees("Sprawl") == [n - 1] * n, (
        f"Sprawl degrees are {degrees('Sprawl')}; Sprawl is the complete graph")

    # ...and no layout may strand a tile, whatever its shape.
    for variant in pl.VARIANTS:
        assert connected(variant), f"{variant} leaves a tile unreachable"


def test_every_path_variant_has_board_art():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import path_layouts as pl

    missing = [v for v in pl.VARIANTS
               if not os.path.isfile(os.path.join(
                   ROOT, "art", "board", pl.board_art_name(v) + ".png"))]
    assert not missing, (
        f"no board image for {missing} — run scripts/generate_assets.py. "
        "Setup swaps the board to the picked variant; a missing image leaves "
        "the previous variant's lines printed under the new routes.")

    # ...and Lua must know where each one lives.
    assets = read_text(os.path.join(LUA_DIR, "assets.lua"))
    urls = re.search(r"BOARD_ART_URLS\s*=\s*\{(.*?)\n\}", assets, re.S)
    assert urls, "BOARD_ART_URLS table not found in lua/assets.lua"
    for v in pl.VARIANTS:
        assert re.search(rf"\b{v}\s*=", urls.group(1)), (
            f"BOARD_ART_URLS has no entry for {v} — applyPathVariant cannot "
            "repaint the board for that variant.")


def test_default_variant_matches_the_shipped_board_image():
    """The save ships main_board.png; it must be the default variant's art,
    or a game that never runs setup shows lines the Move graph disagrees with."""
    import hashlib
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import path_layouts as pl

    board_dir = os.path.join(ROOT, "art", "board")
    shipped = os.path.join(board_dir, "main_board.png")
    default = os.path.join(board_dir, pl.board_art_name(pl.DEFAULT_VARIANT) + ".png")
    assert os.path.isfile(shipped) and os.path.isfile(default), \
        "run scripts/generate_assets.py"

    def h(p):
        with open(p, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    assert h(shipped) == h(default), (
        f"main_board.png is not {pl.DEFAULT_VARIANT}'s art. Rerun "
        "scripts/generate_assets.py, or change DEFAULT_PATH_VARIANT in "
        "lua/ui_actionbar_core.lua to match.")


def test_lua_default_variant_matches_python():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import path_layouts as pl
    src = read_text(os.path.join(LUA_DIR, "ui_actionbar_core.lua"))
    m = re.search(r'DEFAULT_PATH_VARIANT\s*=\s*"(\w+)"', src)
    assert m, "DEFAULT_PATH_VARIANT not found in ui_actionbar_core.lua"
    assert m.group(1) == pl.DEFAULT_VARIANT, (
        f"lua default {m.group(1)!r} != python default {pl.DEFAULT_VARIANT!r}")


# --------------------------------------------------------------------------
# 12. Out-of-play objects must not answer the mouse.
# --------------------------------------------------------------------------
# Everything below the table is still a physical object: hovering the board
# raised tooltips and drew ghost outlines of cards that are not in play
# ("random tool tips for random cards ... they are supposed to be hidden").

def test_hidden_objects_do_not_answer_the_pointer():
    noisy = []
    for o in _load_save()["ObjectStates"]:
        if o["Transform"]["posY"] < 0 and o.get("Tooltip"):
            noisy.append(o.get("Nickname") or o.get("Name"))
    assert not noisy, (
        "objects parked below the table still show tooltips on hover — the "
        "player sees ghost cards that are out of play:\n  " + "\n  ".join(noisy))


# --------------------------------------------------------------------------
# 13. Runtime UI colours must not contradict the XML palette.
# --------------------------------------------------------------------------
# setActionEnabled re-applied a hard-coded dark plate at runtime, overwriting
# the light one in the XML — and set `color` without `textColor`, so the bar
# went back to dark-text-on-dark. Colours belong to the shared constants.

_BTN_COLOR_LITERAL = re.compile(
    r'UI\.setAttribute\(\s*[^,]+,\s*"color"\s*,\s*"(#[0-9A-Fa-f]+)"')


def test_action_buttons_do_not_hardcode_a_plate_colour():
    problems = []
    for rel in all_lua_files():
        src = read_text(os.path.join(LUA_DIR, rel))
        for i, line in enumerate(src.splitlines(), 1):
            if line.lstrip().startswith("--"):
                continue
            if not _BTN_COLOR_LITERAL.search(line):
                continue
            # Only action-bar buttons: banner/tab/toggle tinting is deliberate.
            if re.search(r'"act[A-Z]\w*"|buttonId', line):
                problems.append(f"{rel}:{i}: {line.strip()}")
    assert not problems, (
        "action-bar button colours set from a literal at runtime. That "
        "overwrites the XML palette, and setting `color` without `textColor` "
        "is how the bar ended up dark-on-dark twice. Use setButtonLabel() or "
        "BTN_DARK_PLATE / BTN_ON_DARK (helpers.lua):\n  " + "\n  ".join(problems))


# --------------------------------------------------------------------------
# 14. Player boards line up square with the game board.
def _player_board_zoom_rot():
    """build_save.PLAYER_BOARD_ZOOM_ROT — the half turn the player board OBJECT
    carries so its upright artwork renders correctly on the felt AND reads the
    right way up under Alt-zoom. Read from source rather than imported:
    importing build_save runs the whole build."""
    src = read_text(os.path.join(ROOT, "scripts", "build_save.py"))
    m = re.search(r"^PLAYER_BOARD_ZOOM_ROT\s*=\s*(\d+)", src, re.M)
    assert m, "PLAYER_BOARD_ZOOM_ROT is gone from build_save.py"
    return int(m.group(1))


# --------------------------------------------------------------------------
# They used to sit on a pentagon at angles like 294.3 and 215.1 degrees, which
# reads as scattered next to a square board, and the two northern seats hung
# off the felt. Square to the edges, tops facing in, clear of the board and of
# the Market column.

def test_player_boards_are_square_to_the_board_and_face_it():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import math

    import board_geometry as g

    save = _load_save()
    half = g.BOARD_WORLD_HALF
    # Measured from the built save, not hard-coded: the Market column is the
    # thing the west seats have to clear, and it has moved before.
    market_west = min(
        (o["Transform"]["posX"] - o["Transform"]["scaleX"] * g.BOARD_MESH_HALF
         for o in save["ObjectStates"]
         if any(t.startswith("MarketSlot:") for t in o.get("Tags", []))),
        default=-13.7)
    # Inner edge of the east/west hand zones, also measured from the save.
    hand_inner = min(
        (abs(o["Transform"]["posX"]) - o["Transform"]["scaleZ"] / 2
         for o in save["ObjectStates"]
         if o.get("Name") == "HandTrigger" and abs(o["Transform"]["posX"]) > 1),
        default=19.0)
    problems = []
    for o in save["ObjectStates"]:
        if not any(t.startswith("PlayerBoard:") for t in o.get("Tags", [])):
            continue
        name = o.get("Nickname", "?")
        t = o["Transform"]
        ry = t["rotY"] % 360
        if min(abs(ry - a) for a in (0, 90, 180, 270, 360)) > 0.01:
            problems.append(f"{name}: rotY={ry:.1f} is not square to the board")
            continue
        # The printed top does NOT point along +z at rotY=0. The artwork is
        # authored upright and the OBJECT carries the half turn a Custom_Tile
        # needs to render right way up (build_save.PLAYER_BOARD_ZOOM_ROT) —
        # done that way round because TTS draws Alt-zoom from the object's
        # local frame, so artwork pre-rotated to suit the felt magnified upside
        # down. Read the constant rather than hard-coding the offset, so this
        # follows the build instead of quietly disagreeing with it.
        facing = math.radians((ry + _player_board_zoom_rot()) % 360)
        nx, nz = math.sin(facing), math.cos(facing)
        if nx * -t["posX"] + nz * -t["posZ"] <= 0:
            problems.append(f"{name}: printed top faces away from the board")
        # Must not sit on top of the board itself.
        hx, hz = ((t["scaleX"], t["scaleZ"]) if ry % 180 == 0
                  else (t["scaleZ"], t["scaleX"]))
        if not (abs(t["posX"]) - hx >= half - 0.01 or abs(t["posZ"]) - hz >= half - 0.01):
            problems.append(
                f"{name}: overlaps the board (centre {t['posX']:.1f},{t['posZ']:.1f})")
        # West-side boards must clear the Market column.
        if t["posX"] < 0 and (t["posX"] + hx) > market_west:
            problems.append(
                f"{name}: overlaps the Market column (inner edge "
                f"{t['posX'] + hx:.2f}, the market frames reach {market_west:.2f})")
        # ... and must not be pushed so far out that they stick into the
        # seat's private hand zone. The flank between the two is narrow and
        # the boards sit hard against the outer limit.
        if abs(t["posX"]) + hx > hand_inner + 0.01:
            problems.append(
                f"{name}: outer edge {abs(t['posX']) + hx:.2f} crosses into the "
                f"hand zone (starts at {hand_inner:.2f})")
    assert not problems, (
        "player boards are not lined up with the game board:\n  " + "\n  ".join(problems))


# The Market column is beside the board, not on it. It shipped as five
# full-size TTS Notecards centred at x=-12.5: the notecards AND the cards
# dealt onto them both lay across the printed map ("the market slots are
# covering the board up"). What matters is the footprint of the CARD that
# lands on each slot, not just the marker — the marker can be shrunk to
# nothing and a 2.3-unit card will still cover the board.

def test_market_column_clears_the_printed_board():
    import re
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import board_geometry as g

    src = open(os.path.join(ROOT, "scripts", "build_save.py"), encoding="utf-8").read()
    card_w, card_l = (float(v) for v in re.search(
        r"MARKET_CARD_W,\s*MARKET_CARD_L\s*=\s*([\d.]+),\s*([\d.]+)", src).groups())

    half = g.BOARD_WORLD_HALF
    problems = []
    for o in _load_save()["ObjectStates"]:
        if not any(t.startswith("MarketSlot:") for t in o.get("Tags", [])):
            continue
        t = o["Transform"]
        name = o.get("Nickname", "?")
        # The frame itself, and the card that will be dealt onto it.
        for what, w, length in (("frame", t["scaleX"] * 2 * g.BOARD_MESH_HALF,
                                 t["scaleZ"] * 2 * g.BOARD_MESH_HALF),
                                ("dealt card", card_w, card_l)):
            over_x = abs(t["posX"]) - w / 2 < half
            over_z = abs(t["posZ"]) - length / 2 < half
            if over_x and over_z:
                problems.append(
                    f"{name}: its {what} reaches x={abs(t['posX']) - w / 2:.2f}, "
                    f"z={abs(t['posZ']) - length / 2:.2f} — inside the +/-{half} board")
    assert not problems, (
        "the Market column lies across the printed board:\n  " + "\n  ".join(problems)
        + "\n  push MARKET_COLUMN_X further west in build_save.py")


# A locked object never settles, so whatever y it is authored at is where it
# stays forever. A flat tile parked even a tenth of a unit high reads as
# floating from a seated camera angle ("the player card describing James is
# levitating off the table") — its bottom face has to be ON the felt, and that
# height is derivable from its own thickness rather than a hand-tuned constant.

def test_locked_table_level_tiles_rest_on_the_table_rather_than_hover():
    import re
    build_src = open(os.path.join(ROOT, "scripts", "build_save.py"),
                     encoding="utf-8").read()
    table_y = float(re.search(r"TABLE_SURFACE_Y\s*=\s*([\d.]+)", build_src).group(1))

    problems = []
    for o in _load_save()["ObjectStates"]:
        if not any(t.split(":", 1)[0] in ("PlayerBoard", "MarketSlot")
                   for t in o.get("Tags", []) if ":" in t):
            continue
        t = o["Transform"]
        if t["posY"] < table_y:          # deliberately benched under the table
            continue
        half = o["CustomImage"]["CustomTile"]["Thickness"] * t["scaleY"] / 2.0
        gap = t["posY"] - half - table_y
        if abs(gap) > 0.01:
            problems.append(
                f"{o.get('Nickname', '?')}: bottom face sits {gap:+.2f} from the felt "
                f"(posY={t['posY']}, half-thickness={half})")
    assert not problems, (
        "locked table-level tiles do not rest on the table surface:\n  "
        + "\n  ".join(problems)
        + "\n  a locked object never settles — author posY as "
          "TABLE_SURFACE_Y + thickness/2 (that is what SURFACE_Y is)")
