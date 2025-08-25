#!/usr/bin/env python3
"""
使用pip和setuptools创建项目发行版
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def build_distribution():
    """
    构建项目发行版
    """
    project_root = Path(__file__).parent.absolute()
    
    print("开始构建项目发行版...")
    
    # 清理之前的构建文件
    clean_previous_builds(project_root)
    
    # 构建wheel发行版
    print("构建wheel发行版...")
    subprocess.run([sys.executable, "setup.py", "bdist_wheel"], check=True, cwd=project_root)
    
    # 构建源码发行版
    print("构建源码发行版...")
    subprocess.run([sys.executable, "setup.py", "sdist"], check=True, cwd=project_root)
    
    print("构建完成！发行版文件位于 dist/ 目录中")


def clean_previous_builds(project_root):
    """
    清理之前的构建文件
    """
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)


def create_requirements_txt():
    """
    创建requirements.txt文件
    """
    requirements_content = """openpyxl>=3.1.0
mysql-connector-python>=8.0.0,<9.0.0
pandas>=1.5.0
cryptography>=3.4.8
"""
    
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements_content)
    
    print("已创建requirements.txt文件")


def freeze_dependencies():
    """
    冻结当前环境的依赖到requirements.txt
    """
    print("冻结当前环境的依赖...")
    with open("requirements.txt", "w", encoding="utf-8") as f:
        subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=f, check=True)
    
    print("依赖已冻结到requirements.txt")


def create_frozen_dist():
    """
    创建包含冻结依赖的发行版
    """
    project_root = Path(__file__).parent.absolute()
    dist_dir = project_root / "frozen_dist"
    
    print("创建包含冻结依赖的发行版...")
    
    # 删除已存在的发行版目录
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # 创建发行版目录
    dist_dir.mkdir()
    
    # 复制项目文件
    copy_project_files(project_root, dist_dir)
    
    # 冻结依赖
    os.chdir(dist_dir)
    freeze_dependencies()
    
    # 创建安装脚本
    create_install_script(dist_dir)
    
    print(f"冻结发行版创建完成: {dist_dir}")


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
        "setup.py",
        "pyproject.toml",
    ]
    
    # 复制项目文件和目录
    for item in items_to_copy:
        src_path = project_root / item
        if src_path.exists():
            if src_path.is_dir():
                shutil.copytree(src_path, target_dir / item)
            else:
                shutil.copy2(src_path, target_dir / item)


def create_install_script(dist_dir):
    """
    创建安装脚本
    """
    # Windows批处理脚本
    bat_content = """@echo off
REM ZR Daily Report 安装脚本

echo 创建虚拟环境...
python -m venv venv

echo 激活虚拟环境...
call venv\\Scripts\\activate.bat

echo 安装依赖...
pip install -r requirements.txt

echo 安装项目...
pip install .

echo 安装完成！
pause
"""
    
    with open(dist_dir / "install.bat", "w", encoding="utf-8") as f:
        f.write(bat_content)
    
    # Unix/Linux/macOS安装脚本
    sh_content = """#!/bin/bash
# ZR Daily Report 安装脚本

echo "创建虚拟环境..."
python3 -m venv venv

echo "激活虚拟环境..."
source venv/bin/activate

echo "安装依赖..."
pip install -r requirements.txt

echo "安装项目..."
pip install .

echo "安装完成！"
read -p "按Enter键退出"
"""
    
    sh_path = dist_dir / "install.sh"
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write(sh_content)
    
    # 给予执行权限
    os.chmod(sh_path, 0o755)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "frozen":
        create_frozen_dist()
    else:
        create_requirements_txt()
        build_distribution()