#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Wine process launcher
# Sets up the Wine execution environment and A3D diagnostic log path. This is launch
# plumbing, not a native audio engine; a genuine game installation and 32-bit Wine
# support remain required.
# Execute any installed 32-bit game through Wine with its own working directory.
set -euo pipefail
if (( $# < 1 )); then echo 'Usage: run_game_wine.sh /absolute/path/to/game.exe [game arguments...]' >&2; exit 2; fi
GAME=$(realpath -- "$1"); shift
[[ -f "$GAME" ]] || { echo "Missing executable: $GAME" >&2; exit 2; }
DIR=$(dirname -- "$GAME")
BASE=$(basename -- "$GAME")
export WINEPREFIX="${A3D_DROPIN_WINEPREFIX:-$HOME/.local/share/a3d-portable/wineprefix-x86}"
mkdir -p "$(dirname "$WINEPREFIX")"
# wineboot initializes an isolated prefix before wine attempts to chdir into it.
if [[ ! -f "$WINEPREFIX/system.reg" ]]; then
  echo "Initialising Wine prefix $WINEPREFIX"
  WINEARCH=win32 wineboot --init
fi
cd -- "$DIR"
export A3D_PROBE_LOG="${A3D_PROBE_LOG:-$DIR/a3d-portable.log}"
exec wine "./$BASE" "$@"
