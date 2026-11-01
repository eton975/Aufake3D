#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Installer / launcher support
# Supports reversible game-local deployment and diagnostics; the original executable
# and vendor Miles modules should remain untouched.
# Proves, or disproves, registration-free CoCreateInstance in a *fresh* prefix.
# Never calls reg.exe, never touches an installed Wine prefix or AU8830.
set -euo pipefail
for cmd in wine mktemp cp tar; do
 command -v "$cmd" >/dev/null || { echo "Missing dependency: $cmd" >&2; exit 2; }
done
here="$(cd "$(dirname "$0")" && pwd)"
root="$(mktemp -d "${TMPDIR:-/tmp}/a3d-regfree-XXXXXX")"
report="$(mktemp -d "${TMPDIR:-/tmp}/a3d-regfree-report-XXXXXX")"
cleanup(){ rm -rf -- "$root" "$report"; }
trap cleanup EXIT
mkdir -p "$root/program"
cp "$here/bin/a3dapi.dll" "$here/bin/a3d-comtest.exe" "$here/a3d-comtest.exe.manifest" "$root/program/"
# The prefix is brand-new. No COM registry utility is run. A successful
# CoCreateInstance here is strong evidence of local manifest activation.
export WINEPREFIX="$root/prefix"
export WINEDLLOVERRIDES='a3dapi=n,b'
export A3D_PROBE_LOG='a3d-regfree-probe.log'
set +e
(cd "$root/program" && wine ./a3d-comtest.exe) > "$report/com-terminal.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$report/exit-code.txt"
if [[ -f "$root/program/a3d-regfree-probe.log" ]]; then
 cp "$root/program/a3d-regfree-probe.log" "$report/a3d-regfree-probe.log"
fi
{
 echo "Wine: $(wine --version)"
 echo 'Mode: brand-new Wine prefix, no COM registration performed'
 echo "COMTEST_EXIT=$status"
} > "$report/summary.txt"
archive="$HOME/a3d-regfree-test-$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
tar -czf "$archive" -C "$report" .
echo "COMTEST_EXIT=$status"
echo "Diagnostic archive: $archive"
if (( status != 0 )); then
 echo 'App-local COM activation is NOT confirmed on this Wine build.'
else
 echo 'App-local COM activation succeeded in the fresh Wine prefix.'
fi
exit 0
