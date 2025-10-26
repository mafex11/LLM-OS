@echo off
echo Setting up API keys for Windows-Use...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Run the setup script
python setup_api_keys.py

echo.
echo Setup complete! You can now run the Electron app.
pause




