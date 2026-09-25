-- assets.lua
-- Image URLs the *scripts* load at runtime: the board image setup swaps in
-- for the chosen path variant and Doom length (BOARD_ART_URLS, below). Art on
-- the table's objects is baked into the save by build_save.py (its
-- ASSET_MAP), not read from here — don't add an entry nothing reads, it only
-- grows the hosted payload.
-- During local dev: run scripts/serve_art.bat (iwanttoplay starts it).
-- Publishing needs no edit here: build_save.py --publish rewrites _BASE.

-- TTS has no require() — this file is concatenated into the global script.

-- The local dev server (scripts/serve_art.bat) now serves the repo root,
-- so paths under art/ go via the /art prefix. Sound URLs go through
-- audio_manifest.lua which uses its own /sounds prefix.
local _BASE = "http://localhost:8080/art"
local function url(path) return _BASE .. "/" .. path end

ASSETS = {
    -- Standard and Nightmare: the 30-step Doom track.
    BOARD_MAIN_STAR      = url("board/main_board_star.png"),
    BOARD_MAIN_RING      = url("board/main_board_ring.png"),
    BOARD_MAIN_COMPACT   = url("board/main_board_compact.png"),
    BOARD_MAIN_SPRAWL    = url("board/main_board_sprawl.png"),
    BOARD_MAIN_LINEAR    = url("board/main_board_linear.png"),
    -- Long Weekend halves the Doom track, so it needs its own board: the
    -- printed track ends (and says DEFEAT) at 15 instead of 30.
    BOARD_MAIN_STAR_D15    = url("board/main_board_star_d15.png"),
    BOARD_MAIN_RING_D15    = url("board/main_board_ring_d15.png"),
    BOARD_MAIN_COMPACT_D15 = url("board/main_board_compact_d15.png"),
    BOARD_MAIN_SPRAWL_D15  = url("board/main_board_sprawl_d15.png"),
    BOARD_MAIN_LINEAR_D15  = url("board/main_board_linear_d15.png"),
    -- Story lengthens the Doom track to 35 (§17.2) — same 7-day week, more
    -- room before the world ends — so it needs its own board too.
    BOARD_MAIN_STAR_D35    = url("board/main_board_star_d35.png"),
    BOARD_MAIN_RING_D35    = url("board/main_board_ring_d35.png"),
    BOARD_MAIN_COMPACT_D35 = url("board/main_board_compact_d35.png"),
    BOARD_MAIN_SPRAWL_D35  = url("board/main_board_sprawl_d35.png"),
    BOARD_MAIN_LINEAR_D35  = url("board/main_board_linear_d35.png"),
}

-- Board art per path variant. The printed lines ARE the map, so this
-- table and PATH_LAYOUTS (ui_actionbar_core.lua) must offer the same
-- variant names — tests/test_regression_guards.py checks that.
-- Keyed [variant][doomLimit]: the printed Doom track is part of the board,
-- so Long Weekend's halved track means a different image, not just different
-- text in the HUD. Standard and Nightmare share the 30 board.
BOARD_ART_URLS = {
    -- One row per line: tests/test_cross_refs.py matches each row with a
    -- single-line regex, so wrapping an entry onto a second line hides it.
    Star    = { [30] = ASSETS.BOARD_MAIN_STAR,    [15] = ASSETS.BOARD_MAIN_STAR_D15,    [35] = ASSETS.BOARD_MAIN_STAR_D35 },
    Ring    = { [30] = ASSETS.BOARD_MAIN_RING,    [15] = ASSETS.BOARD_MAIN_RING_D15,    [35] = ASSETS.BOARD_MAIN_RING_D35 },
    Compact = { [30] = ASSETS.BOARD_MAIN_COMPACT, [15] = ASSETS.BOARD_MAIN_COMPACT_D15, [35] = ASSETS.BOARD_MAIN_COMPACT_D35 },
    Sprawl  = { [30] = ASSETS.BOARD_MAIN_SPRAWL,  [15] = ASSETS.BOARD_MAIN_SPRAWL_D15,  [35] = ASSETS.BOARD_MAIN_SPRAWL_D35 },
    Linear  = { [30] = ASSETS.BOARD_MAIN_LINEAR,  [15] = ASSETS.BOARD_MAIN_LINEAR_D15,  [35] = ASSETS.BOARD_MAIN_LINEAR_D35 },
}
