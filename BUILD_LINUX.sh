#!/usr/bin/env bash
# Build PE32 Windows binaries on Linux; Wine is NOT required for compilation.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! command -v python3 >/dev/null 2>&1; then
  printf 'ERROR: Python 3.10+ missing. Debian/Ubuntu: sudo apt install python3\n' >&2
  exit 1
fi
exec python3 scripts/build_pinned.py "$@"
