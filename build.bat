@echo off
REM Thin wrapper: keep the PyInstaller flags in build.py, where they can be
REM read and diffed. This file used to carry a second, divergent copy of them.
cd /d "%~dp0"

py build.py
if errorlevel 1 (
    echo BUILD FAILED
    pause
    exit /b 1
)

pause
