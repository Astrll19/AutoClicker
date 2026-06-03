@echo off
title Auto Clicker by Astryxl
python AstryxlDesk.py
if errorlevel 1 (
    echo.
    echo [ERROR] Gagal jalan. Install dulu:
    echo pip install pynput pyautogui pillow
    pause
) else (
    pause
)
