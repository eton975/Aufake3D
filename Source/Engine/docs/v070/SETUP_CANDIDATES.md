# Candidate setup â€” v0.7.0-alpha

Use a copy of a working Windows game installation. Close the game, back up existing A3D DLLs/manifests and copy the matching Binaries profile's contents beside its executable. Do not copy game files into this project's distributable source. No global COM registration or on-disk executable patching is required. Real game execution remains unverified.

## Half-Life retail

Target an original retail/WON-era build with an A3D backend. The local GOTY disc readme identifies version 1.0.1.1 and explicitly requires A3D 2.0, and the supplied installed hw.dll/sw.dll have now been inspected. See HALFLIFE_PROGRESS.md and HALFLIFE_BINARY_REPORT.json for the isolated startup diagnosis and limits. Do not assume a current Steam executable retains the same audio path.

Copy Binaries/HalfLife-Retail contents beside hl.exe. Keep all the original engine modules and valve data. Normal RUN_A3D_WINDOWS.cmd passes +s_eax 0 +s_a3d 1. Extra arguments follow these defaults, so caller commands can override them. For example, a mod can be selected with -game followed by its directory. A3D_LOG=0 is the default. The diagnostic launcher sets A3D_LOG=1 and writes a bounded a3d-v070-alpha.log in that directory.

The supplied installed hl.exe, hlds.exe, hw.dll and sw.dll are now inventoried. The user confirms unmodified startup works normally. No further upload of these files is needed. Wrapper audio/gameplay remains to be verified.

## Optional Half-Life 1.0.1.1 splash workaround

Start with RUN_A3D_WINDOWS.cmd. If this old build exits immediately in a context that cannot write the legacy Aureal HKLM SplashScreen setting, try RUN_A3D_SPLASH_FIX_WINDOWS.cmd in the copied test installation. The Wine equivalent is `bash RUN_A3D_SPLASH_FIX_WINE.sh`. These scripts explicitly select A3D_HALFLIFE_SPLASH_FIX=1; the option is off in normal launchers. This workaround is not automatically selected for other editions. Unknown signatures cause a clear refusal rather than a blind patch. No registry permissions or executable files are changed. Wine behavior of this workaround remains unverified.

For startup diagnostics, the existing diagnostic launcher enables both the wrapper log and a separate `a3d-launcher.log`. You may also set A3D_LAUNCH_LOG=1 for launcher-only diagnostics, or A3D_LAUNCH_LOG_PATH to a chosen file path. A3D_LAUNCH_LOG=0 explicitly disables that log even if A3D_LOG=1. The launcher log overwrites on each enabled run and is capped at 64 KiB; preserve a useful result before retrying. Logging defaults off. To combine diagnostics with the optional workaround in Windows, set A3D_LOG=1 before running the splash-fix script; in Bash use `A3D_LOG=1 bash RUN_A3D_SPLASH_FIX_WINE.sh`.

A child exit of zero, a visible window or a successful signature match is not an audio pass. Please check that A3D remains enabled and the log shows real source playback and listener/geometry activity before assessing positioning, voices, effects, music and room changes.

## Unreal / Unreal Gold with Galaxy

Copy Binaries/Unreal-Galaxy contents into the installed game's System directory, beside Unreal.exe and Galaxy.dll. Core.dll, Engine.dll and the rest of the game's dependencies/data must remain installed. Modern Unreal patches may select OpenAL/FMOD; those paths do not call this A3D backend.

Back up System/Unreal.ini before configuring audio. In the configuration used for this test, select:

```ini
[Engine.Engine]
AudioDevice=Galaxy.GalaxyAudioSubsystem

[Galaxy.GalaxyAudioSubsystem]
Use3dHardware=True
```

Keep your other video, controls, music and Galaxy settings unchanged initially. Close/restart Unreal after changing the audio backend. The launcher intentionally does not edit or rewrite your INI. You may copy the entire Unreal.ini to A3D-v070-alpha.ini, edit only that copy, and pass `ini=A3D-v070-alpha.ini` through the launcher to isolate the experiment. Confirm the actual backend in Unreal.log; an accepted configuration is not proof of wrapper use.

The inspected Unreal Gold Galaxy.dll has SHA-256 be3c7edb0fd044b0141bd0eef65882a0b1ce83a44c11b1d20d40a752c9d96c2f and embeds the A3D class/IA3d3/IA3d4/geometry/source/listener GUIDs. This is a promising candidate, not an allowlist or a gameplay certification. A read-only startup inspection found an IA3d4 initialization request with flags 0xc2 and left-handed coordinates. Music/DirectSound interoperation and complete source/geometry behavior remain to be tested.

## Wine

Use the game's working WINEPREFIX and a Wine installation capable of PE32 programs. Run `bash ./RUN_A3D_WINE.sh` from the profile installation directory. Both candidates use local native A3D overrides and preserve unrelated Wine overrides. Avoid conflicting entries for a3dapi/a3d. A3D_WINE_EXECUTABLE may specify the path to a Wine executable, not a command with arguments.

Linux filenames are case-sensitive: the candidate expects hl.exe or Unreal.exe, and Galaxy.dll/Core.dll/Engine.dll with those spellings for Unreal. Use the installed names carefully; do not overwrite original executables to resolve casing. Existing v0.6.12 platform prerequisites are retained under Source/release-docs/LINUX_WINE_SETUP.md. No real Wine test was available on this host.

## Inspect without starting a game

Python 3, no third-party packages needed:

```text
python tools/inspect_game_v070.py halflife "C:/path/to/Half-Life" --out half-life-report.json
python tools/inspect_game_v070.py unreal "C:/path/to/Unreal Gold" --out unreal-report.json
```

The Unreal tool accepts the game root or System directory. Reports contain filenames, hashes, import names and A3D clues, not raw executable contents. It refuses to overwrite an existing output file. Static markers alone cannot prove a reachable backend. Keep supplied game binaries private; they are never part of release ZIPs.

## What to report after a game test

Game/patch and engine DLL hashes, operating system/Wine version, launcher used, whether A3D stays enabled, wrapper log and Unreal.log/console error if applicable. A log that only shows class activation is insufficient: we need source creation/playback and spatial updates before claiming support. Compare music, voices, effects, directionality, room changes and shutdown behavior. No listening test is claimed by this snapshot.

Close the game and restore backed-up files/configuration to revert. The new profiles have no supported SOFTWARE_FALLBACK launcher: use the original game launcher/configuration for an unmodified baseline.
