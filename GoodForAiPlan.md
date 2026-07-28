# GoodForAiPlan — making Starve No More cheaper and more reliable for AI work

**Audience:** the next agent (or human) who picks up work in this repo.
**Goal:** cut the tokens and turns a routine task costs, and close the gaps
where a wrong change still passes `python -m pytest tests`.

This is the *third* pass at this problem. Two earlier programs shipped and were
retired into git history + [`CHANGELOG.md`](CHANGELOG.md):

- **compartmentaliseplan** (2026-07) — built the navigation layer
  ([`CLAUDE.md`](CLAUDE.md) → [`TASKMAP.md`](TASKMAP.md) →
  [`SYMBOLS.md`](SYMBOLS.md)), split the design doc into
  [`docs/design/`](docs/design/README.md), split the oversized Lua/Python
  modules, and extracted [`scripts/load_order.json`](scripts/load_order.json) +
  [`scripts/generators.json`](scripts/generators.json).
- **structuralimprovements** (2026-07) — doc-reference guards, the
  `regenerate_all.py` orchestrator, live-session forensics
  (`scripts/inspect_save.py`), the TTS runtime contract docs.

Those solved *navigation* ("which file do I open?"). What is left is a different
class of cost, and this plan is scoped to it:

1. **Bootstrap tax** — a fresh session cannot run the tests without discovering
   and installing dependencies first.
2. **Silent-failure surface** — the parts of the codebase where a green suite
   does not mean a working game (the whole UI layer, and `gameState`).
3. **Context bill** — the two files an agent is told to consult are ~17k and
   ~18.5k tokens.
4. **Drift pairs** — places where the same fact is written twice with nothing
   binding them.

Status legend (same convention as the retired plans): ⬜ open · ✅ shipped ·
🔎 investigated, no action. Priority: **P1** high value / low risk, **P2**
worth doing, **P3** nice to have. Effort: **S** ≲1 session · **M** 1–2 ·
**L** multi-session.

---

## 1. What is already good — do not redo it

An agent arriving here should not spend a session re-deriving these. They were
measured on 2026-07-28 and are genuinely in good shape:

| Property | Measurement | Verdict |
|---|---|---|
| Test suite wall time | **17.4 s**, 678 tests, 1 skipped | Fast enough that "run the whole suite" is always the right advice. Do not shard it. |
| Determinism | Every stochastic test is seeded (`random.Random(seed)` in `test_sim.py`, `test_full_campaign.py`, `simulate_balance.py`) | No flakes. Do not add unseeded randomness. |
| Regeneration | `python scripts/regenerate_all.py` = **0.4 s**, idempotent, clean `git status` afterwards | Cheap enough to run unconditionally before every commit. |
| Failure-message quality | The freshness guard fails with *"lua/recipe_data.lua is stale: scripts/generate_recipe_data.py produces different output … Rerun the generator and rebuild the save."* | Names the exact fix. This is the house style — match it in every new guard. |
| Navigation layer | [`TASKMAP.md`](TASKMAP.md) routes job → files; [`SYMBOLS.md`](SYMBOLS.md) routes symbol → `file:line` | Works. The remaining problem is its *size*, not its design (see 4.2). |
| Doc rot guards | `test_doc_links.py`, `test_doc_file_refs.py`, `test_doc_section_refs.py` | Prose references, links and section numbers are all enforced. Strong. |
| File-size discipline | CI warns above 500 lines, never fails | Correct call. 14 tracked source files are over budget; that is a backlog, not a break. |

**Corollary:** the cheapest remaining wins are *not* more splitting. They are
bootstrap, coverage of the untested surface, and shrinking the two monolith
reference docs.

---

## 2. How this was measured (re-run before claiming progress)

Every number in this plan is reproducible with these commands. Re-run them
after finishing a phase and update the scoreboard in section 3.

