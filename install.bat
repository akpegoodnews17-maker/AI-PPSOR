@echo off
setlocal

REM Always run from the project root
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "REQ_FILE=requirements.txt"

REM Find a Python launcher
where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py"
) else (
    where python >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
    ) else (
        echo Python was not found on this system.
        echo Please install Python 3.10+ and try again.
        pause
        exit /b 1
    )
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment in %VENV_DIR% ...
    "%PYTHON_CMD%" -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create the virtual environment.
        pause
        exit /b 1
    )
)

set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

echo Installing dependencies from %REQ_FILE% ...
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 (
    echo Dependency installation failed.
    echo Please check the error output above and fix the issue before retrying.
    pause
    exit /b 1
)

echo.
echo All dependencies are installed successfully.
echo Starting the app...
call start.bat
exit /b %ERRORLEVEL%
