@echo off
if "%~1"=="" (
 echo Drag an older quake3.exe onto this .cmd file, or pass its full path as the first argument.
 exit /b 2
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" -Game "%~1" -Kind quake3
if errorlevel 1 (echo Installation failed; original executable was not modified. & exit /b 1)
echo The legacy bridge currently supplies DirectSound, not reference Aureal Wavetracing.
