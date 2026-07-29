"""The persistent Message Log panel (lua/ui_msglog.lua).

The log exists because TTS broadcasts fade in a few seconds and render behind
the Phase Banner — playtest: "messages disappear before I can read them". So
every public `broadcastEvent` is also kept in `gameState.messageLog` and drawn
in a panel that stays until the player clears or hides it.

That makes it a *history*, and history has failure modes nothing else in the
suite watches: it must not grow without bound inside the save payload, it must
survive save/load, hiding the panel must not throw the backlog away, and the
category a message carries must actually have a colour — an unmapped category
still renders, just in the wrong colour, so it fails silently forever.

`ui_msglog.lua` had no tests at all: `logMessage`, `refreshMsgLog`,
`onMsgLogToggle`, `onMsgLogClear` and `onMsgLogHide` were never named in any
test module, and the XML handler smoke test only proves the three buttons do
not crash.
"""
import os
import re

import pytest
from conftest import LUA_DIR, all_lua_files, lua52, lua_to_py, make_env, read_text

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


def log_entries(env):
    return lua_to_py(env.eval("gameState.messageLog")) or []


def messages(env):
    return [e["m"] for e in log_entries(env)]


def panel_text(env):
    return env.eval('UI.getAttribute("msgLogBody", "text")') or ""


def panel_visible(env):
    return lua_to_py(env.eval("TTS.ui.visible")).get("msgLog")


class TestBroadcastsAreRecorded:
    def test_every_broadcast_lands_in_the_log(self, env):
        """The wiring in global.lua's broadcastEvent — the only way entries
        ever get in. It is wrapped in pcall there, so a break here would lose
        the log silently rather than raising."""
        env.globals().broadcastEvent("gain", "Ellie gathers 2 Wood.")
        env.globals().broadcastEvent("damage", "Charlie strikes!")
        assert messages(env) == ["Ellie gathers 2 Wood.", "Charlie strikes!"]

    def test_entries_carry_category_and_day(self, env):
        env.execute("gameState.day = 4")
        env.globals().broadcastEvent("warn", "The porch light flickers.")
        entry = log_entries(env)[0]
        assert entry["c"] == "warn"
        assert entry["day"] == 4, "the day stamp is what makes the log readable after Dawn"

    def test_log_self_heals_on_a_save_that_never_had_one(self, env):
        """messageLog is not in migrateGameState's defaults — logMessage
        creates it. A save from before the panel existed must still log."""
        env.execute("gameState.messageLog = nil")
        env.globals().broadcastEvent("proc", "restored save speaks")
        assert messages(env) == ["restored save speaks"]


class TestTheLogIsBounded:
    def test_it_caps_at_msglog_max_and_keeps_the_newest(self, env):
        """gameState is JSON-encoded into the save on every autosave, so an
        uncapped log grows the payload for the whole 7-day campaign."""
        cap = env.eval("MSGLOG_MAX")
        for i in range(cap + 25):
            env.globals().broadcastEvent("proc", "msg %d" % i)

        kept = messages(env)
        assert len(kept) == cap
        assert kept == ["msg %d" % i for i in range(25, cap + 25)], \
            "the cap must drop the oldest entries, not the newest"

    def test_the_panel_renders_only_the_newest_lines(self, env):
        show = env.eval("MSGLOG_SHOW_LINES")
        for i in range(show + 6):
            env.globals().broadcastEvent("proc", "msg %d" % i)

        lines = panel_text(env).split("\n")
        assert len(lines) == show
        assert "msg %d" % (show + 5) in lines[-1], "the newest message must be last"
        assert "msg 0" not in panel_text(env)


class TestHidingNeverLosesHistory:
    def test_hide_keeps_the_backlog_and_stops_reopening(self, env):
        env.globals().broadcastEvent("gain", "before hiding")
        env.globals().onMsgLogHide(None, None, None)
        assert panel_visible(env) is False

        env.globals().broadcastEvent("damage", "while hidden")
        assert panel_visible(env) is False, \
            "a new message must not reopen a panel the player deliberately hid"
        assert messages(env) == ["before hiding", "while hidden"], \
            "hiding the panel must not stop recording"

    def test_toggle_brings_it_back_with_the_backlog_intact(self, env):
        env.globals().broadcastEvent("gain", "written while visible")
        env.globals().onMsgLogHide(None, None, None)
        env.globals().broadcastEvent("damage", "written while hidden")

        env.globals().onMsgLogToggle(None, None, None)
        assert env.eval("gameState.msgLogHidden") is False
        assert panel_visible(env) is True
        assert "written while hidden" in panel_text(env), \
            "reopening must redraw what arrived while the panel was hidden"

    def test_the_custom_ui_toggle_does_not_drop_messages(self, env):
        """The global "hide every panel this mod draws" switch makes
        refreshMsgLog return early. The record must still be kept, or a player
        who plays with the custom UI off loses their history entirely."""
        env.execute("customUIHidden = true")
        env.globals().broadcastEvent("phase", "Night falls.")
        assert messages(env) == ["Night falls."]

        env.execute("customUIHidden = false")
        env.globals().refreshMsgLog()
        assert "Night falls." in panel_text(env)

    def test_clear_empties_both_the_state_and_the_panel(self, env):
        env.globals().broadcastEvent("gain", "one")
        env.globals().broadcastEvent("gain", "two")
        env.globals().onMsgLogClear(None, None, None)
        assert messages(env) == []
        assert panel_text(env) == "", \
            "clearing the state but leaving the panel drawn shows a phantom log"


