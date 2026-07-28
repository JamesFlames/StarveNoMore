#!/bin/bash
# PostToolUse hook — regenerate SYMBOLS.md + .luacheckrc after any lua/ edit.
#
# "Rerun generate_symbol_index.py after touching lua/" is a rule written in
# three CLAUDE.md files that the agent has to *remember*. The freshness test
# (tests/test_generated_freshness.py) catches a miss, but only after a full
# suite run. This hook makes it unmissable and free: the generator is ~0.2 s
# and idempotent, so a no-op edit costs nothing.
#
# The freshness test stays — the hook is the fast path, the test is the
# guarantee (a hook can be disabled; CI cannot).
set -euo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

# PostToolUse feeds the tool call as JSON on stdin. Pull out the edited path;
# stay silent (exit 0) for anything that is not a hand-written lua/ file.
payload="$(cat)"
path="$(printf '%s' "$payload" | python -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
p = (d.get("tool_input") or {}).get("file_path") or ""
print(p)
' 2>/dev/null || true)"

case "$path" in
  *lua/*.lua) ;;
  *) exit 0 ;;
esac

# Generated lua/ files are written *by* generators; editing one by hand is
# already a mistake the freshness test reports. Do not paper over it here.
if head -3 "$path" 2>/dev/null | grep -qi 'AUTO-GENERATED'; then
  exit 0
fi

if ! python -c "import sys" 2>/dev/null; then
  exit 0
fi

if python "$ROOT/scripts/generate_symbol_index.py" >/dev/null 2>&1; then
  exit 0
fi

# Non-blocking: report on stderr with exit 2 so the agent sees it and can fix
# the generator, rather than silently shipping a stale index.
echo "generate_symbol_index.py failed after editing $path — SYMBOLS.md/.luacheckrc may be stale. Run: python scripts/check.py" >&2
exit 2
