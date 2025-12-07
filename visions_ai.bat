@echo off
TITLE Visions AI - Smart Routing Edition
COLOR 0A
CLS

ECHO ========================================================
ECHO   VISIONS AI - SMART ROUTING EDITION
ECHO ========================================================
ECHO   Models: Flash-Lite + Flash + Pro + Gemini 3 Pro
ECHO   Routing: Intelligent query triage
ECHO   Primary: Vertex AI (Global Endpoint)
ECHO   Fallback: Google AI Studio API
ECHO   Memory: 100 entries per session
ECHO ========================================================
ECHO.
ECHO Launching Neural Interface...
ECHO.

:: Launch WSL, navigate to project, activate venv, run CLI
wsl -e bash -c "cd '/mnt/c/Users/super/Watchtower/HQ_WhoArt/Visions-ai' && source venv/bin/activate && python cli.py; echo 'Session Terminated. Press Enter to close.'; read"