#!/usr/bin/env python3
"""
测试运行脚本
提供多种方式运行测试的便捷脚本
"""

import os
import sys
import subprocess
import argparse


def run_unit_tests():
    """运行单元测试"""
    print("运行单元测试...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests", "-m", "unit", "--verbose"])
    return result.returncode == 0


def run_integration_tests():
    """运行集成测试"""
    print("运行集成测试...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests", "-m", "integration", "--verbose"])
    return result.returncode == 0


def run_all_tests():
    """运行所有测试"""
    print("运行所有测试...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests", "--verbose"])
    return result.returncode == 0


def run_tests_with_coverage():
    """运行测试并生成覆盖率报告"""
    print("运行测试并生成覆盖率报告...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", "tests",
        "--cov=src",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--verbose"
    ])
    return result.returncode == 0


def run_lint():
    """运行代码风格检查"""
    print("运行代码风格检查...")
    result = subprocess.run([sys.executable, "-m", "flake8", "src", "tests"])
    return result.returncode == 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ZR Daily Report 测试运行脚本")
    parser.add_argument(
        "--unit", 
        action="store_true", 
        help="运行单元测试"
    )
    parser.add_argument(
        "--integration", 
        action="store_true", 
        help="运行集成测试"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="运行测试并生成覆盖率报告"
    )
    parser.add_argument(
        "--lint", 
        action="store_true", 
        help="运行代码风格检查"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="运行所有测试（默认）"
    )
    
    args = parser.parse_args()
    
    # 如果没有指定任何选项，则运行所有测试
    if not any([args.unit, args.integration, args.coverage, args.lint]):
        args.all = True
    
    success = True
    
    if args.unit:
        success &= run_unit_tests()
    
    if args.integration:
        success &= run_integration_tests()
    
    if args.coverage:
        success &= run_tests_with_coverage()
    
    if args.lint:
        success &= run_lint()
    
    if args.all:
        success &= run_all_tests()
    
    if success:
        print("\n所有测试运行成功！")
        sys.exit(0)
    else:
        print("\n部分测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()