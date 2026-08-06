"""Secret Dusk commitment (§11.3 variant) and Solo mode (§20.3).

Both are off-by-default setup toggles, and both are A/B experiments rather than
settled rules — Secret Dusk in particular cuts against §11.3's explicit intent
(the public declaration is celebrated there), so it has to earn the default
from table data.

The property that makes Secret Dusk worth anything is *simultaneity*: the alpha
player can still argue, but can no longer confirm compliance. If a committed
move landed as it was clicked, the last player to commit would see everyone
else's board and the variant would be theatre. That is what these tests pin.
"""
import pytest
from conftest import add_char, broadcasts, lua_to_py, make_env, neighbours

pytest.importorskip("lupa")


def public(env):
    """Only what the whole table sees. The stub records printToColor in the
    same list as broadcastToAll, and the distinction is the entire point of
    this variant, so it has to be made explicitly."""
    return " ".join(b["message"] for b in lua_to_py(env.eval("TTS.broadcasts"))
                    if not b.get("target"))


def private(env, color):
    return " ".join(b["message"] for b in lua_to_py(env.eval("TTS.broadcasts"))
                    if b.get("target") == color)


@pytest.fixture
def dusk():
    env = make_env()
    env.execute("gameState.started = true")
    env.execute('gameState.subPhase = "Dusk"')
    env.execute("gameState.duskSecret = true")
    env.execute("gameState.duskMoves = {}; gameState.duskPending = {}")
    add_char(env, "White", "Coco", location="EllieLucaHouse")
    add_char(env, "Green", "Rayman", location="EllieLucaHouse")
    return env


def loc(env, color):
    return env.eval(f"gameState.activeChars.{color}.location")


def hunger(env, color):
    return env.eval(f"gameState.activeChars.{color}.hunger")


# ------------------------------------------------------------ commitment

def test_a_committed_move_does_not_happen_yet(dusk):
    dusk.eval("doDuskMove")("White", "BadmintonCourt")
    assert loc(dusk, "White") == "EllieLucaHouse", (
        "the move landed immediately — the variant is theatre")
    assert dusk.eval("gameState.duskPending.White") == "BadmintonCourt"


def test_the_commitment_is_not_announced(dusk):
    dusk.eval("doDuskMove")("White", "BadmintonCourt")
    assert "BadmintonCourt" not in public(dusk), (
        f"the destination leaked to the table: {public(dusk)}")
    assert "committed" in public(dusk).lower(), (
        "the table must still learn THAT a choice was made — only where is secret")
    assert "BadmintonCourt" in private(dusk, "White"), (
        "the committer must be told what they committed to")


def test_hunger_is_charged_on_reveal_not_on_commit(dusk):
    before = hunger(dusk, "White")
    dusk.eval("doDuskMove")("White", "BadmintonCourt")
    assert hunger(dusk, "White") == before, "charged before the move happened"
    dusk.eval("revealDuskCommitments()")
    assert hunger(dusk, "White") == before - 1


def test_still_only_one_scramble_each(dusk):
    dusk.eval("doDuskMove")("White", "BadmintonCourt")
    dusk.eval("doDuskMove")("White", "JamesHouse")
    assert dusk.eval("gameState.duskPending.White") == "BadmintonCourt", (
        "a second commitment overwrote the first — one scramble per character")


def test_adjacency_is_still_enforced_before_banking(dusk):
    # Ask the layout what is out of reach instead of naming a tile: this said
    # "RaymanHouse", which became adjacent to nothing in particular the day
    # Ring stopped being a wheel.
    dusk.execute('gameState.activeChars.White.location = "JamesHouse"')
    far = next(t for t in ("RaymanHouse", "BadmintonCourt", "BasketballCourt",
                           "EllieLucaHouse")
               if t not in neighbours(dusk, "JamesHouse"))
    dusk.eval("doDuskMove")("White", far)
    assert dusk.eval("gameState.duskPending.White") is None


# ---------------------------------------------------------------- reveal

