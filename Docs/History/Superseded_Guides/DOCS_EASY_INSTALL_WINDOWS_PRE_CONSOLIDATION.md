# Aufake3D v0.8.18 — easy installation guide for Windows

**For players using Windows 10 or 11. No source compilation or registry editing is required when using the supplied launchers. **Alice 2011 does require saving two renamed copies of its original Miles DLL before installing.****

This guide covers **American McGee's Alice (2000)**, **Alice: Madness Returns (2011, VorpalFix 4.2.1 profile)** and **Quake III Arena 1.17**. The Half-Life kit is still experimental and is not covered here.

> **Before anything else:** Lower your headphone/speaker volume. Aufake3D uses a high default master gain of **5.0**, with a limiter. Back up the **entire game folder** before installing. These are manually copied files; there is no automatic uninstall receipt.

## 1. Find the correct download

Download the **compiled Aufake3D v0.8.18 runtime ZIP** (for example `Aufake3D_v0.8.18_Local_Runtime.zip`, if you have that local build). **Do not use** `Aufake3D_v0.8.18_Complete_Source.zip`: that contains development source code, not the ready-to-copy binaries.

Extract the runtime ZIP fully. The extracted top-level folder contains `Game_Kits`.

## 2. Select the kit matching your game

| Your game | Folder to open inside `Game_Kits` | Find this original executable on your PC |
|---|---|---|
| **Alice (2000)** | `Alice_2000/COPY_TO_GAME_FOLDER` | `alice.exe` (possibly displayed as `Alice.exe`) |
| **Alice (2011) with VorpalFix 4.2.1** | `Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER` | `alice.exe` in the game `bin` folder |
| **Quake III Arena 1.17** | `Quake_III_117/COPY_TO_GAME_FOLDER` | `quake3.exe` |

**The golden rule:** Copy **everything *inside*** `COPY_TO_GAME_FOLDER` into the directory holding the original game `.exe`. Do **not** copy the outer folder itself. If a `SndDrivers` folder appears, **merge** its contents with your existing `SndDrivers` folder; **do not delete or replace the whole folder**.

### Alice (2000) — simple setup

1. Back up the game directory. Make sure the real `alice.exe` is present and that your original Miles sound files, including `SndDrivers/mss32.dll`, are intact.
2. In the runtime ZIP, open `Game_Kits/Alice_2000/COPY_TO_GAME_FOLDER`.
3. Copy **all eight files** into the directory containing `alice.exe`:

   ```text
   <your Alice (2000) folder>/
     alice.exe                      YOUR original game - keep it
     a3d.dll                        from Aufake3D
     a3dapi.dll                     from Aufake3D
     alice-a3d-bridge.exe          from Aufake3D
     alice-a3d-bridge.exe.manifest from Aufake3D
     alice.exe.manifest            from Aufake3D
     RUN_AUFAKE3D_WINDOWS.cmd      from Aufake3D
     RUN_AUFAKE3D_WINE.sh          from Aufake3D
     AUFAKE3D_SET_INITIAL_A3D2.ps1 from Aufake3D (initial default)
   ```

   (There are **eight** supplied files; the original game `.exe` is not included.) If an existing `alice.exe.manifest` would be overwritten, back it up and investigate before proceeding.
4. Double-click **`RUN_AUFAKE3D_WINDOWS.cmd`** in the game folder — not the original `.exe`.
5. **On the first Windows launch, Aufake3D selects A3D2 as your initial default.** It makes a backup of the saved `base/config.cfg` before changing only `s_milesdriver`. If the config is missing, it first lets Alice generate it and sets A3D2 after the first session. Later launches do not change that setting; you can select Miles 2D or Dolby in-game and the selection will be respected. If A3D2 did not start, use the game's sound settings to select **Aureal A3D 2.0** once.

**Expected:** Sound starts normally, and selecting A3D2 opens its provider. If you change provider, allow the game to restart its sound system. Alice 2000's full round-trip provider switching still needs independent gameplay validation for this release candidate.

### Alice (2011, VorpalFix 4.2.1) — important preparation first

**Stop before copying the kit.** The current adapter is designed for a **specific** Alice 2011 executable and Miles DLL. The original `SndDrivers/mss32.dll` must be preserved, because the new `mss32.dll` supplied by Aufake3D is a proxy that still needs the original.

1. Start with a **clean, functioning Alice 2011 + VorpalFix 4.2.1** installation. In the directory containing `alice.exe`, confirm you have `winmm.dll`, `VorpalFix.ini`, and `SndDrivers/mssa3d2.m3d`. Do not replace those files.
2. Confirm your files match these required SHA-256 fingerprints **before installing**:

   | Your original file | Required SHA-256 |
   |---|---|
   | `alice.exe` | `08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50` |
   | `SndDrivers/mss32.dll` | `14fb663762695a02e06b144c487254b08163185fa009efb32df733882cd570de` |

   *Easy way to check:* Open PowerShell in the folder containing `alice.exe`, then run:

   ```powershell
   Get-FileHash -Algorithm SHA256 .\alice.exe
   Get-FileHash -Algorithm SHA256 .\SndDrivers\mss32.dll
   ```

   The displayed `Hash` values must match the two values above. **If either differs, stop.** Do not blindly copy the proxy into a different game build. If you previously installed Aufake3D, first restore the genuine game-owned Miles DLL from your backup; the proxy will not have the required hash.
