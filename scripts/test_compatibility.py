#!/usr/bin/env python3
"""
依赖版本兼容性测试脚本

此脚本用于在依赖版本升级前后执行兼容性测试，
确保核心功能在不同版本下能够正常工作。
"""

import subprocess
import sys
import os
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_command(command, cwd=None):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd or project_root,
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout, result.stderr, 0
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode

def check_dependencies():
    """检查关键依赖的当前版本"""
    print("检查关键依赖版本...")
    
    dependencies = [
        "openpyxl",
        "mysql-connector-python", 
        "pandas"
    ]
    
    for dep in dependencies:
        try:
            result, _, code = run_command(f"python -c \"import {dep.split('-')[0]}; print('{dep}:', {dep.split('-')[0]}.__version__)\"")
            if code == 0:
                print(f"  {result.strip()}")
            else:
                print(f"  无法获取 {dep} 版本信息")
        except Exception as e:
            print(f"  检查 {dep} 版本时出错: {e}")

def run_compatibility_tests():
    """运行依赖兼容性测试"""
    print("\n运行依赖版本兼容性测试...")
    
    # 运行依赖兼容性测试
    stdout, stderr, code = run_command("python -m pytest tests/test_dependency_compatibility.py -v")
    
    if code == 0:
        print("依赖兼容性测试通过!")
        print(stdout)
        return True
    else:
        print("依赖兼容性测试失败!")
        print("STDOUT:")
        print(stdout)
        print("STDERR:")
        print(stderr)
        return False

def run_all_tests():
    """运行所有测试"""
    print("\n运行所有测试...")
    
    stdout, stderr, code = run_command("python -m pytest tests/ -v")
    
    if code == 0:
        print("所有测试通过!")
        return True
    else:
        print("部分测试失败!")
        print("STDOUT:")
        print(stdout)
        print("STDERR:")
        print(stderr)
        return False

def main():
    """主函数"""
    print("ZR Daily Report 依赖版本兼容性测试工具")
    print("=" * 50)
    
    # 检查当前依赖版本
    check_dependencies()
    
    # 运行依赖兼容性测试
    compatibility_passed = run_compatibility_tests()
    
    if not compatibility_passed:
        print("\n警告: 依赖兼容性测试未通过，请检查依赖版本是否正确!")
        sys.exit(1)
    
    # 询问是否运行所有测试
    run_all = input("\n是否运行所有测试? (y/N): ").strip().lower()
    if run_all == 'y':
        all_passed = run_all_tests()
        if not all_passed:
            print("\n警告: 部分测试未通过!")
            sys.exit(1)
    
    print("\n依赖版本兼容性检查完成!")

if __name__ == "__main__":
    main()