# Optional Descent 3 **source-engine** A3D2 adapter

Status: **experimental / standalone-compiled / not game-built / not gameplay-tested**.

This separately maintained, independently written implementation fills in
Descent 3's missing `A3D_*` helper methods by converting the historical
`auddev.h` function signatures into the **real A3D2 COM interfaces** supplied
by the locally loaded Aufake3D `a3dapi.dll`.

It's an optional **source integration for an engine built from the published
Descent 3 GPL source**. It does not patch an original `main.exe` or imply that
a source-built engine is an unmodified retail game. Its code is MIT licensed,
but combining/distributing it with Descent 3 must respect the game source's
GPL-3.0-or-later and all other applicable licenses.

## Historical inputs

`DescentDevelopers/Descent3` at `07262f6`, where `dd_sndlib/auddev.h`
declares `A3D_*` functions under a commented `SUPPORT_AUREAL` switch and
`dd_sndlib/CMakeLists.txt` includes the legacy geometry and sound sources.
The available historical tree lacks a corresponding implementation for the
helper layer. The adapter is based on the official A3D2 COM method contracts,
not copied Aureal proprietary binaries.

## Build integration

First, on a copy of the historical Descent 3 *source checkout*, from the
Aufake3D repository root, run a non-modifying check:

```powershell
python Integrations/Descent3_Source/install_into_checkout.py "C:\Src\Descent3"
```

Then explicitly apply to that *source* checkout:

```powershell
python Integrations/Descent3_Source/install_into_checkout.py "C:\Src\Descent3" --apply
```

The installer changes only `dd_sndlib/auddev.h`,
`dd_sndlib/CMakeLists.txt` and creates
`dd_sndlib/aufake3d_aureal.cpp`. It refuses unknown layouts or repeat
installation, and saves `.aufake3d.bak` copies of the two original text files.
It never modifies the user's retail game directory or builds/replaces EXEs.

Then build the Descent 3 source project using its documented 32-bit Windows
build toolchain. The actual historical game build is **not validated yet**:
other game dependencies, launcher configuration and Windows source portability
may need changes. Game files and original binaries are not distributed.

## Implemented adapter API classes

- `A3D_Init`, `A3D_Destroy`, `A3D_CreateListener` and listener position,
  orientation, velocity, rolloff, Doppler and units-per-metre.
- Static/dynamic PCM source allocation, sample copy using Lock/Unlock,
  play/stop/duplicate, seek/query, positional properties, source lifecycle,
  wave-event registration and gain/priority.
- Geometry lists, triangles, quads, material creation and binding, scene clear
  and flush. Descent 3's original rock/water/metal material values come from
  the historical game source, not guessed in the adapter.

## Unresolved before calling it game support

- The exact original retail loader/API path has not been inspected. The
  source-engine adapter intentionally does **not** attempt to load the
  unmodified retail game itself.
- Sample streaming/event timing and PCM wraparound under real game loads need
  verification. The underlying wrapper implements cursor event signalling,
  but this is not yet demonstrated in Descent 3.
- `IA3dSource::SetPanValues` is now available only via experimental
  `A3D_ENABLE_PAN_VALUES=1`. The original argument semantics are not fully
  reverse-engineered; don't consider this historically exact.
- Global environmental reverb is unimplemented (adapter returns false).
  Geom.BindSource/BindListener are approximated by updating position/orientation
  rather than associating geometry with discrete COM source objects.
- Sound card selection, 3D initialization, 2D stereo mixing, Doppler, cursor
  positions, per-level geometry, and release lifetimes have not been tested
  in a built/played Descent 3 engine on Windows/Wine or the AU8830.
- The built engine may require a genuine A3D provider selection setting that
  the modern game launcher does not expose. Do not relabel non-Aureal providers.

This module does not claim to restore the original, missing Aureal helper
implementation byte-for-byte. It is intended to be a verifiable, independently
written integration path to the existing general-purpose Aufake3D engine.
