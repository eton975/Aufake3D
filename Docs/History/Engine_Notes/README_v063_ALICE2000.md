# A3D v0.6.3 — Alice 2000 playback pacing candidate

**Report:** Quake III Arena 1.17 runs smoothly with v0.6.2; Alice 2011
runs smoothly on its legacy mode; Alice 2000 still exhibits audio/script
misalignment in `tower2` / Water Logged, where the Cheshire Cat vanishes
before speech has finished. This is a candidate, NOT a proven in-game fix.

## Changes

1. The PCM snapshot captures the number of source frames actually needed to
   produce 256 output frames, based on source rate, pitch, Doppler, current
   listener position and interpolation safety margin. Previous snapshots
   always captured 2050 source frames per active voice. This reduces mutex
   hold time for common 11025/22050/44100-Hz game samples.
2. The 48-tap HRTF, reflections and reverb retain their mathematical operations,
   but the hot history/delay ring index uses equivalent wrapping instead of
   remainder arithmetic. Does NOT reduce spatial quality, voices or volume.
3. Alice 2000 defaults to eight 512-frame WaveOut headers (85.3ms total)
   instead of three (32ms), matching the stable Alice 2011's buffering budget.
   This trades ~53ms more possible queued latency for resilience to short
   render spikes. It does NOT guarantee that script/audio timing will align.
   One-click RUN_A3D_3HEADERS_* fallback tests the previous queue setting.
4. Additional cumulative snapshot diagnostics on normal process shutdown:
   max captured frames, average captured PCM bytes and voices captured.

## Invariants

- The 5.0 master gain and stereo-linked peak limiter remain.
- A3D_HRTF_TAPS=48 for all games.
- Geometry tracing, reverb, Doppler, and voice limits remain enabled.
- Quake III keeps v0.6.2 profile defaults (3 headers, snapshot mode).
- Alice 2011 keeps legacy mode and 8 headers.
- Original game, Miles and VorpalFix files are not replaced by the ZIP.
- Windows 10/11 and Wine use identical rebuilt 32-bit PE DLLs.

## Testing

Install to a BACKED-UP TEST COPY, placing only files from the matching game
profile beside `alice.exe` or `quake3.exe`. On Windows launch
`RUN_A3D_WINDOWS.cmd`; on Linux use `bash RUN_A3D_WINE.sh`. For Alice 2000,
compare `RUN_A3D_3HEADERS_WINDOWS.cmd` / `RUN_A3D_3HEADERS_WINE.sh`.

Reproduce `tower2` and check the Cheshire Cat dialogue/cutscene timing.
On orderly exit, submit the `a3d-alice2000-*.log` file. Important counters:

- A3D.Mixer.DSP.blocks_over_5333us (missed 5.33ms block deadline)
- A3D.Mixer.waveOut.queue_empty_events (actual output queue drains)
- A3D.Mixer.snapshot.capture_max_us and commit_max_us (mixer lock cost)
- A3D.Mixer.snapshot.avg_pcm_capture_bytes (new bounded capture efficiency)

If the dialogue still lags but those counters are healthy, that suggests a
clock/timing contract mismatch rather than pure DSP overload; next focus is
Miles source cursor/status semantics and scene-specific spoken audio timing.

## What has been validated

Clang/LLD PE32 cross-compile and offline tests, including 864 rate/pitch/
Doppler PCM parity cases and 80-block 10-voice byte-identical DSP output.
We cannot test the actual games or the FX-6300 performance in this container.
