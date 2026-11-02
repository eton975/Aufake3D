@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
rem EXPERIMENTAL; never replace original Miles DLLs or patch game EXE.
if not exist "gta3.exe" (echo Missing original gta3.exe & exit /b 2)
if not exist "mss32.dll" (echo Missing original Miles mss32.dll & exit /b 2)
if not exist "a3d.dll" (echo Missing Aufake3D a3d.dll & exit /b 2)
if not exist "a3dapi.dll" (echo Missing Aufake3D a3dapi.dll & exit /b 2)
if not exist "mss\mssa3d2.m3d" echo WARNING: No original mss\mssa3d2.m3d; check game edition.
if not defined A3D_HRTF_MODE set "A3D_HRTF_MODE=reference"
if not defined A3D_MASTER_GAIN set "A3D_MASTER_GAIN=5.0"
if not defined A3D_WAVEOUT_QUEUE_HEADERS set "A3D_WAVEOUT_QUEUE_HEADERS=6"
if not defined A3D_WAVEOUT_SUBBLOCKS set "A3D_WAVEOUT_SUBBLOCKS=1"
echo Experimental GTA A3D probe: select real A3D 2.0 provider and verify actual API usage.
"gta3.exe" %*
exit /b %ERRORLEVEL%
