#!/usr/bin/env bash
# Classic American McGee's Alice (2000), A3D 2.0 launcher for A3D v0.6.0.
# Launches the adjacent alice-a3d-bridge.exe, which spawns stock alice.exe
# and adds the a3d2 => Aureal A3D 2.0 (TM) mapping IN CHILD RAM ONLY.
# Do not use this launcher for the 2011/VorpalFix remaster.
set -euo pipefail
if (( $# < 1 )); then
  echo 'Usage: bash run_alice2000_wine.sh /absolute/path/to/alice.exe [game args...]' >&2
  exit 2
fi
EXE=$(realpath -- "$1"); shift
[[ "${EXE##*/}" == 'alice.exe' ]] || { echo 'Classic game must be named alice.exe (case sensitive).' >&2; exit 2; }
DIR=$(dirname -- "$EXE")
for file in alice-a3d-bridge.exe alice-a3d-bridge.exe.manifest a3dapi.dll alice.exe.manifest; do
  [[ -f "$DIR/$file" ]] || { echo "Missing: $DIR/$file" >&2; exit 2; }
done
# Respect a user-selected prefix. If none is supplied, reuse the prior
# known-good A3D drop-in prefix when it already exists.
if [[ -z "${WINEPREFIX:-}" ]]; then
  if [[ -n "${A3D_DROPIN_WINEPREFIX:-}" ]]; then
    export WINEPREFIX="$A3D_DROPIN_WINEPREFIX"
  elif [[ -f "$HOME/.local/share/a3d-dropin/wineprefix-v040/system.reg" ]]; then
    export WINEPREFIX="$HOME/.local/share/a3d-dropin/wineprefix-v040"
  fi
fi
export WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
# When available, ask winepath to turn the host path into a Windows path.
if [[ -z "${A3D_PROBE_LOG:-}" ]]; then
  if command -v winepath >/dev/null 2>&1; then
    A3D_PROBE_LOG=$(winepath -w "$DIR/a3d-portable.log") || { echo 'winepath failed' >&2; exit 1; }
  else
    A3D_PROBE_LOG="$DIR/a3d-portable.log"
  fi
  export A3D_PROBE_LOG
fi
cd -- "$DIR"
echo "Classic Alice 2000 A3D2 bridge; prefix: ${WINEPREFIX:-<Wine default>}" >&2
exec "${A3D_WINE_EXECUTABLE:-wine}" ./alice-a3d-bridge.exe "$@"
