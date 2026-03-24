@echo off
title CRE Enterprise Suite
color 0A
echo ========================================
echo   CRE Enterprise Suite - Starting...
echo ========================================
echo.

cd /d C:\Users\alank\.qclaw\workspace\CREEnterprise\backend
start "CRE Backend" cmd /k "py -m uvicorn main:app --reload --port 8000"

timeout /t 3 /nobreak

cd /d C:\Users\alank\.qclaw\workspace\CREEnterprise\frontend
start "CRE Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo   Servers Starting...
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Open your browser to: http://localhost:5173
echo.
pause