3. **Before copying anything from Aufake3D**, make two *copies* of the genuine original `SndDrivers/mss32.dll`:

   ```text
   COPY FROM:  SndDrivers\mss32.dll       (your original file)
   COPY TO:    a3d_mss_real.dll            (next to alice.exe)
   COPY TO:    SndDrivers\a3d_mss_real.dll
   ```

   You can copy the DLL with File Explorer and rename the two copies. Leave `SndDrivers/mss32.dll` in place until the next step. **Both saved copies must still be the ORIGINAL DLL, not Aufake3D's replacement.** Also back up any existing `mss32.dll` in the folder containing `alice.exe`.
4. Now open `Game_Kits/Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER`. Copy **all contents**, including the `SndDrivers` subfolder, into the directory with `alice.exe`. Choose to **merge** the `SndDrivers` folder (not replace the entire folder). This installs the Aufake3D proxy at both `mss32.dll` locations while preserving your two original copies.
5. Make sure the finished layout resembles:

   ```text
   <your Alice (2011) bin folder>/
     alice.exe                        original game, unmodified
     winmm.dll, VorpalFix.ini        keep original VorpalFix files
     a3d_mss_real.dll                saved ORIGINAL Miles DLL
     mss32.dll                       Aufake3D proxy
     a3d.dll, a3dapi.dll             Aufake3D
     a3d-miles-local.manifest        Aufake3D
     alice-a3d2011-native.exe       Aufake3D selector bridge
     RUN_AUFAKE3D_WINDOWS.cmd        launch this file
     AUFAKE3D_SET_INITIAL_A3D2.ps1  initial default setup
     SndDrivers/
       mssa3d2.m3d                   keep original
       a3d_mss_real.dll              saved ORIGINAL Miles DLL
       mss32.dll                     Aufake3D proxy
       a3d.dll, a3dapi.dll           Aufake3D
       a3d-miles-local.manifest      Aufake3D
   ```

6. **Before starting**, check that `alice.exe.manifest` does not already exist in this directory. The v0.8.18 launcher creates it **temporarily** and will refuse to overwrite an existing one. If it exists, don't simply delete it; identify whether it belongs to an existing installation or a previous interrupted test.
7. Double-click **`RUN_AUFAKE3D_WINDOWS.cmd`**. On your **first** run, it seeds A3D2 in the saved configuration at `Documents/My Games/American McGee's Alice/config.cfg` (with a backup), without forcing the command line. To check switching, try Miles 2D → A3D2 → Dolby → Miles 2D → A3D2. The launcher uses the RAM-only selector bridge and deliberately does **not** force the `a3d2` startup setting.

**Expected:** A3D2 should be selected initially, then the sound changes with the selected provider, and switching back to Miles 2D does not reopen A3D2. The dedicated RAM selector was validated in a gameplay test; the final integrated v0.8.18 release candidate still merits a check on your exact setup.

### Quake III Arena 1.17 — simple setup

1. Back up the game directory. Confirm `quake3.exe` is present and that the `baseq3` folder contains compatible original Quake III 1.17 game data (`pak*.pk3`). Incorrect or mismatched PK3 files can prevent the game from working independently of Aufake3D.
2. Open `Game_Kits/Quake_III_117/COPY_TO_GAME_FOLDER` and copy **all five files** next to `quake3.exe`:

   ```text
   <your Quake III 1.17 folder>/
     quake3.exe                  YOUR original game - keep it
     baseq3/                    YOUR existing game data - keep it
     a3d.dll                    from Aufake3D
     a3dapi.dll                 from Aufake3D
     quake3.exe.manifest        from Aufake3D
     RUN_AUFAKE3D_WINDOWS.cmd  from Aufake3D
     RUN_AUFAKE3D_WINE.sh      from Aufake3D
   ```

   If `quake3.exe.manifest` already exists, back it up and check whether another modification depends on it.
3. Double-click **`RUN_AUFAKE3D_WINDOWS.cmd`**.
4. Open Quake III's console and enable A3D with **`s_enable_a3d 1`**. If prompted, restart the sound system or game. The launcher already supplies the recommended sound-mixing timing settings.

## Alice (2000): preserving and recovering video settings

Aufake3D should **never** reset `r_mode`, `r_customwidth`, `r_customheight`, `r_fullscreen` or other video/keybinding settings during ordinary launches. The one-time sound-preference helper does **not** restore its `.bak` file at launch. It now refuses to create a partial `base/config.cfg` when no game configuration exists. On a brand-new installation, the first launch lets Alice create a complete config; after the game exits, the launcher saves A3D2 **only if the game left its provider unset or `auto`**. An explicit Miles/Dolby choice made during that first session is respected. The first launch may therefore use Miles 2D.

