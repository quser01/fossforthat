#!/usr/bin/env bash
# Refresh GitHub stats then rebuild static pages.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v node >/dev/null 2>&1; then
  node scripts/refresh.js
else
  echo "node not found; using Python fallback…"
  python3 scripts/refresh.py
fi

python3 scripts/build.py
echo "Refresh + build done."
