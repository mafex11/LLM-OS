@echo off
echo ========================================
echo Building Windows-Use Desktop App
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.12+ from https://www.python.org/
    pause
    exit /b 1
)

echo Step 1: Installing desktop-app dependencies...
cd desktop-app
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install desktop-app dependencies
    pause
    exit /b 1
)

echo.
echo Step 2: Installing PyInstaller...
cd ..
call pip install pyinstaller
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo Step 3: Building backend executable...
cd desktop-app
call python build_backend.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build backend
    pause
    exit /b 1
)

echo.
echo Step 4: Building frontend...
cd ..\frontend
call npm install
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build frontend
    pause
    exit /b 1
)

REM Copy frontend build to desktop-app
echo.
echo Step 5: Copying frontend build...
xcopy /E /I /Y "out" "..\desktop-app\frontend-build"
if not exist "..\desktop-app\frontend-build" (
    mkdir "..\desktop-app\frontend-build"
    xcopy /E /I /Y ".next\*" "..\desktop-app\frontend-build"
)

echo.
echo Step 6: Building Electron installer...
cd ..\desktop-app
call npm run electron:build
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build Electron installer
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Installer location: desktop-app\dist\
echo.
pause

