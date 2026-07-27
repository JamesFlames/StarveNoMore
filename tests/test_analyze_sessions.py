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


# --------------------------------------------------------------------------
# Option utilization (§20.2 item 8). The whole value of this report is in its
# ZEROS — the options nobody ever touches — so the property that matters is
# that it scores against the authored catalog, not against the log.
# --------------------------------------------------------------------------

def _log2(usage, **kw):
    log = _log(**kw)
    log["schema"] = 2
    log["usage"] = usage
    return log


def test_schema_1_logs_still_load():
    """Old logs predate `usage`. Rejecting them would throw away the win-rate
    history for the sake of a newer report."""
    r = az.analyze([_log()])
    assert r["games"] == 1
    assert r["utilization_games"] == 0


def test_unused_content_appears_as_an_explicit_zero():
    """A report over only the things that WERE used can never show you the
    things that never are. This is the finding, in one assertion."""
    r = az.analyze([_log2({"crafted": {"Flashlight": 2}})])
    rows = {x["name"]: x for x in r["utilization"]["crafted"]["rows"]}
    assert r["utilization"]["crafted"]["catalog_known"], (
        "content/cards_market.csv did not load — the report is only as good "
        "as its catalog")
    assert rows["Flashlight"]["games"] == 1
    assert rows["Flashlight"]["uses"] == 2
    # Something authored but untouched must be present and zero.
    zeros = [n for n, x in rows.items() if x["games"] == 0]
    assert len(zeros) > 40, (
        f"only {len(zeros)} never-used Market items — the catalog isn't being "
        "scored against")
    assert "Crowbar" in zeros


def test_rows_are_sorted_with_the_cut_candidates_first():
    r = az.analyze([_log2({"crafted": {"Flashlight": 5, "Crowbar": 1}})])
    rows = r["utilization"]["crafted"]["rows"]
    assert rows[0]["games"] == 0, "unused options must sort to the top"
    games = [x["games"] for x in rows]
    assert games == sorted(games), "rows are not ascending"


def test_share_is_a_fraction_of_games_not_of_uses():
    """'Crafted in 1 of 2 games' and 'crafted twice' are different facts, and
    the first is the one that decides whether content is dead."""
    r = az.analyze([_log2({"crafted": {"Flashlight": 9}}),
                    _log2({"crafted": {}})])
    rows = {x["name"]: x for x in r["utilization"]["crafted"]["rows"]}
    assert rows["Flashlight"]["games"] == 1
    assert rows["Flashlight"]["uses"] == 9
    assert abs(rows["Flashlight"]["share"] - 0.5) < 1e-9


def test_every_bucket_is_reported_even_with_no_data():
    r = az.analyze([_log2({})])
    for bucket in ("crafted", "cooked", "visitors", "trophies",
                   "actions", "locations"):
        assert bucket in r["utilization"], f"{bucket} missing from the report"
    # The Visitor deck is §19.6 item 3's open question — it must be scored.
    assert r["utilization"]["visitors"]["catalog_known"]
    assert all(x["games"] == 0 for x in r["utilization"]["visitors"]["rows"])


def test_all_five_locations_are_scored():
    """The Badminton-Court prediction needs every tile listed, including the
    ones nobody visited."""
    r = az.analyze([_log2({"locations": {"EllieLucaHouse": 12}})])
    names = {x["name"] for x in r["utilization"]["locations"]["rows"]}
    assert "BadmintonCourt" in names and "BasketballCourt" in names


def test_the_printed_report_runs(capsys):
    r = az.analyze([_log2({"crafted": {"Flashlight": 2}})])
    az.print_utilization(r)
    out = capsys.readouterr().out
    assert "OPTION UTILIZATION" in out
    assert "never used" in out


def test_every_catalog_column_actually_exists():
    """A wrong column name here doesn't error — it makes load_catalog return
    None, and the report quietly degrades to 'nothing was ever used'. That is
    exactly the failure the report exists to prevent, so pin it."""
    for bucket, (filename, column, label) in az.CATALOGS.items():
        names = az.load_catalog(filename, column)
        assert names, (
            f"{bucket}: could not read column {column!r} from {filename} — "
            "the utilization report for this bucket would silently be empty")
        assert len(names) >= 3, f"{bucket}: only {len(names)} entries in {filename}"
