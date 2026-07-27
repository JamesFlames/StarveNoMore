"""Single source of truth for main-board geometry shared by the art renderer
(generate_assets.py) and the save builder (build_save.py).

THREE numbers, and conflating any two of them is the bug that heaped every
piece in the middle of the board (2026-07-25):

  BOARD_WORLD_HALF     the world half-extent the art is AUTHORED across.
                       Every object position in build_save.py lives inside
                       this square, so the printed rings / DAY COUNTER frame
                       / Doom track must span exactly it.
  BOARD_MESH_HALF      the local half-extent of the TTS Custom_Board mesh at
                       Transform scale 1. This is NOT 1.0 — it was measured
                       in a live game at ~9.14 (auditBoardGeometry, lua/audit.lua).
  BOARD_TRANSFORM_SCALE  the Transform scale to write into the save, chosen so
                       BOARD_MESH_HALF * scale == BOARD_WORLD_HALF.

The old code assumed the mesh spanned local -1..+1 and therefore used a single
"BOARD_SCALE = 12" as both the transform scale and the world half-extent. With
a mesh half-extent of 9.14 that painted the board across +/-110 world units:
the art was stretched nine times too wide, so every piece (all authored inside
+/-12) landed in a heap in the middle while the printed rings sat far outside
them. The pieces were never misplaced — the board was.

AttachedSnapPoints are stored in BOARD-LOCAL space and TTS multiplies them by
the Transform scale, so world->local is a divide by BOARD_TRANSFORM_SCALE
(world_to_local) — NOT by BOARD_WORLD_HALF.

Axis convention (verified in TTS): a Custom_Board at rotY=0 renders its image
rotated 180 degrees relative to the default table view (the same reason cards
and the Day Counter carry ry=180 to read right-side-up). generate_assets
therefore composes the board image normally and rotates the finished image
180 degrees before saving, which makes the net mapping for AUTHORED pixel
coordinates:

    image left  -> -x  (west,  screen left in the default view)
    image top   -> +z  (north, screen top  in the default view)

i.e. px_to_world_x is the plain linear map and px_to_world_z is NEGATED.
Anything that draws on the board image must author against this mapping
(world_to_px / world_to_py are the inverses).
"""

BOARD_IMAGE_SIZE = 4096    # px — art/board/main_board.png is square

# World half-extent the board art is authored across (the board spans
# -12..+12 in x and z). Changing this means regenerating the board art.
BOARD_WORLD_HALF = 12.0

# Local half-extent of the board mesh at Transform scale 1.
#
# The board is a Custom_TILE, not a Custom_Board. A Custom_Board always draws
# a brown border around the image and that border CANNOT be removed
# (kb.tabletopsimulator.com + Steam discussions): getBoundsNormalized() then
# reports the frame's extent while the art only spans the inner area, so every
# printed feature sits pulled toward the centre relative to the physical
# pieces — worst at the corners, which is why the DAY COUNTER frame and the
# location rings never lined up however carefully both were placed. A tile has
# no border: the image fills it exactly.
#
# 0.99 = measured, from the location tiles reporting 4.95 world units at
# Transform scale 2.5 (auditObjectFootprints).
BOARD_MESH_HALF = 0.99

# Transform scale to author in the save so the art spans exactly
# +/-BOARD_WORLD_HALF world units.
BOARD_TRANSFORM_SCALE = BOARD_WORLD_HALF / BOARD_MESH_HALF


def px_to_world_x(px):
    """Authored board-image x pixel -> world x coordinate."""
    return (px / BOARD_IMAGE_SIZE - 0.5) * 2.0 * BOARD_WORLD_HALF


def px_to_world_z(py):
    """Authored board-image y pixel -> world z coordinate (negated: image top
    renders at +z once the finished image is rotated 180)."""
    return -(py / BOARD_IMAGE_SIZE - 0.5) * 2.0 * BOARD_WORLD_HALF


def world_to_px(wx):
    """World x (board centered at origin) -> authored image x pixel."""
    return (wx / (2.0 * BOARD_WORLD_HALF) + 0.5) * BOARD_IMAGE_SIZE


def world_to_py(wz):
    """World z (board centered at origin) -> authored image y pixel."""
    return (0.5 - wz / (2.0 * BOARD_WORLD_HALF)) * BOARD_IMAGE_SIZE


def world_to_local(w):
    """World offset from the board centre -> board-local units, the space
    AttachedSnapPoints are stored in (TTS multiplies them by the Transform
    scale, so board.positionToWorld returns the world value again)."""
    return w / BOARD_TRANSFORM_SCALE


# Day Counter: the gadget's world position AND the centre of the frame
# printed for it. Shared so the two cannot drift apart.
#
# x = -8.0, not -10: at -10 the counter (2.97 wide) reached x=-11.49 and
# overlapped Market Slot 1's card (which reaches -11.35), so that card could
# not lie flat.
DAY_COUNTER_WORLD = (-8.0, 8.0)


