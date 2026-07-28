"""Off-turn reactions: the Haunted buy-in (§10.1) and Luca's Rally (§6.5).

Both let a player act on somebody else's turn, and both spend the actor's own
resource — so the risk they carry is not "does the effect work" but "can the
wrong player fire it". These tests pin the ownership check, the pricing, the
deterministic row order (rows are clicked by index), and the once-per-round
scoping that stops off-turn Rally becoming +4 actions a day.

Note on the fixtures: Ellie & Luca's House is the map's central node, so it is
adjacent to *every* other tile (§7). Luca can therefore never be out of Rally
range of the centre — which is why the Witness fixture leaves him out of the
game entirely rather than parking him somewhere "far away".
"""
import pytest
from conftest import add_char, broadcasts, lua_to_py, make_env

pytest.importorskip("lupa")


def _multi(env, expr):
    """A Lua call's multiple returns as a Python list."""
    return list(env.eval("{%s}" % expr).values())


@pytest.fixture
def haunt():
    """Coco Haunted at the kitchen, Rayman standing with her. No Luca."""
    env = make_env()
    env.execute('gameState.started = true')
    env.execute('gameState.subPhase = "Day"')
    add_char(env, "White", "Coco", location="EllieLucaHouse", sanity=2)
    add_char(env, "Green", "Rayman", location="EllieLucaHouse")
    env.execute('gameState.activeColor = "White"')
    env.execute('gameState.turnOrder = {"White", "Green"}')
    # BeginDay records the haunting; set it directly so this stays a unit test.
    env.execute('gameState.haunted = { White = { location = "EllieLucaHouse", '
                'witnesses = {} } }')
    return env


@pytest.fixture
def rally():
    """Luca and Rayman together, Rayman active, nobody Haunted."""
    env = make_env()
    env.execute('gameState.started = true')
    env.execute('gameState.subPhase = "Day"')
    add_char(env, "Red", "Luca", location="EllieLucaHouse")
    add_char(env, "Green", "Rayman", location="EllieLucaHouse")
    env.execute('gameState.activeColor = "Green"')
    env.execute('gameState.turnOrder = {"Green", "Red"}')
    env.execute('gameState.haunted = {}')
    return env


# ---------------------------------------------------------------- Witness

def test_ally_at_the_tile_may_witness(haunt):
    assert haunt.eval('(canWitness("Green"))') is True
    before = haunt.eval('gameState.activeChars.Green.sanity')
    assert haunt.eval('doWitness("Green", "White")') is True
    after = haunt.eval('gameState.activeChars.Green.sanity')
    assert after == before - haunt.eval('WITNESS_SANITY_COST'), (
        "witnessing must cost the witness Sanity — that IS the rule")
    assert haunt.eval('gameState.haunted.White.witnesses.Green') is True


def test_witnessing_is_once_per_haunting(haunt):
    haunt.eval('doWitness("Green", "White")')
    ok, why = _multi(haunt, 'canWitness("Green")')
    assert ok is False
    assert "already see" in why


def test_a_character_elsewhere_cannot_witness(haunt):
    """The whole point is that somebody has to BE there."""
    add_char(haunt, "Blue", "James", location="RaymanHouse")
    ok, why = _multi(haunt, 'canWitness("Blue")')
    assert ok is False
    assert "Haunted" in why
    assert haunt.eval('doWitness("Blue", "White")') is False
    assert haunt.eval('gameState.activeChars.Blue.sanity') == 10, "no Sanity spent"


def test_witnessing_never_puts_the_witness_down(haunt):
    """Trading your own collapse for someone else's rescue is not a bargain
    the rule should offer silently."""
    haunt.execute('gameState.activeChars.Green.sanity = 1')
    ok, why = _multi(haunt, 'canWitness("Green")')
    assert ok is False
    assert "Sanity" in why
    assert haunt.eval('gameState.activeChars.Green.down') is False


def test_the_haunted_character_cannot_witness_themselves(haunt):
    assert haunt.eval('(canWitness("White"))') is False


# ------------------------------------------------------- Reactions panel

def test_panel_offers_the_witness_and_names_its_actor(haunt):
    haunt.eval('refreshReactionsPanel()')
    ui = lua_to_py(haunt.eval("TTS.ui"))
    assert ui["visible"].get("reactionsPanel") is True
    label = ui["attrs"]["reactBtn_1"]["text"]
    assert "Rayman" in label and "Coco" in label, (
        f"a shared panel must name whose call each row is; got {label!r}")


