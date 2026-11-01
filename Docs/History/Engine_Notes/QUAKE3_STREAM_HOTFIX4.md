# Quake III 1.17 — Experimental Streaming Hotfix 4

This is a source-and-binaries engineering build based on the v0.6.0 Hotfix 3a
foundation. It is **not** yet a demonstrated cure under Debian/Wine. Hotfix 3a's
working A3D initialization, contiguous Lock, bounded queue and fixed 24-tap
HRTF window are retained. Original game assets and EXE are NOT included or
modified. Both Alice selector bridges are preserved, but Alice gameplay
regression with this DLL remains untested.

## Changes

1. **DMA cursor bounds:** the default IA3dSource.GetWavePosition reports a
   byte offset modulo the source's circular PCM buffer. Quake III converts
   this to sample units and ring-masks it. Previous code returned unbounded
   rendered bytes.
2. **Event-driven WaveOut:** the output worker uses CALLBACK_EVENT with an
   auto-reset event when supported. An unsupported event mode falls back to
   the old polling backend. `A3D_WAVEOUT_EVENT=0` forces the old behaviour.
3. **Worker priority:** ABOVE_NORMAL is the default (priority 1). Override
   with `A3D_WAVEOUT_PRIORITY=0` (normal) or `2` (highest). This is advisory
   under Wine and does not imply real-time privileges.
4. **Independent DMA clock (optional):** `A3D_Q3_DMA_CLOCK=1` reports a
   monotonic QPC-based byte position to Quake III instead of using the DSP
   render cursor or WaveOut's device cursor. It is OFF by default, to avoid
   modifying Alice's timing. Do not combine it with
   `A3D_WAVEOUT_PLAY_CURSOR=1` for initial A/B tests; independent mode has
   precedence when enabled. The clock may drift from a badly delayed output
   device: that's why this is an experiment, not a proven replacement.
5. **Diagnostics at mixer shutdown:** the log records `event_wakes`,
   `poll_timeouts`, `DSP.max_block_us`, `DSP.blocks_over_5333us`,
   `DSP.blocks_over_10000us` and existing `queue_empty_events`. Timers are
   checked without synchronous log-file writes on each DSP block. All such
   counters require **normal game exit** to appear.

## Installation

**Preserve your existing working Quake III installation** before updating.
Uninstall Hotfix 3/3a using its own original `a3d_port.py` first; do not
hand-delete the install receipt or EXE manifest. Avoid overwriting an owned
DLL because the installer's hash-based rollback would then become invalid.

```bash
G="$HOME/Games/QuakeIII-117-A3D2/quake3.exe"
python3 /path/to/extracted-HF3a/a3d_port.py uninstall "$G"
# Enter the extracted A3D_Portable_v0.6.0_Q3_Stream_Hotfix4 directory:
python3 a3d_port.py install "$G" --profile quake3 --mode both
python3 a3d_port.py verify "$G"
```

## First controlled audio comparison (same demo, separate game runs)

Test A — event-driven output, original render cursor:

```bash
cd "$HOME/Games/QuakeIII-117-A3D2"
env -u A3D_TRACE_DETAIL A3D_PROBE_LOG="$PWD/q3-hf4-a.log" \
 A3D_MASTER_GAIN=0.5 A3D_WAVEOUT_EVENT=1 \
 A3D_WAVEOUT_PRIORITY=1 A3D_Q3_DMA_CLOCK=0 \
 A3D_WAVEOUT_PLAY_CURSOR=0 A3D_WAVEOUT_QUEUE_HEADERS=3 \
 A3D_WAVEOUT_SUBBLOCKS=2 wine ./quake3.exe
```

Test B — same output, independent Quake III DMA clock:

```bash
cd "$HOME/Games/QuakeIII-117-A3D2"
env -u A3D_TRACE_DETAIL A3D_PROBE_LOG="$PWD/q3-hf4-b.log" \
 A3D_MASTER_GAIN=0.5 A3D_WAVEOUT_EVENT=1 \
 A3D_WAVEOUT_PRIORITY=1 A3D_Q3_DMA_CLOCK=1 \
 A3D_WAVEOUT_PLAY_CURSOR=0 A3D_WAVEOUT_QUEUE_HEADERS=3 \
 A3D_WAVEOUT_SUBBLOCKS=2 wine ./quake3.exe
```

After exiting, compare:

```bash
grep -E 'event_mode|QPC DMA clock|queue_empty_events|DSP\.max_block_us|DSP\.blocks_over|event_wakes|poll_timeouts' \
  "$HOME"/Games/QuakeIII-117-A3D2/q3-hf4-{a,b}.log
```

**Interpretation:** An increasing queue-empty counter suggests output
starvation, but is not a direct PipeWire underrun count. DSP max times above
5333 microseconds mean a 256-frame audio render took longer than its nominal
playback duration. A large `event_wakes` count with lower dropouts would
support the event-driven scheduling hypothesis. If both A and B still stutter,
try A with `A3D_WAVEOUT_EVENT=0` to isolate Wine callback compatibility and
share the logs; do not increase queue depth without evidence.

## Verification limits

The PE32/x86 DLL compiles using clang/lld-link and the original 24-tap
native-signal test and offline regression suite pass. We have not run Wine,
Quake III, or the actual audio device in this build environment. No claim of
fully debugged or stutter-free audio is made until the user's runtime check.
