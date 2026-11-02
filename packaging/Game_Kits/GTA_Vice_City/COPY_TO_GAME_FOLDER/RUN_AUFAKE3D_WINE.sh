#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ -f "gta-vc.exe" && -f mss32.dll && -f a3d.dll && -f a3dapi.dll ]] || { echo 'Original game/Miles or Aufake3D files missing' >&2; exit 2; }
[[ -f mss/mssa3d2.m3d ]] || echo 'WARNING: no original mss/mssa3d2.m3d found' >&2
export A3D_HRTF_MODE="${A3D_HRTF_MODE:-reference}"
export A3D_MASTER_GAIN="${A3D_MASTER_GAIN:-5.0}"
export A3D_WAVEOUT_QUEUE_HEADERS="${A3D_WAVEOUT_QUEUE_HEADERS:-6}"
export A3D_WAVEOUT_SUBBLOCKS="${A3D_WAVEOUT_SUBBLOCKS:-1}"
export WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
echo 'Experimental GTA A3D probe; no support claim. Original Miles remains unchanged.' >&2
"${A3D_WINE_EXECUTABLE:-wine}" ./gta-vc.exe "$@"
