# Aureal A3D v0.6.0 — Quake III 1.17 Streaming Hotfix 2 (experimental)

## Background and evidence

The user confirmed the hotfix 1 `IA3dSource::Lock` fix allows Quake III 1.17
(verified authentic 1.17 PK3s) to enter A3D mode and continue playing a demo.
However, audio is very choppy, with frequent dropouts. The precise runtime
failure has NOT been identified by a Wine audio log or waveOut queue trace.
The source shows two credible risks, now made independently testable:

1. The old output worker submitted sixteen **256-frame** WaveOut buffers,
   each representing only 5.33ms of audio at 48kHz. Small API buffers can
   magnify scheduling jitter on Wine's audio backends.
2. `IA3dSource::GetWavePosition()` returned the cursor of audio already
   **rendered/queued** by the worker, not the cursor of sound **played** by
   waveOut. The old queue could be ~85ms ahead of the audible device position;
   changing this may fix Quake's circular-buffer producer/consumer phasing.

These are engineering hypotheses, not proven causes. A3D software HRTF still
requires actual listening tests, underflow verification and spatial evaluation.

## Patch contents

- `stream_winmm.inc`: Groups 256-frame DSP renders into one larger WaveOut
  submission, configurable via `A3D_WAVEOUT_SUBBLOCKS=1`, `2`, or `4`.
  Defaults to **2**, yielding 12 headers of 512 frames (128ms nominal maximum
  queue capacity). 1 -> 12 x 256 = 64ms; 4 -> 12 x 1024 = 256ms. These are
  nominal buffer capacities, not measured device output latency.
- `waveout_renderer.inc`: Dynamically resolves the optional WinMM
  `waveOutGetPosition` API, without changing required Windows imports.
- `source_probe.inc`: Opt-in `A3D_WAVEOUT_PLAY_CURSOR=1` reports played audio
  frames relative to the source's Play start. Works with returned sample,
  byte or millisecond formats and falls back if unsupported. Default 0
  retains hotfix 1 render-cursor behaviour for other games.
- Existing full-buffer Lock/Unlock correctness fix and both Alice launchers
  remain. `a3d.dll`, tests, manifests, installer mechanics remain unmodified.

## Safe installation

**Keep a working backup of Hotfix 1.** Use the matching installer from the
original hotfix 1 directory to uninstall; the receipts are SHA-256 protected.

```sh
G="$HOME/Games/Quake3-117-a3d/quake3.exe"
python3 /path/to/Hotfix1/a3d_port.py uninstall "$G"
cd /path/to/A3D_Portable_v0.6.0_Q3_Hotfix2
python3 a3d_port.py install "$G" --profile quake3 --mode both
python3 a3d_port.py verify "$G"
```

Run Wine from the Quake III test directory (do not run the old Wine launcher
with a different default prefix). Use the same Wine prefix where vanilla 1.17
and hotfix 1 already work.

## Three reproducible A/B tests

Use one setting per launch; restart Quake III between runs. In the Quake III
console, run `s_enable_a3d` and the same demo for each test.

**Test A: larger headers, original cursor**

```sh
cd "$HOME/Games/Quake3-117-a3d"
A3D_MASTER_GAIN=0.5 A3D_WAVEOUT_SUBBLOCKS=2 \
A3D_WAVEOUT_PLAY_CURSOR=0 A3D_PROBE_LOG="$PWD/q3-a3d-A.log" \
wine ./quake3.exe
```

**Test B: larger headers, playback-device cursor**

```sh
A3D_MASTER_GAIN=0.5 A3D_WAVEOUT_SUBBLOCKS=2 \
A3D_WAVEOUT_PLAY_CURSOR=1 A3D_PROBE_LOG="$PWD/q3-a3d-B.log" \
wine ./quake3.exe
```

**Test C: even larger headers, playback-device cursor**

```sh
A3D_MASTER_GAIN=0.5 A3D_WAVEOUT_SUBBLOCKS=4 \
A3D_WAVEOUT_PLAY_CURSOR=1 A3D_PROBE_LOG="$PWD/q3-a3d-C.log" \
wine ./quake3.exe
```

Do not set `A3D_TRACE_DETAIL=1` while comparing real-time performance: it
performs synchronous per-call file operations and may itself cause stutter.
If all three fail, repeat B with `A3D_HRTF_TAPS=24` as a CPU-isolation test.

Record for A/B/C: whether the menu and demo have clear continuous sound, if
stutter correlates with busy scenes, whether the audio lags or glitches, and
attach the corresponding log. The startup log should show the header size;
test B/C should log `A3D.Mixer WaveOut playback-cursor mode active` or fall
back if the host API does not support device-position reporting.

## Validation and limitations

- Compiles with Clang + lld-link as PE32/x86 `a3dapi.dll`.
- Offline source/installer/ABI tests pass, including the hotfix 1 lock ABI.
- Runtime Wine audio and real Quake III gameplay remain **UNTESTED HERE**.
- Native benchmark of the HRTF core suggests low CPU use on *this* build
  host; this does NOT measure Wine/WaveOut latency on the user's computer.
- Tests A/B/C are experimental. If any causes regression, uninstall this
  hotfix using its own receipt and reinstall Hotfix 1.
- This is not a claim of fully accurate or complete Aureal A3D 2.0 playback.
