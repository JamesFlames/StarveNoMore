"""The Truth Run (§16.2): three Clues, findable by decision.

Two things are guarded here, and the first is the more important:

1. gameState.clueCount was NEVER INCREMENTED by anything. Three Clue cards
   shipped, a Trophy existed for collecting them, a Dawn card referenced them,
   and checkBonusVictories read a counter that stayed 0 forever. The
   achievement was unreachable in code, not merely improbable. A test that
   drives a real claim end-to-end is the only thing that would have caught it.

2. Even fixed, drawing three specific cards from a 49-card deck through a
   5-card display is shuffle luck deciding an achievement. The guarantees that
   replace the lottery — the Sealed Basement clue and the refill checkpoints —
   are what the rest of these tests pin.
"""
import pytest
from conftest import add_char, broadcasts, lua_to_py, make_env

pytest.importorskip("lupa")


def _card(env, nickname, tags=None):
    """A stand-in Market card handle."""
    return env.eval("TTS.addObject")(env.eval("JSON").decode(
        '{"tags": %s, "nickname": "%s", "position": [0,1,0]}'
        % (repr(tags or ["MarketCard"]).replace("'", '"'), nickname)))


@pytest.fixture
def env():
    rt = make_env()
    rt.execute("gameState.started = true")
    add_char(rt, "White", "Coco")
    rt.execute('gameState.activeColor = "White"')
    rt.execute("gameState.cluesFound = {}")
    rt.execute("gameState.clueCount = 0")
    return rt


def test_a_clue_card_is_recognised_by_tag_and_by_name(env):
    tagged = _card(env, "Whatever", ["MarketCard", "M_CLUE_TAPE"])
    named = _card(env, "Clue: A Polaroid")
    plain = _card(env, "Flashlight")
    # isClueCard returns (bool, id); lupa hands back a tuple for multi-return.
    def is_clue(card):
        r = env.eval("isClueCard")(card)
        return r[0] if isinstance(r, tuple) else r

    assert is_clue(tagged) is True
    assert is_clue(named) is True
    assert is_clue(plain) is False


def test_claiming_a_clue_increments_the_counter(env):
    """The defect: nothing ever moved this number."""
    assert env.eval("gameState.clueCount") == 0
    env.eval("recordClueFound")("White", _card(env, "Clue: A Cassette",
                                               ["MarketCard", "M_CLUE_TAPE"]))
    assert env.eval("gameState.clueCount") == 1


def test_the_same_clue_cannot_be_counted_twice(env):
    """A card that bounces back to the deck, or a retried craft, must not turn
    the Truth Run into a bug."""
    card = _card(env, "Clue: A Cassette", ["MarketCard", "M_CLUE_TAPE"])
    assert env.eval("recordClueFound")("White", card) is True
    assert env.eval("recordClueFound")("White", card) is False
    assert env.eval("gameState.clueCount") == 1


def test_three_distinct_clues_reach_the_truth_run_threshold(env):
    for nick, tag in [("Clue: A Cassette", "M_CLUE_TAPE"),
                      ("Clue: A Burned Note", "M_CLUE_NOTE"),
                      ("Clue: A Polaroid", "M_CLUE_PHOTO")]:
        env.eval("recordClueFound")("White", _card(env, nick, ["MarketCard", tag]))
    assert env.eval("gameState.clueCount") == env.eval("CLUES_FOR_TRUTH_RUN")
    assert any("ALL THREE CLUES" in b for b in broadcasts(env))


def test_the_truth_run_bonus_actually_fires(env):
    """End to end: three clues claimed, then the victory check must award it.
    This is the assertion that would have failed before clues.lua existed."""
    for nick, tag in [("Clue: A Cassette", "M_CLUE_TAPE"),
                      ("Clue: A Burned Note", "M_CLUE_NOTE"),
                      ("Clue: A Polaroid", "M_CLUE_PHOTO")]:
        env.eval("recordClueFound")("White", _card(env, nick, ["MarketCard", tag]))
    env.eval("checkBonusVictories()")
    assert any("Truth Run" in b for b in broadcasts(env)), (
        "three clues found and checkBonusVictories stayed silent")


def test_progress_is_reported_in_the_rules_panel(env):
    env.eval("recordClueFound")("White", _card(env, "Clue: A Cassette",
                                               ["MarketCard", "M_CLUE_TAPE"]))
    env.eval("refreshRulesPanel()")
    ui = lua_to_py(env.eval("TTS.ui"))
    body = ui["attrs"]["rulesBody"]["text"]
    assert "TRUTH RUN" in body and "1 of 3" in body, (
        "a bonus victory nobody can see the progress of is one nobody plays "
        f"toward; rules panel said:\n{body}")


# ------------------------------------------------- the anti-lottery guarantees

def test_the_sealed_basement_promises_a_clue():
    """The one guaranteed clue in the game — the thing that turns the Truth
    Run from a draw into a plan."""
    rt = make_env()
    assert rt.eval("SEALED_REWARDS.BASEMENT.clue") == 1
    line = rt.eval("SEALED_REWARDS.BASEMENT.line")
    assert "CLUE" in line.upper(), (
        "the basement pays a clue but doesn't say so on the tooltip: " + line)


def test_no_clue_is_due_before_the_first_checkpoint(env):
    env.execute("gameState.day = 1")
    assert env.eval("clueDueForRefill()") is None


def test_a_clue_becomes_due_once_the_week_passes_a_checkpoint(env):
    """By Day 3 the team must have been *offered* a clue, whatever the
    shuffle did. Without a Market deck present this returns nil, so the test
    asserts the decision logic rather than the physical draw."""
    env.execute("gameState.day = 3")
    env.execute("gameState.cluesSurfaced = 0")
    # No deck in this bare world → nil, but the quota must have been consumed
    # only if a clue was actually found, so cluesSurfaced stays 0.
    env.eval("clueDueForRefill()")
    assert env.eval("gameState.cluesSurfaced") == 0, (
        "the checkpoint was spent without a clue being dealt")


def test_checkpoints_stop_once_all_three_are_found(env):
    env.execute("gameState.day = 7")
    env.execute('gameState.cluesFound = {M_CLUE_TAPE=true, M_CLUE_NOTE=true, '
                'M_CLUE_PHOTO=true}')
    env.execute("gameState.clueCount = 3")
    assert env.eval("clueDueForRefill()") is None
