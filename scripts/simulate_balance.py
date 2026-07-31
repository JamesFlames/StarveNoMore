"""
Monte Carlo balance simulator for Starve No More.

Simulates the 7-day campaign loop with scripted team policies and reports
win rates, loss causes, Doom trajectories, and down counts. Use it to
sanity-check rule changes before human playtests (design target: 40-50%
wins on Standard for an experienced group — §20.2).

Usage:
  python scripts/simulate_balance.py                     # all policies, new rules
  python scripts/simulate_balance.py --sims 5000
  python scripts/simulate_balance.py --rules old         # pre-2026-07 ruleset
  python scripts/simulate_balance.py --players 5 --policy turtle
  python scripts/simulate_balance.py --sweep3            # all ten 3-char teams
  python scripts/simulate_balance.py --no-defence        # location defence off

Rule sets:
  new — current design: deterministic escalating Charlie (2/1 +1 per
        consecutive dark night), festering Doom (+1 per ordinary threat at
        Dawn capped at +3; bosses +2 each and Treeguard +1, uncapped),
        Doom +1 per Down, Source-mandatory victory (final boss alive at
        end of Day 7 = loss; every policy engages it), whiff-only fumbles,
        Press the Attack (pay 1 Sanity per bonus die after a hit; modeled
        against bosses while sanity > 4), boss-kill rewards (Deerclops
        Doom -2, Eye -3, +3 loot resources), Flee (1 Sanity), crowded
        floor (2 beds/house), Moonlit Salvage, Treeguard mini-boss,
        Scarcity at Doom 15. Batch 2: Nothing Left to Lose (Doom 25:
        +1 attack die for everyone, Rest heals +1 Health anywhere),
        Signature Moves (once per game: All-Nighter +3 actions on Day 6+
        with a -3 Sanity crash, Touch of Hope +4 Health emergency heal,
        Posterize deletes one non-boss threat but echoes +1 draw,
        The Feast mass-cook consuming all Food, The Speech +2 Sanity to
        all when someone is Down/below 3 Sanity), the Source splitting
        into two Terror Beaks (2/2) at <=5 HP, and the fixed Last Dawn
        (Day 7 has no Dawn-card effect). Batch 3 models only its two
        balance-touching pieces: the Sealed Basement (a one-time
        tool-gated cache at the kitchen from Day 2 — pay 1 Metal for the
        Pry Bar, gain 2 Food + 1 Wood + 1 Battery + 1 random) and the
        Wrongness token (one deferred threat lands at the Basketball
        Court at the Day-4 Dawn). Night Sounds, Dawn Dares, and the rest
        of batch 3 are PLAYTEST-ONLY: opt-in texture the sim cannot
        meaningfully evaluate. Batch 4: the Source retuned HP 10 -> 8
        (the W3 calibration knob that put the best line in the 40-50%
        band), and the 3-player reliefs (§20.1): Big Appetite costs 2
        Hunger only on days Rayman fought or moved 2+ tiles, and Loud
        needs 3+ tiles moved (both playerCount == 3 only). Batch 5:
        per-location defence (§7.1-7.5) on the counter-attack — the
        Garage and the Badminton Court roll a blocking die, the
        Basketball Court hands the threat an extra swing; --no-defence
        is the control group. Trophies remain unmodeled (reward side is
        still understated — the rebate/loot carry it).
  old — previous design: Charlie d8 Sanity + d6 Health, ghost Sanity
        drain, Doom = phase rate only, fumble per natural 1, no salvage,
        no bed limit, no Treeguard, Doom 15 slows market (no craft effect).

Model simplifications (documented deliberately — this is a dynamics probe,
not a rules engine):
  * Resources are a shared team pool (over-models trading; the design's
    same-tile trade restriction is looser here).
  * The Market is abstracted to two craft targets: Flashlights (1 Metal +
    1 Battery) and one Weapon per fighter (2 Metal + 1 Wood).
  * Dawn cards are a random minor-effect distribution; the named bosses
    arrive on schedule (Deerclops Day 4, Eye Day 5, Source Day 6) rather
    than by deck luck.
  * Night threats: 55%% Hard (HP 3-4, Atk 1-2), 45%% Soft (-1 Sanity).
  * Characters fight as a group at their tile; they flee (new rules) when
    the group is outmatched, leaving the threat to fester.
"""

import argparse
import random
import statistics
from collections import Counter

# ---------------------------------------------------------------------------
# Static data (mirrors global.lua / the design doc)
# ---------------------------------------------------------------------------

CHARACTERS = {
    "James":  dict(health=8,  hunger=6,  sanity=10, home="JamesHouse"),
    "Coco":   dict(health=6,  hunger=8,  sanity=12, home=None),
    "Rayman": dict(health=12, hunger=10, sanity=6,  home="RaymanHouse"),
    "Ellie":  dict(health=8,  hunger=10, sanity=8,  home="EllieLucaHouse"),
    "Luca":   dict(health=7,  hunger=8,  sanity=10, home="EllieLucaHouse"),
}
ROSTERS = {3: ["Coco", "Ellie", "Luca"],   # strongest 3-char team per --sweep3;
           #  the default 3p row is an upper bound — run --sweep3 for the rest
           4: ["James", "Coco", "Rayman", "Ellie"],
           5: ["James", "Coco", "Rayman", "Ellie", "Luca"]}

# Best-fighters-first, used to pick weapon carriers and the boss strike pair
# for whatever roster is in play (Rayman hits hardest; Coco is the frail
# healer, drafted last). On the standard 4p/5p rosters this resolves to
# Rayman + James — identical to the original hand-tuned policies, so the
# 4-player baselines in docs/agents/balance-simulation.md are unaffected.
FIGHTER_PRIORITY = ["Rayman", "James", "Luca", "Ellie", "Coco"]


def top_fighters(g, n=2):
    names = {c.name for c in g.alive()}
    return [f for f in FIGHTER_PRIORITY if f in names][:n]

HOUSES = ("JamesHouse", "RaymanHouse", "EllieLucaHouse")
COURTS = ("BasketballCourt", "BadmintonCourt")
CENTER = "EllieLucaHouse"

# Gather yields per location (uniform pick)
YIELDS = {
    "JamesHouse":      ["energy", "battery", "food"],
    "RaymanHouse":     ["metal", "battery", "food"],
    "EllieLucaHouse":  ["food", "food", "cloth"],
    "BasketballCourt": ["wood", "metal", "cloth"],
    "BadmintonCourt":  ["cloth", "wood", "metal"],
}

# Per-location defence (Design §7.1-7.5). MIRRORS LOCATION_DEFENSE in
# lua/global.lua and the `defense` column of content/locations.csv;
# tests/test_sim.py enforces the mirror. Positive = dice the defenders roll
# to turn counter-attack hits aside (The Net); negative = extra dice the
# threat swings, because being caught on an open court is the same rule
# pointed the other way. Read by group_fight's counter-attack, new rules only.
LOCATION_DEFENSE = {
    "JamesHouse":      0,
    "RaymanHouse":     1,
    "EllieLucaHouse":  0,
    "BasketballCourt": -1,
    "BadmintonCourt":  1,
}

