#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ZR Daily Report 主程序
"""

import argparse
import datetime
import json
import os
import sys
import traceback
import tkinter as tk
from tkinter import ttk

# 添加项目根目录到sys.path，确保能正确导入模块
sys.path.insert(0, os.path.dirname(__file__))

# 导入项目模块
from src.cli.argument_parser import parse_arguments, print_usage
from src.ui.mode_selector import show_mode_selection_dialog
from src.ui.filedialog_selector import choose_file, choose_directory
from src.core.report_controller import (
    generate_inventory_reports,
    generate_customer_statement,
    generate_both_reports,
    _load_config
)
from src.core.db_handler import DatabaseHandler
from src.core.inventory_handler import InventoryReportGenerator
from src.core.statement_handler import CustomerStatementGenerator
from src.core.file_handler import FileHandler
from src.utils.date_utils import validate_csv_data
from src.utils.config_handler import ConfigHandler

# 导入mysql.connector
import mysql.connector


def get_user_input(prompt):
    root = tk.Tk()
    root.withdraw()
    result = tk.simpledialog.askstring("Input", prompt)
    return result.get()


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
        elif mode == 'both':
            # 使用优化的综合报表生成功能
            generate_both_reports()
                
    except Exception as e:
        print(f"主程序执行过程中发生异常: {e}")
        print(f"详细错误信息:\n{traceback.format_exc()}")
        exit(1)


if __name__ == "__main__":
    main()
