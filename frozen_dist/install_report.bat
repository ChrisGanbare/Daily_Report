@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

@echo --------------------------------------------------
@echo                ZR Daily Report 安装程序
@echo --------------------------------------------------
@echo.

@echo 正在检查Python环境...
@python --version >nul 2>&1
@if %errorlevel% NEQ 0 (
    @echo 错误: 未找到Python环境,请先安装Python 3.8或更高版本
    @echo.
    @echo 下载地址: https://www.python.org/downloads/
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

REM 检查Python版本
@python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
@if %errorlevel% NEQ 0 (
    @for /f "tokens=*" %%i in ('python --version 2^>nul') do set "PYTHON_VERSION=%%i"
    @echo 错误: Python版本不符合要求,需要Python 3.8或更高版本
    @echo 当前Python版本: !PYTHON_VERSION!
    @echo.
    @echo 下载地址: https://www.python.org/downloads/
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

@echo Python环境检查通过
@echo.

@echo 创建虚拟环境...
@python -m venv venv >nul 2>&1
@if %errorlevel% NEQ 0 (
    @echo 错误: 创建虚拟环境失败
    @echo.
    @echo 可能的原因:
    @echo 1. Python安装不完整
    @echo 2. 磁盘空间不足
    @echo 3. 当前目录没有写入权限
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

@echo 虚拟环境创建成功
@echo.

@echo 激活虚拟环境...
@call venv\Scripts\activate.bat >nul 2>&1
@if %errorlevel% NEQ 0 (
    @echo 错误: 激活虚拟环境失败
    @echo.
    @echo 可能的原因:
    @echo 1. 虚拟环境创建不完整
    @echo 2. 脚本文件权限问题
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

@echo 虚拟环境激活成功
@echo.

@echo 安装依赖包...
@pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ >nul 2>&1
@if %errorlevel% NEQ 0 (
    @echo 错误: 安装依赖包失败
    @echo.
    @echo 可能的原因:
    @echo 1. 网络连接问题
    @echo 2. 阿里云镜像源暂时不可用
    @echo 3. 依赖包版本不兼容
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

@echo 依赖包安装成功
@echo.

@echo 安装ZR Daily Report程序...
@pip install ./zr_daily_report >nul 2>&1
@if %errorlevel% NEQ 0 (
    @echo 错误: 安装程序失败
    @echo.
    @echo 可能的原因:
    @echo 1. 项目文件损坏
    @echo 2. 安装脚本权限问题
    @echo.
    @echo 按任意键退出当前窗口
    @pause >nul
    @exit /b 1
)

@echo 程序安装成功
@echo.

@echo --------------------------------------------------
@echo                     安装完成！
@echo --------------------------------------------------
@echo.
@echo 双击 "run_report.bat" 运行程序
@echo.
@echo 按任意键退出当前窗口
@pause >nul
