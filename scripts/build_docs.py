#!/usr/bin/env python3
"""
文档构建脚本
用于自动构建和检查项目文档
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


def check_mkdocs_installed():
    """检查MkDocs是否已安装"""
    returncode, _, _ = run_command("mkdocs --version")
    return returncode == 0


def build_docs():
    """构建文档"""
    print("正在构建文档...")
    
    # 检查MkDocs是否已安装
    if not check_mkdocs_installed():
        print("错误: 未找到 MkDocs，请先安装:")
        print("pip install mkdocs mkdocs-material")
        return False
    
    # 构建文档
    returncode, stdout, stderr = run_command("mkdocs build")
    
    if returncode == 0:
        print("文档构建成功!")
        print("文档已生成到 site/ 目录")
        return True
    else:
        print("文档构建失败:")
        print(stderr)
        return False


def serve_docs():
    """启动本地文档服务器"""
    print("正在启动本地文档服务器...")
    print("请在浏览器中打开 http://127.0.0.1:8000 查看文档")
    print("按 Ctrl+C 停止服务器")
    
    # 检查MkDocs是否已安装
    if not check_mkdocs_installed():
        print("错误: 未找到 MkDocs，请先安装:")
        print("pip install mkdocs mkdocs-material")
        return False
    
    # 启动服务器
    returncode, stdout, stderr = run_command("mkdocs serve")
    
    if returncode != 0:
        print("启动文档服务器失败:")
        print(stderr)
        return False
    
    return True


def check_docs():
    """检查文档配置"""
    print("正在检查文档配置...")
    
    # 检查MkDocs是否已安装
    if not check_mkdocs_installed():
        print("错误: 未找到 MkDocs，请先安装:")
        print("pip install mkdocs mkdocs-material")
        return False
    
    # 检查配置
    returncode, stdout, stderr = run_command("mkdocs build --dirty")
    
    if returncode == 0:
        print("文档配置检查通过!")
        return True
    else:
        print("文档配置检查失败:")
        print(stderr)
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scripts/build_docs.py build    - 构建文档")
        print("  python scripts/build_docs.py serve    - 启动本地服务器")
        print("  python scripts/build_docs.py check    - 检查文档配置")
        return 1
    
    command = sys.argv[1]
    
    if command == "build":
        success = build_docs()
    elif command == "serve":
        success = serve_docs()
    elif command == "check":
        success = check_docs()
    else:
        print(f"未知命令: {command}")
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())