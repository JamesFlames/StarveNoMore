"""XML UI quality gates.

TTS fails silently on all of these, so they must be caught at test time:
  - malformed XML: the whole UI vanishes with no error;
  - a literal backslash-n in an attribute renders as the two characters "\\n"
    (players saw exactly this on the setup walkthrough);
  - rgb()/rgba() color components are parsed as 0-1 FLOATS — 0-255 values
    clamp to white, which turned every "dark" panel white and made the pale
    text unreadable (the great readability bug of the first playtest);
  - an <Image image="X"> with no matching CustomUIAssets entry renders blank.
"""
import json
import os
import re
import xml.etree.ElementTree as ET

import pytest
from conftest import (
    ART_DIR,
    LUA_DIR,
    ROOT,
    XML_DIR,
    all_lua_files,
    all_xml_files,
    read_text,
)

XML_FILES = all_xml_files()

# Attribute values that look like colors, wherever they appear.
HEX_COLOR_RE = re.compile(r'="\s*(#[0-9A-Fa-f]+)\s*"')
FUNC_COLOR_RE = re.compile(r'="\s*(rgba?\([^)"]*\))\s*"')
VALID_HEX_LENGTHS = {3, 4, 6, 8}


def _bad_color_function(value):
    """Return an error string if an rgb()/rgba() value is not valid for TTS
    (every component must be a 0-1 float), else None."""
    inner = value[value.index("(") + 1:value.rindex(")")]
    parts = [p.strip() for p in inner.split(",") if p.strip()]
    if not parts:
        return f"{value!r}: empty component list"
    for p in parts:
        try:
            f = float(p)
        except ValueError:
            return f"{value!r}: non-numeric component {p!r}"
        if f > 1.0:
            return (f"{value!r}: component {p} > 1 — TTS parses rgb()/rgba() as 0-1 "
                    "floats, so this clamps to white. Use #RRGGBBAA hex instead.")
    return None


@pytest.mark.parametrize("filename", XML_FILES)
def test_xml_well_formed(filename):
    src = read_text(os.path.join(XML_DIR, filename))
    # TTS XML is a fragment list (multiple roots), so parse under a wrapper.
    try:
        ET.fromstring("<root>" + src + "</root>")
    except ET.ParseError as e:
        raise AssertionError(f"{filename} is not well-formed XML: {e}") from e


@pytest.mark.parametrize("filename", XML_FILES)
def test_no_literal_backslash_n(filename):
    """TTS renders a literal \\n in an attribute as text. Use &#10; instead."""
    src = read_text(os.path.join(XML_DIR, filename))
    bad = [f"line {i}: {line.strip()[:90]}"
           for i, line in enumerate(src.splitlines(), 1) if "\\n" in line]
    assert not bad, (f"{filename} contains literal backslash-n sequences "
                     "(use &#10; for line breaks):\n" + "\n".join(bad))


@pytest.mark.parametrize("filename", XML_FILES)
def test_xml_colors_are_tts_parseable(filename):
    src = read_text(os.path.join(XML_DIR, filename))
    problems = []
    for i, line in enumerate(src.splitlines(), 1):
        for hexval in HEX_COLOR_RE.findall(line):
            if len(hexval) - 1 not in VALID_HEX_LENGTHS:
                problems.append(f"line {i}: {hexval!r} has {len(hexval) - 1} hex digits "
                                f"(TTS accepts {sorted(VALID_HEX_LENGTHS)})")
        for funcval in FUNC_COLOR_RE.findall(line):
            err = _bad_color_function(funcval)
            if err:
                problems.append(f"line {i}: {err}")
    assert not problems, f"{filename}:\n" + "\n".join(problems)


# Lua sets colors at runtime via UI.setAttribute — same rules apply there.
LUA_COLOR_CALL_RE = re.compile(
    r'"(?:color|textColor|outline|backgroundColor)"\s*,\s*"([^"]+)"')
LUA_FUNC_COLOR_RE = re.compile(r'"(rgba?\([^)"]*\))"')