class TestSurvivesSaveLoad:
    def test_the_log_comes_back_after_a_reload(self, env):
        """The panel's whole promise is that a message stays readable. A TTS
        autosave/reload mid-turn must not be the thing that erases it."""
        env.execute("gameState.day = 3")
        env.globals().broadcastEvent("warn", "Doom reaches 12.")
        saved = env.globals().onSave()

        restored = make_env()
        restored.globals().onLoad(saved)

        # onLoad broadcasts its own start-up notices, which append after the
        # restored history — so assert on presence, not on the whole list.
        entries = {e["m"]: e for e in log_entries(restored)}
        assert "Doom reaches 12." in entries
        assert entries["Doom reaches 12."]["day"] == 3
        assert entries["Doom reaches 12."]["c"] == "warn"


# --------------------------------------------------------------------------
# Static: the category vocabulary
#
# A category with no entry in MSGLOG_COLORS still renders — in the fallback
# grey. Nothing errors, nothing is logged, and the line just reads as the
# wrong kind of event for the rest of the game. Both halves are checked
# because the two tables are hand-mirrored across two files.
# --------------------------------------------------------------------------

# `broadcastEvent("warn", ...)` — literal first argument only.
BROADCAST_CALL_RE = re.compile(r'\bbroadcastEvent\(\s*"([^"]*)"')
# The keys of a `local X = { a = "...", ... }` table.
TABLE_KEY_RE = re.compile(r"^\s*(\w+)\s*=", re.M)


def _table_keys(src, decl):
    m = re.search(re.escape(decl) + r"\s*=\s*\{(.*?)\n\}", src, re.S)
    assert m, f"could not find the {decl} table — did it move or change shape?"
    return set(TABLE_KEY_RE.findall(m.group(1)))


def _broadcast_colors():
    return _table_keys(read_text(os.path.join(LUA_DIR, "global.lua")), "BROADCAST_COLORS")


def _msglog_colors():
    return _table_keys(read_text(os.path.join(LUA_DIR, "ui_msglog.lua")), "local MSGLOG_COLORS")


def test_msglog_colors_mirror_broadcast_colors():
    """ui_msglog.lua calls its palette "readable-on-black versions of
    BROADCAST_COLORS". Make that comment load-bearing: a category added to one
    table and not the other is a line that renders in the fallback grey."""
    broadcast, msglog = _broadcast_colors(), _msglog_colors()
    assert broadcast == msglog, (
        f"BROADCAST_COLORS (global.lua) and MSGLOG_COLORS (ui_msglog.lua) have "
        f"drifted — only in broadcast: {sorted(broadcast - msglog)}, only in "
        f"msglog: {sorted(msglog - broadcast)}. A category in neither renders "
        "grey in the panel and white in the broadcast, silently.")


def test_every_broadcast_category_has_a_colour():
    """~460 call sites pass the category as a literal. A typo'd one is not an
    error anywhere: broadcastToAll falls back to white, the panel to grey."""
    known = _broadcast_colors()
    assert known, "BROADCAST_COLORS parsed as empty — the parser broke"

    bad = []
    for rel in all_lua_files():
        src = read_text(os.path.join(LUA_DIR, rel))
        for i, line in enumerate(src.splitlines(), 1):
            if line.lstrip().startswith("--"):
                continue
            for category in BROADCAST_CALL_RE.findall(line):
                if category not in known:
                    bad.append(f"{rel}:{i}: broadcastEvent({category!r}, ...)")

    assert not bad, (
        f"broadcastEvent called with a category that has no colour "
        f"(known: {sorted(known)}):\n  " + "\n  ".join(bad) +
        "\n\nNothing raises — the message just renders in the fallback colour, "
        "so this only ever shows up as 'that warning didn't look like a warning'.")
