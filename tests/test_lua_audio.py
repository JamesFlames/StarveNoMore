"""audio.lua's failure handling — the part that decides a clip is dead.

The soundscape has no in-game controls, so when it stops there is nothing to
click and nothing on screen that says why. Both behaviours below produced
exactly that: a table that played in silence for the rest of the session and
could only get the sound back by reloading the save.
"""
import pytest

try:
    import lupa.lua52 as lua52
except ImportError:  # pragma: no cover
    lua52 = None

from conftest import make_env

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")


@pytest.fixture
def env():
    return make_env()


def played(rt):
    return rt.eval("#MusicPlayer.clips")


def strike(rt):
    """Fire the load watchdog once, the way six seconds of silence would.

    Not via flush(): the stub runs queued callbacks in scheduling order and
    ignores delays, and _playNextDay always queues the next-track wait BEFORE
    the watchdog — so the next track always "arrives" first and cancels the
    watchdog, which therefore never fires under flush(). In real TTS the
    watchdog is 6s and the track is 50-150s, so it always fires first. Calling
    the callback by hand is the only way to test the path the game runs.

    A no-op when no watchdog is armed, which is itself the state a silent
    audio system ends up in.
    """
    rt.execute("""
        (function()
            local h = Audio.state.watchHandle
            if not h then return end
            local fn = TTS.waits[h]
            TTS.waits[h] = nil
            if fn then fn() end
        end)()
    """)


def test_a_total_outage_does_not_silence_the_rest_of_the_session(env):
    """Every clip failing at once is an outage, not a pool of broken files.

    The whole soundscape comes off one local http.server, and the deploy
    script purges TTS's asset cache on every run — so the load right after a
    deploy cold-fetches every board, card and clip at once, and a server that
    is slow, closed, or beaten to :8080 by a leftover copy of itself fails all
    of them together. The skip list used to be permanent and per-session: once
    it had swallowed the pool, _pickRandom returned nil forever, and the
    server coming back up could not fix it. Only reloading the save could,
    and nothing said so.
    """
    env.execute('MusicPlayer.player_status = "Stop"')
    env.globals().Audio.startDayAmbience()
    for _ in range(12):        # more strikes than the pool has clips
        strike(env)

    env.execute('MusicPlayer.clips = {}; MusicPlayer.player_status = "Play"')
    env.globals().Audio.startDayAmbience()          # the next Dawn

    assert played(env) > 0, (
        "audio never recovered from a total outage — the skip list ate the "
        "whole pool and kept it")


def test_night_recovers_from_a_total_outage_too(env):
    """The night drones are their own, much smaller pool, so they empty
    fastest of all."""
    env.execute('MusicPlayer.player_status = "Stop"')
    env.globals().Audio.startNightAmbience()
    for _ in range(12):
        strike(env)

    env.execute('MusicPlayer.clips = {}; MusicPlayer.player_status = "Play"')
    env.globals().Audio.startNightAmbience()

    assert played(env) > 0


def test_one_bad_load_is_a_retry_not_a_verdict(env):
    """The first miss is usually the cold cache, not the file. A clip that
    fails once and then loads must keep its place in the pool."""
    env.execute('MusicPlayer.player_status = "Stop"')
    env.globals().Audio.startDayAmbience()
    first = env.eval("Audio.state.dayClip.url")

    strike(env)                                     # one failure, then it loads
    env.execute('MusicPlayer.player_status = "Play"')

    assert env.eval("Audio.state.dayClip.url") == first, (
        "a single failed load must not retire the track")


def test_a_clip_that_never_loads_is_eventually_given_up_on(env):
    """...but a URL that is genuinely dead has to stop costing a track-length
    hole in the soundscape."""
    env.execute('MusicPlayer.player_status = "Stop"')
    env.globals().Audio.startDayAmbience()
    first = env.eval("Audio.state.dayClip.url")

    strike(env)
    strike(env)

    assert env.eval("Audio.state.dayClip.url") != first, (
        "two failures in a row and the clip is still being chosen")


def test_a_long_clip_is_watched(env):
    """Ambient tracks run 50-150s, so the 6s watchdog is a real load check."""
    env.globals().Audio.startDayAmbience()
    assert env.eval("Audio.state.watchHandle") is not None


def test_a_short_clip_is_not_watched(env):
    """A bearger roar is under 4s. The watchdog fires at 6s, by which point a
    perfectly good clip has ENDED — and a finished MusicPlayer reports the
    same "Stop" a failed load does, so watching short clips would strike every
    boss sound for the crime of playing correctly."""
    env.globals().Audio.playBossLoop("bearger")
    assert env.eval("Audio.state.watchHandle") is None
    assert played(env) == 1, "the roar itself must still play"


# --------------------------------------------------------------------------
# The convenience names must resolve to clips that actually exist.
#
# Audio.playSFX returns early when AUDIO.SFX[key] is missing, by design — a
# missing sound must never break a turn. The cost of that is total silence
# with no error anywhere: rename a file under sounds/sfx/ and the manifest
# key changes, Audio.playHitLand() quietly no-ops, and the only symptom is
# that combat sounds like nothing. This is the test that notices.


def _convenience_keys(lua_sources):
    """Every `function Audio.playX() Audio.playSFX("key")` pair in audio.lua."""
    import re
    src = lua_sources["audio.lua"]
    return dict(re.findall(
        r'function\s+(Audio\.play\w+)\s*\(\s*\)\s*Audio\.playSFX\(\s*"([^"]+)"',
        src))


def test_every_sfx_convenience_name_resolves_to_a_real_clip(env, lua_sources):
    pairs = _convenience_keys(lua_sources)
    assert pairs, "found no Audio.playX -> playSFX pairs; did audio.lua change shape?"
    missing = [f"{fn}() -> {key}" for fn, key in pairs.items()
               if env.eval(f'AUDIO.SFX["{key}"] == nil')]
    assert not missing, (
        "these play helpers point at SFX keys with no clip in the manifest, so "
        "they silently do nothing: " + ", ".join(sorted(missing)) +
        "\nAdd the file under sounds/sfx/ and rerun generate_audio_manifest.py")


@pytest.mark.parametrize("fn", ["playHitLand", "playHitTaken"])
def test_the_combat_impacts_actually_play(env, fn):
    """The two new cues, end to end: helper -> manifest -> MusicPlayer."""
    before = played(env)
    getattr(env.globals().Audio, fn)()
    assert played(env) == before + 1, f"Audio.{fn}() played nothing"