def test_lua_color_literals_are_tts_parseable():
    problems = []
    for rel in all_lua_files():
        src = read_text(os.path.join(LUA_DIR, rel))
        for i, line in enumerate(src.splitlines(), 1):
            # Any rgb()/rgba() string literal anywhere in Lua is checked.
            for funcval in LUA_FUNC_COLOR_RE.findall(line):
                err = _bad_color_function(funcval)
                if err:
                    problems.append(f"{rel}:{i}: {err}")
            # Values passed to color-ish attributes must be valid hex or rgb().
            for value in LUA_COLOR_CALL_RE.findall(line):
                if value.startswith("#"):
                    if len(value) - 1 not in VALID_HEX_LENGTHS:
                        problems.append(f"{rel}:{i}: {value!r} has {len(value) - 1} "
                                        "hex digits")
                elif not value.startswith("rgb"):
                    problems.append(f"{rel}:{i}: {value!r} is neither #hex nor rgb()")
    assert not problems, "\n".join(problems)


def _load_save():
    path = os.path.join(ROOT, "saves", "StarveNoMore.json")
    assert os.path.isfile(path), "saves/StarveNoMore.json missing — run build_save.py"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_xml_image_assets_exist():
    """Every <Image image="X"> must have a CustomUIAssets entry in the built
    save, and local asset URLs must point at files that exist."""
    names = set()
    for filename in XML_FILES:
        names |= set(re.findall(r'\bimage="([^"]+)"', read_text(os.path.join(XML_DIR, filename))))
    if not names:
        pytest.skip("no <Image image=...> elements in the XML")

    save = _load_save()
    assets = {a["Name"]: a["URL"] for a in save.get("CustomUIAssets", [])}
    missing = sorted(names - set(assets))
    assert not missing, f"XML image= names with no CustomUIAssets entry: {missing}"

    # file:/// URLs embed the build machine's absolute path — check the
    # art-relative part against this checkout instead (matches the
    # normalization test_build_output.py uses).
    broken = []
    for name in sorted(names):
        url = assets[name]
        m = re.search(r"file:///.*?/art/(.+)$", url)
        if m and not os.path.isfile(os.path.join(ART_DIR, *m.group(1).split("/"))):
            broken.append(f"{name} -> art/{m.group(1)}")
    assert not broken, "CustomUIAssets URLs with no file under art/:\n" + "\n".join(broken)


# Ids the Lua builds dynamically per character ("card" .. name etc.) — the
# literal-string contract test can't see them, so enumerate them here.
CHARACTERS = ["James", "Coco", "Rayman", "Ellie", "Luca"]
PER_CHARACTER_ID_PATTERNS = [
    "pick{}", "card{}", "charName_{}",                       # ui_setup.lua
    "rosterRow_{}", "rosterName_{}",                          # ui_banner.lua
    "rosterHealth_{}", "rosterHealthVal_{}",
    "rosterHunger_{}", "rosterHungerVal_{}",
    "rosterSanity_{}", "rosterSanityVal_{}",
]


def test_per_character_dynamic_ui_ids_exist():
    xml_ids = set()
    for filename in XML_FILES:
        xml_ids |= set(re.findall(r'\bid\s*=\s*"([^"]+)"',
                                  read_text(os.path.join(XML_DIR, filename))))
    missing = [pat.format(name)
               for name in CHARACTERS
               for pat in PER_CHARACTER_ID_PATTERNS
               if pat.format(name) not in xml_ids]
    assert not missing, (
        "per-character UI ids the Lua targets dynamically are missing from the XML: "
        + ", ".join(missing))


# --------------------------------------------------------------------------
# Screen-space layout: TTS silently draws panels over each other.
# --------------------------------------------------------------------------
# offsetXY positions an element's CENTRE, so its edges are +/- half its
# width/height from there. Get that wrong and a panel slides under another one
# with no error and no visual clue in the XML: hostControls declared height
# 310 at offsetY -150 put its top edge at y=+5 — off the top of the screen and
# behind the Phase Banner, hiding the title and the first buttons ("the end
# turn button is hidden underneath the Day 1 of 7 phase bar").

def _panels(root):
    """{id: element} for every <Panel>/<Button> with an explicit rect."""
    out = {}
    for el in root.iter():
        if el.get("id") and el.get("width") and el.get("height") and el.get("rectAlignment"):
            out[el.get("id")] = el
    return out