def test_reveal_applies_every_commitment_at_once(dusk):
    # Two different adjacent tiles, whichever ones this layout provides.
    near = neighbours(dusk, "EllieLucaHouse")
    assert len(near) >= 2, "this test needs a hub with two exits"
    dusk.eval("doDuskMove")("White", near[0])
    dusk.eval("doDuskMove")("Green", near[1])
    dusk.eval("revealDuskCommitments()")
    assert loc(dusk, "White") == near[0]
    assert loc(dusk, "Green") == near[1]
    assert not dict(dusk.eval("gameState.duskPending") or {}), "pending not cleared"


def test_reveal_names_who_ended_up_alone(dusk):
    """'I thought you were coming with me' is the beat the variant exists to
    generate — it must be said out loud, not discovered at Tick."""
    dusk.eval("doDuskMove")("White", "BadmintonCourt")
    dusk.eval("revealDuskCommitments()")
    said = " ".join(broadcasts(dusk))
    assert "Coco is alone" in said, said
    assert "Rayman is alone" in said, "Rayman was left behind and nobody said so"


def test_reveal_is_idempotent(dusk):
    """beginNight calls it; a manual host Resolve Night must not move anyone
    twice or double-charge Hunger."""
    dusk.eval("doDuskMove")("White", "BadmintonCourt")
    dusk.eval("revealDuskCommitments()")
    h = hunger(dusk, "White")
    dusk.eval("revealDuskCommitments()")
    assert hunger(dusk, "White") == h
    assert loc(dusk, "White") == "BadmintonCourt"


def test_nobody_moving_is_a_valid_outcome(dusk):
    dusk.eval("revealDuskCommitments()")
    assert any("Nobody moved" in b for b in broadcasts(dusk))


# --------------------------------------------------------- off by default

def test_the_variant_is_off_by_default():
    env = make_env()
    assert env.eval("gameState.duskSecret") in (False, None)
    assert env.eval("gameState.solo") in (False, None)


def test_with_the_variant_off_dusk_is_public_and_immediate():
    env = make_env()
    env.execute("gameState.started = true")
    env.execute('gameState.subPhase = "Dusk"')
    env.execute("gameState.duskMoves = {}")
    add_char(env, "White", "Coco", location="EllieLucaHouse")
    env.eval("doDuskMove")("White", "BadmintonCourt")
    assert env.eval("gameState.activeChars.White.location") == "BadmintonCourt"
    assert any("BadmintonCourt" in b for b in broadcasts(env)), (
        "the standard rule declares out loud — that is §11.3's whole point")


def test_reveal_is_a_no_op_when_the_variant_is_off():
    env = make_env()
    env.execute("gameState.duskSecret = false")
    env.execute('gameState.duskPending = { White = "BadmintonCourt" }')
    add_char(env, "White", "Coco", location="EllieLucaHouse")
    env.eval("revealDuskCommitments()")
    assert env.eval("gameState.activeChars.White.location") == "EllieLucaHouse"


# ------------------------------------------------------------------ solo

def test_both_variants_are_reported_in_the_rules_panel():
    env = make_env()
    env.execute("gameState.started = true")
    env.execute("gameState.duskSecret = true; gameState.solo = true")
    add_char(env, "White", "Coco")
    env.eval("refreshRulesPanel()")
    from conftest import lua_to_py
    body = lua_to_py(env.eval("TTS.ui"))["attrs"]["rulesBody"]["text"]
    assert "Secret Dusk" in body
    assert "SOLO MODE" in body, (
        "a mode whose entire content is 'these rules are suspended' has to say "
        "so somewhere persistent")


def test_both_variants_reach_the_session_log():
    """Without these on the log, an aggregate win rate silently mixes rule
    sets — which is how an A/B stops being an A/B."""
    import json as _json
    env = make_env()
    env.execute("gameState.started = true")
    env.execute("gameState.duskSecret = true; gameState.solo = true")
    add_char(env, "White", "Coco")
    env.eval("recordSetupInChronicle()")
    log = _json.loads(env.globals().exportSessionLog())
    assert log["setup"]["duskSecret"] is True
    assert log["setup"]["solo"] is True
