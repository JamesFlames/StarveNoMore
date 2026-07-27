"""
Aggregate playtest session logs → the tables the batch-4 gates need.

Each playtest exports a JSON blob via the Week in Review panel's
"Copy Session Log" button (lua/telemetry.lua, schema 1). Save each one as
a .json file under playtest/sessions/ and run:

    python scripts/analyze_sessions.py                 # default directory
    python scripts/analyze_sessions.py path/to/logs    # any directory

Reports:
  * win rate — overall, by difficulty, by player count (W3: the 40-50%
    Standard target)
  * loss-day histogram + loss causes (W3: losses should cluster late)
  * median/mean turn seconds split by turnStyle (W1: the Rotation A/B
    verdict lives here)
  * batch-beat usage — press kills, Signatures, Source splits, dares
    (do the built moments actually fire at real tables?)
  * OPTION UTILIZATION — the fraction of games in which each Market item is
    crafted, each recipe cooked, each action taken, each location visited,
    each Visitor drawn and each Trophy earned, sorted ascending, scored
    against the full catalog in content/. Everything near zero is a cut
    candidate under the design's §3 complexity-budget audit.

Without this file, "instrumented humans" decays back into anecdote at the
aggregation step (I in frameworkimprovements.md).
"""

import csv
import json
import os
import statistics
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DIR = os.path.join(REPO_ROOT, "playtest", "sessions")
CONTENT = os.path.join(REPO_ROOT, "content")

# Schema 1 predates the `usage` block; it still aggregates for everything
# else, and simply contributes no utilization data. Rejecting old logs would
# throw away the win-rate history for the sake of a newer report.
KNOWN_SCHEMAS = {1, 2}

# Which usage bucket is scored against which authored catalog. The catalog is
# the point: a report over only the things that WERE used can never show you
# the things that never are, and the never-used tail is the whole finding.
# The column is the card's PRINTED name, because that is what the Lua side
# records (recordUsage is fed getNickname()). A mismatch here silently turns
# the whole report into "nothing was ever used", so it is worth a test.
CATALOGS = {
    "crafted":   ("cards_market.csv",   "name",      "Market items"),
    "cooked":    ("cards_recipes.csv",  "name",      "recipes"),
    "visitors":  ("cards_visitors.csv", "character", "Visitors"),
    "trophies":  ("cards_trophies.csv", "boss",      "Trophies"),
}
# Not CSV-backed — small fixed sets defined in the rules.
STATIC_CATALOGS = {
    "actions":   (["Move", "Gather", "Craft", "Cook", "Fight", "Rest", "Cleanse",
                   "Barricade", "Defend", "Stabilize", "Trade (remote)",
                   "Trade (extra)"], "action types"),
    "locations": (["JamesHouse", "RaymanHouse", "EllieLucaHouse",
                   "BasketballCourt", "BadmintonCourt"], "locations"),
}


def load_catalog(filename, column):
    """Authored names for a content deck, or None if the file isn't there."""
    path = os.path.join(CONTENT, filename)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or column not in rows[0]:
        return None
    return [r[column] for r in rows if r.get(column)]


