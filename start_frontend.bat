@echo off
set PATH=C:\Program Files\nodejs;%PATH%
echo Starting Book2Podcast Frontend...
cd /d "%~dp0frontend"
npm run dev
pause
