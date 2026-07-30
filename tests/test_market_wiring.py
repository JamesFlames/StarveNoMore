"""Every Market card prints a rule. Which ones does the mod actually run?

49 craftable cards, each with an `effect` column that reads like a rule the
game enforces. A 2026-07 audit found 33 of them wired to nothing at all — and
crucially, with *no way for a player to apply them by hand either*: there is
no Use Item verb outside `items.lua`, no manual stat editor, and stats live in
`gameState` where a player cannot reach them. A crafted First Aid Kit was a
card in your hand that could not do the thing written on its face.

That is not the same as a card the table resolves socially (Duct Tape's
"repair a broken Item" has nothing to repair; the Notebook is a prop). So this
module does not demand every card be scripted. It demands the split be
**written down**: each card is either wired, or named below with the reason it
is not. The failure mode this prevents is the one that happened — 33 cards
quietly doing nothing, indistinguishable from 33 cards deliberately left to
the table.

`M_BANDAGE` is the worked example of why it matters. Its effect line went
unimplemented for the whole project, and separately `doStabilize` charged a
Bandage it never checked for. Two halves of one card, both missing, neither
visible.
"""
import csv
import os
import re

from conftest import CONTENT, LUA_DIR, read_text


def _market_rows():
    with open(os.path.join(CONTENT, "cards_market.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _lua_corpus():
    out = {}
    for dirpath, _dirs, files in os.walk(LUA_DIR):
        for fn in sorted(files):
            if fn.endswith(".lua") and fn != "market_data.lua":
                out[fn] = read_text(os.path.join(dirpath, fn))
    return out


# Cards deliberately not scripted, each with the reason. "Nobody got round to
# it" is not a reason — that is the bug this module exists to surface.
UNWIRED = {
    # --- single-use, needs machinery the mod does not have -----------------
    "M_CIRCLE_OF_SALT": "boss movement bans; bosses are placed by Dawn effects, not moved",
    "M_CAMERA": "reorder the top 3 of the Threat deck — no deck-reorder UI",
    "M_WHISTLE": "pulls other characters to your tile; moving someone else's standee",
    "M_PEPPER_SPRAY": "pushes a Threat card to another tile; threats have no scripted position",
    "M_FIRST_GENERATION_PHONE": "peek any deck — doPeek already covers this for James",
    # --- persistent passives: a hook in another system ---------------------
    "M_TOOLBOX": "craft cost -1; would need a discount seam in doCraft",
    "M_BICYCLE": "Move costs 0 Hunger; a hook in doMove",
    "M_HEADPHONES": "negate 1 Sanity loss per Day; needs a per-day damage filter",
    "M_WARM_BLANKET": "sleep +1 Sanity and negate 1 Charlie damage; hooks in resolveSleep + resolveCharlieAttack",
    "M_STUFFED_ANIMAL": "+2 Sanity at Tick; a hook in resolveTick",
    "M_PHOTO_ALBUM": "storytelling +1 Sanity to the tile; a hook in resolveStorytelling",
    "M_MUSIC_PLAYER": "storytelling +2 Sanity once per Night; as above, plus a once-per-night flag",
    "M_RADIO": "adjacent allies +1 Sanity at Night; as above, across tiles",
    "M_KEYS": "lock a house against entering Threats for 1 Night; a hook in the night draw",
    "M_REINFORCED_DOOR": "+2 defense at a house tile; 'defense' is not a stat the mod has",
    "M_BARRICADE": "+1 defense at a court; doBarricade is the scripted version of this",
    "M_WATCHTOWER": "see the top of the Threat deck from this tile; a passive peek",
    "M_THERMOS": "carry a cooked Recipe for later; needs a stored-recipe slot",
    "M_RABBIT_FOOT": "reroll any 1 die once per game; needs a reroll prompt in the dice seam",
    "M_DOG_LEASH": "pull an adjacent ally to your tile once per Day",
    "M_ENERGY_DRINK_CASE": "1 Energy Drink per Dawn; a hook in BeginDay",
    # --- genuinely the table's ------------------------------------------
    "M_DUCT_TAPE": "repair a broken Item — the mod has no item-damage concept",
    "M_NOTEBOOK": "a prop for tracking effects by hand; the Rules panel does this",
    "M_SLINGSHOT": "attack an adjacent tile; ranged combat is not a mechanic here",
}


def _wired_ids(corpus):
    """Card ids some Lua file outside the generated data actually reads."""
    wired = set()
    market_data = read_text(os.path.join(LUA_DIR, "market_data.lua"))
    # WEAPON_DICE is a generic, data-driven hook: being in it IS the wiring.
    wired |= set(re.findall(r"WEAPON_DICE\.(M_\w+)", market_data))
    for src in corpus.values():
        wired |= set(re.findall(r"\bM_[A-Z0-9_]+\b", src))
    return wired


def test_every_market_card_is_wired_or_listed():
    rows = _market_rows()
    wired = _wired_ids(_lua_corpus())

    missing = sorted(
        r["id"] for r in rows
        if r["id"] not in wired and r["id"] not in UNWIRED
    )
    assert not missing, (
        f"{len(missing)} Market card(s) that nothing reads and nothing "
        f"explains:\n  " + "\n  ".join(missing)
        + "\n\nEach prints a mechanical effect on its face and the mod gives "
          "players no way to apply one by hand — there is no manual stat "
          "editor, and stats live in gameState. Either script it (a stat or "
          "Doom change belongs in USE_ITEMS, lua/items.lua) or add it to "
          "UNWIRED in this file with the reason it stays the table's job."
    )


def test_the_unwired_list_has_no_stale_entries():
    """A list nobody prunes stops being a review and becomes a place to hide."""
    ids = {r["id"] for r in _market_rows()}
    stale = sorted(set(UNWIRED) - ids)
    assert not stale, (
        f"UNWIRED names Market card(s) that no longer exist: {stale} — remove "
        "them from tests/test_market_wiring.py")


def test_a_card_that_gains_wiring_leaves_the_list():
    wired = _wired_ids(_lua_corpus())
    promoted = sorted(set(UNWIRED) & wired)
    assert not promoted, (
        f"listed as unwired but the Lua now reads them: {promoted} — remove "
        "them from UNWIRED in tests/test_market_wiring.py")


def test_use_items_match_their_printed_effect():
    """USE_ITEMS is a transcription of the `effect` column. A number that
    drifts from the card face is a rule the player is told twice, differently.
    """
    effects = {r["id"]: r["effect"] for r in _market_rows()}
    src = read_text(os.path.join(LUA_DIR, "items.lua"))
    block = src.split("USE_ITEMS = {", 1)[1].split("\n}", 1)[0]

    problems = []
    for entry in re.finditer(
            r"(M_[A-Z0-9_]+)\s*=\s*\{(.*?)\},?\s*(?=\n\s*(?:M_|$))", block, re.S):
        card_id, body = entry.group(1), entry.group(2)
        printed = effects.get(card_id, "")
        if not printed:
            problems.append(f"{card_id}: not a Market card")
            continue
        for stat, amount in re.findall(r"(health|hunger|sanity)\s*=\s*(\d+)", body):
            # The card prints "Restore 4 Health" / "2 Hunger and 1 Sanity".
            if not re.search(rf"\b{amount}\s+{stat}\b", printed, re.I):
                problems.append(
                    f"{card_id}: USE_ITEMS gives {amount} {stat}, card says {printed!r}")
        doom = re.search(r"doom\s*=\s*(-?\d+)", body)
        if doom and "Doom" not in printed:
            problems.append(f"{card_id}: USE_ITEMS moves Doom, card says {printed!r}")

    assert not problems, "USE_ITEMS drifted from cards_market.csv:\n  " + "\n  ".join(problems)
