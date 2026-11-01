# A3D v0.6.6 — Alice 2000 32ms Queue A/B Comparison (experimental)

## The three primary tests

Run each independently, in the same `tower2`/Water Logged area, for several minutes.
Please compare crackling and spatial responsiveness and check Cheshire Cat dialogue
remains correctly synchronised. Avoid other system changes between runs.

| Windows launcher | 48kHz stereo waveOut configuration | Nominal queue capacity |
|---|---|---|
| `RUN_A3D_6x256_WINDOWS.cmd` | Fixed 6 headers of 256 frames | 32.0 ms |
| `RUN_A3D_3x512_WINDOWS.cmd` | Fixed 3 headers of 512 frames | 32.0 ms |
| `RUN_A3D_8x256_WINDOWS.cmd` | Fixed 8 headers of 256 frames | 42.7 ms |

Also supplied: `RUN_A3D_4x256_WINDOWS.cmd` (21.3 ms comparison).
Equivalent `_WINE.sh` scripts are included. All four tests share **exactly
one v0.6.6 DLL**, the same sample/DSP code and 48-tap HRTF; the only differing
runtime rendering variables are subblocks and fixed queue limit.

The default `RUN_A3D_WINDOWS.cmd` is **6x256 fixed (32 ms)**, and LOGGING IS OFF.
Run `RUN_A3D_6x256_WINDOWS.cmd` instead to generate the bounded diagnostic log.

## Installation

1. Close Alice and back up your working game's A3D DLLs, manifest and launchers.
2. Copy the **contents of `Alice2000/`** into the folder with original `alice.exe`.
3. **Never replace the original `alice.exe`**, Miles binaries or game data.
4. Launch a comparison `.cmd` on Windows or `.sh` on Wine.
5. Upload the matching `A3D_v066_Alice2000_*_windows.log` after normal exit.
6. If this build is unstable, restore `KnownGood-v063-Alice2000/` DLLs/launchers.

## v0.6.6 changes

- **Fixed**, not adaptive, WaveOut queue for controlled tests.
- Preserves 256-frame mix blocks, adaptive PCM snapshots, snapshot off-lock DSP,
  geometry, reverb, 48-tap HRTF, master gain 5.0 and linked limiter.
- On normal runs the DLL does **not create a log file**. Diagnostic runs require
  **`A3D_LOG=1`**. Each process truncates its own log on first use and caps
  the A3D2 writer at 1 MiB total; the A3D1 bridge has an additional 32 KiB cap.
  This is opt-in at launch, not an in-game hotkey and not runtime switchable yet.
  The test logs overwrite, rather than append to, previous runs of the same profile.
- `A3D_LATENCY_TRACE=1` optionally collects bounded summary telemetry, including
  estimated worst-block thread CPU time via `GetThreadTimes` when supported.
  Windows thread CPU timings can be quantised; they cannot prove a stall was
  caused by OS preemption. No per-block disk writes are introduced.
- Distinguishes actual output queue empty events from brief near-empty cursor
  observations. A zero queue-empty count cannot rule out every audible click.

## Limits

The quoted 32ms and 42.7ms values are *queue capacities*, NOT actual
end-to-end or measured headphone latency. This release has NOT been run on a
real native Windows game/audio device or Wine. The aim is to isolate the
relationship between buffer size, callback rate and crackling, without
reintroducing the Cheshire Cat dialogue desynchronisation regression.

No changes to the Quake III 1.17 or Alice 2011 installed profiles are required.
Source build: `bash win32/build.sh` (Clang/LLD on a supported host).
Run Python suite AFTER the build: `python3 -m unittest discover -s tools -p 'test_*.py' -q`.
