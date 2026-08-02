"""The guided setup walkthrough, walked — including the ugly paths.

Setup produced three separate fix commits ("ghost Step 2 panel stranding the
reseated player", "self-heal the setup pick queue", "setup names players not
seat colours") and ui_setup.lua is the largest hand-written Lua file. Every one
of those bugs was found by a human at a table, because the walkthrough is a
state machine nothing drove end to end.

test_lua_setup.py covers the pieces; test_full_campaign.py runs the happy
two-player path. This module walks the machine for 1-5 players and then does
the things real tables do that the happy path never does:

  * two players click the same character,
  * a player leaves mid-pick,
  * a player changes seat between steps,
  * someone clicks a step that is no longer open,
  * the host clicks through for everyone (the hotseat path).

The invariant behind all of them: the walkthrough must always either finish or
say why — never strand the table on a step nobody can advance.
"""
import pytest

try:
    import lupa.lua52 as lua52
except ImportError:  # pragma: no cover
    lua52 = None

from conftest import flush, lua_to_py, make_env, populate_full_world

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")

# A character's seat colour is fixed (CHARACTER_COLORS, lua/global.lua).
SEAT_FOR = {"James": "Blue", "Coco": "White", "Rayman": "Green",
            "Ellie": "Yellow", "Luca": "Red"}
# Seating each player on their own character's colour means no reseat fires,
# which keeps the walkthrough tests about the STEP MACHINE. The reseat/swap
# path has its own coverage in test_full_campaign.py.
ROSTER = ["Coco", "James", "Rayman", "Ellie", "Luca"]

SETUP_PANELS = ("setupStep1", "setupStepVariants", "setupStep2", "charBriefing")


def begin(env, names):
    """Seat `names` (each on their character's colour) and reach Step 2."""
    populate_full_world(env)
    env.globals().onLoad("")
    flush(env)
    colors = [SEAT_FOR[n] for n in names]
    env.execute("TTS.seated = {%s}" % ", ".join(f'"{c}"' for c in colors))
    host = colors[0]
    env.execute(f'onHostSetupGuided(Player["{host}"])')
    env.execute(f'onPickPath(Player["{host}"], "-1", "pickCompact")')
    env.execute(f'onVariantsContinue(Player["{host}"], "-1", "variantsContinue")')
    flush(env)
    return host


def pick(env, name, as_color=None):
    color = as_color or SEAT_FOR[name]
    env.execute(f'onPickChar(Player["{color}"], "-1", "pick{name}")')
    flush(env)


def dismiss(env, color):
    env.execute(f'onBriefDismiss(Player["{color}"], "-1", "briefDismiss")')
    flush(env)


def visible(env, panel):
    return bool((lua_to_py(env.eval("TTS.ui.visible")) or {}).get(panel))


def roster(env):
    return {c: v["name"] for c, v in (lua_to_py(env.eval("gameState.activeChars")) or {}).items()}


def messages(env):
    return [b["message"] for b in lua_to_py(env.eval("TTS.broadcasts"))]


@pytest.mark.parametrize("count", [1, 2, 3, 4, 5])
def test_walkthrough_completes_for_any_table_size(count):
    names = ROSTER[:count]
    env = make_env()
    begin(env, names)
    for n in names:
        pick(env, n)
        dismiss(env, SEAT_FOR[n])

    assert env.eval("gameState.started") is True, (
        f"{count}-player guided setup never finished — the table is stranded "
        "on a step with nothing left to click")
    assert env.eval("gameState.playerCount") == count
    assert roster(env) == {SEAT_FOR[n]: n for n in names}
    for panel in SETUP_PANELS:
        assert not visible(env, panel), (
            f"{panel} still open after setup finished — this is the ghost-panel "
            "class of bug: a window no code path can close again")


def test_the_same_character_cannot_be_picked_twice():
    """Two players click the same card. The second must be refused, and the
    queue must not lose the refused player's turn."""
    env = make_env()
    begin(env, ["Coco", "James", "Rayman"])
    pick(env, "Coco")
    dismiss(env, "White")

    # Blue tries to take Coco, who is gone.
    env.execute("TTS.broadcasts = {}")
    pick(env, "Coco", as_color="Blue")
    assert any("already taken" in m for m in messages(env)), (
        "a duplicate pick was not refused — two players would share a character")
    assert roster(env) == {}, "a refused pick started the game anyway"

    # Blue is still owed a pick, and the walkthrough still completes.
    pick(env, "James", as_color="Blue")
    dismiss(env, "Blue")
    pick(env, "Rayman")
    dismiss(env, "Green")
    assert env.eval("gameState.started") is True, (
        "a refused duplicate pick consumed the player's turn and stranded setup")
    assert roster(env) == {"White": "Coco", "Blue": "James", "Green": "Rayman"}


def test_a_player_leaving_mid_pick_does_not_strand_the_table():
    """Someone quits between picks. The queue must reconcile against who is
    actually seated, not wait forever on an empty chair."""
    env = make_env()
    begin(env, ["Coco", "James", "Rayman"])
    pick(env, "Coco")
    dismiss(env, "White")

    # Blue rage-quits before picking.
    env.execute('TTS.seated = {"White", "Green"}')
    pick(env, "Rayman")
    dismiss(env, "Green")

    assert env.eval("gameState.started") is True, (
        "setup hung waiting on a player who left — reconcilePendingColors "
        "must drop seats nobody is sitting in")
    assert roster(env) == {"White": "Coco", "Green": "Rayman"}
    assert env.eval("gameState.playerCount") == 2


