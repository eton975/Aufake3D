# Descent 3 retail — experimental Aufake3D v0.9.2 kit

**For an existing copy of the original Descent 3 game (`main.exe`), not for building the open-source engine.** The retail route uses the same two universal Aufake3D DLLs as other supported/experimental games. It never modifies the original game executable.

## Get the right file

The **public experimental download** is:

`Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip`

A normal source build generates it at **`dist/Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip`**. This ZIP is intended to be published as a separate GitHub Release asset **only after the required certification passes**. GitHub's automatic *Source code (zip)* is not this file.

> **Do not confuse** the public ZIP with `dist/descent3/`: that optional folder contains a development COM probe `.exe`, a standalone test adapter `.obj`, and diagnostics. Those files do **not** belong in a player's retail game installation.

## Install on Windows

1. Close both Descent 3 and its setup program. Back up the complete game folder, including any existing A3D DLLs.
2. Extract the public experimental ZIP. Open `COPY_TO_DESCENT3_GAME_FOLDER/` and copy **both** `a3d.dll` and `a3dapi.dll` into the folder containing the original `main.exe`.
3. Run Descent 3's usual setup utility and select **Aureal 3D** as the actual sound provider. Do not relabel another backend. Keep normal game settings intact.
4. Start the existing game, listen at conservative volume and test ordinary campaign audio. If anything fails, restore the original game directory backup.

No administrator installation, game EXE patch, COM registry registration, original Aureal driver, proprietary game data or separate Descent 3 source build is intended for this kit.

## What testing has established

A retail Descent 3 test on Windows showed:

- The unmodified `main.exe` successfully loaded the **local** `a3dapi.dll`, captured in ProcMon `Load Image`/module records.
- With Aureal 3D selected and the DLLs present, game audio played. With the two local DLLs removed and setup unchanged, the game became silent; **restoring** the DLLs restored sound (A/B/A test).
- A 3D-mode stereo recording showed interchannel timing and high-frequency level changes, and the tester perceived more immersive spatial sound than in 2D mode.

This supports **real DLL use and some working game audio**, but does **not** conclusively establish correct Aureal HRTF, accurate positional sound, real A3D2 geometry, reflections, occlusion or broad game-version compatibility. Record this as **EXPERIMENTAL**, not gameplay-certified.

For a useful next test, find a safe stationary environmental sound, stay in one position, rotate through 360° and record in stereo. Compare to the same scene in 2D mode. See the [compatibility test guidance](COMPATIBILITY.md).

## Public ZIP contents and verification

The public archive has a ready-to-copy folder with **only the universal Win32 x86 `a3d.dll` and `a3dapi.dll`**, plus `README_FIRST.txt` and `CONTENT_SHA256.json` for installation and checksums. The SHA-256 sidecar in `dist/DESCENT3_PUBLIC_RELEASE_SHA256.json` records the complete archive digest outside the ZIP.

The build uses fixed ZIP member order, timestamps and metadata with `ZIP_STORED` to make the **complete ZIP bytes reproducible**. The normal three-way local build and separate five-target CI comparison must verify the raw public ZIP bytes, not just decompressed file content. The five targets are Windows Server 2022, Ubuntu 24.04, Ubuntu 26.04, Ubuntu 26.10 and Debian 13. A source change, local pass, or CI workflow file does **not** itself establish that a published archive was certified; inspect actual passing evidence first.

**Developer distinction:** `Integrations/Descent3_Source/aufake3d_aureal.cpp` is an experimental *source-engine* adapter. The standalone `.obj`/contract-probe executable is useful for development, but is not a game-loadable DLL or a linked Descent 3 engine. Neither is needed for the retail DLL test.

Read [Installation](INSTALLATION.md), [Build/release](BUILD_AND_RELEASE.md) and [Troubleshooting](TROUBLESHOOTING.md) for further steps.
