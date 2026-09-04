@echo off
echo ========================================
echo Starting EduClassify Application
echo ========================================
echo.

echo [1/2] Starting Backend Server...
cd /d "%~dp0"
start "EduClassify Backend" cmd /k "python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 --timeout-keep-alive 300 --h11-max-incomplete-event-size 5242880"
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Server...
cd frontend
start "EduClassify Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo Both servers are starting...
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo ========================================
echo.
echo Press any key to close this window...
pause >nul
