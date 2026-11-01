# A3D Portable v0.5.0 — commented-source engineering guide

**Purpose:** explanatory supplement to the frozen v0.5.0 implementation. It documents the actual code paths and boundaries, with block comments added to the hand-written sources. No algorithm, exported symbol, constant, or compiled binary was changed. Generated measurement coefficients are not individually annotated.

## 1. Module map and read order

| Read | Source | What it controls |
|---|---|---|
| 1 | `portable/a3d_port.py` | PE architecture check, package selection, registration-free COM manifest, safe installation/verification/uninstall |
| 2 | `win32/a3d_legacy_bridge.c` + `.def` | A3D 1.x entrypoint spellings and DirectSound fallback; COM factory forwarding |
| 3 | `win32/a3dapi.c` + `.def` | A3D 2.x CLSID, IA3d3/IA3d4 interface vtables, COM object lifecycle |
| 4 | `win32/source_probe.inc` | PCM source and buffer lifecycle: format, allocation, Lock/Unlock, Play, source positions, velocities and gain |
| 5 | `win32/listener_trace.inc` | Listener's 3D position, orientation, velocity |
| 6 | `win32/stream_core.h` | 48-kHz per-voice mixing, HRTF/distance/Doppler, acoustic contribution, output limiting |
| 7 | `win32/measured_hrtf.h` + `measured_hrir_data.h` | Lookup of measured KEMAR HRIR filter values |
| 8 | `win32/acoustic_scene.h`, `acoustic_dsp.h`, `geom_trace.inc` | Geometry submission and approximate occlusion/reflection/reverb |
| 9 | `win32/stream_winmm.inc`, `waveout_renderer.inc` | WinMM waveOut queue, mixer wakeups and playback teardown |
| 10 | `acoustics/src/` | Independent geometric-acoustics and BSP parser tests |
| 11 | `tools/`, `portable/tests/`, `dropin/tests/` | Regression tests and diagnostic probes |

## 2. Actual playback call paths

### A3D 1.x — legacy fallback, not full emulation

```text
Legacy application → LoadLibrary(a3d.dll) → _A3dCreate@12 / A3dCreate
  → a3d_legacy_bridge.c → DirectSoundCreate → system/Wine DirectSound
```

This permits loader/DirectSound compatibility only. The return object is **not** fed to the measured-HRTF mixer. It does not implement authentic Aureal hardware effects.

### A3D 2.0 — independently implemented software processing

```text
A3D2 application / Miles mssa3d2.m3d
  → CoCreateInstance(A3D 2.x CLSID) → a3dapi.dll
  → IA3d4 root → IA3dSource / IA3dListener / geometry
  → SetWaveFormat / AllocateWaveData / Lock / Unlock / Play
  → voice cursor + source/listener state
  → HRTF / distance / Doppler / early paths / late reverb
  → stereo-linked output limiter → WinMM waveOut → Wine/Windows device
```

Successful class creation or `IA3d4.Init` is *not* evidence that the game has submitted audible per-source PCM; check `IA3dSource.Play` and playback logs.

### A3D 3.x

No complete IA3d5 / A3D3-specific contract is implemented. Games asking for these interfaces may reject the class or be missing features. Do not describe this build as A3D 3.0 compatible.

## 3. ABI and object lifetime

- Win32 **PE32/i386**, not x86-64; COM functions use stdcall-compatible ABIs.
- Exported entrypoints and IA3d vtable slot ordering cannot be rearranged without breaking external callers.
- `QueryInterface`/`AddRef`/`Release` ownership dictates how long source/listener/root objects remain live; test use-after-free and outstanding playback thread references.
- `a3dapi.dll` is class-registered through a game-local manifest by default; the portable script does **not** install drivers, patch the game EXE, or require system-wide registration.
- A present `a3d.dll` is not proof of active HRTF: in this version it forwards `A3dCreate` to DirectSound.

## 4. Mixer and acoustic parameters

- Fixed `A3DMIX_RATE=48000`, `A3DMIX_BLOCK=256`, `A3DMIX_VOICES=24`; the queue and processing cost matter under Wine.
- Per-source PCM is read with a fractional position/pitch cursor, then filtered in relation to listener pose; interpolation choices and coordinate handedness affect perceived direction.
- Default HRTF length `48` taps (configurable); the table is measured KEMAR data, not bespoke Aureal AU8830 filter coefficients.
- Source-gain, distance falloff and reflected-path gains must be handled consistently, otherwise quiet direct sounds can acquire unnaturally strong reflections.
- Master gain defaults to **5.0** (user-requested). Stereo-linked limiter prevents sample overflow but can audibly compress simultaneous loud sources. Lower headphone volume during initial use.
- Geometry/reflections have no effect unless the game actually calls their submission interfaces. Enabling reverb does not validate Wavetracing.

## 5. Quake III Arena 1.17 — practical validation status

- The **real** Quake III 1.17 executable contains `s_enable_a3d`, `s_disable_a3d`, A3D startup strings and the A3D2 COM CLSID. Later 1.32 removed that route. This was established **after** the original v0.5.0 release.
- The user subsequently got **vanilla** Quake III 1.17 running on Debian/Wine with matching historic 1.17 PK3 assets. That fixes the standalone game baseline, **not** the emulator's compatibility.
- Neither the legacy HRTF path nor successful Quake III gameplay audio through v0.5.0 is established. Keep a separate copy of the working vanilla installation.
- For tests: inspect the EXE, install locally into a test copy, run legacy and COM probes, issue `s_enable_a3d`, record `s_usingA3D`, log COM source/renderer calls, and perform directional listening tests.
- `a3d_port.py` intentionally does not rewrite Quake III, Alice, game assets or the registry.

## 6. Building and verifying

```bash
cd win32
bash build.sh             # Clang + lld-link, 32-bit Windows PE targets
cd ..
python3 -m unittest discover -s portable/tests -p 'test_*.py'
python3 -m unittest discover -s dropin/tests -p 'test_*.py'
bash tools/verify_all.sh  # broader checks; may need Wine / other tools
```

The ZIP contains the **precompiled archived v0.5.0 binaries**; compiling the new commentary-only source should produce functionally equivalent code, but hashes depend on toolchain/version. For reproducibility, compare generated exports with the `.def` files and run the portable inspector/tests before installation.

## 7. Engineering risks and follow-ups

1. Rework A3D 1.x into a *real* source-level spatial frontend rather than a DirectSound object forwarder.
2. Capture the exact A3D2 calls made by genuine Quake III 1.17 and implement any missing methods/interface contracts.
3. Build IA3d5 and A3D3 extension support separately; never assume a shared DLL name means shared ABI.
4. Evaluate HRTF output against measured legacy hardware and a deterministic PCM corpus rather than only synthetic smoke tests.
5. Test native Windows and Wine independently; app-local COM manifests and waveOut scheduling can differ.

## 8. License / data

Review the included root `LICENSE`, `acoustics/LICENSE`, and data provenance notes before redistributing. This archive does not ship original commercial Quake III assets, Miles drivers, or Aureal driver files.
