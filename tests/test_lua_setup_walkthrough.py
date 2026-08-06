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
    """The hotseat path: one person at the keyboard, driving every seat.

    This is the case the whole design exists for. One click per character, in
    the order the panel names, with no seat switching and no confirmation step
    — the host clause in onPickChar is what allows it, and the seat a pick
    lands on comes from the queue rather than from whichever player TTS
    happens to have active. Under the old model this same sequence assigned
    characters to seats the clicker had not chosen, which is what "I picked as
    Jamesx and it went to Raymanx" was.
    """
    env = make_env()
    host = begin(env, ["Coco", "James", "Rayman"])
    assert host == "White"

    for name in ("Coco", "James", "Rayman"):
        pick(env, name, as_color=host)
        assert visible(env, "charBriefing"), (
            f"the host's click on {name} did not take — a hotseat driver "
            "cannot get through setup one click at a time")
        dismiss(env, host)

    assert env.eval("gameState.started") is True, (
        "the hotseat path did not finish — one person cannot set up the table")
    # Assigned in queue order, to the seats the panel named — NOT all to the
    # clicker, and not to whichever seat TTS had active.
    assert roster(env) == {"White": "Coco", "Blue": "James", "Green": "Rayman"}


def test_a_second_player_keeps_their_own_pick():
    """A bystander cannot spend somebody else's pick.

    The host may click for anyone — that is what makes hotseat work — but a
    player who is neither the host nor the seat being picked for must be
    refused, and told whose turn it is. Without that clause, "any click
    assigns to the queue's front seat" would let a player who has already
    chosen keep choosing for everybody else."""
    env = make_env()
    host = begin(env, ["James", "Rayman", "Coco"])   # seats Blue, Green, White
    assert host == "Blue"
    pick(env, "James", as_color=host)                # the host's own seat is up
    dismiss(env, host)

    # Green is up now. White is neither the host nor the named seat.
    env.execute("TTS.broadcasts = {}")
    pick(env, "Rayman", as_color="White")
    assert not visible(env, "charBriefing"), (
        "a bystander's click was accepted — they spent the named seat's choice")
    assert any("pick" in m for m in messages(env)), (
        "the refused player was told nothing; the old dead end was silence")
    dump = env.eval("dumpSetupState()")
    assert "Green=" in dump.split("waiting:")[1].split("|")[0], (
        f"Green's turn was consumed by somebody else's click: {dump}")

    # Green's own click lands, and then White's.
    pick(env, "Rayman", as_color="Green")
    dismiss(env, "Green")
    pick(env, "Coco", as_color="White")
    dismiss(env, "White")
    assert env.eval("gameState.started") is True
    assert roster(env) == {"Blue": "James", "Green": "Rayman", "White": "Coco"}


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


# ---------------------------------------------------------------------------
# The three modes, against one code path.
#
# Character picking broke three times in a row, and every break was the same
# root cause: the seat a pick landed on was inferred from player.color, which
# in hotseat is whichever seat TTS has active — invisible to the person at the
# keyboard and not under their control. The queue is authoritative now, so
# these three tests should read almost identically. That is the point of them:
# if a future change makes one mode need special handling, one of these fails.
# ---------------------------------------------------------------------------

def test_solo_one_seat_one_player():
    """Solo: a single seat, and every click is unambiguously theirs."""
    env = make_env()
    host = begin(env, ["Coco"])
    pick(env, "Coco", as_color=host)
    dismiss(env, host)
    assert env.eval("gameState.started") is True, "a solo table could not set up"
    assert roster(env) == {"White": "Coco"}
    assert env.eval("gameState.playerCount") == 1


def test_a_short_table_is_told_it_is_a_short_table():
    """One seat = one character, and setup has to say so up front.

    The game is tuned for 3-5 characters and getDoomRate clamps to the
    3-player Doom clock however few there are, so a one-character game is the
    full pressure against a third of the actions. It is still allowed — the
    host's table, the host's call — but discovering it on Day 3 is not a call.
    """
    env = make_env()
    begin(env, ["Coco"])
    said = " ".join(messages(env))
    assert "1-CHARACTER game" in said, "a lone host was not told the party size"
    assert "Hotseat" in said, (
        "the warning has to point at the way solo actually works — three "
        "seated colours driven from one keyboard, not one character")


def test_a_full_table_is_not_warned_about_its_size():
    env = make_env()
    begin(env, ["Coco", "James", "Rayman"])
    assert "CHARACTER game" not in " ".join(messages(env))


def test_multiplayer_each_player_picks_on_their_own_turn():
    """Multiplayer: everyone clicks their own card when the panel names them."""
    env = make_env()
    begin(env, ["Coco", "James", "Rayman"])
    for name, seat in (("Coco", "White"), ("James", "Blue"), ("Rayman", "Green")):
        pick(env, name, as_color=seat)
        dismiss(env, seat)
    assert env.eval("gameState.started") is True
    assert roster(env) == {"White": "Coco", "Blue": "James", "Green": "Rayman"}


def test_hotseat_one_person_drives_every_seat_without_switching():
    """Hotseat: the host clicks through all three seats from one keyboard.

    The clicks all arrive on the host's colour — that is exactly what TTS does
    when one person drives several seats — and they must still be distributed
    down the queue rather than piling onto the clicker.
    """
    env = make_env()
    host = begin(env, ["Coco", "James", "Rayman"])
    for name in ("Coco", "James", "Rayman"):
        pick(env, name, as_color=host)      # never switching seats
        dismiss(env, host)
    assert env.eval("gameState.started") is True
    assert roster(env) == {"White": "Coco", "Blue": "James", "Green": "Rayman"}, (
        "the hotseat driver's clicks did not follow the queue — this is the "
        "'I picked as Jamesx and it went to Raymanx' bug")


def test_the_three_modes_agree():
    """Same clicks, same result, whoever the clicks came from.

    Multiplayer (each player clicks their own) and hotseat (one person clicks
    them all) must produce an identical roster. They are the same code path
    now; if they ever diverge, the inference has come back.
    """
    def run(driver_is_host):
        env = make_env()
        host = begin(env, ["Coco", "James", "Rayman"])
        for name, seat in (("Coco", "White"), ("James", "Blue"), ("Rayman", "Green")):
            who = host if driver_is_host else seat
            pick(env, name, as_color=who)
            dismiss(env, who)
        return roster(env)

    assert run(True) == run(False)