DOOM_RATES = {3: [1, 1, 1, 1], 4: [1, 1, 1, 3], 5: [1, 1, 2, 2]}
PHASE_FOR_DAY = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4}

# Mirrors of lua/global.lua and lua/combat.lua — tests/test_sim.py enforces
# equality, so a rule change on either side turns into a red test.
DOOM_THRESHOLDS = {"night": 10, "scarcity": 15, "tick": 20, "anyPhaseBosses": 25}
CLEANSE_COST = {"wood": 1, "cloth": 1, "battery": 1, "energy": 1}
CLEANSE_REDUCTION = 2
SOURCE_SPLIT_HP = 5

# Last Nerve (design §10.1.1): while ANY stat is below this, Flee costs 0
# Sanity and Rest restores 1 extra. The individual-level mirror of Doom 25.
# Mirrors LAST_NERVE_THRESHOLD in lua/helpers.lua.
LAST_NERVE_THRESHOLD = 3


def last_nerve(game, char):
    """New rules only — the valve did not exist under the old ruleset, and the
    old numbers in §20.1 were measured without it."""
    if getattr(game, "rules", "new") != "new" or char.down:
        return False
    t = LAST_NERVE_THRESHOLD
    return char.health < t or char.hunger < t or char.sanity < t


BOSSES = {  # day -> (name, hp, atk, location fn)
    4: ("Deerclops", 6, 3, lambda rng: "BasketballCourt"),
    5: ("EyeOfTerror", 8, 3, lambda rng: rng.choice(HOUSES)),
    6: ("TheSource", 8, 3, lambda rng: CENTER),
}

# Difficulty modes — MIRRORS DIFFICULTY_PARAMS in lua/global.lua, which
# tests/test_sim.py guards. Difficulty and length are separate dials (§17.2):
# story/standard/nightmare are three difficulties on the same full 7-day arc,
# and weekend is a 3-day *length*. Only "standard" is calibrated; the others
# are derived offsets, and this simulator exists to bracket their ordering
# (§26 — trust the ordering, playtest the magnitude).
# doom_delta is either a flat int or a {phase: delta} dict — see getDoomDelta
# in lua/global.lua, which this mirrors.
DIFFICULTIES = {
    "story":     dict(days=7, doom_limit=35, doom_delta=0, source_hp=6, min_phase=None),
    "standard":  dict(days=7, doom_limit=30, doom_delta=0, source_hp=8, min_phase=None),
    "nightmare": dict(days=7, doom_limit=30, doom_delta={3: 1, 4: 1}, source_hp=9,
                      min_phase=2),
    "weekend":   dict(days=3, doom_limit=15, doom_delta=0, source_hp=8, min_phase=None,
                      phase_for_day={1: 1, 2: 1, 3: 2}),
}


def phase_delta(doom_delta, phase):
    """Flat int or per-phase dict → this phase's Doom surcharge."""
    if isinstance(doom_delta, dict):
        return doom_delta.get(phase, 0)
    return doom_delta or 0


class Char:
    def __init__(self, name):
        base = CHARACTERS[name]
        self.name = name
        self.home = base["home"]
        self.max = dict(health=base["health"], hunger=base["hunger"], sanity=base["sanity"])
        self.health = base["health"]
        self.hunger = base["hunger"]
        self.sanity = base["sanity"]
        self.location = self.home or CENTER
        self.down = False
        # starting hands: James begins with a Flashlight, Rayman with his
        # Basketball (improvised weapon)
        self.flashlight = (name == "James")
        self.weapon = (name == "Rayman")
        self.charlie_streak = 0

    def gain(self, stat, n):
        setattr(self, stat, min(self.max[stat], getattr(self, stat) + n))

    def lose(self, stat, n):
        setattr(self, stat, max(0, getattr(self, stat) - n))


class Threat:
    def __init__(self, rng, boss=None):
        if boss:
            self.name, self.hp, self.atk, self.boss = boss[0], boss[1], boss[2], True
        else:
            self.name, self.boss = "threat", False
            self.hp = rng.choice([3, 3, 4])
            self.atk = rng.choice([1, 1, 2])


