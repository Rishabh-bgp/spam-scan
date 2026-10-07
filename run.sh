#!/usr/bin/env bash
# Create venv, install deps, train if needed, and start the app.
set -euo pipefail
cd "$(dirname "$0")"

PY=python3
command -v "$PY" >/dev/null 2>&1 || PY=python

if [ ! -d .venv ]; then
  echo "Creating virtual environment..."
  "$PY" -m venv .venv
fi
VENV_PY=.venv/bin/python

echo "Installing dependencies..."
"$VENV_PY" -m pip install --quiet --upgrade pip
"$VENV_PY" -m pip install --quiet -r requirements.txt

if [ ! -f model.joblib ] && [ ! -f data/combined.csv.gz ]; then
  echo "Training data missing; installing data-prep extras (pandas, pyarrow)..."
  "$VENV_PY" -m pip install --quiet -r requirements-data.txt
fi

if [ ! -f model.joblib ]; then
  echo "Training model..."
  "$VENV_PY" train.py
fi

echo "Starting app at http://127.0.0.1:${PORT:-5000}"
exec "$VENV_PY" app.py
