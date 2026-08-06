"""Every authored hint must be reachable, or it is help nobody can get.

`content/help/whatnow_hints.md` is authored prose, generated into
`lua/whatnow_hints.lua`, and shown by the "What next?" panel — the game's whole
answer to a player who does not know what to do next. The dispatch in
`ui_help.lua` picks entries by game state, and **fifteen of the forty-nine
authored hints had no condition that could ever select them**:

    Dawn      ongoing_effect
    Day       all_passed
    Stats     critical_any
    Strategic enemy_at_location, market_good_item, no_light_source
    Dusk      alone_sport_court, coco_alone_warning, no_light_warning
    Night     charlie_incoming, combat_active, sleep_phase, storytelling
    Tick      someone_down
    Ellie     ellie_no_food

Four of those are named in the dispatcher's *own header comment* as hints it
dispatches ("Stats (low_hunger / sanity / health / **critical_any**)",
"Strategic (doom_high / ally_down / **no_light_source** / **market_good_item**
/ **enemy_at_location**)"). The comment described the intended dispatch; the
code below it implemented two of the five.

Two more could not have been reached by any condition, because there was
nothing to test: the Night runs threat draws, storytelling, sleep and the Tick
under the single sub-phase name "Night", so `storytelling` and `sleep_phase`
had no state to key off. `gameState.nightStage` now names the step.

This module fails on an authored hint the dispatch never mentions. Unreachable
help is worse than missing help: it costs authoring, it ships in the bundle,
and it reads as done.
"""
import os
import re

import pytest
from conftest import LUA_DIR, add_char, lua52, py_to_lua, read_text

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


# Hints selected by a computed key rather than a literal, with the source of
# that key. The dispatch does `phaseHints[gameState.gameOverCause]`, and the
# four causes are the four literals endGame() passes.
DYNAMIC = {
    "victory": "endGame('victory')",
    "defeat_doom": "endGame('defeat_doom')",
    "defeat_all_down": "endGame('defeat_all_down')",
    "defeat_source": "endGame('defeat_source')",
}


def _authored_keys():
    """{group: {key, ...}} from the generated table."""
    src = read_text(os.path.join(LUA_DIR, "whatnow_hints.lua"))
    out = {}
    for m in re.finditer(r"WHATNOW_HINTS\.(\w+)\s*=\s*\{(.*?)\n\}", src, re.S):
        out[m.group(1)] = set(re.findall(r"^\s*(\w+)\s*=", m.group(2), re.M))
    return out


def test_every_authored_hint_is_reachable():
    dispatch = read_text(os.path.join(LUA_DIR, "ui_help.lua"))
    unreachable = []
    for group, keys in sorted(_authored_keys().items()):
        for key in sorted(keys):
            if key in DYNAMIC:
                continue
            if not re.search(r"\.%s\b" % key, dispatch):
                unreachable.append("%s.%s" % (group, key))

    assert not unreachable, (
        "%d authored hint(s) the What-now dispatch can never select:\n  %s\n\n"
        "Each was written in content/help/whatnow_hints.md, generated into the "
        "bundle, and shipped — with no condition in onWhatNowClick "
        "(lua/ui_help.lua) that reaches it. Give it a condition, or delete the "
        "prose. Unreachable help costs authoring and reads as done."
        % (len(unreachable), "\n  ".join(unreachable))
    )


def test_the_dynamic_allowlist_still_matches_the_game_over_causes():
    """DYNAMIC claims these keys are chosen by `gameState.gameOverCause`.
    If endGame ever passes a cause with no authored hint, the post-game panel
    silently falls back to the generic line."""
    tick = read_text(os.path.join(LUA_DIR, "tick_victory.lua"))
    causes = set(re.findall(r'endGame\("(\w+)"\)', tick))
    authored = _authored_keys().get("PostGame", set())
    assert causes == set(DYNAMIC), (
        f"endGame passes {sorted(causes)}; this module expects {sorted(DYNAMIC)}")
    assert causes <= authored, (
        f"no PostGame hint for {sorted(causes - authored)} — the panel would "
        "fall back to the generic default on that ending")


def test_no_authored_hint_is_orphaned_prose():
    """The other direction: a condition naming a hint the markdown no longer
    has renders nothing, silently."""
    dispatch = read_text(os.path.join(LUA_DIR, "ui_help.lua"))
    authored = set()
    for keys in _authored_keys().values():
        authored |= keys
    # Only the names the dispatch reads off a hints table: the named locals it
    # binds each group to, plus the inline `(WHATNOW_HINTS.X or {}).key` form.
    # A bare `}).key` would also match ordinary code like
    # `(getPlayerResources(color) or {}).Provisions`, so the inline form is anchored
    # on WHATNOW_HINTS.
    named = set(re.findall(
        r"(?:phaseHints|charHints|stats|strat|locHints|duskHints)\.(\w+)", dispatch))
    named |= set(re.findall(r"WHATNOW_HINTS\.\w+\s+or\s+\{\}\)\.(\w+)", dispatch))
    stale = sorted(n for n in named - authored if n not in {"default"})
    assert not stale, (
        f"the dispatch names hint(s) that no longer exist in "
        f"content/help/whatnow_hints.md: {stale}")


# ---------------------------------------------------------------------------
# Behaviour: the newly reachable hints actually come out.
# ---------------------------------------------------------------------------


def _ask(env, color="White"):
    env.eval("onWhatNowClick")(py_to_lua(env, {"color": color}))
    attrs = env.eval("TTS.ui")["attrs"]
    return attrs["whatNowBody"]["text"] if "whatNowBody" in attrs else ""


