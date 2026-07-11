# Session logs

Paste each playtest's **Copy Session Log** export (Week in Review panel → the
JSON lands in the TTS Notes panel) into a file here, one session per file:

```
playtest/sessions/2026-07-18_5p_standard_full.json
playtest/sessions/2026-07-18_5p_standard_rotation.json
```

Name files `date_players_difficulty_turnstyle.json` — the analyzer doesn't
parse names (everything it needs is inside the JSON), but humans scanning the
directory do.

Then aggregate:

```bash
python scripts/analyze_sessions.py
```

Commit the logs — the evidence trail is part of the project.
