"""Single source of truth for the map's path layouts.

A "path variant" is the shape of the map graph: which locations connect to
which. It is chosen during setup, and it has to agree in THREE places or the
board lies to the player:

  1. the printed board art  (generate_assets renders one board per variant),
  2. the Move adjacency     (PATH_LAYOUTS in lua/ui_actionbar_core.lua),
  3. the variant the setup UI advertises.

They drifted before: the board printed eight edges while the adjacency table
was a hard-coded star, so "Ring" was announced, a line was visible from
James's House to the Badminton Court, and walking it was refused. This module
is the one place the graphs are written down;
tests/test_regression_guards.py::test_path_layouts_mirror_the_lua_table and
::test_every_path_variant_has_board_art keep the other two honest.

Edges are unordered pairs of LOCATION KEYS (the Location:<key> tags), always
stored with the endpoints sorted so an edge can't be listed twice.
"""

LOCATIONS = [
    "JamesHouse",
    "RaymanHouse",
    "EllieLucaHouse",
    "BasketballCourt",
    "BadmintonCourt",
]

# World (x, z) of each location, the ONE place they are written down:
# build_save.py places the tiles and snap points from this, generate_assets
# draws the rings from it. They used to be duplicated in both files.
#
# BasketballCourt sits at z=-6.8, not -8: at -8 its printed ring reached
# z=-11.8 and ran straight through the Doom track ("the basketball court
# graphic should not overlap the doom counter").
LOCATION_WORLD = {
    "JamesHouse":      (-8.0, -4.0),
    "RaymanHouse":     ( 8.0, -4.0),
    "EllieLucaHouse":  ( 0.0,  0.0),
    "BasketballCourt": ( 0.0, -6.8),
    "BadmintonCourt":  ( 0.0,  8.0),
}

# Printed ring radius around each location, world units. Bigger than the
# 2.5-unit tile half-width so the ring peeks out around the art, small
# enough to clear the Doom track along the south edge.
LOCATION_RING_R = 3.3

# Display names as printed on the board (generate_assets draws these).
LOCATION_LABELS = {
    "JamesHouse":      "James's House",
    "RaymanHouse":     "Rayman's House",
    "EllieLucaHouse":  "Ellie & Luca's House",
    "BasketballCourt": "Basketball Court",
    "BadmintonCourt":  "Badminton Court",
}


def _edges(*pairs):
    return sorted(tuple(sorted(p)) for p in pairs)


# Ellie & Luca's House sits at the map's centre, so it is the natural hub;
# the four others sit around it. Each variant is a genuinely different shape,
# not a re-skin: the number of routes out of a tile is the whole tactical
# difference between them.
PATH_LAYOUTS = {
    # Hub and spokes only — every trip goes through the middle. Longest
    # journeys, most pressure on Ellie & Luca's House.
    "Star": _edges(
        ("EllieLucaHouse", "JamesHouse"),
        ("EllieLucaHouse", "RaymanHouse"),
        ("EllieLucaHouse", "BasketballCourt"),
        ("EllieLucaHouse", "BadmintonCourt"),
    ),
    # Hub plus a full outer loop — you can always go around. The most open
    # map, and the layout the original board art drew.
    "Ring": _edges(
        ("EllieLucaHouse", "JamesHouse"),
        ("EllieLucaHouse", "RaymanHouse"),
        ("EllieLucaHouse", "BasketballCourt"),
        ("EllieLucaHouse", "BadmintonCourt"),
        ("JamesHouse", "BasketballCourt"),
        ("BasketballCourt", "RaymanHouse"),
        ("RaymanHouse", "BadmintonCourt"),
        ("BadmintonCourt", "JamesHouse"),
    ),
    # Hub plus one shortcut per house — each home has its own back door.
    "Compact": _edges(
        ("EllieLucaHouse", "JamesHouse"),
        ("EllieLucaHouse", "RaymanHouse"),
        ("EllieLucaHouse", "BasketballCourt"),
        ("EllieLucaHouse", "BadmintonCourt"),
        ("JamesHouse", "BasketballCourt"),
        ("RaymanHouse", "BadmintonCourt"),
    ),
    # Everything connects to everything: one move reaches any tile.
    "Sprawl": _edges(*[
        (a, b) for i, a in enumerate(LOCATIONS) for b in LOCATIONS[i + 1:]
    ]),
    # A single chain: James - Basketball - Ellie & Luca - Badminton - Rayman.
    # The houses are four moves apart; splitting up is genuinely dangerous.
    "Linear": _edges(
        ("JamesHouse", "BasketballCourt"),
        ("BasketballCourt", "EllieLucaHouse"),
        ("EllieLucaHouse", "BadmintonCourt"),
        ("BadmintonCourt", "RaymanHouse"),
    ),
}

# The variant the shipped save's board image is drawn for (build_save writes
# art/board/main_board.png from this one, so a game that never runs setup
# still shows a board whose lines match the default adjacency).
DEFAULT_VARIANT = "Ring"

VARIANTS = list(PATH_LAYOUTS)


def adjacency(variant):
    """{location: [neighbour, ...]} for a variant, neighbours sorted."""
    out = {loc: [] for loc in LOCATIONS}
    for a, b in PATH_LAYOUTS[variant]:
        out[a].append(b)
        out[b].append(a)
    return {k: sorted(v) for k, v in out.items()}


def board_art_name(variant):
    """Asset basename for a variant's board image."""
    return f"main_board_{variant.lower()}"
