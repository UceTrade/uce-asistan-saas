@echo off
title UceAsistan - AI Trading Coach
color 0A

echo ============================================
echo    UceAsistan - AI Trading Coach
echo    Version 2.2.0
echo ============================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python bulunamadi!
    echo Lutfen Python 3.10+ yukleyin: https://python.org/downloads
    pause
    exit /b 1
)

:: Change to backend directory
cd /d "%~dp0backend"

:: Check if requirements are installed
python -c "import websockets" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Bagimliliklar yukleniyor...
    pip install -r requirements.txt
)

:: Start the server
echo [OK] Sunucu baslatiliyor...
echo.
python start_server.py

:: If server exits, wait for user
echo.
echo [INFO] Sunucu durdu.
pause
