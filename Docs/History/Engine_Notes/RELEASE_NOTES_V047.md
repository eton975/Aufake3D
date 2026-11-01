# A3D wrapper v0.4.7 — maximum master gain as default

- Baseline: v0.4.6 source/renderer.
- Set the default `A3D_MASTER_GAIN` to `5.0` (same as the maximum accepted gain). Range remains 0.1 through 5.0.
- Updated all three default initialisation points: the core mixer, the first-activity WinMM mixer, and `IA3d4.Init`. No environment variable is required for the full-range default.
- Preserve stereo-linked peak limiter, which may attenuate boosted signal and prevent perceived volume from scaling linearly.
- Keep all spatial, reverb, reflection, listener and source algorithms unchanged.
- The A3D runtime selector is separate and is not modified by this package; no change to stock `alice.exe`.

## Expected diagnostics

`A3D.MasterGain.start.x1000 5000` after first mixer creation, and `A3D.MasterGain.Init.x1000 5000` if IA3d4.Init is called. Use the exact format emitted by the logger.

**Not live-verified** with Alice under Wine or Windows. Offline tests are part of the archive.
