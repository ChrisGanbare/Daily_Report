#!/usr/bin/env python3
"""
创建ZR Daily Report可移植包的脚本
此脚本将创建一个包含所有依赖的完整包，可在其他电脑上直接运行
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
    package_name = "zr_daily_report_portable"
    package_dir = project_root / package_name
    
    print("开始创建可移植包...")
    print(f"项目根目录: {project_root}")
    
    # 删除已存在的包目录
    if package_dir.exists():
        print("删除已存在的包目录...")
        shutil.rmtree(package_dir)
    
    # 创建包目录结构
    print("创建包目录结构...")
    (package_dir / "zr_daily_report").mkdir(parents=True)
    
    print("复制项目文件...")
    # 复制项目文件
    copy_project_files(project_root, package_dir / "zr_daily_report")
    
    print("创建说明文件...")
    # 创建说明文件
    create_readme(package_dir)
    
    print("创建启动脚本...")
    # 创建启动脚本
    create_startup_scripts(package_dir)
    
    print("创建安装脚本...")
    # 创建安装脚本
    create_install_script(package_dir)
    
    print("创建压缩包...")
    # 创建压缩包
    zip_path = project_root / f"{package_name}.zip"
    create_zip_package(package_dir, zip_path)
    
    print(f"打包完成！")
    print(f"可移植包位置: {zip_path}")
    print("\n使用说明:")
    print("1. 将zip文件解压到目标电脑的任意位置")
    print("2. Windows系统: 双击运行 run_report.bat")
    print("3. Linux/macOS系统: 在终端中运行 ./run_report.sh")


def copy_project_files(project_root, target_dir):
    """
    复制项目文件到目标目录
    """
    # 需要复制的目录和文件
    items_to_copy = [
        "src",
        "config",
        "template",
        "data",
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
                print(f"  复制文件: {item}")
        else:
            print(f"  跳过不存在的项目项: {item}")

    # 复制或创建requirements.txt文件
    requirements_src = project_root / "requirements.txt"
    requirements_dst = target_dir / "requirements.txt"
    
    if requirements_src.exists() and requirements_src.stat().st_size > 0:
        # 如果存在非空的requirements.txt，则复制它
        shutil.copy2(requirements_src, requirements_dst)
        print("  复制现有的requirements.txt")
    else:
        # 否则创建一个新的requirements.txt
        create_requirements_file(target_dir)
        print("  创建新的requirements.txt")


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
    result = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"创建虚拟环境失败: {result.stderr}")
        raise RuntimeError("无法创建虚拟环境")


def install_dependencies(package_dir):
    """
    在虚拟环境中安装项目依赖
    """
    # Windows和Unix系统使用不同的激活脚本
    if os.name == "nt":  # Windows
        pip_path = package_dir / "venv" / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        pip_path = package_dir / "venv" / "bin" / "pip"
    
    requirements_path = package_dir / "zr_daily_report" / "requirements.txt"
    
    # 升级pip
    print("  升级pip...")
    subprocess.run([str(pip_path), "install", "--upgrade", "pip"], 
                  check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 安装项目依赖
    print("  安装依赖...")
    subprocess.run([str(pip_path), "install", "-r", str(requirements_path)], 
                  check=True, stdout=subprocess.DEVNULL)
    
    # 安装项目本身
    print("  安装项目...")
    project_path = package_dir / "zr_daily_report"
    subprocess.run([str(pip_path), "install", str(project_path)], 
                  check=True, stdout=subprocess.DEVNULL)


def create_startup_scripts(package_dir):
    """
    创建启动脚本
    """
    # 创建Windows批处理脚本
    bat_content = """@echo off
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
    ps1_content = """# ZR Daily Report 启动脚本

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


def create_readme(package_dir):
    """
    创建说明文件
    """
    readme_content = """# ZR Daily Report 可移植包

这是一个完整的可移植包，包含了运行ZR Daily Report所需的所有文件。

## 安装步骤

1. 在目标计算机上确保已安装Python 3.8或更高版本
2. 双击运行 `install.bat` 脚本
3. 按照提示完成环境安装

## 运行程序

安装完成后，可以通过以下方式运行程序：
- 双击 `run_report.bat` 运行程序
- 或在命令行中执行 `python ZR_Daily_Report.py`

## 项目结构
- `zr_daily_report/` - 项目主目录
- `venv/` - 虚拟环境目录（安装后创建）
- `install.bat` - 安装脚本
- `run_report.bat` - 启动脚本
- `run_report.ps1` - PowerShell启动脚本

## 系统要求
- Windows 7/8/10/11
- Python 3.8或更高版本
- 至少100MB可用磁盘空间

## 注意事项
- 请勿修改目录结构
- 如需重新安装，请删除 `venv` 目录并重新运行 `install.bat`
"""
    
    with open(package_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)


def create_zip_package(package_dir, zip_path):
    """
    创建ZIP压缩包
    """
    if zip_path.exists():
        zip_path.unlink()
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=5) as zipf:
        for root, dirs, files in os.walk(package_dir):
            # 跳过__pycache__目录
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                # 跳过.pyc文件
                if file.endswith('.pyc'):
                    continue
                    
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arc_path)


if __name__ == "__main__":
    try:
        create_portable_package()
        print("\n可移植包创建成功！")
    except Exception as e:
        print(f"\n创建可移植包时发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)