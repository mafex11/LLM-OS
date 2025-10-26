@echo off
echo ========================================
echo Fixing NSIS Plugin Issues
echo ========================================
echo.

REM Step 1: Clear corrupted NSIS caches
echo Step 1: Clearing corrupted NSIS caches...
if exist "%LOCALAPPDATA%\electron-builder\Cache\nsis" (
    echo Removing NSIS cache...
    rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache\nsis"
) else (
    echo NSIS cache not found
)

if exist "%LOCALAPPDATA%\electron-builder\Cache\nsis-resources" (
    echo Removing NSIS resources cache...
    rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache\nsis-resources"
) else (
    echo NSIS resources cache not found
)

echo ✅ NSIS caches cleared
echo.

REM Step 2: Rebuild NSIS cache (forces fresh plugin download)
echo Step 2: Rebuilding NSIS cache...
echo Running: npx electron-builder --dir
call npx electron-builder --dir
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to rebuild NSIS cache
    echo Exit code: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo ✅ NSIS cache rebuilt successfully
echo.

REM Step 3: Retry full Windows build
echo Step 3: Building Windows installer...
echo Running: npm run electron:build
call npm run electron:build
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo ❌ Build failed
    echo ========================================
    echo Exit code: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================
echo ✅ Build completed successfully!
echo ========================================
echo.
echo Installer location: dist\
echo.
pause
