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
if not defined A3D_HRTF_MODE set "A3D_HRTF_MODE=fast"
if not defined A3D_WAVEOUT_QUEUE_HEADERS set "A3D_WAVEOUT_QUEUE_HEADERS=6"
if not defined A3D_WAVEOUT_SUBBLOCKS set "A3D_WAVEOUT_SUBBLOCKS=1"
if not exist "hl.exe" (echo Missing original Half-Life & exit /b 2)
echo Aufake3D Half-Life 1.0.1.1; runtime gameplay integration NOT YET VERIFIED.
echo Optional historical compatibility launcher halflife-a3d-alpha.exe can be tested separately.
"hl.exe" +s_eax 0 +s_a3d 1 %*
exit /b %ERRORLEVEL%
