#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ -f Unreal.exe ]] || { echo 'Missing original game executable Unreal.exe' >&2; exit 2; }
export A3D_HRTF_MODE="${A3D_HRTF_MODE:-fast}"
export A3D_MASTER_GAIN="${A3D_MASTER_GAIN:-5.0}"
export A3D_WAVEOUT_QUEUE_HEADERS="${A3D_WAVEOUT_QUEUE_HEADERS:-6}"
export A3D_WAVEOUT_SUBBLOCKS="${A3D_WAVEOUT_SUBBLOCKS:-1}"
export WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
echo 'Experimental Unreal (1998/classic) compatibility probe; A3D activation not confirmed.' >&2
"${A3D_WINE_EXECUTABLE:-wine}" ./Unreal.exe "$@"
