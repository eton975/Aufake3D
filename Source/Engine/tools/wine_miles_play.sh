#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
# v0.2.6 — Audible sample playback through ORIGINAL Miles A3D2 provider.
# Never launches Alice or modifies her game files. Runs 3 position modes in
# independent, bounded processes. The only game assets used are Miles DLLs.
set -euo pipefail
if (( $# != 1 )); then
  echo 'Usage: bash tools/wine_miles_play.sh "/absolute/path/to/Alice.exe"' >&2
  exit 2
fi
for exe_name in wine realpath tar timeout grep; do
  command -v "$exe_name" >/dev/null || { echo "Missing: $exe_name" >&2; exit 2; }
done
exe="$(realpath "$1")"
[[ -f "$exe" ]] || { echo "Missing game executable: $exe" >&2; exit 2; }
gamedir="$(dirname "$exe")"
snd=''
for candidate in "$gamedir/SndDrivers" "$gamedir/snddrivers" "$gamedir/SNDDRIVERS" "$gamedir"; do
  if [[ -f "$candidate/mss32.dll" && -f "$candidate/mssa3d2.m3d" ]]; then snd="$candidate"; break; fi
done
[[ -n "$snd" ]] || { echo 'Original Miles mss32.dll and mssa3d2.m3d not found' >&2; exit 3; }
here="$(cd "$(dirname "$0")/.." && pwd)"
probe="$here/deliverables/a3d-miles-wave.exe"
[[ -f "$probe" ]] || { echo "Missing: $probe" >&2; exit 3; }
export WINEPREFIX="${A3D_LAB_PREFIX:-$HOME/.local/share/alice-a3d2/wineprefix}"
lab="$WINEPREFIX/drive_c/A3D2Lab"
[[ -f "$WINEPREFIX/system.reg" && -d "$lab" ]] || {
  echo 'Isolated prefix missing. First run bash tools/wine_probe.sh' >&2; exit 3;
}
printf '%s\n' 'This test PLAYS three 400-ms synthetic tones from the original Miles provider.' \
 'Set headphone/system volume LOW before starting. No real Alice sound files are read.'

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
res="$HOME/alice-a3d2-miles-play-$stamp"
mkdir -p "$res"
{
 echo "WINE_VERSION=$(wine --version)"
 echo "WINEPREFIX=$WINEPREFIX"
 echo "MILES_DIR=$snd"
 echo 'TEST=original Miles A3D 2.0 provider / AIL_start_3D_sample / 3 positional 400-ms tones'
 echo 'AUDIO_OUTPUT=WinMM waveOut via A3D shim; conservative bounded prototype gain'
 echo 'ORIGINAL_GAME_NOT_LAUNCHED=yes'
 echo 'ORIGINAL_GAME_NOT_MODIFIED=yes'
 echo 'A3D2_HRTF_OR_WAVETRACING_NOT_IMPLEMENTED=yes'
} > "$res/context.txt"
set +e
bash "$here/tools/wine_com_probe.sh" > "$res/com-preflight-terminal.log" 2>&1
comstatus=$?
set -e
printf '%s\n' "$comstatus" > "$res/com-preflight-exit.txt"
if (( comstatus != 0 )); then
  echo "COM preflight failed ($comstatus); see report. Skipping audible tests."
else
  for loc in left center right; do
    log_win="C:\\A3D2Lab\\miles-play-$loc-$stamp.log"
    log_host="$lab/miles-play-$loc-$stamp.log"
    rm -f -- "$log_host"
    echo "TESTING_MILES_AUDIO_POSITION=$loc"
    set +e
    (
      cd "$snd"
      timeout --signal=TERM --kill-after=5s 30s env \
        A3D_MILES_PROVIDER=a3d2 \
        A3D_MILES_SAMPLE_TEST=1 \
        A3D_MILES_WAVE_MODE="play-$loc" \
        A3D_PROBE_LOG="$log_win" \
        WINEPATH="C:\\A3D2Lab${WINEPATH:+;$WINEPATH}" \
        WINEDLLOVERRIDES='a3dapi=n,b' \
        WINEDEBUG='-all,+loaddll,+ole' \
        wine "$probe"
    ) > "$res/$loc-terminal.log" 2> "$res/$loc-winedebug.log"
    status=$?
    set -e
    printf '%s\n' "$status" > "$res/$loc-exit.txt"
    if [[ -f "$log_host" ]]; then
      cp "$log_host" "$res/$loc-a3d-shim.log"
    else
      echo 'A3D wrapper was not observed in this process' > "$res/$loc-no-shim-calls.txt"
    fi
    grep -iE 'a3dapi|a3d\.dll|mssa3d|mss32|CoCreateInstance|err:|fail' \
      "$res/$loc-winedebug.log" | tail -n 1000 > "$res/$loc-wine-interesting.log" || true
    if (( $(wc -c < "$res/$loc-winedebug.log") > 4000000 )); then
      tail -n 300 "$res/$loc-winedebug.log" > "$res/$loc-winedebug-tail.log"
      rm -f -- "$res/$loc-winedebug.log"
    fi
    echo "MILES_PLAY_EXIT_$loc=$status"
    grep -E 'OPEN_RESULT=|SET_WAVE_FILE_RESULT=|AIL_START_3D_SAMPLE|PLAY_SKIPPED|PLAYBACK_WAIT' \
      "$res/$loc-terminal.log" || true
  done
fi
archive="$res.tar.gz"
tar -czf "$archive" -C "$HOME" "$(basename "$res")"
echo "COM_PREFLIGHT_EXIT=$comstatus"
echo "ARCHIVE=$archive"
echo 'Please report whether each tone was audible and appeared left, center, right.'
