@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo Aufake3D Descent 3 EXPERIMENTAL source adapter and contract probe
where py >nul 2>&1
if not errorlevel 1 (
    py -3 scripts\build_descent3_experimental.py %*
) else (
    python scripts\build_descent3_experimental.py %*
)
exit /b %ERRORLEVEL%