# Dawn card display — today's card and the pile of spent ones.
#
# These were fixed positions in day_loop.lua with nothing printed for them, at
# (-7.5, 9.5) and (-4.5, 9.5): a card is 2.3 x 3.2, so today's Dawn landed on
# top of the Day Counter's frame AND the printed "STARVE NO MORE" title. It
# read as a card someone had dropped there rather than the day's event
# ("the cards we get each new day are kind of under the day counter").
#
# They now sit in the board's clear east band — south of the severity legend
# (which starts at z 9.84), north of Rayman's ring (which ends at z -0.7), and
# east of the Badminton/Ellie rings (which end at x 3.3) — inside a printed
# box that says what they are. Shared with day_loop.lua via
# tests/test_cross_refs.py::test_lua_dawn_display_mirrors_board_geometry.
DAWN_REVEAL_WORLD = (6.3, 4.9)    # today's card
DAWN_DISCARD_WORLD = (9.3, 4.9)   # the spent pile
DAWN_SLOT_W, DAWN_SLOT_L = 2.7, 3.7    # printed frame per slot (card + margin)
DAWN_BOX = (4.6, 1.9, 11.0, 7.9)       # x0, z0, x1, z1 of the enclosing box

# Printed Doom track (drawn by generate_assets.generate_main_board):
# a horizontal strip along the board's SOUTH edge (the only band clear of
# location rings and their labels), running step 0 (west) to the limit (east).
#
# The track always occupies the SAME strip of board; what changes with the
# difficulty is how many cells that strip is cut into. Long Weekend loses at
# Doom 15, so its board prints 16 fatter cells over the same span — the marker
# still crosses the whole track exactly as the world is consumed. Printing 31
# cells and stopping the marker halfway is the bug this parameter fixes ("the
# doom track is halved, but it still goes up to 30").
DOOM_TRACK_WORLD_Z = -11.5       # row center, world units (was -11.2: the
                                 # Basketball ring overlapped the track)
DOOM_STEP0_WORLD_X = -10.9       # center of step 0's cell (west end)
DOOM_STEP30_WORLD_X = 10.9       # center of the LAST cell (east end), whatever
                                 # number that cell carries
DOOM_TRACK_PX_Y = world_to_py(DOOM_TRACK_WORLD_Z)
DOOM_STEP0_PX_X = world_to_px(DOOM_STEP0_WORLD_X)

# The Doom limit the shipped board art is drawn for. Other limits get their
# own board image (see DOOM_LIMITS / generate_assets.generate_all_main_boards).
DEFAULT_DOOM_LIMIT = 30

# Every distinct Doom limit DIFFICULTY_PARAMS (lua/global.lua) can produce.
# Standard and Nightmare both end at 30 and share one board.
DOOM_LIMITS = (30, 15)

# Nights survived per limit, for the board's printed subtitle — same source,
# so a board can't advertise 7 nights on a 3-day game.
DOOM_LIMIT_DAYS = {30: 7, 15: 3}

# Printed threshold ribbons. MIRRORS DOOM_THRESHOLDS in lua/global.lua — the
# board must promise exactly what checkDoomThresholds actually fires, and this
# used to be a third hand-typed copy of those numbers.
# tests/test_cross_refs.py::test_board_doom_thresholds_mirror_the_lua_table
# guards the mirror.
DOOM_THRESHOLDS = {
    10: "Threats +1",       # night
    15: "Crafts +1 cost",   # scarcity
    20: "+1 Sa loss",       # tick
    25: "Bosses any",       # anyPhaseBosses
}


def doom_step_px(step, limit=DEFAULT_DOOM_LIMIT):
    """Authored image (x, y) pixel center of a Doom step's cell."""
    span = world_to_px(DOOM_STEP30_WORLD_X) - DOOM_STEP0_PX_X
    return DOOM_STEP0_PX_X + span * (step / float(limit)), DOOM_TRACK_PX_Y


def doom_step_world(step, limit=DEFAULT_DOOM_LIMIT):
    """World (x, z) of a Doom step's cell center (board centered at origin)."""
    px, py = doom_step_px(step, limit)
    return px_to_world_x(px), px_to_world_z(py)


def doom_step_local(step, limit=DEFAULT_DOOM_LIMIT):
    """Board-local (x, z) of a Doom step's cell center — the space the
    AttachedSnapPoints for Snap:Doom:N are stored in."""
    wx, wz = doom_step_world(step, limit)
    return world_to_local(wx), world_to_local(wz)


def doom_thresholds_for(limit):
    """The ribbons a board drawn for `limit` may print: the thresholds that
    can actually fire before the game ends, plus DEFEAT on the last cell.

    A threshold ON the limit is unreachable — the defeat check and the
    threshold check both trigger at that value and defeat wins — so the last
    cell reads DEFEAT and nothing else (Long Weekend's 15 is exactly that
    case: 'Crafts +1 cost' can never apply).
    """
    out = {s: label for s, label in DOOM_THRESHOLDS.items() if s < limit}
    out[limit] = "DEFEAT"
    return out
