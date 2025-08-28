@echo off
REM This is a universal startup script that can continue to be used after project migration
REM Get the directory where the current script is located (i.e. the project root directory)
set PROJECT_DIR=%~dp0

REM Remove the trailing backslash
if "%PROJECT_DIR:~-1%"=="\" set PROJECT_DIR=%PROJECT_DIR:~0,-1%

REM Switch to the project directory
cd /d "%PROJECT_DIR%"

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment. Please ensure Python is installed.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if requirements are installed
echo Checking and installing dependencies...
pip install -e .[test,dev] --upgrade
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies. Trying alternative installation...
    pip install openpyxl mysql-connector-python pandas cryptography
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install dependencies. Please check your Python and pip installation.
        pause
        exit /b 1
    )
)

REM Run the main program and pass all arguments
echo Running ZR Daily Report program...
python zr_daily_report.py %*

REM Keep the window open to view the output
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo The program encountered an error, please check the error message above.
    pause
)

REM Pause if the program ends normally to prevent the window from closing
pause