@echo off
title Auto Clicker by Astryxl - Builder
color 0A

echo.
echo  ============================================
echo    Auto Clicker by Astryxl - Build Script
echo  ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python tidak ditemukan!
    echo  Download dari: https://python.org/downloads
    echo  Pastikan centang "Add Python to PATH"
    pause
    exit /b 1
)

echo  [1/4] Python ditemukan
python --version

:: Install dependencies
echo.
echo  [2/4] Install dependencies...
pip install pynput pyautogui pillow pyinstaller -q
if errorlevel 1 (
    echo  [ERROR] Gagal install dependencies!
    pause
    exit /b 1
)
echo  Dependencies OK

:: Build exe
echo.
echo  [3/4] Building .exe (ini bisa makan 1-3 menit)...
echo.
pyinstaller --noconfirm AstryxlDesk.spec
if errorlevel 1 (
    echo.
    echo  [ERROR] Build gagal! Coba jalankan ulang sebagai Administrator.
    pause
    exit /b 1
)

:: Done
echo.
echo  ============================================
echo   [4/4] BUILD SUKSES!
echo  ============================================
echo.
echo   File .exe ada di folder:
echo   dist\Auto Clicker by Astryxl.exe
echo.
echo   Kamu bisa copy .exe itu ke mana aja,
echo   ga perlu install Python lagi di komputer lain.
echo.

:: Open dist folder
explorer dist

pause
