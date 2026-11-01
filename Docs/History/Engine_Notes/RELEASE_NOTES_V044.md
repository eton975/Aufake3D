# A3D Alice v0.4.4 — experimental direct/reflection balance fix

This is a **single-DLL hotfix** for the successful Alice A3D 2.0 / Wine
runtime-selector installation. It does NOT patch the game executable,
replace Miles SndDrivers files, or change the runtime-selector bridge.

## What changed since v0.4.3

Early reflection gains now follow source/master volume, distance roll-off,
and A3D_MUTE maximum distance. Before v0.4.4, the early reflection path
omitted those terms. That could produce an unusually diffuse, distant
sound field even with late reverberation turned off. Direct HRTF filtering,
late reverb algorithm, output buffering, and default wet mix are unchanged.

New optional diagnostic variable (read when A3D provider initializes):
`A3D_EARLY_REFLECTION_TRIM=0.0..2.0` (default 1.0). Values below 1.0
make early geometry reflections less prominent. Don't set to zero as a
permanent solution; use it only to isolate an issue.

Existing controls retained:
`A3D_DIRECT_TRIM` default 1.0, `A3D_REVERB_WET` default 0.14 only
when late reverb requested (otherwise 0), `A3D_DISTANCE_STRENGTH`
default 1.0, and `A3D_HRTF_TAPS` default 48.

## Install

Exit Alice. From a terminal:

    cd "$HOME/Games/ALICE"
    cp -v a3dapi.dll a3dapi.v043.backup.dll
    cp -v /path/to/unpacked/A3D_Alice_Spatial_Focus_v0.4.4/a3dapi.dll "$HOME/Games/ALICE/a3dapi.dll"

Leave `alice.exe`, `alice-a3d-bridge.exe`, their manifests, and
`SndDrivers/` untouched. Launch exactly as you did for the successful
no-stutter A3D 2.0 test (using your existing `run_wine.sh`).

## Suggested A/B listening comparisons

A. With v0.4.4 installed, launch without A3D_* tuning variables.
   The normal reverb depth remains. Compare the same sound at the same
   game location with the same audio-device volume.

B. If still hollow, with v0.4.4 installed (from the existing launcher dir):

    A3D_DIRECT_TRIM=1.2 A3D_REVERB_WET=0.10 bash ./run_wine.sh "$HOME/Games/ALICE/alice-a3d-bridge.exe"

   This **retains some late reverb** and strengthens the localisable direct
   component, rather than making the entire soundscape dry.

C. If the source still floats in an environment with active scene geometry,
   compare `A3D_EARLY_REFLECTION_TRIM=0.75` by itself.

For diagnosing geometry participation, check A3D logs for
`A3D.Scene.Flush triangles` and `IA3d4.Init requested_flags`.
Zero triangles means this early-reflection fix may have no audible
impact for the observed game scene. In that case, HRTF coloration or
late reverb remains a stronger candidate.

## Rollback

    cd "$HOME/Games/ALICE"
    cp -v a3dapi.v043.backup.dll a3dapi.dll

## Validation limits

A PE32/i386 a3dapi.dll compiled successfully. All 45 Python tests pass,
as do native portable tests for geometry, streaming, audio calibration,
and a new reflected-audio gain/mute regression. Not yet tested under
Wine or inside Alice: any listening improvement is provisional.

This is an independent approximate renderer, not a verified recreation
of Aureal AU8830 DSP or authentic Wavetracing acoustics.
