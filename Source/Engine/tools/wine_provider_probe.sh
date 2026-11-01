#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
# Alice A3D 2.0 exact-provider activation probe (v0.1.8).
# Runs only in the separate A3D Wine prefix. Never modifies EXE/DLL files or PCI drivers.
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo 'Usage: bash tools/wine_provider_probe.sh "/absolute/path/to/Alice.exe"' >&2
  exit 2
fi
for cmd in wine realpath tar find grep python3 sha256sum; do
  command -v "$cmd" >/dev/null || { echo "Missing $cmd" >&2; exit 2; }
done
exe="$(realpath "$1")"
[[ -f "$exe" ]] || { echo "No such executable: $exe" >&2; exit 2; }
gamedir="$(dirname "$exe")"
here="$(cd "$(dirname "$0")/.." && pwd)"
export WINEPREFIX="${A3D_LAB_PREFIX:-$HOME/.local/share/alice-a3d2/wineprefix}"
lab="$WINEPREFIX/drive_c/A3D2Lab"
[[ -f "$WINEPREFIX/system.reg" && -d "$lab" ]] || { echo 'First run bash tools/wine_probe.sh in this kit.' >&2; exit 2; }
# Prove the current DLL is registered and the SDK's IA3d4 interface is usable.
echo 'Checking 32-bit IA3d4 COM activation...'
bash "$here/tools/wine_com_probe.sh" || { echo 'COM preflight failed. Inspect ~/alice-a3d2-com-results-v017.tar.gz'; exit 3; }

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
res="$HOME/alice-a3d2-provider-probe-$stamp"
mkdir -p "$res/before" "$res/after" "$res/old-console-logs"
log_win="C:\\A3D2Lab\\provider-$stamp.log"
log_host="$lab/provider-$stamp.log"

# Snapshot only sound-related configuration, NOT private/game account configuration.
config_scan() {
  local destination="$1" file rel
  : > "$destination"
  while IFS= read -r -d '' file; do
    rel="${file#"$gamedir"/}"
    printf 'FILE: %s\n' "$rel" >> "$destination"
    grep -inE 's_milesdriver|s_initsound|s_speaker_type|s_reverb|^.*seta[[:space:]]+logfile' "$file" >> "$destination" || true
  done < <(find "$gamedir" -maxdepth 5 -type f -iname '*config*.cfg' -print0)
}
config_scan "$res/before/sound-cvars.txt"
sha256sum "$exe" > "$res/alice-executable-sha256.txt"
python3 - "$exe" > "$res/a3d-detection-patch-status.txt" <<'PYCHK'
import sys
raw=open(sys.argv[1],'rb').read()
original=bytes.fromhex('B000520053E87095070083C40885C0751A')
patched=bytes.fromhex('B000520053E87095070083C40885C0741A')
print('Known A3D enablement conditional, this Alice executable:')
print('Unpatched sequence at', hex(raw.find(original)) if original in raw else 'not found')
print('Patched sequence at', hex(raw.find(patched)) if patched in raw else 'not found')
print('No modification performed. Absence of both sequences is inconclusive for another game version.')
PYCHK

# Preserve pre-existing console logs, so +set logfile cannot destroy user logs.
# We only restore/clean qconsole.log. Game config files are never auto-restored.
while IFS= read -r -d '' file; do
  rel="${file#"$gamedir"/}"
  mkdir -p "$res/old-console-logs/$(dirname "$rel")"
  cp -p "$file" "$res/old-console-logs/$rel"
done < <(find "$gamedir" -maxdepth 5 -type f -iname qconsole.log -print0)
restore_console() {
  local file rel saved
  while IFS= read -r -d '' file; do
    rel="${file#"$gamedir"/}"
    saved="$res/old-console-logs/$rel"
    if [[ -f "$saved" ]]; then
      cp -p "$saved" "$file" || true
    else
      # Created by this test and not previously there.
      rm -f -- "$file" || true
    fi
  done < <(find "$gamedir" -maxdepth 5 -type f -iname qconsole.log -print0)
}
trap restore_console EXIT

printf '%s\n' '=== Test ===' \
  "Wine: $(wine --version)" \
  "Prefix: $WINEPREFIX" \
  'Provider forced by one-run command line: Aureal A3D 2.0 (TM)' \
  'Cvars: developer=1, logfile=1, s_milesdriver=Aureal A3D 2.0 (TM)' \
  'This does not assert that the game accepts the provider or that A3D audio is rendered.' \
  > "$res/environment.txt"

printf '%s\n' 'Launching Alice with the EXACT Miles A3D 2.0 provider name.' \
  'Enter a level, then exit normally. Do not launch another Alice session concurrently.'
set +e
(cd "$gamedir" && \
 A3D_PROBE_LOG="$log_win" \
 WINEPATH="C:\\A3D2Lab${WINEPATH:+;$WINEPATH}" \
 WINEDLLOVERRIDES='a3dapi=n,b' \
 WINEDEBUG='-all,+loaddll,+ole,+reg' \
 wine "$(basename "$exe")" \
   +set developer 1 +set logfile 1 \
   +set s_milesdriver 'Aureal A3D 2.0 (TM)') \
   > "$res/wine-verbose.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$res/alice-exit-code.txt"
config_scan "$res/after/sound-cvars.txt"
if [[ -f "$log_host" ]]; then cp "$log_host" "$res/a3d-shim-calls.log"; else
  echo 'No A3D shim calls captured.' > "$res/no-shim-calls.txt"
fi
# Save game console output before restoring the user's old log(s).
while IFS= read -r -d '' file; do
 rel="${file#"$gamedir"/}"
 mkdir -p "$res/after/console/$(dirname "$rel")"
 if [[ $(wc -c < "$file") -le 5000000 ]]; then cp "$file" "$res/after/console/$rel"; else
   grep -iE 'provider|a3d|sound|direct|miles|error|failed|cvar' "$file" | tail -n 1000 > "$res/after/console/$(basename "$rel").filtered.txt" || true
 fi
done < <(find "$gamedir" -maxdepth 5 -type f -iname qconsole.log -print0)
# Also extract the loader, registry and COM details into a manageable report.
grep -iE 'mss32|mssa3d|a3dapi|a3d\\.dll|aureal|CoCreateInstance|CoGetClassObject|Reg(Open|Query|Create)|err:|failed' "$res/wine-verbose.log" \
 | tail -n 6000 > "$res/wine-interesting-lines.log" || true
tail -n 450 "$res/wine-verbose.log" > "$res/wine-tail.log"
size=$(wc -c < "$res/wine-verbose.log")
if (( size > 4000000 )); then
  echo "Full WINEDEBUG log omitted ($size bytes); filtered and tail logs retained." > "$res/large-log-note.txt"
  rm -f "$res/wine-verbose.log"
fi
# Exclude original backed-up console content from report; restore it, then remove backup.
restore_console
trap - EXIT
rm -rf "$res/old-console-logs"
archive="$HOME/alice-a3d2-provider-probe-$stamp.tar.gz"
tar -czf "$archive" -C "$HOME" "$(basename "$res")"
echo "ALICE_EXIT=$status"
echo "Wrapper calls: $(if [[ -f "$res/a3d-shim-calls.log" ]]; then wc -l < "$res/a3d-shim-calls.log"; else echo 0; fi)"
echo "Diagnostic archive: $archive"
echo 'The game may fall back to ordinary Miles/DirectSound output; sound alone is not an A3D2 pass.'
