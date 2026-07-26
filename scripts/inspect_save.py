"""inspect_save.py — read a TTS save like a debugger, not like a JSON blob.

The fastest way to answer "what actually happened in the user's session":
TTS autosaves (TS_AutoSave*.json in the TTS Saves folder) carry BOTH the
live gameState (LuaScriptState) and every object's real position. This tool
prints the useful views so nobody has to hand-write JSON spelunking again.

Usage (repo root):
    python scripts/inspect_save.py                    # built save: state + flags
    python scripts/inspect_save.py --live             # newest TTS autosave instead
    python scripts/inspect_save.py PATH               # any save file
    python scripts/inspect_save.py --objects gather   # object table (filter optional)
    python scripts/inspect_save.py --band             # objects sunk in the tabletop (invisible!)
    python scripts/inspect_save.py --error 2517       # map "<Global:2517>" to source file:line

--error reads the BUILT save's Lua bundle (the concatenation build_save.py
made), so run it against the same build the error came from.
"""

import argparse
import glob
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUILT_SAVE = os.path.join(REPO_ROOT, "saves", "StarveNoMore.json")

TTS_SAVE_DIRS = [
    os.path.expandvars(r"%USERPROFILE%\Documents\My Games\Tabletop Simulator\Saves"),
    os.path.expandvars(r"%OneDrive%\Documents\My Games\Tabletop Simulator\Saves"),
]

# Mirror of TABLE_SURFACE_Y in build_save.py: the glass table's playing
# surface. Objects at 0 < y < surface are INSIDE the tabletop — invisible
# until physics or a player fishes them out. (Objects at y < 0 are the
# deliberate under-table library; the main board and hand zones are fine.)
TABLE_SURFACE_Y = 1.55
# The main board is a thin tile resting ON the table, so its CENTRE sits
# inside the band while its top face is above it - exempt it by tag.
BAND_EXEMPT_NAMES = {"Custom_Board", "HandTrigger"}
BAND_EXEMPT_TAGS = {"MainBoard"}


def newest_live_save():
    candidates = []
    for d in TTS_SAVE_DIRS:
        if os.path.isdir(d):
            candidates += glob.glob(os.path.join(d, "TS_AutoSave*.json"))
            p = os.path.join(d, "StarveNoMore.json")
            if os.path.isfile(p):
                candidates.append(p)
    if not candidates:
        sys.exit("no TTS saves found under: " + " | ".join(TTS_SAVE_DIRS))
    return max(candidates, key=os.path.getmtime)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def show_state(save):
    st = save.get("LuaScriptState", "")
    if not st:
        print("no LuaScriptState (fresh, never-played save)")
        return
    gs = json.loads(st)
    print(f"day {gs.get('day')}  phase {gs.get('phase')}  subPhase {gs.get('subPhase')}  "
          f"doom {gs.get('doom')}  difficulty {gs.get('difficulty')}  "
          f"started {gs.get('started')}  activeColor {gs.get('activeColor')}")
    for color, ch in (gs.get("activeChars") or {}).items():
        print(f"  {color:7s} {ch.get('name', '?'):7s} "
              f"H {ch.get('health')}/{ch.get('maxHealth')}  "
              f"U {ch.get('hunger')}/{ch.get('maxHunger')}  "
              f"S {ch.get('sanity')}/{ch.get('maxSanity')}  "
              f"at {ch.get('location')}  actions {ch.get('actionsLeft')}"
              + ("  DOWN" if ch.get("down") else ""))
    ongoing = [k for k, v in (gs.get("ongoingDawnEffects") or {}).items() if v]
    if ongoing:
        print("  ongoing effects:", ", ".join(sorted(ongoing)))
    dawn = gs.get("activeDawn")
    if dawn:
        print("  active dawn:", dawn.get("title"))
    tail = (gs.get("messageLog") or [])[-5:]
    if tail:
        print("  last messages:")
        for e in tail:
            print(f"    [{e.get('c')}] {e.get('m')}")


def iter_objects(save):
    for o in save.get("ObjectStates", []):
        yield o


def show_objects(save, needle):
    needle = (needle or "").lower()
    for o in iter_objects(save):
        nick = o.get("Nickname", "")
        tags = ",".join(o.get("Tags", []))
        hay = (nick + " " + tags + " " + o.get("Name", "")).lower()
        if needle and needle not in hay:
            continue
        t = o["Transform"]
        contained = len(o.get("ContainedObjects", []))
        print(f"{(nick or o.get('Name', '?'))[:36]:38s} "
              f"pos ({t['posX']:7.2f} {t['posY']:5.2f} {t['posZ']:7.2f})  "
              f"rot ({t['rotX']:.0f} {t['rotY']:.0f} {t['rotZ']:.0f})  "
              f"{'locked ' if o.get('Locked') else '       '}"
              f"{('holds ' + str(contained)) if contained else '':9s} {tags}")


def show_band(save):
    bad = []
    for o in iter_objects(save):
        y = o["Transform"]["posY"]
        if 0 < y < TABLE_SURFACE_Y and o.get("Name") not in BAND_EXEMPT_NAMES:
            bad.append((o.get("Nickname") or o.get("Name"), round(y, 2)))
    if bad:
        print(f"OBJECTS INSIDE THE TABLETOP (0 < y < {TABLE_SURFACE_Y}) — these are "
              "invisible on the table until moved:")
        for nick, y in bad:
            print(f"  {nick}  y={y}")
    else:
        print(f"clean: nothing inside the tabletop band (0 < y < {TABLE_SURFACE_Y})")


def show_error_line(save, lineno):
    """Map an in-TTS '<Global:NNNN>' error line to source file + local line.

    build_save.py joins '-- ========== file ==========' markers and file
    bodies with blank lines; walking the concatenation reproduces the
    numbering TTS reports.
    """
    lua = save.get("LuaScript", "")
    if not lua:
        sys.exit("save has no LuaScript — point me at a built/played save")
    lines = lua.split("\n")
    if not (1 <= lineno <= len(lines)):
        sys.exit(f"bundle has {len(lines)} lines; {lineno} is out of range")

    current_file, file_start = "?", 1
    for i, line in enumerate(lines[:lineno], 1):
        if line.startswith("-- ========== "):
            current_file = line.replace("-- ========== ", "").replace(" ==========", "").strip()
            file_start = i + 1
    local = lineno - file_start + 1
    print(f"<Global:{lineno}> -> lua/{current_file}:{local}")
    print()
    for i in range(max(1, lineno - 4), min(len(lines), lineno + 4) + 1):
        marker = ">>" if i == lineno else "  "
        print(f"{marker} {i:5d}  {lines[i - 1]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path", nargs="?", help="save file (default: the built save)")
    ap.add_argument("--live", action="store_true",
                    help="use the newest TTS autosave / installed save instead")
    ap.add_argument("--objects", nargs="?", const="", metavar="FILTER",
                    help="list objects (optional nickname/tag substring filter)")
    ap.add_argument("--band", action="store_true",
                    help="list objects embedded inside the tabletop (invisible)")
    ap.add_argument("--error", type=int, metavar="N",
                    help="map an in-TTS '<Global:N>' error to source file:line")
    args = ap.parse_args()

    path = args.path or (newest_live_save() if args.live else BUILT_SAVE)
    print(f"# {path}")
    save = load(path)

    if args.error is not None:
        show_error_line(save, args.error)
        return
    if args.objects is not None:
        show_objects(save, args.objects)
        return
    if args.band:
        show_band(save)
        return
    show_state(save)
    show_band(save)


if __name__ == "__main__":
    main()
