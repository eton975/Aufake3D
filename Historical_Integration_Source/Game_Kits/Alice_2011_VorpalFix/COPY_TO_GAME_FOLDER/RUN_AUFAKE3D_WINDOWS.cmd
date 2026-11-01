@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
rem v0.8.13 reliable WaveOut compatibility pump (proven poll4 baseline).
rem No diagnostic logging needed. Independent short one-shot edge guard.
set "A3D_LATENCY_TRACE=0"
set "A3D_WAVEOUT_POSITION_PROBE=1"
set "A3D_WAVEOUT_POSITION_INTERVAL=4"
set "A3D_WAVEOUT_SCHEDULE_TEST="
set "A3D_SHORT_SFX_DECLICK=1"

if not defined A3D_MASTER_GAIN set "A3D_MASTER_GAIN=5.0"
if not defined A3D_MILES_MODE set "A3D_MILES_MODE=activate"
set "A3D_MILES_ALIAS_UNKNOWN=1"
set "A3D_MILES_REQUIRE_CLI_A3D2=1"
set "A3D_MILES_DISPLAY_CANONICAL=1"
set "A3D_MILES_COM_PROBE=0"
set "A3D_WAVEOUT_QUEUE_HEADERS=3"
set "A3D_WAVEOUT_SUBBLOCKS=2"
set "A3D_RENDER_SNAPSHOT=0"
set "A3D_WAVEOUT_ADAPTIVE=0"
set "A3D_WAVEOUT_EVENT=1"
set "A3D_WAVEOUT_PRIORITY=1"
if not exist "alice.exe" (echo Missing alice.exe & exit /b 2)
if not exist "SndDrivers\a3d_mss_real.dll" (echo Missing original Miles copy & exit /b 2)
echo Aufake3D v0.8.13: Alice 2011 VorpalFix A3D2 name-fix profile.
echo Warning: default audio gain 5.0. Lower device volume before running.
"alice.exe" +set s_milesdriver a3d2 %*
exit /b %ERRORLEVEL%
