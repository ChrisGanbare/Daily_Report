#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
跨平台启动脚本
可以在任何设备上运行，无需修改环境变量
"""

import sys
import os
import subprocess

def main():
    # 获取当前脚本所在的目录（即项目根目录）
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 切换到项目目录
    os.chdir(project_dir)
    
    print("正在运行 ZR Daily Report 程序...")
    
    # 检查是否存在虚拟环境
    venv_activate = None
    if os.name == 'nt':  # Windows
        venv_activate = os.path.join(project_dir, '.venv', 'Scripts', 'activate.bat')
    else:  # Unix/Linux/macOS
        venv_activate = os.path.join(project_dir, '.venv', 'bin', 'activate')
    
    # 构建运行命令
    cmd = [sys.executable, "zr_daily_report.py"] + sys.argv[1:]
    
    try:
        # 运行主程序
        result = subprocess.run(cmd, cwd=project_dir)
        
        if result.returncode != 0:
            print("\n程序运行出现错误，请查看上面的错误信息。")
            input("按回车键退出...")
            
    except FileNotFoundError:
        print("错误：找不到Python解释器或主程序文件")
        input("按回车键退出...")
    except Exception as e:
        print(f"运行程序时发生错误: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()