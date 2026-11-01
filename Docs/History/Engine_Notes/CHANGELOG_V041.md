# v0.4.1: Alice/game-fed PCM spatialisation improvements

This update was built and tested offline. It has **not** yet passed an in-game Alice playback test. The last observed Alice launch selected Miles Fast 2D, so its actual A3D2 sound-feed remains the main integration gate.

## Changes

- Wire the original `IA3d4::Init` flags (`0x20` distance and `0x10` automatic Doppler) through the real-time mixer's per-voice processing.
- Respect each source's minimum/maximum audible distance, distance scale, and `A3D_AUDIBLE`/`A3D_MUTE` range policy using 3D Euclidean distance rather than the early Manhattan-distance prototype.
- Apply radial Doppler to the per-source PCM read rate using source/listener velocity, global and per-source Doppler scale, units-per-metre, and a guarded velocity range. This is an approximation, not measured Vortex hardware behaviour.
- Respect `A3DSOURCE_TRANSFORMMODE_HEADRELATIVE`: headphone direction fixed in listener coordinates as the camera turns, with world-space geometry bypassed for those sources.
- Respond to changes in source velocity, distance range, transform mode, Doppler, output gain, and listener velocity while a sample is playing.
- Assign source IDs and log PCM buffer checksums, source ID, size and relative positions at the A3D sample feed/play boundary so a game run can establish which real game samples reach the renderer.
- Add native sanitised regression coverage for range behaviour, Doppler signs, headphone channel output and head-relative source invariance.
- Restore synthetic OBJ regression fixture absent from the source-only zip and update the integration test to check the modern measured-HRTF call signature.

## Verification (not gameplay)

- `bash tools/verify_all.sh`: **PASS**, including 32-bit PE DLL builds, native ASan/UBSan streaming/spatial tests, four CTest acoustics tests, Python source and drop-in installer/ABI tests.
- The Win32 binary outputs were checked as PE32/i386. No Alice.exe, game assets or original Aureal/Miles binaries are included.
- **Not yet verified:** Alice's A3D2 provider activation, COM/Wine app-local deployment on the user's machine, in-game sounds, real hardware waveform fidelity, original Aureal HRTF filters, or Quake III gameplay.

## First Alice gameplay check

Use the safe `dropin/install.py` instructions in `dropin/README.md` against an original, user-owned Alice installation; do not overwrite an installed v0.4.0 release or original DLLs. Confirm the log records `IA3d4.NewSource`, `IA3dSource.Unlock` and `IA3dSource.Play` with IDs and nonzero PCM byte counts. If it shows only COM creation, or Alice remains on Fast 2D, the game-to-provider route still needs repair. Listen for left/right/back/front placement and whether sources become quieter at distance.