def load_sessions(directory):
    sessions, skipped = [], []
    for fn in sorted(os.listdir(directory)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(directory, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                blob = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            skipped.append((fn, str(e)))
            continue
        if blob.get("schema") not in KNOWN_SCHEMAS:
            skipped.append((fn, f"unknown schema {blob.get('schema')!r}"))
            continue
        blob["_file"] = fn
        sessions.append(blob)
    return sessions, skipped


def pct(n, d):
    return f"{100.0 * n / d:.0f}%" if d else "—"


def analyze(sessions):
    """Aggregate into a plain dict (unit-testable; printing happens in main)."""
    out = {"games": len(sessions)}
    wins = [s for s in sessions if s.get("outcome", {}).get("cause") == "victory"]
    out["wins"] = len(wins)

    by_difficulty = {}
    by_players = {}
    loss_days = {}
    loss_causes = {}
    for s in sessions:
        setup = s.get("setup") or {}
        cause = (s.get("outcome") or {}).get("cause")
        won = cause == "victory"
        d = setup.get("difficulty") or "unknown"
        by_difficulty.setdefault(d, [0, 0])
        by_difficulty[d][0] += won
        by_difficulty[d][1] += 1
        p = setup.get("playerCount") or "?"
        by_players.setdefault(p, [0, 0])
        by_players[p][0] += won
        by_players[p][1] += 1
        if not won and cause:
            day = (s.get("outcome") or {}).get("day")
            loss_days[day] = loss_days.get(day, 0) + 1
            loss_causes[cause] = loss_causes.get(cause, 0) + 1
    out["by_difficulty"] = by_difficulty
    out["by_players"] = by_players
    out["loss_days"] = loss_days
    out["loss_causes"] = loss_causes

    # Turn durations by turn style (the W1 A/B verdict)
    by_style = {}
    for s in sessions:
        style = (s.get("setup") or {}).get("turnStyle") or "unknown"
        secs = [t.get("seconds", 0) for t in (s.get("turns") or [])]
        by_style.setdefault(style, []).extend(secs)
    out["turns_by_style"] = {
        style: {"turns": len(secs),
                "median_s": statistics.median(secs) if secs else None,
                "mean_s": round(statistics.mean(secs), 1) if secs else None}
        for style, secs in by_style.items()
    }

    # Batch beats: do the built moments fire?
    beats_total = {"pressKills": 0, "signaturesUsed": 0, "sourceSplit": 0, "daresTaken": 0}
    for s in sessions:
        b = s.get("beats") or {}
        beats_total["pressKills"] += b.get("pressKills") or 0
        beats_total["signaturesUsed"] += len(b.get("signaturesUsed") or [])
        beats_total["sourceSplit"] += 1 if b.get("sourceSplit") else 0
        beats_total["daresTaken"] += b.get("daresTaken") or 0
    out["beats"] = beats_total

    # ---- option utilization (§26 / design §20.2 item 8) -------------------
    # Two numbers per option: the fraction of GAMES it appeared in (the one
    # that decides whether content is dead), and the raw count (which
    # separates "used once, in one game" from "used constantly, in one game").
    logged = [s for s in sessions if s.get("usage")]
    util = {}
    for bucket in list(CATALOGS) + list(STATIC_CATALOGS):
        games_with, totals = {}, {}
        for s in logged:
            counts = (s.get("usage") or {}).get(bucket) or {}
            for name, n in counts.items():
                games_with[name] = games_with.get(name, 0) + 1
                totals[name] = totals.get(name, 0) + int(n or 0)

        if bucket in CATALOGS:
            filename, column, label = CATALOGS[bucket]
            catalog = load_catalog(filename, column)
        else:
            catalog, label = STATIC_CATALOGS[bucket]

        # Score against the catalog so never-used options appear as zeros
        # rather than being invisible. Anything the log names that the
        # catalog doesn't is kept too — a renamed card should show up as a
        # discrepancy, not vanish.
        names = sorted(set(catalog or []) | set(games_with))
        rows = [{"name": n,
                 "games": games_with.get(n, 0),
                 "uses": totals.get(n, 0),
                 "share": (games_with.get(n, 0) / len(logged)) if logged else None}
                for n in names]
        rows.sort(key=lambda r: (r["games"], r["uses"], r["name"]))
        util[bucket] = {"label": label, "rows": rows,
                        "catalog_known": catalog is not None}
    out["utilization"] = util
    out["utilization_games"] = len(logged)
    return out


def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIR
    if not os.path.isdir(directory):
        raise SystemExit(f"no such directory: {directory}")
    sessions, skipped = load_sessions(directory)
    for fn, why in skipped:
        print(f"  skipped {fn}: {why}")
    if not sessions:
        raise SystemExit(f"no session logs found in {directory} — paste Copy Session Log "
                         "exports there as .json files")

    r = analyze(sessions)
    print(f"\nSessions: {r['games']}   Wins: {r['wins']} ({pct(r['wins'], r['games'])})")

    print("\nWin rate by difficulty (W3 target: Standard 40-50%):")
    for d, (w, n) in sorted(r["by_difficulty"].items()):
        print(f"  {d:<10} {w}/{n}  ({pct(w, n)})")

    print("\nWin rate by player count:")
    for p, (w, n) in sorted(r["by_players"].items(), key=lambda kv: str(kv[0])):
        print(f"  {p} players  {w}/{n}  ({pct(w, n)})")

    if r["loss_days"]:
        print("\nLoss-day histogram (W3: losses should cluster on the last two days):")
        for day, n in sorted(r["loss_days"].items(), key=lambda kv: (kv[0] is None, kv[0])):
            print(f"  day {day}: {'#' * n} ({n})")
        print("Loss causes: " + ", ".join(f"{k}={v}" for k, v in sorted(r["loss_causes"].items())))

    print("\nTurn seconds by turn style (W1 — the Rotation A/B):")
    for style, stats in sorted(r["turns_by_style"].items()):
        print(f"  {style:<8} turns={stats['turns']:<5} median={stats['median_s']}s  mean={stats['mean_s']}s")

    b = r["beats"]
    print("\nBatch beats across all sessions:")
    print(f"  press kills: {b['pressKills']}   signatures used: {b['signaturesUsed']}   "
          f"source splits: {b['sourceSplit']}   dares taken: {b['daresTaken']}")

    print_utilization(r)


def print_utilization(r, top=12):
    """Sorted ascending, because the interesting end is the bottom."""
    n = r.get("utilization_games", 0)
    print(f"\n{'=' * 68}\nOPTION UTILIZATION — {n} session(s) carry usage data")
    if not n:
        print("  No logs with a `usage` block yet (schema 2+). Play a game and\n"
              "  export it; every option below will read 0/0 until then.")
        return
    print("  Sorted ascending: the top of each list is the cut-candidate end.\n"
          "  'games' = sessions the option appeared in; 'uses' = total times.")

    for bucket, data in r["utilization"].items():
        rows = data["rows"]
        unused = [x for x in rows if x["games"] == 0]
        print(f"\n  {data['label'].upper()}  ({len(rows)} authored"
              + ("" if data["catalog_known"] else ", catalog file not found")
              + f"; {len(unused)} never used)")
        for row in rows[:top]:
            share = f"{100 * row['share']:.0f}%" if row["share"] is not None else "—"
            flag = "  <- never used" if row["games"] == 0 else ""
            print(f"    {row['name'][:38]:<40} {row['games']:>3} games "
                  f"({share:>4})  {row['uses']:>4} uses{flag}")
        if len(rows) > top:
            print(f"    … and {len(rows) - top} more (rising)")

    print("\n  Reading it: anything at 0 games across a decent sample is a cut\n"
          "  candidate under the design's §3 complexity-budget audit. The\n"
          "  Visitor deck (§19.6 item 3) is the standing open question — if\n"
          "  Visitors are drawn and ignored, they go.")


if __name__ == "__main__":
    main()
