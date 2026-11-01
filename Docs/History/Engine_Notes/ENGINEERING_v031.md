# Technical implementation notes — v0.3.1

## Real-time path

```
IA3dSource SetWaveFormat / AllocateWaveData / Lock / Unlock
    -> Source-owned PCM memory
    -> Source.Play adds one A3DMixVoice to the process-wide mixer
    -> Dedicated worker, four 256-frame waveOut blocks at 48 kHz
    -> multi-voice resample / spatial HRIR convolution
    -> direct occlusion + first-order delayed specular reflection paths
    -> bounded stereo late-reverb feedback (when enabled)
    -> saturated 16-bit stereo mix -> one waveOut device
```

One critical-section lock coordinates rendering against source removal, format/buffer changes and listener/source movements. Lock/Unlock gates playback during externally writable PCM access to avoid simultaneous writes. A client that retains a lock for a long period may interrupt the corresponding source. Voice slots are bounded at 24; per-source PCM is capped at 64 MiB. A mixer worker is stopped and joined when the root COM object is finally released or Shutdown is requested.

### Known implementation compromises

* Output is always two-channel 48 kHz; input resampling is linear, and the fast renderer applies only 96 early FIR taps from the 48 kHz MIT KEMAR measurement, rather than a frequency-domain full HRIR or individualized HRTF. Direction changes crossfade for 48 frames of each block.
* Acoustic paths are re-traced when the source, listener or committed scene changes (or every five blocks); geometry is tested with brute-force rays, which may be too slow in densely populated levels.
* `SetWaveEvent` currently treats event IDs as byte offsets and the SDK stop sentinel (`0xffffffff`). These semantics need validation using the original Miles provider; alerts correspond to rendering progress, not actual hardware-clock playback.
* Buffer locks temporarily pause a playing source instead of performing strict low-level DMA lock semantics. A client needing precise streaming timing may not work yet.
* Source transforms and material subfaces, full bounding-volume acceleration and source property sets remain incomplete.
* The generic late-reverb feedback delay is an enhancement to first reflections, not the historical Aureal Wavetracing reverb algorithm. It is disabled for games that do not request `A3D_LATE_REFLECTIONS`, unless explicitly enabled through an environment variable.

### Offline verification and quantitative benchmark

The portable mixer uses native C (no Win32 required for tests) and has AddressSanitizer/UndefinedBehaviorSanitizer tests for looping, resampling, multivoice mixing, byte bounds, wall obstruction and geometry-list capture. Its measured HRTF and PCM conversion share headers with the Windows DLL. Compiling and running these tests does *not* test scheduling, WinMM event timing, Windows hardware, Wine's COM activation or game-level functionality.

The simple 24-voice offscreen benchmark renders 300 blocks of 256 frames (~1.6 s of audio); it is *not* a calibrated measurement of the user's FX-6300 or of actual geometry cost. A fast offscreen benchmark is included as `tools/bench_stream_native.c` and can be rerun.

### Production work outstanding

* Actual Alice provider activation, full in-game source/geometry trace and reproducible level test.
* Safe and performant streaming event semantics; lifecycle and underrun tests on Windows 10/11 and Wine.
* Full binaural convolution, real-time HRIR interpolation and room impulse response reconstruction.
* BVH/partitioned geometry, multiple reflection bounces, diffraction, materials, dynamic portals and late reverb.
* Registration-free Windows drop-in strategy and multi-game compatibility matrix.

The historical Aureal SDK was consulted for API/vtable method signatures, but no proprietary driver code is included in this project.
