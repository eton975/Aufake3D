@echo off
setlocal EnableExtensions DisableDelayedExpansion
echo Aufake3D v0.8.18 - opt-in Miles trace for an ALREADY INSTALLED Alice 2011 profile.
set /p "AU_GAME=Full path to installed Alice 2011 alice.exe: "
if not defined AU_GAME exit /b 2
for %%I in ("%AU_GAME%") do set "AU_DIR=%%~dpI"
if not exist "%AU_DIR%alice.exe" (echo alice.exe not found & exit /b 2)
if not exist "%AU_DIR%RUN_AUFAKE3D_WINDOWS.cmd" (echo Aufake3D game launcher not found & exit /b 2)
cd /d "%AU_DIR%"
set "A3D_MILES_TRACE=1"
set "A3D_PROBE_LOG=%AU_DIR%a3d-aufake3d-renderer-test.log"
echo This session will write diagnostic logs in the installed game directory.
call "%AU_DIR%RUN_AUFAKE3D_WINDOWS.cmd"
set "RC=%ERRORLEVEL%"
echo.
echo After the session, check "%AU_DIR%SndDrivers\a3d-v074f-miles.log"
pause
exit /b %RC%
