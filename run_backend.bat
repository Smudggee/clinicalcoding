@echo off
title Clinical Coding Backend (FastAPI)
echo ========================================================
echo Starting Clinical Coding Neuro-Symbolic Backend API...
echo ========================================================
cd /d "%~dp0\clinical-coding-project"
set "PYTHON_EXE=%~dp0clinical-coding-project\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
"%PYTHON_EXE%" -m uvicorn module4_dashboard.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
pause
