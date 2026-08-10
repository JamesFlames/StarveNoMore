"""The Week in Review's margin and hook (§16.5).

These two lines are the design's stated success test in miniature: the Closing
Notes say the game works when a group loses on Day 6 and immediately resets,
and this panel is where that happens or doesn't. A margin line that goes
missing on some ending, or a hook that fires the generic fallback when a
specific diagnosis was available, is a silent regression — the panel still
looks complete.
"""
import pytest
from conftest import add_char, lua_to_py, make_env

pytest.importorskip("lupa")


def review_lines(cause, **state):
    env = make_env()
    env.execute("gameState.started = true")
    add_char(env, "White", "Coco")
    add_char(env, "Green", "Rayman")
    env.execute(f'gameState.gameOverCause = "{cause}"')
    # The chronicle is built on first use, never declared in the gameState
    # literal (there would be two copies of its shape otherwise). Production
    # reaches it through ensureChronicle(); so must a test that pokes fields
    # into it before showWeekInReview() runs.
    env.eval("ensureChronicle")()
    for k, v in state.items():
        env.execute(f"{k} = {v}")
    env.eval("showWeekInReview()")
    ui = lua_to_py(env.eval("TTS.ui"))
    return ui["attrs"]["weekReviewBody"]["text"].splitlines()


def _one(lines, prefix):
    hits = [line for line in lines if line.startswith(prefix)]
    assert hits, f"no {prefix!r} line in:\n" + "\n".join(lines)
    return hits[0]


@pytest.mark.parametrize("cause,state", [
    ("victory", {"gameState.doom": "28", "gameState.day": "7"}),
    ("defeat_doom", {"gameState.doom": "30", "gameState.day": "6"}),
    ("defeat_all_down", {"gameState.doom": "18", "gameState.day": "5"}),
    ("defeat_source", {"gameState.doom": "22", "gameState.day": "7",
                       "gameState.bossHP": "{source=2}"}),
])
def test_every_ending_gets_a_margin_and_a_hook(cause, state):
    lines = review_lines(cause, **state)
    _one(lines, "THE MARGIN")
    _one(lines, "NEXT TIME")


def test_the_source_margin_names_the_hp_that_was_left():
    """'The Source had 2 HP left' is the single most rematch-inducing sentence
    the game can print. It must survive."""
    lines = review_lines("defeat_source", **{
        "gameState.doom": "22", "gameState.day": "7",
        "gameState.bossHP": "{source=2}"})
    margin = _one(lines, "THE MARGIN")
    assert "2 HP left" in margin, margin


def test_a_near_miss_win_says_so():
    lines = review_lines("victory", **{"gameState.doom": "28", "gameState.day": "7"})
    assert any("close as it gets" in line for line in lines), (
        "a 2-Doom win is the near-miss the ritual exists for")


def test_a_comfortable_win_does_not_claim_a_near_miss():
    lines = review_lines("victory", **{"gameState.doom": "8", "gameState.day": "7"})
    assert not any("close as it gets" in line for line in lines)
    assert "22 Doom from the end" in _one(lines, "THE MARGIN")


def test_the_hook_diagnoses_the_dark_before_anything_else():
    """Charlie is the most fixable death in the game, so a table that lost
    nights to her should be told that rather than something generic."""
    lines = review_lines("defeat_doom", **{
        "gameState.doom": "30", "gameState.day": "6",
        "gameState.chronicle.maxCharlieStreak": '{value=3,name="Rayman"}'})
    hook = _one(lines, "NEXT TIME")
    assert "dark" in hook and "Rayman" in hook, hook


def test_the_hook_suggests_coco_when_she_is_not_at_the_table():
    lines = review_lines("defeat_doom", **{
        "gameState.doom": "30", "gameState.day": "6",
        "gameState.activeChars": 'gameState.activeChars',   # no-op, keep roster
        "gameState.chronicle.maxCharlieStreak": '{value=2,name="Rayman"}'})
    hook = _one(lines, "NEXT TIME")
    # Coco IS in the default fixture roster, so the advice must be the
    # light-logistics one, not "try Coco".
    assert "Coco" not in hook, (
        "suggested a character who is already at the table: " + hook)


def test_a_comfortable_story_win_is_pointed_up_a_difficulty():
    lines = review_lines("victory", **{
        "gameState.doom": "8", "gameState.day": "7",
        "gameState.difficulty": '"story"'})
    assert "Standard" in _one(lines, "NEXT TIME")


def test_nothing_new_is_tracked_at_the_table():
    """§16.5's standing constraint: the margin and hook must be computed from
    the chronicle the game already keeps. If they needed new state, a fresh
    game with an empty chronicle would blow up rather than degrade."""
    env = make_env()
    env.execute("gameState.started = true")
    add_char(env, "White", "Coco")
    env.execute('gameState.gameOverCause = "victory"')
    env.execute("gameState.chronicle = nil")   # oldest possible save
    env.eval("showWeekInReview()")
    ui = lua_to_py(env.eval("TTS.ui"))
    body = ui["attrs"]["weekReviewBody"]["text"]
    assert "THE MARGIN" in body and "NEXT TIME" in body


class TestVerdict:
    """"It was day 7, but we were on 30 doom. So I don't know?" — the panel
    said THE WEEK THAT TOOK YOU and "the Doom track ran out on Day 7", and a
    player who had just reached the day they were told to survive to could not
    tell which it was. Reaching Day 7 is not the win condition; reaching it
    with Doom short of the limit is."""

    def _verdict(self, env, cause, **state):
        env.execute(f'gameState.gameOverCause = "{cause}"')
        for k, v in state.items():
            env.execute(f"gameState.{k} = {v}")
        return env.globals().verdictLine()

    def test_a_doom_loss_says_lost(self, env):
        line = self._verdict(env, "defeat_doom", day=7, doom=30)
        assert line.startswith("YOU LOST"), line
        assert "Day 7" in line and "30" in line

    def test_a_win_says_won(self, env):
        line = self._verdict(env, "victory", day=7, doom=22)
        assert line.startswith("YOU WON"), line

    def test_every_ending_states_a_verdict(self, env):
        for cause in ("defeat_doom", "defeat_all_down", "defeat_source", "victory"):
            line = self._verdict(env, cause, day=7, doom=12)
            assert line.startswith(("YOU WON", "YOU LOST")), (cause, line)

    def test_the_verdict_is_the_first_thing_in_the_panel(self, env):
        env.execute('gameState.gameOverCause = "defeat_doom"; gameState.day = 7')
        env.globals().showWeekInReview()
        body = env.eval('UI.getAttribute("weekReviewBody", "text")')
        assert body.splitlines()[0].startswith("YOU LOST"), body[:200]
