@echo off
title Windows System Cleaner - One Click Setup
echo ==========================================
echo    WINDOWS SYSTEM CLEANER SETUP
echo ==========================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://python.org and try again.
    pause
    exit /b
)

echo [1/2] Installing requirements...
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b
)

echo [2/2] Launching Application...
echo.
echo Once the app opens, go to Settings to add it to your Start Menu!
echo.
start "" pythonw WindowsSystemCleaner.py

echo Setup Complete!
timeout /t 3 >nul
exit
