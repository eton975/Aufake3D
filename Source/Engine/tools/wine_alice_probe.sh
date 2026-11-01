#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
# Alice.exe/Miles A3D2 interoperability reconnaissance, release 0.1.6.
# Uses a disposable, per-project Wine prefix and only loads a diagnostic shim.
# No real-time renderer is implemented. Does not access physical PCI hardware.
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo 'Usage: bash tools/wine_alice_probe.sh "/absolute/path/to/Alice.exe"' >&2
  exit 2
fi
for cmd in wine realpath tar grep; do
  command -v "$cmd" >/dev/null || { echo "Required program missing: $cmd" >&2; exit 2; }
done
exe="$(realpath "$1")"
[[ -f "$exe" ]] || { echo "Alice.exe not found: $exe" >&2; exit 2; }
if [[ "$(basename "$exe" | tr '[:upper:]' '[:lower:]')" != 'alice.exe' ]]; then
 echo "WARNING: Expected Alice.exe; supplied $(basename "$exe"). Proceeding as a diagnostic." >&2
fi
here="$(cd "$(dirname "$0")/.." && pwd)"
gamedir="$(dirname "$exe")"
export WINEPREFIX="${A3D_LAB_PREFIX:-$HOME/.local/share/alice-a3d2/wineprefix}"
lab="$WINEPREFIX/drive_c/A3D2Lab"
[[ -d "$lab" && -f "$WINEPREFIX/system.reg" ]] || {
 echo 'Research Wine prefix missing; initializing with wine_probe.sh.'
 bash "$here/tools/wine_probe.sh"
}
# The COM test installs the newest candidate and checks the same activation path
# the Miles provider may use; abort if it fails. This does NOT run Alice.
echo 'Checking 32-bit A3D COM activation before starting Alice...'
if ! bash "$here/tools/wine_com_probe.sh"; then
 echo 'COM preflight failed; not launching Alice. Upload the COM results archive.' >&2
 exit 3
fi
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
results="$HOME/alice-a3d2-alice-probe-$stamp"
mkdir -p "$results"
log_win="C:\\A3D2Lab\\alice-a3d2-probe-$stamp.log"
log_host="$lab/alice-a3d2-probe-$stamp.log"
{
 echo "Wine: $(wine --version)"
 echo 'Test program: Alice.exe (original 2000 PC game; user install)'
 echo "Actual executable: $exe"
 echo "Wine prefix: $WINEPREFIX"
 echo "Shim: $lab/a3dapi.dll"
 echo 'Supported shim functionality: diagnostic COM and partial geometry only; no game sound output'
 echo 'Hardware AU8830 used: no'
} > "$results/environment.txt"
{
 echo '=== Original game-directory dependencies (not copied) ==='
 for f in mss32.dll mssa3d2.m3d a3dapi.dll a3d.dll; do
  if [[ -f "$gamedir/$f" ]]; then echo "FOUND: $f"; else echo "NOT IN EXE DIRECTORY: $f"; fi
 done
 echo '=== A3D providers anywhere below game install (first 30, shallow) ==='
 find "$gamedir" -maxdepth 4 -type f \( -iname 'mssa3d2.m3d' -o -iname 'a3dapi.dll' -o -iname 'a3d.dll' \) -print | head -n 30 || true
} > "$results/provider-inventory.txt"
if [[ -e "$gamedir/a3dapi.dll" || -e "$gamedir/A3DAPI.DLL" ]]; then
 echo 'WARNING: Game directory has an a3dapi.dll; DLL search order may select it instead of the test shim.' | tee "$results/dll-warning.txt"
fi
printf 'Running Alice for Miles/A3D2 interface tracing.\nClose the game normally when finished.\n'
# Do not copy/rename game or replace Miles binaries; restore current cwd on exit.
set +e
(cd "$gamedir" && \
 A3D_PROBE_LOG="$log_win" \
 WINEPATH="C:\\A3D2Lab${WINEPATH:+;$WINEPATH}" \
 WINEDLLOVERRIDES='a3dapi=n,b' \
 WINEDEBUG='-all,+loaddll,+ole' \
 wine "$(basename "$exe")") > "$results/wine-alice-terminal-full.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/alice-exit-code.txt"
if [[ -f "$log_host" ]]; then
 cp "$log_host" "$results/a3d2-probe.log"
else
 echo 'No A3D shim log was created. This does NOT prove Miles did not attempt A3D; inspect loader log.' > "$results/no-shim-log.txt"
fi
# Retain a bounded, focused loader trace and the last 250 lines. The full output
# may be large; include the full log only when small enough for convenient upload.
grep -Ei 'a3d|mssa3d|mss32|CoCreateInstance|CLSID|aureal|err:|failed' "$results/wine-alice-terminal-full.log" \
 | tail -n 500 > "$results/wine-interesting-lines.log" || true
tail -n 250 "$results/wine-alice-terminal-full.log" > "$results/wine-alice-terminal-tail.log"
bytes=$(wc -c < "$results/wine-alice-terminal-full.log")
if (( bytes > 2000000 )); then
 echo "Full loader log exceeded 2 MB ($bytes bytes); only filtered and tail logs included in archive." > "$results/log-truncation-note.txt"
 rm "$results/wine-alice-terminal-full.log"
fi
archive="$HOME/alice-a3d2-alice-probe-$stamp.tar.gz"
tar -czf "$archive" -C "$HOME" "$(basename "$results")"
echo "ALICE_EXIT=$status"
echo "Wrapper calls: $(if [[ -f "$results/a3d2-probe.log" ]]; then wc -l < "$results/a3d2-probe.log"; else echo 0; fi)"
echo "Upload report: $archive"
echo 'Note: A COM test pass is not game compatibility or audio output.'
