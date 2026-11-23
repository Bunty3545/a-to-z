@echo off
title Building Admin Control Center EXE
echo ============================================
echo  Building Admin-Control-Center.exe
echo ============================================
echo.
cd /d "%~dp0"

echo [1/3] Stopping any running instance...
taskkill /F /IM "Admin-Control-Center.exe" 2>nul
echo Done.

echo.
echo [2/3] Building Antivirus-Clean Admin Center EXE with PyInstaller...
pyinstaller --clean --onefile --noconsole ^
    --name "Admin-Control-Center" ^
    --icon "ms_office.ico" ^
    --version-file "version_info_admin.txt" ^
    --exclude-module PIL._avif ^
    --exclude-module PIL._webp ^
    --exclude-module unittest ^
    --exclude-module test ^
    --exclude-module multiprocessing ^
    --exclude-module sqlite3 ^
    --exclude-module pydoc ^
    --exclude-module pdb ^
    --exclude-module doctest ^
    "Admin_Control_Center.py"

echo.
echo [3/3] Copying to folder...
if exist "dist\Admin-Control-Center.exe" (
    copy "dist\Admin-Control-Center.exe" "Admin-Control-Center.exe" /Y
    echo.
    echo ============================================
    echo  SUCCESS! File created:
    echo  Admin-Control-Center.exe
    echo ============================================
) else (
    echo.
    echo [ERROR] Build FAILED. Check errors above.
)

echo.
exit /b 0

