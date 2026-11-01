# A3D v0.6.0 Quake III Geometry-Cache Hotfix 9 (EXPERIMENTAL)

Built **from Hotfix 7**, not the experimental Hotfix 8 PCM-tail branch.
Includes the fixed 128-voice pool and active-play continuity, without
experimental overlapping one-shot tails. Alice 2000/2011 bridges retained.

## Why this test exists

Hotfix 8's *completed* (tails-on) log had 1,785 DSP blocks longer than
5.33ms, 888 longer than 10ms, and worst 45.063ms. The tail mechanism
was NOT invoked (0 tails, 0 deferred PCM commits), so it is not a
plausible explanation of that run's dropouts.

The game resubmits nearly 2,048 acoustic triangles per Flush. The existing
renderer invalidated every source's geometry cache on each Flush, making
very expensive occlusion/reflection tracing recur on successive blocks.
This build rate-limits these *geometry* traces, not PCM or HRTF rendering.
HRTF stays at 48 taps unless explicitly overridden.

## Tunables

* `A3D_GEOMETRY_RETRACE_BLOCKS=8` (default): coalesce scene-Flush
  invalidation for about 43ms; large source/listener movements immediately
  invalidate cache. This intentionally makes acoustic geometry less current.
* `A3D_GEOMETRY_RETRACE_BLOCKS=0`: legacy immediate re-trace on revision
  changes; use for A/B comparison.
* `A3D_GEOMETRY_TRACE=0`: completely disable **occlusion/reflection geometry
  tracing** for diagnosis. Binaural HRTF, panning, distance and PCM remain
  enabled. This may materially change acoustic spatial cues; diagnostic only.
* `A3D_GEOMETRY_TRACE=1`: default, full geometry effects with the above cache.

## Installation (a3dctl v1.1.1)

```
a3dctl install q3 ~/Downloads/A3D_v0.6.0_Q3_Geometry_Hotfix9_Portable.zip
# Optional: append --no-backup (irreversible without separate rollback archive)
a3dctl status q3
```

## Suggested controlled comparison (same Demo 1 each run)

```
cd "$HOME/Games/QuakeIII-117-A3D2"
MODE=8                      # First 8, then 0
LOG="$(winepath -w "$PWD/a3d-hf9-${MODE}.log")"
env -u A3D_TRACE_DETAIL \
 A3D_PROBE_LOG="$LOG" \
 A3D_GEOMETRY_RETRACE_BLOCKS="$MODE" A3D_GEOMETRY_TRACE=1 \
 A3D_MASTER_GAIN=0.1 A3D_HRTF_TAPS=48 A3D_REVERB_WET=0 \
 A3D_VOICE_LIMIT=128 A3D_WAVEOUT_QUEUE_HEADERS=3 \
 A3D_WAVEOUT_SUBBLOCKS=2 A3D_Q3_DMA_CLOCK=0 wine ./quake3.exe
```

For a diagnostic geometry-off third run: set `A3D_GEOMETRY_TRACE=0`,
change the log name to `a3d-hf9-bypass.log`, and repeat.

```
grep -E 'HF9\.|DSP\.|queue_empty_events|voice_rejections' a3d-hf9-*.log
```

We need both the listening results and full log. More traces/cache hits
alone do not prove sound quality. Avoid extended testing if a crash occurs.

## Crash status

The reported `ABABABAB` read fault from Quake III near the end of Demo 1
has not been traced to an offending instruction and cannot be attributed
conclusively to our DLL. The Hotfix 8 off log ended without shutdown
counters; the on log finished and printed them. This build removes Hotfix
8's experimental PCM tail code but is NOT a validated crash fix.

## Test evidence

PE32/i386 build, existing offline suites plus a native cache test which
checks 24 scene revisions: 3 traces at interval 8; 24 at 0; zero with
geometry disabled, and source movement invalidation. Runtime Wine
performance and game compatibility are **not yet verified**.
