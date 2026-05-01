@echo off
title RAG Backend — FastAPI Server
color 0B
echo.
echo  ==========================================
echo   RAG AI Chatbot ^| Backend (FastAPI)
echo   http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo  ==========================================
echo.

:: Check virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo  [ERROR] Virtual environment not found.
    echo  Please run setup.bat first!
    echo.
    pause
    exit /b 1
)

:: Activate venv and start server
call venv\Scripts\activate.bat
echo  Starting backend server...
echo  Press Ctrl+C to stop.
echo.
cd backend
uvicorn api:app --reload --host 0.0.0.0 --port 8000
cd ..
pause
