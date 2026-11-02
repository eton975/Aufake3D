# Developer documentation — Aufake3D v0.8.18

**Start here for current behavior.** v0.8.18 is a source, build-system and
packaging release. The engine and proxy C implementations are unchanged from the
previous baseline; their compiled bytes are only guaranteed to match the known-good
hashes when the reproducible toolchain is used. Neither a local build nor this
source archive constitutes a new gameplay-validated or antivirus-cleared release.

| Need to do… | Read |
|---|---|
| Understand the full call path and which files own each subsystem | [SOURCE_ARCHITECTURE.md](SOURCE_ARCHITECTURE.md) |
| Change COM methods or ABI contracts | [COM_ABI_AND_LIFETIMES.md](COM_ABI_AND_LIFETIMES.md) |
| Debug the audio thread, WaveOut polling or crackling | [WAVEOUT_WORKER_CONTRACT.md](WAVEOUT_WORKER_CONTRACT.md) |
| Modify playback/PCM source ownership or SFX edge envelope | [PCM_AND_SPATIAL_PIPELINE.md](PCM_AND_SPATIAL_PIPELINE.md) |
| Work on geometry, reflections and KEMAR HRTF | [GEOMETRY_AND_HRTF.md](GEOMETRY_AND_HRTF.md) |
| Understand the Alice 2011 provider naming bridge | [MILES_PROXY_AND_GAMES.md](MILES_PROXY_AND_GAMES.md) |
| One-click Windows/Linux build, toolchain fixes, compiled game kits | [ONE_CLICK_BUILD.md](ONE_CLICK_BUILD.md) |
| Compile, run tests and verify identical DLLs | [../BUILDING.md](../BUILDING.md) and [BUILD_AND_RELEASE.md](BUILD_AND_RELEASE.md) |
| Locate key source functions | [SOURCE_FUNCTION_GUIDE.md](SOURCE_FUNCTION_GUIDE.md) |
| Know what is experimentally implemented, unverified, or unsupported | [COMPATIBILITY_PLAN.md](COMPATIBILITY_PLAN.md) |
| Track old experiment notes | [HISTORY_INDEX.md](HISTORY_INDEX.md) |
| Review redistribution and process-modifying helpers | [LICENSING_AUDIT.md](LICENSING_AUDIT.md) and [BINARY_COMPONENTS_AND_SECURITY.md](BINARY_COMPONENTS_AND_SECURITY.md) |

## What the documentation can and cannot guarantee

The comments document the *actual code* and relevant observed Alice 2011
experiments; they do not turn approximations into hardware-accurate A3D 3.0.
Read API return values (`E_NOTIMPL`, `E_NOINTERFACE`) and unsupported interfaces
as deliberately unfinished functionality. User-reported clean dialogue is
host-specific, not a proof for every driver or Wine backend.

For API modifications: update the focused guide and tests in the same change.
For packaging: verify both the release ZIP and fresh Git-clone source ZIP.

Current toolchain-fix details: [v0.8.16 release notes](../RELEASE_NOTES_V0816.md).
