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

from conftest import confirm_roster, flush, lua_to_py, make_env, populate_full_world

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")

# A character's seat colour is fixed (CHARACTER_COLORS, lua/global.lua).
SEAT_FOR = {"James": "Blue", "Coco": "White", "Rayman": "Green",
            "Ellie": "Yellow", "Luca": "Red"}
# Seating each player on their own character's colour means no reseat fires,
# which keeps the walkthrough tests about the STEP MACHINE. The reseat/swap
# path has its own coverage in test_full_campaign.py.
ROSTER = ["Coco", "James", "Rayman", "Ellie", "Luca"]

SETUP_PANELS = ("setupStep1", "setupStepVariants", "setupStep2",
                "setupRosterConfirm", "charBriefing")


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
    # The last dismiss lands on the roster confirmation, not on a built table.
    confirm_roster(env, color)


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
    the order the panel names, with no seat switching and nothing to confirm
    per pick (the roster confirmation comes once, at the end)
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


# ---------------------------------------------------------------------------
# The Solo toggle vs. the seats it actually needs
#
# "It said it would let me pick 3 characters but it only let me pick 1 and then
# I had Begin Day." The toggle read "one player runs 3 characters" and never
# counted the seated colours the pick queue is built from, so at one seat it
# promised three, dealt one, and the start-of-setup size warning had long
# scrolled away. Solo cannot seat the other two itself — Hotseat is a TTS
# client setting — so the toggle has to tell the truth instead.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# The roster confirmation (Step 2.5)
#
# Setup used to be built by the last briefing click. A hotseat player named
# their seats after the characters they meant to play, picked Ellie while the
# panel was picking for the seat named Jamesx, and could not reconstruct it
# afterwards — finalize renames every seat to its character's colour, so the
# evidence was gone by the time the table looked. The last click shows the
# roster now, and Pick again costs nothing because nothing has been placed.
# ---------------------------------------------------------------------------

def reach_roster_confirm(env, names):
    """Pick every character but do NOT confirm — stop on the roster panel."""
    host = begin(env, names)
    for n in names:
        pick(env, n)
        env.execute(f'onBriefDismiss(Player["{SEAT_FOR[n]}"], "-1", "briefDismiss")')
        flush(env)
    return host


def roster_body(env):
    return env.eval('UI.getAttribute("rosterConfirmBody", "text")')


def test_the_last_click_shows_the_roster_instead_of_building_the_table():
    env = make_env()
    reach_roster_confirm(env, ["Coco", "James"])
    assert visible(env, "setupRosterConfirm")
    assert env.eval("gameState.started") is not True, (
        "the table was built before anyone confirmed the roster")
    body = roster_body(env)
    assert "Coco" in body and "James" in body, body
    assert "White seat" in body and "Blue seat" in body, (
        "the summary has to name the SEAT each character landed on — the seat "
        "is what the player recognises before finalize renames it: " + body)


def test_confirming_builds_the_table():
    env = make_env()
    host = reach_roster_confirm(env, ["Coco", "James"])
    env.execute(f'onRosterConfirm(Player["{host}"], "-1", "rosterConfirm")')
    flush(env)
    assert env.eval("gameState.started") is True
    assert roster(env) == {"White": "Coco", "Blue": "James"}
    assert not visible(env, "setupRosterConfirm")


def test_pick_again_clears_every_pick_not_just_the_last():
    """The table cannot tell which click was the wrong one — that is the whole
    reason the panel exists — so Pick again resets the lot."""
    env = make_env()
    host = reach_roster_confirm(env, ["Coco", "James"])
    env.execute(f'onRosterRedo(Player["{host}"], "-1", "rosterRedo")')
    flush(env)

    assert env.eval("gameState.started") is not True
    assert not visible(env, "setupRosterConfirm")
    assert visible(env, "setupStep2"), "Pick again did not reopen the pick step"
    waiting = env.eval("dumpSetupState()")
    assert "White=" in waiting.split("waiting:")[1].split("| picked")[0]
    assert "Blue=" in waiting.split("waiting:")[1].split("| picked")[0]
    assert "picked: nobody" in waiting, (
        "Pick again left an old choice behind: " + waiting)


