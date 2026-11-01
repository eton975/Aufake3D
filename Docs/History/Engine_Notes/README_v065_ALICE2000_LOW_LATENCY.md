# A3D v0.6.5 — Alice 2000 low-latency 256-frame candidate

**Experimental test, not yet verified by gameplay.** Built from v0.6.4 source
without altering Quake III or Alice 2011 profiles. Earlier v0.6.3 Alice 2000
was user-verified to fix `tower2` / Water Logged Cheshire Cat dialogue timing.

## What the new default does

- The Alice2000 `RUN_A3D_WINDOWS.cmd` / `RUN_A3D_WINE.sh` start at **4 x 256 frames**
  (21.33 ms nominal queued capacity), and after 20 s of stability reduce to
  **3 x 256 frames** (16 ms). They can recover up to **8 x 256 frames**
  (42.67 ms) if underrun or sustained near-empty playback is observed.
- An advisory `waveOutGetPosition` check can trigger early recovery after two
  consecutive low-headroom readings, at most once per second. Invalid readings
  are ignored and do NOT alter the audio cursor. The controller still uses
  completed WaveOut headers as its primary queue control.
- The main renderer, full 48-tap HRTF, geometry, reverb, snapshot caching,
  normal thread priority, default gain 5.0, and linked peak limiter remain.
- Actual end-to-end audio latency includes device/Windows/Wine delays; the
  quoted numbers are **queue capacities**, not measured latency.

## How to try it

1. Back up your working Alice 2000 game directory. Close the game.
2. Copy **only the contents of `Alice2000/`** beside the original `alice.exe`.
   Do not overwrite the actual game EXE, original Miles files, or game data.
3. On Windows: double-click `RUN_A3D_WINDOWS.cmd`. On Linux with 32-bit Wine:
   `bash RUN_A3D_WINE.sh`. The original Windows game DLLs are used in Wine;
   no native `.so` is installed.
4. Test the Cheshire Cat dialogue at `tower2`, plus moving around a sound source.
   On normal game exit, attach `a3d-alice2000-windows.log` (or Wine equivalent).
5. Compare `RUN_A3D_3HDR_FIXED_WINDOWS.cmd`, `RUN_A3D_4HDR_FIXED_WINDOWS.cmd`,
   and `RUN_A3D_8HDR_FIXED_WINDOWS.cmd` for fixed queues of 16, 21.3 and
   85.3 ms respectively. Matching `_WINE.sh` scripts are included.
6. If dialogue de-sync, stuttering or spatial glitches occur, use 8HDR fixed or
   restore `KnownGood-v063-Alice2000/` files (DLLs and launchers) to revert
   to the **previously user-verified** eight-header build.

## Important diagnostic log entries

- `A3D.Mixer.waveOut.frames_per_header`: should be **0x100 (256)**.
- `A3D.Latency.start_headers`: should be **4**.
- `A3D.Latency.adaptive_min_headers`: should be **3**.
- `A3D.Latency.final_target_headers`, `adaptive_reductions`, `adaptive_recoveries`.
- `A3D.Latency.early_headroom_recoveries`, `low_headroom_samples`.
- `A3D.Mixer.waveOut.queue_empty_events` and `A3D.Mixer.DSP.max_block_us`.
- `A3D.Latency.ahead_avg_frames` is estimated from waveOutGetPosition; a zero
  position count means position was unavailable or never plausibly sampled.

## Build and validation

`bash win32/build.sh` cross-compiles 32-bit PE DLLs using Clang/LLD. The
`tools/test_latency_governor_v065.py` compiles and runs the real C controller
logic against a simulated Windows clock. Run all Python tests with:
`python3 -m unittest discover -s tools -p 'test_*.py' -q`.
No in-game playback, dialogue timing or host latency was measured here.
