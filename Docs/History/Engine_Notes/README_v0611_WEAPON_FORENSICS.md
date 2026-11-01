# A3D v0.6.11 — Automatic Weapon Audio Forensics (Alice 2000 / 2011)

**Purpose:** Diagnose quiet/missing weapon sounds, including Jabberwock's Eye Staff, with ordinary gameplay rather than repeated manual recreations. **Diagnostic release candidate, not a sound-priority fix.** The common A3D rendering path and profiles are unchanged.

## Run on Windows (or Wine)

1. Back up the working installed `a3dapi.dll` / `a3d.dll`, game-specific bridges, and configuration. Copy the matching Alice2000 or Alice2011-VorpalFix v0.6.11 package into its existing game directory. Original legally installed game, Miles plugin and VorpalFix (2011) are required; no game EXE included.
2. Use **`RUN_A3D_WEAPON_DIAGNOSTIC_WINDOWS.cmd`** or **`RUN_A3D_WEAPON_DIAGNOSTIC_WINE.sh`**. Do not use the normal launcher for capture. Audio and FPS profiles remain identical to v0.6.9/v0.6.10. The separate 144 FPS launcher for Alice 2011 remains optional.
3. Play normally and exit normally. No GOOD/BAD flags are required. If you notice trouble, optionally click `MARK_STAFF_BAD_WINDOWS.cmd`, but it is not necessary for recognition. Exit reasonably soon after the incident: last 256 Play snapshots are retained. No continuous disk writes during gameplay.
4. Upload both `a3d-v0611-weapon-alice2000-windows.bin` **and** `.log` (2011/wine names differ), so they can be analysed alongside the user's already-supplied weapons archive. The binary is about 4.2 MiB maximum and may contain **copyrighted original game audio excerpts**. Share privately, not publicly.

## Fully automatic reference matching

The private 100-WAV archive is **not redistributed**. The included `weapon_reference_catalog_v0611.json` contains 100 filenames, rates, lengths, SHA-256 checksums and no PCM. The original ZIP can be used to automate matching after gameplay (the ZIP is NOT loaded by the game or DLL).

- Optional local installation on Debian 13: `sudo apt install python3-numpy python3-scipy` (using the distro's Python interpreter). On Windows, use Python + NumPy + SciPy if installed, or simply upload `.bin` and `.log` for external analysis.
- For Windows one-click analysis, make a private copy of your uploaded ZIP named `Weapons.zip` beside `ANALYSE_WEAPONS_WINDOWS.cmd` and run it.
- Or run: `python3 ANALYSE_WEAPONS_V0611.py a3d-v0611-weapon-alice2000-windows.bin --archive 'your weapon sounds.zip' --log a3d-v0611-weapon-alice2000-windows.log`.
- The script scans **all 100 original WAVs**, compares gain-invariant spectral characteristics, validates candidates with normalized cross-correlation, and emits a per-source CSV with recognized WAV name, confidence, source PCM RMS, A3D source gain/priority, and nearby global voice/limiter observations. **Unknown is a valid result.** Matches >=0.85 are higher confidence; 0.65–0.85 are candidates, not proof.

## What is / is not measured

Measured at source Play: raw mono 16-bit source PCM up to first 16,384 bytes (8,192 source frames), source ID, sample rate, API gain/priority, timestamps and byte length. Recorded in a 256-slot bounded RAM ring (~4.2 MiB); exported to a sidecar only during orderly mixer shutdown. The existing 4,096-event v0.6.10 lifecycle/limiter telemetry and the hard 1 MiB text log limit are retained. No game audio is written to disk while the game is running.

The offline matcher can identify raw source sounds despite substantial gain differences and source offsets, but may miss pitch-shifted, differently decoded, transformed, streaming or non-mono PCM; short samples and multiple near-identical weapon sounds can be ambiguous. Source snippets are **not** isolated post-HRTF / post-limiter signals. A nearby whole-mix limiter reading does **not** establish the staff's individual post-limiter level. A missing match is **not proof** of upstream Miles voice stealing or missing playback. No audio source priorities, filtering, gain or output buffer dimensions have been changed.

## Preserved defaults

Alice 2000: snapshot renderer, 6 x 256 = 32 ms. Alice 2011: legacy renderer, 6 x 256 = 32 ms, VorpalFix controls FPS by default, optional 144 FPS override and optional 4 x 512 fallback. Quake III Arena 1.17: snapshot renderer, 6 x 256 = 32 ms, 3 x 512 fallback retained. All three: common PE32 DLL, 48-tap HRTF, master gain 5.0, linked peak limiter, logging/capture OFF for standard launchers. Debian 13 and newer WoW64 Wine tests still need to be run by the user.

**Deployment status:** Build and offline tests do not substitute for actual Windows/Wine gameplay validation. The 32-bit bridge executables are retained from the working earlier release; retail games and copyrighted WAV data are not redistributed.
