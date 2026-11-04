#!/usr/bin/env bash
set -euo pipefail
# Audio reliability baseline: keep the WinMM position pump on without tracing.
export A3D_LATENCY_TRACE=0 A3D_WAVEOUT_POSITION_PROBE=1 A3D_WAVEOUT_POSITION_INTERVAL=4
export A3D_WAVEOUT_SCHEDULE_TEST='' A3D_SHORT_SFX_DECLICK=1

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ -f alice.exe && -f alice-a3d-bridge.exe ]] || { echo 'Missing classic Alice or compatibility bridge' >&2; exit 2; }
export A3D_MASTER_GAIN="${A3D_MASTER_GAIN:-5.0}"
export A3D_HRTF_MODE="${A3D_HRTF_MODE:-reference}"
export A3D_WAVEOUT_QUEUE_HEADERS="${A3D_WAVEOUT_QUEUE_HEADERS:-6}"
export A3D_WAVEOUT_SUBBLOCKS="${A3D_WAVEOUT_SUBBLOCKS:-1}"
export WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
exec "${A3D_WINE_EXECUTABLE:-wine}" ./alice-a3d-bridge.exe "$@"
