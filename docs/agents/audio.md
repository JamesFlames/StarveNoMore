# Audio

The sound tree, the generated manifest, and how cues are chosen at runtime.

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

Game audio is local-asset-driven, no AI generation. Files under `sounds/` are
served by `scripts/serve_art.bat` (which now serves the repo root, so both
`art/` and `sounds/` are reachable at `http://localhost:8080/...`) and
referenced in `lua/audio_manifest.lua` (auto-generated).

## Asset layout

```
sounds/
├── ambient/
│   ├── suburban/   <-- 20 tracks: each Dawn picks ONE and loops it all day
│   ├── varied/     <-- 39 tracks: fallback pool if suburban/ is empty
│   └── night/      <-- 3 synthesized low drones: one picked per night, looped
├── creatures/
│   ├── bearger/    <-- 8 sounds (canonical name; folder was renamed from "beager")
│   ├── deerclops/  <-- 12 sounds (Phase 2 boss)
│   ├── eye_of_terror/  <-- 13 sounds (Phase 3 boss)
│   └── treeguard/  <-- 26 sounds (Phase 2.5 mini-boss — wakes Dusk of Day 4, lua/treeguard.lua)
└── sfx/
    ├── tick_chime.wav             <-- synthesized two-note bell (G5+C6) for end-of-day Tick
    ├── Character_Walk_Sound.mp3   <-- played on Move into an empty location
    ├── Character_Meet_Sound.mp3   <-- played on Move into a location occupied by another character
    ├── Character_TalkTrade_Sound.mp3  <-- played on Trade
    ├── Character_Death_Sound.mp3  <-- played when a character flips to Down
    ├── Turn_Ping_Sound.wav         <-- synthesized E5→A5 ping on turn start (Audio.playTurnPing)
    └── night_growl.wav             <-- synthesized low growl: Night Sounds (Audio.playGrowl, fires at Dusk when the top Threat card is Hard)
```

Any audio file dropped into `sounds/sfx/` is auto-discovered by
`scripts/generate_audio_manifest.py` and exposed as `AUDIO.SFX.<key>`, where
`<key>` is the filename stem lowercased with a trailing `_sound` stripped
(e.g. `Character_Walk_Sound.mp3` → `character_walk`).

The Source has no audio folder; `Audio.playBossLoop("the_source")` no-ops
silently and ambient continues.

## In-game behaviour

- **Day start (Dawn):** `Audio.startDayAmbience()` picks ONE suburban track
  (varied pool as fallback) and loops it until nightfall — a mid-day track
  change read as "did something happen?", so a new track means a new day.
- **Night start:** `Audio.startNightAmbience()` picks one low drone from `sounds/ambient/night/` and loops it. A live boss loop keeps priority (both `startDayAmbience` and `startNightAmbience` no-op while `mode == "boss"`); `stopBossLoop` resumes the night drone if it's Night, the day's track otherwise. `Audio.stopAmbience()` remains as a hard stop.
- **Boss arrives:** `Audio.playBossLoop(<key>)` suspends ambient and plays a
  random sound from `sounds/creatures/<key>/`. After the sound ends + 10s, if
  the boss is still alive, another random sound from the same folder plays.
  Loops until `Audio.stopBossLoop(<key>)` is called.
- **Boss defeated:** combat.lua maps the threat name to a boss key
  (`Audio.threatNameToBossKey`) and calls `Audio.stopBossLoop(<key>)`, which
  resumes the day's looped track (or the night drone at Night).
- **Tick (end of day):** `Audio.playChime()` briefly takes over MusicPlayer for
  the chime, then resumes ambient/boss audio.
- **Character SFX (one-shots):**
  - `Audio.playWalk()` on `doMove` / `doRaymanBonusMove` when the destination is empty.
  - `Audio.playMeet()` on the same handlers when the destination already has another non-Down character.
  - `Audio.playTradeChat()` at the end of `doTrade`.
  - `Audio.playDeath()` from `checkDownState` when a character flips to Down.
  - All four go through `Audio.playSFX(<key>)`, which uses the same brief-interrupt-then-resume machinery as `playChime()`.

Single-channel constraint: TTS has only one global `MusicPlayer`. One-shots
(chime, character SFX, boss roar) interrupt the ambient track for their
duration; the next ambient track is rescheduled fresh after.

## Pipeline

1. **Edit/add sound files** under `sounds/...`.
2. **Regenerate the manifest:** `python scripts/generate_audio_manifest.py` —
   walks the tree, computes durations (precise for `.wav`, file-size-estimated
   for `.mp3`), writes `lua/audio_manifest.lua`.
3. **Build the save:** `python scripts/build_save.py` — `audio_manifest.lua`
   and `audio.lua` are concatenated early in `LUA_LOAD_ORDER` so all gameplay
   files can reference `Audio.*`.
4. **Run the local server:** `scripts/serve_art.bat` (serves repo root over
   `:8080`) so TTS can reach the WAV/MP3 files at the URLs in the manifest.
5. **Hand-add new bosses:** drop sound files in `sounds/creatures/<name>/` and
   extend `Audio.threatNameToBossKey()` if the threat-card name doesn't
   contain `<name>` as a substring.
