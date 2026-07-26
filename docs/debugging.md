# Debugging a live TTS session

How to answer "what happened in the user's game last night" **without
launching TTS** — everything a session leaves behind is on disk.

## Where the evidence lives

| Artifact | Path | Contains |
|---|---|---|
| Installed save | `Documents\My Games\Tabletop Simulator\Saves\StarveNoMore.json` | The build the user actually loaded (compare its mtime to `saves/StarveNoMore.json`) |
| **Autosaves** | same folder, `TS_AutoSave*.json` | Full snapshots of the live session: every object's real position/rotation **and** the live `gameState` (in `LuaScriptState`, as JSON) |
| Asset cache | `...\Tabletop Simulator\Mods\` | Cached art/audio — stale entries cause "old art" bugs (see [tts-runtime.md](tts-runtime.md)) |
| Engine log | `AppData\LocalLow\Berserk Games\Tabletop Simulator\Player.log` | Unity/engine noise only — **Lua errors are NOT persisted anywhere**; they exist only in the in-game chat. Ask the user for the exact red text. |

## One tool: `scripts/inspect_save.py`

```bash
python scripts/inspect_save.py --live            # newest autosave: gameState + sunk-object check
python scripts/inspect_save.py --live --objects doom   # where is X, really?
python scripts/inspect_save.py --band            # anything spawned inside the tabletop?
python scripts/inspect_save.py --error 2517      # user saw "<Global:2517>" → source file:line + context
```

`--error` decodes TTS's `<Global:NNNN>` error lines against the built
bundle. Run it against the same build that produced the error (check
save mtimes if unsure).

## Typical diagnosis flow

1. **User reports an error string** → `inspect_save.py --error N` → open
   the named `lua/` file at that line. Check [tts-interface.md](tts-interface.md)
   first — most runtime errors are one of the known API gotchas.
2. **"X is missing / in the wrong place"** → `inspect_save.py --live
   --objects <name>` for where the engine actually put it; `--band` for
   the invisible-object class.
3. **"The pieces and the printed board disagree"** → the object positions
   in the save are literal, so the *board* is what's wrong. Check its
   orientation first (`rotY` must be 0, and the PNG carries the 180°
   pre-rotation — [tts-runtime.md](tts-runtime.md#diagnosing-everything-is-180-out)
   has the full diagnostic and why the camera in a screenshot proves
   nothing). Only suspect a stale cached image when the art is the **wrong
   picture** rather than in the wrong place — a whole map turned about its
   centre is geometry, not caching.
4. **Gameplay state questions** ("why did James lose sanity?") →
   `inspect_save.py --live` prints stats, location, ongoing effects, and
   the last Message Log entries; the full log is in the autosave's
   `LuaScriptState → messageLog / dayLog`.
5. **Reproduce headlessly** before fixing: the pytest bundle harness
   (`tests/conftest.py`) can script the same situation with fake dice
   (`script_dice`) — cheaper than a TTS launch, and the fix ships with
   its regression test.

## Deploying a fix to the table

`iwanttoplay` (repo root) = regenerate → build → full pytest gate → copy
save + cover → **purge this mod's stale cache** → ensure asset server →
launch TTS. Flags: `--skip-tests`, `--no-launch`.

Release gate before sharing: the checklist in
[agents.md](../agents.md#release-checklist-before-sharing-a-new-save),
including `runSelfTest()` from the TTS console.

## Measuring the live table (probes)

Some bugs are only answerable with numbers from a running game — TTS
primitives have mesh extents that are not 1 unit, so a Transform scale
cannot be reasoned about from the save alone. Two probes run at load and
report into the Message Log, which the autosave persists:

- **`auditBoardGeometry()`** — the board's real world size vs. the square
  the art is authored across, and the *corrected* Transform scale. Silent
  when they match; warns loudly when they don't. This is what identified
  the board rendering across ±110 world units instead of ±12.
- **`auditObjectFootprints()`** — each key object's real world size, plus
  how far its rendered centre sits from its transform origin (a gadget
  that doesn't sit where it's placed). Gated behind `MEASURE_FOOTPRINTS`
  in `lua/audit.lua`; turn it off once sizes are tuned.

Read the results without touching the console:

```bash
python scripts/inspect_save.py --live
```

The full Message Log is in the autosave's `LuaScriptState → messageLog`.
TTS autosaves every ~5 minutes, so a probe result appears within one
autosave cycle of loading the save.

> Lua `print()` does **not** reach Unity's `Player.log` — that file only
> carries engine output. The Message Log (via `broadcastEvent`) is the
> channel that survives to disk.