def test_only_the_named_actor_can_fire_a_reaction_row(haunt):
    """The ownership check is what makes one shared panel safe for actions
    that spend the actor's own Sanity."""
    add_char(haunt, "Blue", "James", location="RaymanHouse")
    haunt.eval('refreshReactionsPanel()')
    haunt.eval('onReactionClick')({"color": "Blue"}, "1", "reactBtn_1")
    assert haunt.eval('gameState.activeChars.Green.sanity') == 6, (
        "James clicking Rayman's row must not spend Rayman's Sanity")
    assert haunt.eval('gameState.haunted.White.witnesses.Green') is None
    assert any("call, not yours" in b for b in broadcasts(haunt))


def test_the_named_actor_can_fire_their_own_row(haunt):
    haunt.eval('refreshReactionsPanel()')
    haunt.eval('onReactionClick')({"color": "Green"}, "1", "reactBtn_1")
    assert haunt.eval('gameState.haunted.White.witnesses.Green') is True


def test_panel_hides_when_nothing_is_available(haunt):
    haunt.execute('gameState.haunted = {}')
    haunt.eval('refreshReactionsPanel()')
    ui = lua_to_py(haunt.eval("TTS.ui"))
    assert ui["visible"].get("reactionsPanel") is False


def test_reactions_are_day_phase_only(haunt):
    """Offering an off-turn stat spend mid-night invites double resolution."""
    haunt.execute('gameState.subPhase = "Night"')
    haunt.eval('refreshReactionsPanel()')
    ui = lua_to_py(haunt.eval("TTS.ui"))
    assert ui["visible"].get("reactionsPanel") is False


def test_row_order_is_stable_across_refreshes(haunt):
    """Rows are clicked BY INDEX, so an unstable order means a player can
    click 'Rayman: witness' and fire something else. Two Haunted allies at one
    tile is the case that exposes a pairs()-ordered build."""
    add_char(haunt, "Blue", "James", location="EllieLucaHouse", sanity=2)
    haunt.execute('gameState.haunted.Blue = { location = "EllieLucaHouse", '
                  'witnesses = {} }')
    seen = set()
    for _ in range(6):
        haunt.eval('refreshReactionsPanel()')
        ui = lua_to_py(haunt.eval("TTS.ui"))
        seen.add(tuple(ui["attrs"][f"reactBtn_{i}"]["text"] for i in (1, 2, 3)))
    assert len(seen) == 1, f"panel rows reordered between refreshes: {seen}"


# ---------------------------------------------------------------- Rally

def test_rally_is_offered_off_turn_to_the_active_player(rally):
    """Luca beside the active player, on somebody else's turn: the row exists.
    This is the downtime cure — the gift arrives while they can still spend it.
    """
    rally.eval('refreshReactionsPanel()')
    ui = lua_to_py(rally.eval("TTS.ui"))
    assert ui["visible"].get("reactionsPanel") is True
    assert "rally" in ui["attrs"]["reactBtn_1"]["text"].lower()

    rally.eval('onReactionClick')({"color": "Red"}, "1", "reactBtn_1")
    assert rally.eval('gameState.activeChars.Green.actionsLeft') == 4


def test_rally_row_is_absent_on_lucas_own_turn(rally):
    """On his turn the Action Bar's Rally button is the right affordance;
    showing both would read as two different rules."""
    rally.execute('gameState.activeColor = "Red"')
    rally.eval('refreshReactionsPanel()')
    ui = lua_to_py(rally.eval("TTS.ui"))
    assert ui["visible"].get("reactionsPanel") is False


def test_rally_is_once_per_round_not_once_per_turn(rally):
    """A per-turn reset would hand Luca one rally per PLAYER turn once Rally
    became firable off-turn — up to +4 actions a day at five players. It must
    reset only at Dawn."""
    assert rally.eval('doRally("Red", "Green")') is True
    assert rally.eval('gameState.lucaRallyUsed') is True

    # Advancing to another player's turn must NOT refill it.
    rally.eval('advanceToNextPlayer()')
    assert rally.eval('gameState.lucaRallyUsed') is True, (
        "Rally refilled on a turn change — that is the +4-actions-a-day bug")
    ok, why = _multi(rally, 'canRally("Red")')
    assert ok is False
    assert "round" in why
