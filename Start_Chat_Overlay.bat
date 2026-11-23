@echo off
title Floating Chat Assistant Overlay
echo ===================================================
echo  Starting Floating Chat Overlay...
echo  Press [Ctrl + Shift + C] anywhere to Open/Close!
echo ===================================================
echo.
cd /d "%~dp0"
python floating_chat_overlay.py
pause

