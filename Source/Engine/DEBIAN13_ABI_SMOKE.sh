#!/usr/bin/env bash
# Under a real Debian 13 Wine installation: validate PE32 loading and COM
# before opening copyrighted games. This is NOT a real audio/gameplay test.
set -euo pipefail
cd -- "$(dirname -- "$(realpath -- "$0")")"
wine_exec="${A3D_WINE_EXECUTABLE:-wine}"
command -v "$wine_exec" >/dev/null || { echo 'Wine missing: run DEBIAN13_PREFLIGHT.sh'; exit 4; }
cd Alice2000
[[ -f a3dapi.dll && -f a3d-comtest.exe.manifest ]] || { echo 'Missing binary or COM test manifest'; exit 3; }
export A3D_LOG=0
export A3D_MASTER_GAIN=5.0
export WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
echo 'Testing 32-bit PE DLL exports with Wine...'
"$wine_exec" ./a3d-selftest.exe
echo 'Testing registration-free COM activation with Wine...'
"$wine_exec" ./a3d-comtest.exe
echo 'A3D v0.6.12 PE32 loader/COM smoke tests passed. Run actual games for sound validation.'
