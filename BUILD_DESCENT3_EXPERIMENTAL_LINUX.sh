#!/usr/bin/env bash
# Opt-in Descent 3 synthetic API probe + source-adapter object; NOT playable game support.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec python3 scripts/build_descent3_experimental.py "$@"
