# Aureal A3D v0.6.2 — off-lock audio worker performance candidate

## Purpose
Addresses severe game-logic stalls experienced with v0.6.1 on native Windows 10
in Quake III Arena 1.17 and American McGee's Alice (2000). The previously smooth
Alice 2011 + VorpalFix defaults to its proven legacy audio path.

## Game-specific defaults

| Game | A3D_RENDER_SNAPSHOT | Worker priority | WaveOut headers | HRTF | Master gain |
|---|---|---|---|---|---|
| Quake III 1.17 | 1 | normal (0) | 3 | 48 taps | 5.0 |
| Alice 2000 | 1 | normal (0) | 3 | 48 taps | 5.0 |
| Alice 2011 | 0 (legacy) | existing above-normal (1) | 8 | 48 taps | 5.0 |

All original geometry/reverb presets remain. The stereo-linked limiter targets
~0.95 sample peak. Digital limiting is not a guarantee of hearing safety or
absence of source/intersample distortion; lower physical volume first.

## What changed in a3dapi.dll

The old WaveOut worker held the game-facing mixer lock while performing HRTF,
reflection traces, reverb and mixing. The opt-in snapshot worker now:

1. Captures game-facing controls, committed triangles and a bounded PCM window
   under the mutex; game PCM is never read after the mutex is released.
2. Advances PRIVATE worker-owned voice history/cursors and reverb/limiter state,
   with no game-facing lock held during rendering.
3. Reacquires the mutex for a short playback cursor/event commit. Rejected
   commits for stopped/restarted/released/repositioned sources are counted.

A 2050-frame source PCM window covers one 256-frame audio block at the mixer's
maximum permitted stepping rate of 8 input frames/output frame. The window
also accommodates interpolation and circular wrap. Source release and buffer
free are protected by the same lock during capture/commit.

## Installation (test copy only)

Back up each game's folder first. Copy contents of the ONE matching profile
folder beside quake3.exe / alice.exe, replacing only the files from the A3D
v0.6.1 test package. Do not replace game executables, game archives, original
Miles SndDrivers, or VorpalFix's winmm.dll or VorpalFix.ini.

Native Windows: double-click RUN_A3D_WINDOWS.cmd
Linux/Wine:      bash RUN_A3D_WINE.sh

Quake III and Alice 2000: for A/B comparison or quick recovery, double-click
RUN_A3D_LEGACY_WINDOWS.cmd or run bash RUN_A3D_LEGACY_WINE.sh. The DLL also
accepts A3D_RENDER_SNAPSHOT=0 from the environment. A3D_RENDER_SNAPSHOT=1
explicitly enables the experimental renderer for Alice 2011 if desired;
this is NOT the recommended default for that game yet.

## Where to look in the A3D log

A3D.Mixer.snapshot_enabled                  = 1/0
A3D.Mixer.snapshot.blocks                   = processed blocks
A3D.Mixer.snapshot.stale_commits            = game changes during DSP
A3D.Mixer.snapshot.scene_copies            = committed geometry snapshots
A3D.Mixer.snapshot.max_pcm_capture_bytes   = maximum per-voice capture
A3D.Mixer.snapshot.capture_max_us           = max mutex hold for capture
A3D.Mixer.snapshot.commit_max_us            = max mutex hold for commit
A3D.Mixer.DSP.max_block_us                  = max DSP wall time
A3D.Mixer.DSP.blocks_over_5333us            = missed 5.33ms budget
A3D.Mixer.waveOut.queue_empty_events        = output underrun indicator

Metrics are written at orderly engine shutdown. Crashes may omit final counters.

## Verification and limitations

PE32/x86 build with Clang/LLD; existing COM exports preserved. 192 offline
synthetic PCM tests compare output byte-for-byte with the original complete
PCM-buffer path for looped/non-looped sources, 8/16-bit, mono/stereo,
multiple pitch rates, and synthetic acoustic geometry; zero differences.
The existing source/regression suites and maximum-gain tests passed.

IMPORTANT: These updated DLLs HAVE NOT BEEN REAL-GAME PLAYBACK TESTED on native
Windows or Wine. Stutters may also be caused by CPU-heavy geometry work,
WaveOut scheduling, repeated A3D source updates, or game-specific assumptions.
The snapshot path is an EXPERIMENT to isolate contention; game performance,
audio integrity and long-term lifetime need live regression testing.

A3D DLLs are 32-bit Windows PE files for native Windows and for 32-bit-game
support in Wine on Debian 13, Ubuntu, Mint, Fedora. No Linux .so binary is
needed. The independent original game installations and compatible Wine setup
must be supplied by the user.

## Build from source

With Clang/LLD and Python 3 available, execute:

    python3 build_from_recipe.py
    bash build_and_test_v060.sh
    bash TEST_MAX_GAIN_OFFLINE.sh
    python3 -m unittest tools.test_snapshot_profiles -v

New snapshot implementation: win32/stream_winmm.inc
Source lifecycle epoch:      win32/source_probe.inc
Bounded PCM view support:    win32/stream_core.h
Freestanding PE memcpy:      win32/a3dapi.c
PCM regression:              win32/test_snapshot_pcm_native.c
Profile contract tests:     tools/test_snapshot_profiles.py

The legacy build_and_test_v060.sh filename is retained for compatibility.
Original A3D .DLL and release files are not Aureal drivers.
