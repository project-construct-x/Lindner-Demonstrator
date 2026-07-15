#!/bin/sh
set -e

if [ ! -d node_modules ]; then
  echo "Installing npm dependencies..."
  npm ci
fi

exec npm run dev -- --host 0.0.0.0 --port 3000
