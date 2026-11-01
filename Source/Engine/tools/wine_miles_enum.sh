#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
# Enumerate the user's installed Miles 3D providers without launching Alice or opening sound output.
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo 'Usage: bash tools/wine_miles_enum.sh "/absolute/path/to/Alice.exe"' >&2; exit 2
fi
for cmd in wine realpath tar grep; do command -v "$cmd" >/dev/null || { echo "Missing: $cmd" >&2; exit 2; }; done
exe="$(realpath "$1")"
[[ -f "$exe" ]] || { echo "Missing game: $exe" >&2; exit 2; }
gamedir="$(dirname "$exe")"
snd=""
for directory in "$gamedir/SndDrivers" "$gamedir/snddrivers" "$gamedir/SNDDRIVERS" "$gamedir"; do
  if [[ -f "$directory/mss32.dll" ]]; then snd="$directory"; break; fi
done
[[ -n "$snd" ]] || { echo 'mss32.dll was not found beside Alice.exe or in SndDrivers' >&2; exit 3; }
here="$(cd "$(dirname "$0")/.." && pwd)"
probe="$here/deliverables/a3d-miles-enum.exe"
[[ -f "$probe" ]] || { echo "Missing compiled probe: $probe" >&2; exit 3; }
export WINEPREFIX="${A3D_LAB_PREFIX:-$HOME/.local/share/alice-a3d2/wineprefix}"
[[ -f "$WINEPREFIX/system.reg" ]] || { echo "Isolated Wine prefix not found: $WINEPREFIX" >&2; exit 3; }
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
res="$HOME/alice-a3d2-miles-enum-$stamp"
mkdir -p "$res"
{
  echo "WINE_VERSION=$(wine --version)"
  echo "PREFIX=$WINEPREFIX"
  echo "MILES_FOLDER=$snd"
  echo "A3D1_PLUGIN_PRESENT=$(test -f "$snd/mssa3d.m3d" && echo yes || echo no)"
  echo "A3D2_PLUGIN_PRESENT=$(test -f "$snd/mssa3d2.m3d" && echo yes || echo no)"
  echo 'TEST=read-only Miles provider enumeration; Alice.exe not launched'
} > "$res/context.txt"
set +e
(cd "$snd" && WINEDEBUG='-all,+loaddll' wine "$probe") > "$res/miles-enum-terminal.log" 2> "$res/miles-loader.log"
status=$?
set -e
printf '%s\n' "$status" > "$res/miles-enum-exit-code.txt"
grep -iE 'mss32|mssa3d|a3dapi|a3d\.dll|err:' "$res/miles-loader.log" > "$res/miles-loader-interesting.log" || true
# Retain the short original loader trace as a diagnostic, never copy game binaries.
archive="$res.tar.gz"
tar -czf "$archive" -C "$HOME" "$(basename "$res")"
echo '===== Miles provider enumeration ====='
cat "$res/miles-enum-terminal.log"
echo "ENUM_EXIT=$status"
echo "ARCHIVE=$archive"
