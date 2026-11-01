@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
echo Aufake3D v0.8.13 - install from the same ready-to-copy Game_Kits as the manual
echo NOTE: Only Alice 2011 plus VorpalFix has the v0.8.9 name-fix tested on Windows.
echo Choose profile: alice2011 / alice2000 / quake3 / halflife
set /p "AU_PROFILE=Profile: "
set /p "AU_GAME=Full path to ORIGINAL game EXE: "
if not defined AU_PROFILE exit /b 2
if not defined AU_GAME exit /b 2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Tools\Install-Windows.ps1" -Profile "%AU_PROFILE%" -GameExe "%AU_GAME%"
set "STATUS=%ERRORLEVEL%"
echo.
if %STATUS% NEQ 0 echo Installation was NOT completed. Inspect the message above.
pause
exit /b %STATUS%
