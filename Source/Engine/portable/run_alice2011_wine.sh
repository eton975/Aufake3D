#!/usr/bin/env bash
# A3D v0.6.0 Alice 2011 + VorpalFix 4.2.1 launcher.
# NO new prefix is silently created. Existing Wine/Proton setup is respected.
# The 32-bit bridge launches the adjacent unmodified alice.exe suspended, installs
# a version-pinned RAM-only selector hook, then resumes the game. VorpalFix is
# loaded by Wine's native-first winmm override; it is never replaced by us.
set -euo pipefail
if (( $# < 1 )); then
  echo 'Usage: run_alice2011_wine.sh /path/to/Alice1/bin/alice.exe [game args...]' >&2
  exit 2
fi
EXE=$(realpath -- "$1"); shift
[[ "${EXE##*/}" == 'alice.exe' ]] || { echo 'Use original remaster executable named alice.exe (lowercase).' >&2; exit 2; }
DIR=$(dirname -- "$EXE")
for item in winmm.dll VorpalFix.ini a3dapi.dll alice-a3d2011-bridge.exe; do
  [[ -f "$DIR/$item" ]] || { echo "Missing prerequisite: $DIR/$item" >&2; exit 2; }
done
for item in mss32.dll mssa3d2.m3d; do
  [[ -f "$DIR/SndDrivers/$item" ]] || { echo "Missing original Miles module: $DIR/SndDrivers/$item" >&2; exit 2; }
done
# Preserve existing overrides for other game requirements. In Wine/Proton,
# winmm=n,b explicitly loads VorpalFix's game-local winmm.dll first.
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:+${WINEDLLOVERRIDES};}winmm=n,b"
if [[ -z "${A3D_PROBE_LOG:-}" ]]; then
  if command -v winepath >/dev/null 2>&1; then
    A3D_PROBE_LOG="$(winepath -w "$DIR/a3d-portable.log")"
  else
    A3D_PROBE_LOG="$DIR/a3d-portable.log"
  fi
  export A3D_PROBE_LOG
fi
cd -- "$DIR"
echo "Alice 2011/VorpalFix bridge; prefix: ${WINEPREFIX:-<Wine default>}; A3D log: $A3D_PROBE_LOG" >&2
exec "${A3D_WINE_EXECUTABLE:-wine}" ./alice-a3d2011-bridge.exe "$@"
