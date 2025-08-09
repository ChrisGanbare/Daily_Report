import csv
import re
import os
import json
import argparse
from datetime import datetime, timedelta
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askdirectory
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font
import mysql.connector

# 添加项目根目录到sys.path，确保能正确导入模块
import sys
sys.path.insert(0, os.path.dirname(__file__))

# 使用包导入简化导入路径
from src.core import DatabaseHandler, StatementHandler
from src.utils import ConfigHandler, DataValidator
from src.core import ExcelHandler, FileHandler

def get_device_and_customer_info(connection, device_no, device_query_template, device_query_fallback_template=None):
    """
    根据设备编号查询设备ID和客户ID，优先使用device_code查询，如果未找到则使用device_no查询
    """
    cursor = None
    try:
        cursor = connection.cursor()
        
        # 优先使用device_code查询
        cursor.execute(device_query_template, (device_no,))
        result = cursor.fetchone()
        
        # 如果通过device_code未找到，且提供了备用查询模板，则使用device_no查询
        if not result and device_query_fallback_template:
            cursor.execute(device_query_fallback_template, (device_no,))
            result = cursor.fetchone()
            
        return (result[0], result[1]) if result else None
    except mysql.connector.Error as err:
        print(f"查询设备ID失败: {err}")
        return None
    finally:
        if cursor:
            cursor.close()

def get_customer_id(connection, device_id):
    """
    根据设备ID获取客户ID
    """
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT customer_id FROM oil.t_device WHERE id = %s", (device_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except mysql.connector.Error as err:
        print(f"查询客户ID失败: {err}")
        return None
    finally:
        if cursor:
            cursor.close()

def get_customer_name_by_device_code(connection, device_id, customer_query_template):
    """
    根据设备ID获取客户名称
    """
    try:
        # 先通过设备ID获取客户ID
        customer_id = get_customer_id(connection, device_id)
        
        if customer_id:
            # 再通过客户ID获取客户名称
            cursor = connection.cursor()
            cursor.execute(customer_query_template, (customer_id,))
            customer_result = cursor.fetchone()
            if customer_result and customer_result[0]:
                return customer_result[0]
        
        print(f"警告：未找到设备ID {device_id} 对应的客户信息")
        return "未知客户"
    except mysql.connector.Error as err:
        print(f"通过设备ID查询客户名称失败: {err}")
        return "未知客户"
    except Exception as e:
        print(f"查询客户名称时发生未知错误: {e}")
        return "未知客户"

def load_configuration():
    """
    独立配置管理：为每个功能创建独立的配置读取逻辑
    """
    config_handler = ConfigHandler()
    try:
        # 使用项目根目录下的配置文件
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'query_config.json')
        print(f"尝试读取配置文件: {config_path}")
        query_config = config_handler.load_plain_config(config_path)
        print("成功读取配置文件")
        return query_config
    except FileNotFoundError as e:
        error_msg = f"配置文件未找到: {e}"
        print(error_msg)
        exit(1)
    except Exception as e:
        error_msg = f"读取查询配置文件失败: {e}"
        print(error_msg)
        exit(1)

