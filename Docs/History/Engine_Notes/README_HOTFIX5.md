# A3D v0.6.0 — Quake III Voice/Logging Hotfix 5 (128 slots)

**Status:** experimental Win32 DLL / offline validated. Real-game audio under Wine has **not** yet been proven stutter-free.

## Why this patch exists

A diagnostic run from authentic Quake III Arena 1.17 on Debian/Wine showed:
- 68 distinct A3D source objects created during the run.
- Hundreds of repeated `A3D.Mixer rejected source: maximum active voices` messages, owing to the prior 24-slot mixer pool.
- Approximately **87,164** `IA3dSource.Stop` calls; prior code performed synchronous open/append/close logging for each call, even with `A3D_TRACE_DETAIL` unset.
- WaveOut queue-empty events of zero, but some slow DSP blocks; the source-rejection and synchronous-log issues are better grounded than another buffer-size adjustment.

## Changes

1. **128-voice capacity by default**, replacing the old 24-slot limit. This is capacity, not a promise that mixing 128 simultaneous HRTF voices is always real-time on every CPU.
2. `A3D_VOICE_LIMIT` environment variable can lower the effective pool for controlled A/B comparisons (e.g. 24, 80, or 128). Values are read when the mixer first initialises. Restart the game between tests.
3. `Stop`, `Play`, `NewList`, geometry binding, and source-rejection tracing are less chatty in the frequent paths. Detailed tracing remains opt-in via `A3D_TRACE_DETAIL=1`; keep this unset during normal gaming.
4. New shutdown counters `A3D.Mixer.voice_peak`, `.voice_additions`, `.voice_rejections`, `.source_stop_calls` supplement the existing WaveOut/DSP counters.
5. Preserves Hotfix 1 Lock/Unlock fixes, Hotfixes 2–4 output scheduling experiments, and Hotfix 3a onset-aware 24-tap HRTF mode.

## Upgrade using version-independent a3dctl on Linux

In a terminal (assuming you've already registered the `q3` game profile):

```bash
 a3dctl install q3 "$HOME/Downloads/A3D_v0.6.0_Q3_Voice_Hotfix5_128_Portable.zip"
 a3dctl status q3
```

If the ZIP is saved elsewhere, use its actual absolute path. The manager backs up the preceding installation. Do **not** manually delete the old receipt or replace the game EXE. Do not run the old installer first.

Run Quake III from its own folder:

```bash
cd "$HOME/Games/QuakeIII-117-A3D2"
LOG="$(winepath -w "$PWD/a3d-hf5-debug.log")"
env -u A3D_TRACE_DETAIL \
 A3D_PROBE_LOG="$LOG" \
 A3D_VOICE_LIMIT=128 \
 A3D_MASTER_GAIN=0.5 \
 A3D_WAVEOUT_QUEUE_HEADERS=3 \
 A3D_WAVEOUT_SUBBLOCKS=2 \
 A3D_WAVEOUT_PLAY_CURSOR=0 \
 A3D_Q3_DMA_CLOCK=0 \
 wine ./quake3.exe
```

Enable A3D with `/s_enable_a3d`, replay the same demo, and **exit the game normally** to flush shutdown diagnostic counters. Inspect the end of `a3d-hf5-debug.log`:

```bash
grep -E 'voice_(limit|peak|rejections)|source_stop_calls|DSP.max_block_us|DSP.blocks_over|queue_empty_events' a3d-hf5-debug.log
```

If the audio still stutters, test the *same* settings with `A3D_VOICE_LIMIT=80` to distinguish extra HRTF load from missing voices. 128 slots alone do not mean 128 active voices.

To roll back: `a3dctl rollback q3`.

## Validation and limitations

- PE32/i386 DLL and diagnostic Win32 executables cross-compiled successfully.
- 98 offline Python tests passed (portable, drop-in, remaster, core source/ABI tests).
- Native regression tested 128 successful registrations, overflow rejection, duplicate registration idempotence, freed-slot reuse, and 24-voice override.
- Native HRTF impulse tests pass, including Hotfix 3a 24-tap case.
- Real Quake III audio playback and simultaneous 128-voice DSP throughput **not tested** here.

The implementation remains an experimental Aureal A3D compatibility layer, not hardware-identical AU8830 emulation. Alice 2000 and 2011 retain their dedicated launchers; runtime regressions have not yet been tested.
