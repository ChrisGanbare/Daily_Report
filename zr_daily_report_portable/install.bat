@echo off
echo Installing ZR Daily Report dependencies...
echo ========================================

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to create virtual environment. Please ensure Python is installed and accessible.
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to upgrade pip.
    pause
    exit /b 1
)

REM Install required packages
echo Installing required packages...
pip install openpyxl mysql-connector-python pandas cryptography
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install required packages.
    pause
    exit /b 1
)

echo.
echo Installation completed successfully!
echo You can now run the program using run_report.bat
echo.
pause