```bash
# Bootstrap: does a cold environment run the suite at all?
python -c "import pytest, lupa, PIL" ; echo "exit=$?"

# Suite cost
time python -m pytest tests -q --durations=15

# Regeneration cost + idempotence
time python scripts/regenerate_all.py && git status --short   # must be empty

# Context bill of the read-first docs (chars/4 ≈ tokens)
for f in CLAUDE.md TASKMAP.md SYMBOLS.md agents.md README.md; do
  echo "$(( $(wc -c < $f) / 4 )) tok  $f"; done

# Untested surface: global Lua functions never named in any test
python - <<'EOF'
import re, os, glob
funcs = {}
for p in glob.glob('lua/**/*.lua', recursive=True):
    src = open(p, encoding='utf-8').read()
    if 'AUTO-GENERATED' in src[:300]: continue
    for m in re.finditer(r'^function\s+([A-Za-z_]\w*)\s*\(', src, re.M):
        funcs.setdefault(os.path.relpath(p), []).append(m.group(1))
tests = "\n".join(open(f, encoding='utf-8').read()
                  for f in glob.glob('tests/*.py') + glob.glob('tests/*.lua'))
tot = sum(len(v) for v in funcs.values())
un  = sum(1 for v in funcs.values() for n in v if n not in tests)
print(f"{un}/{tot} global functions never named in a test ({un*100//tot}%)")
EOF

# Untested surface: XML click handlers never named in any test
python - <<'EOF'
import re, glob
xml = "\n".join(open(f, encoding='utf-8').read() for f in glob.glob('xml/*.xml'))
h = {r.split("/")[-1].split("(")[0].strip()
     for r in re.findall(r'\bon(?:Click|ValueChanged|EndEdit|Submit)\s*=\s*"([^"]+)"', xml)}
tests = "\n".join(open(f, encoding='utf-8').read() for f in glob.glob('tests/*.py'))
print(f"{sum(1 for n in h if n and n not in tests)}/{len(h)} XML handlers never named in a test")
EOF

# gameState spread
grep -rhoE "gameState\.[A-Za-z_][A-Za-z0-9_]*" lua/ | sort -u | wc -l
grep -rlE "gameState\." lua/ | wc -l
```

---

## 3. Baseline scoreboard (2026-07-28)

The numbers this plan is trying to move. Re-measure with section 2.

| Metric | Baseline | Target | Item |
|---|---|---|---|
| Cold-start: `import lupa` succeeds | **No** — suite unrunnable until deps installed | Yes, automatically | 4.1 |
| Commands to go from edit → verified | 3 (`regenerate_all` → `build_save` → `pytest`) | 1 | 4.3 |
| Global Lua functions never named in a test | **235 / 394 (59 %)** | < 35 % | 5.1 |
| XML click handlers never named in a test | **58 / 73 (79 %)** | 0 % | 5.1 |
| `gameState` fields with a declared schema | **0 / 71** | 71 / 71 | 5.3 |
| `gameState` initialisers that can drift | **2** (`global.lua`, `ui_controls.lua`) | 1 | 5.2 |
| Lua files outside `load_order.json` | **1** (`assets.lua`, warns only) | 0, enforced | 5.5 |
| `agents.md` size | **~18.6k tok** (one file) | ≤ 2.5k per topic file | 6.1 |
| `SYMBOLS.md` size | **~17.1k tok** (read or grep) | queryable in one call | 6.2 |
| Suite wall time | 17.4 s | ≤ 30 s (protect it) | — |
| Tracked media | 274 MB (`.git` pack 398 MB) | −17 MB, then hold | 7.1 |

---

## 4. Phase A — kill the bootstrap tax (P1, do first)

The highest-frequency cost in the repo: it is paid at the start of *every*
session, before any useful work.

### 4.1 ⬜ Ship a `SessionStart` hook that installs the test dependencies (P1, S)

**Problem.** A fresh container clones the repo and cannot run the suite.
**Evidence.** On this machine, out of the box:

```
$ python -m pytest tests
/usr/local/bin/python: No module named pytest
$ python -c "import lupa"
ModuleNotFoundError: No module named 'lupa'
```

