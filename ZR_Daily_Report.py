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
from src.core import DatabaseHandler, CustomerStatementGenerator
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
            raise Exception("无法加载任何配置文件")
    
    raise Exception("未找到有效的配置文件")

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
    query_config = load_config()
    
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
            
            # 创建设备数据，但不保存到all_devices_data（因为库存报表不需要这个数据）
            device_data = {
                'device_code': device_code,
                'oil_name': '切削液',  # 假设所有设备都是切削液设备
                'data': data,
                'raw_data': raw_data,
                'columns': columns,
                'customer_name': customer_name,
                'customer_id': customer_id  # 添加客户ID用于高性能分组
            }
            
            # 生成Excel文件
            excel_handler = ExcelHandler()
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
                            return datetime.strptime(date_string, fmt).date()
                        except ValueError:
                            continue
                    # 如果所有格式都失败，则抛出异常
                    raise ValueError(f"无法解析日期格式: {date_string}")
                
                excel_handler.generate_excel_with_chart(
                    data=data,
                    output_file=output_filepath,
                    device_code=device_code,
                    start_date=parse_date(start_date),
                    end_date=parse_date(end_date)
                )
                success_msg = f"  成功生成库存报表: {output_filepath}"
                print(success_msg)
                log_messages.append(success_msg)
            except Exception as e:
                error_msg = f"  生成库存报表失败: {e}"
                print(error_msg)
                log_messages.append(error_msg)
                failed_devices.append(device_code)
                continue
                
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
    生成客户对账单的主函数
    """
    # 初始化日志消息列表
    log_messages = []
    start_time = datetime.now()
    log_messages.append(f"程序开始执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append("")
    
    print("=" * 50)
    print("ZR Daily Report - 客户对账单生成功能")
    print("=" * 50)
    log_messages.append("ZR Daily Report - 客户对账单生成功能")
    
    # 显示文件选择对话框，让用户选择设备信息CSV文件
    Tk().withdraw()  # 隐藏主窗口
    csv_file = askopenfilename(
        title="选择设备信息CSV文件",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not csv_file:
        print("未选择文件，程序退出。")
        return
    
    log_messages.append(f"选择的设备信息文件: {csv_file}")
    
    # 读取设备信息
    try:
        file_handler = FileHandler()
        devices = file_handler.read_devices_from_csv(csv_file)
        data_validator = DataValidator()
        valid_devices = [d for d in devices if data_validator.validate_csv_data(d)]
        log_messages.append(f"总共读取设备数量: {len(devices)}")
        log_messages.append(f"有效设备数量: {len(valid_devices)}")
    except Exception as e:
        error_msg = f"读取设备信息失败: {e}"
        print(error_msg)
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
        query_config = load_config()
        db_config = query_config['db_config']
        inventory_query_template = query_config['sql_templates']['inventory_query']
        device_query_template = query_config['sql_templates']['device_id_query']
        device_query_fallback_template = query_config['sql_templates'].get('device_id_fallback_query')
        customer_query_template = query_config['sql_templates']['customer_query']
    except Exception as e:
        error_msg = f"加载配置失败: {e}"
        print(error_msg)
        log_messages.append(error_msg)
        log_messages.append("")
        exit(1)
    
    # 连接数据库
    try:
        db_handler = DatabaseHandler(db_config)
        connection = db_handler.connect()
        log_messages.append("数据库连接成功")
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
                'customer_name': customer_name,
                'customer_id': customer_id  # 添加客户ID用于高性能分组
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
                        start_date_obj = datetime.strptime(start_date, fmt).date()
                        end_date_obj = datetime.strptime(end_date, fmt).date()
                        break
                    except ValueError:
                        continue
                
                if start_date_obj is None or end_date_obj is None:
                    raise ValueError(f"无法解析日期格式: start_date='{start_date}', end_date='{end_date}'")
                
                # 格式化日期用于文件名（使用统一格式）
                formatted_start_date = start_date_obj.strftime('%Y-%m-%d')
                formatted_end_date = end_date_obj.strftime('%Y-%m-%d')
            
            # 生成对账单文件名: 客户名称xxxx年xx月对账单
            statement_file = os.path.join(
                output_dir,
                f"{customer_name}{start_date_obj.strftime('%Y年%m月')}对账单.xlsx"
            )
            
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
                log_messages.append(error_msg)
    
    # 记录程序结束时间
    
    # 初始化日期变量
    start_date_obj = None
    end_date_obj = None
    
    # 初始化日期变量
    start_date_obj = None
    end_date_obj = None
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