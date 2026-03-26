@echo off
REM CRE Enterprise - Quick Start Script for Windows
REM This script starts both backend and frontend servers

echo ==========================================
echo   CRE Enterprise Suite - Quick Start
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

echo [OK] Python and Node.js are installed
echo.

REM Start Backend
echo [1/2] Starting Backend Server...
cd backend
start "CRE Backend" cmd /k "python -m uvicorn main:app --reload --port 8000"
cd ..
echo       Backend running at: http://localhost:8000
echo       API Documentation: http://localhost:8000/docs
echo.

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start Frontend
echo [2/2] Starting Frontend Server...
cd frontend
start "CRE Frontend" cmd /k "npm run dev"
cd ..
echo       Frontend running at: http://localhost:5173
echo.

echo ==========================================
echo   Both servers are starting!
echo ==========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press any key to open the application in your browser...
pause >nul

start http://localhost:5173

echo.
echo The application should open in your browser shortly.
echo Close this window when done.
pause
