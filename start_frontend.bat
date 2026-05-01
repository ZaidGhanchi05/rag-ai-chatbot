@echo off
title RAG Frontend — React Dev Server
color 0D
echo.
echo  ==========================================
echo   RAG AI Chatbot ^| Frontend (React)
echo   http://localhost:5173
echo  ==========================================
echo.

:: Check node_modules exists
if not exist "frontend\node_modules" (
    echo  [ERROR] node_modules not found.
    echo  Please run setup.bat first!
    echo.
    pause
    exit /b 1
)

echo  Starting frontend dev server...
echo  Press Ctrl+C to stop.
echo.
cd frontend
npm run dev
cd ..
pause
