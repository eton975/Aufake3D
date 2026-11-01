# PCM ownership, source lifetime and signal path

## Producer–consumer boundary

The game submits source format, ring data, position and control state via the
COM `Source` API in `source_probe.inc`. A successful `Lock` grants writable
sample regions. `Unlock` completes the game write; the audio worker must not
consume uncommitted regions or stale pointers. Source releases, stops and
reposition operations must invalidate snapshots/serials correctly.

The worker renders audio through `A3DMixVoice` in `stream_core.h`. When a
bounded immutable PCM window is captured, `a3dmix_sample_at` reads from that
capture instead of re-reading the game's mutable memory. It first checks
stride/frame bounds and handles the source's ring cursor. Do not change the
ownership model to copy only a pointer without synchronizing its lifetime.

## Bounded DSP path

Broadly, each active voice is sampled and stepped with its rate/pitch;
listener-relative geometry, distance attenuation, Doppler, measured HRTF and
bounded reflection/reverb paths contribute to stereo output. A game-driven
weapon clarity option can use protected/mixed buses. The global `5.0` master
boost is followed by linked limiting to reduce PCM clipping; it is not an
assurance of zero perceived distortion. Output is 48 kHz, signed 16-bit
interleaved stereo. See `a3dmix_render` for the definitive execution order.

Voice registration is bounded to `A3DMIX_VOICES = 128` slots. Full allocation
must fail without dropping unrelated pointers or writing out of bounds;
peak voice count is recorded separately from total capacity.

## Short-SFX edge fade

`a3dmix_short_sfx_envelope` applies a short (~32 output frames, approximately
0.67 ms at 48 kHz) edge fade only to *eligible short, non-looping* sounds
(roughly 300 ms or less). It must not fade longer speech or looped ambience;
`A3D_SHORT_SFX_DECLICK=0` disables it. This suppresses some audible edge
transients but is not a cure for every source update, mixing or driver fault.

## When changing playback code

- Avoid allocation and unbounded loops in the worker's fixed-block render path.
- Keep sample-rate, channel count and bit-depth validation before PCM reads.
- Preserve stale-snapshot rejection and source generation checks.
- Preserve the stable 32 ms queue by default until comparative gameplay tests
  justify alternatives.
- Compare Cheshire Cat dialogue *and* menu rollover sounds; test high-voice
  loads and rapid source restarts separately.
