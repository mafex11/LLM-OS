@echo off
echo ========================================
echo Windows-Use Desktop - Quick Setup
echo ========================================
echo.
echo This script will help you set up the desktop app quickly.
echo.
pause

echo Step 1: Creating app icons...
python create_icons.py
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Icon creation failed. Installing Pillow...
    pip install pillow
    python create_icons.py
)

echo.
echo Step 2: Installing dependencies...
call npm install

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run 'build.bat' to build the full desktop app
echo 2. Or run 'npm run electron:dev' to test in development mode
echo.
pause

