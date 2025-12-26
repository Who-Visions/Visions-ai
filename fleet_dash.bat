@echo off
title VISIONS AETHER COMMAND
color 0B
echo ====================================================
echo   🛰️  VISIONS FLEET: AETHER COMMAND CENTER  ⚡
echo ====================================================
echo.

:: Detect Python Version
echo [SYS] Detecting Python Environment...
python --version
if %errorlevel% neq 0 (
    echo [WARN] 'python' command not found. Trying 'py -3.12'...
    set PYTHON_CMD=py -3.12
) else (
    set PYTHON_CMD=python
)

%PYTHON_CMD% --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [CRITICAL] No Python executable found. Please install Python 3.12+.
    pause
    exit /b
)

echo [SYS] Using: %PYTHON_CMD%
echo.

echo [SYS] Checking Aether-X Dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARN] Auto-install failed. Attempting manual install...
    %PYTHON_CMD% -m pip install rich psutil requests
)

echo.
echo [SYS] Initializing Aether-X Dashboard...
%PYTHON_CMD% fleet_dashboard.py

echo.
echo [SYS] Signal Lost. Session Terminated.
pause
