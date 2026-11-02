#!/usr/bin/env bash
set -euo pipefail
# Audio reliability baseline: keep the WinMM position pump on without tracing.
export A3D_LATENCY_TRACE=0 A3D_WAVEOUT_POSITION_PROBE=1 A3D_WAVEOUT_POSITION_INTERVAL=4
export A3D_WAVEOUT_SCHEDULE_TEST='' A3D_SHORT_SFX_DECLICK=1

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ -f quake3.exe ]] || { echo 'Missing original quake3.exe' >&2; exit 2; }
export A3D_MASTER_GAIN="${A3D_MASTER_GAIN:-5.0}"
export A3D_HRTF_MODE="${A3D_HRTF_MODE:-fast}"
export A3D_GEOMETRY_TRACE="${A3D_GEOMETRY_TRACE:-1}"
export A3D_GEOMETRY_RETRACE_BLOCKS="${A3D_GEOMETRY_RETRACE_BLOCKS:-4}"
export A3D_REVERB_WET="${A3D_REVERB_WET:-0.14}"
export A3D_HRTF_TAPS="${A3D_HRTF_TAPS:-56}"
export A3D_VOICE_LIMIT="${A3D_VOICE_LIMIT:-128}"
export A3D_WAVEOUT_QUEUE_HEADERS="${A3D_WAVEOUT_QUEUE_HEADERS:-6}"
export A3D_WAVEOUT_SUBBLOCKS="${A3D_WAVEOUT_SUBBLOCKS:-1}"
export A3D_Q3_DMA_CLOCK="${A3D_Q3_DMA_CLOCK:-0}"
export WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
exec "${A3D_WINE_EXECUTABLE:-wine}" ./quake3.exe +set s_mixahead 0.35 +set s_mixPreStep 0.05 "$@"
