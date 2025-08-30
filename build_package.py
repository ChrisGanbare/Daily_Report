#!/usr/bin/env python3
"""
项目打包脚本，用于创建可移植的完整包，可以在其他电脑上直接运行
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
import subprocess


def get_project_version():
    """
    获取项目版本号
    """
    # 首先尝试从Git标签获取版本号
    try:
        result = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], 
                              capture_output=True, text=True, cwd=Path(__file__).parent)
        if result.returncode == 0:
            version = result.stdout.strip()
            # 移除开头的'v'字符（如果存在）
            if version.startswith('v'):
                version = version[1:]
            return version
    except Exception:
        pass  # 如果Git命令失败，则使用其他方法
    
    # 从pyproject.toml文件中提取版本号
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("version ="):
                    # 提取版本号字符串
                    version = line.split("=")[1].strip().strip('"')
                    return version
    
    # 如果无法从pyproject.toml获取，则从setup.py获取
    setup_path = Path(__file__).parent / "setup.py"
    if setup_path.exists():
        with open(setup_path, "r", encoding="utf-8") as f:
            for line in f:
                if "version=" in line:
                    # 提取版本号字符串
                    version = line.split("version=")[1].split(",")[0].strip().strip('"')
                    return version
    
    # 默认版本号
    return "1.0.0"


def create_portable_package():
    """
    创建可移植的完整包
    """
    project_root = Path(__file__).parent.absolute()
    version = get_project_version()
    package_name = f"zr_daily_report_v{version}"
    package_dir = project_root / package_name
    
    # 创建 release 目录（如果不存在）
    release_dir = project_root / "release"
    release_dir.mkdir(exist_ok=True)
    
    print(f"开始创建可移植包: {package_name}")
    
    # 删除已存在的包目录
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    # 删除旧的压缩包
    zip_filename = f"{package_name}.zip"
    zip_path = release_dir / zip_filename  # 将压缩包放在 release 目录中
    if zip_path.exists():
        zip_path.unlink()
    
    # 创建包目录结构
    (package_dir / "zr_daily_report").mkdir(parents=True)
    (package_dir / "venv").mkdir()
    
    print("复制项目文件...")
    # 复制项目文件
    copy_project_files(project_root, package_dir / "zr_daily_report")
    
    print("创建虚拟环境...")
    # 创建虚拟环境
    create_virtual_environment(package_dir)
    
    print("安装依赖...")
    # 安装依赖
    install_dependencies(package_dir)
    
    print("打包依赖...")
    # 打包依赖到便携包中
    pack_dependencies(package_dir)
    
    print("创建启动脚本...")
    # 创建启动脚本
    create_startup_scripts(package_dir)
    
    print("创建压缩包...")
    # 创建压缩包
    create_zip_package(package_dir, zip_path)
    
    # 清理临时目录
    print("清理临时文件...")
    shutil.rmtree(package_dir)
    
    print(f"打包完成！可移植包位置: {zip_path}")


def copy_project_files(project_root, target_dir):
    """
    复制项目文件到目标目录
    """
    # 需要复制的目录和文件
    items_to_copy = [
        "src",
        "config",
        "template",
        "zr_daily_report.py",
        "README.md",
    ]
    
    # 复制项目文件和目录
    for item in items_to_copy:
        src_path = project_root / item
        if src_path.exists():
            if src_path.is_dir():
                shutil.copytree(src_path, target_dir / item)
            else:
                shutil.copy2(src_path, target_dir / item)
    
    # 创建requirements.txt文件
    create_requirements_file(target_dir)


def create_requirements_file(target_dir):
    """
    创建requirements.txt文件
    """
    requirements_content = """openpyxl>=3.1.0
