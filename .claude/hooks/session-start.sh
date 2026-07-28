#!/bin/bash
# SessionStart hook — install the Python packages the test suite needs.
#
# Without this, a fresh container clones the repo and `python -m pytest tests`
# fails with "No module named pytest", which reads like a broken repo rather
# than a missing dependency. (A `pytest` shim on PATH can make that worse: it
# resolves, but not for the interpreter the tests run under.) Every agent
# rediscovered this and burned turns on it before its first green run.
#
# Idempotent: pip no-ops once the packages are present, so re-running on
# resume/clear/compact costs a second or two.
set -euo pipefail

# Local machines already have a working environment (and may use a venv we
# should not write into). This is purely a remote-container fixup.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# pytest + lupa run the suite; Pillow is needed by the art generators that
# scripts/regenerate_all.py can invoke; ruff is the linter CI runs on
# scripts/ and tests/ (see .github/workflows/tests.yml).
#
# --root-user-action needs pip >= 22.1; retry without it (and without the
# stderr mask, so a genuine failure is still visible) on anything older.
python -m pip install --quiet --disable-pip-version-check \
    --root-user-action=ignore pytest lupa Pillow ruff 2>/dev/null \
  || python -m pip install --quiet --disable-pip-version-check \
    pytest lupa Pillow ruff

# luacheck is a hard gate in CI (.github/workflows/tests.yml), so it should be
# runnable here too — scripts/check.py runs it when present and reports it as
# skipped when not. Best-effort: apt may be unavailable or offline, and a
# missing linter must never block a session.
if ! command -v luacheck >/dev/null 2>&1; then
  apt-get install -y -qq lua-check >/dev/null 2>&1 || true
fi

if command -v luacheck >/dev/null 2>&1; then
  echo "Starve No More: dependencies ready (pytest, lupa, Pillow, ruff, luacheck)."
else
  echo "Starve No More: dependencies ready (pytest, lupa, Pillow, ruff)."
  echo "  luacheck unavailable — scripts/check.py will report the lint stage as skipped."
fi
echo "Verify a change with: python scripts/check.py"