def generate_inventory_reports():
    """
    专门用于生成库存报表
    """
    # 初始化日志列表
    log_messages = []
    failed_devices = []
    
    # 记录程序开始时间
    start_time = datetime.now()
    log_messages.append(f"程序开始执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append("")  # 添加空行分隔
    
    print("=" * 50)
    print("步骤1：读取配置文件和设备信息（库存报表）")
    print("=" * 50)
    
    # 初始化处理器
    file_handler = FileHandler()
    data_validator = DataValidator()
    
    # 读取查询配置文件
    query_config = load_configuration()
    
    # 提取数据库配置和SQL模板
    db_config = query_config.get('db_config', {})
    sql_templates = query_config.get('sql_templates', {})
    
    # 获取SQL查询模板
    device_query_template = sql_templates.get('device_id_query')
    device_query_fallback_template = sql_templates.get('device_id_fallback_query')
    inventory_query_template = sql_templates.get('inventory_query', "")
    customer_query_template = sql_templates.get('customer_query')
    
    # 如果某些模板未在配置文件中定义，则使用默认值
    if not device_query_template:
        device_query_template = "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s ORDER BY create_time DESC LIMIT 1"
    
    if not device_query_fallback_template:
        device_query_fallback_template = "SELECT id, customer_id FROM oil.t_device WHERE device_no = %s ORDER BY create_time DESC LIMIT 1"
    
    if not customer_query_template:
        customer_query_template = "SELECT customer_name FROM oil.t_customer WHERE id = %s"
    
    # 显示文件选择对话框，让用户选择设备信息CSV文件
    Tk().withdraw()  # 隐藏主窗口
    devices_csv = askopenfilename(
        title="选择设备信息文件（用于生成库存报表）",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not devices_csv:
        print("未选择设备信息文件，程序退出。")
        return
    
    # 读取设备信息
    devices = file_handler.read_devices_from_csv(devices_csv)
    if not devices:
        print("未能读取设备信息，请检查文件格式。")
        return
    
    # 验证设备信息
    valid_devices = []
    for device in devices:
        if data_validator.validate_csv_data(device):
            valid_devices.append(device)
        else:
            print(f"设备信息验证失败: {device}")
    
    if not valid_devices:
        print("没有有效的设备信息，请检查设备文件内容。")
        return
    
    print(f"成功读取 {len(valid_devices)} 个有效设备信息。")
    log_messages.append(f"成功读取 {len(valid_devices)} 个有效设备信息。")
    log_messages.append("")  # 添加空行分隔
    
    # 初始化数据库连接
    db_handler = DatabaseHandler(db_config)
    try:
        connection = db_handler.connect()
    except Exception as e:
        error_msg = f"数据库连接失败: {e}"
        print(error_msg)
        log_messages.append(error_msg)
        log_messages.append("")
        exit(1)
    
    # 显示目录选择对话框，让用户选择输出目录
    output_dir = askdirectory(title="选择库存报表输出目录")
    if not output_dir:
        print("未选择输出目录，程序退出。")
        connection.close()
        return
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "=" * 50)
    print("步骤2：生成库存报表")
    print("=" * 50)
    
    # 处理每个设备
    for i, device in enumerate(valid_devices, 1):
        device_code = device['device_code']
        start_date = device['start_date']
        end_date = device['end_date']
        
        print(f"\n处理第 {i} 个设备 ({device_code})...")
        log_messages.append(f"处理设备 {device_code}...")
        
        try:
            # 获取设备ID和客户ID
            device_info = get_device_and_customer_info(connection, device_code, device_query_template, device_query_fallback_template)
            if not device_info:
                error_msg = f"  无法找到设备 {device_code} 的信息"
                print(error_msg)
                log_messages.append(error_msg)
                failed_devices.append(device_code)
                continue
                
            device_id, customer_id = device_info
            print(f"  设备ID: {device_id}, 客户ID: {customer_id}")
            
            # 获取客户名称
            customer_name = get_customer_name_by_device_code(connection, device_id, customer_query_template)
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
            data, columns, raw_data = db_handler.fetch_inventory_data(query)
            
            if not data:
                print(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                log_messages.append(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
            
            # 生成Excel报表
            # 格式化日期用于文件名（将/替换为-）
            formatted_start_date = start_date.replace("/", "-")
            formatted_end_date = end_date.replace("/", "-")
            output_file = os.path.join(
                output_dir, 
                f"{customer_name}_{device_code}_{formatted_start_date}_to_{formatted_end_date}.xlsx"
            )
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else output_dir, exist_ok=True)
            
            excel_handler = ExcelHandler()
            # 将字符串日期转换为date对象，支持多种格式
            start_date_obj = None
            end_date_obj = None
            
            # 尝试多种日期格式
            date_formats = ['%Y-%m-%d', '%Y/%m/%d']
            for fmt in date_formats:
                try:
                    start_date_obj = datetime.strptime(start_date, fmt).date()
                    end_date_obj = datetime.strptime(end_date, fmt).date()
                    break
                except ValueError:
                    continue
            
            if start_date_obj is None or end_date_obj is None:
                raise ValueError(f"无法解析日期格式: start_date='{start_date}', end_date='{end_date}'")
                
            excel_handler.generate_excel_with_chart(data, output_file, device_code, start_date_obj, end_date_obj)
            print(f"  成功生成报表: {output_file}")
            log_messages.append(f"  成功生成报表: {output_file}")
            
        except Exception as e:
            error_msg = f"  处理设备 {device_code} 时发生错误: {e}"
            print(error_msg)
            log_messages.append(error_msg)
            failed_devices.append(device_code)
            continue
    
    # 记录程序结束时间
    end_time = datetime.now()
    duration = end_time - start_time
    log_messages.append("")
    log_messages.append(f"程序结束执行时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append(f"总执行时间: {duration}")
    
    # 记录失败设备
    if failed_devices:
        log_messages.append("")
        log_messages.append(f"失败设备列表: {', '.join(failed_devices)}")
    
    # 生成日志文件
    log_file = os.path.join(output_dir, f"处理日志_{start_time.strftime('%Y%m%d_%H%M%S')}.txt")
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_messages))
        print(f"\n日志文件已保存到: {log_file}")
    except Exception as e:
        print(f"保存日志文件失败: {e}")
    
    print("\n库存报表生成功能执行完毕！")
    connection.close()

def generate_customer_statement():
    """
    专门用于生成客户对账单
    """
    # 初始化日志列表
    log_messages = []
    
    # 记录程序开始时间
    start_time = datetime.now()
    log_messages.append(f"程序开始执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append("")  # 添加空行分隔
    
    print("=" * 50)
    print("步骤1：读取配置文件和设备信息（客户对账单）")
    print("=" * 50)
    
    # 初始化处理器
    file_handler = FileHandler()
    data_validator = DataValidator()
    
    # 读取查询配置文件
    query_config = load_configuration()
    
    # 提取数据库配置和SQL模板
    db_config = query_config.get('db_config', {})
    sql_templates = query_config.get('sql_templates', {})
    
    # 获取SQL查询模板
    device_query_template = sql_templates.get('device_id_query')
    device_query_fallback_template = sql_templates.get('device_id_fallback_query')
    inventory_query_template = sql_templates.get('inventory_query', "")
    customer_query_template = sql_templates.get('customer_query')
    
    # 如果某些模板未在配置文件中定义，则使用默认值
    if not device_query_template:
        device_query_template = "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s ORDER BY create_time DESC LIMIT 1"
    
    if not device_query_fallback_template:
        device_query_fallback_template = "SELECT id, customer_id FROM oil.t_device WHERE device_no = %s ORDER BY create_time DESC LIMIT 1"
    
    if not customer_query_template:
        customer_query_template = "SELECT customer_name FROM oil.t_customer WHERE id = %s"
    
    # 显示文件选择对话框，让用户选择设备信息CSV文件
    Tk().withdraw()  # 隐藏主窗口
    devices_csv = askopenfilename(
        title="选择设备信息文件（用于生成客户对账单）",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not devices_csv:
        print("未选择设备信息文件，程序退出。")
        return
    
    # 读取设备信息
    devices = file_handler.read_devices_from_csv(devices_csv)
    if not devices:
        print("未能读取设备信息，请检查文件格式。")
        return
    
    # 验证设备信息
    valid_devices = []
    for device in devices:
        if data_validator.validate_csv_data(device):
            valid_devices.append(device)
        else:
            print(f"设备信息验证失败: {device}")
    
    if not valid_devices:
        print("没有有效的设备信息，请检查设备文件内容。")
        return
    
    print(f"成功读取 {len(valid_devices)} 个有效设备信息。")
    log_messages.append(f"成功读取 {len(valid_devices)} 个有效设备信息。")
    log_messages.append("")  # 添加空行分隔
    
    # 初始化数据库连接
    db_handler = DatabaseHandler(db_config)
    try:
        connection = db_handler.connect()
    except Exception as e:
        error_msg = f"数据库连接失败: {e}"
        print(error_msg)
        log_messages.append(error_msg)
        log_messages.append("")
        exit(1)
    
    # 显示目录选择对话框，让用户选择输出目录
    output_dir = askdirectory(title="选择客户对账单输出目录")
    if not output_dir:
        print("未选择输出目录，程序退出。")
        connection.close()
        return
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "=" * 50)
    print("步骤2：生成客户对账单")
    print("=" * 50)
    
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
            device_info = get_device_and_customer_info(connection, device_code, device_query_template, device_query_fallback_template)
            if not device_info:
                error_msg = f"  无法找到设备 {device_code} 的信息"
                print(error_msg)
                log_messages.append(error_msg)
                failed_devices.append(device_code)
                continue
                
            device_id, customer_id = device_info
            print(f"  设备ID: {device_id}, 客户ID: {customer_id}")
            
            # 获取客户名称
            customer_name = get_customer_name_by_device_code(connection, device_id, customer_query_template)
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
            data, columns, raw_data = db_handler.fetch_inventory_data(query)
            
            if not data:
                print(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                log_messages.append(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
            
            # 保存设备数据供后续使用
            device_data = {
                'device_code': device_code,
                'oil_name': '切削液',  # 假设所有设备都是切削液设备
                'data': data,
                'raw_data': raw_data,
                'columns': columns,
                'customer_name': customer_name
            }
            all_devices_data.append(device_data)
            
        except Exception as e:
            error_msg = f"  处理设备 {device_code} 时发生错误: {e}"
            print(error_msg)
            log_messages.append(error_msg)
            failed_devices.append(device_code)
            continue
    
    # 生成对账单
    if all_devices_data:
        # 获取客户名称（假设所有设备属于同一客户）
        customer_name = all_devices_data[0]['customer_name']
        
        # 获取日期范围
        start_date = valid_devices[0]['start_date']
        end_date = valid_devices[0]['end_date']
        
        # 格式化日期用于文件名
        formatted_start_date = start_date.replace("/", "-")
        formatted_end_date = end_date.replace("/", "-")
        
        # 将字符串日期转换为date对象，支持多种格式
        start_date_obj = None
        end_date_obj = None
        
        # 尝试多种日期格式
        date_formats = ['%Y-%m-%d', '%Y/%m/%d']
        for fmt in date_formats:
            try:
                start_date_obj = datetime.strptime(start_date, fmt).date()
                end_date_obj = datetime.strptime(end_date, fmt).date()
                break
            except ValueError:
                continue
        
        if start_date_obj is None or end_date_obj is None:
            raise ValueError(f"无法解析日期格式: start_date='{start_date}', end_date='{end_date}'")
        
        # 生成对账单文件名
        statement_file = os.path.join(
            output_dir,
            f"{customer_name}_对账单_{formatted_start_date}_to_{formatted_end_date}.xlsx"
        )
        
        # 生成对账单
        statement_handler = StatementHandler()
        try:
            statement_handler.generate_statement_from_template(
                all_devices_data, statement_file, customer_name, 
                start_date_obj, end_date_obj
            )
            print(f"成功生成对账单: {statement_file}")
            log_messages.append(f"成功生成对账单: {statement_file}")
        except Exception as e:
            error_msg = f"生成对账单失败: {e}"
            print(error_msg)
            log_messages.append(error_msg)
    
    # 记录程序结束时间
    end_time = datetime.now()
    duration = end_time - start_time
    log_messages.append("")
    log_messages.append(f"程序结束执行时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append(f"总执行时间: {duration}")
    
    # 记录失败设备
    if failed_devices:
        log_messages.append("")
        log_messages.append(f"失败设备列表: {', '.join(failed_devices)}")
    
    # 生成日志文件
    log_file = os.path.join(output_dir, f"处理日志_{start_time.strftime('%Y%m%d_%H%M%S')}.txt")
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_messages))
        print(f"\n日志文件已保存到: {log_file}")
    except Exception as e:
        print(f"保存日志文件失败: {e}")
    
    print("\n客户对账单生成功能执行完毕！")
    connection.close()

def main():
    """
    主函数，根据命令行参数选择执行哪个功能
    """
    parser = argparse.ArgumentParser(description='ZR Daily Report Generator')
    parser.add_argument('--mode', choices=['inventory', 'statement', 'both'], 
                        default='both', help='选择执行模式: inventory(库存报表), statement(客户对账单), both(两者都执行)')
    
    args = parser.parse_args()
    
    if args.mode == 'inventory':
        generate_inventory_reports()
    elif args.mode == 'statement':
        generate_customer_statement()
    elif args.mode == 'both':
        # 先执行库存报表功能
        generate_inventory_reports()
        # 添加分割线以区分两个任务
        print("\n" + "=" * 50)
        print("以上为库存报表生成日志")
        print("以下为客户对账单生成日志")
        print("=" * 50 + "\n")
        # 再执行客户对账单功能
        generate_customer_statement()

if __name__ == "__main__":
    main()