# A3D v0.6.4 — Spatial latency research candidate (Windows 10/11 and Wine)

This is an EXPERIMENTAL, opt-in low-latency branch built from v0.6.3.
It is NOT validated by real in-game playback on native Windows or Wine.

## Three known-good reference profiles
Quake III 1.17: snapshot/off-lock, 3 x 512-frame headers (32 ms maximum queue).
Alice 2000: snapshot/off-lock, 8 x 512-frame headers (85.3 ms maximum queue);
             preserves the Water Logged / tower2 dialogue-sync fix.
Alice 2011 + VorpalFix 4.2.1: legacy renderer, 4 x 512-frame headers
             (42.7 ms maximum queue); launch with com_maxfps 144.
All three: 48-tap HRTF, maximum 5.0 master gain and existing peak limiter.

## Installation
1. BACK UP the A3D DLLs and launchers in the original game directory first.
2. Copy the contents of ONE appropriate profile folder alongside that game's EXE
   (QuakeIII-117 / Alice2000 / Alice2011-VorpalFix).
3. Keep original game .exe, SndDrivers, VorpalFix, winmm.dll, and config files unchanged.
4. Start RUN_A3D_ADAPTIVE_WINDOWS.cmd or RUN_A3D_ADAPTIVE_WINE.sh.
5. Re-run the SAME sound/camera test with RUN_A3D_FIXED_WINDOWS.cmd or
   RUN_A3D_FIXED_WINE.sh, then compare the A3D_v064_*.log files.
6. If unstable, copy A3D files back from matching KnownGood-PerGame folder.
   More conservative: run regular RUN_A3D_WINDOWS.cmd, which disables adaptive
   mode by default but still uses the experimental v0.6.4 DLL.

## What the code really changes
A3D_WAVEOUT_ADAPTIVE=1: starts at the proven queued-header ceiling, reduces
one 512-frame header after >=12 sec of uninterrupted stable output and >=20 sec
since any recorded queue-empty event; immediately restores up to two headers
if the queue runs completely empty. It never goes above the profile ceiling
or below the configured minimum. This is not a platform-level latency API.
A3D_LATENCY_TRACE=1: logs orientation setter counts (Euler vs six-vector),
last-received listener state age when a block is rendered, and a best-effort
waveOutGetPosition estimate of queued audio ahead of the playback cursor.
Unsupported or implausible position readings are rejected.
NO Euler rotation conversion is performed: the game/SDK angle convention has
not yet been confirmed. We do not want to corrupt the working spatial maths.

## Expected target ranges (headers * 512 / 48000)
Quake III: target 3 -> 2 headers, 32 -> 21.3 ms
Alice 2000: target 8 -> 6 headers, 85.3 -> 64 ms
Alice 2011: target 4 -> 3 headers, 42.7 -> 32 ms
These are MAXIMUM queued durations, not measured end-to-end listener latency.
Extra Wine / Windows host-mixer / DAC delays are not included.

## Interpreting the logs
- A3D.Latency.listener_euler_updates > 0 with orientation6_updates == 0:
  strong reason to investigate missing Euler-to-vector propagation.
- Recent listener age is simply time since last update, not a proof of
  delayed orientation when the camera is stationary.
- A3D.Latency.ahead_avg_frames / 48 gives nominal milliseconds of queued
  audio from the waveOut reported position (only if samples >0).
- `queue_empty_events` or adaptive recoveries are warnings; compare both
  profiles and check subjective sound continuity. The governor uses queue
  empty events as a conservative starvation signal, not an xrun API.

## Reproducibility / limitations
Source and tests in the companion Source ZIP. 32-bit PE compiled with Clang
and LLD; no game executable was modified on disk. Offline tests pass, but actual
Linux distribution support has not been established through listening tests.
