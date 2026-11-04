# Troubleshooting — start with the simplest cause

**First check `dist/`:** if you're looking for compiled files, the source checkout has no ready-to-install DLLs until you successfully build. The main outputs are `dist/core/a3d.dll`, `dist/core/a3dapi.dll`, `dist/Aufake3D_v0.9.2_Local_Runtime.zip` and the experimental Descent 3 ZIP. Do not hunt for distributable DLLs in source folders.

## Game has no sound

- Confirm that the original game works without modifications and that you've selected the genuine Aureal option supported by that specific edition.
- Check that both `a3d.dll` and `a3dapi.dll` are in the **same directory as the game's actual executable**, except where a kit explicitly requires a nested `SndDrivers` copy.
- Check whether another mod or older DLL is shadowing the new build; restore your backup before changing sound providers again.
- Descent 3 retail: use its ordinary setup and the **separate** [Descent 3 ZIP instructions](DESCENT3_PUBLIC_RELEASE.md), not the developer-only `dist/descent3/` probe or adapter `.obj`.
- If a DLL doesn't appear in PowerShell's module snapshot, capture startup with Microsoft Process Monitor and filter **Process Name = main.exe** and **Path contains a3d**. A successful `Load Image` event confirms a file was mapped into the process, not that its 3D implementation is accurate.

## Alice (2011) loses sound / proxy fails

**Do not overwrite the last surviving original Miles DLL.** The intended VorpalFix installation requires game-owned `SndDrivers/mss32.dll` copied **before** installing the proxy to `a3d_mss_real.dll` both beside `alice.exe` and inside `SndDrivers`. Verify the original executable and Miles DLL SHA-256 against the [installation guide](INSTALLATION.md); do not use a proxy built for different bytes. Keep `mssa3d2.m3d`, VorpalFix files and saved settings intact.

## Build fails, tests skip or output hashes differ

- Use the top-level one-click launcher: Windows `BUILD_WINDOWS.cmd`; Debian/Ubuntu `./BUILD_LINUX.sh`. It activates the **pinned** compiler/Python environment. Do not silently switch to `/usr/bin/clang++` while verifying a pinned build.
- LLVM 19.1.7 is the reference compiler. CI uses Python 3.13.7. Missing optional CMake/MSVC acoustics prerequisites must be reported as skipped or cause a failure when explicitly required; a skip is never a pass.
- Read the complete failure output. A local three-build certificate (`dist/REPRODUCIBILITY_VERIFIED.json`) proves only same-host/toolchain identity; the **five-target** CI result is separate. Never publish a ZIP as reproducible if one mandatory target failed.
- If `git push --dry-run` says `Everything up-to-date` while source files are modified, they are **uncommitted**. Check `git status --short --branch`, include new files with `git add -A`, review `git diff --cached --check` and only then commit.

## Audio sounds wrong

Test with low output volume, confirm stereo (not mono), known sample rate, correct game version and the real A3D provider. Test a fixed-position sound source with a controlled ship/camera rotation. Ordinary stereo panning can imitate directionality; it doesn't prove A3D2 geometry, reflections or authentic Vortex 2 HRTF.

For detailed build dependencies and verification see [Build and release](BUILD_AND_RELEASE.md); for technical instrumentation see [Developer index](DEVELOPER_INDEX.md).
