@echo off
title Clinical Coding Dashboard (Vite Frontend)
echo ========================================================
echo Starting Medical Coding Review Dashboard Frontend...
echo ========================================================
set PATH=C:\Program Files\nodejs;%PATH%
cd /d "%~dp0\clinical-coding-project\module4_dashboard\frontend"
call npm run dev -- --host 0.0.0.0 --port 5173
pause
