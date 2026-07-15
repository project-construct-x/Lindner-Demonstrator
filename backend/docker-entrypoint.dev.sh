#!/bin/sh
set -e

if [ ! -x .venv/bin/uvicorn ]; then
  echo "Creating .venv and installing dependencies..."
  python -m venv .venv
  .venv/bin/pip install --no-cache-dir -r requirements.txt
fi

export VIRTUAL_ENV=/backend/.venv
export PATH="/backend/.venv/bin:$PATH"

exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /backend