def _rect(el, screen=(1920, 1080)):
    """(left, top, right, bottom) in pixels, y measured DOWN from the top."""
    sw, sh = screen
    w, h = float(el.get("width")), float(el.get("height"))
    ox, oy = (float(v) for v in (el.get("offsetXY") or "0 0").split())
    align = el.get("rectAlignment", "MiddleCenter")
    ax = {"Left": 0.0, "Center": sw / 2, "Right": sw}[
        "Left" if "Left" in align else "Right" if "Right" in align else "Center"]
    ay = {"Upper": 0.0, "Middle": sh / 2, "Lower": sh}[
        "Upper" if "Upper" in align else "Lower" if "Lower" in align else "Middle"]
    cx, cy = ax + ox, ay - oy          # offsetY is positive-UP
    return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2


def _overlap(a, b):
    return (a[0] < b[2] and b[0] < a[2]) and (a[1] < b[3] and b[1] < a[3])


def test_top_anchored_panels_clear_the_phase_banner():
    """The Phase Banner is always on screen and always on top. Anything else
    anchored to the top of the screen has to start below it."""
    root = ET.fromstring("<root>" + read_text(os.path.join(XML_DIR, "hud.xml")) + "</root>")
    panels = _panels(root)
    assert "phaseBanner" in panels, "phaseBanner missing from hud.xml"
    banner = _rect(panels["phaseBanner"])

    problems = []
    for pid, el in panels.items():
        if pid == "phaseBanner" or "Upper" not in el.get("rectAlignment", ""):
            continue
        r = _rect(el)
        if r[1] < 0:
            problems.append(f"{pid}: top edge at y={r[1]:.0f} is off the top of the screen")
        if _overlap(r, banner):
            problems.append(
                f"{pid}: {tuple(round(v) for v in r)} overlaps the phase banner "
                f"{tuple(round(v) for v in banner)}")
    assert not problems, (
        "top-anchored UI hidden behind the Phase Banner:\n  " + "\n  ".join(problems)
        + "\n  remember offsetXY sets the CENTRE — the top edge is offsetY + height/2 up.")


def test_phase_banner_is_flush_with_the_top():
    """The status bar sits ON the top edge of the screen, with no margin above
    it. offsetXY sets the CENTRE, so this only holds while offsetY is exactly
    -height/2 — nudge either number alone and a gap reappears."""
    root = ET.fromstring("<root>" + read_text(os.path.join(XML_DIR, "hud.xml")) + "</root>")
    banner = _rect(_panels(root)["phaseBanner"])
    assert banner[1] == 0, (
        f"phase banner top edge is at y={banner[1]:.0f}, not 0 — it should be "
        "flush with the top of the screen (set offsetY to -height/2)")


def test_panel_heights_match_their_contents():
    """A panel taller than its content pushes its own top edge upward for no
    reason — which is how hostControls ended up under the banner."""
    root = ET.fromstring("<root>" + read_text(os.path.join(XML_DIR, "hud.xml")) + "</root>")
    problems = []
    for pid, el in _panels(root).items():
        layout = el.find("VerticalLayout")
        if layout is None:
            continue
        pad = [float(v) for v in (layout.get("padding") or "0 0 0 0").split()]
        spacing = float(layout.get("spacing") or 0)
        kids = [k for k in layout if k.get("preferredHeight")]
        if len(kids) < 2:
            continue
        need = (sum(float(k.get("preferredHeight")) for k in kids)
                + spacing * (len(kids) - 1) + pad[2] + pad[3])
        have = float(el.get("height"))
        if have < need - 1:
            problems.append(f"{pid}: height {have:.0f} but contents need {need:.0f}")
        elif have > need + 40:
            problems.append(f"{pid}: height {have:.0f} for {need:.0f} of content "
                            f"({have - need:.0f}px of dead space)")
    assert not problems, (
        "panel heights disagree with their contents:\n  " + "\n  ".join(problems))


# --------------------------------------------------------------------------
# A TTS Text overflows preferredWidth by DRAWING OVER its neighbours.
# --------------------------------------------------------------------------
# It does not wrap, clip or ellipsise inside a HorizontalLayout, so a slot
# sized for the placeholder in the XML garbles the bar as soon as the runtime
# string is longer. The Phase Banner showed "Doom 0 / 30  (next:" written
# through the active-player field.

# Longest string each banner field can carry at runtime (ui_banner.lua).
BANNER_WORST_CASE = {
    "bannerDay":    "Day 7 of 7",
    "bannerPhase":  "Dusk of the Week",
    "bannerDoom":   "Doom 30 / 30  (next: 25)",
    # Dusk's "<name> settles (<seat>)" (ui_banner.lua) is one character longer
    # than the Day's "<name>'s turn (<seat>)", so it is the worst case now.
    "bannerActive": "Rayman settles (Yellow)",
    "bannerNext":   "Click Begin Day to start Day 1",
}

