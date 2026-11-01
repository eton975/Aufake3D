#!/usr/bin/env bash
set -euo pipefail
# Audio reliability baseline: keep the WinMM position pump on without tracing.
export A3D_LATENCY_TRACE=0 A3D_WAVEOUT_POSITION_PROBE=1 A3D_WAVEOUT_POSITION_INTERVAL=4
export A3D_WAVEOUT_SCHEDULE_TEST='' A3D_SHORT_SFX_DECLICK=1

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ -f hl.exe ]] || { echo 'Missing original hl.exe' >&2; exit 2; }
export A3D_MASTER_GAIN="${A3D_MASTER_GAIN:-5.0}"
export WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
echo 'Half-Life 1.0.1.1 Wine A3D compatibility not yet verified' >&2
exec "${A3D_WINE_EXECUTABLE:-wine}" ./hl.exe +s_eax 0 +s_a3d 1 "$@"
