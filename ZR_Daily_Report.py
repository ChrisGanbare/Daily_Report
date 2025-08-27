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

<<<<<<< HEAD
# 导入mysql.connector
import mysql.connector


def print_usage():
    """
    打印使用说明
    """
    print("ZR Daily Report Generator 使用说明:")
    print("=" * 50)
    print("命令行参数选项:")
    print("  --mode inventory    只生成库存报表")
    print("  --mode statement    只生成客户对账单")
    print("  --mode both         同时生成库存报表和客户对账单（默认）")
    print()
    print("示例:")
    print("  python ZR_Daily_Report.py")
    print("  python ZR_Daily_Report.py --mode inventory")
    print("  python ZR_Daily_Report.py --mode statement")
    print("  python ZR_Daily_Report.py --mode both")
    print("=" * 50)


def load_config():
    """
    加载配置文件，优先加载加密配置文件，如果不存在则加载明文配置文件
    """
    CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'config')
    config_file_encrypted = os.path.join(CONFIG_DIR, 'query_config_encrypted.json')
    config_file_plain = os.path.join(CONFIG_DIR, 'query_config.json')
    
    # 优先尝试加载加密配置文件
    if os.path.exists(config_file_encrypted):
        try:
            print(f"尝试读取加密配置文件: {config_file_encrypted}")
            # 使用ConfigHandler加载加密配置
            config_handler = ConfigHandler(CONFIG_DIR)
            config = config_handler.load_encrypted_config(config_file_encrypted)
            print("成功加载加密配置文件")
            return config
        except Exception as e:
            print(f"加载加密配置文件失败: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            # 如果加密配置加载失败，继续尝试加载明文配置
    
    # 如果加密配置文件不存在或加载失败，尝试加载明文配置文件
    if os.path.exists(config_file_plain):
        try:
            print(f"尝试读取明文配置文件: {config_file_plain}")
            with open(config_file_plain, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("成功加载明文配置文件")
            return config
        except Exception as e:
            print(f"加载明文配置文件失败: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise Exception("无法加载任何配置文件")
    
    raise Exception("未找到有效的配置文件")

def _save_error_log(log_messages, error_details, log_filename_prefix):
    """
    保存错误日志到文件
    
    Args:
        log_messages (list): 日志消息列表
        error_details (dict): 错误详细信息
        log_filename_prefix (str): 日志文件名前缀
    """
    error_time = datetime.datetime.now()
    # 创建统一的错误日志目录
    error_log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(error_log_dir):
        os.makedirs(error_log_dir)
    
    # 使用指定的命名格式，包含error_log_前缀
    error_log_file = os.path.join(
        error_log_dir, 
        f"error_log_{log_filename_prefix}_{error_time.strftime('%Y%m%d_%H%M%S')}.txt"
    )
    try:
        with open(error_log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_messages))
            if 'error' in error_details:
                f.write(f"\n\n{error_details.get('error_type', 'Error')}: {error_details['error']}\n")
            if 'error_code' in error_details:
                f.write(f"错误代码: {error_details['error_code']}\n")
            if 'traceback' in error_details:
                f.write(f"详细错误信息:\n{error_details['traceback']}")
        print(f"{error_details.get('log_description', '错误日志')}已保存到: {error_log_file}")
    except Exception as log_e:
        print(f"保存{error_details.get('log_description', '日志文件')}失败: {log_e}")

def _handle_db_connection_error(log_messages, error, error_type="MySQL错误"):
    """
    处理数据库连接错误
    
    Args:
        log_messages (list): 日志消息列表
        error (Exception): 错误对象
        error_type (str): 错误类型描述
    """
    error_msg = f"数据库连接失败 ({error_type}): {error}"
    print(error_msg)
    if hasattr(error, 'errno'):
        print(f"错误代码: {error.errno}")
    print(f"详细错误信息:\n{traceback.format_exc()}")
    log_messages.append(error_msg)
    log_messages.append("")
    
    # 生成错误日志文件
    error_details = {
        'error': error,
        'error_type': error_type,
        'traceback': traceback.format_exc(),
        'log_description': '数据库连接错误日志'
    }
    if hasattr(error, 'errno'):
        error_details['error_code'] = error.errno
    
    _save_error_log(log_messages, error_details, "数据库连接错误日志")

def generate_inventory_reports(log_prefix="库存表处理日志", query_config=None):
    """
    专门用于生成库存报表
    """
    # 初始化日志列表
    log_messages = []
    failed_devices = []
    
    # 记录程序开始时间
    start_time = datetime.datetime.now()
    log_messages.append(f"程序开始执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append("")  # 添加空行分隔
    
    print("=" * 50)
    print("ZR Daily Report - 设备库存表生成功能")
    print("=" * 50)
    print("\n" + "-" * 50)
    print("步骤1：读取配置文件和设备信息（库存报表）")
    print("-" * 50)
    
    try:
        # 初始化处理器
        file_handler = FileHandler()
        
        # 如果没有传入配置，则读取查询配置文件
        if query_config is None:
            query_config = load_config()
        
        # 提取数据库配置和SQL模板
        db_config = query_config.get('db_config', {})
        sql_templates = query_config.get('sql_templates', {})
        
        # 获取SQL查询模板
        device_query_template = sql_templates.get('device_id_query')
        customer_query_template = sql_templates.get('customer_query')
        
        # 如果某些模板未在配置文件中定义，则使用默认值
        if not device_query_template:
            device_query_template = "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s ORDER BY create_time DESC LIMIT 1"
        
        if not customer_query_template:
            customer_query_template = "SELECT customer_name FROM oil.t_customer WHERE id = %s"
        
        # 显示文件选择对话框，让用户选择设备信息CSV文件
        csv_file = choose_file(
            title="选择设备信息CSV文件",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=os.path.join(os.path.expanduser("~"), "Desktop")  # 修改为桌面路径
        )
        
        if not csv_file:
            print("未选择设备信息文件，程序退出。")
            return None
        
        # 读取设备信息
        devices = file_handler.read_devices_from_csv(csv_file)
        if not devices:
            print("未能读取设备信息。")
            return None
        
        # 验证设备信息
        valid_devices = []
        for device in devices:
            if validate_csv_data(device):
                valid_devices.append(device)
            else:
                print(f"设备信息验证失败: {device}")
        
        if not valid_devices:
            print("没有有效的设备信息，请检查设备文件内容。")
            return None
        
        print(f"成功读取 {len(valid_devices)} 个有效设备信息。")
        log_messages.append(f"成功读取 {len(valid_devices)} 个有效设备信息。")
        log_messages.append("")  # 添加空行分隔
        
        # 初始化数据库连接
        db_handler = DatabaseHandler(db_config)
        connection = None
        try:
            print("开始数据库连接...")
            connection = db_handler.connect()
            print("数据库连接对象创建成功")
        except mysql.connector.Error as err:
            _handle_db_connection_error(log_messages, err, "MySQL错误")
            exit(1)
        except Exception as e:
            _handle_db_connection_error(log_messages, e, "未知错误")
            exit(1)
        except BaseException as e:
            error_msg = f"数据库连接过程中发生严重错误: {e}"
            print(error_msg)
            print(f"错误类型: {type(e)}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            log_messages.append(error_msg)
            log_messages.append("")
            
            # 生成错误日志文件
            error_details = {
                'error': e,
                'error_type': '严重错误',
                'traceback': traceback.format_exc(),
                'log_description': '数据库连接严重错误日志'
            }
            _save_error_log(log_messages, error_details, "数据库连接严重错误日志")
            
            exit(1)

        # 显示目录选择对话框，让用户选择输出目录
        output_dir = choose_directory(title="选择保存目录（设备库存报表）", initialdir=os.path.join(os.path.expanduser("~"), "Desktop"))
        if not output_dir:
            print("未选择输出目录，程序退出。")
            connection.close()
            return None
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "-" * 50)
        print("步骤2：生成库存报表")
        print("-" * 50)
        
        # 用于存储处理失败的设备
        failed_devices = []
        
        # 处理每个设备
        for i, device in enumerate(valid_devices, 1):
            device_code = device['device_code']
            start_date = device['start_date']
            end_date = device['end_date']
            
            print(f"\n处理第 {i} 个设备 ({device_code})...")
            log_messages.append(f"处理设备 {device_code}...")
            
            try:
                # 获取设备ID和客户ID
                device_info = db_handler.get_latest_device_id_and_customer_id(device_code, device_query_template)
                if not device_info:
                    error_msg = f"  无法找到设备 {device_code} 的信息"
                    print(error_msg)
                    log_messages.append(error_msg)
                    failed_devices.append(device_code)
                    continue
                    
                device_id, customer_id = device_info
                print(f"  设备ID: {device_id}, 客户ID: {customer_id}")
                
                # 获取客户名称
                customer_name = db_handler.get_customer_name_by_device_code(device_code)
                print(f"  客户名称: {customer_name}")
                
                # 生成查询语句
                inventory_query_template = sql_templates.get('inventory_query')
                if not inventory_query_template:
                    inventory_query_template = "SELECT * FROM oil.t_inventory WHERE device_id = %s AND create_time BETWEEN %s AND %s ORDER BY create_time DESC"
                end_condition = f"{end_date} 23:59:59"
                query = inventory_query_template.format(
                    device_id=device_id,
                    start_date=start_date,
                    end_condition=end_condition
                )
                
                # 获取库存数据
                print("  正在获取库存数据...")
                data, columns, raw_data = db_handler.fetch_inventory_data(device_id, inventory_query_template, start_date, end_date)
                
                if not data:
                    print(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                    log_messages.append(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                
                # 保存设备数据供后续使用
                # 检查是否存在油品名称列
                if not raw_data or '油品名称' not in columns:
                    error_msg = f"  错误：设备 {device_code} 的数据中未找到油品名称列，请检查数据库查询结果"
                    print(error_msg)
                    log_messages.append(error_msg)
                    failed_devices.append(device_code)
                    continue
                
                # 获取第一条记录的油品名称作为该设备的油品名称
                # 注意：这里假设一个设备只使用一种油品，这是业务上的合理假设
                first_row = raw_data[0]
                if isinstance(first_row, dict):
                    oil_name = first_row.get('油品名称')
                else:
                    # 如果是元组或列表形式，根据列名索引获取油品名称
                    oil_name_index = columns.index('油品名称')
                    oil_name = first_row[oil_name_index] if oil_name_index < len(first_row) else None
                
                # 检查油品名称是否有效
                if not oil_name:
                    error_msg = f"  错误：设备 {device_code} 的数据中油品名称为空，请检查数据库数据完整性"
                    print(error_msg)
                    log_messages.append(error_msg)
                    failed_devices.append(device_code)
                    continue
                
                device_data = {
                    'device_code': device_code,
                    'oil_name': oil_name,  # 从数据库查询结果中获取油品名称
                    'data': data,
                    'raw_data': raw_data,
                    'columns': columns,
                    'customer_name': customer_name,
                    'customer_id': customer_id  # 添加客户ID用于高性能分组
                }
                
                # 生成Excel文件
                inventory_handler = InventoryReportGenerator()
                # 替换日期中的非法字符，确保文件名合法
                safe_start_date = start_date.replace("/", "-").replace("\\", "-")
                safe_end_date = end_date.replace("/", "-").replace("\\", "-")
                output_filename = f"{device_code}_{safe_start_date}_to_{safe_end_date}_库存报表.xlsx"
                output_filepath = os.path.join(output_dir, output_filename)
                
                try:
                    # 处理不同格式的日期字符串
                    def parse_date(date_string):
                        # 尝试多种日期格式
                        formats = ['%Y-%m-%d', '%Y/%m/%d']
                        for fmt in formats:
                            try:
                                parsed_date = datetime.datetime.strptime(date_string, fmt).date()
                                return parsed_date
                            except ValueError:
                                continue
                        # 如果所有格式都失败，则抛出异常
                        raise ValueError(f"无法解析日期格式: {date_string}")
                    
                    inventory_handler.generate_inventory_report_with_chart(
                        inventory_data=data,
                        output_file_path=output_filepath,
                        device_code=device_code,
                        start_date=parse_date(start_date),
                        end_date=parse_date(end_date),
                        oil_name=oil_name  # 添加油品名称参数
                    )
                    success_msg = f"  成功生成库存报表: {output_filepath}"
                    print(success_msg)
                    log_messages.append(success_msg)
                except Exception as e:
                    error_msg = f"  生成库存报表失败: {e}"
                    print(error_msg)
                    print(f"详细错误信息:\n{traceback.format_exc()}")
                    log_messages.append(error_msg)
                    failed_devices.append(device_code)
                    continue
                    
            except Exception as e:
                error_msg = f"  处理设备 {device_code} 时发生错误: {e}"
                print(error_msg)
                print(f"详细错误信息:\n{traceback.format_exc()}")
                log_messages.append(error_msg)
                failed_devices.append(device_code)
                continue
        
        # 记录程序结束时间
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        log_messages.append("")
        log_messages.append(f"程序结束执行时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log_messages.append(f"总执行时间: {duration}")
        
        # 记录失败设备
        if failed_devices:
            log_messages.append("")
            log_messages.append(f"失败设备列表: {', '.join(failed_devices)}")
        
        # 保存日志文件
        end_time = datetime.datetime.now()
        log_messages.append(f"程序结束执行时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log_messages.append(f"程序总执行时间: {end_time - start_time}")
        log_messages.append("")  # 添加空行分隔

        log_file = os.path.join(output_dir, f"程序执行日志_{start_time.strftime('%Y%m%d_%H%M%S')}.txt")
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                for message in log_messages:
                    f.write(message + '\n')
            log_save_msg = f"程序执行日志已保存至: {os.path.basename(log_file)}"
            print(log_save_msg)
            log_messages.append(log_save_msg)
            log_messages.append("")  # 添加空行分隔
        except Exception as e:
            log_error_msg = f"保存日志文件时出错: {e}"
            print(log_error_msg)
            log_messages.append(log_error_msg)
            log_messages.append("")  # 添加空行分隔
        
        print("\n库存报表生成功能执行完毕！")
        try:
            if connection and connection.is_connected():
                connection.close()
                print("数据库连接已关闭")
        except Exception as e:
            print(f"关闭数据库连接时发生错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
        
        # 返回有效的设备数据，供后续使用
        return valid_devices
        
    except Exception as e:
        error_msg = f"库存报表生成过程中发生未处理异常: {e}"
        print(error_msg)
        print(f"详细错误信息:\n{traceback.format_exc()}")
        log_messages.append(error_msg)
        
        # 生成错误日志文件
        error_details = {
            'error': e,
            'traceback': traceback.format_exc(),
            'log_description': '错误日志'
        }
        _save_error_log(log_messages, error_details, "错误日志")
        
        # 确保数据库连接关闭
        try:
            if 'connection' in locals() and connection.is_connected():
                connection.close()
        except:
            pass
        
        exit(1)

def generate_customer_statement(log_prefix="对账单处理日志", devices_data=None, query_config=None):
    """
    专门用于生成客户对账单
    """
    # 初始化日志列表
    log_messages = []
    failed_devices = []
    
    # 记录程序开始时间
    start_time = datetime.datetime.now()
    log_messages.append(f"程序开始执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append("")  # 添加空行分隔
    
    print("=" * 50)
    print("ZR Daily Report - 客户对账单生成功能")
    print("=" * 50)
    
    try:
        # 如果传入了设备数据，则不需要重新选择文件
        if devices_data:
            valid_devices = devices_data
            print("\n" + "-" * 50)
            print("步骤1：使用缓存数据（客户对账单）")
            print("-" * 50)
            log_messages.append(f"使用已提供的设备数据，设备数量: {len(valid_devices)}")
        else:
            print("\n" + "-" * 50)
            print("步骤1：读取配置文件和设备信息（客户对账单）")
            print("-" * 50)
            
            # 显示文件选择对话框，让用户选择设备信息CSV文件
            csv_file = choose_file(
                title="选择设备信息CSV文件",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=os.path.join(os.path.expanduser("~"), "Desktop")  # 修改为桌面路径
            )
            
            if not csv_file:
                print("未选择文件，程序退出。")
                return
            
            log_messages.append(f"选择的设备信息文件: {csv_file}")
            
            # 读取设备信息
            try:
                file_handler = FileHandler()
                devices = file_handler.read_devices_from_csv(csv_file)
                valid_devices = [d for d in devices if validate_csv_data(d)]
                log_messages.append(f"总共读取设备数量: {len(devices)}")
                log_messages.append(f"有效设备数量: {len(valid_devices)}")
            except Exception as e:
                error_msg = f"读取设备信息失败: {e}"
                print(error_msg)
                print(f"详细错误信息:\n{traceback.format_exc()}")
                log_messages.append(error_msg)
                log_messages.append("")
                exit(1)
            
            if not valid_devices:
                error_msg = "没有有效的设备信息，请检查CSV文件格式。"
                print(error_msg)
                log_messages.append(error_msg)
                log_messages.append("")
                exit(1)
        
        # 加载数据库配置
        try:
            # 如果没有传入配置，则加载配置
            if query_config is None:
                query_config = load_config()
            db_config = query_config['db_config']
            inventory_query_template = query_config['sql_templates']['inventory_query']
            device_query_template = query_config['sql_templates']['device_id_query']
            customer_query_template = query_config['sql_templates']['customer_query']
        except Exception as e:
            error_msg = f"加载配置失败: {e}"
            print(error_msg)
            print(f"详细错误信息:\n{traceback.format_exc()}")
            log_messages.append(error_msg)
            log_messages.append("")
            exit(1)
        
        # 连接数据库
        connection = None
        try:
            print("开始数据库连接...")
            db_handler = DatabaseHandler(db_config)
            connection = db_handler.connect()
            log_messages.append("数据库连接成功")
        except mysql.connector.Error as err:
            _handle_db_connection_error(log_messages, err, "MySQL错误")
            exit(1)
        except Exception as e:
            _handle_db_connection_error(log_messages, e, "未知错误")
            exit(1)
        except BaseException as e:
            error_msg = f"数据库连接过程中发生严重错误: {e}"
            print(error_msg)
            print(f"错误类型: {type(e)}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            log_messages.append(error_msg)
            log_messages.append("")
            
            # 生成错误日志文件
            error_details = {
                'error': e,
                'error_type': '严重错误',
                'traceback': traceback.format_exc(),
                'log_description': '数据库连接严重错误日志'
            }
            _save_error_log(log_messages, error_details, "数据库连接严重错误日志")
            
            exit(1)

        # 显示目录选择对话框，让用户选择输出目录
        output_dir = choose_directory(title="选择保存目录（客户对账单）", initialdir=os.path.join(os.path.expanduser("~"), "Desktop"))
        if not output_dir:
            print("未选择输出目录，程序退出。")
            connection.close()
            return
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "-" * 50)
        print("步骤2：生成客户对账单")
        print("-" * 50)
        
        # 用于存储所有设备数据，供生成对账单使用
        all_devices_data = []
        failed_devices = []
        
        # 处理每个设备
        for i, device in enumerate(valid_devices, 1):
            device_code = device['device_code']
            start_date = device['start_date']
            end_date = device['end_date']
            
            print(f"\n处理第 {i} 个设备 ({device_code})...")
            log_messages.append(f"处理设备 {device_code}...")
            
            try:
                # 获取设备ID和客户ID
                device_info = db_handler.get_latest_device_id_and_customer_id(device_code, device_query_template)
                if not device_info:
                    error_msg = f"  无法找到设备 {device_code} 的信息"
                    print(error_msg)
                    log_messages.append(error_msg)
                    failed_devices.append(device_code)
                    continue
                    
                device_id, customer_id = device_info
                print(f"  设备ID: {device_id}, 客户ID: {customer_id}")
                
                # 获取客户名称
                customer_name = db_handler.get_customer_name_by_device_code(device_code)
                print(f"  客户名称: {customer_name}")
                
                # 生成查询语句
                end_condition = f"{end_date} 23:59:59"
                query = inventory_query_template.format(
                    device_id=device_id,
                    start_date=start_date,
                    end_condition=end_condition
                )
                
                # 获取库存数据
                print("  正在获取库存数据...")
                data, columns, raw_data = db_handler.fetch_inventory_data(device_id, inventory_query_template, start_date, end_date)
                
                # 获取对账单每日用量数据
                print("  正在获取对账单每日用量数据...")
                daily_usage_data, _, _ = db_handler.fetch_daily_usage_data(device_id, inventory_query_template, start_date, end_date)
                
                # 获取对账单每月用量数据
                print("  正在获取对账单每月用量数据...")
                monthly_usage_data, _, _ = db_handler.fetch_monthly_usage_data(device_id, inventory_query_template, start_date, end_date)
                
                if not data:
                    print(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                    log_messages.append(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                
                # 保存设备数据供后续使用
                # 检查是否存在油品名称列
                if not raw_data or '油品名称' not in columns:
                    error_msg = f"  错误：设备 {device_code} 的数据中未找到油品名称列，请检查数据库查询结果"
                    print(error_msg)
                    log_messages.append(error_msg)
                    failed_devices.append(device_code)
                    continue
                
                # 获取第一条记录的油品名称作为该设备的油品名称
                # 注意：这里假设一个设备只使用一种油品，这是业务上的合理假设
                first_row = raw_data[0]
                if isinstance(first_row, dict):
                    oil_name = first_row.get('油品名称')
                else:
                    # 如果是元组或列表形式，根据列名索引获取油品名称
                    oil_name_index = columns.index('油品名称')
                    oil_name = first_row[oil_name_index] if oil_name_index < len(first_row) else None
                
                # 检查油品名称是否有效
                if not oil_name:
                    error_msg = f"  错误：设备 {device_code} 的数据中油品名称为空，请检查数据库数据完整性"
                    print(error_msg)
                    log_messages.append(error_msg)
                    failed_devices.append(device_code)
                    continue
                
                device_data = {
                    'device_code': device_code,
                    'oil_name': oil_name,  # 从数据库查询结果中获取油品名称
                    'data': data,
                    'daily_usage_data': daily_usage_data,  # 对账单每日用量数据
                    'monthly_usage_data': monthly_usage_data,  # 对账单每月用量数据
                    'raw_data': raw_data,
                    'columns': columns,
                    'customer_name': customer_name,
                    'customer_id': customer_id  # 添加客户ID用于高性能分组
                }
                all_devices_data.append(device_data)
                
            except Exception as e:
                error_msg = f"  处理设备 {device_code} 时发生错误: {e}"
                print(error_msg)
                print(f"详细错误信息:\n{traceback.format_exc()}")
                log_messages.append(error_msg)
                failed_devices.append(device_code)
                continue
        
        # 生成对账单
        if all_devices_data:
            # 按客户ID对设备进行分组（使用客户ID比客户名称更准确且性能更好）
            customers_data = {}
            for device_data in all_devices_data:
                customer_id = device_data['customer_id']
                customer_name = device_data['customer_name']
                # 使用客户ID作为键，但保存客户名称用于文件命名
                if customer_id not in customers_data:
                    customers_data[customer_id] = {
                        'customer_name': customer_name,
                        'devices': []
                    }
                customers_data[customer_id]['devices'].append(device_data)
            
            # 初始化日期变量
            start_date_obj = None
            end_date_obj = None
            formatted_start_date = None
            formatted_end_date = None
            
            # 为每个客户生成对账单
            for customer_id, customer_info in customers_data.items():
                customer_name = customer_info['customer_name']
                customer_devices = customer_info['devices']
                
                print(f"\n为客户 {customer_name} (ID: {customer_id}) 生成对账单...")
                log_messages.append(f"为客户 {customer_name} (ID: {customer_id}) 生成对账单...")
                
                # 获取日期范围（使用第一个设备的日期范围）
                if not start_date_obj or not end_date_obj:
                    start_date = valid_devices[0]['start_date']
                    end_date = valid_devices[0]['end_date']
                    
                    # 尝试多种日期格式
                    date_formats = ['%Y-%m-%d', '%Y/%m/%d']
                    for fmt in date_formats:
                        try:
                            start_date_obj = datetime.datetime.strptime(start_date, fmt).date()
                            end_date_obj = datetime.datetime.strptime(end_date, fmt).date()
                            break
                        except ValueError:
                            continue
                    
                    if start_date_obj is None or end_date_obj is None:
                        raise ValueError(f"无法解析日期格式: start_date='{start_date}', end_date='{end_date}'")
                    
                    # 格式化日期用于文件名（使用统一格式）
                    formatted_start_date = start_date_obj.strftime('%Y-%m-%d')
                    formatted_end_date = end_date_obj.strftime('%Y-%m-%d')
                
                # 生成对账单文件名
                # 如果是跨月情况，使用结束日期的年月命名
                if start_date_obj.month != end_date_obj.month:
                    statement_filename = f"{customer_name}{end_date_obj.strftime('%Y年%m月')}对账单.xlsx"
                else:
                    statement_filename = f"{customer_name}{start_date_obj.strftime('%Y年%m月')}对账单.xlsx"
                
                statement_file = os.path.join(output_dir, statement_filename)
                
                # 生成对账单
                statement_generator = CustomerStatementGenerator()
                try:
                    statement_generator.generate_customer_statement_from_template(
                        customer_devices, statement_file, customer_name, 
                        start_date_obj, end_date_obj
                    )
                    print(f"成功生成对账单: {statement_file}")
                    log_messages.append(f"成功生成对账单: {statement_file}")
                except Exception as e:
                    error_msg = f"生成对账单失败: {e}"
                    print(error_msg)
                    print(f"详细错误信息:\n{traceback.format_exc()}")
                    log_messages.append(error_msg)
        
        # 记录程序结束时间
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        log_messages.append("")
        log_messages.append(f"程序结束执行时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log_messages.append(f"总执行时间: {duration}")
        
        # 记录失败设备
        if failed_devices:
            log_messages.append("")
            log_messages.append(f"失败设备列表: {', '.join(failed_devices)}")
        
        # 生成日志文件
        log_file = os.path.join(output_dir, f"{log_prefix}_{start_time.strftime('%Y%m%d_%H%M%S')}.txt")
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_messages))
            print(f"\n日志文件已保存到: {log_file}")
        except Exception as e:
            print(f"保存日志文件失败: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
        
        print("\n客户对账单生成功能执行完毕！")
        try:
            if connection and connection.is_connected():
                connection.close()
                print("数据库连接已关闭")
        except Exception as e:
            print(f"关闭数据库连接时发生错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")

    except Exception as e:
        error_msg = f"客户对账单生成过程中发生未处理异常: {e}"
        print(error_msg)
        print(f"详细错误信息:\n{traceback.format_exc()}")
        log_messages.append(error_msg)
        
        # 生成错误日志文件
        error_details = {
            'error': e,
            'traceback': traceback.format_exc(),
            'log_description': '错误日志'
        }
        _save_error_log(log_messages, error_details, "错误日志")
        
        # 确保数据库连接关闭
        try:
            if 'connection' in locals() and connection.is_connected():
                connection.close()
        except:
            pass
        
        exit(1)

def show_mode_selection_dialog():
    """
    显示模式选择对话框
    """
    def on_select():
        selected_value = combo.get()
        if selected_value == "请选择":
            # 显示提示信息并保持对话框打开
            tk.messagebox.showwarning("无效选择", "请选择一个有效的执行模式！")
            return
        elif selected_value == "同时生成库存表和对账单":
            result.set("both")
        elif selected_value == "生成库存表":
            result.set("inventory")
        elif selected_value == "生成对账单":
            result.set("statement")
        root.quit()
    
    def on_cancel():
        result.set(None)
        root.quit()
    
    def on_closing():
        # 处理用户点击窗口关闭按钮的情况
        result.set(None)
        root.quit()
    
    root = tk.Tk()
    root.title("ZR Daily Report - 模式选择")
    root.geometry("400x200")
    root.attributes('-topmost', True)
    
    # 设置窗口关闭事件处理函数
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 居中显示窗口
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (400 // 2)
    y = (root.winfo_screenheight() // 2) - (200 // 2)
    root.geometry(f"400x200+{x}+{y}")
    
    # 创建主框架
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 添加标签
    label = ttk.Label(main_frame, text="请选择执行模式:", font=("Arial", 12))
    label.pack(pady=(0, 10))
    
    # 添加下拉框
    options = ["请选择", "同时生成库存表和对账单", "生成库存表", "生成对账单"]
    combo = ttk.Combobox(main_frame, values=options, state="readonly", font=("Arial", 10), width=30)
    combo.set("请选择")
    combo.pack(pady=(0, 20))
    
    # 添加按钮框架
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X)
    
    # 添加确定按钮
    ok_button = ttk.Button(button_frame, text="确定", command=on_select)
    ok_button.pack(side=tk.LEFT, padx=(0, 10))
    
    # 添加取消按钮
    cancel_button = ttk.Button(button_frame, text="取消", command=on_cancel)
    cancel_button.pack(side=tk.LEFT)
    
    # 存储结果
    result = tk.StringVar()
    
    # 绑定回车键
    root.bind('<Return>', lambda event: on_select())
    # 绑定ESC键
    root.bind('<Escape>', lambda event: on_cancel())
    
    root.mainloop()
    
    # 只有在root仍然存在时才尝试销毁它
    try:
        if root.winfo_exists():
            root.destroy()
    except:
        pass
    
    return result.get()
=======
>>>>>>> 2c70ea71d10c297a06e670cf428a38b578983b25

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
            # 使用优化的综合报表生成功能
            generate_both_reports()
            
    except Exception as e:
        print(f"主程序执行过程中发生异常: {e}")
        print(f"详细错误信息:\n{traceback.format_exc()}")
        exit(1)


# 保证这个部分没有额外的缩进或空行
if __name__ == "__main__":
    main()