mysql-connector-python>=8.0.0,<9.0.0
cryptography==43.0.1
"""
    
    with open(target_dir / "requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements_content)


def create_virtual_environment(package_dir):
    """
    在包目录中创建虚拟环境
    """
    venv_dir = package_dir / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)


def install_dependencies(package_dir):
    """
    在虚拟环境中安装项目依赖
    """
    # Windows和Unix系统使用不同的激活脚本
    if os.name == "nt":  # Windows
        python_path = package_dir / "venv" / "Scripts" / "python.exe"
        pip_path = package_dir / "venv" / "Scripts" / "pip"
    else:  # Unix/Linux/macOS
        python_path = package_dir / "venv" / "bin" / "python"
        pip_path = package_dir / "venv" / "bin" / "pip"
    
    requirements_path = package_dir / "zr_daily_report" / "requirements.txt"
    
    # 升级pip，使用阿里云镜像源
    try:
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip", 
                        "-i", "https://mirrors.aliyun.com/pypi/simple/"], check=True)
    except subprocess.CalledProcessError:
        # 如果阿里云镜像源失败，则使用默认源
        print("使用阿里云镜像源升级pip失败，尝试使用默认源...")
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    
    # 安装项目依赖，使用阿里云镜像源
    try:
        subprocess.run([str(pip_path), "install", "-r", str(requirements_path), 
                        "-i", "https://mirrors.aliyun.com/pypi/simple/"], check=True)
    except subprocess.CalledProcessError:
        # 如果阿里云镜像源失败，则使用默认源
        print("使用阿里云镜像源安装依赖失败，尝试使用默认源...")
        subprocess.run([str(pip_path), "install", "-r", str(requirements_path)], check=True)


def pack_dependencies(package_dir):
    """
    将依赖打包到便携包中，使用阿里云镜像源下载依赖
    """
    # Windows和Unix系统使用不同的激活脚本
    if os.name == "nt":  # Windows
        python_path = package_dir / "venv" / "Scripts" / "python.exe"
        pip_path = package_dir / "venv" / "Scripts" / "pip"
    else:  # Unix/Linux/macOS
        python_path = package_dir / "venv" / "bin" / "python"
        pip_path = package_dir / "venv" / "bin" / "pip"
    
    # 下载依赖包到本地目录，使用阿里云镜像源
    wheels_dir = package_dir / "zr_daily_report" / "wheels"
    wheels_dir.mkdir(exist_ok=True)
    
    requirements_path = package_dir / "zr_daily_report" / "requirements.txt"
    try:
        subprocess.run([str(pip_path), "download", "-r", str(requirements_path), 
                        "-d", str(wheels_dir), "-i", "https://mirrors.aliyun.com/pypi/simple/"], check=True)
    except subprocess.CalledProcessError:
        # 如果阿里云镜像源失败，则使用默认源
        print("使用阿里云镜像源下载依赖失败，尝试使用默认源...")
        subprocess.run([str(pip_path), "download", "-r", str(requirements_path), 
                        "-d", str(wheels_dir)], check=True)


def create_startup_scripts(package_dir):
    """
    创建启动脚本
    """
    project_dir = package_dir / "zr_daily_report"
    
    # 创建Windows批处理脚本
    bat_content = f"""@echo off
REM ZR Daily Report 启动脚本

REM 获取当前脚本所在的目录
set PROJECT_DIR=%~dp0

REM 切换到项目目录
cd /d "%PROJECT_DIR%zr_daily_report"

REM 激活虚拟环境
call "..\venv\Scripts\activate.bat"

