"""The XML <-> Lua UI contract.

TTS fails silently when Lua targets a UI id that isn't in the XML, or when an
XML onClick names a Lua function that doesn't exist. Both directions are
checked here with literal-string extraction (dynamically-built ids/handlers
are out of scope and whitelisted explicitly where they exist).
"""
import re

# UI.* methods whose first literal string argument is an element id
UI_ID_CALL_RE = re.compile(
    r'UI\.(?:show|hide|setAttribute|setAttributes|getAttribute|getValue|setValue|setClass)'
    r'\(\s*"([A-Za-z0-9_\-]+)"\s*[,)]'
)

XML_ID_RE = re.compile(r'\bid\s*=\s*"([^"]+)"')
XML_HANDLER_RE = re.compile(r'\bon(?:Click|ValueChanged|EndEdit|Submit|MouseEnter|MouseExit)\s*=\s*"([^"]+)"')

# Lua function definitions: `function name(` and `name = function(`
LUA_FN_DEF_RE = re.compile(r"\bfunction\s+([A-Za-z0-9_]+)\s*\(|\b([A-Za-z0-9_]+)\s*=\s*function\b")

CLICK_FN_RE = re.compile(r'click_function\s*=\s*"([A-Za-z0-9_]+)"')

# Handlers/ids created dynamically (verified by reading the code, not testable
# by literal match). Add here only after confirming the dynamic definition.
DYNAMIC_HANDLER_WHITELIST = set()
DYNAMIC_ID_WHITELIST = set()


def defined_functions(lua_sources):
    defined = set()
    for src in lua_sources.values():
        for a, b in LUA_FN_DEF_RE.findall(src):
            defined.add(a or b)
        # _G["name"] = ... dynamic global definitions
        defined |= set(re.findall(r'_G\["([A-Za-z0-9_]+)"\]\s*=', src))
    return defined


def test_lua_ui_ids_exist_in_xml(lua_sources, xml_source):
    xml_ids = set(XML_ID_RE.findall(xml_source)) | DYNAMIC_ID_WHITELIST
    problems = []
    for rel, src in lua_sources.items():
        for lineno, line in enumerate(src.splitlines(), 1):
            for uid in UI_ID_CALL_RE.findall(line):
                if uid not in xml_ids:
                    problems.append(f"{rel}:{lineno}: UI call targets id {uid!r} not present in any xml/ file")
    assert not problems, "\n".join(problems)


def test_xml_handlers_are_defined_in_lua(lua_sources, xml_source):
    defined = defined_functions(lua_sources) | DYNAMIC_HANDLER_WHITELIST
    problems = []
    for raw in set(XML_HANDLER_RE.findall(xml_source)):
        # strip optional "Global/" prefix and "(...)" argument suffix
        name = raw.split("/")[-1].split("(")[0].strip()
        if name and name not in defined:
            problems.append(f"XML handler {raw!r}: no Lua function named {name!r}")
    assert not problems, "\n".join(sorted(problems))


def test_createbutton_click_functions_are_defined(lua_sources):
    defined = defined_functions(lua_sources) | DYNAMIC_HANDLER_WHITELIST
    problems = []
    for rel, src in lua_sources.items():
        for lineno, line in enumerate(src.splitlines(), 1):
            for name in CLICK_FN_RE.findall(line):
                if name not in defined:
                    problems.append(f"{rel}:{lineno}: click_function {name!r} is not defined anywhere")
    assert not problems, "\n".join(problems)


def test_xml_ids_unique(xml_source):
    ids = XML_ID_RE.findall(xml_source)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate element ids across the xml/ files: {dupes}"
