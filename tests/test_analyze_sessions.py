"""analyze_sessions.py must aggregate real telemetry exports correctly
(I in frameworkimprovements.md). Uses synthetic schema-1 logs shaped exactly
like lua/telemetry.lua's buildSessionLog output."""
import json

import analyze_sessions as az  # scripts/ is on sys.path via conftest


def _log(cause="victory", day=7, difficulty="standard", players=4,
         turn_style="full", turns=(30, 60, 90), beats=None):
    return {
        "schema": 1,
        "setup": {"playerCount": players, "roster": ["James", "Coco"],
                  "pathVariant": "Compact", "scenario": None,
                  "turnStyle": turn_style, "difficulty": difficulty},
        "outcome": {"cause": cause, "day": day, "doom": 22},
        "finalCharacters": [], "days": {}, "kills": [], "meals": {},
        "turns": [{"day": 1, "name": "James", "seconds": s} for s in turns],
        "beats": beats or {"pressKills": 2, "signaturesUsed": ["James"],
                           "sourceSplit": True, "daresTaken": 1},
        "peakDoom": {"value": 24, "day": 6}, "downs": 1, "revives": 0,
    }


def test_load_skips_bad_files(tmp_path):
    (tmp_path / "good.json").write_text(json.dumps(_log()), encoding="utf-8")
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "future.json").write_text(json.dumps({"schema": 99}), encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore me", encoding="utf-8")
    sessions, skipped = az.load_sessions(str(tmp_path))
    assert len(sessions) == 1
    assert {fn for fn, _ in skipped} == {"broken.json", "future.json"}


def test_analyze_aggregates():
    sessions = [
        _log(cause="victory", difficulty="standard", players=4, turn_style="full"),
        _log(cause="defeat_doom", day=6, difficulty="standard", players=4,
             turn_style="rotate", turns=(10, 20, 30)),
        _log(cause="defeat_source", day=7, difficulty="nightmare", players=5,
             turn_style="full"),
    ]
    r = az.analyze(sessions)
    assert r["games"] == 3 and r["wins"] == 1
    assert r["by_difficulty"]["standard"] == [1, 2]
    assert r["by_difficulty"]["nightmare"] == [0, 1]
    assert r["by_players"][4] == [1, 2]
    assert r["loss_days"] == {6: 1, 7: 1}
    assert r["loss_causes"] == {"defeat_doom": 1, "defeat_source": 1}
    assert r["turns_by_style"]["rotate"]["median_s"] == 20
    assert r["turns_by_style"]["full"]["turns"] == 6
    assert r["beats"]["pressKills"] == 6
    assert r["beats"]["signaturesUsed"] == 3
    assert r["beats"]["sourceSplit"] == 3


def test_real_export_shape_is_accepted():
    """The synthetic shape must match the actual lua exporter: drive the real
    bundle, export, and feed the result through the analyzer."""
    from conftest import make_env, add_char
    env = make_env()
    add_char(env, "White", "James")
    env.execute('gameState.gameOverCause = "victory"; gameState.day = 7')
    blob = json.loads(env.globals().exportSessionLog())
    r = az.analyze([blob])
    assert r["games"] == 1 and r["wins"] == 1
