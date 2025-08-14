#!/usr/bin/env python3
"""
Script to set up Git hooks for code quality checks.
"""

import os
import stat
import subprocess
from pathlib import Path

def setup_pre_commit_hook():
    """Set up pre-commit hook for code quality checks."""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    hooks_dir = project_root / '.git' / 'hooks'
    
    # 确保hooks目录存在
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Pre-commit hook内容
    pre_commit_content = '''#!/bin/bash
# Pre-commit hook for code quality checks

echo "Running pre-commit code quality checks..."

# 检查必要的工具是否已安装
for tool in black isort flake8 mypy; do
    if ! command -v $tool &> /dev/null; then
        echo "$tool is not installed. Please install it with: pip install $tool"
        exit 1
    fi
done

# 获取暂存区的Python文件
PYTHON_FILES=$(git diff --cached --name-only --diff-filter=ACMR | grep '\.py$' | tr '\\n' ' ')

if [ -z "$PYTHON_FILES" ]; then
    echo "No Python files to check."
    exit 0
fi

echo "Checking files: $PYTHON_FILES"

# 运行代码格式化工具 (会修改文件)
echo "Running black..."
black $PYTHON_FILES

echo "Running isort..."
isort $PYTHON_FILES

# 将修改后的文件重新添加到暂存区
for file in $PYTHON_FILES; do
    git add "$file"
done

# 运行只读检查
echo "Running flake8..."
if ! flake8 $PYTHON_FILES; then
    echo "flake8 checks failed. Please fix the issues before committing."
    exit 1
fi

echo "Running mypy..."
if ! mypy $PYTHON_FILES; then
    echo "mypy checks failed. Please fix the issues before committing."
    exit 1
fi

echo "All pre-commit checks passed!"
'''

    # 写入pre-commit文件
    pre_commit_file = hooks_dir / 'pre-commit'
    with open(pre_commit_file, 'w', encoding='utf-8') as f:
        f.write(pre_commit_content)
    
    # 给予执行权限
    st = os.stat(pre_commit_file)
    os.chmod(pre_commit_file, st.st_mode | stat.S_IEXEC)
    
    print(f"Pre-commit hook installed at {pre_commit_file}")

def setup_commit_msg_hook():
    """Set up commit message hook for commit message validation."""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    hooks_dir = project_root / '.git' / 'hooks'
    
    # Commit message hook内容
    commit_msg_content = '''#!/bin/bash
# Commit message hook for validating commit messages

commit_msg_file=$1
commit_msg=$(cat $commit_msg_file)

# 检查提交信息是否为空
if [ -z "$commit_msg" ]; then
    echo "Error: Commit message is empty."
    exit 1
fi

# 检查提交信息长度
msg_length=${#commit_msg}
if [ $msg_length -lt 10 ]; then
    echo "Error: Commit message is too short (minimum 10 characters)."
    exit 1
fi

# 检查提交信息是否以大写字母开头
first_char=${commit_msg:0:1}
if [[ ! $first_char =~ [A-Z] ]]; then
    echo "Error: Commit message should start with an uppercase letter."
    exit 1
fi

echo "Commit message validation passed!"
'''

    # 写入commit-msg文件
    commit_msg_file = hooks_dir / 'commit-msg'
    with open(commit_msg_file, 'w', encoding='utf-8') as f:
        f.write(commit_msg_content)
    
    # 给予执行权限
    st = os.stat(commit_msg_file)
    os.chmod(commit_msg_file, st.st_mode | stat.S_IEXEC)
    
    print(f"Commit message hook installed at {commit_msg_file}")

def main():
    """Main function to set up Git hooks."""
    print("Setting up Git hooks...")
    setup_pre_commit_hook()
    setup_commit_msg_hook()
    print("Git hooks setup completed!")

if __name__ == "__main__":
    main()