"""Single source of truth for main-board geometry shared by the art renderer
(generate_assets.py) and the save builder (build_save.py).

The main board is a square Custom_Board: image BOARD_IMAGE_SIZE px on a side,
mesh spanning board-local -1..+1, Transform scale BOARD_SCALE. So one image
pixel = 2/BOARD_IMAGE_SIZE board-local units = 2*BOARD_SCALE/BOARD_IMAGE_SIZE
world units, and AttachedSnapPoints (stored board-local) convert to world by
multiplying by BOARD_SCALE.

Axis convention assumed here: image left edge -> -x, image top edge -> -z
(matching how the location nodes were authored against loc_positions in
build_save.py). If in TTS the board image turns out to render rotated 180
degrees (Doom marker at the far end of the printed track / on the wrong
side of the board), set BOARD_IMAGE_AXIS_SIGN = -1 and rebuild.
"""

BOARD_IMAGE_SIZE = 4096   # px — art/board/main_board.png is square
BOARD_SCALE = 12          # Transform scale of the Custom_Board in the save
BOARD_IMAGE_AXIS_SIGN = 1 # flip to -1 if the image renders rotated 180 deg

# Printed Doom track (drawn by generate_assets.generate_main_board):
# a vertical column on the right side of the image. Step i's cell spans
# DOOM_TRACK_PX_TOP + i*DOOM_STEP_PX .. +(i+1)*DOOM_STEP_PX vertically.
DOOM_TRACK_PX_X = 3600       # column center
DOOM_TRACK_PX_TOP = 300      # top edge of step 0's cell
DOOM_TRACK_PX_BOTTOM = 3800  # top edge of step 30's cell
DOOM_STEP_PX = (DOOM_TRACK_PX_BOTTOM - DOOM_TRACK_PX_TOP) / 30.0


def px_to_local(px):
    """Board-image pixel offset (one axis) -> board-local coordinate."""
    return BOARD_IMAGE_AXIS_SIGN * (px / BOARD_IMAGE_SIZE - 0.5) * 2.0


def doom_step_local(step):
    """Board-local (x, z) of Doom step's cell center on the printed track."""
    cell_center_px = DOOM_TRACK_PX_TOP + (step + 0.5) * DOOM_STEP_PX
    return px_to_local(DOOM_TRACK_PX_X), px_to_local(cell_center_px)


def doom_step_world(step):
    """World (x, z) of Doom step's cell center (board centered at origin)."""
    lx, lz = doom_step_local(step)
    return lx * BOARD_SCALE, lz * BOARD_SCALE
