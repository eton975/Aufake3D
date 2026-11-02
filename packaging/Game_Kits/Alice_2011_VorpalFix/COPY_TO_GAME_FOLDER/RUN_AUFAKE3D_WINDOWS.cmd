@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
rem WaveOut compatibility pump: v0.8.12-v0.8.14 proven poll4 baseline, unchanged in v0.8.16.
rem No diagnostic logging needed. Independent short one-shot edge guard.
set "A3D_LATENCY_TRACE=0"
set "A3D_WAVEOUT_POSITION_PROBE=1"
set "A3D_WAVEOUT_POSITION_INTERVAL=4"
set "A3D_WAVEOUT_SCHEDULE_TEST="
set "A3D_SHORT_SFX_DECLICK=1"

if not defined A3D_MASTER_GAIN set "A3D_MASTER_GAIN=5.0"
rem Shared AU8830 56-tap engine: same reference/fast/legacy modes as other games.
if not defined A3D_HRTF_MODE set "A3D_HRTF_MODE=reference"
if not defined A3D_MILES_MODE set "A3D_MILES_MODE=activate"
set "A3D_MILES_ALIAS_UNKNOWN=0"
rem The RAM selector recognises a3d2 directly; never advertise the unsafe unknown alias.
set "A3D_MILES_REQUIRE_CLI_A3D2=1"
set "A3D_MILES_DISPLAY_CANONICAL=1"
set "A3D_MILES_COM_PROBE=0"
set "A3D_WAVEOUT_QUEUE_HEADERS=6"
set "A3D_WAVEOUT_SUBBLOCKS=1"
set "A3D_RENDER_SNAPSHOT=0"
set "A3D_WAVEOUT_ADAPTIVE=0"
set "A3D_WAVEOUT_EVENT=1"
set "A3D_WAVEOUT_PRIORITY=1"
if not exist "alice.exe" (echo Missing alice.exe & exit /b 2)
if not exist "alice-a3d2011-native.exe" (echo Missing RAM selector bridge & exit /b 2)
if not exist "a3d-miles-local.manifest" (echo Missing local COM manifest & exit /b 2)
if exist "alice.exe.manifest" (echo Existing alice.exe.manifest: refusing to overwrite & exit /b 5)
if not exist "SndDrivers\a3d_mss_real.dll" (echo Missing original Miles copy & exit /b 2)
rem One-time saved default: never supply +set s_milesdriver, which can reselect A3D2
rem during a Miles/Dolby change. After first run, menu choices are untouched.
if not exist "AUFAKE3D_A3D2_INITIAL_DEFAULT_DONE.txt" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0AUFAKE3D_SET_INITIAL_A3D2.ps1" -Game Alice2011 -GameDir "%CD%"
  if errorlevel 1 echo NOTE: Could not seed initial A3D2 setting. Select A3D2 once from the game menu.
)
echo Aufake3D v0.9.0 unified engine candidate: Alice 2011 VorpalFix selector profile.
echo Warning: default audio gain 5.0. Lower device volume before running.
rem Use the signature-checked, child-RAM-only selector bridge. Do not alter alice.exe on disk.
rem The temporary manifest is required to activate the app-local A3D COM server.
copy /Y "a3d-miles-local.manifest" "alice.exe.manifest" >nul
if errorlevel 1 (echo Failed to create temporary alice.exe.manifest & exit /b 5)
"alice-a3d2011-native.exe" %*
set "A3D_EXIT_STATUS=%ERRORLEVEL%"
del /Q "alice.exe.manifest" >nul 2>nul
if exist "alice.exe.manifest" echo WARNING: Failed to remove temporary alice.exe.manifest; remove manually.
exit /b %A3D_EXIT_STATUS%
