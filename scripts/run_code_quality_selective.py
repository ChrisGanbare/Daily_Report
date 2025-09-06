#!/usr/bin/env python3
"""
选择性运行代码质量检查的脚本，跳过指定的模块
"""

import subprocess
import sys
import os
from pathlib import Path

def run_mypy():
    """运行mypy检查，使用配置文件排除指定模块"""
    cmd = [
        "python", "-m", "mypy",
        "--config-file", "mypy.ini",
        "src", "tests"
    ]
    
    print("运行mypy检查...")
    print(f"命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0

def run_black():
    """运行black检查（可选）"""
    cmd = ["python", "-m", "black", "--check", "src", "tests"]
    
    print("运行black检查...")
    print(f"命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0

def run_isort():
    """运行isort检查（可选）"""
    cmd = ["python", "-m", "isort", "--check-only", "src", "tests"]
    
    print("运行isort检查...")
    print(f"命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0

def main():
    """主函数"""
    print("选择性代码质量检查")
    print("=" * 50)
    
    # 确保在项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # 检查命令行参数
    skip_black = "--skip-black" in sys.argv
    skip_isort = "--skip-isort" in sys.argv
    skip_mypy = "--skip-mypy" in sys.argv
    
    all_passed = True
    
    # 运行各项检查
    if not skip_black:
        if not run_black():
            all_passed = False
            
    if not skip_isort:
        if not run_isort():
            all_passed = False
            
    if not skip_mypy:
        if not run_mypy():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("所有检查通过!")
        return 0
    else:
        print("某些检查失败，请查看上面的输出。")
        return 1

if __name__ == "__main__":
    sys.exit(main())