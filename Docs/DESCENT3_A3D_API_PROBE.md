# Descent 3 original A3D2 backend: testable interface milestone

**Development-only. Not a Descent 3 game patch, playable compatibility claim,
or an authentic recreation of the missing game-side A3D helper implementation.**

The historical `DescentDevelopers/Descent3` tree at **`07262f6`** declares
`A3D_*` helper functions in `dd_sndlib/auddev.h`, but `SUPPORT_AUREAL` is
**commented out** there. `dd_sndlib/CMakeLists.txt` lists no file implementing
those helpers. The presence of conditional calls in `Ds3dlib.cpp`,
`dsound3d.cpp`, and `geometry.cpp` consequently does **not** establish
that the community source can build an Aureal backend, nor that the original
retail executable uses the same path. The original retail `main.exe` is not
available in this test environment.

This milestone provides a **no-retail-assets, registration-free Win32 x86
executable** to exercise the standard Aureal A3D2 COM operations that would be
needed by a reconstructed Descent 3 helper layer. It directly loads the
co-located `a3dapi.dll` and calls its actual `DllGetClassObject` export;
no COM registry entries, injected DLLs or proprietary game files are needed.

## What the test does

1. Calls `DllGetClassObject(CLSID_A3dApi, IID_IClassFactory)` and creates
   `IA3d4`; initializes scene features (`A3D_OCCLUSIONS|A3D_1ST_REFLECTIONS`).
2. Obtains `IA3dListener`, sets position and two orientation vectors.
3. Obtains `IA3dGeom`, enables geometry, creates and reads back three source-
   accurate material presets in Descent 3's code: **rock, water, metal**.
4. Records three A3D quads with distinct tags in an `IA3dList`, asserts the
   **polygon-count** return semantics of both `End()` and `Call()`; calls
   `IA3d4.Flush()` to commit the scene.
5. Creates `IA3dSource`, negotiates PCM16 mono/22,050 Hz, allocates, locks,
   fills and unlocks a deterministic synthetic waveform, then sets source
   position, velocity and attenuation. **No audio is played by default**.
6. With explicit `--audio`, plays a short, relatively quiet synthetic tone,
   then stops and releases the source. This test remains a listening smoke
   test; it does not prove original-game fidelity.

## Build and use

From the project root, with `clang` and `lld-link` on PATH:

```shell
python scripts/build_descent3_contract_probe.py
```

The script compiles two independent copies and requires byte-identical PE32
output. The result is `dist/experimental-descent3/a3d-descent3-contract-probe.exe`.
The executable requires the *real Aufake3D build* of `a3dapi.dll` beside it.
Use the DLL supplied in the separate experimental test ZIP, or manually copy
one from your own clean Aufake3D build. Do **not** copy Microsoft/Windows
system DLLs, import-library stubs or original Aureal driver files.

On Windows 10, in the directory containing both files:

```powershell
.\a3d-descent3-contract-probe.exe
.\a3d-descent3-contract-probe.exe --audio
```

On Debian with Wine, if your prefix supports 32-bit Win32 executables:

```shell
wine ./a3d-descent3-contract-probe.exe
wine ./a3d-descent3-contract-probe.exe --audio
```

Return code **0** and `PASS: Descent 3 A3D2 synthetic API contract` mean the
probe completed. Failure codes identify the stage (10–17: load/activation,
30–39: source audio, 50–76: geometry/material/list). The probe never inspects
or changes the game installation. It cannot run here because Wine and retail
Descent 3 are not installed in this builder environment.

## Remaining compatibility work

- Verify original retail `main.exe` A3D activation (static imports, dynamic
  loads, COM, and any A3D SDK helper utility library).
- Recover or independently reimplement the **full** Descent 3 `A3D_*`
  utility adapter if source-building a GPL engine; link it to the standard
  Aureal COM APIs and test on Windows. The historical tree lacks the helper
  function definitions under the conditional code.
- Verify source duplication, streaming and cursor/event semantics, geometry
  list retention and material lifetime on a real running game.
- Build and test the GPL game engine separately from the MIT Aufake3D DLL.
  A source-built game is **not** an unmodified retail DLL drop-in.
- Verify reference behaviour on period hardware and perform Alice/Quake
  game regressions before labeling any new game supported.

The existing WaveOut renderer, provider activation and stable game paths are
**not modified** by this probe milestone.

## Inspecting the retail executable without patching it

A read-only local scanner is included, specifically to separate the likely
retail activation mechanism from the reconstructed source-engine path:

```powershell
python Tools/inspect_descent3_executable.py "C:\Games\Descent 3\main.exe" --output "descent3-pe-evidence.json"
```

The path is illustrative, not an assertion about your installation layout.
The scanner records a SHA-256, PE architecture, static Aureal imports and
possible dynamic-loading/COM imports, plus conservative embedded ASCII/UTF-16
markers. A result with no A3D static imports **does not** rule out a dynamic
A3D path; strings and imports **do not** prove runtime behaviour. The original
file is never modified, launched or included in any distribution.

## Optional generic stereo-pan implementation (research build)

The core now contains an **opt-in** implementation of `IA3dSource` vtable
slots 57–58 (`SetPanValues` / `GetPanValues`). Prior builds returned
`E_NOTIMPL`. By default, this remains exactly as before, preserving the
Alice/Quake audio contract. Only with `A3D_ENABLE_PAN_VALUES=1` will callers
be able to set one or two per-ear linear gains in the range 0–1. The gains
are applied after per-voice direct+early-reflection rendering. Values are
copied both on `Play()` initialization and when changed on an active voice.

This is explicitly **not** a verified reconstruction of the original Aureal
pan API semantics (particularly the meaning of the first DWORD argument or
how the original game calculates channel gains). Do not enable it in a known-
good game without controlled A/B testing. The wrapper's existing position
and HRTF path has not been renamed or bypassed.

The main renderer's **source-wave event logic already exists** in both legacy
and snapshot modes; the original historical notes that described registrations
as storage-only should not be interpreted as proof that events never fire.
Event-offset corner cases and streaming behaviour nevertheless need real
Descent 3 testing. This milestone does not modify WaveOut queue scheduling.
