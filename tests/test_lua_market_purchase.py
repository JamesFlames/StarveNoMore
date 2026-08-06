"""Buying a card from the Market, end to end.

This path had NO coverage at all, and the reason is worth recording: the TTS
stub was missing `getGUID()`, and its permissive __index fallback turned the
call into a no-op returning nil instead of an error. `_craftSlotByGuid[
card.getGUID()] = slot` then threw "table index is nil" inside the caller's
bare pcall — so under test the scan silently found nothing, and in game the
player was told "No cards in the Market display" while looking at five cards.

Per docs/tts-interface.md: a stub gap that hides a feature is the finding.
"""
import pytest
from conftest import (
    add_char,
    broadcasts,
    flush,
    lua52,
    make_env,
    populate_full_world,
    py_to_lua,
)

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")

# Slot geometry copied from a real table (scripts/build_save.py places the five
# slots in a column; a dealt card settles ~0.11u above its slot).
SLOT_X, SLOT_Y, CARD_Y = -13.45, 1.60, 1.71
SLOT_Z = [8.8, 4.4, 0.0, -4.4, -8.8]


@pytest.fixture
def env():
    rt = make_env()
    populate_full_world(rt)
    rt.execute('gameState.started = true; gameState.subPhase = "Day"; '
               'gameState.activeColor = "White"')
    add_char(rt, "White", "James", location="JamesHouse")
    # Put the slots where the real board puts them.
    rt.execute(
        "for i = 0, 4 do local s = findOneByTag('MarketSlot:' .. i)\n"
        "  if s then s.setPosition({x = %s, y = %s, z = %s - i * 4.4}) end end"
        % (SLOT_X, SLOT_Y, SLOT_Z[0]))
    return rt


def deal(rt, cards):
    """Deal market cards onto slots 1..n, the way dealMarketDisplay does."""
    add = rt.eval("TTS.addObject")
    for i, card_id in enumerate(cards):
        add(py_to_lua(rt, {
            "tags": [card_id, "MarketCard"],
            "nickname": card_id,
            "position": [SLOT_X, CARD_Y, SLOT_Z[i]],
        }))


def give(rt, color, **res):
    rt.execute("gameState.resources = gameState.resources or {}")
    rt.execute(f'gameState.resources["{color}"] = {{}}')
    for r, q in res.items():
        rt.execute(f'gameState.resources["{color}"]["{r}"] = {q}')


def craft_buttons(rt):
    """Every CRAFT button currently on a market card, as {nickname: label}."""
    out = {}
    world = rt.eval("TTS.world")
    for obj in dict(world).values():
        btns = obj.getButtons()
        if not btns:
            continue
        for b in dict(btns).values():
            if b["label"] == "CRAFT":
                out[obj.getNickname()] = b["click_function"]
    return out


def test_craft_offers_a_button_on_every_dealt_card(env):
    deal(env, ["M_BANDAGE", "M_SHARPENED_SPOON", "M_FIRST_AID"])
    assert env.globals()._spawnCraftButtons() == 3
    assert set(craft_buttons(env)) == {"M_BANDAGE", "M_SHARPENED_SPOON", "M_FIRST_AID"}


def test_the_action_reports_the_real_reason_when_it_cannot(env):
    """"No cards in the Market display" was printed for every failure mode,
    including the ones where the display was full."""
    env.globals().onActCraft(py_to_lua(env, {"color": "White"}), None, "actCraft")
    said = " ".join(broadcasts(env))
    assert "no Market cards are dealt" in said, said

    # ...and a card that has wandered off its slot says THAT instead.
    env.execute("TTS.broadcasts = {}")
    add = env.eval("TTS.addObject")
    add(py_to_lua(env, {"tags": ["M_BANDAGE", "MarketCard"], "nickname": "M_BANDAGE",
                        "position": [40, 1, 40]}))
    env.globals().onActCraft(py_to_lua(env, {"color": "White"}), None, "actCraft")
    said = " ".join(broadcasts(env))
    assert "none is near a Market slot" in said, said


def test_buying_a_card_pays_for_it_and_takes_the_action(env):
    deal(env, ["M_BANDAGE"])            # 1 Cloth
    give(env, "White", Cloth=2, Wood=1)
    env.globals()._spawnCraftButtons()

    env.globals().doCraft("White", 1)
    flush(env)

    assert env.eval('gameState.resources.White.Cloth') == 1, "the Cloth was not paid"
    assert env.eval('gameState.activeChars.White.actionsLeft') == 2, "no action was spent"
    assert "Bandage" in " ".join(broadcasts(env)) or "M_BANDAGE" in " ".join(broadcasts(env))


def test_a_purchase_you_cannot_afford_costs_nothing(env):
    deal(env, ["M_FIRST_AID"])          # 1 Cloth + 1 Metal
    give(env, "White", Cloth=1)         # no Metal
    env.globals().doCraft("White", 1)
    flush(env)

    assert env.eval('gameState.resources.White.Cloth') == 1, "resources were taken anyway"
    assert env.eval('gameState.activeChars.White.actionsLeft') == 3, (
        "the refused purchase kept the action")


