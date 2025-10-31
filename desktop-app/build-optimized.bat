@echo off
echo ========================================
echo Building Windows-Use Desktop App (Optimized)
echo ========================================
echo.

set PYTHON_CMD=python
set NODE_CMD=node

REM Check if Node.js is installed
where %NODE_CMD% >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
where %PYTHON_CMD% >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.12+ from https://www.python.org/
    pause
    exit /b 1
)

echo.
echo Step 1: Installing desktop-app dependencies...
cd desktop-app
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install desktop-app dependencies
    pause
    exit /b 1
)

echo.
echo Step 2: Building optimized backend executable...
cd ..
call %PYTHON_CMD% desktop-app\build_backend.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build backend
    pause
    exit /b 1
)

echo.
echo Step 3: Building frontend...
cd frontend
call npm install
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build frontend
    pause
    exit /b 1
)

echo.
echo Step 4: Copying frontend build...
cd ..\desktop-app

REM Remove old build if exists
if exist "frontend-build" (
    rmdir /S /Q "frontend-build"
)

REM Create frontend-build directory
mkdir "frontend-build"

REM Copy the standalone build from frontend
cd ..\frontend
if exist ".next\standalone" (
    echo Copying standalone Next.js build...
    xcopy /E /I /Y ".next\standalone\*" "..\desktop-app\frontend-build\"
) else (
    echo ERROR: Standalone build not found. Make sure frontend build completed successfully.
    pause
    exit /b 1
)

REM Also copy necessary .next files
if exist ".next" (
    xcopy /E /I /Y ".next\static" "..\desktop-app\frontend-build\.next\static\"
    if exist ".next\BUILD_ID" (
        xcopy /E /I /Y ".next\BUILD_ID" "..\desktop-app\frontend-build\.next\BUILD_ID"
    )
)

cd ..\desktop-app

echo.
echo Step 5: Building Electron package...
call npm run electron:build
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build Electron package
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
echo Package size reduction optimizations applied:
echo - Backend: Excluded torch, scipy, sklearn, and other large packages
echo - Frontend: Using Next.js standalone mode
echo - Compression: Maximum LZMA compression enabled
echo.
pause





