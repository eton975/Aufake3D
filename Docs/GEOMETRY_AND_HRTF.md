# Geometry and HRTF implementation notes

## Source of spatial inputs

The listener/source COM callbacks receive game-supplied positions and
orientations; in a third-person game they need not equal the visual avatar's
heading. We preserve the caller's transform rather than trying to infer camera
or player angles. `geom_trace.inc` receives matrix-stack operations and
primitive submissions, eventually updating `A3DScene` through
`acoustic_scene.h`.

Geometry API entrypoints exist even when the client supplies no actual
triangles. In prior Alice diagnostics many trace calls were observed without
renderable submitted triangles; that is **not** proof that occlusion/wavetracing
has been exercised. Some material serialization/geometry modes explicitly
return `E_NOTIMPL`; A3D 3.0 IA3dGeom2 is not implemented.

## Runtime cost and approximations

The experimental scene representation bounds its triangle/list capacity and
limits expensive retracing for frequently resubmitted scenes. `geometry_lists.inc`
and `geom_trace.inc` translate COM submission into scene geometry;
`acoustic_scene.h` and `acoustic_dsp.h` approximate acoustics. The current
pipeline is not an exact reconstruction of the original AU8830's hardware
wavetracing or all A3D 3.0 modes.

Spatial output uses measured MIT Media Lab KEMAR HRIR data stored in
`measured_hrir_data.h` with front-end code in `measured_hrtf.h` and
`stream_core.h`. The original dataset is freely usable with attribution to
Bill Gardner and Keith Martin; preserve the terms in `THIRD_PARTY_NOTICES.md`.
Generated HRIR tables are deliberately not manually edited or exhaustively
recommented, because their numeric integrity is more important than line-by-line
prose. The default filter uses 48 taps from the available measured data;
proximity, orientation and interpolation details remain areas for objective
acoustic tests.

## Test strategy

The `Source/Engine/acoustics/` library includes synthetic OBJ/BSP fixtures and
CMake tests independent of copyrighted game assets. These prove only their
specific geometric operations. Tests of real-game geometry require runtime
traces demonstrating nonzero scene triangles and directional/occlusion audio
changes—not just successful `IA3dGeom` initialization.