class Game:
    def __init__(self, policy, players, rules, rng, roster=None, difficulty="standard",
                 location_defence=True):
        self.policy = policy
        self.rules = rules          # "new" | "old"
        self.rng = rng
        # Location defence is a NEW-rules mechanic; --no-defence turns it off
        # to reproduce the pre-d886c81 counter-attack for before/after diffs.
        self.location_defence = location_defence and rules == "new"
        # Difficulty is read once into plain attributes so the day loop never
        # has to know which dial a number came from.
        d = DIFFICULTIES[difficulty]
        self.difficulty = difficulty
        self.days = d["days"]
        self.doom_limit = d["doom_limit"]
        self.doom_delta = d["doom_delta"]
        self.source_hp = d["source_hp"]
        self.min_phase = d["min_phase"]
        self.phase_for_day = d.get("phase_for_day") or PHASE_FOR_DAY
        self.chars = [Char(n) for n in (roster or ROSTERS[players])]
        self.players = players
        self.doom = 0
        self.day = 1
        self.pool = Counter()       # shared team resource pool
        self.threats = {}           # location -> [Threat]
        self.downs = 0              # cumulative down events
        self.loss = None
        self.fester_log = []
        self.deerclops_alive = False
        self.treeguard = None       # location or None
        self.james_drank = False
        self.source_split = False   # the Source's one phase beat (batch 2)
        self.sig_used = set()       # Signature Moves fired (once per game each)
        self.james_crash = False    # All-Nighter's -3 Sanity, owed at Tick
        self.basement_opened = False  # the Sealed Basement cache (batch 3)
        self.wrongness_done = False   # the deferred Wrongness threat (batch 3)
        self.rayman_tiles = 0         # 3p Big Appetite relief (batch 4 W2)
        self.rayman_fought = False
        # Option utilization (design §20.2 item 8). The sim models resources
        # abstractly, so it cannot speak to individual Market items or
        # recipes — that data has to come from real session logs
        # (scripts/analyze_sessions.py). What it CAN answer are the two
        # predictions in that section that are about geometry and pricing:
        # is the Badminton Court visited less than the Basketball Court, and
        # is Cleanse ever a rational spend?
        self.action_counts = Counter()
        self.night_locations = Counter()
        # Location-defence telemetry: how often the rule actually bites.
        self.def_blocked = 0        # counter hits turned aside by cover
        self.def_extra_dice = 0     # extra swings granted by open ground
        # Boss kills by name. The Deerclops is the one the defence rule can
        # reach — it always spawns on the Basketball Court, the game's only
        # negative-defence tile — so its kill rate is the sharpest read on
        # whether exposure suppresses the boss-kill line the rebates reward.
        self.boss_kills = Counter()

    # ---------------- helpers ----------------
    def alive(self):
        return [c for c in self.chars if not c.down]

    def defence_at(self, loc):
        """Mirrors LOCATION_DEFENSE[here] in applyCounterAttack."""
        if not self.location_defence:
            return 0
        return LOCATION_DEFENSE.get(loc, 0)

    def at(self, loc):
        return [c for c in self.alive() if c.location == loc]

    def source_split_hp(self):
        """Mirrors getSourceSplitHP() in lua/global.lua."""
        return 4 if self.difficulty == "story" else SOURCE_SPLIT_HP

    def add_doom(self, n):
        # Clamped at the track's own end, not a literal 35 — Story's track is
        # 35 long, so the old constant happened to be right for exactly one
        # mode and silently over-clamped Long Weekend's 15-step track.
        self.doom = min(self.doom_limit, self.doom + n)

    def check_down(self, c):
        if not c.down and (c.health <= 0 or c.sanity <= 0):
            c.down = True
            self.downs += 1
            if self.rules == "new":
                self.add_doom(1)

    def check_source_split(self, threat, loc):
        """Source phase (design §12.6): the first time it drops to the split
        threshold or below, two Terror Beaks (2/2) peel off at its tile. The
        threshold scales with the difficulty's HP pool (Story: 6 HP, split at
        4) so the beat always keeps a 'before' phase."""
        if self.rules != "new" or threat.name != "TheSource" or self.source_split:
            return
        if 0 < threat.hp <= self.source_split_hp():
            self.source_split = True
            for _ in range(2):
                beak = Threat(self.rng)
                beak.name, beak.hp, beak.atk = "TerrorBeak", 2, 2
                self.threats.setdefault(loc, []).append(beak)

    # ---------------- combat ----------------
    def group_fight(self, fighters, threat, max_rounds=3):
        """Fight until dead, fled, or out of rounds. One day Fight action is
        a single exchange (max_rounds=1); night resolution allows a short
        running battle before the group flees. Returns True if killed."""
        rounds = 0
        while threat.hp > 0 and rounds < max_rounds:
            rounds += 1
            group = [f for f in fighters if not f.down and f.hunger >= 3]
            if not group:
                return False
            if any(f.name == "Rayman" for f in group):
                self.rayman_fought = True
            dice = 0
            for f in group:
                d = 1 + (1 if f.name == "Rayman" else 0) + (1 if f.weapon else 0)
                if f.name == "Rayman" and f.location == "BasketballCourt":
                    d += 1
                if self.rules == "new" and self.doom >= DOOM_THRESHOLDS["anyPhaseBosses"]:
                    d += 1   # Nothing Left to Lose (Doom 25 buff)
                dice += d
            rolls = [self.rng.randint(1, 6) for _ in range(dice)]
            hits = sum(1 for r in rolls if r >= 5)
            ones = sum(1 for r in rolls if r == 1)
            if self.rules == "new":
                if hits == 0 and ones > 0:
                    tank = max(group, key=lambda f: f.health)
                    tank.lose("health", 1)
                    self.check_down(tank)
            else:
                for i in range(ones):
                    f = group[i % len(group)]
                    f.lose("health", 1)
                    self.check_down(f)
            threat.hp -= hits
            # Press the Attack (new rules, §12.5): after landing a hit,
            # fighters may pay 1 Sanity per bonus die until one misses.
            # Policy: press only bosses, and only while Sanity stays above 4
            # (the burst tool the mandatory Source fight was built for).
            if self.rules == "new" and hits > 0 and threat.hp > 0 and threat.boss:
                for f in group:
                    while threat.hp > 0 and f.sanity > 4:
                        f.lose("sanity", 1)
                        if self.rng.randint(1, 6) >= 5:
                            threat.hp -= 1
                        else:
                            break
            # Source phase beat fires on the freshly applied damage (batch 2)
            self.check_source_split(threat, group[0].location)
            if threat.hp <= 0:
                for f in group:
                    f.gain("sanity", 1)
                # Boss rewards (new rules, design_batch1.md §2): the kill
                # visibly rescues the week — Doom rebate + loot shower.
                if threat.boss:
                    self.boss_kills[threat.name] += 1
                if self.rules == "new" and threat.boss:
                    rebate = {"Deerclops": 2, "EyeOfTerror": 3}.get(threat.name, 0)
                    if rebate:
                        self.doom = max(0, self.doom - rebate)
                    for _ in range(3):
                        self.pool[self.rng.choice(["wood", "metal", "cloth", "food"])] += 1
                return True
            # counter-attack. Where the fight is decides how well the group
            # can cover (§7.1-7.5, new rules) — mirrors applyCounterAttack in
            # lua/combat_resolve.lua: a negative defence is folded in as extra
            # dice BEFORE the swing, a positive one is a block roll made only
            # when something actually landed.
            atk = threat.atk
            defence = self.defence_at(group[0].location)
            if defence < 0 and atk > 0:
                atk -= defence
                self.def_extra_dice += -defence
            hits = sum(1 for _ in range(atk) if self.rng.randint(1, 6) >= 5)
            if defence > 0 and hits > 0:
                blocked = min(hits, sum(1 for _ in range(defence)
                                        if self.rng.randint(1, 6) >= 5))
                hits -= blocked
                self.def_blocked += blocked
            for _ in range(hits):
                tank = max((f for f in group if not f.down), key=lambda f: f.health, default=None)
                if tank:
                    tank.lose("health", 1)
                    self.check_down(tank)
            # flee check: outmatched group bails
            group_alive = [f for f in group if not f.down]
            if group_alive and min(f.health for f in group_alive) <= 2:
                for f in group_alive:
                    if self.rules == "new":
                        # Flee: 1 tile, 1 Sanity — but FREE on the Last Nerve
                        # (design §10.1.1), which is exactly when an outmatched
                        # group bails, so this branch is where the valve bites.
                        f.lose("sanity", 0 if last_nerve(self, f) else 1)
                    else:
                        f.lose("hunger", 1)   # old flee: pays Hunger
                    self.check_down(f)
                return False
        return threat.hp <= 0

    # ---------------- day phases ----------------
    def dawn(self):
        self.rayman_tiles = 0        # 3p Big Appetite relief: daily reset
        self.rayman_fought = False
        phase = self.phase_for_day[min(self.day, max(self.phase_for_day))]
        if self.min_phase:
            phase = max(self.min_phase, phase)
        rate = DOOM_RATES[self.players][phase - 1] + phase_delta(self.doom_delta, phase)
        self.add_doom(rate)

        # Festering (new rules): ordinary threats +1 each capped at +3;
        # bosses +2 each and the Treeguard +1, uncapped (Design §15.1 —
        # ignoring THE monster is never the cheap line).
        ordinary = sum(1 for v in self.threats.values() for t in v if not t.boss)
        bosses = sum(1 for v in self.threats.values() for t in v if t.boss)
        self.fester_log.append(ordinary + bosses + (1 if self.treeguard else 0))
        if self.rules == "new":
            fester_doom = min(3, ordinary) + 2 * bosses + (1 if self.treeguard else 0)
            if fester_doom:
                self.add_doom(fester_doom)

        # Moonlit Salvage (new rules)
        if self.rules == "new":
            for c in self.alive():
                if c.location in COURTS:
                    for _ in range(2):
                        self.pool[self.rng.choice(YIELDS[c.location])] += 1

        # Haunted (new rules): personal threat for Sanity < 3
        if self.rules == "new":
            for c in self.alive():
                if 0 < c.sanity < 3:
                    t = Threat(self.rng)
                    if not self.group_fight([c], t):
                        pass  # fled: hallucinations never fester

        # Dawn card: random minor effect. Day 7 under new rules is THE LAST
        # DAWN — fixed and toneless, never a penalty (design_batch2.md §3).
        # The Last Dawn (§15.7) is the FINAL day's, whatever that day is —
        # Long Weekend's Day 3 gets it too.
        if not (self.rules == "new" and self.day == self.days):
            roll = self.rng.random()
            if roll < 0.40:
                for c in self.alive():
                    c.lose("sanity", 1)
                    self.check_down(c)
            elif roll < 0.60:
                self.pool["food"] = max(0, self.pool["food"] - len(self.alive()))
            elif roll < 0.80:
                for c in self.alive():
                    c.lose("hunger", 1)

        # The Wrongness (new rules, batch 3): ONE card among the 16 in the
        # Phase-2 deck defers a threat to the next Dawn at the Basketball
        # Court. Two Phase-2 draws -> ~12.5% of games see it; ~55% of
        # deferred draws are Hard threats that stick and fester (a Soft one
        # resolves at the empty court and discards — no lasting effect).
        if self.rules == "new" and self.day == 4 and not self.wrongness_done:
            self.wrongness_done = True
            if self.rng.random() < (2 / 16) * 0.55:
                self.threats.setdefault("BasketballCourt", []).append(Threat(self.rng))

        # Scheduled bosses. New rules: no arrival Doom — a boss charges the
        # track by STAYING (+2 fester per Dawn), not by showing up. Arrival
        # doom on top of uncapped festering double-charged the fight.
        if self.day in BOSSES:
            name, hp, atk, locfn = BOSSES[self.day]
            if name == "TheSource":
                hp = self.source_hp      # difficulty knob (§17.2 / §20.1)
            loc = locfn(self.rng)
            self.threats.setdefault(loc, []).append(Threat(self.rng, boss=(name, hp, atk)))
            if name == "Deerclops":
                self.deerclops_alive = True
            if self.rules == "old":
                self.add_doom({"Deerclops": 1, "EyeOfTerror": 2, "TheSource": 3}[name])

    def craft_cost_ok(self, cost):
        """cost: Counter. Scarcity (new rules, doom>=15): +1 any resource."""
        need = sum(cost.values()) + (1 if (self.rules == "new" and self.doom >= DOOM_THRESHOLDS["scarcity"]) else 0)
        if sum(self.pool.values()) < need:
            return False
        return all(self.pool[k] >= v for k, v in cost.items())

    def craft(self, cost):
        for k, v in cost.items():
            self.pool[k] -= v
        if self.rules == "new" and self.doom >= DOOM_THRESHOLDS["scarcity"]:
            extra = max(self.pool, key=lambda k: self.pool[k])
            self.pool[extra] -= 1

    def fire_signatures(self):
        """Once-per-game Signature Moves (§6.7) with simple trigger policies.
        All-Nighter (James) and Posterize (Rayman) live in day_actions /
        dusk_and_night — they are action- and night-economy moves."""
        if self.rules != "new":
            return
        names = {c.name for c in self.alive()}
        # Touch of Hope: emergency button — someone standing is at <=2 Health.
        if "Coco" in names and "Coco" not in self.sig_used:
            hurt = min(self.alive(), key=lambda c: c.health)
            if hurt.health <= 2:
                hurt.gain("health", 4)
                self.sig_used.add("Coco")
        # The Speech: gated — only while an ally is Down or below 3 Sanity.
        if "Luca" in names and "Luca" not in self.sig_used:
            if any(c.down for c in self.chars) or any(c.sanity < 3 for c in self.alive()):
                for c in self.alive():
                    c.gain("sanity", 2)
                self.sig_used.add("Luca")
        # The Feast: at the crockpot, team hungry, pantry stocked — mass cook,
        # then the pantry is empty (all Food consumed).
        ellie = next((c for c in self.alive() if c.name == "Ellie"), None)
        if ellie and "Ellie" not in self.sig_used and ellie.location == CENTER:
            hungry = sum(1 for c in self.alive() if c.hunger <= c.max["hunger"] - 4)
            if hungry >= 2 and self.pool["food"] >= 4 and self.pool["wood"] >= 2:
                cooks = 0
                while cooks < 3 and self.pool["food"] >= 1 and self.pool["wood"] >= 1:
                    self.act_cook(ellie)
                    cooks += 1
                self.pool["food"] = 0
                self.sig_used.add("Ellie")

    def day_actions(self):
        self.james_drank = False
        stations = self.policy.stations(self)
        for c in self.alive():
            actions = 3
            # All-Nighter (James's Signature): +3 actions for the endgame
            # push, billed -3 Sanity at Tick.
            if self.rules == "new" and c.name == "James" \
               and "James" not in self.sig_used and self.day >= 6:
                self.sig_used.add("James")
                self.james_crash = True
                actions += 3
            # move to day station (1 hop = 1 action + 1 hunger; via center = 2)
            target = stations.get(c.name, c.location)
            hops = 0 if target == c.location else (1 if CENTER in (target, c.location) else 2)
            if c.name == "Rayman" and hops == 2:
                hops_cost = 1   # Speed: 2 tiles per action (still 2 Hunger)
                c.lose("hunger", 2)
                actions -= hops_cost
                c.location = target
                self.rayman_tiles += 2
            elif hops:
                c.lose("hunger", hops)
                actions -= hops
                c.location = target
                if c.name == "Rayman":
                    self.rayman_tiles += hops
            # free: eat raw to stay functional (not Ellie)
            while c.name != "Ellie" and c.hunger < 4 and self.pool["food"] > 0:
                self.pool["food"] -= 1
                c.gain("hunger", 1)
                c.lose("sanity", 1)
                self.check_down(c)
            # free: James drinks (The Stash keeps him stocked)
            if c.name == "James" and self.pool["energy"] > 0:
                self.pool["energy"] -= 1
                c.gain("sanity", 2)
                self.james_drank = True
            # free: anyone shaky sips an Energy Drink (leave one for James)
            if c.sanity <= 4 and self.pool["energy"] > 1:
                self.pool["energy"] -= 1
                c.gain("sanity", 2)

            while actions > 0 and not c.down:
                actions -= self.policy.act(self, c)
        self.fire_signatures()

    def act_gather(self, c):
        self.action_counts["Gather"] += 1
        loc = c.location
        if self.rules == "new" and self.treeguard == loc:
            return  # the Treeguard guards the timber
        if loc == "JamesHouse" and self.pool["energy"] < 4:
            self.pool["energy"] += 2  # The Stash (§7.1 — any gatherer may)
            return
        self.pool[self.rng.choice(YIELDS[loc])] += 1
        if c.name == "Ellie" and loc == CENTER:
            self.pool["food"] += 1  # Knows the Pantry

    def act_cook(self, c):
        self.action_counts["Cook"] += 1
        cost_food = 1 if c.name == "Ellie" else 2  # Crockpot Master
        self.pool["food"] -= cost_food
        self.pool["wood"] -= 1
        for e in self.at(c.location):
            if e.name == "Ellie" and e.hunger == e.max["hunger"]:
                continue
            bonus = 1 if (c.name == "Ellie" and e is not c) else 0
            e.gain("hunger", 4 + bonus)
            e.gain("sanity", 2 + bonus)

    # ---------------- night ----------------
    def dusk_and_night(self):
        berths = self.policy.berths(self)
        for c in self.alive():
            target = berths.get(c.name, c.location)
            if target != c.location:
                # dusk scramble: 1 tile (through-center moves settled during day)
                c.lose("hunger", 1)
                c.location = target
                if c.name == "Rayman":
                    self.rayman_tiles += 1

        # Where the team actually SLEEPS is the sharpest read on whether a
        # location is doing work (§20.2 item 8): the standing prediction is
        # that the Badminton Court is visited less than the Basketball Court,
        # because it shares Moonlit Salvage but carries the highest threat
        # rate and no Rayman synergy.
        for c in self.alive():
            self.night_locations[c.location] += 1

        # Treeguard wakes at Dusk of Day 4 (new rules)
        if self.rules == "new" and self.day == 4 and self.treeguard is None:
            self.treeguard = self.rng.choice(COURTS)

        rayman_moved = True  # policies move him almost every day; Loud applies
        # 3p Loud relief (batch 4 W2, §20.1): at 3 players Loud needs 3+
        # tiles moved, not any move — a short errand stays quiet.
        if self.rules == "new" and self.players == 3:
            rayman_moved = self.rayman_tiles >= 3

        for loc in set(c.location for c in self.alive()):
            occupants = self.at(loc)
            rate = 0 if loc in HOUSES else 1
            if self.doom >= DOOM_THRESHOLDS["night"]:
                rate += 1
            if len(occupants) == 1 and loc in COURTS:
                rate += 1
            if self.rules == "new" and rayman_moved and any(c.name == "Rayman" for c in occupants):
                rate += 1
            for _ in range(rate):
                if self.rng.random() < 0.55:
                    self.threats.setdefault(loc, []).append(Threat(self.rng))
                else:
                    victim = self.rng.choice(occupants)
                    victim.lose("sanity", 1)
                    self.check_down(victim)

            # fight what's here (policy decides whether to engage bosses);
            # unfought Hard threats get one attack on a random occupant —
            # "must be fought or fled" isn't optional.
            for t in list(self.threats.get(loc, [])):
                # Posterize (Rayman's Signature): dunk one meaty non-boss
                # threat out of existence; the echo draws +1 here tonight.
                if self.rules == "new" and not t.boss and t.hp >= 3 \
                   and "Rayman" not in self.sig_used \
                   and any(c.name == "Rayman" for c in occupants):
                    self.sig_used.add("Rayman")
                    self.threats[loc].remove(t)
                    if self.rng.random() < 0.55:
                        self.threats.setdefault(loc, []).append(Threat(self.rng))
                    else:
                        victim = self.rng.choice(occupants)
                        victim.lose("sanity", 1)
                        self.check_down(victim)
                    continue
                # The Source is never skippable under new rules (§16.3.3):
                # every sane team engages the mandatory boss.
                must_fight = self.rules == "new" and t.name == "TheSource"
                if t.boss and not self.policy.fight_bosses and not must_fight:
                    victim = self.rng.choice(occupants)
                    if self.rng.randint(1, 6) >= 5:
                        victim.lose("health", 1)
                        self.check_down(victim)
                    continue
                if self.group_fight(occupants, t):
                    self.threats[loc].remove(t)
                    if t.name == "Deerclops":
                        self.deerclops_alive = False

            # Charlie: per the implementation (night.lua), the check only
            # fires at courts or where threats were drawn — a quiet house
            # is dark but sheltered.
            charlie_here = loc in COURTS or rate > 0
            for c in occupants:
                if c.down or c.name == "Coco":
                    continue
                if not charlie_here or c.flashlight:
                    c.charlie_streak = 0
                    continue
                if self.rules == "new":
                    c.lose("sanity", 2 + c.charlie_streak)
                    c.lose("health", 1 + c.charlie_streak)
                    c.charlie_streak += 1
                else:
                    c.lose("sanity", self.rng.randint(1, 8))
                    c.lose("health", self.rng.randint(1, 6))
                self.check_down(c)

        self.sleep()
        self.tick()

    def sleep(self):
        # crowded floor (new rules): 2 beds per house
        floor = set()
        if self.rules == "new":
            for loc in HOUSES:
                sleepers = self.at(loc)
                if len(sleepers) > 2:
                    sleepers.sort(key=lambda c: (c.home != loc, c.sanity))
                    floor.update(c.name for c in sleepers[2:])
        for c in self.alive():
            loc = c.location
            if c.name in floor:
                pass
            elif c.home == loc:
                c.gain("sanity", 1)
                c.gain("hunger", 1)
                c.gain("health", 1)
            elif loc in HOUSES and len(self.at(loc)) > 1:
                c.gain("sanity", 1)
            if c.name == "Coco" and loc not in HOUSES and len(self.at(loc)) == 1:
                c.lose("sanity", 3)
                self.check_down(c)
        # Luca's storytelling
        luca = next((c for c in self.alive() if c.name == "Luca"), None)
        if luca and len(self.at(luca.location)) > 1:
            for c in self.at(luca.location):
                c.gain("sanity", 1)

    def tick(self):
        coco = next((c for c in self.alive() if c.name == "Coco"), None)
        for c in self.alive():
            hunger_loss = 2 if c.name == "Rayman" else 1
            # 3p Big Appetite relief (batch 4 W2, §20.1): at 3 players, the
            # -2 only applies on days Rayman fought or moved 2+ tiles.
            if c.name == "Rayman" and self.players == 3 and self.rules == "new" \
               and not self.rayman_fought and self.rayman_tiles < 2:
                hunger_loss = 1
            sanity_loss = 1
            if self.doom >= DOOM_THRESHOLDS["tick"]:
                sanity_loss += 1
            if self.deerclops_alive:
                sanity_loss *= 2
            if coco and c is not coco and c.location == coco.location:
                sanity_loss = max(0, sanity_loss - 1)
            c.lose("hunger", hunger_loss)
            c.lose("sanity", sanity_loss)
            if c.hunger <= 0:
                c.lose("health", 1)
            if c.name == "James" and not self.james_drank:
                c.lose("sanity", 2)
            if c.name == "James" and self.james_crash:
                c.lose("sanity", 3)   # the All-Nighter's bill comes due
                self.james_crash = False
            self.check_down(c)
        # old rules: ghost drain
        if self.rules == "old":
            for g in self.chars:
                if g.down:
                    for c in self.at(g.location):
                        c.lose("sanity", 1)
                        self.check_down(c)

    # ---------------- run ----------------
    def trace_state(self, label):
        if not getattr(self, "trace", False):
            return
        chars = "  ".join(
            f"{c.name}[{'DOWN' if c.down else ''}H{c.health}/Hu{c.hunger}/S{c.sanity}@{c.location[:9]}]"
            for c in self.chars)
        threats = {loc: len(ts) for loc, ts in self.threats.items() if ts}
        print(f"D{self.day} {label:<6} doom={self.doom:<3} pool={dict(self.pool)} "
              f"threats={threats} tg={self.treeguard}\n    {chars}")

    def run(self):
        for self.day in range(1, self.days + 1):
            self.dawn()
            self.trace_state("dawn")
            if self.doom >= self.doom_limit:
                self.loss = "doom"
                return False
            if not self.alive():
                self.loss = "all_down"
                return False
            self.day_actions()
            self.policy.special(self)
            self.trace_state("day")
            self.dusk_and_night()
            self.trace_state("night")
            if self.doom >= self.doom_limit:
                self.loss = "doom"
                return False
            if not self.alive():
                self.loss = "all_down"
                return False
        # New rules (Design §16.3.3): the Source is mandatory. If the final
        # boss still stands at the end of Day 7, survival wasn't enough.
        if self.rules == "new":
            for ts in self.threats.values():
                if any(t.name == "TheSource" for t in ts):
                    self.loss = "source"
                    return False
        return True


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------