If an earlier installation has already reverted your resolution to 640×480, first close the game. In PowerShell inside the folder containing the original `alice.exe`, run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\AUFAKE3D_RESTORE_DISPLAY_SETTINGS.ps1
```

This **optional, manual-only** recovery copies only `r_*`, `vid_*` and `gl_*` settings from `base/config.cfg.AUFAKE3D_before_A3D2_default.bak` into the active `base/config.cfg`. It preserves the current sound provider, binds and other choices, and saves a dated backup of the current file first. It never runs automatically. If the old backup does not contain your preferred resolution, set it inside Alice instead.

If resolution still resets after this repair, do not repeatedly run the recovery utility: inspect what Alice actually saves in `base/config.cfg` before and after a launch. That would identify an independent game configuration-loading or graphics-mode issue.

## About the A3D2 default (Alice on Windows)

The new `AUFAKE3D_SET_INITIAL_A3D2.ps1` helper is invoked **only until its first successful setup**. It edits the existing game `config.cfg` (or creates one if missing), saves a `.AUFAKE3D_before_A3D2_default.bak` backup if needed, and writes a marker file named `AUFAKE3D_A3D2_INITIAL_DEFAULT_DONE.txt` beside the launcher.

**It is not a permanent override.** Once initialized, the launcher never forces `+set s_milesdriver a3d2`, never creates an `autoexec.cfg`, and never substitutes a Miles provider handle. Switching to Miles or Dolby inside the game remains permitted and those settings can persist to later launches. If you previously set Miles in your config, the *first* launch of this updated kit changes it once to A3D2; after that your choices are yours again.

The helper requires built-in Windows PowerShell. If it cannot write the config (for example, due to permissions), it prints a warning and launches Alice anyway: just select A3D2 in-game. **This initial-default change is source-checked, but its in-game behavior still requires a fresh gameplay round-trip test.** Existing custom `autoexec.cfg` or modifications that override `s_milesdriver` can also take precedence.

On Linux/Wine the current scripts still respect the game's saved setting; the one-time default seeder is Windows-only.

## Having trouble?

| What you see | What to do |
|---|---|
| The launcher says the game `.exe` is missing | You copied into the wrong directory. Find the actual `alice.exe` or `quake3.exe` and use that folder. |
| The game can't find `a3dapi.dll` or the bridge | Recopy **all** files from the correct kit. Do not copy only the two DLLs. |
| Alice 2011 complains about `a3d_mss_real.dll` | Restore the **original game-owned** `SndDrivers/mss32.dll` from your backup, then create the two required renamed copies before installing the proxy. |
| Alice 2011 says an `alice.exe.manifest` already exists | Don't overwrite it. Identify and safely back up the conflicting file; an interrupted previous run can leave one behind. |
| A3D2 is not initially selected | Check that Windows PowerShell was allowed to run the included helper. Otherwise select A3D2 once in the audio menu. |
| A3D2 isn't available or switching sounds wrong | Start from the provided `RUN_AUFAKE3D_WINDOWS.cmd`; avoid old test launchers, forced startup sound settings or mixing files from different Aufake3D versions. |
| Sounds too loud | Lower your system or headphone volume before testing. Default master gain is 5.0. |
| Quake III crashes or has incompatible UI | Confirm the original `pak*.pk3` files match the Quake III **1.17** executable. |

## Uninstalling a manually copied kit

The safest option is to **restore the complete backup you made before installation**. If restoring individual files, remove only files that were added by Aufake3D and restore **every original file that was overwritten**. In particular, Alice 2011 must regain its genuine `SndDrivers/mss32.dll`. Never delete the retail game `.exe`, `baseq3` data, `mssa3d2.m3d`, VorpalFix `winmm.dll`, or `VorpalFix.ini`.

If you used the **automated** installer instead, use its rollback instructions and receipt; do not manually delete files that the installer is tracking.

## Linux / Wine users

Copy the same game's kit into its Windows-game directory and launch **from that directory** using:

```bash
bash ./RUN_AUFAKE3D_WINE.sh
```

The Wine scripts configure DLL overrides. If necessary, set the desired `WINEPREFIX` in your terminal first. Alice 2011's current Wine profile is experimental and has not received the same validation as the Windows test. Consult the full `Docs/MANUAL_INSTALLATION.md` in the runtime package for advanced details.

---

**Release status:** Aufake3D v0.8.18 is a release candidate. The game, game-owned Miles DLL, VorpalFix, and original game assets are not distributed with Aufake3D. The Alice selector bridges change only checked child-process memory, not the original on-disk game executables. This is a user-friendly guide to the existing kit, not a claim that every A3D game or configuration is supported.
