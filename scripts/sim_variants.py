"""Scenario and map-topology data for `simulate_balance.py`.

Two setup-time dials the balance sim did not model until now, both of which
are drawn at random by `startGame` in `lua/setup.lua` — so **every real game
has one of each**, and a sim that models neither was measuring a table state
that never occurs:

  * **Scenario** (`SCENARIOS` in `lua/setup.lua`) — a week-long rules twist,
    drawn from eight at setup. This module mirrors the *flag sets*; the sim
    reads them and applies the behaviour.
  * **Path variant** (`PATH_LAYOUTS`, `scripts/path_layouts.py`) — the shape
    of the map graph, drawn from five at setup. Distances between tiles are
    the whole tactical difference between them.

Both mirrors are guarded by `tests/test_sim.py`, which parses `lua/setup.lua`
for the flag sets and compares the topology tables against `path_layouts.py`
(itself already mirrored against the Lua adjacency by
`tests/test_regression_guards.py`).

Movement rules encoded here (design §11.1, §11.3):
  * a Move action is one tile and costs 1 Hunger (Rayman's Speed covers two
    tiles per action, still paying Hunger per tile),
  * the Dusk scramble is **one tile**, whatever the map looks like,
  * `SC_SHORTCUT` adds a James's House <-> Badminton Court edge that costs
    0 Hunger to walk (`doMove` in `lua/actions.lua`, `adjacentLocations` in
    `lua/helpers.lua`).
"""

from collections import deque
from functools import lru_cache

from path_layouts import LOCATIONS, PATH_LAYOUTS

# The map graph, keyed by variant name. path_layouts.py is the single source
# of truth shared with the board art and the Lua Move adjacency.
TOPOLOGIES = {name: tuple(edges) for name, edges in PATH_LAYOUTS.items()}

# The sim's historic hop model — "1 action to the centre, 2 to anywhere else"
# — is exactly Star's distance table, so Star is the default and every
# baseline in docs/agents/balance-simulation.md is a Star number. The shipped
# board defaults to Ring and setup draws uniformly from all five.
DEFAULT_TOPOLOGY = "Star"

# SC_SHORTCUT's extra road, stored endpoint-sorted like every other edge.
SHORTCUT_EDGE = tuple(sorted(("JamesHouse", "BadmintonCourt")))


# ---------------------------------------------------------------------------
# Scenarios — mirrors SCENARIOS in lua/setup.lua
# ---------------------------------------------------------------------------
#
# `flags` is the exact `gameState.scenarioFlags` table the Lua onApply sets.
# `sim` is what THIS model does with them; a clause listed as "-" is one the
# sim cannot reach (it abstracts the Market and the item deck away), and the
# probe doc says so rather than pretending otherwise.
SCENARIOS = {
    "none": dict(
        name="No Scenario",
        flags=frozenset(),
        sim="control group — the state the sim measured before this existed, "
            "and one no real table ever plays",
    ),
    "SC_WINTER": dict(
        name="The Long Winter",
        flags=frozenset({"hungerDecayX2", "foodGatherPenalty", "housesSanityBonus"}),
        sim="Tick Hunger loss doubled; a Gather draw that comes up Provisions "
            "comes up empty; +1 Sanity for anyone sleeping in a house",
    ),
    "SC_SUMMER": dict(
        name="The Scorching Summer",
        flags=frozenset({"energyDrinkBonus", "courtGatherBonus"}),
        # The -2 max Hunger is inline in onApply rather than a flag, so the
        # sim keys it off the scenario id (see Game.__init__).
        sim="every character starts at -2 max Hunger; Energy Drinks give +3 "
            "Sanity instead of +2; a Gather at a sport court draws twice",
    ),
    "SC_AUTUMN": dict(
        name="The Rotting Autumn",
        flags=frozenset({"foodSpoilsAtDawn", "recipeBonus", "clothBonus"}),
        sim="1 Provisions spoils per occupied tile at Dawn; cooking restores "
            "+1 Hunger; Cloth is a second entry in every draw table",
    ),
    "SC_SPRING": dict(
        name="The False Spring",
        flags=frozenset({"falseSpring"}),
        sim="no Charlie check on Days 1-3; from Day 4 Charlie checks "
            "EVERY tile, houses included",
    ),
    "SC_BLACKOUT": dict(
        name="Total Blackout",
        flags=frozenset({"noBatteries", "onlyFireLight"}),
        sim="Batteries never come out of the ground and James's starting "
            "Flashlight is dead; the light craft becomes the Lantern "
            "(2 Metal + 1 Wood); the only Battery in the world is Coco's "
            "Spare Phone Battery, which arrives Day 2 and is what the "
            "Telltale Heart revive has to be built from",
    ),
    "SC_RATIONING": dict(
        name="Strict Rationing",
        flags=frozenset({"slowMarket", "cheapRecipes"}),
        sim="at most one Market craft every 2 days; a recipe costs 1 fewer "
            "Provisions (never below 1)",
    ),
    "SC_FULL_MOON": dict(
        name="The Full Moon",
        flags=frozenset({"noCharlie", "softToHard"}),
        sim="Charlie never attacks; every Soft draw becomes a fightable "
            "2 HP / 1 Attack threat that festers if ignored",
    ),
    "SC_SHORTCUT": dict(
        name="The Shortcut",
        flags=frozenset({"shortcutPath", "shortcutThreatBonus"}),
        sim="an extra James's House <-> Badminton Court road that costs 0 "
            "Hunger to walk; +1 threat draw at both ends every night",
    ),
}

SCENARIO_IDS = list(SCENARIOS)


# ---------------------------------------------------------------------------
# Map geometry
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def adjacency(topology, shortcut=False):
    """{location: (neighbour, ...)} for a variant, plus SC_SHORTCUT's road."""
    edges = list(TOPOLOGIES[topology])
    if shortcut and SHORTCUT_EDGE not in edges:
        edges.append(SHORTCUT_EDGE)
    out = {loc: [] for loc in LOCATIONS}
    for a, b in edges:
        out[a].append(b)
        out[b].append(a)
    return {k: tuple(sorted(v)) for k, v in out.items()}


@lru_cache(maxsize=None)
def _paths_from(topology, shortcut, src):
    """BFS tree from one tile: {dst: (src, ..., dst)}, fewest tiles walked."""
    adj = adjacency(topology, shortcut)
    paths = {src: (src,)}
    q = deque([src])
    while q:
        here = q.popleft()
        for nxt in adj[here]:
            if nxt not in paths:
                paths[nxt] = paths[here] + (nxt,)
                q.append(nxt)
    return paths


def path(topology, shortcut, src, dst):
    """Shortest tile path src -> dst, inclusive of both ends."""
    return _paths_from(topology, shortcut, src).get(dst, (src,))


def distance(topology, shortcut, src, dst):
    """Tiles walked between two locations. Every variant is connected, so
    this is always defined."""
    return len(path(topology, shortcut, src, dst)) - 1


def hunger_cost(topology, shortcut, walked):
    """Hunger for a walked path: 1 per tile, except SC_SHORTCUT's free road."""
    cost = 0
    for a, b in zip(walked, walked[1:]):
        if not (shortcut and tuple(sorted((a, b))) == SHORTCUT_EDGE):
            cost += 1
    return cost


def eccentricity(topology):
    """Longest shortest-path from each tile — how far the map can strand you."""
    return {loc: max(distance(topology, False, loc, other) for other in LOCATIONS)
            for loc in LOCATIONS}
