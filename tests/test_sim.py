"""simulate_balance.py as a regression harness.

Two jobs:
 1. Enforce the docs/agents/balance-simulation.md maintenance rule mechanically: the sim mirrors
    rule constants from lua/global.lua by hand, so verify the mirror.
 2. Run seeded batches and assert invariants + broad win-rate bands, so an
    accidental rule/constant change shows up as a red test instead of a
    silently wrong balance table.
"""
import os

import pytest

import simulate_balance as sim  # scripts/ is on sys.path via conftest

import re as _re

from conftest import LUA_DIR, SCRIPTS, TESTS, read_text

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


def test_doom_thresholds_match(lua_globals):
    for key, value in sim.DOOM_THRESHOLDS.items():
        lua_value = lua_globals.eval(f"DOOM_THRESHOLDS.{key}")
        assert value == lua_value, (
            f"DOOM_THRESHOLDS.{key}: sim={value} lua={lua_value} — "
            "simulate_balance.py has drifted from global.lua")


# The sim's pool keys vs the lua resource-bag tags.
_SIM_RESOURCE_NAMES = {"Wood": "wood", "Cloth": "cloth", "Battery": "battery",
                       "EnergyDrink": "energy", "Metal": "metal", "Food": "food"}


def test_cleanse_cost_and_reduction_match(lua_globals):
    lua_cost = {k: lua_globals.eval(f'CLEANSE_COST["{k}"]')
                for k in ("Wood", "Cloth", "Battery", "EnergyDrink")}
    sim_cost = {k: sim.CLEANSE_COST.get(_SIM_RESOURCE_NAMES[k], 0) for k in lua_cost}
    assert lua_cost == sim_cost, f"Cleanse cost drift: lua={lua_cost} sim={sim_cost}"
    assert lua_globals.eval("CLEANSE_REDUCTION") == sim.CLEANSE_REDUCTION


def test_location_yields_match(lua_globals):
    # Gather now spawns tokens straight from LOCATION_YIELDS (global.lua); the
    # sim's YIELDS drives balance. Same distribution per location (order and
    # duplicates included, so Food-doubled Ellie & Luca's stays doubled).
    lua_to_sim = _SIM_RESOURCE_NAMES
    for loc, sim_names in sim.YIELDS.items():
        n = lua_globals.eval(f"#LOCATION_YIELDS.{loc}")
        lua_names = [lua_globals.eval(f"LOCATION_YIELDS.{loc}[{i}]") for i in range(1, n + 1)]
        assert sorted(lua_to_sim[r] for r in lua_names) == sorted(sim_names), (
            f"{loc}: lua={lua_names} sim={sim_names} — "
            "LOCATION_YIELDS (global.lua) drifted from simulate_balance.py YIELDS")


# ---------------------------------------------------------------------------
# Boss statlines: sim BOSSES <-> build_save.py standees <-> lua constants.
# build_save.py executes its whole build on import, so it is parsed, not
# imported; the lua constants likewise (they live outside global.lua).
# ---------------------------------------------------------------------------


def _build_save_bosses():
    src = read_text(os.path.join(SCRIPTS, "build_save.py"))
    m = _re.search(r"bosses = \[(.*?)\]", src, _re.S)
    assert m, "bosses list not found in build_save.py"
    return {name: (int(hp), int(atk))
            for name, hp, atk in _re.findall(r'\("(\w+)",\s*(\d+),\s*(\d+)\)', m.group(1))}


def test_boss_stats_match_build_save():
    standees = _build_save_bosses()
    for _day, (name, hp, atk, _loc) in sim.BOSSES.items():
        assert name in standees, f"{name} missing from build_save.py bosses list"
        assert standees[name] == (hp, atk), (
            f"{name}: build_save standee {standees[name]} != sim ({hp}, {atk})")


def test_source_constants_match_combat_lua():
    src = read_text(os.path.join(LUA_DIR, "combat.lua"))
    max_hp = int(_re.search(r"SOURCE_MAX_HP\s*=\s*(\d+)", src).group(1))
    split_hp = int(_re.search(r"SOURCE_SPLIT_HP\s*=\s*(\d+)", src).group(1))
    assert max_hp == sim.BOSSES[6][1], (
        f"Source HP: combat.lua {max_hp} != sim {sim.BOSSES[6][1]}")
    assert split_hp == sim.SOURCE_SPLIT_HP, (
        f"Source split threshold: combat.lua {split_hp} != sim {sim.SOURCE_SPLIT_HP}")


def test_treeguard_stats_match_build_save():
    src = read_text(os.path.join(LUA_DIR, "treeguard.lua"))
    m = _re.search(r"TREEGUARD_STATS\s*=\s*{[^}]*hp\s*=\s*(\d+)[^}]*attack\s*=\s*(\d+)", src)
    assert m, "TREEGUARD_STATS not parsed from treeguard.lua"
    assert _build_save_bosses()["Treeguard"] == (int(m.group(1)), int(m.group(2)))


