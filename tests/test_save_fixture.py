"""Frozen-save compatibility (G in frameworkimprovements.md).

saves/fixtures/midgame_v1.json is a committed Day-4 mid-campaign save.
Loading it into the CURRENT bundle and playing a full day must work — that
makes "does an in-flight campaign survive this upgrade?" a checked property
instead of a hope. When the schema changes on purpose: bump SCHEMA_VERSION,
extend migrateGameState(), and only regenerate the fixture if the old one
can no longer represent a legal game.
"""
import json
import os

import pytest

try:
    import lupa.lua52 as lua52
except ImportError:  # pragma: no cover
    lua52 = None

from conftest import ROOT
from test_lua_runtime import make_env, populate_full_world, flush
from test_full_campaign import SEATS, play_day, simple_bot_turn, subphase, assert_invariants

pytestmark = pytest.mark.skipif(lua52 is None, reason="lupa (pip install lupa) required")

FIXTURE = os.path.join(ROOT, "saves", "fixtures", "midgame_v1.json")


def load_fixture_env():
    with open(FIXTURE, "r", encoding="utf-8") as f:
        saved = f.read()
    env = make_env()
    populate_full_world(env)
    env.execute("TTS.seated = {%s}" % ", ".join(f'"{c}"' for c in SEATS))
    env.globals().onLoad(saved)
    flush(env)
    return env


def test_fixture_exists_and_is_json():
    assert os.path.isfile(FIXTURE), "committed fixture missing"
    with open(FIXTURE, "r", encoding="utf-8") as f:
        blob = json.load(f)
    assert blob["day"] >= 2 and blob["started"] is True


def test_fixture_loads_and_migrates():
    env = load_fixture_env()
    assert env.eval("gameState.started") is True
    assert env.eval("gameState.day") >= 2
    # migration ran: current schema stamped, all default-filled fields present
    assert env.eval("gameState.schemaVersion") == env.eval("SCHEMA_VERSION")
    for field in ("bossHP", "pendingSanityPenalty", "loudSignature",
                  "ongoingDawnEffects", "scenarioFlags"):
        assert env.eval(f'type(gameState.{field})') == "table", f"{field} not migrated"
    assert env.eval("gameState.difficulty") == "standard"


def test_fixture_plays_a_full_day_on_current_code():
    env = load_fixture_env()
    day_before = env.eval("gameState.day")
    play_day(env, simple_bot_turn)
    assert_invariants(env, "fixture day")
    assert subphase(env) == "GameOver" or env.eval("gameState.day") == day_before + 1


def test_stripped_fixture_still_migrates():
    """Simulate an OLDER save: strip every batch-era field and reload — the
    migration layer must fill them all back in."""
    with open(FIXTURE, "r", encoding="utf-8") as f:
        blob = json.load(f)
    for field in ("schemaVersion", "bossHP", "pendingSanityPenalty", "loudSignature",
                  "difficulty", "chronicle", "raymanTilesMovedToday", "wrongness"):
        blob.pop(field, None)
    for char in blob.get("activeChars", {}).values():
        char.pop("signatureUsed", None)
    env = make_env()
    populate_full_world(env)
    env.globals().onLoad(json.dumps(blob))
    flush(env)
    assert env.eval("gameState.schemaVersion") == env.eval("SCHEMA_VERSION")
    assert env.eval('type(gameState.bossHP)') == "table"
    assert env.eval("gameState.difficulty") == "standard"
    assert env.eval("gameState.activeChars.White.signatureUsed") is False
    # and it still plays
    env.execute("TTS.seated = {%s}" % ", ".join(f'"{c}"' for c in SEATS))
    play_day(env, simple_bot_turn)
    assert_invariants(env, "stripped fixture day")
