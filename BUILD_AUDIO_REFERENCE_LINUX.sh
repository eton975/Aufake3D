#!/usr/bin/env bash
# Standalone Alice five-way audio-reference packaging; no core DLL compilation.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'ERROR: Python 3.10+ is required.' >&2
  exit 1
fi
exec python3 scripts/build_audio_reference.py "$@"
