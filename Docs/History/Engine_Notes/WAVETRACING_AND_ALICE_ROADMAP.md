# A3D2 / Alice integration: engineering status at v0.3.0

## Verified observations from the user's Wine environment

- Alice.exe loads the Miles A3D2 plugin but was falling back to Miles Fast 2D on the tested game startup. `mssa3d2.m3d` being *loaded* isn't proof that A3D2 actually opened.
- The standalone original Miles `AIL_open_3D_provider` successfully opened with the custom `a3dapi.dll` after v0.2.1 (IA3d4 + IA3dGeom + wall materials).
- `AIL_set_3D_sample_file` accepted PCM after the SetWaveEvent contract in v0.2.5.
- User confirmed directional left/centre/right Miles-initiated sound in v0.2.7; v0.2.9's KEMAR front/back/above differences were only slight.
- Original AU8830 sound hardware and drivers are not needed for the Windows/Wine software development track.

## What v0.3.0 adds (compiled, native geometry tests; **not** Wine-tested)

- Submitted geometry: A3D primitive mode `A3D_TRIANGLES=3`, `A3D_QUADS=4`, column-major matrix stack and translation/rotation/scale.
- Scene frame lifecycle: `IA3d4.Clear` resets staged geometry, `Flush` commits the frame. Scene capped at **2048 triangles**; overflow counted, not dynamically grown.
- Acoustic materials: reflectance, transmittance and polygon render masks captured on submit.
- Direct-path occlusion through Moller-Trumbore ray-triangle tests with combined frequency-dependent attenuation.
- Specular first-order image-source reflections, visibility checks, speed-of-sound delays, four strongest bounce paths, bounded audio tail, direction-dependent stereo reflection gains over direct KEMAR HRTF.
- WinMM loop flags for already-loaded static samples (`A3D_LOOPED`); **not live streaming/cursor events**.
- Independent instrumented unit tests for wall blocking, same-side specular reflection, frame Clear/Flush lifecycle, transforms and delayed audio effect.

## Important limitations — do not claim the game is complete

1. **Alice provider selection**: The game itself previously reported failure to select the exact A3D2 provider, even when Miles independently opened it. Need compare `s_milesdriver`, enumeration, sound-card detection patch and startup in a controlled, reversible run.
2. **No shared real-time mixer**: Each source still opens its own `waveOut` handle with a pre-rendered PCM buffer. Streaming updates, per-source cursor, callback notification, real-time interpolation and seamless pitch/motion need a shared worker/mixer and synchronized state.
3. **No full A3D geometry list API**: `IA3dGeom::NewList`, `IA3dList::Begin/End/Call` unimplemented. Some games put all geometry in lists; therefore these will not trace properly yet.
4. **No live scene re-spatialization**: Sound position or wall changes after Play do not re-render the already queued sound. Need continuous audio blocks (e.g., 256 frames).
5. **No late diffuse reverb, diffraction, air absorption, multi-bounce ricochets, or source transforms**: v0.3.0 has only simple occlusion and first-order specular reflections, and simple low/high material bands.
6. **No reconstruction of Aureal's proprietary algorithms**: Original AU8830 measurements may improve fidelity later. MIT KEMAR measured HRTF is not Aureal's HRTF.
7. **Not a registration-free drop-in DLL**: Windows/Wine still need COM activation routing; a local COM activation strategy or safe installer must be built and validated on Windows 10/11.
8. **Performance / safety**: 2048 triangle brute-force search and global scene state lack production synchronization, resource bounds and per-game acceptance testing. Treat as a research alpha.

## Fastest credible order to full Alice support

1. Fix game-level provider selection with a reversible strategy; verify in-game wrapper logs and ensure the actual active provider is A3D2, not Miles Fast 2D.
2. Implement A3D geometry display lists and source/listener binding transforms; compare Alice's actual submitted geometry with the BSP topology.
3. Replace separate one-shot waveOut devices with one shared real-time mixer, generation-checked source handles, playback cursors, loop & event semantics, sample-rate conversion and continuous moving HRTF interpolation.
4. Integrate occlusion and early specular reflections **in the real-time mixer**, use material bands and per-path HRIRs; implement bounded late reverb and test audible room transitions.
5. Test actual Alice levels (indoor, outdoor, doorways, moving enemies) with original audio assets; instrument latency, underruns, CPU use, listener orientation, source count and wall segments.
6. Package a Windows 10/11 setup and Wine plugin with reproducible builds, per-game options and explicit support matrix. Broaden A3D 1.x, 2.0 and 3.x titles only after Alice is validated.

## Test and reproduction

Build Win32: `bash win32/build.sh`

Offline geometry+DPS sanitizer test:

`clang -std=c11 -Iwin32 -O1 -g -Wall -Wextra -Wno-unused-function -fsanitize=address,undefined tools/test_acoustic_native.c -lm -o /tmp/a3d-acoustic-test && /tmp/a3d-acoustic-test`

The existing Miles playback and diagnostic scripts are retained. No need to repeat positional test now. No claim of game-compatible A3D2 playback should be made until real Alice logging proves it.

A3D primitive values and matrix layout were verified against public ia3dapi.h (docbrown/3dml); acoustics are independent original implementation, not code from Aureal's driver.
