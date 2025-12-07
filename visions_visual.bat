@echo off
TITLE Visions AI - Ultra Visual + Smart Routing
COLOR 0A
CLS

ECHO ========================================================
ECHO   🎨 VISIONS AI - ULTRA VISUAL + SMART ROUTING 🎨
ECHO ========================================================
ECHO   Cascade: Flash-Lite → Flash → Pro → Gemini 3 Pro
ECHO   Routing: Intelligent query triage
ECHO   Primary: Vertex AI (Global)
ECHO   Fallback: AI Studio API ✅
ECHO   Memory: 100 entries (Short-term) + SQL (Long-term)
ECHO   Typo Correction: ENABLED
ECHO   Aspect Ratios: 1:1, 16:9, 9:16, 4:3, 3:4, 21:9
ECHO ========================================================
ECHO.
ECHO 🚀 Launching Ultra-Visual Interface...
ECHO.

:: Launch WSL, navigate to project, activate venv, run visual CLI
wsl -e bash -c "cd '/mnt/c/Users/super/Watchtower/HQ_WhoArt/Visions-ai' && source venv/bin/activate && python cli_visual.py; echo '✨ Session Terminated. Press Enter to close.'; read"