def test_difficulty_params_invariants(lua_globals):
    """DIFFICULTY_PARAMS (global.lua) must stay internally consistent —
    every mode playable by the same loop code."""
    modes = ["story", "standard", "weekend", "nightmare"]
    for mode in modes:
        days = lua_globals.eval(f"DIFFICULTY_PARAMS.{mode}.days")
        limit = lua_globals.eval(f"DIFFICULTY_PARAMS.{mode}.doomLimit")
        assert days and days >= 1, f"{mode}: bad day count {days}"
        assert limit and limit >= 10, f"{mode}: bad doom limit {limit}"
        # every playable day maps to a phase 1..4
        lua_globals.execute(f'gameState.difficulty = "{mode}"')
        for day in range(1, int(days) + 1):
            phase = lua_globals.globals().getPhaseForDay(day)
            assert phase in (1, 2, 3, 4), f"{mode} day {day}: phase {phase}"
    lua_globals.execute("gameState.difficulty = nil")
    assert lua_globals.eval("DIFFICULTY_PARAMS.standard.days") == 7
    assert lua_globals.eval("DIFFICULTY_PARAMS.standard.doomLimit") == 30


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
# Baselines (docs/agents/balance-simulation.md, 2026-07 batch 4 calibration — batches 1-3 plus the
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
        "full 3000-sim baseline, update docs/agents/balance-simulation.md, and adjust these bands.")


def test_old_ruleset_still_frozen():
    """--rules old is the control group; it must not drift. Spread under old
    rules won ~100% of games at the 2026-07 baseline."""
    r = sim.simulate("spread", players=4, rules="old", sims=200, seed=SEED)
    assert r["win"] >= 0.9, (
        f"old-rules spread win rate {r['win']:.1%} < 90% — the frozen pre-2026-07 "
        "ruleset appears to have been modified.")


def test_sim_difficulties_mirror_the_lua_table(lua_globals):
    """DIFFICULTIES (simulate_balance.py) is the probe's copy of
    DIFFICULTY_PARAMS (global.lua). A drift here doesn't error — it silently
    means the numbers quoted in §17.2 and §20.1 were measured against a game
    nobody plays, which is the worst kind of balance bug."""
    import simulate_balance as sb

    src = read_text(os.path.join(LUA_DIR, "global.lua"))
    body = _re.search(r"DIFFICULTY_PARAMS\s*=\s*\{(.*?)\n\}", src, _re.S).group(1)
    # Anchor on `label` so nested keys (doomDelta, phaseForDay are themselves
    # tables) aren't mistaken for modes.
    lua_modes = set(_re.findall(r"^\s*(\w+)\s*=\s*\{\s*label\s*=", body, _re.M))
    assert lua_modes == set(sb.DIFFICULTIES), (
        f"modes differ — lua {sorted(lua_modes)} vs sim {sorted(sb.DIFFICULTIES)}")

    for mode, spec in sb.DIFFICULTIES.items():
        lua_globals.execute(f'gameState.difficulty = "{mode}"')
        assert lua_globals.globals().getTotalDays() == spec["days"], mode
        assert lua_globals.globals().getDoomLimit() == spec["doom_limit"], mode
        assert lua_globals.globals().getSourceMaxHP() == spec["source_hp"], mode
        # Per-phase Doom surcharge, the knob that made Nightmare winnable.
        for phase in (1, 2, 3, 4):
            want = sb.phase_delta(spec["doom_delta"], phase)
            got = lua_globals.globals().getDoomDelta(phase)
            assert got == want, f"{mode} phase {phase}: lua {got} vs sim {want}"
    lua_globals.execute("gameState.difficulty = nil")


def test_nightmare_is_winnable_but_only_just(lua_globals):
    """The point of the retune. A difficulty nobody can beat is not a
    difficulty, it is a broken mode — and a flat +1 measured at 0-6%.

    Bands are deliberately wide: this asserts the ORDERING and that Nightmare
    is off both floors, which is what §26 says a probe can certify. The exact
    magnitude needs a table (§20.2 item 10)."""
    import simulate_balance as sb

    def best(mode, sims=400):
        return max(sb.simulate(p, 4, "new", sims, 7, difficulty=mode)["win"]
                   for p in sb.POLICIES)

    story, standard, nightmare = best("story"), best("standard"), best("nightmare")
    assert nightmare > 0.08, (
        f"Nightmare best line {nightmare:.1%} — that is unwinnable, not hard")
    assert nightmare < standard, (
        f"Nightmare ({nightmare:.1%}) is not harder than Standard ({standard:.1%})")
    assert standard < story, (
        f"Standard ({standard:.1%}) is not harder than Story ({story:.1%})")
