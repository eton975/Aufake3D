@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ================================================
echo Aufake3D v0.9.2 -- Alice 5-way audio reference
 echo Standalone data and analyzer packaging target
 echo NO Windows DLLs or game EXEs will be compiled.
echo ================================================
where py >nul 2>&1
if not errorlevel 1 (
    py -3 scripts\build_audio_reference.py %*
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Install Python 3.10 or later.
        pause
        exit /b 1
    )
    python scripts\build_audio_reference.py %*
)
set "RESULT=%ERRORLEVEL%"
if "%RESULT%"=="0" (
    echo DONE: dist\audio-reference\
) else (
    echo AUDIO REFERENCE BUILD FAILED. See Docs\AUDIO_REFERENCE_5WAY.md
)
pause
exit /b %RESULT%
