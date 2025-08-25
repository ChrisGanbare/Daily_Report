@echo off
REM This is a universal startup script that can continue to be used after project migration
REM Get the directory where the current script is located (i.e. the project root directory)
set PROJECT_DIR=%~dp0

REM Remove the trailing backslash
if "%PROJECT_DIR:~-1%"=="\" set PROJECT_DIR=%PROJECT_DIR:~0,-1%

REM Switch to the project directory
cd /d "%PROJECT_DIR%"

REM Check if virtual environment exists and activate it
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Run the main program and pass all arguments
echo Running ZR Daily Report program...
python ZR_Daily_Report.py %*

REM Keep the window open to view the output
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo The program encountered an error, please check the error message above.
    pause
)

REM Pause if the program ends normally to prevent the window from closing
pause