class Policy:
    """Base: gather-focused, cook when possible, rest when shaky."""
    name = "base"
    fight_bosses = False

    def stations(self, g):   # day locations
        return {}

    def berths(self, g):     # night locations
        return {}

    def act(self, g, c):
        """One action; returns actions spent (always 1 here)."""
        # revive a co-located Down friend (Telltale Heart: cloth+battery+food,
        # cook pays 2 Health — collapsed into one action here)
        for d in g.chars:
            if d.down and d.location == c.location and \
               g.pool["cloth"] >= 1 and g.pool["battery"] >= 1 and g.pool["food"] >= 1:
                g.pool["cloth"] -= 1
                g.pool["battery"] -= 1
                g.pool["food"] -= 1
                c.lose("health", 2)
                g.check_down(c)
                if not c.down:
                    d.down = False
                    d.health = max(1, d.max["health"] // 2)
                    d.hunger = max(1, d.max["hunger"] // 2)
                    d.sanity = max(1, d.max["sanity"] // 2)
                return 1
        # cook if at crockpot and stocked
        cost_food = 1 if c.name == "Ellie" else 2
        hungry = any(e.hunger < e.max["hunger"] - 3 for e in g.at(c.location))
        if c.location == CENTER and g.pool["food"] >= cost_food and g.pool["wood"] >= 1 and hungry:
            g.act_cook(c)
            return 1
        # craft flashlight for the lightless
        if not c.flashlight and g.craft_cost_ok(Counter(metal=1, battery=1)):
            g.craft(Counter(metal=1, battery=1))
            c.flashlight = True
            return 1
        # weapon for the roster's best fighters
        if c.name in top_fighters(g) and not c.weapon and g.craft_cost_ok(Counter(metal=2, wood=1)):
            g.craft(Counter(metal=2, wood=1))
            c.weapon = True
            return 1
        # Sealed Basement (new rules, batch 3): a fixed tool-gated cache at
        # the kitchen — pay a Pry Bar's worth of metal once, from Day 2.
        if g.rules == "new" and not g.basement_opened and g.day >= 2 \
           and c.location == CENTER and g.craft_cost_ok(Counter(metal=1)):
            g.craft(Counter(metal=1))
            g.basement_opened = True
            g.pool["food"] += 2
            g.pool["wood"] += 1
            g.pool["battery"] += 1
            g.pool[g.rng.choice(["wood", "metal", "cloth", "food"])] += 1
            return 1
        # cleanse when doom presses (cost/effect are the mirrored constants)
        bundle = Counter(CLEANSE_COST)
        if g.doom >= 14 and all(g.pool[k] >= v for k, v in bundle.items()):
            for k, v in bundle.items():
                g.pool[k] -= v
            g.doom = max(0, g.doom - CLEANSE_REDUCTION)
            g.action_counts["Cleanse"] += 1
            return 1
        # rest if shaky. Last Nerve (design §10.1.1, new rules only): with any
        # stat below 3, Rest restores 1 extra. Mirrored from doRest in
        # lua/actions.lua — tests/test_sim.py guards the pair.
        if c.sanity <= 4 or c.health <= 3:
            g.action_counts["Rest"] += 1
            c.gain("sanity", 2 + (1 if last_nerve(g, c) else 0))
            # home bonus — or anywhere under Nothing Left to Lose (Doom 25)
            if c.home == c.location or (g.rules == "new" and g.doom >= DOOM_THRESHOLDS["anyPhaseBosses"]):
                c.gain("health", 1)
            return 1
        # fight festering threats here during the day (1 action = 1 exchange);
        # the Source is mandatory under new rules, whatever the policy
        for t in list(g.threats.get(c.location, [])):
            if not t.boss or self.fight_bosses or \
               (g.rules == "new" and t.name == "TheSource"):
                g.action_counts["Fight"] += 1
                if g.group_fight(g.at(c.location), t, max_rounds=1):
                    g.threats[c.location].remove(t)
                    if t.name == "Deerclops":
                        g.deerclops_alive = False
                return 1
        g.act_gather(c)
        return 1

    def special(self, g):
        pass


class Turtle(Policy):
    """Everyone stacks at Ellie & Luca's, day and night. Ignores the map."""
    name = "turtle"

    def stations(self, g):
        return {c.name: CENTER for c in g.alive()}

    def berths(self, g):
        return {c.name: CENTER for c in g.alive()}


class Spread(Policy):
    """Gather at courts by day, everyone sleeps at their own home."""
    name = "spread"

    def stations(self, g):
        s = {}
        for c in g.alive():
            if c.name == "James":
                s[c.name] = "JamesHouse"     # work The Stash + batteries
            elif c.name == "Rayman":
                s[c.name] = COURTS[0]
            else:
                s[c.name] = CENTER
        return s

    def berths(self, g):
        return {c.name: (c.home or CENTER) for c in g.alive()}


class Balanced(Policy):
    """Pairs at night, fights bosses, appeases the Treeguard, cleanses.

    Boss response under the uncapped boss fester (+2/dawn):
      * Deerclops/Eye: the strike pair (Rayman + James) converges by DAY
        and chips with group exchanges, but sleeps somewhere safe —
        sleeping at the boss tile is how strike pairs die.
      * The Source (mandatory, §16.3.3): all hands. It spawns at the
        center house, so the whole team stations AND sleeps there; night
        resolution's multi-round group fight is what actually kills it."""
    name = "balanced"
    fight_bosses = True

    def _boss_locs(self, g):
        return [loc for loc, ts in g.threats.items() if any(t.boss for t in ts)]

    def _source_loc(self, g):
        return next((loc for loc, ts in g.threats.items()
                     if any(t.name == "TheSource" for t in ts)), None)

    def stations(self, g):
        s = {}
        boss_locs = self._boss_locs(g)
        source_loc = self._source_loc(g)
        strike = top_fighters(g)             # Rayman+James on the full roster
        for c in g.alive():
            if source_loc:
                s[c.name] = source_loc       # the final boss: all hands
            elif boss_locs and c.name in strike:
                s[c.name] = boss_locs[0]
            elif c.name == "James":
                s[c.name] = "JamesHouse"     # stash + batteries fuel the team
            elif c.name == "Coco":
                s[c.name] = COURTS[0]
            else:
                s[c.name] = CENTER
        return s

    def berths(self, g):
        source_loc = self._source_loc(g)
        if source_loc:
            return {c.name: source_loc for c in g.alive()}
        # Everyone defaults to their own home; homeless Coco joins the kitchen.
        b = {c.name: (c.home or CENTER) for c in g.alive()}
        # Rayman never sleeps alone — his Loud noise needs witnesses. Send the
        # spare body: Coco (homeless) > James > Luca (Ellie keeps the kitchen).
        # On the 4p/5p rosters this reproduces the original pairing exactly.
        names = {c.name for c in g.alive()}
        if "Rayman" in names:
            for witness in ("Coco", "James", "Luca"):
                if witness in names:
                    b[witness] = "RaymanHouse"
                    break
        return b

    def special(self, g):
        # appease the Treeguard the day after it wakes
        if g.rules == "new" and g.treeguard and g.pool["wood"] >= 2:
            g.pool["wood"] -= 2
            g.treeguard = None


class CourtCamper(Balanced):
    """Balanced, but Rayman sleeps at a court for the Moonlit Salvage."""
    name = "court_camper"

    def berths(self, g):
        b = super().berths(g)
        rayman = next((c for c in g.alive() if c.name == "Rayman"), None)
        # boss duty outranks salvage greed
        if rayman and rayman.flashlight and not self._boss_locs(g) \
           and not self._source_loc(g):
            b["Rayman"] = COURTS[0]
        return b


class NetCamper(CourtCamper):
    """court_camper with one tile changed: the salvage camp is the BADMINTON
    Court, not the Basketball Court.

    This policy exists to answer the §20.2 item-8 question the sim could not
    previously reach — every other policy hardcodes COURTS[0], so the
    Badminton Court had never been stood on in a simulated game. It is the
    controlled A/B for location defence (§7.1-7.5): identical play, one
    berth moved, and the tile differs in exactly the three things that
    should decide it — defence (+1 vs -1), night threat rate (2 vs 1), and
    Rayman's Court Master (+1 attack die at Basketball only). If the Net is
    worth its threat rate, this policy beats court_camper; if it loses, the
    Net is a consolation prize on a tile nobody should sleep on."""
    name = "net_camper"

    def berths(self, g):
        b = super().berths(g)
        if b.get("Rayman") == COURTS[0]:
            b["Rayman"] = COURTS[1]
        return b


POLICIES = {p.name: p for p in (Turtle(), Spread(), Balanced(), CourtCamper(),
                                NetCamper())}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def simulate(policy_name, players, rules, sims, seed, roster=None, difficulty="standard",
             location_defence=True):
    rng = random.Random(seed)
    wins = 0
    losses = Counter()
    dooms, downs, festers, loss_days = [], [], [], []
    blocked, extra_dice = [], []
    actions_total, nights_total, kills_total = Counter(), Counter(), Counter()
    for _ in range(sims):
        g = Game(POLICIES[policy_name], players, rules, random.Random(rng.random()),
                 roster=roster, difficulty=difficulty, location_defence=location_defence)
        won = g.run()
        wins += won
        if not won:
            losses[g.loss] += 1
            loss_days.append(g.day)
        dooms.append(g.doom)
        downs.append(g.downs)
        festers.append(statistics.mean(g.fester_log) if g.fester_log else 0)
        blocked.append(g.def_blocked)
        extra_dice.append(g.def_extra_dice)
        actions_total.update(g.action_counts)
        nights_total.update(g.night_locations)
        kills_total.update(g.boss_kills)
    return dict(
        win=wins / sims,
        loss_doom=losses["doom"] / sims,
        loss_all_down=losses["all_down"] / sims,
        loss_source=losses["source"] / sims,
        doom=statistics.mean(dooms),
        downs=statistics.mean(downs),
        fester=statistics.mean(festers),
        # Location defence (§7.1-7.5): counter hits cover turned aside, and
        # extra swings open ground handed out, per game.
        def_blocked=statistics.mean(blocked),
        def_extra_dice=statistics.mean(extra_dice),
        boss_kills={k: v / sims for k, v in kills_total.items()},
        # W3 calibration gate: losses should cluster on Days 6-7 (a
        # near-miss finish, not a mid-week strangle).
        late_loss=(sum(1 for d in loss_days if d >= 6) / len(loss_days)) if loss_days else 0.0,
        # Option utilization (§20.2 item 8), per game
        actions_per_game={k: v / sims for k, v in actions_total.items()},
        nights_per_game={k: v / sims for k, v in nights_total.items()},
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--sims", type=int, default=2000)
    ap.add_argument("--players", type=int, default=4, choices=(3, 4, 5))
    ap.add_argument("--rules", default="new", choices=("new", "old"))
    ap.add_argument("--policy", default=None, choices=list(POLICIES))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--trace", action="store_true",
                    help="run a single game and print a day-by-day log")
    ap.add_argument("--sweep3", action="store_true",
                    help="composition sweep: every 3-character team under one "
                         "policy (--policy, default balanced). Answers: is "
                         "every 3-char subset viable, or is a sanity-support "
                         "character (Coco/Luca) mandatory?")
    ap.add_argument("--difficulty", default="standard", choices=list(DIFFICULTIES),
                    help="which mode to simulate (§17.2). story/standard/nightmare "
                         "are difficulties on the full 7-day arc; weekend is a "
                         "3-day length.")
    ap.add_argument("--utilization", action="store_true",
                    help="option-utilization report (§20.2 item 8): action mix "
                         "and where the team actually sleeps. Tests the two "
                         "standing predictions the sim can reach — is the "
                         "Badminton Court doing less work than the Basketball "
                         "Court, and is Cleanse ever a rational spend? Item- "
                         "and recipe-level data needs real logs: see "
                         "scripts/analyze_sessions.py.")
    ap.add_argument("--sweep-difficulty", action="store_true",
                    help="run every mode and print them together — the check "
                         "that the difficulty ORDERING is monotonic. Per §26, "
                         "trust this ordering and playtest the magnitude.")
    ap.add_argument("--no-defence", dest="defence", action="store_false",
                    help="switch off the per-location defence roll (§7.1-7.5) — "
                         "the control group for it, reproducing the flat "
                         "counter-attack the sim modeled before the rule "
                         "existed. Run both and diff.")
    args = ap.parse_args()
    defence = args.defence

    if args.utilization:
        names = [args.policy] if args.policy else list(POLICIES)
        print(f"Option utilization — {args.sims} games/policy, {args.players} players, "
              f"mode={args.difficulty}\n")
        for name in names:
            r = simulate(name, args.players, args.rules, args.sims, args.seed,
                         difficulty=args.difficulty, location_defence=defence)
            print(f"[{name}]  win {r['win']*100:.1f}%")
            acts = r["actions_per_game"]
            total = sum(acts.values()) or 1
            print("  actions per game (share):")
            for act, n in sorted(acts.items(), key=lambda kv: kv[1]):
                print(f"    {act:<12} {n:>6.2f}  ({100*n/total:>4.1f}%)")
            nights = r["nights_per_game"]
            nt = sum(nights.values()) or 1
            print("  character-nights per location (defence in brackets):")
            for loc, n in sorted(nights.items(), key=lambda kv: kv[1]):
                d = LOCATION_DEFENSE.get(loc, 0)
                tag = f"{d:+d}" if d else " 0"
                print(f"    {loc:<18} {tag}  {n:>6.2f}  ({100*n/nt:>4.1f}%)")
            kills = ", ".join(f"{k} {v:.2f}" for k, v in sorted(r["boss_kills"].items()))
            print(f"  boss kills per game: {kills or 'none'}")
            print(f"  location defence: {r['def_blocked']:.2f} hits blocked, "
                  f"{r['def_extra_dice']:.2f} extra swings taken per game")
            print()
        print("Reading this (§20.2 item 8):\n"
              "  * CLEANSE — testable here, and the answer is stark: it is ~1.5% of\n"
              "    actions at best and 0.00 for two policies. A 4-resource bundle plus\n"
              "    an action for Doom -2 competes badly against boss rebates of -2/-3\n"
              "    that also pay spoils and a Trophy.\n"
              "  * BADMINTON COURT — the four original policies all hardcode\n"
              "    COURTS[0] (Basketball, for Rayman's Court Master), so their zero\n"
              "    is an artifact of the policy set, not a finding. net_camper is the\n"
              "    control that moves exactly that one berth: read its win% against\n"
              "    court_camper's, not these night counts. Its answer so far is that\n"
              "    the Net does not pay for the tile's threat rate — but a bot that\n"
              "    cannot value 'fight where you are covered' is the weakest kind of\n"
              "    witness, so this stays a table question.\n"
              "Item-, recipe- and Visitor-level utilization needs real session logs:\n"
              "  python scripts/analyze_sessions.py")
        return

    if args.sweep_difficulty:
        names = [args.policy] if args.policy else list(POLICIES)
        print(f"Starve No More difficulty sweep — {args.sims} games/cell, "
              f"{args.players} players, rules={args.rules}")
        print("story/standard/nightmare are the full 7-day arc; weekend is 3 days "
              "(a length, not a difficulty).\n")
        print(f"{'mode':<12}{'days':>6}{'doom':>6}{'srcHP':>7}  " +
              "".join(f"{n:>16}" for n in names))
        for mode in DIFFICULTIES:
            d = DIFFICULTIES[mode]
            cells = []
            for name in names:
                r = simulate(name, args.players, args.rules, args.sims, args.seed,
                             difficulty=mode, location_defence=defence)
                cells.append(f"{r['win']*100:>15.1f}%")
            print(f"{mode:<12}{d['days']:>6}{d['doom_limit']:>6}{d['source_hp']:>7}  "
                  + "".join(cells))
        return

    if args.sweep3:
        from itertools import combinations
        policy = args.policy or "balanced"
        print(f"Starve No More 3-character composition sweep — {args.sims} games/team, "
              f"policy={policy}, rules={args.rules}\n")
        print(f"{'team':<24}{'win%':>7}{'loss:doom':>11}{'loss:down':>11}"
              f"{'loss:source':>13}{'avg doom':>10}{'avg downs':>11}")
        rows = []
        for combo in combinations(CHARACTERS, 3):
            r = simulate(policy, 3, args.rules, args.sims, args.seed, roster=list(combo),
                         difficulty=args.difficulty, location_defence=defence)
            rows.append((combo, r))
        rows.sort(key=lambda cr: -cr[1]["win"])
        for combo, r in rows:
            team = "+".join(combo)
            print(f"{team:<24}{r['win']*100:>6.1f}%{r['loss_doom']*100:>10.1f}%"
                  f"{r['loss_all_down']*100:>10.1f}%{r['loss_source']*100:>12.1f}%"
                  f"{r['doom']:>10.1f}{r['downs']:>11.2f}")
        return

    if args.trace:
        g = Game(POLICIES[args.policy or "balanced"], args.players, args.rules,
                 random.Random(args.seed), difficulty=args.difficulty,
                 location_defence=defence)
        g.trace = True
        won = g.run()
        print("RESULT:", "WIN" if won else f"LOSS ({g.loss})")
        return

    names = [args.policy] if args.policy else list(POLICIES)
    print(f"Starve No More balance sim — {args.sims} games/policy, "
          f"{args.players} players, rules={args.rules}, mode={args.difficulty}, "
          f"defence={'on' if defence else 'OFF'}\n")
    print(f"{'policy':<14}{'win%':>7}{'loss:doom':>11}{'loss:down':>11}{'loss:source':>13}"
          f"{'avg doom':>10}{'avg downs':>11}{'fester/dawn':>13}{'late-loss%':>12}"
          f"{'blocked':>9}{'exposed':>9}")
    for name in names:
        r = simulate(name, args.players, args.rules, args.sims, args.seed,
                     difficulty=args.difficulty, location_defence=defence)
        print(f"{name:<14}{r['win']*100:>6.1f}%{r['loss_doom']*100:>10.1f}%"
              f"{r['loss_all_down']*100:>10.1f}%{r['loss_source']*100:>12.1f}%{r['doom']:>10.1f}"
              f"{r['downs']:>11.2f}{r['fester']:>13.2f}{r['late_loss']*100:>11.1f}%"
              f"{r['def_blocked']:>9.2f}{r['def_extra_dice']:>9.2f}")
    if defence:
        print("\nblocked = counter hits cover turned aside per game; exposed = extra "
              "swings\nopen ground handed the threats per game (§7.1-7.5). "
              "Diff against --no-defence.")


if __name__ == "__main__":
    main()
