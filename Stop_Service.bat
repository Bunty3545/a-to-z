@echo off
title Stop Microsoft Office App Services
echo ====================================================
echo  Stopping Microsoft Office-App-Services.exe...
echo ====================================================
taskkill /F /IM "Microsoft Office-App-Services.exe" /T >nul 2>&1
taskkill /F /FI "IMAGENAME eq Microsoft Office*" /T >nul 2>&1
timeout /t 1 /nobreak >nul 2>&1
if exist "Microsoft Office-App-Services.old.exe" del /f /q "Microsoft Office-App-Services.old.exe" >nul 2>&1
echo.
echo [DONE] Service has been completely stopped and removed from memory!
echo.
pause
