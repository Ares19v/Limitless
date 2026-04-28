@echo off
setlocal enabledelayedexpansion
title Limitless — Run
color 0A

echo.
echo  ██╗     ██╗███╗   ███╗██╗████████╗██╗     ███████╗███████╗███████╗
echo  ██║     ██║████╗ ████║██║╚══██╔══╝██║     ██╔════╝██╔════╝██╔════╝
echo  ██║     ██║██╔████╔██║██║   ██║   ██║     █████╗  ███████╗███████╗
echo  ██║     ██║██║╚██╔╝██║██║   ██║   ██║     ██╔══╝  ╚════██║╚════██║
echo  ███████╗██║██║ ╚═╝ ██║██║   ██║   ███████╗███████╗███████║███████║
echo  ╚══════╝╚═╝╚═╝     ╚═╝╚═╝   ╚═╝   ╚══════╝╚══════╝╚══════╝╚══════╝
echo.
echo  AI-Powered PDF Chat
echo  ===================
echo.

:: ── Prerequisite checks ────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Run INSTALL.bat first.
    pause & exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js not found. Run INSTALL.bat first.
    pause & exit /b 1
)

:: ── Check installation ─────────────────────────────────────────────────────
if not exist "backend\.venv" (
    echo  [ERROR] Python environment not found. Run INSTALL.bat first.
    pause & exit /b 1
)

if not exist "frontend\node_modules" (
    echo  [ERROR] Frontend packages not found. Run INSTALL.bat first.
    pause & exit /b 1
)

:: ── Check .env ─────────────────────────────────────────────────────────────
if not exist "backend\.env" (
    echo  [ERROR] backend\.env not found. Run INSTALL.bat first.
    pause & exit /b 1
)

:: ── Activate and set PYTHONPATH ────────────────────────────────────────────
call backend\.venv\Scripts\activate.bat
set PYTHONPATH=%~dp0backend

echo  [OK] Environment ready
echo.
echo  Starting services...
echo.
echo    Backend  ^>  http://localhost:8000
echo    API Docs ^>  http://localhost:8000/docs
echo    Frontend ^>  http://localhost:5173
echo.

:: ── Start backend ──────────────────────────────────────────────────────────
start "Limitless Backend" cmd /k "cd /d %~dp0backend && set PYTHONPATH=. && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: ── Wait for backend to be ready (poll /health up to 60s) ─────────────────
echo  [WAIT] Waiting for backend to start...
set READY=0
for /l %%i in (1,1,30) do (
    if !READY!==0 (
        timeout /t 2 /nobreak >nul
        curl -sf http://localhost:8000/health >nul 2>&1
        if not errorlevel 1 (
            set READY=1
            echo  [OK] Backend is ready
        )
    )
)

if !READY!==0 (
    echo  [WARN] Backend did not respond in 60s. Opening browser anyway...
)

:: ── Start frontend ─────────────────────────────────────────────────────────
start "Limitless Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: ── Wait for frontend to be ready ─────────────────────────────────────────
echo  [WAIT] Waiting for frontend to start...
timeout /t 5 /nobreak >nul

:: ── Open browser ───────────────────────────────────────────────────────────
start http://localhost:5173

echo.
echo  ┌──────────────────────────────────────────────────────────────┐
echo  │  Limitless is running!                                       │
echo  │                                                              │
echo  │  Frontend  → http://localhost:5173                          │
echo  │  API Docs  → http://localhost:8000/docs                     │
echo  │                                                              │
echo  │  Close the Backend and Frontend windows to stop.            │
echo  └──────────────────────────────────────────────────────────────┘
echo.
pause
