"""Guard: we may only call TTS API methods that actually exist.

A method name that TTS does not have fails ONLY at runtime, and only on the
code path that reaches it:

    cannot access field setNotebookTabs of userdata<LuaNotes>
    cannot access field LightIntensity of userdata<LuaLighting>

Both shipped. The Notebook one is the instructive case: the whole Notebook
was empty every game, and **every test passed**, because tests/tts_stub.lua
had invented a `Notes.setNotebookTabs()` that the real API does not have. The
stub is our model of TTS; when the model is wrong in the same direction as the
code, tests confirm the bug instead of catching it.

So this module guards the surface from BOTH sides:

  1. lua/ may only call methods on the allowlist below;
  2. tts_stub.lua may only DEFINE methods on the allowlist — it is not allowed
     to invent API, which is what let the notebook bug through.

Adding a method means adding it here, which is the moment to go and check it
against the real API. The names below were verified against Tabletop
Simulator's own assembly (Tabletop Simulator_Data/Managed/Assembly-CSharp.dll,
where the C# methods are PascalCase and exposed to Lua as camelCase) and the
published API docs. NOTE that a name being absent from the assembly's string
table does not prove it is missing — several real methods are bound
dynamically and never appear as plain strings — so this list is curated, not
machine-generated.
"""

import os
import re

from conftest import LUA_DIR, TESTS, all_lua_files, read_text

# Methods only. Properties (Lighting.light_intensity, Turns.enable,
# MusicPlayer.player_status, ...) are assigned rather than called and are not
# part of this check — the regex below only matches `Name.member(`.
TTS_SINGLETON_API = {
    "Notes": {
        # NB: there is no setNotebookTabs. Tabs are managed one at a time.
        "getNotes", "setNotes",
        "getNotebookTabs", "addNotebookTab", "editNotebookTab", "removeNotebookTab",
    },
    "Lighting": {
        "apply",
        "getLightColor", "setLightColor",
        "getAmbientSkyColor", "setAmbientSkyColor",
        "getAmbientEquatorColor", "setAmbientEquatorColor",
        "getAmbientGroundColor", "setAmbientGroundColor",
    },
    "UI": {
        "show", "hide",
        "getAttribute", "getAttributes", "setAttribute", "setAttributes",
        "getValue", "setValue",
        "getXml", "setXml", "getXmlTable", "setXmlTable",
        "getCustomAssets", "setCustomAssets",
        "setClass", "getClass",
    },
    "Wait": {"time", "frames", "condition", "stop", "stopAll"},
    "Player": {"getPlayers", "getSpectators", "getColors", "getAvailableColors"},
    "JSON": {"encode", "encode_pretty", "decode"},
    "Turns": {"getNextTurnColor", "getPreviousTurnColor"},
    "Physics": {"cast", "getGravity", "setGravity", "play"},
    "MusicPlayer": {
        "play", "pause", "skipBack", "skipForward",
        "getCurrentAudioclip", "setCurrentAudioclip",
        "getPlaylist", "setPlaylist",
    },
    "Global": {"call", "getVar", "setVar", "getTable", "setTable"},
}

_CALL_RE = re.compile(
    r"\b(" + "|".join(TTS_SINGLETON_API) + r")\.([A-Za-z_]\w*)\s*\(")


def _strip_comments(src):
    """Drop -- line comments so prose can name a method without failing."""
    return "\n".join(re.sub(r"--.*$", "", line) for line in src.splitlines())


def test_lua_only_calls_tts_methods_that_exist():
    problems = []
    for rel in all_lua_files():
        src = _strip_comments(read_text(os.path.join(LUA_DIR, rel)))
        for i, line in enumerate(src.splitlines(), 1):
            for obj, method in _CALL_RE.findall(line):
                if method not in TTS_SINGLETON_API[obj]:
                    problems.append(f"{rel}:{i}: {obj}.{method}() is not a TTS API method")
    assert not problems, (
        "Lua calls TTS methods that do not exist. This fails only at runtime, "
        "on the path that reaches it — 'cannot access field X of "
        "userdata<...>' — and the feature silently does nothing until then:\n  "
        + "\n  ".join(problems)
        + "\n\nIf the method IS real, add it to TTS_SINGLETON_API in "
          "tests/test_tts_api_surface.py after checking the API docs.")


def _stub_table(src, name):
    """Body of a `Name = { ... }` assignment, brace-balanced."""
    m = re.search(rf"^{name}\s*=\s*\{{", src, re.M)
    if not m:
        return None
    i, depth = m.end() - 1, 0
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[i + 1:j]
    return None


def test_the_stub_does_not_invent_api_that_tts_lacks():
    """The stub is our model of TTS. A method here that TTS lacks makes every
    test agree with a bug — exactly how Notes.setNotebookTabs shipped."""
    src = _strip_comments(read_text(os.path.join(TESTS, "tts_stub.lua")))
    problems = []
    for name, allowed in TTS_SINGLETON_API.items():
        body = _stub_table(src, name)
        if body is None:
            continue
        # Only top-level `key = function` entries of this table.
        depth = 0
        for line in body.splitlines():
            if depth == 0:
                m = re.match(r"\s*(\w+)\s*=\s*function", line)
                if m and m.group(1) not in allowed:
                    problems.append(
                        f"tts_stub.lua: {name}.{m.group(1)}() is stubbed but is "
                        "not a real TTS method")
            depth += line.count("{") - line.count("}")
    assert not problems, (
        "the TTS stub invents API that the real engine does not have, so tests "
        "validate against a fiction:\n  " + "\n  ".join(problems))


def test_the_notebook_is_populated_through_the_real_api():
    """Specific regression: the Notebook was empty every game."""
    # Comments stripped: the code there explains the bug by name.
    src = _strip_comments(read_text(os.path.join(LUA_DIR, "ui_help.lua")))
    assert "setNotebookTabs" not in src, \
        "Notes.setNotebookTabs does not exist — use addNotebookTab/editNotebookTab"
    assert "addNotebookTab" in src and "editNotebookTab" in src, \
        "populateNotebook should add tabs, and edit them in place on reload"
