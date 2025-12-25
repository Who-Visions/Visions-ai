@echo off
cd /d "%~dp0"
title VISIONS AI - DIRECTOR INTERFACE

if exist .venv\Scripts\activate.bat (
    echo [VISIONS AI] Activating .venv...
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    echo [VISIONS AI] Activating venv...
    call venv\Scripts\activate.bat
)

echo [VISIONS AI] Launching Director Interface...
python cli_enhanced.py
pause
