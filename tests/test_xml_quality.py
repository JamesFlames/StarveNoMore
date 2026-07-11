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

from conftest import ART_DIR, LUA_DIR, ROOT, XML_DIR, all_lua_files, all_xml_files, read_text

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