# Rough advance width per character as a fraction of fontSize. Deliberately
# generous — this is a "does it obviously not fit" gate, not a text engine.
CHAR_W = 0.55


def test_phase_banner_slots_fit_their_text():
    root = ET.fromstring("<root>" + read_text(os.path.join(XML_DIR, "hud.xml")) + "</root>")
    fields = {el.get("id"): el for el in root.iter("Text") if el.get("id") in BANNER_WORST_CASE}
    missing = sorted(set(BANNER_WORST_CASE) - set(fields))
    assert not missing, f"banner field(s) {missing} vanished from hud.xml"

    problems = []
    for fid, el in fields.items():
        want = len(BANNER_WORST_CASE[fid]) * float(el.get("fontSize")) * CHAR_W
        have = float(el.get("preferredWidth"))
        if have < want:
            problems.append(
                f"{fid}: {have:.0f}px for {BANNER_WORST_CASE[fid]!r} (~{want:.0f}px) — "
                "it will draw over the next field")
    assert not problems, (
        "phase banner fields too narrow for their runtime text:\n  " + "\n  ".join(problems))


# Verbs that call spendAction() (grep lua/ for spendAction). Everything else
# takes no action: Flee is priced in Sanity, Revive in Health + a Telltale
# Heart, the Signature is once-per-game, and Peek/Rally/Pry are free perks.
# Trade is in FREE because its headline case is free — once per turn at your
# own tile; the trade dialog prices each partner individually.
COSTED_ACTIONS = {
    "actMove", "actGather", "actCraft", "actCook", "actFight", "actRest",
    "actCleanse", "actStabilize", "actDefend", "actBarricade", "actAppease",
    "actClear",
}


def _action_groups():
    root = ET.fromstring("<root>" + read_text(os.path.join(XML_DIR, "hud.xml")) + "</root>")
    bar = next(el for el in root.iter("Panel") if el.get("id") == "actionBar")
    groups = {}
    for grp in bar.iter("HorizontalLayout"):
        if grp.get("id") in ("actGroupCosted", "actGroupFree"):
            groups[grp.get("id")] = [b for b in grp if b.tag == "Button"]
    return bar, groups


def test_action_bar_groups_match_the_action_costs():
    """A button's group must match whether the verb behind it spends an action.

    The bar was one undifferentiated run, so the only way to find out that Pry
    and Rally are free while Rest and Cleanse are not was to spend an action
    finding out.
    """
    bar, groups = _action_groups()
    assert set(groups) == {"actGroupCosted", "actGroupFree"}, (
        "the action bar lost one of its two groups")

    costed = {b.get("id") for b in groups["actGroupCosted"]}
    free = {b.get("id") for b in groups["actGroupFree"]}
    assert costed == COSTED_ACTIONS, (
        f"COSTS-1 group is {sorted(costed)}; the verbs that call spendAction() "
        f"are {sorted(COSTED_ACTIONS)}. Move the button or update the set — but "
        "only after checking the Lua, not to make this pass.")
    assert not (costed & free), "a button is in both groups"

    every = {b.get("id") for b in bar.iter("Button")}
    assert every == costed | free, (
        f"action-bar buttons in neither group: {sorted(every - costed - free)}")


def test_costed_action_labels_carry_their_price():
    """...and the label says it too, for anyone reading the button and not the
    group heading above it."""
    _bar, groups = _action_groups()
    missing = [b.get("id") for b in groups["actGroupCosted"] if "(1)" not in (b.get("text") or "")]
    assert not missing, f"COSTS-1 buttons whose label omits '(1)': {missing}"
    # actSignature is relabelled at runtime to the signature's own name
    # (ui_actionbar_display.lua), so its XML placeholder is not the real label.
    stray = [b.get("id") for b in groups["actGroupFree"]
             if "(1)" in (b.get("text") or "") and b.get("id") != "actSignature"]
    assert not stray, f"FREE buttons whose label claims an action cost: {stray}"


TOOLTIP_MAX_LINE = 74