`pytest` exists as a `uv` tool shim on `PATH` but is invisible to the
interpreter the tests need, so even the "obvious" invocation fails in a way
that reads like a broken repo rather than a missing dependency. Every agent
rediscovers this, guesses, and burns 2–4 turns before its first green run.

**Change.** Add `.claude/settings.json` with a `SessionStart` hook running
`python -m pip install -q pytest lupa Pillow` (idempotent; a no-op once
present). The `session-start-hook` skill exists for exactly this shape of
setup. Mirror the same three packages in
[`.github/workflows/tests.yml`](.github/workflows/tests.yml), which currently
installs only `pytest lupa` — `Pillow` is needed by the art generators that
`regenerate_all.py` can invoke.

**Verify.** In a fresh clone, the first `python -m pytest tests` succeeds with
no manual step.

### 4.2 ⬜ Un-ignore `.claude/` and commit the project-level config (P1, S)

**Problem.** `.gitignore` line 2 is `.claude/`, so every per-project agent
setting — permissions, hooks, skills, slash commands — is local-only and dies
with the container. Nothing an agent learns about *how to work here* can be
saved for the next one.

**Change.** Narrow the ignore to `.claude/settings.local.json` (personal
overrides) and commit `.claude/settings.json`. Seed it with:

- **A permission allowlist** for the routine loop — `python -m pytest tests`,
  `python scripts/regenerate_all.py`, `python scripts/build_save.py`,
  `python scripts/generate_*.py`, `git status/diff/log/add/commit`. Each
  approval prompt an agent avoids is a saved round-trip; the `/permissions`
  and `fewer-permission-prompts` tooling can generate the list from a real
  transcript rather than guessing.
- **The `SessionStart` hook** from 4.1.
- **A `PostToolUse` hook on `Edit`/`Write` under `lua/`** that runs
  `python scripts/generate_symbol_index.py`. Today "rerun the generator" is a
  rule in three `CLAUDE.md` files that the agent must *remember*; the freshness
  test catches the miss, but only after a full suite run. A hook makes it
  unmissable and free. (Keep the freshness test — the hook is the fast path,
  the test is the guarantee.)

**Note.** `test_doc_links.py` and `test_doc_file_refs.py` already skip
`.claude/`, so committing it does not disturb the doc guards.

**Verify.** `git ls-files .claude` lists `settings.json`; a Lua edit leaves
`SYMBOLS.md` fresh without an explicit regenerate step.

### 4.3 ⬜ One command for "am I done?" (P1, S)

**Problem.** Every `CLAUDE.md` ends with the same three-step ritual:
regenerate → build → test. Three commands means three chances to do two of
them. [`TASKMAP.md`](TASKMAP.md) already hedges with *"Unsure which generator?
`regenerate_all.py` runs them all"* — the same hedge belongs at the finish line.

**Change.** Add `scripts/check.py`: `regenerate_all.py` (which already ends in
`build_save.py`) → `python -m pytest tests` → `luacheck lua/` if the binary
exists (skip with a note if not; it is absent from this environment and from
the default CI image except in its own job). Print a one-line verdict. Then
replace the three-command instruction in [`CLAUDE.md`](CLAUDE.md),
[`TASKMAP.md`](TASKMAP.md), [`lua/CLAUDE.md`](lua/CLAUDE.md),
[`scripts/CLAUDE.md`](scripts/CLAUDE.md), [`tests/CLAUDE.md`](tests/CLAUDE.md)
and [`content/CLAUDE.md`](content/CLAUDE.md) with `python scripts/check.py`.

**Watch out.** Do not delete the underlying commands from the docs — an agent
debugging a *generator* still needs to run one in isolation. Demote them to a
sub-bullet.

**Verify.** `python scripts/check.py` exits non-zero on a deliberately stale
generated file and zero on a clean tree, in under ~25 s.

