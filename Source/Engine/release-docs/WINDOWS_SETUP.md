# Fresh Windows setup — A3D v0.6.12

## 1. Prepare the game

Install your own Windows game and run it once normally. Keep a backup or use a copy of its installed folder, preferably in a user-writable location. Close the game before copying files. Back up any existing a3dapi.dll, a3d.dll, adjacent executable manifest and A3D launchers so you can restore your previous setup.

Choose precisely one profile:

* Alice2000: the original American McGee's Alice, with alice.exe and its original matching Miles components and game data.
* Alice2011-VorpalFix: the 2011 rerelease of the original Alice, with the supported VorpalFix 4.2.1 layout. This is not Alice: Madness Returns itself. Keep VorpalFix's own winmm.dll beside alice.exe and SndDrivers/mssa3d2.m3d below that directory. Install and configure VorpalFix separately before adding A3D.
* QuakeIII-117: Quake III Arena Windows version 1.17, with its matching baseq3 data. Do not combine a later executable or later patch PK3 set with this profile. Use your genuine 1.17 installation, including the appropriate pak0–pak3 files.

The launch bridges recognise specific instruction layouts and reject mismatches. Their checks are not a general game-version detector or whole-file authentication. Do not bypass a selector-signature error; restore the matching executable from your installation.

## 2. Copy the profile

Extract the ZIP first. Open Binaries and the chosen game folder. Copy all files from inside that folder into the directory containing alice.exe or quake3.exe. Do not copy the outer Alice2000 folder as a nested subdirectory. Accept replacement only for the A3D files you backed up. Never replace the original game executable, Miles provider or VorpalFix winmm.dll with a file from another title.

The two A3D DLLs, game activation bridge and executable manifest must remain together beside the original executable. No system DLL directory installation or global COM registration is required. The bridge starts only the adjacent game and changes a checked selector in that new process's memory; it does not patch the executable on disk.

## 3. Launch

Double-click RUN_A3D_WINDOWS.cmd. In Alice, the launcher requests the Miles a3d2 provider. Quake III receives s_enable_a3d 1, s_mixahead 0.35 and s_mixPreStep 0.05. Use headphones/stereo output when evaluating the binaural renderer. Avoid stacking extra system spatial-audio processing while comparing directionality.

For Alice's previous mix, close the game and use RUN_A3D_ORIGINAL_MIX_WINDOWS.cmd. Return to the normal launcher to restore clarity. Alice 2011 additionally provides RUN_A3D_144FPS_WINDOWS.cmd; use the normal launcher to return FPS control to VorpalFix. A persisted game configuration may retain a console FPS change: inspect your VorpalFix/game configuration if the cap remains after a comparison.

The *_FALLBACK launchers change buffering only: Alice 2011 offers 4 × 512 frames, Quake III 3 × 512. They are troubleshooting alternatives, not release defaults. Alice 2000's 6x256 launcher is an explicit alias for its normal queue. The ORIGINAL_MIX fallback changes the mixer, not buffering.

## 4. Troubleshoot or remove

Run a launcher from Command Prompt to keep an error visible. A missing executable means the files are in the wrong folder. A signature mismatch requires the supported game build. Missing Miles/VorpalFix components require restoring the game's own files. Do not download random system DLL replacements.

For a short diagnostic session, run RUN_A3D_DIAGNOSTIC_WINDOWS.cmd, exit normally and inspect its log. Do not use WEAPON_DIAGNOSTIC or STAFF_DIAGNOSTIC unless you deliberately want their extra capture files. Normal launchers produce no wrapper logs unless you set an override. Existing old logs are not automatically deleted.

To remove A3D, close the game, remove the files you copied and restore every backed-up file. Keep original winmm.dll, SndDrivers, game data and the game executable. Launch the game normally again.
