# Aufake3D v0.9.2 — deterministic RtCW BSP surface-export research candidate

**Not a gameplay-certified or period-hardware-compatible RtCW mod.**

## New

- Added `Tools/export_rtcw_bsp_acoustics.py` for validated deterministic
  extraction of *visual planar / triangle-soup candidate surfaces* from original
  RtCW BSP v47 maps or user-owned PK3 archives, with source SHA-256 and shader
  flag/material-hint provenance.
- Refuses malformed geometry, non-finite vertex positions, unsafe output
  overwrite and excessive triangle counts; counts unsupported curved patches.
  Does not modify or distribute original game maps.
- Added synthetic BSP/PK3 regression tests for parser safety, stable serialization,
  and preserving source data. The exporter is included in runtime `Tools/` and
  documented in `Docs/RTCW_BSP_EXPORT_V092.md`.
- Bumped active build, runtime archive and installer metadata to v0.9.2.

## Kept unchanged from v0.9.1

- Shared 56-tap AU8830 Reference/Fast and 48-tap Legacy rendering, fixed
  WaveOut 6 x 256 buffering, master gain 5.0 default, and existing geometry
  diagnostic and provider-switch behavior.
- The default packaging build remains gated by **three exact same-toolchain
  builds**, comparing every generated PE binary and complete runtime ZIP.
- The experimental GTA III/Vice City, Unreal, Half-Life and RtCW kits retain
  their existing unverified status. The tested Alice and Quake III paths have
  not been modified for this milestone.

## Not yet delivered

- Collision-brush reconstruction, curved surface tessellation, geometry
  simplification, BSP->Aureal COM submission and driver material calibration.
- A playable source-modified RtCW executable, physical Vortex 2 operation,
  Windows 95/98/ME/2000 validation, or actual real-game map testing.
- Demonstrated identical Windows-vs-Debian-vs-GitHub checksums; local identical
  same-toolchain checks do not guarantee cross-platform bit identity.
