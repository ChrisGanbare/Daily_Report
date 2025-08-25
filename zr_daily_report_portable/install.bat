@echo off
REM ZR Daily Report 安装脚本

echo ================================
echo ZR Daily Report 环境安装脚本
echo ================================

echo.
echo 此脚本将:
echo 1. 创建Python虚拟环境
echo 2. 安装所有必需的依赖
echo.

REM 确认是否继续
set /p confirm=是否继续安装？(y/N): 
if /i not "%confirm%"=="y" (
    echo 安装已取消
    pause
    exit /b
)

echo.
echo 创建虚拟环境...
python -m venv venv
if %errorlevel% neq 0 (
    echo 错误：无法创建虚拟环境
    echo 请确保已安装Python并已将其添加到系统PATH中
    pause
    exit /b
)

echo.
echo 激活虚拟环境...
call venv\Scripts\activate.bat

echo.
echo 升级pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo 警告：pip升级失败，将继续安装依赖
)

echo.
echo 安装项目依赖...
pip install -r zr_daily_report\requirements.txt
if %errorlevel% neq 0 (
    echo 错误：依赖安装失败
    pause
    exit /b
)

echo.
echo 安装项目...
pip install zr_daily_report/
if %errorlevel% neq 0 (
    echo 警告：项目安装失败，可以直接运行主程序
)

echo.
echo 安装完成！
echo.
echo 要运行程序，请双击 run_report.bat
pause