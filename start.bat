@echo off
setlocal

REM Always run from the project root (location of this .bat file)
cd /d "%~dp0"

REM Prefer local virtual environment if it exists
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

REM Validate Python is available
"%PYTHON_EXE%" --version >nul 2>nul
if errorlevel 1 (
    echo Python was not found.
    echo Install Python or create .venv in this project, then try again.
    pause
    exit /b 1
)

echo Starting AI-Powered Personal Stylist app...
echo URL: http://127.0.0.1:5000
echo Press Ctrl+C to stop.
echo.

"%PYTHON_EXE%" run.py
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo App exited with code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
