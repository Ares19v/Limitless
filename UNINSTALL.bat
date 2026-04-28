@echo off
setlocal enabledelayedexpansion
title Limitless — Uninstall
color 0C

echo.
echo  ██╗     ██╗███╗   ███╗██╗████████╗██╗     ███████╗███████╗███████╗
echo  ██║     ██║████╗ ████║██║╚══██╔══╝██║     ██╔════╝██╔════╝██╔════╝
echo  ██║     ██║██╔████╔██║██║   ██║   ██║     █████╗  ███████╗███████╗
echo  ██║     ██║██║╚██╔╝██║██║   ██║   ██║     ██╔══╝  ╚════██║╚════██║
echo  ███████╗██║██║ ╚═╝ ██║██║   ██║   ███████╗███████╗███████║███████║
echo  ╚══════╝╚═╝╚═╝     ╚═╝╚═╝   ╚═╝   ╚══════╝╚══════╝╚══════╝╚══════╝
echo.
echo  UNINSTALL — Remove local installation
echo  =======================================
echo.
echo  This will delete:
echo    - backend\.venv          (Python virtual environment)
echo    - frontend\node_modules  (npm packages)
echo    - backend\uploads\       (uploaded PDF files)
echo    - backend\data\          (SQLite database)
echo    - backend\bm25_indexes\  (BM25 keyword indexes)
echo.
echo  Your .env files and source code will NOT be deleted.
echo.

set /p CONFIRM="  Type YES to proceed: "
if /i not "!CONFIRM!"=="YES" (
    echo.
    echo  [CANCELLED] Nothing was deleted.
    pause
    exit /b 0
)

echo.
echo  [REMOVING] Deleting Python virtual environment...
if exist "backend\.venv" (
    rmdir /s /q "backend\.venv"
    echo  [OK] backend\.venv removed
) else (
    echo  [SKIP] backend\.venv not found
)

echo  [REMOVING] Deleting node_modules...
if exist "frontend\node_modules" (
    rmdir /s /q "frontend\node_modules"
    echo  [OK] frontend\node_modules removed
) else (
    echo  [SKIP] frontend\node_modules not found
)

echo  [REMOVING] Deleting uploaded PDFs...
if exist "backend\uploads" (
    rmdir /s /q "backend\uploads"
    echo  [OK] backend\uploads removed
) else (
    echo  [SKIP] backend\uploads not found
)

echo  [REMOVING] Deleting SQLite database...
if exist "backend\data" (
    rmdir /s /q "backend\data"
    echo  [OK] backend\data removed
) else (
    echo  [SKIP] backend\data not found
)

echo  [REMOVING] Deleting BM25 indexes...
if exist "backend\bm25_indexes" (
    rmdir /s /q "backend\bm25_indexes"
    echo  [OK] backend\bm25_indexes removed
) else (
    echo  [SKIP] backend\bm25_indexes not found
)

echo.
echo  ┌──────────────────────────────────────────────────────────┐
echo  │  Uninstall complete.                                     │
echo  │  Run INSTALL.bat to set up again from scratch.          │
echo  └──────────────────────────────────────────────────────────┘
echo.
pause
