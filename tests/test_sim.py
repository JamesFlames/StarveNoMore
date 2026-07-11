"""simulate_balance.py as a regression harness.

Two jobs:
 1. Enforce the agents.md maintenance rule mechanically: the sim mirrors
    rule constants from lua/global.lua by hand, so verify the mirror.
 2. Run seeded batches and assert invariants + broad win-rate bands, so an
    accidental rule/constant change shows up as a red test instead of a
    silently wrong balance table.
"""
import os

import pytest

import simulate_balance as sim  # scripts/ is on sys.path via conftest

from conftest import LUA_DIR, TESTS, read_text

try:
    import lupa.lua52 as lua52
except ImportError:  # pragma: no cover
    lua52 = None


# ---------------------------------------------------------------------------
# Constant mirror: sim <-> lua/global.lua
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def lua_globals():
    """Evaluate just global.lua (it is self-contained data + pure functions)."""
    assert lua52 is not None, "lupa required"
    rt = lua52.LuaRuntime()
    rt.execute(read_text(os.path.join(TESTS, "tts_stub.lua")))
    rt.execute(read_text(os.path.join(LUA_DIR, "global.lua")))
    return rt


def test_character_stats_match(lua_globals):
    for name, base in sim.CHARACTERS.items():
        lua_stats = lua_globals.eval(f"CHARACTER_STATS.{name}")
        assert lua_stats is not None, f"{name} missing from CHARACTER_STATS in global.lua"
        for stat in ("health", "hunger", "sanity"):
            assert base[stat] == lua_stats[stat], (
                f"{name}.{stat}: sim={base[stat]} lua={lua_stats[stat]} — "
                "simulate_balance.py has drifted from global.lua")


def test_character_homes_match(lua_globals):
    for name, base in sim.CHARACTERS.items():
        lua_home = lua_globals.eval(f"CHARACTER_HOMES.{name}")
        assert base["home"] == lua_home, (
            f"{name} home: sim={base['home']!r} lua={lua_home!r}")


def test_doom_rates_match(lua_globals):
    for players, rates in sim.DOOM_RATES.items():
        for phase_idx, rate in enumerate(rates, start=1):
            lua_rate = lua_globals.eval(f"DOOM_RATES[{players}][{phase_idx}]")
            assert rate == lua_rate, (
                f"DOOM_RATES[{players}][{phase_idx}]: sim={rate} lua={lua_rate}")


def test_phase_for_day_matches(lua_globals):
    for day, phase in sim.PHASE_FOR_DAY.items():
        lua_phase = lua_globals.globals().getPhaseForDay(day)
        assert phase == lua_phase, f"day {day}: sim phase {phase}, lua phase {lua_phase}"


# ---------------------------------------------------------------------------
# Invariants over seeded batches
# ---------------------------------------------------------------------------

SIMS = 300
SEED = 42


def run_games(policy, players=4, rules="new", sims=SIMS, seed=SEED):
    import random
    rng = random.Random(seed)
    games = []
    for _ in range(sims):
        g = sim.Game(sim.POLICIES[policy], players, rules, random.Random(rng.random()))
        won = g.run()
        games.append((g, won))
    return games


@pytest.mark.parametrize("policy", sorted(sim.POLICIES))
def test_game_invariants(policy):
    for g, won in run_games(policy, sims=150):
        assert g.loss in (None, "doom", "all_down", "source"), f"unknown loss reason {g.loss!r}"
        assert won == (g.loss is None), "won flag inconsistent with loss reason"
        assert 0 <= g.doom, f"doom went negative: {g.doom}"
        assert g.day <= 8, f"game ran past day 7 (day={g.day})"
        for c in g.chars:
            assert 0 <= c.health <= c.max["health"], f"{c.name} health {c.health} out of range"
            assert 0 <= c.hunger <= c.max["hunger"], f"{c.name} hunger {c.hunger} out of range"
            assert 0 <= c.sanity <= c.max["sanity"], f"{c.name} sanity {c.sanity} out of range"
            if not c.down:
                assert c.health > 0 and c.sanity > 0, (
                    f"{c.name} standing with health={c.health} sanity={c.sanity}")
        for res, n in g.pool.items():
            assert n >= 0, f"resource pool went negative: {res}={n}"


def test_downed_chars_stay_consistent_on_loss():
    for g, won in run_games("turtle", sims=100, seed=7):
        if g.loss == "all_down":
            assert all(c.down for c in g.chars), "all_down loss but someone is standing"


@pytest.mark.parametrize("policy", ["balanced", "turtle"])
def test_roster_override_sweep_smoke(policy):
    """--sweep3 plumbing: every 3-character roster runs to completion with
    composition-aware policies (no James/Coco hardcode assumptions)."""
    import itertools
    import random
    for combo in itertools.combinations(sim.CHARACTERS, 3):
        g = sim.Game(sim.POLICIES[policy], 3, "new", random.Random(11), roster=list(combo))
        g.run()
        assert g.loss in (None, "doom", "all_down", "source"), (combo, g.loss)
        for c in g.chars:
            assert 0 <= c.health <= c.max["health"], (combo, c.name)


# ---------------------------------------------------------------------------
# Win-rate regression bands
#
# Baselines (agents.md, 2026-07 batch 4 calibration — batches 1-3 plus the
# Source retuned HP 10 -> 8 (the W3 knob that landed the 40-50% target)
# and the 3-player reliefs; new rules, 4 players, 3000 sims): turtle 42%,
# spread 42%, balanced 15%, court_camper 14%, with ~100% of losses on
# Days 6-7. Bands are generous — a failure means a rule constant changed
# materially, not noise.
# ---------------------------------------------------------------------------

WIN_BANDS = {
    "turtle": (0.28, 0.55),
    "spread": (0.28, 0.55),
    "balanced": (0.05, 0.28),
    "court_camper": (0.05, 0.28),
}


@pytest.mark.parametrize("policy", sorted(WIN_BANDS))
def test_win_rate_within_band(policy):
    r = sim.simulate(policy, players=4, rules="new", sims=SIMS, seed=SEED)
    lo, hi = WIN_BANDS[policy]
    assert lo <= r["win"] <= hi, (
        f"{policy} win rate {r['win']:.1%} outside [{lo:.0%}, {hi:.0%}] — a rule or "
        "constant changed the balance (or the sim drifted). If intentional, rerun the "
        "full 3000-sim baseline, update agents.md, and adjust these bands.")


def test_old_ruleset_still_frozen():
    """--rules old is the control group; it must not drift. Spread under old
    rules won ~100% of games at the 2026-07 baseline."""
    r = sim.simulate("spread", players=4, rules="old", sims=200, seed=SEED)
    assert r["win"] >= 0.9, (
        f"old-rules spread win rate {r['win']:.1%} < 90% — the frozen pre-2026-07 "
        "ruleset appears to have been modified.")
