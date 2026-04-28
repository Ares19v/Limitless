@echo off
setlocal enabledelayedexpansion
title Limitless — Install
color 0A

echo.
echo  ██╗     ██╗███╗   ███╗██╗████████╗██╗     ███████╗███████╗███████╗
echo  ██║     ██║████╗ ████║██║╚══██╔══╝██║     ██╔════╝██╔════╝██╔════╝
echo  ██║     ██║██╔████╔██║██║   ██║   ██║     █████╗  ███████╗███████╗
echo  ██║     ██║██║╚██╔╝██║██║   ██║   ██║     ██╔══╝  ╚════██║╚════██║
echo  ███████╗██║██║ ╚═╝ ██║██║   ██║   ███████╗███████╗███████║███████║
echo  ╚══════╝╚═╝╚═╝     ╚═╝╚═╝   ╚═╝   ╚══════╝╚══════╝╚══════╝╚══════╝
echo.
echo  INSTALL — First-Time Setup
echo  ===========================
echo.

:: ── Check prerequisites ────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install Python 3.11+ from https://python.org
    pause & exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK] Python %PY_VER% found

node --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js not found. Install Node 20+ from https://nodejs.org
    pause & exit /b 1
)
for /f %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo  [OK] Node.js %NODE_VER% found
echo.

:: ── Backend .env ────────────────────────────────────────────────────────────
if not exist "backend\.env" (
    echo  [SETUP] Creating backend\.env from example...
    copy "backend\.env.example" "backend\.env" >nul
    echo.
    echo  ┌─────────────────────────────────────────────────────────┐
    echo  │  ACTION REQUIRED — Fill in your API keys                │
    echo  │                                                         │
    echo  │  1. GROQ_API_KEY     → https://console.groq.com        │
    echo  │  2. PINECONE_API_KEY → https://www.pinecone.io         │
    echo  │     (Create index: name=documind, dims=384, cosine)    │
    echo  └─────────────────────────────────────────────────────────┘
    echo.
    echo  Opening backend\.env in Notepad — save and close when done.
    notepad "backend\.env"
) else (
    echo  [OK] backend\.env already exists — skipping
)

:: ── Frontend .env ──────────────────────────────────────────────────────────
if not exist "frontend\.env" (
    echo  [SETUP] Creating frontend\.env from example...
    copy "frontend\.env.example" "frontend\.env" >nul
    echo  [OK] frontend\.env created
) else (
    echo  [OK] frontend\.env already exists — skipping
)

:: ── Python virtual environment ─────────────────────────────────────────────
if not exist "backend\.venv" (
    echo.
    echo  [SETUP] Creating Python virtual environment...
    python -m venv backend\.venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause & exit /b 1
    )
    echo  [OK] Virtual environment created
) else (
    echo  [OK] Virtual environment already exists
)

:: ── Install backend Python packages (always run to ensure all deps present) ──
echo.
echo  [SETUP] Installing backend dependencies (this may take a few minutes)...
call backend\.venv\Scripts\activate.bat

echo  [SETUP] Upgrading pip...
python -m pip install --upgrade pip -q

echo  [SETUP] Installing CPU-only torch first...
pip install -q torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu

echo  [SETUP] Installing remaining backend dependencies...
pip install -q -r backend\requirements.txt

echo  [OK] Backend dependencies installed

:: ── Install frontend npm packages ──────────────────────────────────────────
echo.
echo  [SETUP] Installing frontend dependencies...
cd frontend
npm install --silent
if errorlevel 1 (
    echo  [ERROR] npm install failed.
    cd ..
    pause & exit /b 1
)
cd ..
echo  [OK] Frontend dependencies installed

:: ── Done ───────────────────────────────────────────────────────────────────
echo.
echo  ┌─────────────────────────────────────────────────────────────┐
echo  │  Installation complete!                                     │
echo  │                                                             │
echo  │  Run the project:  Run_Project.bat                         │
echo  │  Remove install:   UNINSTALL.bat                           │
echo  └─────────────────────────────────────────────────────────────┘
echo.
pause
