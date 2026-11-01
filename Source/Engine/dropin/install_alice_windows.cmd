@echo off
if "%~1"=="" (
 echo Drag Alice.exe onto this .cmd file, or pass its full path as the first argument.
 exit /b 2
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" -Game "%~1" -Kind alice -PatchAlice
if errorlevel 1 (echo Installation failed; original Alice.exe was never modified. & exit /b 1)
echo The separate Alice-A3D2.exe is the test executable. It may still fall back to non-A3D audio.
