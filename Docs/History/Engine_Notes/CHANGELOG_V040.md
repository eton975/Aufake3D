# Release 0.4.0 — game-local integration candidate

## Added and compiled

1. Legacy `a3d.dll` bridge with five exports matching the authentic historical
   2041 Aureal `a3d.dll` name/ordinal table, including `_A3dCreate@12`.
   This is a DirectSound output bridge; no legacy HRTF/Wavetracing claim.
2. Application-local Win32 manifests for `Alice.exe`, optional patched
   `Alice-A3D2.exe`, `quake3.exe`, and a COM test executable.
3. Cross-platform Python installer with optional verified, non-destructive
   Alice hardware-check bypass and an integrity-preserving uninstaller.
4. Windows 10/11 batch + PowerShell install, no system driver/registry change.
5. Fresh-prefix Wine COM isolation test and Wine game launcher.
6. Installer/manifests tests, reference-export and PE32 structural checks.

## Retained from 0.3.1

The Windows x86 `a3dapi.dll` retains COM `IA3d4`, `IA3dGeom`, reusable lists,
24-voice streaming mixer, measured KEMAR HRIR renderer, early reflections,
occlusion and preliminary reverb. It is experimental and not identical to the
original Vortex 2. The project-owned source is MIT-licensed, with third-party
HRTF measurement attribution in the full source kit.

## Not established

There is no Wine runtime in the build environment. No completed gameplay test
of this new drop-in package exists. A PE32 build and passing offline checks do
not establish that Alice or Quake III plays or produces A3D2 acoustics.

## Driver progress

Read-only disassembly of the actual 2041 `Au30DAL.dll` confirms the three
HRTF-related DeviceIoControl values `0x001D2F90`, `0x001D2FB8`, and
`0x001D2FE0` at the corresponding exported routines. These findings are
recorded in `research/DRIVER_FIDELITY.md`. The algorithm and AU8830 filter
coefficients are not yet recovered.

An explicit, optional per-user 32-bit Windows COM registration fallback is
provided for systems that ignore sidecar manifests. It is not invoked by
default and refuses to overwrite an existing Aureal registration.
