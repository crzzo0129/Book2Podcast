@echo off
echo Starting Book2Podcast Backend...
cd /d "%~dp0backend"
python -m uvicorn main:app --host 0.0.0.0 --port 8000
pause
