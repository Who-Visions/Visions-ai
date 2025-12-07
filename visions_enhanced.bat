@echo off
TITLE Visions AI - Memory + Smart Routing Edition
COLOR 0A
CLS

ECHO ========================================================
ECHO   🧠 VISIONS AI - SMART ROUTING + MEMORY 🧠
ECHO ========================================================
ECHO   Cascade: Flash-Lite → Flash → Pro → Gemini 3 Pro
ECHO   Routing: Intelligent query triage
ECHO   Primary: Vertex AI (Global)
ECHO   Fallback: AI Studio API
ECHO   Memory: 100 entries + Async SQL
ECHO   Typo Correction: ENABLED
ECHO   Contextual Understanding: ENABLED
ECHO ========================================================
ECHO.
ECHO 💾 Launching Smart Memory Interface...
ECHO.

:: Launch WSL, navigate to project, activate venv, run enhanced CLI
wsl -e bash -c "cd '/mnt/c/Users/super/Watchtower/HQ_WhoArt/Visions-ai' && source venv/bin/activate && python cli_enhanced.py; echo 'Session Terminated. Press Enter to close.'; read"
