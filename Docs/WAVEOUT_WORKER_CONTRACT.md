# WinMM/WaveOut worker — concurrency and evidence

**Do not disable `waveOutGetPosition()` polling merely because its return value
isn't used for fixed-queue playback.** The Windows Alice 2011 test series
showed a repeatable behavioural difference; the underlying WinMM mechanism
is **not conclusively identified**.

## Important quantities

- Internal render block: `A3DMIX_BLOCK = 256` frames at 48 kHz (~5.33 ms).
- The verified Alice 2011 release configuration groups two blocks per header
  (512 frames) and queues three output headers (~32 ms total). The prepared
  header *pool* is larger (`MIX_BUFFERS = 12`) and must not be confused with
  the number of simultaneously submitted headers.
- Default WaveOut position probe: enabled, once every **four** worker wakes;
  `A3D_LATENCY_TRACE` is not required. With adaptive buffering disabled, the
  position result is advisory, not a PCM seek point.
- `A3D_WAVEOUT_POSITION_PROBE` and `A3D_WAVEOUT_POSITION_INTERVAL` were used
  experimentally; their defaults preserve the observed working configuration.

## Worker contracts (see `mixer_thread_run`)

1. Header lifecycle: `WHDR_DONE` determines reclaim eligibility. A prepared
   header cannot be rendered into or resubmitted while the device still owns it.
   The pool tracks a second `mix_header_outstanding[]` state for diagnostics.
2. Snapshot and normal render: mutable voices/source pointers are protected by
   the mixer critical section. Snapshot work must validate `sample_id` and
   `render_serial` before committing positions/events after an unlocked render.
3. Keep external WinMM position calls **outside the mixer lock**; a callback or
   device query may take nontrivial time. Never wait for worker termination
   while holding that same lock.
4. Don't write diagnostic files on the realtime audio thread. The metrics
   report, when enabled, is emitted after worker termination.
5. Do not infer sample correctness or dialogue synchronization solely from
   `queue_empty_events == 0`; our failing tests also showed zero observed
   empty-queue events.

## Evidence from controlled Windows tests (Nov 2026)

| Configuration | User-observed Alice 2011 outcome |
|---|---|
| Position query every 4 wakes, no latency logging | Cheshire dialogue clean; mild menu crackle in early candidate |
| Position query every 8 wakes | Dialogue clean; no claim of universal optimal cadence |
| Position polling OFF | Dialogue stutters/desynchronizes; severe crackle |
| `Sleep(0)` in place of query | Fails |
| `Sleep(1)` in place of query | Fails |
| Position query every 4 wakes with QPC profiling | Dialogue clean; mean observed query duration ~265 µs (2,633 calls) |

Position-probe runs and no-probe controls used the same candidate core. The
successful v0.8.12 RC1/v0.8.13 runtime also added a bounded short-SFX edge
fade; the user reported overall Alice 2011 playback worked very well.
Those tests **do not prove** a particular hidden WinMM lock or driver bug;
they only support retaining the empirically successful polling operation.

## Failure analysis and maintenance

The telemetry includes submitted/completed headers, queue-empty observations,
position-valid/invalid counts, wake/timeouts and a limited PCM boundary-step
counter. PCM boundary jumps can be legitimate transients; they're not a direct
measure of audible crackling. Avoid increasing the 32 ms queue, enabling
unbounded logging or filtering the entire signal without a controlled test.

Retain a configuration switch and rollback path for future Wine/driver-specific
failures. Stereo HRTF and A3D2 provider naming remain independent layers.
