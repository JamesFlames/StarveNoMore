"""Generic guards for the *classes* of bug that keep surfacing in playtests.

Each test here encodes a lesson from a real breakage so the whole family is
caught before the next one ships, not just the one instance that was fixed:

  - objects spawned overlapping (player boards spawned 3 units apart at
    scale 3 => physics flung the stack across the table);
  - text-gadget objects rotated 180 (the Quick Start notecard read upside
    down; the same convention trips cards vs. counters/notecards);
  - dark-on-dark / low-contrast button text (the recurring readability
    complaints);
  - object handles dereferenced in a takeObject callback without a pcall
    guard (the "cannot access field getNickname of userdata" crash, hit
    three separate times: pry, dawn reveal, threat reveal).

See docs/tts-runtime.md for the underlying engine behaviours.
"""
import json
import os
import re

from conftest import LUA_DIR, ROOT, XML_DIR, all_lua_files, all_xml_files, read_text


def _load_save():
    path = os.path.join(ROOT, "saves", "StarveNoMore.json")
    assert os.path.isfile(path), "saves/StarveNoMore.json missing — run scripts/build_save.py"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _category(tags):
    """The functional group a laid-out object belongs to (PlayerBoard,
    Location, ...) — the namespaced tag, e.g. 'PlayerBoard:James' -> 'PlayerBoard'."""
    for t in tags:
        if ":" in t:
            return t.split(":", 1)[0]
    return None


# --------------------------------------------------------------------------
# 1. Objects laid out in a group must not overlap at spawn.
# --------------------------------------------------------------------------
# A Custom_Tile spans ~2 world units per unit of Transform scale (the 2.5-scale
# location tiles are the "5x5-unit" footprint the board art is drawn around),
# so two tiles clear each other only when their centres are at least
# (scaleX_a + scaleX_b) apart. Player boards violated this — scale 3, spaced 3.

def test_grouped_tiles_do_not_overlap_at_spawn():
    save = _load_save()
    groups = {}
    for o in save["ObjectStates"]:
        if o.get("Name") != "Custom_Tile":
            continue
        cat = _category(o.get("Tags", []))
        if cat in ("PlayerBoard", "Location"):
            t = o["Transform"]
            groups.setdefault(cat, []).append(
                (o.get("Nickname") or o["Name"], t["posX"], t["posZ"], t["scaleX"], t["scaleZ"]))

    problems = []
    for cat, items in groups.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                na, xa, za, sxa, sza = items[i]
                nb, xb, zb, sxb, szb = items[j]
                dx, dz = abs(xa - xb), abs(za - zb)
                # Clear if separated on EITHER axis by the summed half-widths
                # (half-width ~= scale, since width ~= 2*scale).
                if dx < (sxa + sxb) and dz < (sza + szb):
                    problems.append(
                        f"{cat}: '{na}' and '{nb}' overlap "
                        f"(centres dx={dx:.1f} dz={dz:.1f}, need dx>={sxa+sxb:.0f} or dz>={sza+szb:.0f})")
    assert not problems, (
        "objects in a laid-out group overlap at spawn — TTS physics will shove "
        "the stack apart across the table:\n  " + "\n  ".join(problems))


# --------------------------------------------------------------------------
# 2. Text-gadget objects must render upright (rotY ~ 0), not 180.
# --------------------------------------------------------------------------
# Notecards / Counters print engine text that reads right-side-up at rotY=0
# (unlike flat card/tile ART, which needs 180 or a pre-rotated image). The
# Quick Start notecard shipped at rotY=180 and read upside down for weeks.

def test_text_gadgets_are_upright():
    save = _load_save()
    bad = []
    for o in save["ObjectStates"]:
        if o.get("Name") in ("Notecard", "Counter"):
            ry = o["Transform"]["rotY"] % 360
            if not (ry < 1 or ry > 359):
                bad.append(f"{o.get('Nickname') or o['Name']} ({o['Name']}) has rotY={ry:.0f}")
    assert not bad, (
        "text-gadget objects rotated away from upright (they print engine text "
        "that reads right-side-up only at rotY=0):\n  " + "\n  ".join(bad))


