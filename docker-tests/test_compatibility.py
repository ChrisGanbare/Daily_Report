#!/usr/bin/env python3
"""
测试不同Python版本的兼容性
"""

import subprocess
import sys
import os
from pathlib import Path

def test_python_versions():
    """测试不同Python版本的兼容性"""
    # 定义要测试的Python版本
    python_versions = ["3.8", "3.9", "3.10", "3.11"]
    
    # 检查发布包是否存在
    release_dir = Path("../release")
    if not release_dir.exists():
        print("错误: 未找到release目录")
        return False
    
    zip_files = list(release_dir.glob("zr_daily_report_*.zip"))
    if not zip_files:
        print("错误: 未找到发布包")
        return False
    
    print(f"找到发布包: {zip_files[0].name}")
    
    # 构建Docker镜像
    print("开始构建Docker镜像...")
    for version in python_versions:
        print(f"\n构建Python {version}的Docker镜像...")
        try:
            # 构建镜像
            build_cmd = [
                "docker", "build",
                "--build-arg", f"PYTHON_VERSION={version}",
                "-t", f"zr-daily-report:py{version.replace('.', '')}",
                "-f", "Dockerfile",
                ".."
            ]
            
            result = subprocess.run(
                build_cmd,
                cwd=".",
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✓ Python {version}镜像构建成功")
            else:
                print(f"✗ Python {version}镜像构建失败")
                print(f"错误信息: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"构建Python {version}镜像时出错: {e}")
            return False
    
    # 测试安装脚本
    print("\n开始测试安装脚本...")
    for version in python_versions:
        print(f"\n测试Python {version}兼容性...")
        try:
            # 运行容器测试安装脚本
            test_cmd = [
                "docker", "run",
                "--rm",
                f"zr-daily-report:py{version.replace('.', '')}"
            ]
            
            result = subprocess.run(
                test_cmd,
                cwd=".",
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print(f"✓ Python {version}安装脚本测试通过")
            else:
                print(f"✗ Python {version}安装脚本测试失败")
                print(f"输出: {result.stdout}")
                print(f"错误: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"✗ Python {version}安装脚本测试超时")
            return False
        except Exception as e:
            print(f"测试Python {version}时出错: {e}")
            return False
    
    print("\n🎉 所有Python版本兼容性测试通过!")
    return True

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    success = test_python_versions()
    sys.exit(0 if success else 1)