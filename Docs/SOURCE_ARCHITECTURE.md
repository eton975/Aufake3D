# Source architecture and execution flow

## Binary boundaries

Aufake3D consists of a reusable **Win32/x86 A3D COM core** (`a3dapi.dll`
plus `a3d.dll`) and optional integration bridges. Source is shared between
all game kits; per-game activation is not a separate renderer.

```
Original game / Miles / A3D client
       |
       +-- optional app-local Miles proxy (Alice 2011: mss32.dll)
       |     +-- forwards vendor exports to user-owned a3d_mss_real.dll
       |     +-- adapts only pinned provider enumeration/display behavior
       |
       +-- A3D COM activation (app-local manifests/activation contexts)
                  |
              a3dapi.dll: Win32 x86 COM factory / A3D root vtables
                  |
          listener_trace.inc / source_probe.inc / geom_trace.inc
                  |
          stream_winmm.inc: one mixer state + WaveOut worker
                  |
          stream_core.h: bounded 256-frame software mixer
                  |          \ acoustic_scene.h / measured_hrtf.h
                  v
              signed 16-bit interleaved stereo / WaveOut
```

The `.inc` sources are textually included from `win32/a3dapi.c`; they are **not**
standalone compilation units. `a3d_legacy_bridge.c` supplies the separate
legacy-facing DLL. The 39-command, fixed-toolchain PE32 recipe lives in
`Source/Engine/windows-build-recipe.json` and is invoked through
`scripts/build_engine.py`.

## Responsibility map

| Code | Owns | Explicit boundary |
|---|---|---|
| `win32/a3dapi.c` | GUIDs, object/vtable declarations, COM factory and exported entrypoints, opt-in bounded diagnostic log | ABI-critical; do not reorder COM methods |
| `win32/listener_trace.inc` | Listener position/orientation/velocity state and propagation to mixer | Game supplies the transform; no camera reinterpretation |
| `win32/source_probe.inc` | Game source properties, Lock/Unlock, PCM lifetime, playback commands | Prevent worker reading stale or uncommitted game data |
| `win32/geom_trace.inc` | Geometry COM methods, transform stack, materials | Some methods deliberately return E_NOTIMPL |
| `win32/geometry_lists.inc` | Lists/polygon submission | Submission is not proof triangles reached the renderer |
| `win32/stream_winmm.inc` | Mixer synchronization, worker thread, header ownership, WaveOut device, diagnostics | No realtime log writes; position samples advisory |
| `win32/stream_core.h` | Source mixing, distance/Doppler/HRTF/reflections, short SFX envelope, limiter | No WinMM calls; bounded samples/voice capacity |
| `win32/acoustic_scene.h`, `acoustic_dsp.h` | Scene representation and propagation approximations | Not exact vendor wavetracing model |
| `win32/measured_hrtf.h`, `measured_hrir_data.h` | MIT KEMAR HRIR lookups/data | Measurement data has separate attribution obligations |
| `Source/Engine/acoustics/` | Independent C++ geometry/acoustics helpers and synthetic tests | Does not imply every game submits geometry |
| `Source/Alice2011_NameFix_v089/` | App-local vendor forwarder, A3D2 enumeration/name adaptation | Not a general replacement for Miles or A3D 3.0 |
| `Source/Engine/experimental/`, `native/` | Opt-in game launch/activation experiments | Memory-writing helpers merit extra security review |
| `Tools/`, `scripts/`, `release_tests/` | Install, diagnostics, CI and verification | Not part of the realtime audio path |

## Runtime ordering

1. Host loads the compatible A3D frontend (or first traverses the *optional*
   Miles proxy); COM creation allocates/returns the supported root interfaces.
2. Client registers a listener and sources; the game writes PCM via source
   lock/unlock and updates source geometry/position as it runs.
3. Worker owns a prepared WaveOut header pool. It checks completion flags,
   periodically samples playback position, and renders bounded PCM subblocks.
4. The portable mixer spatializes registered sources and converts the result to
   16-bit stereo using its master-gain/limiting policy.
5. Prepared headers are submitted to WinMM and reclaimed only after reported
   completion; on shutdown the worker stops before headers are unprepared.

## Why one engine with several adapters?

Games differ in *how* they request A3D—legacy COM, Miles enumeration, manifest
activation or historical launcher tricks. They should not fork our HRTF core.
Byte-identical `a3d.dll` and `a3dapi.dll` across the four kits are verified by
release tests. Only Alice 2011/VorpalFix's exact pinned version has a confirmed
canonical name-fix playback test on Windows. All other claims require separate
runtime evidence.
