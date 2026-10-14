#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]] || ! .venv/bin/python -c 'import ultralytics, PIL, numpy' >/dev/null 2>&1; then
  echo 'First run: installing Python dependencies (internet required)...'
  if command -v uv >/dev/null 2>&1; then
    if [[ ! -x .venv/bin/python ]]; then uv venv --python 3.12 .venv; fi
    uv pip install --python .venv/bin/python -r requirements.txt
  else
    if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
    .venv/bin/python -m pip install -r requirements.txt
  fi
fi
if [[ ! -f frontend/dist/index.html ]]; then
  npm --prefix frontend install
  npm --prefix frontend run build
fi
exec .venv/bin/python server.py "$@"