### 4.4 ⬜ A committed `/verify` and `/newtask` command pair (P2, S)

Once 4.2 lands, `.claude/commands/` is a shareable place to put the two
workflows every session repeats: *verify* (run `check.py`, summarise failures)
and *newtask* (read `TASKMAP.md`, open only the routed files, state the plan
before editing). Cheap to add, and it converts prose conventions into something
the harness executes.

---

## 5. Phase B — close the silent-failure gaps (P1, highest reliability value)

This is where a green suite currently fails to mean a working game. The commit
log shows the cost: *"Playtest feedback batch: setup flow, table clarity, UI
declutter"*, *"Fix ghost Step 2 panel stranding the reseated player after
setup"*, *"Self-heal the setup pick queue"*, *"many many fixes"*. These are all
UI-layer bugs found by humans playing the game, because nothing else could find
them.

### 5.1 ⬜ Smoke-test every XML click handler (P1, M) — *the single highest-value item in this plan*

**Problem.** The XML↔Lua contract is checked for *existence* only.
`test_xml_lua_contract.py` proves every `onClick` names a real Lua function and
every `UI.show("id")` targets a real XML id — but nothing ever *calls* those
functions.

**Evidence.** 73 XML handlers; **58 (79 %) are never named in any test**,
including every action button in the game: `onActGather`, `onActFight`,
`onActCook`, `onActCraft`, `onActMove`, `onActRest`, `onActTrade`,
`onActSignature`, `onActUndo`, `onPressAttack`, `onHostBeginDay`,
`onHostResolveNight`, `onDuskReadyClick`, `onWeekReviewClose`, the whole
achievements panel, the whole help/rules panel. At the function level the same
hole shows as **235 / 394 (59 %) of global Lua functions never named in a
test**, concentrated exactly where the bugs were:
`ui_actionbar_handlers.lua` 29/29 unreferenced, `ui_banner.lua` 13/16,
`ui_actionbar_targets.lua` 13/14, `ui_mood.lua` 9/9, `ui_msglog.lua` 5/5.

**Change.** Add `tests/test_ui_handlers_smoke.py`. Reuse the existing
`make_env()` / `start_game()` harness from `test_full_campaign.py` (it already
drives a real seeded campaign through the Lua bundle under `lupa`). For each
handler discovered by parsing `xml/*.xml` — the same regex
`test_xml_lua_contract.py` already uses, so the list can never go stale —
invoke it with a stub `Player` in a matrix of states (PreGame, Day with an
active seat, Day with a *wrong* seat, Dusk, Night, GameOver) and assert:

1. no Lua error escapes (the `tts_stub.lua` error path already exists);
2. `gameState` invariants still hold afterwards (reuse
   `assert_invariants()` from `test_full_campaign.py`);
3. clicking out of turn or out of phase is *refused*, not crashed.

Handlers needing arguments (`onCookOptionClick`, `onDuskMoveClick`,
`onRallyTargetClick`, `onSignatureTargetClick`, `onTradeTargetClick`,
`onPeekDeckClick`, `onDawnStepClick`, `onResourcePickCancel`) get a small
explicit fixture table; keep that table *required* — an unlisted handler must
fail the test, not be skipped, or the coverage rots the first time someone adds
a button.

**Why this beats more unit tests.** It is one test module that permanently
covers 79 % of the interactive surface, it cannot drift (the handler list is
derived from the XML), and it targets the exact failure mode TTS is worst at:
silent no-ops and mid-click errors that only a human at the table notices.

**Verify.** The two coverage one-liners in section 2 drop to 0/73 handlers and
under ~35 % of functions. Deliberately breaking a handler (e.g. index a nil
`gameState` field in `onActGather`) must fail the suite.

### 5.2 ⬜ One `gameState` initialiser, not two (P1, S)

**Problem.** `gameState` is built from scratch in two places that must agree
and are not bound:

- `lua/global.lua:10` — the full literal (~40 fields, heavily commented).
- `lua/ui_controls.lua:238` — the **Restart** path, a hand-copied shorter
  literal.

