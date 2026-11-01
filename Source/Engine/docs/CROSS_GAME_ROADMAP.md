# Cross-game A3D compatibility roadmap

## Product objective

Alice (2000) is the reference conformance game **only**. The long-term objective is a reusable 32-bit (and where relevant 64-bit) Windows/Wine compatibility layer for the largest achievable set of games using Aureal A3D 1.x, A3D 2.0 and A3D 3.0. A3D 2.0 geometry-aware Wavetracing is the fidelity priority. No blanket claim of compatibility with every title can be made without per-game testing.

## Architectural invariants

- **Versioned frontends:** shared core COM/legacy DLL ABI, proper class IDs, method layouts, capabilities, source/listener/geometry/material interfaces. Legacy titles may use A3D API directly, through Miles, or through DirectSound/property sets. A loader interface is not sufficient by itself.
- **Renderer/backend isolation:** game-neutral scene representation with sources, listener, static/dynamic geometry, material properties and acoustic parameters; software classic and enhanced modes should share the scene model.
- **Platform separation:** same Win32 DLLs run on modern native Windows and Wine. Sound backend uses native Windows output or Wine->PipeWire/ALSA through a suitable audio library; hardware AU8830 should remain optional for research/fidelity measurements.
- **Per-game quirk profiles:** use narrowly scoped compatibility fixes only when demonstrably necessary, never hardcode Alice coordinates, object identities or level assumptions into the shared A3D DLL.
- **Conformance tests:** separate ABI/COM and API semantics tests, geometry and sound-source tests, deterministic waveform rendering tests, Wine integration tests, and end-to-end tests of actual game builds.

## Version targets

| API family | Short-term | Ultimate target |
|---|---|---|
| A3D 1.x | Correct loader and positional-source API | Game-compatible positional/HRTF rendering |
| **A3D 2.0** | Accurate geometry/material COM ingestion and source playback | Reflections, occlusion, geometry-dependent Wavetracing and measured AU8830 comparison |
| A3D 3.0 | Detect version/interface-specific requests | Preserve 2.0 semantics and implement later extensions where documentation/tests permit |

## Test matrix (example categories, not verified supported titles)

- Native Win32 COM DLL loading (`CoCreateInstance`, `QueryInterface`, reference management, registered class availability).
- Historical intermediary engines: Miles 6.x provider loading/selection, DirectSound/DirectSound3D property sets.
- Multiple listener/source and streaming formats, resource exhaustion, pauses/restarts and device changes.
- Geometry scene submission: coordinate systems, transforms, triangles, material binding, changes over time, reflection modes and occlusion.
- One selected release/build per game, with game log and expected audio reference for regression testing.

## Current reality

The v0.1.3 shim only passes offline compilation/structural checks and **one user-reported Wine Win32 direct DLL self-test in v0.1.1**. Real `CoCreateInstance` in Wine, Alice/Miles provider activation and all other game titles remain unverified. The software acoustic engine is standalone and not connected to game source buffers. Full A3D 1.x, A3D 2.0 and A3D 3.0 coverage is **not implemented**.

## First proper milestones

1. Verified COM registry activation in Wine with `a3d-comtest.exe`.
2. Obtain Alice's actual COM/Miles load trace (without AU8830 hardware).
3. Implement correct source and material COM interfaces, streaming and renderer interface.
4. Feed Alice geometry/source data into a real-time geometry engine with binaural output.
5. Start a per-game test matrix, keeping compatibility code generic and opting into game-specific adapters only when required.