def test_an_empty_slot_refunds_the_action(env):
    """doCraft spends the action before it looks for the card, so every early
    return has to hand it back — this one did not, and a click on a slot whose
    card had drifted just ate an action."""
    give(env, "White", Cloth=9)
    env.globals().doCraft("White", 2)   # nothing dealt anywhere
    assert env.eval('gameState.activeChars.White.actionsLeft') == 3


def test_the_click_handler_routes_to_the_right_slot(env):
    """The CRAFT button carries the card, and _craftSlotByGuid carries which
    slot that card is on. Buying the third card must not buy the first."""
    deal(env, ["M_BANDAGE", "M_SHARPENED_SPOON", "M_FIRST_AID"])
    give(env, "White", Cloth=1, Metal=1)
    env.globals()._spawnCraftButtons()

    card = env.eval("findAllByTag('MarketCard')")
    third = [o for o in dict(card).values() if o.getNickname() == "M_FIRST_AID"][0]
    env.globals().gameState.pendingAction = py_to_lua(env, {"type": "craft", "color": "White"})
    env.globals().onCraftTargetClick(third, "White", False)
    flush(env)

    said = " ".join(broadcasts(env))
    assert "M_FIRST_AID" in said or "First Aid" in said, said
    assert env.eval('gameState.resources.White.Metal') == 0, "the First Aid Kit was not paid for"


# --------------------------------------------------------- staged reveal

def test_day_one_puts_two_shelves_on_offer(env):
    """Five unknown items, five costs and six resource types is the heaviest
    read on the table, and it lands on the turn with the least context. Day 1
    is a choice between two cards, not five."""
    env.execute("gameState.day = 1")
    assert env.globals().marketOpenSlots() == 2
    before = env.eval("getMarketDeck().getQuantity()")
    env.globals().dealMarketDisplay()
    flush(env)
    assert env.eval("getMarketDeck().getQuantity()") == before - 5, (
        "all five shelves are stocked on Day 1 — only the FACE is staged")
    assert [env.globals().marketSlotIsHidden(i) for i in range(1, 6)] == \
           [False, False, True, True, True]


def test_one_more_shelf_opens_each_day(env):
    opens = []
    for day in range(1, 8):
        env.execute(f"gameState.day = {day}")
        opens.append(env.globals().marketOpenSlots())
    assert opens == [2, 3, 4, 5, 5, 5, 5]


def test_a_hidden_shelf_gets_no_craft_button(env):
    deal(env, ["M_BANDAGE", "M_SHARPENED_SPOON", "M_FIRST_AID", "M_BAT", "M_SLINGSHOT"])
    env.execute("gameState.day = 1; gameState.marketFaceDown = {[3]=true,[4]=true,[5]=true}")
    assert env.globals()._spawnCraftButtons() == 2, (
        "a face-down card must not be offered for sale")
    assert set(craft_buttons(env)) == {"M_BANDAGE", "M_SHARPENED_SPOON"}


def test_buying_a_hidden_shelf_is_refused_for_free(env):
    deal(env, ["M_BANDAGE", "M_SHARPENED_SPOON", "M_FIRST_AID"])
    env.execute("gameState.day = 1; gameState.marketFaceDown = {[3]=true}")
    give(env, "White", Cloth=9, Metal=9)
    env.globals().doCraft("White", 3)
    flush(env)
    assert env.eval('gameState.activeChars.White.actionsLeft') == 3, (
        "a refusal the player had no way to see coming must not cost an action")
    assert env.eval('gameState.resources.White.Metal') == 9, "resources were taken"
    assert "still face down" in " ".join(broadcasts(env))


def test_the_dawn_reveal_opens_exactly_one_more(env):
    deal(env, ["M_BANDAGE", "M_SHARPENED_SPOON", "M_FIRST_AID", "M_BAT", "M_SLINGSHOT"])
    env.execute("gameState.day = 1; gameState.marketFaceDown = {[3]=true,[4]=true,[5]=true}")
    env.execute("gameState.day = 2")
    env.globals().revealMarketSlotsForToday()
    flush(env)
    assert [env.globals().marketSlotIsHidden(i) for i in range(1, 6)] == \
           [False, False, False, True, True]
    assert "on offer" in " ".join(broadcasts(env))


def test_the_reveal_is_idempotent(env):
    """A reloaded save or a skipped Dawn must not leave the Market short: the
    reveal states what today's shelf count IS, rather than stepping a counter."""
    deal(env, ["M_BANDAGE", "M_SHARPENED_SPOON", "M_FIRST_AID", "M_BAT", "M_SLINGSHOT"])
    env.execute("gameState.day = 1; gameState.marketFaceDown = {[3]=true,[4]=true,[5]=true}")
    env.execute("gameState.day = 4")
    for _ in range(3):
        env.globals().revealMarketSlotsForToday()
        flush(env)
    assert not any(env.globals().marketSlotIsHidden(i) for i in range(1, 6))
