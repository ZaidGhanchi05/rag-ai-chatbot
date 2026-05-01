@echo off
title RAG AI Chatbot — First-Time Setup
color 0B
echo.
echo  ==========================================
echo   RAG AI Chatbot ^| First-Time Setup
echo  ==========================================
echo.

:: ── Check Python ──────────────────────────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: ── Check Node.js ─────────────────────────────────────────────────────────────
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Node.js not found. Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo  [1/4] Creating Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 ( echo  [ERROR] venv creation failed. & pause & exit /b 1 )

echo  [2/4] Installing Python dependencies (this may take a few minutes)...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %errorlevel% neq 0 ( echo  [ERROR] pip install failed. & pause & exit /b 1 )

echo  [3/4] Installing frontend dependencies...
cd frontend
call npm install
if %errorlevel% neq 0 ( echo  [ERROR] npm install failed. & pause & exit /b 1 )
cd ..

echo  [4/4] Creating data directories...
if not exist "data\uploads" mkdir "data\uploads"
if not exist "data\index"   mkdir "data\index"

echo.
echo  ==========================================
echo   Setup complete!
echo   Now double-click:
echo     start_backend.bat   (run first)
echo     start_frontend.bat  (run second)
echo  ==========================================
echo.
pause
