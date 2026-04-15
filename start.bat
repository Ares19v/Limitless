@echo off
title DocuMind Launcher
color 0A

echo.
echo  ██████╗  ██████╗  ██████╗██╗   ██╗███╗   ███╗██╗███╗   ██╗██████╗
echo  ██╔══██╗██╔═══██╗██╔════╝██║   ██║████╗ ████║██║████╗  ██║██╔══██╗
echo  ██║  ██║██║   ██║██║     ██║   ██║██╔████╔██║██║██╔██╗ ██║██║  ██║
echo  ██║  ██║██║   ██║██║     ██║   ██║██║╚██╔╝██║██║██║╚██╗██║██║  ██║
echo  ██████╔╝╚██████╔╝╚██████╗╚██████╔╝██║ ╚═╝ ██║██║██║ ╚████║██████╔╝
echo  ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝
echo.
echo  AI-Powered PDF Chat  --  Production Ready
echo  ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

:: Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js not found. Please install Node 20+ from nodejs.org
    pause
    exit /b 1
)

:: Setup backend .env
if not exist "backend\.env" (
    echo  [SETUP] Creating backend .env from example...
    copy "backend\.env.example" "backend\.env" >nul
    echo  [!] IMPORTANT: Edit backend\.env and add your Pinecone API key.
    echo  [!] GROQ_API_KEY is already pre-filled.
    echo  [!] Get your Pinecone key at: https://www.pinecone.io
    echo.
    notepad backend\.env
)

:: Setup frontend .env
if not exist "frontend\.env" (
    echo  [SETUP] Creating frontend .env from example...
    copy "frontend\.env.example" "frontend\.env" >nul
)

:: Install backend dependencies
if not exist "backend\.venv" (
    echo  [SETUP] Creating Python virtual environment...
    python -m venv backend\.venv
    echo  [SETUP] Installing backend dependencies...
    call backend\.venv\Scripts\activate.bat
    pip install -q -r backend\requirements.txt
) else (
    call backend\.venv\Scripts\activate.bat
)

:: Install frontend dependencies
if not exist "frontend\node_modules" (
    echo  [SETUP] Installing frontend dependencies...
    cd frontend
    npm install --silent
    cd ..
)

echo.
echo  Starting services...
echo  Backend  -> http://localhost:8000  (API Docs: http://localhost:8000/docs)
echo  Frontend -> http://localhost:5173
echo.

:: Start backend in new window
start "DocuMind Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Give backend 2 seconds to start
timeout /t 2 /nobreak >nul

:: Start frontend in new window
start "DocuMind Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Open browser after 4 seconds
timeout /t 4 /nobreak >nul
start http://localhost:5173

echo  [OK] DocuMind is running!
echo  Close the backend and frontend windows to stop.
echo.
pause
