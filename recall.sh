#!/bin/sh
# Usage: ./recall.sh run | status | power | review | rescore | export
cd "$(dirname "$0")" || exit 1
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
exec "$PY" -m recall "$@"
