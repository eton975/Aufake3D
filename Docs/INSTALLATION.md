# Install Aufake3D v0.9.2 (Windows 10/11 or Wine)

**This is the current installation guide.** There is no need to compile anything if you already have a verified compiled ZIP. The game must be legitimately installed and its original executable retained.

> **Always back up the entire game directory. Start with low speaker/headphone volume**: Aufake3D defaults to master gain `5.0` with a limiter. Installing a DLL does not establish that a game supports Aureal 3D.

## 1. Find the right ZIP

Use an official release asset after its checks pass, or build locally. **All locally built distributable ZIPs and DLLs are under `dist/` in the source checkout.** GitHub's automatic `Source code (zip)` does **not** contain ready-to-use binaries.

| Use case | Built artifact in `dist/` |
|---|---|
| Game kits, including Alice and Quake III | `Aufake3D_v0.9.2_Local_Runtime.zip` |
| Original retail Descent 3 | `Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip` |
| Bare core DLLs (developer use) | `core/a3d.dll`, `core/a3dapi.dll` |

The ZIPs and core DLLs are **Windows 32-bit PE binaries**, including when compiled on Linux. Run them under native Windows or a suitable 32-bit Wine environment; there are no native Linux `.so` builds.

## 2. Standard game kits

Extract the *runtime* ZIP in full. Inside `Game_Kits/`, locate the kit for your game:

| Game | Folder containing the files to copy | Original executable |
|---|---|---|
| Alice (2000) | `Alice_2000/COPY_TO_GAME_FOLDER/` | `alice.exe` |
| Alice (2011), VorpalFix 4.2.1 | `Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER/` | `alice.exe` in the game's bin folder |
| Quake III Arena 1.17 | `Quake_III_117/COPY_TO_GAME_FOLDER/` | `quake3.exe` |
| Half-Life 1.0.1.1 | `Half_Life_1011/COPY_TO_GAME_FOLDER/` | `hl.exe` |
| Unreal (classic) | `Unreal_Classic/COPY_TO_GAME_FOLDER/` | `Unreal.exe` in `System` |
| RtCW | `Return_to_Castle_Wolfenstein/COPY_TO_GAME_FOLDER/` | `WolfSP.exe` (research only) |
| GTA III / Vice City | `GTA_III` / `GTA_Vice_City`, then `COPY_TO_GAME_FOLDER/` | `gta3.exe` / `gta-vc.exe` |

**Copy the contents of `COPY_TO_GAME_FOLDER` into the actual game executable's directory, not the enclosing `COPY_TO_GAME_FOLDER` directory itself.** Merge nested folders such as `SndDrivers`; never replace the original folder wholesale. Preserve original executable, assets, config and game-owned DLLs. The presence of a kit is **not** a promise of compatibility.

Where supplied, launch with `RUN_AUFAKE3D_WINDOWS.cmd` (Windows) or the matching Wine launcher from the game directory. Choose the game's genuine A3D option; do not rename another provider to pretend that it is A3D.

### Alice (2000)

Copy the supplied Alice 2000 kit beside `alice.exe` and run its supplied launcher. The one-time provider helper aims to select A3D2 when the saved provider is unset/auto without rewriting unrelated video/key bindings. Preserve any existing `.manifest` and `base/config.cfg` before experimenting. You can later select other genuine providers in-game.

### Alice (2011): **mandatory original Miles DLL preservation**

**Do this BEFORE copying the Alice 2011 kit.** The Aufake3D `mss32.dll` proxy does not contain the proprietary Miles sound runtime; it must load an authentic copy from your own game. This profile targets an exact VorpalFix 4.2.1 installation and is **not safe to apply to arbitrary Alice editions**.

1. Confirm `alice.exe`, `winmm.dll`, `VorpalFix.ini` and `SndDrivers/mssa3d2.m3d` exist in their expected places. Keep those original files intact.
2. Verify **your untouched original game files** in Windows PowerShell (run in the folder containing `alice.exe`):

   ```powershell
   Get-FileHash -Algorithm SHA256 .\alice.exe
   Get-FileHash -Algorithm SHA256 .\SndDrivers\mss32.dll
   ```

   Expected fingerprints for the documented VorpalFix profile:

   | Original file | Required SHA-256 |
   |---|---|
   | `alice.exe` | `08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50` |
   | `SndDrivers/mss32.dll` | `14fb663762695a02e06b144c487254b08163185fa009efb32df733882cd570de` |

   **Stop if either hash differs.** If a proxy is already installed, restore the genuine Miles DLL from a clean backup before calculating its fingerprint.
3. From the **original** `SndDrivers/mss32.dll`, make **two copies**, both named `a3d_mss_real.dll`:

   ```text
   <Alice 2011 bin>/a3d_mss_real.dll
   <Alice 2011 bin>/SndDrivers/a3d_mss_real.dll
   ```

   Both copies must contain the original Miles bytes; they are never distributed by Aufake3D. Back up any root-level `mss32.dll` as well.
4. Copy everything inside `Game_Kits/Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER/` beside `alice.exe`, **merging** rather than replacing `SndDrivers`. This installs the replacement `mss32.dll` proxy at both intended locations and the universal `a3d.dll` / `a3dapi.dll`.
5. Do not overwrite an existing `alice.exe.manifest` without investigating its owner. The launcher uses a temporary manifest; interrupted runs may leave something to inspect.
6. Launch `RUN_AUFAKE3D_WINDOWS.cmd`. Test the real provider sequence **Miles 2D → Aureal A3D2 → Dolby → Miles 2D → Aureal A3D2**. Selection and saved settings should be respected rather than permanently forced.

The supplied Alice 2011 launcher must remain paired with the correct DLLs and genuine game-owned runtime. If the game falls silent, restore your backup before trying another build.

### Quake III Arena 1.17

Use a genuine, **matching 1.17 set of PK3 files** in `baseq3` and copy the Quake III kit beside `quake3.exe`. Run the provided launcher. In the console, use `s_enable_a3d 1` and restart sound/the game when required. Incorrect or mismatched PK3 game data may fail independently of Aufake3D.

### Other game kits

Unreal, Half-Life, RtCW and GTA kits are **experimental/research**, not proof that the retail game uses Aureal A3D. For Unreal, its original `System` folder is the relevant executable directory. Before claiming compatibility, verify provider selection and actual DLL use; follow the [status and test guide](COMPATIBILITY.md).

## 3. Original retail Descent 3

Do **not** use the general `Game_Kits` folder or the optional developer probe for this route. Extract `Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip`, enter `COPY_TO_DESCENT3_GAME_FOLDER/`, and copy **both** `a3d.dll` and `a3dapi.dll` beside the game's original `main.exe`. Run Descent 3's own setup and select **Aureal 3D**. The executable is unmodified and no Descent 3 assets are redistributed. See the [dedicated experimental guide](DESCENT3_PUBLIC_RELEASE.md).

## 4. Revert / uninstall

Close the game. Restore its entire backed-up directory or remove only the files that you can definitively identify as installed from the kit. Restore original manifests/configs and any game-owned DLLs. For Alice 2011, restore original `SndDrivers/mss32.dll` and root `mss32.dll` (if any), keeping your separate original Miles backups until verified. Never delete an existing DLL merely because its name matches an Aufake3D component.

## 5. If sound is missing or spatialisation is questionable

Read [Troubleshooting](TROUBLESHOOTING.md). A successful DLL load or left/right sound difference does not by itself establish the fidelity of HRTF, geometry, occlusion or reflections. The [compatibility status](COMPATIBILITY.md) explains how to test these responsibly.