def test_a_seat_change_between_steps_is_absorbed():
    """A player moves colour mid-walkthrough. Their pick must still register.

    The old code refused a player whose seat the queue had lost track of,
    which was a dead end: nothing they clicked could register and nothing on
    screen said why.
    """
    env = make_env()
    begin(env, ["Coco", "James"])
    # Blue wanders onto an unused seat between steps.
    env.execute('Player["Blue"].changeColor("Yellow")')
    flush(env)

    pick(env, "Coco")
    dismiss(env, "White")
    # The moved player picks from their NEW seat, for a character whose
    # colour is that seat, so no reseat masks the result.
    pick(env, "Ellie", as_color="Yellow")
    dismiss(env, "Yellow")

    assert env.eval("gameState.started") is True, (
        "a player who changed seat mid-walkthrough could not pick — the queue "
        "was still waiting on the seat they left")
    assert roster(env) == {"White": "Coco", "Yellow": "Ellie"}


def test_the_host_can_click_through_for_everyone():
    """The hotseat path: one person at the keyboard, everyone else watching.

    Picking for a seat that is NOT yours now takes two clicks. The queue only
    ever holds seated colours, so the code cannot tell a hotseat from a real
    second player who just hasn't clicked yet — and picking for the latter on
    one click is exactly how a host ended up choosing a character for someone
    who was sitting there with the panel open. First click warns, second click
    commits; the host's own pick is unaffected.
    """
    env = make_env()
    host = begin(env, ["Coco", "James", "Rayman"])
    assert host == "White"

    # The host's own pick: one click, no confirm.
    pick(env, "Coco", as_color=host)
    assert visible(env, "charBriefing")
    dismiss(env, host)

    for name in ("James", "Rayman"):
        pick(env, name, as_color=host)
        assert not visible(env, "charBriefing"), (
            f"picking {name} for another seated player went through on the "
            "first click — that seat's own player never got to choose")
        pick(env, name, as_color=host)          # confirm
        assert visible(env, "charBriefing"), (
            f"no briefing opened after the host confirmed {name} — the hotseat "
            "driver would silently stall on the next click")
        dismiss(env, host)

    assert env.eval("gameState.started") is True, (
        "the hotseat path did not finish — one person cannot set up the table")
    assert sorted(roster(env).values()) == ["Coco", "James", "Rayman"]


def test_a_second_player_keeps_their_own_pick():
    """The bug this all came from: the host picks his own character, clicks a
    second card, and the game hands it to the next seat in the queue — a real
    player who was sitting there with the pick panel open and had clicked
    nothing. One click must not be able to spend somebody else's choice."""
    env = make_env()
    host = begin(env, ["James", "Rayman"])
    pick(env, "James", as_color=host)
    dismiss(env, host)

    # Host clicks a second card. Green is seated and still waiting.
    pick(env, "Rayman", as_color=host)
    dump = env.eval("dumpSetupState()")
    assert "Green=" in dump.split("waiting:")[1].split("|")[0], (
        f"the host's single click spent Green's choice: {dump}")
    assert env.eval("gameState.started") is not True

    # Green makes their own choice: one click, no confirm needed.
    pick(env, "Rayman", as_color="Green")
    dismiss(env, "Green")
    assert env.eval("gameState.started") is True
    assert sorted(roster(env).values()) == ["James", "Rayman"]


def test_clicking_a_closed_step_closes_it_instead_of_acting():
    """A ghost panel must be refused and repaired, not obeyed.

    This is the bug that stranded a reseated player behind a frozen Step 2
    window while the rest of the table started Day 1.
    """
    env = make_env()
    begin(env, ["Coco", "James"])
    pick(env, "Coco")
    dismiss(env, "White")
    pick(env, "James", as_color="Blue")
    dismiss(env, "Blue")
    assert env.eval("gameState.started") is True
    before = roster(env)

    # Every leftover walkthrough click a stale client could still send.
    env.execute("TTS.broadcasts = {}")
    for stale in ('onPickPath(Player["White"], "-1", "pickRing")',
                  'onVariantsContinue(Player["White"], "-1", "variantsContinue")',
                  'onPickChar(Player["White"], "-1", "pickRayman")',
                  'onToggleRotation(Player["White"], "-1", "toggleRotation")',
                  'onToggleDifficulty(Player["White"], "-1", "toggleDifficulty")',
                  'onBriefBack(Player["White"], "-1", "briefBack")'):
        env.execute(stale)
    flush(env)

    assert roster(env) == before, "a ghost-panel click changed the roster after setup"
    assert env.eval("gameState.started") is True, "a ghost-panel click un-started the game"
    assert env.eval('gameState.turnStyle') == "full", (
        "a ghost variants click flipped a rule after the game began")
    for panel in SETUP_PANELS:
        assert not visible(env, panel), f"{panel} was reopened by a stale click"
    assert any("leftover" in m for m in messages(env)), (
        "a ghost-panel click was swallowed silently — the player gets no "
        "explanation and no way to close the window")
