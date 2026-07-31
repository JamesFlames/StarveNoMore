# Test Suite — Static Guards

The half of `tests/` that never runs the game: consistency between artifacts,
and the *classes* of bug that keep coming back. The modules that execute the
Lua bundle are in [test-suite.md](test-suite.md).

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

## Content and build artifacts

- **`test_csv_schema.py`** — every `content/*.csv`: required columns, unique/well-formed ids, stat ranges, starting-item characters/counts.
- **`test_cross_refs.py`** — cross-artifact drift: every Dawn card has a `DAWN_EFFECTS` entry (and no orphans), every `ongoingDawnEffects` flag has an `EFFECT_RULES` label, atlas grids hold every card **and** match `NumWidth/NumHeight` in build_save.py, hardcoded card ids in Lua exist in the CSVs, `MARKET_COSTS` covers the Market deck, every asset/sound URL resolves to a file on disk, `TOOLTIP_DATA` keys are real save tags, starting-hand decks match `cards_starting.csv`, and the standee slot constants in build_save.py mirror `helpers.lua`.
- **`test_generated_freshness.py`** — reruns the generators and fails if any generated `lua/*.lua` is stale (always restores the committed bytes).
- **`test_build_output.py`** — rebuilds the save, validates the JSON, and fails if `saves/StarveNoMore.json` is stale relative to the sources (restores committed bytes; run `python scripts/build_save.py` to fix).
- **`test_publish_build.py`** — a `--publish` build contains no `file:///` or `localhost` URL anywhere and never touches the committed dev save.
- **`test_media_budget.py`** — asset sizes stay inside the budget a Steam Workshop upload can carry.

## The Lua bundle, statically

- **`test_lua_statics.py`** — no global function/constant is defined twice across the concatenated bundle (the later definition would silently win); every lua file is deliberately placed in `LUA_LOAD_ORDER`.
- **`test_lua_reachability.py`** — **every global function must be reachable from something.** The worst bug class here is not a crash but a rule that was written and never wired to a button: the code is correct, its state consumers are correct, and nothing calls it, so it fails silently forever while the UI goes on describing it. A 2026-07 audit found nine at once — including `reviveCharacter`, so Telltale Hearts could be cooked but never spent. Allowlists only TTS engine callbacks (`onLoad`, `onSave`, `onObjectDrop`) and console-only playtest tools. A companion check bans `_G[name]` and `loadstring`, because dynamic dispatch would make an orphan indistinguishable from a live handler and quietly defeat the whole module. **A second check covers the one loophole in the first:** `tests/` counts as a reference, which is right for a real seam and is exactly how `doFlee` — §12.4's escape valve, with no button and six UI strings telling players to use it — stayed hidden through the 2026-07 audit. So a function the *game* never calls must be named in `TEST_SEAMS` on purpose, and a third check ejects an entry the moment it gains a real caller.
- **`test_lua_effect_flags.py`** — **every ongoing rule the game announces must be a rule something enforces.** Reachability one level down: not a function nothing calls but a *flag* nothing reads. A Dawn card sets `ongoingDawnEffects.moveCostPlus1`, chat announces it, the Active Rules panel lists it — and `doMove` has never heard of it. A 2026-07 audit found eleven at once. A flag counts as enforced only when a non-`ui_` file reads it, since printing a rule is what the panel is for and was exactly what all eleven did instead. `DISPLAY_ONLY` allowlists the panel-only flags with a reason each; companion checks catch a flag that gains an enforcer, and a card-set flag the panel never shows. Behaviour: `test_lua_ongoing_effects.py`.
- **`test_lua_lint.py`** — runs `luacheck lua` against the generated `.luacheckrc` when luacheck is installed (skips otherwise; CI's luacheck job always runs it), and asserts `.luacheckrc` is still the generated file.
- **`test_gamestate_schema.py`** — every `gameState` field is either declared in `migrateGameState()` or listed as deliberately transient, and never both.

## Printed-rule wiring

- Whether each Market card, threat card, location special and boss Trophy
  actually does what it prints — five modules, one per content family, each
  requiring an unwired rule to be declared with a reason:
  [content-wiring-guards.md](content-wiring-guards.md).

## UI contracts

- **`test_xml_lua_contract.py`** — every UI id the Lua targets exists in the `xml/` files; every XML `onClick` and Lua `click_function` names a defined function; XML ids are unique across all files.
- **`test_xml_quality.py`** — the silent TTS failure modes: XML well-formedness, no literal `\n` in attributes (renders as text), every color parseable by TTS (hex length 3/4/6/8; rgb()/rgba() components must be 0-1 floats — 0-255 values clamp to white; checked in the XML **and** Lua color literals), `<Image image=...>` names resolve to `CustomUIAssets` + files on disk, and the per-character UI ids the Lua composes dynamically all exist.
- **`test_tts_api_surface.py`** — a curated allowlist of the TTS singleton API, checked in both directions: Lua may only *call* what exists, and `tts_stub.lua` may only *define* what exists (a stub that invents API makes the suite confirm bugs instead of catching them).

## Docs and tooling

- **`test_doc_links.py` / `test_doc_file_refs.py` / `test_doc_section_refs.py`** — relative markdown links resolve, inline source filenames in the navigation docs still exist, and a `Foo.md §N` citation points at a section `Foo.md` really has (with the titled form checked against the heading's actual title).
- **`test_doc_agents_split.py`** — each `docs/agents/` topic file stays under its ~2.5k-token budget and appears in **both** jump tables (`agents.md` and `docs/agents/README.md`).
- **`test_repo_walk.py`** — the shared repo walker (`conftest.walk_repo`/`repo_files`), which prunes `SKIP_DIRS` at any depth so a whole-tree scan cannot descend into `.claude/worktrees/` — a complete second checkout of this repo, whose stale copies once turned 11 correct doc citations red. Bans a private `os.walk(ROOT)` in any test module.
- **`test_script_console.py`** — the command-line scripts survive a redirected stdout. Python only asks the *terminal* for an encoding; pipe it and Windows falls back to cp1252, so `check.py` died on `regenerate_all.py`'s `→` the moment anything captured its output. `scripts/utf8_console.py` fixes both halves (own streams, plus `PYTHONIOENCODING` for every child stage).

## Recurring bug classes

- **`test_regression_guards.py`** — eight generic guards for the bug *classes*
  that keep coming back (overlapping spawns, upside-down text gadgets, button
  contrast, unguarded `takeObject` handles, tags that don't exist in the save,
  text naming deleted components, hardcoded `of 7` / `/ 30`, uninitialised
  `gameState` fields). One file per lesson learned:
  [regression-guards.md](regression-guards.md).
