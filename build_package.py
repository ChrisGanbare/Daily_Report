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
    
    print(f"开始创建可移植包: {package_name}")
    
    # 删除已存在的包目录
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    # 删除旧的压缩包
    zip_filename = f"{package_name}.zip"
    zip_path = project_root / zip_filename
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
        "ZR_Daily_Report.py",
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
    
    # 升级pip
    subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    
    # 安装项目依赖
    subprocess.run([str(pip_path), "install", "-r", str(requirements_path)], check=True)


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
call "..\\venv\\Scripts\\activate.bat"

REM 运行主程序
python ZR_Daily_Report.py %*

REM 如果程序正常结束也暂停，防止窗口关闭
pause
"""
    
    with open(package_dir / "run_report.bat", "w", encoding="utf-8") as f:
        f.write(bat_content)
    
    # 创建PowerShell脚本
    ps1_content = f"""# ZR Daily Report 启动脚本

# 获取当前脚本所在的目录
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 切换到项目目录
Set-Location "$ProjectDir\\zr_daily_report"

# 激活虚拟环境
..\\venv\\Scripts\\Activate.ps1

# 运行主程序
python ZR_Daily_Report.py $args

# 如果程序正常结束也暂停，防止窗口关闭
Read-Host -Prompt "按Enter键退出"
"""
    
    with open(package_dir / "run_report.ps1", "w", encoding="utf-8") as f:
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

# 运行主程序
python ZR_Daily_Report.py "$@"

# 如果程序正常结束也暂停，防止窗口关闭
read -p "按Enter键退出"
"""
    
    sh_path = package_dir / "run_report.sh"
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write(sh_content)
    
    # 给予执行权限
    os.chmod(sh_path, 0o755)


def create_zip_package(package_dir, zip_path):
    """
    创建ZIP压缩包
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arc_path)


if __name__ == "__main__":
    create_portable_package()