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
from src.cli.mode_selector import show_mode_selection_dialog
from src.core.report_controller import (
    generate_inventory_reports,
    generate_customer_statement,
    _load_config
)


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
            args = parse_arguments()
            mode = args.mode
        
        # 根据选择的模式执行相应功能
        if mode == 'inventory':
            generate_inventory_reports()
        elif mode == 'statement':
            generate_customer_statement()
        elif mode == 'both':
            # 先加载配置文件，避免重复加载
            query_config = _load_config()
            
            # 先执行库存报表功能，并获取设备数据
            devices_data = generate_inventory_reports("库存表处理日志", query_config)
            
            # 如果库存报表生成被取消或失败，直接退出程序
            if devices_data is None:
                # generate_inventory_reports函数已经打印了退出信息，这里不需要重复打印
                return

            # 再执行客户对账单功能，传递设备数据避免重复选择和配置对象避免重复加载
            # 确保只有当devices_data不是None且不为空列表时才传递设备数据
            if devices_data is not None and len(devices_data) > 0:
                # 在both模式下，复用之前已经获取的设备数据和数据库连接，避免重复查询
                generate_customer_statement("对账单处理日志", devices_data, query_config)
            else:
                # 如果没有获取到设备数据，则正常执行（会显示文件选择对话框）
                generate_customer_statement("对账单处理日志", None, query_config)
            
    except Exception as e:
        print(f"主程序执行过程中发生异常: {e}")
        print(f"详细错误信息:\n{traceback.format_exc()}")
        exit(1)


# 保证这个部分没有额外的缩进或空行
if __name__ == "__main__":
    main()
