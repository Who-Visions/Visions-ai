@echo off
TITLE Visions AI - Quick Test
wsl -e bash -c "cd '/mnt/c/Users/super/Watchtower/HQ_WhoArt/Visions-ai' && source venv/bin/activate && python test_components.py"
pause
