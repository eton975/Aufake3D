# Open A3D game compatibility project — experimental v0.4.1

See `CHANGELOG_V041.md` for the new game-fed spatial rendering changes and test results. This is still a research build, not an in-game-verified replacement.

This release packages two **32-bit Windows x86** compatibility entry points
and the complete project-authored, commented source code. The user retains
ownership of their original game and Miles sound libraries; these are not
redistributed.

**Do not interpret a successful compile, COM test or Miles test as a guarantee
that Alice or Quake III gameplay now has authentic A3D2 sound.** The shared
real-time renderer first introduced in v0.3.1 has not yet undergone live
ingame testing, and 9x Vortex 2 HRTF equivalence has not been established.

## Main binaries

| Filename | Intended consumer | Status |
|---|---|---|
| `a3dapi.dll` | Alice's Miles A3D 2.0 COM provider | Experimental multi-voice spatial+geometry renderer, A3D2 API partial |
| `a3d.dll` | Legacy A3D/DirectSound path used by some Quake III releases | `A3dCreate` bridge to system DirectSound; **not** A3D2 Wavetracing |

Read `dropin/README.md` for installation. Application-local manifests try
registration-free COM activation. `dropin/test_regfree_wine.sh` tests them in
an absolutely fresh Wine prefix, avoiding false passes caused by the older
research prefix's COM registration. The Python installer and Windows batch
installers do not overwrite existing game files or modify your original
Alice.exe. For an unpatched Alice, an optional *separately named* copy is
created after exact-byte pattern validation.

## What is implemented in the A3D2 renderer

The independently written 32-bit DLL contains `IA3d4`, geometry/material/list
COM interfaces, PCM streaming, 24-voice shared 48-kHz mixer, measured MIT
KEMAR HRIR-based binaural rendering, wall occlusion, first-order reflections,
and a preliminary late reverb. Some interfaces and streaming-event semantics
remain partial. It is not a reconstruction of the original AU8830 DSP.

## What still needs real game integration and reverse engineering

- Alice's actual A3D2 selection, source and geometry frame submissions must
  be confirmed by a new in-game trace; the earlier unpatched executable fell
  back to Miles Fast 2D.
- Quake III build/version-specific A3D routes need inspection; newer Quake III
  builds and many source ports no longer call Aureal APIs.
- Full multi-bounce Wavetracing, original A3D2 HRTF coefficients,
  reflection/reverb laws, and fixed-point fidelity remain unimplemented.
- External manifests are not guaranteed to win over embedded executable
  manifests, and Wine's support must be tested on the user's actual build.

## Build and validation

```bash
bash win32/build.sh
bash tools/verify_all.sh
```

The DLLs use Clang targeting 32-bit Windows and `lld-link` with small import
libraries. The unit tests run on Linux and do not require the AU8830. See
`ENGINEERING_v031.md`, `WAVETRACING_AND_ALICE_ROADMAP.md`,
`research/DRIVER_FIDELITY.md`, `LICENSE` and source comments.

No proprietary 9x driver, game executable, or Miles DLL is included. The
bundled measured HRIRs are separately attributed in `MEASURED_HRTF_v029.md`.
