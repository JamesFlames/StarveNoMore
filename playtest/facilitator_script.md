# Blind Playtest — Facilitator Script

*One page. Read before the group arrives. The point of a blind test is that the game — not you — teaches itself ([PrinciplesOfGoodBoardGames.md §18](../Archive/PrinciplesOfGoodBoardGames.md): watch, don't ask). Companion form: [feedback_form.md](feedback_form.md).*

## Before the session

1. Build and load the current save (`python scripts/build_save.py`, start `scripts/serve_art.bat`, load in TTS). Confirm no red console errors and that art/audio load.
2. Seat 3–5 players who have **never seen the game or its designer explain it**.
3. Decide the session type:
   - **Blind rulebook read (W4):** Standard difficulty. Say only: *"Everything you need is in the game — the Setup button, the '?' Help, the 'What now?' button, and the Notebook tabs."*
   - **Turn-structure A/B (W1, 5 players):** two games with the same group, one full-turns and one Rotation (setup Variants step), order counterbalanced across groups (group 1 plays full→rotation; group 2 rotation→full).
   - **3-player composition check (W2):** 3 players, and the roster must include **Rayman**. You may suggest the trio; nothing else.
4. Open a notes file. Timestamp it.

## During the session — the three rules

1. **No rules help unless truly stuck.** "Truly stuck" = the table has been blocked for 2+ minutes AND the Help/What-now/Notebook path failed. When you do help, **write down what failed first** — every intervention is a rulebook bug with a location.
2. **Watch, don't ask.** Record, with rough timestamps:
   - Rules they get wrong (and *in which direction* — a rule consistently misplayed the same way is often the better rule).
   - Faces during combat, the Doom track, the Source fight. Leaning in or leaning back?
   - Phone-checking / side-talk during *other* players' turns (this is the W1 downtime signal — note who and when).
   - The first time the table argues about a decision (a dare, who checks the Wrongness, who gets the beds) — that argument is the game working.
3. **Never defend the game.** If someone says a rule is bad, write it down. Do not explain the design intent — you won't be in the box they buy.

## After the game

1. **Before any discussion**, have each player fill in [feedback_form.md](feedback_form.md) alone.
2. Ask the retention question **last and casually**: *"Want to play again right now?"* An unprompted yes from the table earlier in the evening counts double; a polite yes to the direct question counts half.
3. Click **Copy Session Log** on the Week in Review panel (it writes JSON to the TTS Notes panel). Paste it into the playtest tracker with the date, the session type, and your notes file.
4. File every rulebook stumble as a fix against `content/notebook/` / `content/help/whatnow_hints.md`.

## What "done" looks like (the gates these sessions feed)

- **W1:** median inter-decision wait and disengagement counts, full vs Rotation → a recorded decision in design §11.2/§20.2.
- **W2:** a Rayman trio that was *fun* (their words, not the win) → closes §20.1.
- **W3:** session outcomes accumulating toward the 40–50% Standard win rate with Day 6–7 losses.
- **W4:** two independent blind groups finish a game; the three batch questions (see the form) score positive; §19.6 items 9 and 10 flip to ✅.