class TestNewlyReachableHints:
    def test_the_dawn_card_is_named_while_it_is_still_in_force(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.subPhase = "Dawn"')
        env.execute('gameState.activeDawn = {title = "The Power Flickers", '
                    'ongoing = "Flashlights are dead tonight."}')
        text = _ask(env)
        assert "The Power Flickers" in text
        assert "{dawnTitle}" not in text, "the placeholder must be substituted"

    def test_a_dawn_card_with_no_ongoing_clause_says_nothing_extra(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.subPhase = "Dawn"')
        env.execute('gameState.activeDawn = {title = "Quiet Evening", ongoing = ""}')
        assert "still active" not in _ask(env)

    def test_all_passed_replaces_the_end_turn_nudge(self, env):
        add_char(env, "White", "James", actionsLeft=0)
        add_char(env, "Green", "Ellie", actionsLeft=0)
        env.execute('gameState.subPhase = "Day"')
        assert "host should advance to Dusk" in _ask(env)

    def test_one_player_still_holding_actions_is_not_all_passed(self, env):
        add_char(env, "White", "James", actionsLeft=0)
        add_char(env, "Green", "Ellie", actionsLeft=2)
        env.execute('gameState.subPhase = "Day"')
        assert "host should advance to Dusk" not in _ask(env)

    def test_two_low_stats_open_with_recovery_first(self, env):
        add_char(env, "White", "James", hunger=2, sanity=2)
        env.execute('gameState.subPhase = "Day"')
        text = _ask(env)
        assert "Survival comes first" in text
        assert "your Hunger is at 2" in text, "the specific advice still follows"

    def test_one_low_stat_does_not(self, env):
        add_char(env, "White", "James", hunger=2)
        env.execute('gameState.subPhase = "Day"')
        text = _ask(env)
        assert "Survival comes first" not in text
        assert "your Hunger is at 2" in text

    def test_a_threat_at_your_tile_is_pointed_out(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        env.execute('gameState.subPhase = "Day"')
        env.eval("TTS.addObject")(py_to_lua(env, {
            "tags": ["Location:JamesHouse"], "position": [0, 1, 0]}))
        env.execute('TTS.addObject({tags = {"ThreatCard", "T_LURKER"}, type = "Card", '
                    'nickname = "Lurker", position = {1,1,1}})')
        assert "active Threat at JamesHouse" in _ask(env)

    def test_no_light_is_flagged_during_the_day_while_it_can_still_be_fixed(self, env):
        add_char(env, "White", "James", location="JamesHouse")
        env.execute('gameState.subPhase = "Day"')
        assert "you don't have a light source" in _ask(env)

    def test_dusk_warns_about_sleeping_alone_on_a_court(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        env.execute('gameState.subPhase = "Dusk"')
        text = _ask(env)
        assert "sleep alone at a sport court" in text
        assert "no light source" in text

    def test_coco_gets_her_own_dusk_warning(self, env):
        add_char(env, "White", "Coco", location="BasketballCourt")
        env.execute('gameState.subPhase = "Dusk"')
        assert "Coco, if you sleep alone" in _ask(env)

    def test_an_ally_at_the_court_removes_the_alone_warning(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        add_char(env, "Green", "Ellie", location="BasketballCourt")
        env.execute('gameState.subPhase = "Dusk"')
        assert "sleep alone at a sport court" not in _ask(env)

    def test_night_names_the_step_it_is_on(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.subPhase = "Night"')
        env.execute('gameState.nightStage = "storytelling"')
        assert "Storytelling phase" in _ask(env)
        env.execute('gameState.nightStage = "sleep"')
        assert "Sleep is resolving" in _ask(env)
        env.execute("gameState.nightStage = nil")
        assert "Night is resolving" in _ask(env)

    def test_a_live_fight_outranks_the_night_step(self, env):
        add_char(env, "White", "James")
        env.execute('gameState.subPhase = "Night"; gameState.nightStage = "sleep"')
        env.execute('gameState.combatContext = {colors = {"White"}, '
                    'threat = {name = "T"}, threatHP = 2}')
        assert "Combat is active" in _ask(env)

    def test_charlie_is_announced_to_whoever_has_no_light(self, env):
        add_char(env, "White", "James", location="BasketballCourt")
        env.execute('gameState.subPhase = "Night"')
        assert "Charlie attacks" in _ask(env)

    def test_coco_is_not_warned_about_charlie(self, env):
        add_char(env, "White", "Coco", location="BasketballCourt")
        env.execute('gameState.subPhase = "Night"')
        assert "Charlie attacks" not in _ask(env), "Night Vision — she is immune"

    def test_the_tick_reports_a_character_going_down(self, env):
        add_char(env, "White", "James")
        add_char(env, "Green", "Ellie", down=True)
        env.execute('gameState.subPhase = "Tick"')
        assert "went Down during the Tick" in _ask(env)

    def test_ellie_is_told_when_her_larder_is_empty(self, env):
        add_char(env, "White", "Ellie", location="RaymanHouse")
        env.execute('gameState.subPhase = "Day"')
        assert "you have no Provisions" in _ask(env)

    def test_ellie_with_food_is_not(self, env):
        add_char(env, "White", "Ellie", location="RaymanHouse")
        env.execute("gameState.resources = {White = {Provisions = 2}}")
        env.execute('gameState.subPhase = "Day"')
        assert "you have no Provisions" not in _ask(env)
