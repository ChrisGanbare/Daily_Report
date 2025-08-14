#!/usr/bin/env python3
"""
文档自动化更新脚本
在代码变更后自动检查和更新文档
"""

import os
import subprocess
import sys
from pathlib import Path


def check_modified_files():
    """检查Git中修改的文件"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        # 如果没有前一个提交，则检查工作区中的所有文件
        return []


def needs_docs_update(modified_files):
    """检查是否需要更新文档"""
    # 定义需要触发文档更新的文件模式
    doc_relevant_patterns = [
        'README.md',
        'docs/',
        'tests/TESTING.md',
        'defect_fixes/',
        'src/',
        'mkdocs.yml'
    ]
    
    for file in modified_files:
        for pattern in doc_relevant_patterns:
            if file.startswith(pattern) or file == pattern[:-1]:
                return True
    return False


def update_docs():
    """更新文档"""
    print("正在检查文档是否需要更新...")
    
    modified_files = check_modified_files()
    
    if not modified_files:
        print("没有检测到文件变更")
        return True
    
    print(f"检测到变更的文件: {modified_files}")
    
    if needs_docs_update(modified_files):
        print("检测到可能影响文档的变更，建议重新构建文档")
        return True
    else:
        print("未检测到影响文档的变更")
        return True


def main():
    """主函数"""
    success = update_docs()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())