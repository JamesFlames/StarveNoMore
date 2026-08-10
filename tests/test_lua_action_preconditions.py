"""Action buttons must not offer what the click will refuse.

ui_actionbar_display.lua states the rule itself — "Unavailable actions are
HIDDEN, not dimmed: a bar of grey buttons made players wonder which ones they
could click" — and then two buttons opted out of it with "the resource check
is manual". A player with none of the four Cleanse ingredients got a live
Cleanse button, spent an action on it, and had the action handed back with a
refusal; from their seat that reads as the game changing its mind, or as
having successfully cleansed. Trade did the same with nobody in reach.
"""
import os
import re

import pytest
from conftest import (
    XML_DIR,
    add_char,
    broadcasts,
    lua52,
    make_env,
    populate_full_world,
    py_to_lua,
    read_text,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


@pytest.fixture
def env():
    rt = make_env()
    populate_full_world(rt)
    rt.execute('gameState.started = true; gameState.subPhase = "Day"; '
               'gameState.activeColor = "White"')
    return rt


def give(rt, color, **res):
    rt.execute("gameState.resources = gameState.resources or {}")
    rt.execute(f'gameState.resources["{color}"] = {{}}')
    for r, q in res.items():
        rt.execute(f'gameState.resources["{color}"]["{r}"] = {q}')


def can(rt, fn, color="White"):
    rt.execute(f"OK, WHY = {fn}('{color}')")
    return bool(rt.eval("OK")), rt.eval("WHY")


# ----------------------------------------------------------------- Cleanse

def test_cleanse_is_refused_without_the_ingredients(env):
    add_char(env, "White", "James")
    give(env, "White", Cloth=1, EnergyDrink=7)     # missing Wood and Battery
    ok, why = can(env, "canCleanse")
    assert not ok
    assert "Wood" in why and "Battery" in why, (
        f"the tooltip has to name what is missing; got {why!r}")


def test_cleanse_is_offered_with_the_full_bundle(env):
    add_char(env, "White", "James")
    give(env, "White", Wood=1, Cloth=1, Battery=1, EnergyDrink=1)
    assert can(env, "canCleanse")[0] is True


def test_cleanse_needs_an_action_too(env):
    add_char(env, "White", "James", actionsLeft=0)
    give(env, "White", Wood=1, Cloth=1, Battery=1, EnergyDrink=1)
    ok, why = can(env, "canCleanse")
    assert not ok and "actions" in why.lower()


def test_a_refused_cleanse_still_costs_nothing(env):
    """The precondition is the fix, but doCleanse remains the backstop —
    nothing may be spent by a Cleanse that cannot be paid for."""
    add_char(env, "White", "James")
    give(env, "White", Cloth=1)
    env.execute('gameState.doom = 6')
    env.globals().doCleanse("White")
    assert env.eval("gameState.doom") == 6, "Doom moved for an unpaid Cleanse"
    assert env.eval('gameState.activeChars.White.actionsLeft') == 3, (
        "the action was not refunded")


# ------------------------------------------------------------------- Trade

def test_trade_is_refused_when_every_ally_is_down(env):
    add_char(env, "White", "James")
    add_char(env, "Red", "Coco", down=True)
    ok, why = can(env, "canTrade")
    assert not ok and "Down" in why


def test_trade_is_refused_when_the_only_ally_is_away_and_actions_are_gone(env):
    add_char(env, "White", "James", location="JamesHouse", actionsLeft=0)
    add_char(env, "Red", "Coco", location="RaymanHouse")
    ok, why = can(env, "canTrade")
    assert not ok and "1 action" in why


def test_trade_at_your_own_tile_survives_zero_actions(env):
    """It is a free action once per turn, so 0 actions must not hide it."""
    add_char(env, "White", "James", location="JamesHouse", actionsLeft=0)
    add_char(env, "Red", "Coco", location="JamesHouse")
    assert can(env, "canTrade")[0] is True


def test_the_dialog_and_the_button_ask_the_same_question(env):
    """tradeOffersFor feeds both, so they cannot drift apart again."""
    add_char(env, "White", "James", location="JamesHouse", actionsLeft=0)
    add_char(env, "Red", "Coco", location="RaymanHouse")
    add_char(env, "Green", "Rayman", location="JamesHouse")
    env.execute("OFFERS, UNAFF = tradeOffersFor('White')")
    offers = dict(env.eval("OFFERS"))
    assert [o["color"] for o in offers.values()] == ["Green"], (
        "only the same-tile ally is affordable with 0 actions")
    assert env.eval("UNAFF") == 1
    assert can(env, "canTrade")[0] is True


# -------------------------------------------------------------------- Cook

def test_the_cook_list_hides_a_once_per_game_recipe_already_eaten(env):
    add_char(env, "White", "Ellie", location="EllieLucaHouse")
    give(env, "White", Cloth=9, Provisions=9, Wood=9, EnergyDrink=9, Battery=9, Metal=9)
    env.globals()._showCookDialog("White")
    before = set(dict(env.eval("_cookDialogIds")).values())
    assert "R_GRANDMAS_RECIPE" in before

    env.execute('gameState.usedRecipes = { R_GRANDMAS_RECIPE = true }')
    env.globals()._showCookDialog("White")
    after = set(dict(env.eval("_cookDialogIds")).values())
    assert "R_GRANDMAS_RECIPE" not in after, (
        "the dialog still offered a recipe doCook will refuse on the click")


def test_the_cook_list_hides_a_crockpot_recipe_away_from_the_pot(env):
    add_char(env, "White", "James", location="JamesHouse")
    give(env, "White", Cloth=9, Provisions=9, Wood=9)
    env.globals()._showCookDialog("White")
    assert "R_GUMBO" not in set(dict(env.eval("_cookDialogIds")).values())


def test_an_empty_cook_list_names_the_missing_resource(env):
    """"Nothing you can cook" is true and useless. Every recipe takes
    Provisions, so that is almost always the real answer."""
    add_char(env, "White", "James", location="EllieLucaHouse")
    give(env, "White", Wood=9, Cloth=9)     # no Provisions at all
    assert env.globals()._showCookDialog("White") == 0
    msg = env.globals().cookShortfallMessage()
    assert "Provisions" in msg, f"got {msg!r}"


def test_the_cook_hint_says_the_meal_is_eaten_now(env):
    add_char(env, "White", "James", location="EllieLucaHouse")
    give(env, "White", Provisions=9, Wood=9, Cloth=9)
    env.globals()._showCookDialog("White")
    hint = env.eval('(function() return UI.getAttribute("cookDialogHint", "text") end)()')
    assert "eaten immediately" in hint, (
        f"cooking is not crafting and the dialog has to say so; got {hint!r}")


# ------------------------------------------------- confirm at the button

def _label(rt, button):
    return rt.eval(f'(function() return UI.getAttribute("{button}", "text") end)()')


def test_the_raising_button_offers_the_confirm(env):
    """The confirm dialog opens at the CENTRE of the screen and the button
    that raised it is at the bottom — so answering your own click meant a full
    traverse of the screen and back. Gather at James's House offers the Stash
    every single time, so it is the worst case."""
    add_char(env, "White", "James", location="JamesHouse")
    before = _label(env, "actGather")
    env.globals().onActGather(env.eval('Player["White"]'), None, "actGather")

    assert env.eval('TTS.ui.visible.confirmDialog') is True, "no confirm was raised"
    # It wears the dialog's own Yes label where there is one — on the Stash
    # that is "Take the Stash", which says what the click does.
    assert _label(env, "actGather") == env.eval("CONFIRM_MIRROR_PREFIX") + "Take the Stash", (
        f'the button that asked did not offer the answer: {_label(env, "actGather")!r}')
    assert _label(env, "actGather") != before


def test_clicking_it_again_confirms(env):
    add_char(env, "White", "James", location="JamesHouse")
    env.globals().onActGather(env.eval('Player["White"]'), None, "actGather")
    env.globals().onActGather(env.eval('Player["White"]'), None, "actGather")

    assert env.eval('TTS.ui.visible.confirmDialog') is False, "the confirm is still open"
    # The Stash pays 2 Energy Drinks.
    assert env.eval('gameState.resources.White.EnergyDrink') == 2, (
        "the second click did not take the Confirm branch")


def test_the_button_goes_back_to_normal_after_cancel(env):
    add_char(env, "White", "James", location="JamesHouse")
    before = _label(env, "actGather")
    env.globals().onActGather(env.eval('Player["White"]'), None, "actGather")
    env.globals().onConfirmNo(env.eval('Player["White"]'), None, "confirmNo")
    assert _label(env, "actGather") == before, "the CONFIRM label was left on the button"


def test_a_refresh_does_not_paint_over_the_confirm(env):
    """The handlers call refreshPhaseBanner on their way out, so a repaint
    lands between the click and the answer."""
    add_char(env, "White", "James", location="JamesHouse")
    env.globals().onActGather(env.eval('Player["White"]'), None, "actGather")
    mirrored = _label(env, "actGather")
    env.globals().refreshActionButtonStates("White")
    assert _label(env, "actGather") == mirrored, (
        "a banner refresh put the action's own label back over the CONFIRM")


def test_only_the_raising_button_is_a_confirm(env):
    """Every other action must still do its own job while a confirm is open."""
    add_char(env, "White", "James", location="JamesHouse")
    env.globals().onActGather(env.eval('Player["White"]'), None, "actGather")
    assert not _label(env, "actCleanse").startswith(env.eval("CONFIRM_MIRROR_PREFIX"))
    assert env.eval("pendingConfirmButton") == "actGather"


def test_a_cancel_that_does_something_says_what(env):
    """"Cancel" on the Stash offer is not "never mind" — it takes the ordinary
    random resource, and nothing on the button said so."""
    add_char(env, "White", "James", location="JamesHouse")
    env.globals().onActGather(env.eval('Player["White"]'), None, "actGather")
    assert _label(env, "confirmNo") == "Gather Random", _label(env, "confirmNo")
    assert _label(env, "confirmYes") == "Take the Stash"


def _style(rt, button):
    return (rt.eval(f'(function() return UI.getAttribute("{button}", "textColor") end)()'),
            rt.eval(f'(function() return UI.getAttribute("{button}", "color") end)()'))


# Every button that means "yes, do it". A second green that is merely close to
# the dialog's does not read as the same control: the mirrored confirm wore its
# own #AEFFAE and "Take the Stash" looked disabled — a pale mint label on a dark
# plate, in a bar of bright sage buttons — while it was the live answer.
YES_BUTTONS = {
    "dialogs.xml": ["confirmYes", "duskReadyBtn"],
    "msglog.xml":  ["whatNowClose"],
}


def test_confirm_green_is_one_colour(env):
    """The yes-green is defined once (BTN_YES_TEXT/BTN_YES_PLATE, helpers.lua)
    and every affirmative button wears it — the XML defaults included, because
    that is what shows before Lua ever repaints the button."""
    text, plate = env.eval("BTN_YES_TEXT"), env.eval("BTN_YES_PLATE")

    for filename, ids in YES_BUTTONS.items():
        xml = read_text(os.path.join(XML_DIR, filename))
        for button_id in ids:
            m = re.search(r'<Button\b[^>]*\bid="%s"[^>]*>' % button_id, xml, re.S)
            assert m, f"{button_id} vanished from xml/{filename}"
            got = re.search(r'textColor="([^"]+)"', m.group(0))
            assert got and got.group(1) == text, (
                f"{button_id} in xml/{filename} is {got and got.group(1)}, not the "
                f"yes-green {text} — a near-miss reads as a disabled button")

    # ...and the confirm mirrored onto the button that raised it (ui_controls.lua)
    add_char(env, "White", "James", location="JamesHouse")
    env.globals().onActGather(env.eval('Player["White"]'), None, "actGather")
    assert _style(env, "actGather") == (text, plate), (
        f"the mirrored confirm wears {_style(env, 'actGather')}, not the dialog's "
        f"own Yes colours {(text, plate)}")
    assert _style(env, "confirmYes") == (text, plate)


def test_an_ordinary_confirm_still_says_confirm_and_cancel(env):
    """...and a dialog whose Cancel really is "never mind" is left alone."""
    add_char(env, "White", "James")
    give(env, "White", Wood=1, Cloth=1, Battery=1, EnergyDrink=1)
    env.globals().onActCleanse(env.eval('Player["White"]'), None, "actCleanse")
    assert _label(env, "confirmYes") == "Confirm"
    assert _label(env, "confirmNo") == "Cancel"


# --------------------------------------------- the Telltale Heart's shopping list

def _cook_world(rt, name="Rayman", color="White"):
    add_char(rt, color, name, location="EllieLucaHouse")
    add = rt.eval("TTS.addObject")
    add(py_to_lua(rt, {"tags": ["Location:EllieLucaHouse"], "position": [0, 1, 0]}))
    add(py_to_lua(rt, {"tags": ["Crockpot"], "position": [0, 1, 0]}))
    add(py_to_lua(rt, {"tags": [f"PlayerBoard:{name}"], "position": [20, 1, 20]}))


def test_a_missing_telltale_heart_names_its_ingredients(env):
    """It is the only way a Down character comes back, it is a RECIPE and not a
    Market card, and nothing named its ingredients unless you already had them
    — so a table with someone down went looking for it in the Market, which
    will never stock it."""
    _cook_world(env)
    hint = env.globals().heartHint("White")
    assert hint, "no hint at all when the heart is uncookable"
    for word in ("Cloth", "Battery", "Provisions"):
        assert word in hint, f"{word} missing from: {hint}"
    assert "2 Health" in hint, hint
    assert "not a Market card" in hint, hint


def test_the_hint_says_what_you_are_short_of(env):
    _cook_world(env)
    env.globals().giveResource("White", "Cloth", 1)
    env.globals().giveResource("White", "Provisions", 1)
    hint = env.globals().heartHint("White")
    assert "1 more Battery" in hint, hint


def test_no_hint_once_the_heart_is_on_the_list(env):
    """When it IS offered it speaks for itself; a second copy of the rules
    beside a button that says the same thing is noise."""
    _cook_world(env)
    for res in ("Cloth", "Battery", "Provisions"):
        env.globals().giveResource("White", res, 2)
    env.globals()._showCookDialog("White")
    assert env.globals().heartHint("White") is None, env.globals().heartHint("White")


def test_the_nothing_cookable_message_carries_it_too(env):
    """The player standing at the pot with nothing cookable is the likeliest
    person to be hunting for it, and that path never opens the dialog."""
    _cook_world(env)
    env.globals().onActCook(py_to_lua(env, {"color": "White"}), None, "actCook")
    said = " ".join(broadcasts(env))
    assert "TELLTALE HEART" in said, said
