@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ==============================================
echo Aufake3D -- Windows 10/11 local x86 build
 echo ==============================================
where py >nul 2>&1
if not errorlevel 1 (
    py -3 scripts\build.py %*
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python 3.10+ is not installed or not on PATH.
        echo Read Docs\ONE_CLICK_BUILD.md
        pause
        exit /b 1
    )
    python scripts\build.py %*
)
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
    echo.
    echo BUILD FAILED. See Docs\ONE_CLICK_BUILD.md.
) else (
    echo.
    echo Build complete. Check dist\ for DLLs, helpers and runtime ZIP.
)
pause
exit /b %RESULT%
