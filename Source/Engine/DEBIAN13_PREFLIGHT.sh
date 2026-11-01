#!/usr/bin/env bash
# Read-only Debian 13/Wine 32-bit readiness check. Does not install anything.
set -uo pipefail
printf 'A3D v0.6.12 / Debian 13 Wine preflight\n'
if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  printf 'OS: %s (version %s)\n' "${PRETTY_NAME:-unknown}" "${VERSION_ID:-unknown}"
  if [[ "${ID:-}" != debian || "${VERSION_ID:-}" != 13* ]]; then
    echo 'NOTE: Not detected as Debian 13; generic Wine checks still apply.'
  fi
fi
if command -v dpkg >/dev/null 2>&1; then
  main_arch=$(dpkg --print-architecture)
  foreign_arch=$(dpkg --print-foreign-architectures | tr '\n' ' ')
  printf 'Debian architecture: %s; multiarch: %s\n' "$main_arch" "${foreign_arch:-none}"
  [[ "$main_arch" == amd64 ]] || echo 'WARNING: This release expects an amd64 Linux system for Debian 13.'
  [[ " $foreign_arch " == *' i386 '* ]] || echo 'NOTE: i386 multiarch not enabled. See LINUX_WINE_SETUP.md (modern WoW64 can sometimes work).'
fi
if ! command -v "${A3D_WINE_EXECUTABLE:-wine}" >/dev/null 2>&1; then
 echo 'NOT READY: Wine not found. Follow LINUX_WINE_SETUP.md.' >&2
 exit 4
fi
printf 'Wine: '; "${A3D_WINE_EXECUTABLE:-wine}" --version || exit 5
if command -v dpkg-query >/dev/null 2>&1; then
 printf 'wine32 package: '
 dpkg-query -W -f='${Status} ${Version}\n' wine32:i386 2>/dev/null || echo 'not installed (WoW64 may be available)'
fi
printf 'WINEPREFIX: %s\n' "${WINEPREFIX:-$HOME/.wine (default)}"
if command -v pactl >/dev/null 2>&1; then
  printf 'Sound server: '; pactl info 2>/dev/null | grep '^Server Name:' | head -1 || true
fi
echo 'Preflight PASS: executable Wine found; verify real PE32 execution with game/COM self-tests.'