def test_picking_again_can_choose_a_different_roster():
    """The bug that prompted this: the wrong character on the first seat."""
    env = make_env()
    host = reach_roster_confirm(env, ["Coco", "James"])
    env.execute(f'onRosterRedo(Player["{host}"], "-1", "rosterRedo")')
    flush(env)

    # Same seats, different characters — and the seats are free again, so the
    # duplicate-pick refusal must not fire on the characters just released.
    pick(env, "Coco", as_color="White")
    dismiss(env, "White")
    pick(env, "James", as_color="Blue")
    dismiss(env, "Blue")
    assert env.eval("gameState.started") is True
    assert roster(env) == {"White": "Coco", "Blue": "James"}


def begin_solo(env, names):
    """Reach the variants panel and flip Solo on, without continuing."""
    populate_full_world(env)
    env.globals().onLoad("")
    flush(env)
    colors = [SEAT_FOR[n] for n in names]
    env.execute("TTS.seated = {%s}" % ", ".join(f'"{c}"' for c in colors))
    host = colors[0]
    env.execute(f'onHostSetupGuided(Player["{host}"])')
    env.execute(f'onPickPath(Player["{host}"], "-1", "pickCompact")')
    env.execute(f'onToggleSolo(Player["{host}"], "-1", "toggleSolo")')
    flush(env)
    return host


def solo_label(env):
    return env.eval('UI.getAttribute("toggleSolo", "text")')


def test_solo_at_one_seat_admits_it_is_a_one_character_game():
    env = make_env()
    begin_solo(env, ["Coco"])
    assert "1-character game" in solo_label(env), (
        "the Solo toggle still promises 3 characters at a table that will be "
        "asked for 1: " + solo_label(env))
    said = " ".join(messages(env))
    assert "Hotseat" in said, "nothing told them how to actually get three seats"


def test_solo_at_three_seats_promises_three():
    env = make_env()
    begin_solo(env, ["Coco", "James", "Rayman"])
    assert "runs 3 characters" in solo_label(env)
    assert "Solo needs" not in " ".join(messages(env))


def test_solo_at_four_seats_promises_four():
    """The bug that prompted this: 4 coloured seats taken, toggle still said
    'runs 3 characters' — the shortfall fix (e447bf5) only covered fewer than
    3 seats, never more."""
    env = make_env()
    begin_solo(env, ["Coco", "James", "Rayman", "Ellie"])
    assert "runs 4 characters" in solo_label(env)
    assert "runs 3 characters" not in solo_label(env)
    assert "Solo needs" not in " ".join(messages(env))


def test_starting_solo_short_handed_says_how_many_characters():
    """The last honest moment: the pick queue is built the instant the
    variants panel closes."""
    env = make_env()
    host = begin_solo(env, ["Coco"])
    env.execute(f'onVariantsContinue(Player["{host}"], "-1", "variantsContinue")')
    flush(env)
    said = " ".join(messages(env))
    assert "SOLO MODE with 1 coloured seat" in said
    assert "one player, 3 characters" not in said
    # The half of Solo that does work at one seat is still on, and still said.
    assert "no ghost word-limit" in said
    assert env.eval("gameState.solo") is True


def test_starting_solo_with_three_seats_announces_three():
    env = make_env()
    host = begin_solo(env, ["Coco", "James", "Rayman"])
    env.execute(f'onVariantsContinue(Player["{host}"], "-1", "variantsContinue")')
    flush(env)
    said = " ".join(messages(env))
    assert "SOLO MODE: one player, 3 characters" in said
    assert "SOLO MODE with" not in said


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
