@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if not exist "WolfSP.exe" (echo Original WolfSP.exe missing & exit /b 2)
rem Experimental compatibility probe. Does NOT claim A3D API integration is confirmed.
if not defined A3D_HRTF_MODE set "A3D_HRTF_MODE=reference"
if not defined A3D_MASTER_GAIN set "A3D_MASTER_GAIN=5.0"
if not defined A3D_WAVEOUT_QUEUE_HEADERS set "A3D_WAVEOUT_QUEUE_HEADERS=6"
if not defined A3D_WAVEOUT_SUBBLOCKS set "A3D_WAVEOUT_SUBBLOCKS=1"
echo Aufake3D 0.9.0 experimental Return to Castle Wolfenstein (retail) probe. A3D activity must be verified in logs.
"WolfSP.exe" %*
exit /b %ERRORLEVEL%
