#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
# A3D COM diagnostic v0.1.7: native 32-bit registry registration then COM activation.
# Only changes the dedicated Alice A3D research Wine prefix, never system registry.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
command -v wine >/dev/null || { echo 'Wine not installed' >&2; exit 2; }
export WINEPREFIX="${A3D_LAB_PREFIX:-$HOME/.local/share/alice-a3d2/wineprefix}"
lab="$WINEPREFIX/drive_c/A3D2Lab"
[[ -f "$WINEPREFIX/system.reg" && -d "$lab" ]] || { echo 'Run bash tools/wine_probe.sh once to create the isolated prefix.' >&2; exit 2; }
for f in a3dapi.dll a3d-comtest.exe a3d-register32.exe; do
 [[ -f "$here/deliverables/$f" ]] || { echo "Missing $f in deliverables" >&2; exit 2; }
 cp "$here/deliverables/$f" "$lab/$f"
done
: > "$lab/a3d2-probe.log"
key='HKCR\CLSID\{92FA2C24-253C-11D2-90FB-006008A1F441}\InprocServer32'
{
 echo '=== Before registration (Wine reg.exe, 32-bit view) ==='
 wine reg query "$key" /reg:32 || true
 echo '=== Registration with native 32-bit executable ==='
 (cd "$lab" && wine ./a3d-register32.exe)
} > "$lab/comtest-registry.log" 2>&1 || {
 echo 'Native registry repair reported an error.' >&2
 tail -n 35 "$lab/comtest-registry.log" >&2
}
{
 echo '=== After registration (Wine reg.exe, 32-bit view) ==='
 wine reg query "$key" /reg:32 || true
} >> "$lab/comtest-registry.log" 2>&1
set +e
(cd "$lab" && WINEDLLOVERRIDES='a3dapi=n,b' wine ./a3d-comtest.exe) > "$lab/comtest-terminal.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$lab/comtest-exit-code.txt"
echo "COMTEST_EXIT=$status"
cat "$lab/comtest-terminal.log"
if [[ "$status" -ne 0 ]]; then
 echo 'Collecting additional OLE and DLL traces (not a new module/hardware test).'
 (cd "$lab" && WINEDEBUG=+ole,+loaddll WINEDLLOVERRIDES='a3dapi=n,b' wine ./a3d-comtest.exe) > "$lab/comtest-winedebug.log" 2>&1 || true
 # Keep the diagnostic package bounded and useful.
 tail -n 350 "$lab/comtest-winedebug.log" > "$lab/comtest-winedebug-tail.log"
else
 printf '%s\n' 'COM activation passed.' > "$lab/comtest-winedebug-tail.log"
fi
archive="$HOME/alice-a3d2-com-results-v017.tar.gz"
tar -czf "$archive" -C "$lab" comtest-terminal.log comtest-exit-code.txt comtest-registry.log a3d2-probe.log comtest-winedebug-tail.log
printf 'Diagnostic archive: %s\n' "$archive"
if [[ "$status" -eq 0 ]] && grep -q 'Factory.CreateInstance' "$lab/a3d2-probe.log"; then
 echo 'PASS: Wine 32-bit CoCreateInstance reached our A3D DLL class factory.'
else
 echo 'FAIL: see the diagnostic archive; no need to rerun.' >&2
 exit 1
fi
