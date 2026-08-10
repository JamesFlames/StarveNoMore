"""Who may click a MOVE HERE / CRAFT / FIGHT button, and what a dead one says.

From a live solo game: "I am on Rayman and clicking MOVE HERE but nothing
happens." Nothing was broken in the move — the click was being refused, twice
invisibly:

  1. the gate compared the click's seat colour against the acting seat, and in
     hotseat that colour is whatever seat TTS had active, not a statement of
     who meant to click. The setup walkthrough stopped inferring from it after
     three separate bug reports (ui_setup.showCharPickForNextPlayer); the
     target buttons had not.
  2. the refusal went out through TTS's own broadcastToColor, which reaches
     exactly one seat — the one the ENGINE named. In hotseat that is easily a
     seat nobody is looking at, so a refused click and a dead button look
     identical.

Both halves are tested here, plus the third silence: a button whose action has
already ended used to `return` with no trace at all.
"""
import pytest
from conftest import a_neighbour_of, add_char, flush, lua52, lua_to_py

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


def log_lines(env):
    """The mod's own message log — the panel that is on screen for everyone,
    as opposed to broadcastToColor's single-seat whisper."""
    return [e["m"] for e in (lua_to_py(env.eval("gameState.messageLog")) or [])]


def armed_move(env, color="Green", name="Rayman", loc="RaymanHouse", solo=True):
    """A character mid-Move: the destination buttons are up and pendingAction
    is armed, exactly as when the player has clicked Move and is reaching for
    a tile."""
    add_char(env, color, name, location=loc)
    there = a_neighbour_of(env, loc)
    env.execute(
        '__there = TTS.addObject({tags = {"Location:%s"}, position = {40,1,40}})' % there)
    env.execute(f'gameState.started = true; gameState.subPhase = "Day"; '
                f'gameState.activeColor = "{color}"; gameState.solo = {str(solo).lower()}')
    # Armed directly rather than through onActMove: this module is about the
    # target click, and going through the action bar would make every test
    # depend on the action bar's own (separate) seat check.
    env.execute(f'gameState.pendingAction = {{ type = "move", color = "{color}" }}')
    return there


def click_there(env, clicker):
    env.eval("onMoveTargetClick")(env.eval("__there"), clicker, False)
    flush(env)


class TestWhoMayClick:
    def test_a_solo_table_may_click_from_any_seat(self, env):
        """The reported bug. One person runs every seat, so the engine's idea
        of which one clicked carries no information at all."""
        there = armed_move(env)
        click_there(env, "Yellow")          # engine says Yellow; the human is Rayman
        assert env.eval("gameState.activeChars.Green.location") == there, (
            "a solo player could not move the character whose turn it is")

    def test_the_acting_seat_still_works(self, env):
        there = armed_move(env, solo=False)
        click_there(env, "Green")
        assert env.eval("gameState.activeChars.Green.location") == there

    def test_the_host_may_click_for_the_acting_player(self, env):
        """Hotseat without the Solo toggle: one keyboard, several seats. The
        host clause is the same one that makes the setup pick queue work."""
        there = armed_move(env, solo=False)
        click_there(env, "White")           # the stub's host
        assert env.eval("gameState.activeChars.Green.location") == there

    def test_a_stranger_is_still_refused(self, env):
        """The gate has to keep meaning something in a real multiplayer game."""
        armed_move(env, solo=False)
        env.execute('TTS.seated = {"Green", "Yellow"}')   # Yellow is not the host
        click_there(env, "Yellow")
        assert env.eval("gameState.activeChars.Green.location") == "RaymanHouse", (
            "another player at a real table hijacked the mover's destination")

    def test_a_refusal_reaches_the_log_not_just_one_seat(self, env):
        armed_move(env, solo=False)
        env.execute('TTS.seated = {"Green", "Yellow"}')
        click_there(env, "Yellow")
        assert any("Only the moving player" in m for m in log_lines(env)), (
            "the refusal only went to broadcastToColor — in hotseat that is a "
            "seat nobody is watching, which is indistinguishable from a dead "
            "button: " + repr(log_lines(env)))


class TestAButtonWhoseActionHasEnded:
    """Turn over, action cancelled, or the 30s timeout fired. The handler used
    to `return` on this, leaving a live-looking control on the table."""

    def test_it_says_so_instead_of_doing_nothing(self, env):
        armed_move(env)
        env.execute("gameState.pendingAction = nil")
        click_there(env, "Green")
        assert any("already finished" in m for m in log_lines(env)), log_lines(env)

    def test_it_takes_the_dead_buttons_away(self, env):
        armed_move(env)
        env.execute("gameState.pendingAction = nil")
        env.execute('__there.createButton({ label = "MOVE HERE", click_function = "x" })')
        click_there(env, "Green")
        assert len(lua_to_py(env.eval("__there.getButtons()")) or []) == 0, (
            "the stale buttons stayed on the tile, so the next click is just "
            "as dead as the last one")

    def test_it_does_not_move_anybody(self, env):
        armed_move(env)
        env.execute("gameState.pendingAction = nil")
        click_there(env, "Green")
        assert env.eval("gameState.activeChars.Green.location") == "RaymanHouse"
