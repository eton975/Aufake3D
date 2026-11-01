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
if not exist "alice-a3d-bridge.exe" (echo Missing Alice classic compatibility bridge & exit /b 2)
if not exist "alice.exe" (echo Missing original Alice & exit /b 2)
echo Aufake3D classic Alice; bridge may modify checked selector in CHILD RAM only.
"alice-a3d-bridge.exe" +set s_milesdriver a3d2 %*
exit /b %ERRORLEVEL%
