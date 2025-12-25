@echo off
cd /d "%~dp0"

if exist .venv\Scripts\activate.bat (
    echo [VISIONS AI] Activating .venv...
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    echo [VISIONS AI] Activating venv...
    call venv\Scripts\activate.bat
)

echo [VISIONS AI] Checking Dependencies...
pip install -q -r requirements.txt
echo [VISIONS AI] Starting Knowledge Indexer...
python build_index.py
pause
