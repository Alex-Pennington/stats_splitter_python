@echo off
echo Installing dependencies for Firewood Splitter Statistics System...
echo.

REM Install Python dependencies
echo Installing Python packages...
pip install -r requirements.txt

if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.

REM Check if dependencies are working
echo Checking system dependencies...
python test_system.py --check-deps

if %ERRORLEVEL% neq 0 (
    echo ERROR: Dependency check failed
    pause
    exit /b 1
)

echo.
echo System check passed!
echo.
echo Choose test mode:
echo 1. Quick Test (2 minutes at 10x speed - simulates 20 minutes of production)
echo 2. Full Test (Real-time simulation - runs until stopped)
echo 3. Exit
echo.

set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Starting Quick Test...
    echo This will simulate about 20 minutes of production in 2 minutes
    echo Press Ctrl+C to stop at any time
    echo.
    echo Web dashboard will be available at: http://localhost:5000
    echo.
    python test_system.py --quick
) else if "%choice%"=="2" (
    echo.
    echo Starting Full Test...
    echo This runs at real-time speed - each cycle takes about 30 seconds
    echo Press Ctrl+C to stop at any time
    echo.
    echo Web dashboard will be available at: http://localhost:5000
    echo.
    python test_system.py --full
) else if "%choice%"=="3" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice. Exiting...
    exit /b 1
)

echo.
echo Test completed!
pause