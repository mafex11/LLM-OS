@echo off
echo ================================================================================
echo Windows-Use Agent - Quick Test Runner
echo ================================================================================
echo.

cd ..\..

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Running automated tests...
echo.

python tests\automated\run_tests.py

echo.
echo ================================================================================
echo Tests Complete!
echo Check tests\automated\results\ for detailed reports
echo ================================================================================
echo.

pause

