@echo off
title Push to GitHub
color 0A
echo.
echo  ==========================================
echo   RAG AI Chatbot ^| Push to GitHub
echo  ==========================================
echo.
echo  INSTRUCTIONS:
echo  1. Go to github.com and create a new repo called "rag-ai-chatbot"
echo  2. Copy your repo URL (e.g. https://github.com/yourname/rag-ai-chatbot.git)
echo  3. Paste it below when asked
echo.
set /p REPO_URL="Paste your GitHub repo URL here: "

if "%REPO_URL%"=="" (
    echo  [ERROR] No URL entered. Exiting.
    pause
    exit /b 1
)

echo.
echo  Connecting to GitHub...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo  Pushing your code...
git branch -M main
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo  ==========================================
    echo   SUCCESS! Your code is now on GitHub.
    echo   URL: %REPO_URL%
    echo  ==========================================
) else (
    echo.
    echo  [ERROR] Push failed.
    echo  Make sure you are logged in to Git.
    echo  Run: git config --global user.name "Your Name"
    echo  Run: git config --global user.email "your@email.com"
)
echo.
pause
