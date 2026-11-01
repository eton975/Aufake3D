# 0.7.0-alpha — Half-Life progress

Diagnosed isolated retail 1.0.1.1 startup failure on obsolete Aureal splash registry setup. Added an explicit, signature-checked child-memory workaround; shared capability bounds/configured limits; bounded optional launcher diagnostics; recursive-target rejection; refreshed generic staging and new boundary/integration tests. Real game audio and Linux gameplay remain unverified.

# 0.7.0-alpha broader compatibility snapshot

Added bounded extended capability responses, IA3d/IA3d2 control views, generic child activation/staging, A3D1/2/3 evidence scanning, supplied Half-Life binary inspection and an audited target shortlist. Full legacy spatial rendering/A3D3 and game runtime validation remain incomplete.

# Changelog

## v0.3.1 â€” game-audio architecture and geometry-list alpha

- Replaced isolated per-source `waveOut` writes with one 48 kHz, four-buffer streaming engine and a shared 24-voice mixer.
- Added continuously advancing playback cursors; 8/16-bit mono/stereo PCM, resampling, looping, source position/gain/pitch updates, stop and source duplication.
- Retained measured MIT KEMAR early-HRIR processing with stateful FIR history, smoothed direction transitions, and a conservative real-time bounded implementation.
- Connected dynamic acoustic geometry to source-dependent obstruction and delayed first-order reflections; added optional elementary late reverb.
- Implemented `IA3dList` Begin/End/Call recording of reusable scene geometry. Corrected the material COM vtable order.
- Added Win32 mixer lifecycle locking, worker termination, and preliminary playback notification events.
- Added standalone guarded/read-only Alice A3D hardware-check inspection with an opt-in copy-only transformation.
- Added native AddressSanitizer / UndefinedBehaviorSanitizer mixer and scene tests; updated the complete build/regression suite.

**Status:** Compiles and passes offline tests. No Wine or Windows runtime test of the *new* engine has been performed; Alice's own A3D2 initialization and full Wavetracing are not demonstrated. No original Aureal/Miles/game binaries are distributed.

## v0.4.4 experimental early reflection balance

- Early reflection audio now obeys source/master level and distance/mute semantics.
- Added `A3D_EARLY_REFLECTION_TRIM` research control (default 1.0).
- Preserved late reverberation and existing HRTF path.
- Added reflection gain/mute regression test.
