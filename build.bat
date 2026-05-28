@echo off
cd /d "%~dp0"
echo === Building AudioCenter portable EXE (onefile) ===
echo.

py -m PyInstaller --onefile --windowed --name AudioCenter --add-data "AudioHelper.exe;." --add-data "icon.ico;." --hidden-import PIL._tkinter_finder --hidden-import themecolors --hidden-import iconutil --hidden-import audio --hidden-import tabs.mixer --hidden-import tabs.playback --hidden-import tabs.recording --hidden-import tabs.profiles --hidden-import tabs.studio --exclude-module numpy --exclude-module numpy._core --exclude-module numpy.libs --exclude-module numpy.random --exclude-module numpy.fft --exclude-module numpy.linalg --exclude-module numpy.polynomial main.py

if errorlevel 1 (
    echo BUILD FAILED
    pause
    exit /b 1
)

echo.
echo === Build complete ===
dir "%~dp0dist\AudioCenter.exe"
pause
