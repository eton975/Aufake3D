# Aufake3D v0.9.0 — AU8830 renderer development candidate

This is **not a final, gameplay-verified release**.

- Corrected AU8830 coefficient dump from an external contributor: 217 directional
  positions, 56 taps per ear, ITD targets in 1/512 samples. Fixed-180 provenance
  is explicit; original 180-degree abnormal capture is not reproduced as a glitch.
- Added `A3D_HRTF_MODE=fast|reference|legacy`; bit-exact processing explicitly
  remains unavailable. Fast is the default for new game kits; legacy is an easy
  rollback to the v0.8.18 KEMAR renderer.
- New bilinear lookup once per source/render block, float 56-tap FIR per ear,
  fractional input ITD before each ear's FIR, and hardware-style 64-sample
  filter/ITD smoothing in both `fast` and `reference`. This corrects two
  moving-source signal-path problems found during listening regression work.
  The two 56-tap modes currently produce matching PCM; audio-performance
  optimizations must preserve parity. Full hardware arithmetic, atmosphere
  and gain are not exact.
- Retained 6×256 WaveOut buffering, 5.0 maximum gain default with limiter,
  and correct Alice provider-switching bridges. A3D2 remains an initial
  game preference, not a compulsory per-launch override.
- Added Unreal 1998 experimental compatibility kit and RtCW **probe-only** kit.
  RtCW's use of A3D is unproven. Half-Life still requires real gameplay tests.
- Retained one-click native Windows and Linux builds; source CSV is checked
  against a reproducible generated C header before compiling.
- No original game files, proprietary Miles DLLs or Aureal driver binaries
  are included. Confirm permission to redistribute the third-party HRTF data.

The user should compare CPU usage and audio results in all three renderer modes
before shipping this as the normal public distribution.
