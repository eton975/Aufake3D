# Aufake3D v0.8.16 — Windows MSVC toolchain autodetection fix

**Type:** build-system/maintenance release. **No Aureal audio-engine C source,
COM interface layout, measured HRTF table, or Miles provider-name logic changes.**

## Why

A Windows 10 contributor had MSVC 14.31.31103 installed with ARM runtime
libraries only, alongside MSVC 14.44.35207 containing the necessary x86 and
x64 runtime libraries. `cl.exe` and CMake were present, but CMake's automatic
compiler selection chose incomplete 14.31 for x64 acoustic tests, producing
`LNK1104: cannot open file 'MSVCRT.lib'` (or `MSVCRTD.lib`). Explicitly
selecting the installed 14.44 compiler resolved this failure on that host.

## Changes

- Search VS 2022/2026 installations, including VSINSTALLDIR and vswhere results.
- Select the newest **complete** toolset with matching x64 `cl.exe`, `link.exe`,
  CRT libraries and SDK rather than trusting the first executable on PATH.
- Pass the exact MSVC version and Visual Studio instance to the CMake Visual
  Studio generator (`-T version=...`, `-DCMAKE_GENERATOR_INSTANCE=...`).
- Configure Release CRT and Release compiler probes, and use a per-toolset
  CMake directory so an old failed CMake cache cannot poison the new build.
- Print the detected compiler/SDK versions in `--doctor`; provide a clear skip
  reason for genuinely missing optional prerequisites.
- Add `--require-acoustics` to promote optional C++ tests to required in CI;
  Windows and Linux CI run them instead of silently skipping them.
- Add a regression fixture modeling incomplete MSVC 14.31 beside complete 14.44,
  and a mocked CMake command test verifying the selected toolset reaches CMake.
- Update v0.8.16 build/version/installer/package metadata and source manifests.

## Scope and confidence

The fix is grounded in the successful native Windows diagnosis described above,
but this source archive was validated using Linux-to-Win32 cross-compilation and
simulated Windows discovery tests. An actual v0.8.16 Windows one-click run and
hosted GitHub Windows CI are **not yet verified**. No new gameplay, malware
scanning, or copyright/licensing clearance is claimed. Known-good historical
`a3d.dll`, `a3dapi.dll` and Miles proxy SHA-256 references are intentionally
unchanged; consult `Docs/REPRODUCIBILITY.md`.

Previous notes: [v0.8.15](RELEASE_NOTES_V0815.md) and
[v0.8.14-RC1](RELEASE_NOTES_V0814_RC1.md).
