#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
# Win32 Aureal COM self-test under an isolated Wine prefix.
# Does not access any PCI device, driver, or ALSA card.
set -euo pipefail
here="$(cd -- "$(dirname "$0")/.." && pwd)"
command -v wine >/dev/null || { echo 'Wine is missing. On Debian 13 install Wine and 32-bit support; see QUICKSTART.md' >&2; exit 2; }
command -v wineboot >/dev/null || { echo 'wineboot is missing' >&2; exit 2; }
export WINEPREFIX="${A3D_LAB_PREFIX:-$HOME/.local/share/alice-a3d2/wineprefix}"
if [[ ! -f "$WINEPREFIX/system.reg" ]]; then
  mkdir -p "$WINEPREFIX"
  # Do NOT force WINEARCH=win32: contemporary Wine WoW64 may reject it.
  unset WINEARCH
  echo "Creating isolated Wine prefix: $WINEPREFIX"
  wineboot -u
fi
lab="$WINEPREFIX/drive_c/A3D2Lab"
mkdir -p "$lab"
# Binary files in the DISTRIBUTED ZIP live under deliverables/, not win32/build/.
cp "$here/deliverables/a3dapi.dll" "$here/deliverables/a3d-selftest.exe" "$lab/"
echo 'Preparing per-prefix A3D COM registration (diagnostic shim only).'
key='HKCU\Software\Classes\CLSID\{92FA2C24-253C-11d2-90FB-006008A1F441}\InprocServer32'
wine reg add "$key" /ve /t REG_SZ /d 'C:\A3D2Lab\a3dapi.dll' /f /reg:32
wine reg add "$key" /v ThreadingModel /t REG_SZ /d Apartment /f /reg:32
printf '%s\n' "Wine: $(wine --version)" "Prefix: $WINEPREFIX" "DLL: $lab/a3dapi.dll"
set +e
(cd "$lab" && WINEDLLOVERRIDES='a3dapi=n,b' wine ./a3d-selftest.exe) 2>&1 | tee "$lab/selftest-terminal.log"
status=${PIPESTATUS[0]}
set -e
printf '%s\n' "$status" > "$lab/selftest-exit-code.txt"
echo "SELFTEST_EXIT=$status"
echo "Saved diagnostic files in: $lab"
[[ "$status" -eq 0 ]] || { echo 'Self-test FAILED. Save selftest-terminal.log, selftest-exit-code.txt, and a3d2-probe.log if present.' >&2; exit "$status"; }
[[ -f "$lab/a3d2-probe.log" ]] || { echo 'Self-test exited 0 but produced no DLL log' >&2; exit 3; }
echo "PASS: self-test returned 0 and created $lab/a3d2-probe.log"
