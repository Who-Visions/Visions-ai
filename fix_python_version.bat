@echo off
cd /d "%~dp0"
echo [VISIONS AI] DETECTED: Python 3.14 (Alpha) in .venv
echo [VISIONS AI] PROBLEM: Google/LangChain libraries do not support 3.14 yet.
echo [VISIONS AI] FIXING: Recreating .venv with Python 3.13 (Stable)...

if exist .venv (
    echo [VISIONS AI] Removing old .venv...
    rmdir /s /q .venv
)

echo [VISIONS AI] Creating new .venv with Python 3.13...
py -3.13 -m venv .venv

echo [VISIONS AI] Activating...
call .venv\Scripts\activate.bat

echo [VISIONS AI] Installing requirements...
pip install -r requirements.txt

echo [VISIONS AI] Done. You can now use run_indexer.bat
pause