`migrateGameState()` (`lua/global.lua:303`) is the documented single source of
defaults — its own header says *"defaults live in ONE place"* — but it is
called from exactly one site, `onLoad` (`lua/global.lua:355`). The Restart path
never calls it, so fields it guarantees (`resources`, `dailyAlerts`,
`messageLog`, `haunted`, `threatDamage`, `cluesFound`, `duskPending`,
`schemaVersion`, …) are simply absent after a Restart. Today that is survivable
because callers are defensive — `test_gamestate_fields_initialised_before_indexing`
enforces lazy-init or a default at every index site — but the *next* field
added without an `or {}` guard becomes a Restart-only crash, which is the
hardest kind to reproduce.

**Change.** Make Restart go through the same door:

```lua
gameState = { achievements = keptAchievements }
migrateGameState()
```

and move any Restart-specific values (`chronicle = nil` for lazy rebuild) to
after the call. Then add a test asserting the key set after Restart is a
superset of the key set after a fresh `onLoad({})` — that is the assertion that
actually prevents the drift returning.

**Verify.** New test fails against today's `ui_controls.lua` and passes after
the change; `test_full_campaign.py`'s existing restart test still passes.

### 5.3 ⬜ Generate a `gameState` schema map (P1, M)

**Problem.** 71 distinct `gameState.*` fields are read or written across **41 of
46 Lua files**, with no schema anywhere. An agent asked to "add a field" or
"find who clears X" has no index — it greps, guesses, and a misspelling
(`activeChar` for `activeChars`) reads as `nil` silently. This was flagged as
deferred item 4.3 in the retired structural plan and is still open; it has only
grown.

**Change.** Add `scripts/generate_gamestate_map.py` → `docs/gamestate.md`,
listing per field: declared default (parsed from `migrateGameState()`), the
files that **write** it, the files that **read** it, and whether it survives
`onSave`. Register it in [`scripts/generators.json`](scripts/generators.json)
so `regenerate_all.py` and the freshness test pick it up for free. Then add the
guard that pays for the generator: **every `gameState.<name>` referenced
anywhere in `lua/` must appear in `migrateGameState()`**, with a small explicit
allowlist for genuinely transient fields. That single assertion converts every
future field typo from a silent `nil` into a named test failure.

**Verify.** `docs/gamestate.md` regenerates clean; renaming any field in one
file and not the others fails the suite with the field name in the message.

### 5.4 ⬜ Bind `CHAR_BRIEFINGS` to its markdown source (P2, S)

**Problem.** The same player-facing text exists twice: `CHAR_BRIEFINGS` at
`lua/ui_setup.lua:595` and `content/help/character_briefings.md`. Nothing binds
them, and **they have already diverged** — the markdown says James *"lives at
James's House, where Energy Drinks and Batteries are plentiful"*; the Lua
briefing has no such line. [`content/CLAUDE.md`](content/CLAUDE.md) tells an
agent that `content/` is the source of truth for in-game text, so the natural
edit lands in the markdown and never reaches the game. Deferred item 6.6 in the
retired plan; still open, now demonstrably broken.

**Change.** Preferred: generate the Lua table from the markdown (a small
generator in the existing `generate_*_data.py` family, registered in
`generators.json` so freshness is automatic). Cheaper fallback: a cross-ref
test in `test_cross_refs.py` asserting one briefing per character in both, with
matching strengths/constraints lines. Either way the *first* run must reconcile
the current divergence — decide which text is canonical before automating it.

**Verify.** Editing the markdown alone fails the suite (or updates the Lua) —
it can no longer silently do nothing.

### 5.5 ⬜ Make an unlisted Lua file an error, not a printed note (P2, S)

