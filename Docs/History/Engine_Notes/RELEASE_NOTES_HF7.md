# Aureal A3D Emulator — Quake III Active-Play Hotfix 7 (EXPERIMENTAL)

## Why
A real Wine Quake III Arena 1.17 run with Hotfix 6 logged 2,998 `Play`
requests on sources **already active**, but only 446 genuine stops, 33 peak
simultaneous voices and zero voice rejections or full WaveOut queue-empty
observations. Hotfix 6's `sr_audio_play` rebuilt the entire voice on **every**
Play request, resetting playback cursor and HRTF history, and copying all PCM.
This can abruptly truncate footsteps when new sounds arrive; it is a concrete
mechanism, but playback under the user's Wine system is not yet verified.

The A3D API describes Play as a request to the resource manager (with delayed
application in later A3D 3.0 versions), not a guarantee of an unconditional
reset when a voice is already playing. This release makes repeat requests
idempotent under defined conditions, while retaining intentional replays.

## Changes
- Preserves an active voice's cursor, HRTF filter history, queued PCM and
  playback clock on redundant Play. No full PCM copy on preserved requests.
- Adds a `pcm_update_serial` advanced on successful Unlock, permitting
  updated SINGLE buffers to restart when new samples have been loaded.
- Explicit Rewind, SetWavePosition and SetWaveTime are not treated as
  redundant; mode switches and Stop+Play still initiate genuine fresh plays.
- Three selectable policies (process environment, read once):
  `A3D_PLAY_ACTIVE_POLICY=2` (default): active LOOPED requests are idempotent,
  as are active SINGLE requests if PCM unchanged. Changing one-shot PCM or
  explicitly seeking allows a new play.
  `A3D_PLAY_ACTIVE_POLICY=1`: preserve LOOPED active voices only; SINGLE
  requests retrigger even if PCM unchanged. Try this if repeated weapon fire
  stops retriggering correctly.
  `A3D_PLAY_ACTIVE_POLICY=0`: restore Hotfix 6's restart-on-every-Play
  semantics (comparison/rollback without uninstalling).
- Shutdown counters: `source_play_active_requests`,
  `source_play_preserved_looped`, `source_play_preserved_single`,
  `source_play_restarts_changed_pcm`, `source_play_restarts_mode_change`,
  `source_play_restarts_other`, plus the previous restart/stop/DSP counters.
- Retains 128 voices, the idle-Stop fast path, WaveOut scheduling, measured
  48/96-tap and corrected onset-aligned 24-tap HRTF, and Alice bridges.

## Installation (Linux)
Extract or download the supplied portable ZIP, then:

    a3dctl install q3 "$HOME/Downloads/A3D_v0.6.0_Q3_ActivePlay_Hotfix7_Portable.zip"
    a3dctl status q3

No prior uninstall required. To revert: `a3dctl rollback q3`.

## Quake III test

    cd "$HOME/Games/QuakeIII-117-A3D2"
    LOG="$(winepath -w "$PWD/a3d-hf7-debug.log")"
    env -u A3D_TRACE_DETAIL A3D_PROBE_LOG="$LOG" \
      A3D_PLAY_ACTIVE_POLICY=2 A3D_VOICE_LIMIT=128 \
      A3D_MASTER_GAIN=0.1 A3D_HRTF_TAPS=48 A3D_REVERB_WET=0 \
      A3D_WAVEOUT_QUEUE_HEADERS=3 A3D_WAVEOUT_SUBBLOCKS=2 \
      A3D_Q3_DMA_CLOCK=0 wine ./quake3.exe

In the console keep `s_mixahead 0.35` and `s_mixPreStep 0.05`, then replay
same scene: sustained footsteps while firing weapons. Exit normally.

    grep -E 'A3D.HF7|active_play_policy|source_play_|source_stop_|DSP.blocks_over|queue_empty_events|voice_rejections' a3d-hf7-debug.log

Compare quality **with your ears**: counters cannot certify sound continuity.
If gunfire itself stops retriggering with policy 2, re-run with
`A3D_PLAY_ACTIVE_POLICY=1`. If policy 1 is also problematic, compare policy 0.
Those are run-time switches, no reinstall needed.

## Validation
Cross-compiled PE32/i386 DLL using Clang + lld-link; offline Python, native
C tests, legacy interface tests, fast24 PCM impulse and voice-allocation tests.
The actual active-Play predicate is compiled and executed by a native test.
No real Quake III/Alice/Wine audio run is possible in this environment; result
is a well-founded **experimental** fix, not a claim of stutter-free playback.
