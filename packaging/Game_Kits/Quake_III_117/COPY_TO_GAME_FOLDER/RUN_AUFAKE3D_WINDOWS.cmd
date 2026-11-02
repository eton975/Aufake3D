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
if not exist "quake3.exe" (echo Missing original Quake III & exit /b 2)
if not defined A3D_GEOMETRY_TRACE set "A3D_GEOMETRY_TRACE=1"
if not defined A3D_GEOMETRY_RETRACE_BLOCKS set "A3D_GEOMETRY_RETRACE_BLOCKS=4"
if not defined A3D_REVERB_WET set "A3D_REVERB_WET=0.14"
if not defined A3D_HRTF_TAPS set "A3D_HRTF_TAPS=56"
if not defined A3D_VOICE_LIMIT set "A3D_VOICE_LIMIT=128"
if not defined A3D_WAVEOUT_QUEUE_HEADERS set "A3D_WAVEOUT_QUEUE_HEADERS=6"
if not defined A3D_WAVEOUT_SUBBLOCKS set "A3D_WAVEOUT_SUBBLOCKS=1"
echo Aufake3D Quake III 1.17: select A3D using the in-game s_enable_a3d command.
"quake3.exe" +set s_mixahead 0.35 +set s_mixPreStep 0.05 %*
exit /b %ERRORLEVEL%