**Problem.** `lua/assets.lua` is absent from
[`scripts/load_order.json`](scripts/load_order.json). The build appends it
last and prints `NOTE: Extra Lua file included: assets.lua`
(`scripts/build_save.py:1514`) — nothing fails, and nothing in the test suite
asserts the note is absent. [`lua/CLAUDE.md`](lua/CLAUDE.md) states the hazard
plainly: *"Files not in the list are appended last — order not guaranteed."*
With one shared global namespace and no `require`, load order **is** the
dependency graph. `assets.lua` defines `ASSETS` and `BOARD_ART_URLS`; its only
consumer today reads `BOARD_ART_URLS` inside a function
(`lua/ui_actionbar_core.lua:63`), so it happens to be safe. The first
top-level read of `ASSETS` from another module turns that luck into a nil.

**Change.** Either add `assets.lua` to `load_order.json` at the correct
position (it defines constants — early), or, if it is deliberately excluded,
add an explicit `EXTRA_LUA` allowlist. Then make the build **fail** on any Lua
file that is in neither list, and add a test asserting every file on disk is
accounted for.

**Verify.** Dropping a new `lua/foo.lua` in without touching the manifest fails
the build with a message naming the file and the manifest.

### 5.6 ⬜ Extend the smoke idea to the setup walkthrough (P2, M)

The setup flow produced three separate fix commits (*ghost Step 2 panel*,
*self-heal the pick queue*, *setup names players not seat colours*) and
`lua/ui_setup.lua` is the largest hand-written Lua file (854 lines, 12/20
functions untested). After 5.1 lands, add a state-machine test that walks the
guided setup for 1–5 players including the ugly paths: a player leaving
mid-pick, two players picking the same character, a reseat between steps.

---

## 6. Phase C — cut the context bill (P2, biggest per-task token win)

### 6.1 ⬜ Split `agents.md` into `docs/agents/` (P2, M)

**Problem.** [`agents.md`](agents.md) is ~18.6k tokens in one file, and
[`CLAUDE.md`](CLAUDE.md) points to it as the deep reference for anything the
lean card does not answer. An agent that needs one section either pays for the
whole file or greps blind.

**Evidence** (measured section sizes, ≈ tokens):

| Section | ~tok | | Section | ~tok |
|---|---:|---|---|---:|
| Game Design Quick Reference | 2995 | | Always-obvious next step | 2019 |
| Test Suite | 2312 | | Documentation Map | 1784 |
| ComfyUI Workflow | 2117 | | File Structure | 1637 |
| Balance Simulation | 1640 | | Architecture | 1162 |
| Audio | 1150 | | Working With This Project | 723 |
| Key Conventions | 426 | | Project Overview | 252 |

**Change.** Apply the pattern that already worked for the design doc: one topic
per file under `docs/agents/` with a `README.md` jump table, leaving `agents.md`
as a thin index (Documentation Map + Key Conventions + the jump table stay in
the root file, since those are the parts read *first*). Split by natural
boundary: architecture+file-structure, design quick reference, test suite,
balance simulation, ComfyUI, audio, UX affordances, working-with-this-project.

**Watch out.** Three tests key off `agents.md` specifically:
`test_doc_links.py::test_every_root_doc_is_in_the_agents_map` (every root
`*.md` must be *named in* `agents.md`), `test_doc_file_refs.py` (NAV_DOCS list)
and `test_doc_section_refs.py`. Update all three lists in the same commit, and
keep the Documentation Map in the root file so the first test still has a
target. `test_cross_refs.py` also cites `agents.md` prose — grep for it.

**Verify.** Suite green; no single `docs/agents/*.md` above ~2.5k tokens;
`TASKMAP.md`/`CLAUDE.md` point at the specific topic file, not the index.

### 6.2 ⬜ Make `SYMBOLS.md` queryable, not readable (P2, S)

**Problem.** [`SYMBOLS.md`](SYMBOLS.md) is ~17.1k tokens. `CLAUDE.md` says to
*grep* it, which is right, but a grep returns a table row (`| 93 | function |
setButtonLabel |`) with no signature and no neighbours, so the agent opens the
file anyway.

