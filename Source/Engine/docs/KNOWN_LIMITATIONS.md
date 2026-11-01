# Current limitations (v0.2.4)

The original Miles A3D 2.0 provider opens successfully under Wine based on the user's v0.2.1/v0.2.2 reports, and creates A3D sources when sound data is supplied based on the v0.2.3 report. In v0.2.4, an in-memory PCM buffer implementation was added, but has not yet been exercised under Wine. **No sound rendering is implemented.** Source Play returns E_NOTIMPL. Accurate HRTF, geometry Wavetracing, and automatic native Windows 10/11 drop-in deployment remain future deliverables.

Cross-game compatibility is the intended design goal; only the user's Alice-era Miles provider has been examined in depth so far. COM registration is currently performed inside an isolated Wine prefix, rather than by an installation-free drop-in DLL. No original proprietary Aureal/Miles binaries are redistributed in the package.

## Additional engineering limitations

## Do not conflate kinds of fidelity

- **ABI compatibility** = game can load COM and call a method without incorrect stack cleanup.
- **Gameplay compatibility** = the game's actual PCM sources stream and play without audio glitches.
- **Acoustic geometry** = correct polygons, transforms, material coefficients and dynamic objects corresponding to Alice's current level.
- **A3D 2.0 fidelity** = reflects/occludes/filters with behavior comparable to a physical Vortex 2; absent hardware comparisons, an enhanced renderer must be labelled enhanced rather than faithful.

A successful API self-test is neither gameplay compatibility nor A3D2 sound reproduction. The device-independent path is primary; hardware capture remains optional.

## Instrumentation limitations

The COM probe writes a UTF-8-compatible ASCII log in the process CWD (`a3d2-probe.log`). It exposes a partial 50-slot IA3dGeom vtable with correct Win32 stdcall argument byte counts; most unimplemented methods return an error. The geometry converter only supports `A3D_TRIANGLES` and `A3D_QUADS` immediate-mode vertices and ignores transformations. The listener method table maintains positions, orientations, velocities but does not drive an audio renderer. Source/material/list/environment creation is intentionally not faked, so Miles may reject the DLL. The COM implementation uses singletons and lacks production-quality re-entrancy/lifetime handling.

The freestanding DLL has no C runtime; it links imported Kernel32 functions via a generated import library. `win32/build/kernel32-stub.dll` is not part of the deliverables and must never be installed or executed.

## Next test prerequisites

The only external runtime test needed *for this stage* is a **Win32/Wine COM self-test** in its isolated prefix. There is no need to touch `snd_au8830`, boot Windows 9x/XP, or access PCI registers. Once the ABI smoke test passes, the next development task is the Miles/A3D2 source-buffer interface, independent of physical hardware.
