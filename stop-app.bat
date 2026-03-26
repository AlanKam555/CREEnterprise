@echo off
REM CRE Enterprise - Stop All Servers
REM This script stops all running backend and frontend servers

echo ==========================================
echo   CRE Enterprise - Stopping Servers
echo ==========================================
echo.

echo Stopping Python backend servers...
taskkill /f /im python.exe 2>nul
if errorlevel 1 (
    echo   No Python processes found
) else (
    echo   Python processes stopped
)

echo Stopping Node.js frontend servers...
taskkill /f /im node.exe 2>nul
if errorlevel 1 (
    echo   No Node processes found
) else (
    echo   Node processes stopped
)

echo.
echo ==========================================
echo   All servers stopped
echo ==========================================
pause