**Change.** Have `generate_symbol_index.py` additionally emit `symbols.json`
(name → file, line, kind, arity, one-line docstring from the preceding comment)
and add `scripts/sym.py NAME` printing `file:line`, the signature, and its
call sites. One tool call replaces a grep + an open. Keep `SYMBOLS.md` — it is
the human-readable view and the freshness test already covers it.

**Verify.** `python scripts/sym.py beginNight` answers in one call with enough
context to edit; `regenerate_all.py` keeps `symbols.json` fresh.

### 6.3 ⬜ De-duplicate the build instructions (P3, S)

The build/regenerate sequence is written out in five places:
[`README.md`](README.md) ("Building"), [`agents.md`](agents.md) ("Working With
This Project"), [`CLAUDE.md`](CLAUDE.md), [`scripts/CLAUDE.md`](scripts/CLAUDE.md)
and [`content/CLAUDE.md`](content/CLAUDE.md). Four of them will drift the first
time a generator is added. After 4.3 exists, collapse them: one canonical block
in `scripts/CLAUDE.md`, everything else says `python scripts/check.py` and
links to it.

### 6.4 ⬜ Per-CSV column dictionary in `content/CLAUDE.md` (P3, S)

Carried forward from the retired plan (item 2.3, still open). To learn what
columns `cards_market.csv` has, an agent currently opens
`tests/test_csv_schema.py` or the CSV itself. A short table per file — column,
type, allowed values, which generator consumes it — is a few hundred tokens
that saves opening two files, and `test_csv_schema.py` can assert the table
matches the schema it enforces so it cannot rot.

---

## 7. Phase D — repo weight and CI (P3)

### 7.1 ⬜ Convert the one 17 MB WAV that escaped the audio compression pass (P3, S)

Commit `04a96a2` converted ambient WAVs to OGG q4, but
`sounds/ambient/varied/battlegrounds fall night_ds_amb.wav` is still **17 MB** —
by far the largest tracked file, ~6 % of all tracked media (274 MB). Convert it
to OGG like its neighbours, rerun `generate_audio_manifest.py`. Then add a
guard test capping *newly tracked* binaries at, say, 4 MB so the next one does
not slip in.

**Do not rewrite history to reclaim the old blobs.** The `.git` pack is 398 MB
and a rewrite would break every existing clone for a one-time saving. If clone
time genuinely hurts a session, the safe lever is a partial clone
(`git clone --filter=blob:none`) — document that in `README.md` rather than
touching history.

### 7.2 ⬜ Flip the `luacheck` job off `continue-on-error` (P3, S — needs maintainer)

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) says the soft-fail
is *"until the first CI run has been reviewed — then flip continue-on-error
off"*. The retired plan deferred this to the maintainer (item 3.3) because it
cannot be verified from inside a sandbox without `luacheck` installed. It is
still soft. Review one real run's output, fix or whitelist what it reports, and
flip it — a lint that cannot fail is a lint an agent learns to ignore.

### 7.3 ⬜ Fix the stale CI comment (P3, XS)

`.github/workflows/tests.yml:41` points at `Archive/compartmentaliseplan.md`,
deleted in commit `10f3dad`. The doc-ref guards do not scan YAML, so it went
unnoticed. Repoint it at the `CLAUDE.md` files that carry the 500-line budget,
or drop the reference.

### 7.4 ⬜ Cross-platform entry point (P3, S)

`iwanttoplay.bat` is Windows-only, so the headline command in
[`CLAUDE.md`](CLAUDE.md) is unavailable to every Linux-container agent — which
is all of them. `scripts/iwanttoplay.py` is already portable; add a POSIX
`iwanttoplay` shim and note in `CLAUDE.md` that the launch/install steps are
Windows-only while regen/build/test are not. (Deferred item 5.2 from the
retired plan.)

---

## 8. Phase E — keep it good (P2, do last but do it)

The previous two programs each shipped, then quietly re-accumulated debt. Add
the guards that make regression visible:

