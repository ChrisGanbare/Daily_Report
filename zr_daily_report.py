#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ZR Daily Report 主程序
"""

import os
import sys
import traceback
import tkinter as tk

# 添加项目根目录到sys.path，确保能正确导入模块
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 使用绝对导入路径
from src.core.consumption_error_handler import MonthlyConsumptionErrorReportGenerator, DailyConsumptionErrorReportGenerator

# 导入项目模块
from src.cli.argument_parser import parse_arguments, print_usage
from src.ui.mode_selector import show_mode_selection_dialog
from src.core.report_controller import (
    generate_inventory_reports,
    generate_customer_statement,
    generate_refueling_details,
    generate_daily_consumption_error_reports, 
    generate_error_summary_report,
    generate_monthly_consumption_error_reports
)


def main():
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
            args = parse_arguments()
            mode = args.mode
        
        # 根据选择的模式执行相应功能
        if mode == 'inventory':
            generate_inventory_reports()
        elif mode == 'statement':
            generate_customer_statement()
        elif mode == 'refueling':
            # 生成加注明细报表
            generate_refueling_details()
        elif mode == 'daily_consumption':
            # 生成每日消耗误差报表
            generate_daily_consumption_error_reports()
        elif mode == 'monthly_consumption':
            # 调用每月消耗误差报表生成
            generate_monthly_consumption_error_reports()
        elif mode == 'error_summary':
            # 生成误差汇总报表
            generate_error_summary_report()
                
    except Exception as e:
        print(f"主程序执行过程中发生异常: {e}")
        print(f"详细错误信息:\n{traceback.format_exc()}")
        exit(1)


if __name__ == "__main__":
    main()