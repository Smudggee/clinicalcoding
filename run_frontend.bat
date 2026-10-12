@echo off
title Clinical Coding Dashboard (Vite Frontend)
echo ========================================================
echo Starting Medical Coding Review Dashboard Frontend...
echo ========================================================
set PATH=C:\Program Files\nodejs;%PATH%
cd /d "%~dp0\Design Medical Coding Dashboard"
call npm run dev -- --host 0.0.0.0 --port 5173
pause
