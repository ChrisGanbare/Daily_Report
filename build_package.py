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


def create_portable_package():
    """
    创建可移植的完整包
    """
    project_root = Path(__file__).parent.absolute()
    package_name = "zr_daily_report_package"
    package_dir = project_root / package_name
    
    print(f"开始创建可移植包: {package_name}")
    
    # 删除已存在的包目录
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
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
    create_zip_package(package_dir, project_root / f"{package_name}.zip")
    
    print(f"打包完成！可移植包位置: {project_root / f'{package_name}.zip'}")


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
pandas>=1.5.0
cryptography>=3.4.8
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
        pip_path = package_dir / "venv" / "Scripts" / "pip"
    else:  # Unix/Linux/macOS
        pip_path = package_dir / "venv" / "bin" / "pip"
    
    requirements_path = package_dir / "zr_daily_report" / "requirements.txt"
    
    # 升级pip
    subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
    
    # 安装项目依赖
    subprocess.run([str(pip_path), "install", "-r", str(requirements_path)], check=True)
    
    # 安装项目本身
    subprocess.run([str(pip_path), "install", str(package_dir / "zr_daily_report")], check=True)


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