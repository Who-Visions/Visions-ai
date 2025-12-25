@echo off
title VISIONS AETHER COMMAND
color 0B
echo ====================================================
echo   🛰️  VISIONS FLEET: AETHER COMMAND CENTER  ⚡
echo ====================================================
echo.
echo [SYS] Checking Aether-X Dependencies...
:: Using python -m pip to bypass potentially broken pip.exe wrappers
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARN] Auto-install failed. Attempting manual install...
    python -m pip install rich psutil requests
)
echo.
echo [SYS] Initializing local environment...
python fleet_dashboard.py
echo.
echo [SYS] Signal Lost. Session Terminated.
pause
