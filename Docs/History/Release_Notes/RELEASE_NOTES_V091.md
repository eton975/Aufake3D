# Aufake3D v0.9.1 — reproducibility-gated development candidate

- **Default build is release-gated:** normal one-click Windows/Linux builds
  must match two independent clean rebuilds, byte-for-byte, across every
  generated PE binary and the complete deterministically packaged runtime ZIP.
- Successful builds write `dist/REPRODUCIBILITY_VERIFIED.json` with SHA-256
  evidence; failed, interrupted or unverified builds do not retain approval.
- Existing shared AU8830 56-tap renderer and 6×256 (32ms) WaveOut defaults
  remain unchanged to avoid introducing audio regressions during build-system
  hardening.
- Experimental GTA III / Vice City compatibility kits are carried forward
  from the separate v0.9.0 patch. This source candidate assumes that patch
  has already been applied; it makes no claims of gameplay verification.
- Original Unreal, Unreal Gold and Return to Castle Wolfenstein integration
  remain research/probe targets. The future RtCW modification should call
  genuine Aureal A3D 2.0 geometry/material APIs for real AU8830 devices under
  period Windows, in addition to supporting Aufake3D on newer systems.
- **Unresolved:** platform-independent byte identity (Windows vs Linux),
  real AU8830/driver validation, and complete A3D material Wavetracing.
