@echo off
TITLE UceAsistan Backend Builder (PyInstaller)
SETLOCAL EnableDelayedExpansion

echo =====================================================
echo   UceAsistan Backend - PyInstaller Build Script
echo =====================================================
echo.

REM Step 1: Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)
python --version

REM Step 2: Install PyInstaller
echo.
echo [2/5] Installing PyInstaller...
pip install pyinstaller --quiet
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller installation failed!
    pause
    exit /b 1
)
echo PyInstaller installed successfully.

REM Step 3: Clean previous builds
echo.
echo [3/5] Cleaning previous builds...
if exist build\ (
    rmdir /s /q build
    echo - Removed build/
)
if exist dist\ (
    rmdir /s /q dist
    echo - Removed dist/
)

REM Step 4: Build backend.exe
echo.
echo [4/5] Building backend.exe (this may take 3-5 minutes)...
echo.
pyinstaller backend.spec --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

REM Step 5: Verify output
echo.
echo [5/5] Verifying build...
if exist dist\uceasistan-backend.exe (
    echo.
    echo =====================================================
    echo   BUILD SUCCESSFUL! 
    echo =====================================================
    echo.
    echo Output: dist\uceasistan-backend.exe
    
    REM Get file size
    for %%A in (dist\uceasistan-backend.exe) do (
        set size=%%~zA
        set /a sizeMB=!size! / 1048576
        echo Size: !sizeMB! MB
    )
    
    echo.
    echo Next steps:
    echo 1. Test: cd dist ^&^& uceasistan-backend.exe
    echo 2. Copy to Electron: copy dist\uceasistan-backend.exe ..\electron\backend\
    echo.
) else (
    echo [ERROR] Backend executable not found!
    pause
    exit /b 1
)

echo =====================================================
pause
