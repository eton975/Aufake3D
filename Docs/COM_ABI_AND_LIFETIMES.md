# Win32 A3D COM ABI and object lifetime

## What is contractual

The core is **32-bit Win32 x86**, not x64 COM. The exported methods have
`__stdcall`/`WINAPI` call convention, `DWORD`/`ULONG` and `HRESULT` widths,
exact GUIDs and a fixed vtable slot sequence. The application calls the
methods **by slot**, not by source identifier. A method reorder can crash the
game despite a successful compile. Existing `.def` exports/ordinals are also
part of the compatibility surface.

The API-class root in `win32/a3dapi.c` exposes supported IA3d1/2/3/4 interface
views and includes the IA3d4 tail *after* preceding methods. There is a
**different legacy class/interface path** in `a3d_legacy_bridge.c`. Do not
confuse the legacy class with an implementation of all modern interfaces.
A3D 3.0 (`IA3d5` and newer family interfaces) remains **unsupported**:
returning `E_NOINTERFACE` is preferable to returning a pointer with the wrong
vtable. SDK contract knowledge is not an implementation.

## COM method rules for contributors

- On successful `QueryInterface`, set the output pointer to a valid view and
  add a reference; on failure, set it to null where the API contract permits.
- Respect `AddRef`/`Release` ownership. Existing root/child lifetime rules
  should be kept consistent; do not free a Source while the WaveOut thread can
  dereference it. See the source's serial/generation guards.
- Maintain `E_POINTER` for null mandatory outputs, and distinguish
  `E_NOTIMPL`, `E_NOINTERFACE`, and ordinary failed initialization.
- Preserve GUIDs, structure packing/layout, signed HRESULT results, and x86
  call convention. Do not fabricate support flags or success responses for
  unsupported reflection/material/geometry methods.
- Update tests when changing a vtable. Include method-slot conformance,
  failed-argument tests, and actual 32-bit Windows/Wine integration where
  possible. An offline ABI pass cannot prove audible 3D rendering.

## Files to inspect

`Source/Engine/win32/a3dapi.c`, `a3d_user_com.c`, `a3d_legacy_bridge.c`,
`listener_trace.inc`, `source_probe.inc`, `geom_trace.inc`, and `a3dapi.def` /
`a3d_legacy_bridge.def`. The historical Aureal SDK was used as a reference;
no vendor copyright licence is implied for wholesale SDK code copying.
