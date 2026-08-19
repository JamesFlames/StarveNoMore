"""Fight Result popup (combat_resolve.lua / ui_actionbar_handlers.lua).

Playtest: "a pop up should say what the result is of each fight — I didn't
know what had happened afterwards." Combat already narrates every hit,
fumble, defeat and counter through broadcastEvent, but TTS's own broadcast
text fades in a few seconds and the persistent Message Log panel is easy to
not be looking at mid-fight. showFightResultDialog answers this the same way
the end-of-day summaryPanel already does (ui_controls.lua): stop fading,
require a click — built by replaying the fight's own gameState.dayLog lines
rather than writing a second description that could drift from what actually
happened.
"""

import pytest
from conftest import add_char, lua52, py_to_lua, script_dice

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


def visible(env, panel_id):
    return env.eval(f'TTS.ui.visible["{panel_id}"]') is True


def body_text(env):
    return env.eval('UI.getAttribute("fightResultBody", "text")')


class TestFightResultDialog:
    def test_a_defeat_shows_the_result(self, env):
        add_char(env, "White", "James")
        script_dice(env, [6])   # one hit, kills a 1 HP threat
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "T", "hp": 1, "attack": 0}))
        assert visible(env, "fightResultDialog")
        assert "DEFEATED" in body_text(env)

    def test_a_survived_whiff_and_counter_also_shows_the_result(self, env):
        """Not just victories — any way the fight actually concluded."""
        add_char(env, "White", "James")
        script_dice(env, [2, 6])   # whiff, then the counter connects
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "T", "hp": 5, "attack": 1}))
        assert visible(env, "fightResultDialog")
        assert "counter-attack" in body_text(env)

    def test_an_open_press_window_does_not_show_a_result_yet(self, env):
        """The fight is not over — pressing or finishing is still a live
        choice, so there is nothing to report yet."""
        add_char(env, "White", "James")
        script_dice(env, [6])   # a hit, threat survives -> press window opens
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "T", "hp": 5, "attack": 0}))
        assert not visible(env, "fightResultDialog")

    def test_finishing_after_a_press_shows_the_result(self, env):
        add_char(env, "White", "James")
        script_dice(env, [6, 2])   # opens the press window, then the counter roll
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "T", "hp": 5, "attack": 1}))
        assert not visible(env, "fightResultDialog")
        env.globals().finishCombat()
        assert visible(env, "fightResultDialog")
        assert "counter-attacks" in body_text(env)

    def test_the_body_replays_the_fights_own_lines_not_a_rewrite(self, env):
        """Built from gameState.dayLog, not a hand-written summary — so it
        can never say something different from what was actually broadcast."""
        add_char(env, "White", "James")
        script_dice(env, [6])
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "Whisperer", "hp": 1, "attack": 0}))
        body = body_text(env)
        assert "Whisperer" in body
        assert "hit(s)!" in body

    def test_ending_a_turn_mid_press_shows_the_result(self, env):
        """endPlayerTurn force-closes an open press window (turns.lua) — that
        exit must report too, not just the two combat_resolve.lua ones."""
        add_char(env, "White", "James", location="JamesHouse")
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:JamesHouse"], "position": [0, 1, 0]}))
        env.execute('gameState.started = true; gameState.subPhase = "Day"; '
                    'gameState.activeColor = "White"; gameState.turnOrder = {"White"}; '
                    'gameState.turnIndex = 1')
        script_dice(env, [6, 2])
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "T", "hp": 5, "attack": 1}))
        assert not visible(env, "fightResultDialog")
        env.globals().endPlayerTurn("White")
        assert visible(env, "fightResultDialog")

    def test_closing_the_dialog_hides_it(self, env):
        add_char(env, "White", "James")
        script_dice(env, [6])
        env.globals().resolveCombat("White", py_to_lua(env, {"name": "T", "hp": 1, "attack": 0}))
        assert visible(env, "fightResultDialog")
        env.globals().onFightResultClose(py_to_lua(env, {"color": "White"}), None, "fightResultClose")
        assert not visible(env, "fightResultDialog")

    def test_no_log_mark_is_harmless(self, env):
        """A defensive call with nothing to report (no fight actually ran)
        must not throw or pop an empty dialog."""
        env.globals().showFightResultDialog(None)
        assert not visible(env, "fightResultDialog")
