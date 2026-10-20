#!/bin/sh
set -e

# Keep bind-mounted dirs writable on the host after container-side npm installs.
fix_bind_mount_ownership() {
  if [ "$(id -u)" != 0 ]; then
    return 0
  fi

  owner=$(stat -c '%u:%g' package.json 2>/dev/null || true)
  if [ -n "$owner" ]; then
    for path in node_modules dist; do
      if [ -e "$path" ]; then
        chown -R "$owner" "$path"
      fi
    done
  fi
}

# node_modules from the host may target a different libc (e.g. after Alpine-based installs).
# Reinstall when the Linux glibc native binding for Vite/Rolldown is missing.
ROLLDOWN_BINDING=node_modules/@rolldown/binding-linux-x64-gnu

if [ ! -d "$ROLLDOWN_BINDING" ] || [ ! -d node_modules/qrcode.vue ]; then
  echo "Installing npm dependencies for container (linux-x64-gnu)..."
  rm -rf node_modules
  npm ci
  fix_bind_mount_ownership
fi

exec npm run dev -- --host 0.0.0.0 --port 3000
