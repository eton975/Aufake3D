#!/usr/bin/env bash
set -euo pipefail
# Audio reliability baseline: keep the WinMM position pump on without tracing.
export A3D_LATENCY_TRACE=0 A3D_WAVEOUT_POSITION_PROBE=1 A3D_WAVEOUT_POSITION_INTERVAL=4
export A3D_WAVEOUT_SCHEDULE_TEST='' A3D_SHORT_SFX_DECLICK=1

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ -f alice.exe && -f 'SndDrivers/a3d_mss_real.dll' ]] || { echo 'Missing Alice or saved original Miles' >&2; exit 2; }
export A3D_MASTER_GAIN="${A3D_MASTER_GAIN:-5.0}"
export A3D_MILES_MODE=activate A3D_MILES_ALIAS_UNKNOWN=0 A3D_MILES_REQUIRE_CLI_A3D2=1
export A3D_MILES_DISPLAY_CANONICAL=1 A3D_MILES_COM_PROBE=0
export A3D_WAVEOUT_QUEUE_HEADERS=6 A3D_WAVEOUT_SUBBLOCKS=1 A3D_RENDER_SNAPSHOT=0
export A3D_WAVEOUT_ADAPTIVE=0 A3D_WAVEOUT_EVENT=1 A3D_WAVEOUT_PRIORITY=1
export WINEDLLOVERRIDES="mss32=n,b;a3dapi=n,b;a3d=n,b;winmm=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
echo 'Aufake3D Alice2011 A3D2 (Wine test not yet validated); gain 5.0 default.' >&2
# Experimental under Wine; Windows gameplay test passed with this RAM-only bridge.
[[ -f alice-a3d2011-native.exe ]] || { echo 'Missing Alice 2011 RAM selector bridge' >&2; exit 2; }
[[ -f a3d-miles-local.manifest ]] || { echo 'Missing local A3D manifest' >&2; exit 2; }
[[ ! -e alice.exe.manifest ]] || { echo 'Existing alice.exe.manifest: refusing to overwrite' >&2; exit 5; }
cp -- a3d-miles-local.manifest alice.exe.manifest
trap 'rm -f -- alice.exe.manifest' EXIT
"${A3D_WINE_EXECUTABLE:-wine}" ./alice-a3d2011-native.exe "$@"
