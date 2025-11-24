@echo off
REM Quick test runner for Windows
REM Runs basic smoke tests to verify everything works

echo ================================================================================
echo Windows-Use Agent - Quick Test Runner
echo ================================================================================
echo.

REM Activate virtual environment if it exists
if exist "..\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\venv\Scripts\activate.bat
)

echo Running quick smoke tests...
echo.

REM Run only fast unit tests
pytest tests/unit -v --tb=short -m "unit and not slow" --maxfail=5

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo All quick tests PASSED!
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo Some tests FAILED. Check output above for details.
    echo ================================================================================
)

pause

