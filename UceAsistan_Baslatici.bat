@echo off
TITLE UceAsistan Super Launcher
SETLOCAL EnableDelayedExpansion
SET "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ===========================================
echo   UceAsistan Hepsi-Bir-Arada Baslatici
echo ===========================================
echo.

:: Step 1: Python Check
echo [1/3] Backend Hazirlaniyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi! Lutfen Python yukleyin.
    pause
    exit /b
)

:: Install Backend Dependencies in background if needed
pip install websockets pandas numpy aiohttp yfinance pydantic pydantic-settings fastapi uvicorn sqlalchemy python-dotenv >nul 2>&1

:: Step 2: Start Backend in a New Window
echo [2/3] Sunucu (Backend) yeni pencerede aciliyor...
start "UceAsistan Backend" cmd /c "cd /d %SCRIPT_DIR%backend && python start_server.py"

:: Buffer to let server initialize
timeout /t 3 /nobreak >nul

:: Step 3: Start Electron Frontend
echo [3/3] Electron Uygulamasi (Frontend) baslatiliyor...
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Node.js/NPM bulunamadi! 
    echo Uygulama yuzunu gormek icin Node.js yuklu olmalidir.
    pause
    exit /b
)

if not exist "node_modules\" (
    echo [BILGI] node_modules eksik, yukleniyor...
    call npm install
)

echo.
echo ===========================================
echo   UceAsistan Sistemleri Aktif! 🚀
echo ===========================================
echo.

npm start

pause
