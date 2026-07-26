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


# Printed Doom track (drawn by generate_assets.generate_main_board):
# a horizontal strip along the board's SOUTH edge (the only band clear of
# location rings and their labels), running step 0 (west) to 30 (east).
DOOM_TRACK_WORLD_Z = -11.5       # row center, world units (was -11.2: the
                                 # Basketball ring overlapped the track)
DOOM_STEP0_WORLD_X = -10.9       # center of step 0's cell
DOOM_STEP30_WORLD_X = 10.9       # center of step 30's cell
DOOM_TRACK_PX_Y = world_to_py(DOOM_TRACK_WORLD_Z)
DOOM_STEP0_PX_X = world_to_px(DOOM_STEP0_WORLD_X)
DOOM_STEP_PX = (world_to_px(DOOM_STEP30_WORLD_X) - DOOM_STEP0_PX_X) / 30.0


def doom_step_px(step):
    """Authored image (x, y) pixel center of a Doom step's cell."""
    return DOOM_STEP0_PX_X + step * DOOM_STEP_PX, DOOM_TRACK_PX_Y


def doom_step_world(step):
    """World (x, z) of a Doom step's cell center (board centered at origin)."""
    px, py = doom_step_px(step)
    return px_to_world_x(px), px_to_world_z(py)


def doom_step_local(step):
    """Board-local (x, z) of a Doom step's cell center — the space the
    AttachedSnapPoints for Snap:Doom:N are stored in."""
    wx, wz = doom_step_world(step)
    return world_to_local(wx), world_to_local(wz)
