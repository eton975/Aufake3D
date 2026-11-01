#!/usr/bin/env bash
# A3D v0.6.0 FINAL: Quake III Arena 1.17 Wine launch preset.
# Works with native 32-bit Wine and the genuine Quake III 1.17 executable.
# Keeps all game data, game executable, and Wine registry untouched.
set -euo pipefail
if (( $# < 1 )); then
  echo 'Usage: run_quake3_117_wine.sh /absolute/path/to/quake3.exe [extra Quake arguments]' >&2
  exit 2
fi
EXE=$(realpath -- "$1"); shift
[[ -f "$EXE" && "${EXE##*/}" == 'quake3.exe' ]] || { echo 'Expected genuine quake3.exe' >&2; exit 2; }
DIR=$(dirname -- "$EXE")
[[ -f "$DIR/a3dapi.dll" ]] || { echo "Missing installed A3D DLL: $DIR/a3dapi.dll" >&2; exit 2; }
# Confirmed Quake III 1.17 Demo 1 listening preset (31 October 2026).
# Export A3D_* variables yourself to override any of these settings.
: "${A3D_GEOMETRY_TRACE:=1}"
: "${A3D_GEOMETRY_RETRACE_BLOCKS:=4}"
: "${A3D_REVERB_WET:=0.14}"
: "${A3D_HRTF_TAPS:=48}"
: "${A3D_VOICE_LIMIT:=128}"
: "${A3D_MASTER_GAIN:=5.0}"
: "${A3D_WAVEOUT_QUEUE_HEADERS:=3}"
: "${A3D_WAVEOUT_SUBBLOCKS:=2}"
: "${A3D_Q3_DMA_CLOCK:=0}"
export A3D_GEOMETRY_TRACE A3D_GEOMETRY_RETRACE_BLOCKS A3D_REVERB_WET
export A3D_HRTF_TAPS A3D_VOICE_LIMIT A3D_MASTER_GAIN
export A3D_WAVEOUT_QUEUE_HEADERS A3D_WAVEOUT_SUBBLOCKS A3D_Q3_DMA_CLOCK
# Diagnostics are optional. If explicitly requested, supply a Wine-friendly path:
# A3D_PROBE_LOG="$(winepath -w "$DIR/a3d-final.log")" ./run_quake3_117_wine.sh "$EXE"
cd -- "$DIR"
echo 'A3D v0.6.0 | Quake III Arena 1.17 | 48-tap HRTF, geometry/4, reverb 0.14' >&2
echo 'Warning: gain 5.0; turn down system/headphone volume before first run.' >&2
exec "${A3D_WINE_EXECUTABLE:-wine}" ./quake3.exe +set s_mixahead 0.35 +set s_mixPreStep 0.05 "$@"
