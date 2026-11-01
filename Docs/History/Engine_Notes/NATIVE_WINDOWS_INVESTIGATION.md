# A3D v0.6.0 native Windows investigation build

31 October 2026. This is a tested investigation build, not a claim of complete A3D compatibility.

## Results
- Quake III Arena 1.17: Demo 1 completed with A3D active; user confirmed audible at moderate gain.
- Alice 2000: A3D2 opened and skool1 loaded; user confirmed audible. Its installed inverted selector branch is repaired only in the child process RAM.
- Alice 2011 with VorpalFix: user confirmed clean audio after reaching the settled main menu, opening the console with F2, then loading skool1. Eight queued 512-frame output headers were used (about 85 ms at 48 kHz).
- Earlier low-gain tests were almost inaudible. Earlier direct-to-level Alice tests were confounded by menu music overlapping gameplay. The unbuffered remaster also had severe crackle/stutter.

## Preserve your installation
No game executable or game archive is included. No installer or registry writer runs automatically. The original F: installations were not upgraded. VorpalFix winmm.dll and VorpalFix.ini must remain in place.

Each game directory contains a3dapi.dll, a new separately named native launcher, a matching game-sidecar COM manifest, and RUN_NATIVE_A3D.cmd. The included manifests are copies of the already-installed A3D manifests. Do not overwrite a different/custom manifest without reviewing it and backing it up. Back up existing wrapper files before installing this bundle. Installation into the original game directories remains a separate review step.

## Launch
Place the matching files beside the corresponding game executable in a test copy, then use RUN_NATIVE_A3D.cmd. Launchers preserve existing game volume settings; the successful listening tests used s_volume 0.5 and s_musicvolume 0.25. Wrapper gain is 1.0.

For Alice 2011: launch without +map, press Enter through the remaster prompt, wait for the main menu to settle, then start normally or press F2 and enter map skool1. Do not load a map before the menu appears.

For Quake III, enable A3D with s_enable_a3d once startup is complete. The 1.17 test also used s_mixahead 0.35 and s_mixPreStep 0.05.

The native launcher activates the adjacent game .exe.manifest explicitly in its own child main thread. This avoids dependence on stale external-manifest caching and the remaster's embedded-manifest precedence. It does not modify game executable bytes on disk. It checks supported code signatures and exits on activation/bootstrap failure. It does modify its own suspended child in RAM, as the existing selector bridges did.

## Source and validation
The source archive includes build_native_windows.ps1 and windows-build-recipe.json. Supply a Clang/LLD bin directory with -ToolchainBin. Tested using LLVM-MinGW 20261020 / LLVM 23.1.4. The full native build, direct DLL ABI self-test, and COM IA3d3/IA3d4/IA3dGeom test pass. There are five existing unused-function compiler warnings.

Added diagnostics count input/output PCM magnitude, output queue state, source locks and selected WinMM output. Optional A3D_CAPTURE_WAV captures the first eight seconds of PCM to the specified local path on mixer shutdown. No capture is enabled by these release launchers. Sample-lock contention warnings remain under investigation; this build does not silently waive buffer locking rules.

## Remaining limitations and restoration
Clean audio was user-confirmed for the stated remaster test; full-game regression, spatial fidelity and every timing scenario are unverified. Original Alice configurations match their baseline copies. Early original-folder Quake testing saved low-volume/windowed settings. Its exact original q3config.cfg is supplied in the separate original-settings output directory; restoration to F: was denied despite granted permissions. Review/restore that file before treating the preservation work as complete.
