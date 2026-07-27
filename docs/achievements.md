# Achievements

24 achievements, one CSV row each, shown in-game in a Steam-style panel and
exported as a Steamworks-shaped manifest for the day this ships as its own
app.

- **Add or reword one** → [`content/achievements.csv`](../content/achievements.csv),
  then `python scripts/generate_achievement_data.py` and add a predicate to
  `lua/achievement_rules.lua`. A row without a rule (or a rule without a row)
  fails `tests/test_lua_achievements.py`, so the two can't drift.
- **Regenerate the art** → [`comfyui-achievement-icons.md`](comfyui-achievement-icons.md).

## First, the awkward part: a TTS mod cannot set a Steam achievement

Starve No More runs inside Tabletop Simulator's Steam app. It has no appid of
its own and no Steamworks surface — `ISteamUserStats::SetAchievement` is not
reachable from a Workshop mod's Lua, and never will be. Anything claiming
otherwise is describing TTS's *own* achievements, which belong to Berserk
Games.

So this ships as two halves that share one source file:

| Half | What it is | Where it runs |
|---|---|---|
| The panel | A real, working achievement system: unlock rules, a vault, toasts, a transferable code | In the mod, today |
| `steam/achievements.json` | The same 24, in the shape Steamworks' Stats & Achievements page wants | The day there's an appid |

The second half costs one generator branch and keeps the naming honest
(`ACH_*` API names, hidden flags, 256px + 64px icons), so a future port is a
copy-paste rather than a redesign. If that port never happens, nothing is
lost — the panel was the point.

## Where unlocks live

TTS gives a mod exactly two places to keep state: the script state it hands to
`onSave`/`onLoad`, and the clipboard. There is no file access and no per-player
storage. So:

- `gameState.achievements = { unlocked = { [id] = {day, at, game} }, games = n }`
- It rides `gameState` (nothing else persists), but it is **not** part of a
  game: `onHostRestart` carries it across the reset deliberately, and
  `migrateGameState` back-fills it so a pre-achievements save loads clean.
- **Save & Play keeps it. A fresh load from the Workshop does not** — that is
  a TTS limit, not a bug. The panel's *Copy my code* button writes a
  `SNM-ACH-1:` string to the Notes panel; pasting it into another table's box
  restores every unlock. Ids, not a bitfield, so a code survives the roster
  being reordered.

## When rules are evaluated

Predicates are pure reads of `gameState` and the Week in Review chronicle, so
there is nothing to hook per achievement — `checkAchievements(reason)` re-tests
the whole roster at four checkpoints:

| Checkpoint | Site | Catches |
|---|---|---|
| `kill` | `combat_resolve.lua`, after the kill is recorded | boss kills, threat counts |
| `turnEnd` | `turns.lua`, `endPlayerTurn` | crafts, cooks, Signatures, revives, Clues |
| `dayEnd` | `tick_victory.lua`, after the day-end summary | day-count achievements |
| `gameOver` | `ui_week_review.lua`, `showWeekInReview` | won / pristine / last one standing |

24 table reads beats 24 call sites to keep in sync, and a broken predicate is
`pcall`-ed: it costs its own achievement and nothing else.

**Nothing new is recorded at the table.** Every number the rules read was
already tracked for the Week in Review (§16.5) or the session telemetry
(§20.2). That is the constraint the Review works under and achievements
inherit it — see `lua/achievement_rules.lua` for which field each one reads.

## Files

| File | Role |
|---|---|
| `content/achievements.csv` | the source of truth — id, API name, text, hidden, category, art prompt |
| `lua/achievement_data.lua` | AUTO-GENERATED roster (never hand-edit) |
| `lua/achievement_rules.lua` | one predicate per id — the hand-written half |
| `lua/achievements.lua` | vault, unlock, checkpoints, export/import code |
| `lua/ui_achievements.lua` | the paged panel and the toast queue |
| `xml/achievements.xml` | panel layout, 8 fixed rows, the `Trophies` button |
| `art/achievements/` | icons (`<base>.png` in-game, `steam/*.jpg` for Steamworks) |
| `steam/achievements.json` | AUTO-GENERATED Steamworks manifest |

## Adding one

1. Add a row to `content/achievements.csv`. `art_notes` is the ComfyUI prompt —
   describe **one object on a dark field**, not a scene (see the run book).
2. Add `ACHIEVEMENT_RULES.A_YOUR_ID = function() ... end` to
   `lua/achievement_rules.lua`. Read only `gameState` / `achChronicle()`.
3. Add a case to `RULE_CASES` in `tests/test_lua_achievements.py`, or a
   dedicated test if it needs more than one field set.
4. `python scripts/regenerate_all.py` (or the three generators by hand:
   `generate_achievement_data.py`, `generate_achievement_icons.py`,
   `generate_symbol_index.py`), then `python -m pytest tests`.

The icon step is safe to run before there is any art: it drops a procedural
placeholder in the game's palette so the panel and the tests stay green, and
upgrades it automatically once `art/achievements/src/<base>.png` shows up.
