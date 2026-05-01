@echo off
title RAG AI Chatbot — Docker
color 0B
echo.
echo  ==========================================
echo   RAG AI Chatbot ^| Docker Launcher
echo  ==========================================
echo.

:: Check Docker is installed and running
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Docker not found.
    echo  Please install Docker Desktop from https://docker.com
    pause
    exit /b 1
)

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Docker is not running.
    echo  Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo  Building and starting all services...
echo  (First time takes a few minutes to download model)
echo.
docker-compose up --build

pause
