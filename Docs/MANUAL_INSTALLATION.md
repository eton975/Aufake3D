# Manual installation — Windows 10/11 and Linux/Wine

These instructions use **only file copying**, not the Aufake3D install scripts.
Each kit already has the correct final filenames: **no DLL renaming is required**.
Use a clean, working installation of the original game and take a complete backup first.

## 1. Choose one kit

| Game | Open this directory inside the release ZIP | Game folder is the one containing... |
|---|---|---|
| Alice (2000) | `Game_Kits/Alice_2000/COPY_TO_GAME_FOLDER/` | `alice.exe` |
| Alice (2011), VorpalFix 4.2.1 | `Game_Kits/Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER/` | `alice.exe` |
| Quake III Arena 1.17 | `Game_Kits/Quake_III_117/COPY_TO_GAME_FOLDER/` | `quake3.exe` |
| Half-Life 1.0.1.1 | `Game_Kits/Half_Life_1011/COPY_TO_GAME_FOLDER/` | `hl.exe` |

> **Copy the contents of** `COPY_TO_GAME_FOLDER`, not the enclosing directory.
> Never overwrite your retail `.exe`; the archive does not contain one with that name.

## 2. Special prerequisite — Alice 2011 *before* copying the kit

Alice 2011's tested name-fix is **version-pinned**. The original game must already have
VorpalFix 4.2.1 (`winmm.dll`, `VorpalFix.ini`) and `SndDrivers/mssa3d2.m3d`.
Do not replace any of those files.

**Verify the files in your own game first:**

| Game-owned file | Required SHA-256 |
|---|---|
| `alice.exe` | `08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50` |
| `SndDrivers/mss32.dll` (original Miles) | `14fb663762695a02e06b144c487254b08163185fa009efb32df733882cd570de` |

Windows: `Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\path\to\file'` in PowerShell.
Linux: `sha256sum '/path/to/file'`. **Stop if either hash differs.**

Before you copy Aufake3D files, make the following two **copies of the original Miles DLL**:

| Copy from (your game) | Copy to (your game) |
|---|---|
| `SndDrivers/mss32.dll` | `a3d_mss_real.dll` |
| `SndDrivers/mss32.dll` | `SndDrivers/a3d_mss_real.dll` |

Back up any already-existing `mss32.dll` in the game root as well. Do not let
either saved vendor DLL become an Aufake3D proxy. Both saved files must retain
the exact original Miles hash shown above.

## 3. Copy one complete kit into your game folder

**Alice 2000:** Open `Game_Kits/Alice_2000/COPY_TO_GAME_FOLDER` and copy these files beside `alice.exe`:

```text
a3d.dll                 a3dapi.dll
alice-a3d-bridge.exe    alice-a3d-bridge.exe.manifest
alice.exe.manifest
RUN_AUFAKE3D_WINDOWS.cmd    RUN_AUFAKE3D_WINE.sh
```

**Alice 2011:** Open `Game_Kits/Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER`. Copy **everything** into
the folder with `alice.exe`; when asked, **merge `SndDrivers`** with the existing folder.
The following files must result (the original files remain alongside them):

```text
<Alice2011 folder>/
  alice.exe                    <-- original, NOT supplied or changed
  a3d.dll                     a3dapi.dll
  mss32.dll                   <-- Aufake3D name-fix proxy
  a3d_mss_real.dll            <-- your saved ORIGINAL Miles DLL
  a3d-miles-local.manifest
  RUN_AUFAKE3D_WINDOWS.cmd    RUN_AUFAKE3D_WINE.sh
  SndDrivers/
    mssa3d2.m3d               <-- original, untouched
    mss32.dll                 <-- Aufake3D proxy
    a3d_mss_real.dll          <-- your saved ORIGINAL Miles DLL
    a3d.dll                   a3dapi.dll
    a3d-miles-local.manifest
```

**Quake III Arena 1.17:** Open `Game_Kits/Quake_III_117/COPY_TO_GAME_FOLDER`, and copy
its files beside `quake3.exe`: `a3d.dll`, `a3dapi.dll`, `quake3.exe.manifest`, and
the two `RUN_AUFAKE3D_*` scripts. Keep the correct original `baseq3/pak*.pk3` data.
The old `quake3-a3d-native.exe` is an **optional** experiment in `Extras/Experimental/`,
not part of the ordinary copy kit.

**Half-Life 1.0.1.1:** Open `Game_Kits/Half_Life_1011/COPY_TO_GAME_FOLDER`, and copy
`a3d.dll`, `a3dapi.dll`, `hl.exe.manifest`, `halflife-a3d-alpha.exe`, and the two
`RUN_AUFAKE3D_*` scripts beside the original `hl.exe`. The alpha `.exe` is an
experimental **additional** helper; never rename it to `hl.exe`.

## 4. Launch on Windows

Open the game directory and double-click **`RUN_AUFAKE3D_WINDOWS.cmd`**.
This is a *launcher*, not an installer. It sets appropriate A3D environment variables
and runs the existing original game (or the Alice 2000 child-process bridge).

## 5. Launch on Linux/Wine

Run from the game directory in a terminal:

```bash
bash ./RUN_AUFAKE3D_WINE.sh
```

If required set `WINEPREFIX` to your 32-bit Wine prefix **before** launching:

```bash
export WINEPREFIX="$HOME/.wine-aufake3d"
bash ./RUN_AUFAKE3D_WINE.sh
```

The Wine launch scripts set the required `WINEDLLOVERRIDES` locally. Do not
run the Windows `.cmd` under Wine. A successful launch alone does **not** confirm
an A3D provider opened or that spatial rendering is correct.

## 6. Undoing the manual copy

There is **no automatic rollback receipt** for manual file copying. Restore your
pre-installation backup of the game folder, or restore every overwritten original
file and remove only Aufake3D-added files. For Alice 2011, restoring original
`SndDrivers/mss32.dll` is mandatory. Do not remove the original `mssa3d2.m3d`,
`winmm.dll`, `VorpalFix.ini`, or retail game data.

For direct commands **without either launch script**, see [LAUNCH_COMMANDS.md](LAUNCH_COMMANDS.md).
For automated backed-up installs and rollback, see [AUTOMATED_INSTALLATION.md](AUTOMATED_INSTALLATION.md).

## Notes on compatibility and safety

- All four kits contain the **same exact** universal A3D DLL pair. Duplicate copies are for convenience.
- The Alice 2011 name-fix proxy is only appropriate for the exact pinned build.
- The Alice 2000 bridge can modify its **child's runtime memory** but not the on-disk game EXE.
- A3D 3.0 implementation is incomplete; Unreal, Unreal Tournament, Unreal II and Halo PC are research targets, not supported profiles.
- Default master gain is `5.0`; start with your speaker/headphone volume low.
- The external original Miles DLL, games, VorpalFix and any copyrighted vendor SDKs are **not included**.
