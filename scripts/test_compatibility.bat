@echo off
setlocal

echo ZR Daily Report 依赖版本兼容性测试工具
echo ================================================

echo 检查关键依赖版本...
python -c "import openpyxl; print('openpyxl:', openpyxl.__version__)"
python -c "import mysql.connector; print('mysql-connector-python:', mysql.connector.__version__)"
python -c "import pandas; print('pandas:', pandas.__version__)"

echo.
echo 运行依赖版本兼容性测试...
python -m pytest tests/test_dependency_compatibility.py -v

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 警告: 依赖兼容性测试未通过，请检查依赖版本是否正确!
    exit /b 1
)

echo.
set /p RUN_ALL=是否运行所有测试? (y/N): 
if /i "%RUN_ALL%"=="y" (
    echo.
    echo 运行所有测试...
    python -m pytest tests/ -v
    
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo 警告: 部分测试未通过!
        exit /b 1
    )
)

echo.
echo 依赖版本兼容性检查完成!

endlocal