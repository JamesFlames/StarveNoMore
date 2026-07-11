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

Without this file, "instrumented humans" decays back into anecdote at the
aggregation step (I in frameworkimprovements.md).
"""

import json
import os
import statistics
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DIR = os.path.join(REPO_ROOT, "playtest", "sessions")

KNOWN_SCHEMAS = {1}


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


if __name__ == "__main__":
    main()
