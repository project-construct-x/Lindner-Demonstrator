#!/bin/sh
set -e

# node_modules from the host may target a different libc (e.g. after Alpine-based installs).
# Reinstall when the Linux glibc native binding for Vite/Rolldown is missing.
ROLLDOWN_BINDING=node_modules/@rolldown/binding-linux-x64-gnu

if [ ! -d "$ROLLDOWN_BINDING" ] || [ ! -d node_modules/qrcode.vue ]; then
  echo "Installing npm dependencies for container (linux-x64-gnu)..."
  rm -rf node_modules
  npm ci
fi

exec npm run dev -- --host 0.0.0.0 --port 3000
