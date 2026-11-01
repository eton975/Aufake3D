#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Installer / launcher support
# Supports reversible game-local deployment and diagnostics; the original executable
# and vendor Miles modules should remain untouched.
# v0.4.1 launcher hotfix: initialise the isolated prefix before calling winepath.
# Does not register COM, change system drivers or modify the game binary.
set -euo pipefail

if (( $# < 1 )); then
  echo 'Usage: bash run_wine.sh "/absolute/path/to/Alice-A3D2.exe" [game args...]' >&2
  exit 2
fi
for cmd in wine winepath wineboot realpath; do
  command -v "$cmd" >/dev/null || { echo "Required command not found: $cmd" >&2; exit 2; }
done

exe="$(realpath "$1")"; shift
[[ -f "$exe" ]] || { echo "Missing game executable: $exe" >&2; exit 2; }
gamedir="$(dirname "$exe")"
[[ -f "$gamedir/a3dapi.dll" ]] || { echo 'Missing installed a3dapi.dll' >&2; exit 2; }
[[ -f "$exe.manifest" ]] || { echo "Missing ${exe}.manifest" >&2; exit 2; }

# Preserve the isolated v0.4.0/v0.4.1 location; do not touch an earlier research prefix.
export WINEPREFIX="${A3D_DROPIN_WINEPREFIX:-$HOME/.local/share/a3d-dropin/wineprefix-v040}"
if [[ ! -f "$WINEPREFIX/system.reg" ]]; then
  mkdir -p -- "$(dirname "$WINEPREFIX")"
  echo "Initialising isolated Wine prefix: $WINEPREFIX"
  wineboot --init
  if [[ ! -f "$WINEPREFIX/system.reg" ]]; then
    echo "Wine prefix initialisation did not create $WINEPREFIX/system.reg" >&2
    exit 1
  fi
fi

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
log="$gamedir/a3d-game-$stamp.log"
if ! win_log="$(winepath -w "$log")"; then
  echo 'winepath failed while resolving the A3D log path' >&2
  exit 1
fi
export A3D_PROBE_LOG="$win_log"
export WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"

echo "Wine process: $(basename "$exe")"
echo "Isolated Wine prefix: $WINEPREFIX"
echo "A3D_PROBE_LOG=$A3D_PROBE_LOG"
set +e
(cd "$gamedir" && wine "$(basename "$exe")" "$@")
status=$?
set -e
echo "Game exit code: $status"
echo "A3D COM log (if activation occurred): $log"
exit "$status"