### 8.1 ⬜ Extend the soft CI guardrail into a context-budget job (P2, S)

The `filesize` job already warns over 500 lines. Extend the same
warn-never-fail job to also report: docs over ~2.5k tokens, Lua files not in
`load_order.json` (until 5.5 makes it hard-fail), and `gameState` fields absent
from `migrateGameState()` (until 5.3 makes it hard-fail). Warnings are the
staging area for future hard gates.

### 8.2 ⬜ Keep the scoreboard honest (P2, XS)

Section 3 is dated. Re-run section 2 at the end of each phase and update the
table in the same commit. A plan whose metrics are never re-measured is a wish
list.

### 8.3 ⬜ Retire this document when it is done (P2, XS)

Follow the established convention: when every item is ✅ or 🔎, fold the
outcome into [`CHANGELOG.md`](CHANGELOG.md), delete the file, and update
`agents.md`'s Documentation Map. Do not let it linger as a third historical
plan an agent has to read to discover it is finished.

---

## 9. Non-goals (deliberately not doing these)

| Not doing | Why |
|---|---|
| Introducing modules/`require` in Lua | TTS has no `require`. The single-namespace concatenation is a platform constraint, not a design mistake — see [`docs/tts-interface.md`](docs/tts-interface.md). |
| Splitting files just to hit 500 lines | The budget is a soft signal. `build_save.py` (1599 lines) is a coherent single-purpose script; splitting it would add navigation cost, not remove it. Split when a file has two *reasons to change*, not at a line count. |
| Chasing 100 % test coverage | The target is the *interactive* surface (5.1) and the state schema (5.3). Coverage of pure formatting helpers buys nothing. |
| Rewriting git history to shrink the pack | Breaks every clone for a one-time win. See 7.1. |
| Adding more prose reminders | [`tests/CLAUDE.md`](tests/CLAUDE.md) already states the rule this plan follows: *"Prefer a test over a reminder."* Every item above is a hook, a generator, or a test — not another paragraph to remember. |
| Sharding or parallelising the test suite | 17.4 s. Speeding it up saves nothing; keeping it under 30 s as it grows is the actual job. |

---

## 10. Suggested order

Ordered by value per unit of effort, and by dependency:

| # | Item | P | Effort | Unblocks |
|---|---|---|---|---|
| 1 | 4.1 SessionStart hook installs deps | P1 | S | every session |
| 2 | 4.2 Commit `.claude/` (permissions, regen hook) | P1 | S | 4.4 |
| 3 | 4.3 `scripts/check.py` one-command verify | P1 | S | 6.3 |
| 4 | 5.2 Single `gameState` initialiser | P1 | S | 5.3 |
| 5 | 5.5 Unlisted Lua file fails the build | P2 | S | — |
| 6 | **5.1 XML handler smoke test** | **P1** | **M** | 5.6 |
| 7 | 5.3 `gameState` schema map + declared-field guard | P1 | M | — |
| 8 | 5.4 Bind `CHAR_BRIEFINGS` to markdown | P2 | S | — |
| 9 | 6.1 Split `agents.md` | P2 | M | 6.3 |
| 10 | 6.2 `symbols.json` + `sym.py` | P2 | S | — |
| 11 | 5.6 Setup-walkthrough state test | P2 | M | — |
| 12 | 4.4, 6.3, 6.4, 7.1–7.4, 8.1 | P2/P3 | S each | — |

Items 1–5 are all small and independent: a single session can land the whole
bootstrap phase plus two reliability fixes. Item 6 is the one worth spending a
full session on alone.

**Definition of done for any item:** the change is in, a test or hook enforces
it (not a doc sentence), `python -m pytest tests` is green, the scoreboard row
in section 3 is updated, and the item is marked ✅ with a one-line note on what
was actually done — including "🔎, no action" if investigation says the problem
is not real. The two retired plans both used that convention and it is why
their leftovers were still legible a month later.