REM 安装本地依赖包（如果存在）
if exist "wheels" (
    echo 安装本地依赖包...
    pip install wheels/*.whl --force-reinstall
)

REM 运行主程序
python zr_daily_report.py %*

REM 如果程序正常结束也暂停，防止窗口关闭
pause
"""
    
    with open(package_dir / "run-report.bat", "w", encoding="utf-8") as f:
        f.write(bat_content)
    
    # 创建PowerShell脚本
    ps1_content = f"""# ZR Daily Report 启动脚本

# 获取当前脚本所在的目录
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 切换到项目目录
Set-Location "$ProjectDir\\zr_daily_report"

# 激活虚拟环境
..\\venv\\Scripts\\Activate.ps1

# 安装本地依赖包（如果存在）
if (Test-Path "wheels") {{
    Write-Host "安装本地依赖包..."
    pip install wheels/*.whl --force-reinstall
}}

# 运行主程序
python zr_daily_report.py $args

# 如果程序正常结束也暂停，防止窗口关闭
Read-Host -Prompt "按Enter键退出"
"""
    
    with open(package_dir / "run-report.ps1", "w", encoding="utf-8") as f:
        f.write(ps1_content)
    
    # 创建Unix/Linux/macOS启动脚本
    sh_content = f"""#!/bin/bash
# ZR Daily Report 启动脚本

# 获取当前脚本所在的目录
PROJECT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

# 切换到项目目录
cd "$PROJECT_DIR/zr_daily_report"

# 激活虚拟环境
source "../venv/bin/activate"

# 安装本地依赖包（如果存在）
if [ -d "wheels" ]; then
    echo "安装本地依赖包..."
    pip install wheels/*.whl --force-reinstall
fi

# 运行主程序
python zr_daily_report.py "$@"

# 如果程序正常结束也暂停，防止窗口关闭
read -p "按Enter键退出"
"""
    
    sh_path = package_dir / "run-report.sh"
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write(sh_content)
    
    # 给予执行权限
    os.chmod(sh_path, 0o755)
    
    # 创建安装脚本
    install_bat_content = """@echo off
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
call "venv\\Scripts\\activate.bat"
if %errorlevel% neq 0 (
    echo 错误：激活虚拟环境失败
    pause
    exit /b 1
)

REM 检查是否需要升级pip
echo.
echo 检查pip版本...
for /f "tokens=2" %%i in ('pip --version 2^>^&1') do set PIP_VERSION=%%i
echo 当前pip版本: %PIP_VERSION%

REM 只有在明确需要升级时才升级pip
set NEED_UPGRADE=0
REM 这里可以添加检查pip版本是否过旧的逻辑，简化起见我们跳过自动升级
if "%NEED_UPGRADE%"=="1" (
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
) else (
    echo.
    echo 跳过pip升级以节省时间
)

REM 安装项目依赖
echo.
echo 正在安装项目依赖...
python -m pip install -r "zr_daily_report\\requirements.txt" -i https://mirrors.aliyun.com/pypi/simple/
if %errorlevel% neq 0 (
    echo 警告：使用阿里云镜像源安装依赖失败，尝试使用默认源...
    python -m pip install -r "zr_daily_report\\requirements.txt"
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
"""
    
    with open(package_dir / "install.bat", "w", encoding="utf-8") as f:
        f.write(install_bat_content)
    
    # 创建README.txt文件
    readme_content = """# ZR Daily Report 可移植包

这是一个完整的可移植包，包含了运行ZR Daily Report所需的所有文件。

## 安装步骤

1. 在目标计算机上确保已安装Python 3.8或更高版本
2. 双击运行 `install.bat` 脚本
3. 按照提示完成环境安装

## 运行程序

安装完成后，可以通过以下方式运行程序：
- 双击 `run-report.bat` 运行程序
- 或在命令行中执行 `python zr_daily_report.py`

## 项目结构
- `zr_daily_report/` - 项目主目录
- `venv/` - 虚拟环境目录（安装后创建）
- `wheels/` - 本地依赖包目录（包含项目核心依赖）
- `install.bat` - 安装脚本
- `run-report.bat` - 启动脚本
- `run-report.ps1` - PowerShell启动脚本

## 系统要求
- Windows 7/8/10/11
- Python 3.8或更高版本
- 至少100MB可用磁盘空间

## 注意事项
- 请勿修改目录结构
- 如需重新安装，请删除 `venv` 目录并重新运行 `install.bat`
- 本地依赖包(wheels目录)已包含项目核心依赖，无需联网下载
"""
    
    with open(package_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)


def should_exclude_file(file_path):
    """
    判断文件是否应该被排除在打包之外
    """
    # 需要排除的文件和目录模式
    exclude_patterns = [
        '__pycache__',
        '.pyc',
        '.pyo',
        '.pyd',
        '.pytest_cache',
        '.coverage',
        'test_',
        '_test',
        'tests/',
        'test.py',
        'conftest.py',
    ]
    
    # 检查文件路径是否匹配排除模式
    for pattern in exclude_patterns:
        if pattern in file_path:
            return True
    
    return False

def create_zip_package(package_dir, zip_path):
    """
    创建ZIP压缩包，排除release目录和测试文件等非业务逻辑文件
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            # 移除release目录，避免递归打包
            dirs[:] = [d for d in dirs if d != "release"]
            
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, package_dir)
                # 确保不包含release目录中的内容
                if not arc_path.startswith("release"):
                    # 排除测试相关的文件
                    if not should_exclude_file(arc_path):
                        zipf.write(file_path, arc_path)


if __name__ == "__main__":
    create_portable_package()