@echo off
REM ZR Daily Report 安装脚本

@chcp 65001 >nul

echo ================================
echo ZR Daily Report 环境安装
echo ================================

REM 检查Python是否已安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python，请先安装Python 3.8或更高版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 获取Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo 检测到Python版本: %PYTHON_VERSION%

REM 创建虚拟环境
echo.
echo 正在创建虚拟环境...
python -m venv venv
if %errorlevel% neq 0 (
    echo 错误：创建虚拟环境失败
    pause
    exit /b 1
)

REM 激活虚拟环境
echo.
echo 正在激活虚拟环境...
call "venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo 错误：激活虚拟环境失败
    pause
    exit /b 1
)

REM 升级pip（使用阿里云镜像源）
echo.
echo 正在升级pip...
python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
if %errorlevel% neq 0 (
    echo 警告：使用阿里云镜像源升级pip失败，尝试使用默认源...
    python -m pip install --upgrade pip
    if %errorlevel% neq 0 (
        echo 错误：升级pip失败
        pause
        exit /b 1
    )
)

REM 重新安装pip以解决路径问题（使用阿里云镜像源）
echo.
echo 正在重新安装pip以解决路径问题...
python -m pip install --force-reinstall pip -i https://mirrors.aliyun.com/pypi/simple/
if %errorlevel% neq 0 (
    echo 警告：使用阿里云镜像源重新安装pip失败，尝试使用默认源...
    python -m pip install --force-reinstall pip
    if %errorlevel% neq 0 (
        echo 错误：重新安装pip失败
        pause
        exit /b 1
    )
)

REM 安装项目依赖（使用阿里云镜像源）
echo.
echo 正在安装项目依赖...
python -m pip install -r "zr_daily_report\requirements.txt" -i https://mirrors.aliyun.com/pypi/simple/
if %errorlevel% neq 0 (
    echo 警告：使用阿里云镜像源安装依赖失败，尝试使用默认源...
    python -m pip install -r "zr_daily_report\requirements.txt"
    if %errorlevel% neq 0 (
        echo 错误：安装项目依赖失败
        pause
        exit /b 1
    )
)

echo.
echo 安装完成！
echo.
echo 请使用以下方式运行程序：
echo 1. 双击 run-report.bat
echo 2. 或在命令行中执行：python zr_daily_report.py
echo.
echo 按任意键退出...
pause >nul
