#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ZR Daily Report Generator
中润每日报表生成工具主程序
"""

import argparse
import sys
import os

# 添加项目根目录到sys.path，确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入核心功能模块
from src.core.report_controller import (
    generate_inventory_reports,
    generate_customer_statement,
    generate_both_reports
)
from src.cli.argument_parser import parse_arguments

# 导入文件对话框工具类
from src.ui.filedialog_selector import choose_file, choose_directory  # 导入文件对话框工具类


def main():
    """
    主函数，根据命令行参数或UI选择执行功能
    """
    try:
        # 显示使用说明
        print_usage()
        
        # 检查是否有命令行参数
        if len(sys.argv) == 1:
            # 没有命令行参数，显示模式选择对话框
            mode = show_mode_selection_dialog()
            
            if mode is None:
                print("用户取消操作，程序退出。")
                return
                
            if not mode:
                print("未选择有效模式，程序退出。")
                return
        else:
            # 有命令行参数，使用argparse解析
            parser = argparse.ArgumentParser(description='ZR Daily Report Generator')
            parser.add_argument('--mode', choices=['inventory', 'statement', 'both'], 
                                default='both', help='选择执行模式: inventory(库存报表), statement(客户对账单), both(两者都执行)')
            
            args = parser.parse_args()
            mode = args.mode
        
        # 根据选择的模式执行相应功能
        if mode == 'inventory':
            generate_inventory_reports()
        elif mode == 'statement':
            generate_customer_statement()
        elif mode == 'both':
            generate_both_reports()
            
    except Exception as e:
        print(f"主程序执行过程中发生异常: {e}")
        print(f"详细错误信息:\n{traceback.format_exc()}")
        exit(1)


# 保证这个部分没有额外的缩进或空行
if __name__ == "__main__":
    main()