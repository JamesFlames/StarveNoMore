# tests/ — pytest suite (no TTS required)

```bash
python scripts/check.py         # regenerate → build → test → lint (finish with this)
python -m pytest tests          # the suite alone, when iterating on one test
```

Dependencies install automatically via the committed `SessionStart` hook
([`.claude/README.md`](../.claude/README.md)); otherwise
`pip install pytest lupa Pillow`.

Runs the real concatenated Lua bundle headlessly under Lua 5.2 (`lupa`) with
`tts_stub.lua` faking the TTS API, plus CSV/XML/color/lint quality gates and
build/publish checks. Shared fixtures live in `conftest.py` (`lua_sources`,
`load_order`, `bundle`, `xml_source`, `card_ids`).

## Conventions

- **Prefer a test over a reminder:** if a change requires remembering to update a
  second file, add the test that remembers instead. The suite already enforces
  generated-file freshness, Dawn card↔handler pairing, XML↔Lua contracts,
  sim↔lua constant mirrors, and more (see the "Key Conventions" list in
  [`../agents.md`](../agents.md)'s Key Conventions).
- Tests script dice by redefining `gameRoll`; never rely on real randomness.
- One topic per module — mirror the Lua/design area under test. If a test module
  passes ~500 lines, split it and keep the shared fixture in `conftest.py`.
- Extend `tts_stub.lua` when the code uses a TTS API the stub doesn't cover yet.
- **Scanning the whole tree?** Use `conftest.walk_repo()` / `repo_files()`, never
  a private `os.walk(ROOT)` (`test_repo_walk.py` enforces this). They prune
  `SKIP_DIRS` — including `.claude/worktrees/`, which holds *entire second
  checkouts of this repo*, so an unpruned walk validates two revisions at once.
  Walking one subtree (`os.walk(LUA_DIR)`) needs no such care.

Full per-module coverage map: [`../docs/agents/test-suite.md`](../docs/agents/test-suite.md).
