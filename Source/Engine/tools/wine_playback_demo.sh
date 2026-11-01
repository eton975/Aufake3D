#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
# User-invoked 3-tone A3D COM playback smoke test. No game files needed.
# Uses the isolated A3D research prefix only, and no PCI/kernel driver calls.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
for cmd in wine tar timeout; do command -v "$cmd" >/dev/null || { echo "Missing: $cmd" >&2; exit 2; }; done
export WINEPREFIX="${A3D_LAB_PREFIX:-$HOME/.local/share/alice-a3d2/wineprefix}"
lab="$WINEPREFIX/drive_c/A3D2Lab"
[[ -d "$lab" && -f "$WINEPREFIX/system.reg" ]] || { echo 'First create the isolated prefix with tools/wine_probe.sh' >&2; exit 2; }
[[ -f "$here/deliverables/a3d-playback-demo.exe" ]] || { echo 'Missing playback demo EXE' >&2; exit 2; }
# Registers the current DLL in the isolated Wine prefix, with preflight.
bash "$here/tools/wine_com_probe.sh" >/dev/null
cp "$here/deliverables/a3d-playback-demo.exe" "$lab/a3d-playback-demo.exe"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
res="$HOME/alice-a3d2-playback-demo-$stamp"
mkdir -p "$res"
log_win="C:\\A3D2Lab\\playback-$stamp.log"
log_host="$lab/playback-$stamp.log"
set +e
( cd "$lab" && timeout --signal=TERM --kill-after=5s 25s env \
  A3D_PROBE_LOG="$log_win" \
  WINEDLLOVERRIDES='a3dapi=n,b' \
  WINEDEBUG='-all,+loaddll' \
  wine ./a3d-playback-demo.exe \
) >"$res/terminal.log" 2>"$res/winedebug.log"
status=$?
set -e
printf '%s\n' "$status" >"$res/exit-code.txt"
[[ ! -f "$log_host" ]] || cp "$log_host" "$res/a3d-shim.log"
{
 echo "WINE_VERSION=$(wine --version)"
 echo "WINEPREFIX=$WINEPREFIX"
 echo "DEMO=3 positional tones / 0.3s each, 16-bit 22050Hz mono input, waveOut stereo output"
 echo "ORIGINAL_GAME_NOT_LAUNCHED=yes"
 echo "ORIGINAL_GAME_NOT_MODIFIED=yes"
 echo "A3D2_HRTF_OR_GEOMETRY_NOT_IMPLEMENTED=yes"
} > "$res/context.txt"
archive="$res.tar.gz"
tar -czf "$archive" -C "$HOME" "$(basename "$res")"
echo "PLAYBACK_DEMO_EXIT=$status"
echo "ARCHIVE=$archive"
cat "$res/terminal.log"
if (( status != 0 )); then echo 'Playback path failed; capture the archive for diagnosis.'; fi
