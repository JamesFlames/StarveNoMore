"""Every ongoing rule the game announces must be a rule something enforces.

`tests/test_lua_reachability.py` guards the same bug class one level up: a
function nothing calls. This module guards the level below it — a *flag*
nothing reads. The shape is identical and so is the cost:

    gameState.ongoingDawnEffects.moveCostPlus1 = true
    broadcastEvent("warn", "Movement costs +1 action this day.")

Nothing errors. The Active Rules panel lists it. The Dawn card says it. The
players play around it. And `doMove` has never heard of it, so the day plays
out exactly like any other. That is worse than a crash: a crash gets fixed,
and this gets played around for a whole campaign.

A 2026-07 audit found eleven at once — every one of them set by a real Dawn
card, printed in EFFECT_RULES, and read by nothing outside the panel that
prints it: restNoHealth, moveCostPlus1, reducedActions, sportCourtHungerCost,
rainSanityCost, rainFireDisabled, reducedCapacity, recipeBonusHunger,
homeSanityBonus, doomReduced, noDoomThisDawn.

The last two are the instructive ones. Both were readable in principle and
still could not work: BeginDay advances Doom and only afterwards reveals the
Dawn card, so a flag set at reveal always missed the advance it was named
for. "Has a reader" is the floor this test enforces, not a proof of
correctness — but the floor is where all eleven were sitting.

Scope: a flag is enforced if some non-`ui_` Lua file reads it. `ui_` files
are excluded on purpose: printing a rule in the panel is what the panel is
for, and it is exactly what all eleven were doing instead of happening.
"""
import os
import re

from conftest import LUA_DIR, read_text

# Flags that legitimately have no rules-code reader. Each needs a reason, and
# "we haven't got round to it" is not one of them — that is the bug this
# module exists to catch.
DISPLAY_ONLY = {
    # Boss-presence bookkeeping. The rules that matter (festering, victory,
    # persistent HP) key off the standee on the map and gameState.bossHP /
    # bossesDefeated, never off these; they exist so the Active Rules panel
    # can name what is standing out there. Only sourceActive qualifies:
    # victory reads bossesDefeated.source and isBossOnMap, never this.
    # (deerclopsActive and eyeActive were both listed here and both wrong —
    # the Eye's each-Dawn extra threat has always read eyeActive, and
    # simulate_balance.py had been modelling the Deerclops' double Sanity
    # drain all along while only the Lua had not.)
    "sourceActive",
    # Set at reveal purely so the panel can report what the card already did
    # to the Doom track this Dawn (the cards apply the change themselves —
    # see dawn_effects_phase4.lua for why a deferred read cannot work).
    "doomReduced",
    "noDoomThisDawn",
    # P3_ALLY_MISSING's +1 action is real, but beginDayPhase reads it off
    # gameState.missingAlly (banked at reveal, before the budget reset wipes
    # it) rather than off this flag; the flag is what the panel shows.
    "missingAllyBonus",
}


def _effect_rule_flags():
    """The flag names EFFECT_RULES (ui_rules.lua) promises to the players."""
    src = read_text(os.path.join(LUA_DIR, "ui_rules.lua"))
    body = src.split("EFFECT_RULES = {", 1)[1].split("\n}", 1)[0]
    return [m.group(1) for m in re.finditer(r"^\s*([A-Za-z]\w*)\s*=", body, re.M)]


def _readers(flag):
    """Files outside ui_* that READ gameState.ongoingDawnEffects.<flag>."""
    hits = []
    for dirpath, _dirs, files in os.walk(LUA_DIR):
        for fn in sorted(files):
            if not fn.endswith(".lua") or fn.startswith("ui_"):
                continue
            path = os.path.join(dirpath, fn)
            for i, line in enumerate(read_text(path).splitlines(), 1):
                code = line.split("--", 1)[0]
                if not re.search(r"ongoingDawnEffects\.%s\b" % flag, code):
                    continue
                # An assignment is the card setting it, not a rule reading it.
                if re.search(r"ongoingDawnEffects\.%s\s*=(?!=)" % flag, code):
                    continue
                hits.append("%s:%d" % (fn, i))
    return hits


def test_every_announced_effect_has_an_enforcer():
    orphans = []
    for flag in _effect_rule_flags():
        if flag in DISPLAY_ONLY:
            continue
        if not _readers(flag):
            orphans.append(flag)

    assert not orphans, (
        "%d ongoing effect(s) that the Active Rules panel promises and no "
        "rule enforces:\n  %s\n\nThe Dawn card sets the flag, EFFECT_RULES "
        "prints it, and nothing in lua/ (outside ui_*) ever reads it — so "
        "the rule is announced to the table and then does not happen. Wire "
        "it into the action, phase step or resolver it describes, or add it "
        "to DISPLAY_ONLY in this file with the reason it is display-only."
        % (len(orphans), "\n  ".join(sorted(orphans)))
    )


def test_display_only_allowlist_has_no_stale_entries():
    """An allowlist nobody prunes is where the next orphan hides."""
    announced = set(_effect_rule_flags())
    stale = sorted(DISPLAY_ONLY - announced)
    assert not stale, (
        "DISPLAY_ONLY names flags EFFECT_RULES no longer announces: %s — "
        "remove them from tests/test_lua_effect_flags.py" % stale
    )


def test_a_display_only_flag_that_gains_an_enforcer_leaves_the_list():
    """DISPLAY_ONLY asserts a flag is panel decoration. Once a rule reads it,
    that claim is false, and the entry starts shielding a real flag from the
    check above — which is exactly how `deerclopsActive` would have gone back
    to sleep after being wired up."""
    promoted = sorted(f for f in DISPLAY_ONLY if _readers(f))
    assert not promoted, (
        f"listed as display-only but a rule now reads them: {promoted} — "
        "remove them from DISPLAY_ONLY in tests/test_lua_effect_flags.py")


def test_every_flag_a_dawn_card_sets_is_announced():
    """The other direction: a flag set by a card but absent from EFFECT_RULES
    is a rule in force that the Active Rules panel never mentions."""
    announced = set(_effect_rule_flags())
    # Bookkeeping flags that are deliberately not player-facing rules.
    internal = re.compile(r"^(doom\d+|.*Defeated|charlie(Paused|Everywhere))$")
    missing = {}
    effects_dir = os.path.join(LUA_DIR, "effects")
    for fn in sorted(os.listdir(effects_dir)):
        if not fn.endswith(".lua"):
            continue
        src = read_text(os.path.join(effects_dir, fn))
        for i, line in enumerate(src.splitlines(), 1):
            code = line.split("--", 1)[0]
            m = re.search(r"ongoingDawnEffects\.(\w+)\s*=\s*true", code)
            if m and m.group(1) not in announced and not internal.match(m.group(1)):
                missing.setdefault(m.group(1), "%s:%d" % (fn, i))

    assert not missing, (
        "Dawn card(s) set ongoing flag(s) that EFFECT_RULES (ui_rules.lua) "
        "never shows the players:\n  "
        + "\n  ".join("%s  (%s)" % (k, v) for k, v in sorted(missing.items()))
        + "\n\nA rule in force that the Active Rules panel omits is a rule "
          "the table has to remember from one line of chat. Add its text to "
          "EFFECT_RULES and its place to EFFECT_RULE_ORDER."
    )
