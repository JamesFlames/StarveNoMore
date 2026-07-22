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
   the named `lua/` file at that line. Check [tts-runtime.md](tts-runtime.md)
   first — most runtime errors are one of the known API gotchas.
2. **"X is missing / in the wrong place"** → `inspect_save.py --live
   --objects <name>` for where the engine actually put it; `--band` for
   the invisible-object class. If object positions are right but the
   *printed board* disagrees, it's a stale cached board image → purge the
   cache (`iwanttoplay` does it automatically).
3. **Gameplay state questions** ("why did James lose sanity?") →
   `inspect_save.py --live` prints stats, location, ongoing effects, and
   the last Message Log entries; the full log is in the autosave's
   `LuaScriptState → messageLog / dayLog`.
4. **Reproduce headlessly** before fixing: the pytest bundle harness
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
