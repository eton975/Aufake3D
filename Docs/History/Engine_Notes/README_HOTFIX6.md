# A3D v0.6.0 Quake III — Hotfix 6 (experimental idle-Stop optimization)

Hotfix 6 **does not claim stutter-free gameplay**. Its objective is to reduce
unnecessary contention between Quake III's high-frequency Source.Stop calls
and the software HRTF render worker, and to distinguish genuine source
interruptions from harmless calls to stop sources that are already inactive.

## Based on a controlled listening comparison
- 24 HRTF taps, gain 0.1: moderate stutter, slight crackling.
- 48 HRTF taps, gain 0.1: moderate stutter, no reported crackling.
- 24 HRTF taps, gain 0.5: moderate stutter, moderate crackling.
- Weapon sounds largely play correctly; footsteps reportedly truncate when
  weapons fire.

The large DSP improvement at 24 taps did **not** reduce stutter. That
implicates more than HRTF calculation time, but does not yet prove which
source is responsible. Lower gain appears to reduce distortion, so retain
A3D_MASTER_GAIN=0.1 for this diagnostic. The renderer still defaults to its
preserved 48-tap measured HRTF and 128-voice pool.

## Code changes (against Hotfix 5)
1. Add a mixer-membership bit to each IA3dSource, updated under mix_cs.
2. A Stop on an already detached source returns immediately without taking
   the global mixer mutex. It still returns S_OK as required for repeated
   stops. Real source stops are serialized and remove the voice as before.
3. Aggregate, low-overhead counters distinguish:
   * A3D.Mixer.source_stop_noops — calls on already detached sources;
   * A3D.Mixer.source_stop_active — calls that removed playing voices;
   * A3D.Mixer.source_stop_ended — removals of ended, inactive voices;
   * A3D.Mixer.source_play_active_restarts — Play restarting an active source.
4. An explicit A3D.HF6 log marker identifies the correct DLL version.
5. Adds a native compiler-driven regression that compiles the actual Stop
   implementation with a mock mutex and tests 101,000 inactive calls plus
   active and ended stop transitions.

## Audio test on Quake III 1.17 under Wine
Install this release ZIP directly with the standalone Linux manager:

    a3dctl install q3 /path/to/A3D_v0.6.0_Q3_IdleStop_Hotfix6_Portable.zip
    a3dctl status q3

Then from the game directory:

    cd "$HOME/Games/QuakeIII-117-A3D2"
    LOG="$(winepath -w "$PWD/a3d-hf6-debug.log")"
    env -u A3D_TRACE_DETAIL A3D_PROBE_LOG="$LOG" \
      A3D_MASTER_GAIN=0.1 A3D_VOICE_LIMIT=128 A3D_HRTF_TAPS=48 \
      A3D_REVERB_WET=0 A3D_WAVEOUT_QUEUE_HEADERS=3 \
      A3D_WAVEOUT_SUBBLOCKS=2 A3D_Q3_DMA_CLOCK=0 \
      wine ./quake3.exe

Keep Quake III s_mixahead 0.35 and s_mixPreStep 0.05, using the same
demo. Exit normally to flush counters. Compare audible footstep truncation
and stutter with Hotfix 5 using the same settings. Then inspect:

    grep -E 'A3D.HF6|source_stop_|source_play_active|voice_peak|voice_rejections|DSP.blocks_over|queue_empty_events' a3d-hf6-debug.log

**Interpretation:** A large source_stop_noops fraction confirms the idle
hot path was unnecessary. A high source_stop_active or source_play_active_restarts
count points to real source truncation in the client/server contract, but
is not in itself proof of an emulator bug: games are allowed to deliberately
reuse or interrupt voices. Comparing normal non-A3D Quake III is an optional
control to distinguish original sound-channel priority from emulation faults.

Compatibility: the COM ABI, classic Alice bridge, Alice 2011 VorpalFix bridge,
WaveOut backend, HRTF tables, and 128-voice limit remain unchanged.
The real Wine/Windows gameplay results are still unverified.
