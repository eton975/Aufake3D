#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if (( $# != 2 )); then
  echo 'Usage: bash INSTALL_WINE_LINUX.sh alice2011|alice2000|quake3|halflife /absolute/path/to/your/game.exe' >&2
  exit 2
fi
python3 "$HERE/Tools/aufake3d.py" install --profile "$1" --game-exe "$2"
echo 'Use RUN_AUFAKE3D_WINE.sh beside your game EXE. Original EXE unchanged.'
