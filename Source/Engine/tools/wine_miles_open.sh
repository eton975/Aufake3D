#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
# v0.2.1: isolate Miles 3D provider opening in TWO independent 32-bit Wine processes.
# Read-only with respect to the original game directory; never starts Alice.exe.
set -euo pipefail
if (( $# != 1 )); then
  echo 'Usage: bash tools/wine_miles_open.sh "/absolute/path/to/Alice.exe"' >&2; exit 2
fi
for command_name in wine realpath tar timeout grep; do
  command -v "$command_name" >/dev/null || { echo "Missing: $command_name" >&2; exit 2; }
done
exe="$(realpath "$1")"
[[ -f "$exe" ]] || { echo "Missing executable: $exe" >&2; exit 2; }
gamedir="$(dirname "$exe")"
snd=''
for candidate in "$gamedir/SndDrivers" "$gamedir/snddrivers" "$gamedir/SNDDRIVERS" "$gamedir"; do
  if [[ -f "$candidate/mss32.dll" && -f "$candidate/mssa3d2.m3d" ]]; then snd="$candidate"; break; fi
done
[[ -n "$snd" ]] || { echo 'Cannot locate original Miles mss32.dll and mssa3d2.m3d' >&2; exit 3; }
here="$(cd "$(dirname "$0")/.." && pwd)"
probe="$here/deliverables/a3d-miles-open.exe"
[[ -f "$probe" ]] || { echo "Missing: $probe" >&2; exit 3; }
export WINEPREFIX="${A3D_LAB_PREFIX:-$HOME/.local/share/alice-a3d2/wineprefix}"
lab="$WINEPREFIX/drive_c/A3D2Lab"
[[ -f "$WINEPREFIX/system.reg" && -d "$lab" ]] || { echo 'Isolated Wine prefix missing. First run bash tools/wine_probe.sh' >&2; exit 3; }
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
res="$HOME/alice-a3d2-miles-open-$stamp"
mkdir -p "$res"
{
  echo "WINE_VERSION=$(wine --version)"
  echo "WINEPREFIX=$WINEPREFIX"
  echo "MILES_DIR=$snd"
  echo 'TEST=read-only direct Miles provider open, one process per provider'
  echo 'EXPECTED=Fast2D baseline may succeed; A3D2 is not expected to render sound'
  echo 'NO_ALICE_EXE_LAUNCH=yes'
  echo 'NO_GAME_BINARIES_MODIFIED=yes'
} > "$res/context.txt"

# Preflight the same wrapper and COM registration the game would see.
# Do not discard provider-open evidence if COM preflight itself fails.
set +e
bash "$here/tools/wine_com_probe.sh" > "$res/com-preflight-terminal.log" 2>&1
comstatus=$?
set -e
printf '%s\n' "$comstatus" > "$res/com-preflight-exit.txt"

run_one() {
  local code="$1" status log_win log_host
  log_win="C:\\A3D2Lab\\miles-open-$code-$stamp.log"
  log_host="$lab/miles-open-$code-$stamp.log"
  rm -f -- "$log_host"
  set +e
  ( cd "$snd" && \
    timeout --signal=TERM --kill-after=5s 35s env \
      A3D_MILES_PROVIDER="$code" \
      A3D_PROBE_LOG="$log_win" \
      WINEPATH="C:\\A3D2Lab${WINEPATH:+;$WINEPATH}" \
      WINEDLLOVERRIDES='a3dapi=n,b' \
      WINEDEBUG='-all,+loaddll,+ole' \
      wine "$probe" \
  ) > "$res/$code-terminal.log" 2> "$res/$code-winedebug.log"
  status=$?
  set -e
  printf '%s\n' "$status" > "$res/$code-exit.txt"
  if [[ -f "$log_host" ]]; then cp "$log_host" "$res/$code-a3d-shim.log"; else
    echo 'No A3D DLL calls logged in this provider-open process.' > "$res/$code-no-shim-calls.txt"
  fi
  grep -iE 'a3dapi|a3d\.dll|mssa3d|mss32|CoCreateInstance|CoGetClassObject|err:|fail' \
    "$res/$code-winedebug.log" | tail -n 2000 > "$res/$code-wine-interesting.log" || true
  if (( $(wc -c < "$res/$code-winedebug.log") > 4000000 )); then
    tail -n 300 "$res/$code-winedebug.log" > "$res/$code-winedebug-tail.log"
    rm -f -- "$res/$code-winedebug.log"
  fi
  echo "==== $code : process exit $status ===="
  cat "$res/$code-terminal.log"
  echo "A3D_WRAPPER_CALLED=$([[ -f "$res/$code-a3d-shim.log" ]] && echo yes || echo no)"
}

# First check a known fallback as a control, then A3D2 in a fresh process.
run_one fast2d
run_one a3d2
archive="$res.tar.gz"
tar -czf "$archive" -C "$HOME" "$(basename "$res")"
echo "COM_PREFLIGHT_EXIT=$comstatus"
echo "ARCHIVE=$archive"
echo 'If A3D2 fails, this is expected diagnostic evidence, not a reason to install original drivers.'
