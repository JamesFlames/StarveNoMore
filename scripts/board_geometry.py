"""Single source of truth for main-board geometry shared by the art renderer
(generate_assets.py) and the save builder (build_save.py).

The main board is a square Custom_Board: image BOARD_IMAGE_SIZE px on a side,
mesh spanning board-local -1..+1, Transform scale BOARD_SCALE. So one image
pixel = 2/BOARD_IMAGE_SIZE board-local units = 2*BOARD_SCALE/BOARD_IMAGE_SIZE
world units, and AttachedSnapPoints (stored board-local) convert to world by
multiplying by BOARD_SCALE.

Axis convention (verified in TTS): a Custom_Board at rotY=0 renders its image
rotated 180 degrees relative to the default table view (the same reason cards
and the Day Counter carry ry=180 to read right-side-up). generate_assets
therefore composes the board image normally and rotates the finished image
180 degrees before saving, which makes the net mapping for AUTHORED pixel
coordinates:

    image left  -> -x  (west,  screen left in the default view)
    image top   -> +z  (north, screen top  in the default view)

i.e. px_to_local_x is the plain linear map and px_to_local_z is NEGATED.
Anything that draws on the board image must author against this mapping
(world_to_px / world_to_py are the inverses).
"""

BOARD_IMAGE_SIZE = 4096   # px — art/board/main_board.png is square
BOARD_SCALE = 12          # Transform scale of the Custom_Board in the save


def px_to_local_x(px):
    """Authored board-image x pixel -> board-local x coordinate."""
    return (px / BOARD_IMAGE_SIZE - 0.5) * 2.0


def px_to_local_z(py):
    """Authored board-image y pixel -> board-local z coordinate (negated:
    image top renders at +z once the finished image is rotated 180)."""
    return -(py / BOARD_IMAGE_SIZE - 0.5) * 2.0


def world_to_px(wx):
    """World x (board centered at origin) -> authored image x pixel."""
    return (wx / (2.0 * BOARD_SCALE) + 0.5) * BOARD_IMAGE_SIZE


def world_to_py(wz):
    """World z (board centered at origin) -> authored image y pixel."""
    return (0.5 - wz / (2.0 * BOARD_SCALE)) * BOARD_IMAGE_SIZE


# Printed Doom track (drawn by generate_assets.generate_main_board):
# a horizontal strip along the board's SOUTH edge (the only band clear of
# location rings and their labels), running step 0 (west) to 30 (east).
DOOM_TRACK_WORLD_Z = -11.2       # row center, world units
DOOM_STEP0_WORLD_X = -10.9       # center of step 0's cell
DOOM_STEP30_WORLD_X = 10.9       # center of step 30's cell
DOOM_TRACK_PX_Y = world_to_py(DOOM_TRACK_WORLD_Z)
DOOM_STEP0_PX_X = world_to_px(DOOM_STEP0_WORLD_X)
DOOM_STEP_PX = (world_to_px(DOOM_STEP30_WORLD_X) - DOOM_STEP0_PX_X) / 30.0


def doom_step_px(step):
    """Authored image (x, y) pixel center of a Doom step's cell."""
    return DOOM_STEP0_PX_X + step * DOOM_STEP_PX, DOOM_TRACK_PX_Y


def doom_step_local(step):
    """Board-local (x, z) of Doom step's cell center on the printed track."""
    px, py = doom_step_px(step)
    return px_to_local_x(px), px_to_local_z(py)


def doom_step_world(step):
    """World (x, z) of Doom step's cell center (board centered at origin)."""
    lx, lz = doom_step_local(step)
    return lx * BOARD_SCALE, lz * BOARD_SCALE
