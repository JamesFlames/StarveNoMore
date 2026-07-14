# tests/ — pytest suite (no TTS required)

```bash
python -m pytest tests          # needs: pip install pytest lupa
```

Runs the real concatenated Lua bundle headlessly under Lua 5.2 (`lupa`) with
`tts_stub.lua` faking the TTS API, plus CSV/XML/color/lint quality gates and
build/publish checks. Shared fixtures live in `conftest.py` (`lua_sources`,
`load_order`, `bundle`, `xml_source`, `card_ids`).

## Conventions

- **Prefer a test over a reminder:** if a change requires remembering to update a
  second file, add the test that remembers instead. The suite already enforces
  generated-file freshness, Dawn card↔handler pairing, XML↔Lua contracts,
  sim↔lua constant mirrors, and more (see the "Key Conventions" list in
  [`../agents.md`](../agents.md)).
- Tests script dice by redefining `gameRoll`; never rely on real randomness.
- One topic per module — mirror the Lua/design area under test. If a test module
  passes ~500 lines, split it and keep the shared fixture in `conftest.py`.
- Extend `tts_stub.lua` when the code uses a TTS API the stub doesn't cover yet.

Full per-module coverage map: the "Test Suite" section of [`../agents.md`](../agents.md).
