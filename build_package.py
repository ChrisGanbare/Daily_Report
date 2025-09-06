#!/usr/bin/env python3
"""
Package building script
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

def ensure_build_tools():
    """
    确保构建工具已安装
    """
    print("检查构建工具...")
    try:
        import build
        print("build 已安装")
    except ImportError:
        print("安装 build...")
        subprocess.run([sys.executable, "-m", "pip", "install", "build"], check=True)

def build_package():
    """构建Python包"""
    # 确保构建工具已安装
    ensure_build_tools()
    
    try:
        # 清理旧的构建文件
        cleanup_build()
        
        # 使用现代 build 工具构建包
        print("使用 modern build 工具构建包...")
        subprocess.run([sys.executable, "-m", "build"], check=True)
        
        print("包构建成功!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"包构建失败: {e}")
        return False

def build_distribution():
    """
    构建项目发行版
    """
    # 确保构建工具已安装
    ensure_build_tools()
    
    project_root = Path(__file__).parent.absolute()
    
    print("开始构建项目发行版...")
    
    # 清理之前的构建文件
    clean_previous_builds(project_root)
    
    # 使用现代 build 工具构建发行版
    print("使用 modern build 工具构建发行版...")
    try:
        subprocess.run([sys.executable, "-m", "build"], check=True, cwd=project_root)
    except subprocess.CalledProcessError as e:
        print(f"构建发行版失败: {e}")
        return False
    
    print("构建完成！发行版文件位于 dist/ 目录中")
    return True

def clean_previous_builds(project_root):
    """
    清理之前的构建文件
    """
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    egg_info_dirs = list(project_root.glob("*.egg-info"))
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        
    for egg_info_dir in egg_info_dirs:
        if egg_info_dir.is_dir():
            shutil.rmtree(egg_info_dir)

def create_requirements_txt():
    """
    创建requirements.txt文件
    """
    requirements_content = """openpyxl==3.1.0
mysql-connector-python==8.0.33
"""
    
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements_content)
    
    print("已创建requirements.txt文件")

def freeze_dependencies():
    """
    冻结当前环境的依赖到requirements.txt
    """
    print("冻结当前环境的依赖...")
    try:
        with open("requirements.txt", "w", encoding="utf-8") as f:
            subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=f, check=True)
        print("依赖已冻结到requirements.txt")
        return True
    except subprocess.CalledProcessError as e:
        print(f"冻结依赖失败: {e}")
        return False

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
    original_cwd = os.getcwd()
    os.chdir(str(dist_dir))
    try:
        freeze_dependencies()
    finally:
        os.chdir(original_cwd)
    
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
        "zr_daily_report.py",
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
    
    # 给予执行权限 (使用跨平台方式)
    sh_path.chmod(0o755)

def show_help():
    """
    显示帮助信息
    """
    help_text = """
ZR Daily Report 构建工具

用法:
    python build_package.py              # 构建标准发行版
    python build_package.py frozen       # 构建包含冻结依赖的发行版
    python build_package.py help         # 显示此帮助信息

功能说明:
    标准发行版: 构建wheel和源码发行包，位于dist目录
    冻结依赖发行版: 创建包含所有项目文件和冻结依赖的完整发行版
"""
    print(help_text)

def cleanup_build():
    """清理构建目录"""
    build_dirs = ["build", "dist", "*.egg-info"]
    for pattern in build_dirs:
        # 使用pathlib处理路径匹配
        if "*" in pattern:
            # 处理通配符模式
            for file_path in Path(".").glob(pattern):
                if file_path.is_dir():
                    shutil.rmtree(file_path)
                else:
                    file_path.unlink()
        else:
            # 处理普通目录/文件
            path = Path(pattern)
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "frozen":
            create_frozen_dist()
        elif sys.argv[1] in ["help", "-h", "--help"]:
            show_help()
        else:
            print(f"未知参数: {sys.argv[1]}")
            show_help()
            sys.exit(1)
    else:
        success = build_distribution()
        if not success:
            sys.exit(1)
