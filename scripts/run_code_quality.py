#!/usr/bin/env python3
"""
代码质量检查脚本
用于手动运行所有代码质量检查工具，无需通过Git提交
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            shell=True,
            cwd=cwd
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def check_tool_installed(tool_name):
    """检查工具是否已安装"""
    returncode, _, _ = run_command(f"where {tool_name}")
    return returncode == 0


def find_project_root():
    """查找项目根目录（包含src和tests目录的目录）"""
    current_path = Path(__file__).parent.absolute()
    
    # 向上搜索直到找到包含src和tests目录的目录
    for parent in [current_path] + list(current_path.parents):
        src_dir = parent / "src"
        tests_dir = parent / "tests"
        if src_dir.is_dir() and tests_dir.is_dir():
            return parent
    
    # 如果没找到，返回脚本所在目录的父目录
    return current_path.parent


def run_quality_checks():
    """运行所有代码质量检查"""
    # 查找项目根目录
    project_root = find_project_root()
    print(f"项目根目录: {project_root}")
    
    # 确认src和tests目录存在
    src_dir = project_root / "src"
    tests_dir = project_root / "tests"
    
    if not src_dir.is_dir():
        print(f"错误: 找不到src目录 {src_dir}")
        return False
    
    if not tests_dir.is_dir():
        print(f"错误: 找不到tests目录 {tests_dir}")
        return False
    
    print("开始运行代码质量检查...")
    print("=" * 50)
    
    # 定义要运行的检查工具和命令
    tools = [
        {
            "name": "black",
            "command": f"black --check {src_dir} {tests_dir}",
            "description": "代码格式检查"
        },
        {
            "name": "isort",
            "command": f"isort --check-only {src_dir} {tests_dir}",
            "description": "导入排序检查"
        },
        {
            "name": "mypy",
            "command": f"mypy {src_dir} {tests_dir}",
            "description": "类型检查"
        }
    ]
    
    failed_tools = []
    passed_tools = []
    
    for tool in tools:
        tool_name = tool["name"]
        command = tool["command"]
        description = tool["description"]
        
        print(f"\n正在运行 {tool_name} ({description})...")
        print("-" * 30)
        
        # 检查工具是否已安装
        if not check_tool_installed(tool_name):
            print(f"警告: {tool_name} 未安装，请先运行 'pip install {tool_name}'")
            failed_tools.append(tool_name)
            continue
        
        # 运行检查
        returncode, stdout, stderr = run_command(command, cwd=str(project_root))
        
        if returncode == 0:
            print(f"✓ {tool_name} 检查通过")
            passed_tools.append(tool_name)
        else:
            print(f"✗ {tool_name} 检查失败")
            if stdout.strip():
                print("输出:")
                print(stdout)
            if stderr.strip():
                print("错误:")
                print(stderr)
            failed_tools.append(tool_name)
    
    # 输出总结
    print("\n" + "=" * 50)
    print("代码质量检查总结:")
    print(f"通过: {len(passed_tools)} 个")
    for tool in passed_tools:
        print(f"  ✓ {tool}")
    
    print(f"失败: {len(failed_tools)} 个")
    for tool in failed_tools:
        print(f"  ✗ {tool}")
    
    if failed_tools:
        print(f"\n以下工具检查失败: {', '.join(failed_tools)}")
        print("请修复问题后重新运行检查。")
        return False
    else:
        print("\n所有代码质量检查通过!")
        return True


def install_quality_tools():
    """安装代码质量检查工具"""
    print("正在安装代码质量检查工具...")
    
    tools = ["black", "isort", "mypy"]
    for tool in tools:
        print(f"安装 {tool}...")
        returncode, stdout, stderr = run_command(f"pip install {tool}")
        if returncode != 0:
            print(f"安装 {tool} 失败:")
            if stderr:
                print(stderr)
            return False
        else:
            print(f"✓ {tool} 安装成功")
    
    print("所有代码质量检查工具安装完成!")
    return True


def main():
    """主函数"""
    print("ZR Daily Report 代码质量检查工具")
    print("================================")
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--install":
            # 安装工具
            if install_quality_tools():
                print("工具安装成功，现在可以运行代码质量检查了。")
            else:
                print("工具安装失败。")
                sys.exit(1)
        elif sys.argv[1] == "--help":
            # 显示帮助信息
            print("使用方法:")
            print("  python scripts/run_code_quality.py          # 运行代码质量检查")
            print("  python scripts/run_code_quality.py --install # 安装代码质量检查工具")
            print("  python scripts/run_code_quality.py --help    # 显示帮助信息")
            return
        else:
            print(f"未知参数: {sys.argv[1]}")
            print("使用 --help 查看帮助信息")
            sys.exit(1)
    
    # 运行代码质量检查
    success = run_quality_checks()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()