# --------------------------------------------------------------------------
# 3. Button text must have enough contrast against its own background.
# --------------------------------------------------------------------------
_BUTTON_RE = re.compile(r"<Button\b[^>]*?>", re.S)
_MIN_CONTRAST = 3.0   # WCAG AA for large text; current lowest real button is 3.79


def _relative_luminance(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 8:
        h = h[:6]
    elif len(h) == 4:
        h = "".join(c * 2 for c in h[:3])
    elif len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _contrast(a, b):
    la, lb = _relative_luminance(a), _relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _alpha(hex_color):
    h = hex_color.lstrip("#")
    return int(h[6:8], 16) / 255 if len(h) == 8 else 1.0


def test_button_text_contrast():
    problems = []
    for filename in all_xml_files():
        src = read_text(os.path.join(XML_DIR, filename))
        for m in _BUTTON_RE.finditer(src):
            tag = m.group(0)
            text = re.search(r'\btext="([^"]*)"', tag)
            color = re.search(r'\bcolor="(#[0-9A-Fa-f]+)"', tag)
            tcolor = re.search(r'\btextColor="(#[0-9A-Fa-f]+)"', tag)
            idm = re.search(r'\bid="([^"]+)"', tag)
            # Skip invisible click-overlays (empty text or transparent paint).
            if not (text and text.group(1).strip() and color and tcolor):
                continue
            if _alpha(color.group(1)) < 0.25 or _alpha(tcolor.group(1)) < 0.25:
                continue
            c = _contrast(color.group(1), tcolor.group(1))
            if c < _MIN_CONTRAST:
                problems.append(
                    f"{filename}: button {idm.group(1) if idm else '?'} contrast "
                    f"{c:.2f} < {_MIN_CONTRAST} (bg {color.group(1)} / text {tcolor.group(1)})")
    assert not problems, (
        "buttons with text too low-contrast against their own background "
        "(dark-on-dark / light-on-light reads as disabled or unreadable):\n  "
        + "\n  ".join(problems))


# --------------------------------------------------------------------------
# 4. takeObject callbacks must guard the object handle with pcall/safecall.
# --------------------------------------------------------------------------
# A takeObject callback can fire with a DEAD handle (the object merged into a
# deck mid-flight); touching any field then throws "cannot access field X of
# userdata<LuaObject>". Every callback that dereferences its object param must
# wrap the access in pcall/safecall. This crash hit three times this session.

_CB_RE = re.compile(r"callback_function\s*=\s*function\s*\(\s*([A-Za-z_]\w*)\s*\)")
# Keywords that open an `end`/`until`-terminated block, and the closers.
_OPENERS = re.compile(r"\b(function|if|for|while|repeat)\b")
_CLOSERS = re.compile(r"\b(end|until)\b")


def _callback_body(src, start):
    """From the 'function(' at `start`, return the source of the callback body
    up to its matching close, by depth-counting block keywords."""
    depth = 0
    i = start
    seen_open = False
    while i < len(src):
        mo = _OPENERS.search(src, i)
        mc = _CLOSERS.search(src, i)
        if mo and (not mc or mo.start() < mc.start()):
            depth += 1
            seen_open = True
            i = mo.end()
        elif mc:
            depth -= 1
            i = mc.end()
            if seen_open and depth == 0:
                return src[start:i]
        else:
            break
    return src[start:i]


def test_takeobject_callbacks_guard_dead_handles():
    problems = []
    for rel in all_lua_files():
        src = read_text(os.path.join(LUA_DIR, rel))
        for m in _CB_RE.finditer(src):
            param = m.group(1)
            body = _callback_body(src, m.start())
            derefs = re.search(r"\b" + re.escape(param) + r"\s*\.\s*\w+", body)
            guarded = ("pcall" in body) or ("safecall" in body)
            if derefs and not guarded:
                line = src.count("\n", 0, m.start()) + 1
                problems.append(
                    f"{rel}:{line}: callback dereferences '{param}' without a "
                    "pcall/safecall guard (dead-handle crash risk)")
    assert not problems, (
        "takeObject callbacks touch their object handle unguarded — a handle "
        "that died mid-flight throws 'cannot access field ... of userdata':\n  "
        + "\n  ".join(problems)
        + "\n(wrap the body in pcall(function() ... end), like revealDawnCard)")