def test_tooltips_are_wrapped():
    """A TTS tooltip does not wrap — it renders as one line, however long.

    The Optional Variants panel had four of them at 243, 302, 311 and 396
    characters: a single strip of text wider than the screen, describing the
    setting the player is deciding on right now. Break with `&#10;` (the same
    entity the button labels already use).
    """
    problems = []
    for name in sorted(os.listdir(XML_DIR)):
        if not name.endswith(".xml"):
            continue
        root = ET.fromstring("<root>" + read_text(os.path.join(XML_DIR, name)) + "</root>")
        for el in root.iter():
            tip = el.get("tooltip")
            if not tip:
                continue
            for line in tip.split("\n"):
                if len(line) > TOOLTIP_MAX_LINE:
                    problems.append(
                        f"{name}:{el.get('id') or el.tag}: {len(line)}-char line "
                        f"(max {TOOLTIP_MAX_LINE}) — {line[:48]}...")
    assert not problems, (
        "tooltips with an unbroken line too long to read:\n  " + "\n  ".join(problems))


def test_every_variant_toggle_explains_itself():
    """Random Scenario was the only toggle on the Variants panel with no
    tooltip — the one setting whose name does not say what it does."""
    root = ET.fromstring("<root>" + read_text(os.path.join(XML_DIR, "setup.xml")) + "</root>")
    panel = next(el for el in root.iter("Panel") if el.get("id") == "setupStepVariants")
    missing = [b.get("id") for b in panel.iter("Button")
               if b.get("id", "").startswith("toggle") and not b.get("tooltip")]
    assert not missing, f"variant toggles with no tooltip: {missing}"


def test_phase_banner_row_fits_inside_its_panel():
    """...and the widened slots must still fit the bar, or the whole row
    overflows the panel instead of one field overflowing its slot."""
    root = ET.fromstring("<root>" + read_text(os.path.join(XML_DIR, "hud.xml")) + "</root>")
    banner = next(el for el in root.iter("Panel") if el.get("id") == "phaseBanner")
    layout = banner.find("HorizontalLayout")
    pad = [float(v) for v in (layout.get("padding") or "0 0 0 0").split()]
    spacing = float(layout.get("spacing") or 0)
    kids = [k for k in layout if k.get("preferredWidth")]
    need = (sum(float(k.get("preferredWidth")) for k in kids)
            + spacing * (len(kids) - 1) + pad[0] + pad[1])
    have = float(banner.get("width"))
    assert need <= have, (
        f"phase banner children need {need:.0f}px but the panel is {have:.0f}px — "
        "trim a slot or drop a separator; widening the panel past ~1470 pushes "
        "it off narrower screens.")


def test_phase_banner_active_field_is_not_centred():
    """bannerActive must not straddle the horizontal centre of the bar.

    TTS's own turn plate draws at the top-centre of the screen and cannot be
    hidden from a script — in Hotseat it re-enables itself whatever we do — so
    it shows through whichever banner field sits there. When that was the
    active-player field, the bar read as giving two different answers to "whose
    turn is it": ours in white over a ghosted player name. Any field may take
    the hit except this one, because only this one can be misread as the same
    statement."""
    root = ET.fromstring("<root>" + read_text(os.path.join(XML_DIR, "hud.xml")) + "</root>")
    banner = next(el for el in root.iter("Panel") if el.get("id") == "phaseBanner")
    layout = banner.find("HorizontalLayout")
    pad = [float(v) for v in (layout.get("padding") or "0 0 0 0").split()]
    spacing = float(layout.get("spacing") or 0)
    kids = [k for k in layout if k.get("preferredWidth")]

    widths = [float(k.get("preferredWidth")) for k in kids]
    row = sum(widths) + spacing * (len(kids) - 1) + pad[0] + pad[1]
    panel = float(banner.get("width"))
    centre = panel / 2.0

    x = (panel - row) / 2.0 + pad[0]      # the row is centred in the panel
    for kid, w in zip(kids, widths):
        if kid.get("id") == "bannerActive":
            assert not (x <= centre <= x + w), (
                f"bannerActive spans {x:.0f}-{x + w:.0f}px and the bar's centre "
                f"is {centre:.0f}px — TTS's turn plate will draw through it and "
                "the banner will look like it disagrees with itself. Reorder "
                "the row so a field that cannot be mistaken for a name (Doom) "
                "takes the centre.")
        x += w + spacing
