"""
报表生成控制器模块
负责协调库存报表和客户对账单的生成流程
"""
import datetime
import json
import os
import traceback

from src.core.db_handler import DatabaseHandler
from src.core.inventory_handler import InventoryReportGenerator
from src.core.statement_handler import CustomerStatementGenerator
from src.core.file_handler import FileHandler
from src.core.data_manager import ReportDataManager
from src.utils.date_utils import validate_csv_data
from src.utils.config_handler import ConfigHandler
from src.ui.filedialog_selector import choose_file, choose_directory

import mysql.connector


def _save_error_log(log_messages, error_details, log_filename_prefix):
    """
    保存错误日志到文件
    
    Args:
        log_messages (list): 日志消息列表
        error_details (dict): 错误详细信息
        log_filename_prefix (str): 日志文件名前缀
    """
    error_time = datetime.datetime.now()
    error_log_file = os.path.join(os.getcwd(), f"{log_filename_prefix}_{error_time.strftime('%Y%m%d_%H%M%S')}.txt")
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
            query_config = _load_config()
        
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
        try:
            devices = file_handler.read_devices_from_csv(csv_file)
        except Exception as e:
            print(f"读取设备信息文件失败: {csv_file}")
            # 不再重复打印错误详情，因为FileHandler已经打印过了
            print("\n解决建议:")
            print("1. 检查CSV文件是否包含正确列: device_code, start_date, end_date")
            print("2. 检查日期格式（支持 YYYY-MM-DD 或 YYYY/M/D）")
            print("3. 确保开始日期不晚于结束日期且范围不超过2个月")
            print("4. 检查设备编码格式（以字母开头，只包含字母和数字）")
            return None
            
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
        
        # 创建数据管理器
        data_manager = ReportDataManager(db_handler)
        
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
                
                # 通过数据管理器一次性获取设备原始数据
                raw_data = data_manager.fetch_raw_data(device_id, inventory_query_template, start_date, end_date)
                
                # 从原始数据中提取库存表所需数据
                data = data_manager.extract_inventory_data(raw_data)
                
                if not data:
                    print(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                    log_messages.append(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                
                # 保存设备数据供后续使用
                # 检查是否存在油品名称列
                if not raw_data[2] or '油品名称' not in raw_data[1]:
                    error_msg = f"  错误：设备 {device_code} 的数据中未找到油品名称列，请检查数据库查询结果"
                    print(error_msg)
                    log_messages.append(error_msg)
                    failed_devices.append(device_code)
                    continue
                
                # 获取第一条记录的油品名称作为该设备的油品名称
                # 注意：这里假设一个设备只使用一种油品，这是业务上的合理假设
                first_row = raw_data[2][0]
                if isinstance(first_row, dict):
                    oil_name = first_row.get('油品名称')
                else:
                    # 如果是元组或列表形式，根据列名索引获取油品名称
                    oil_name_index = raw_data[1].index('油品名称')
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
                    'raw_data': raw_data[2],
                    'columns': raw_data[1],
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
                    
                    # 使用重构后的generate_report方法
                    inventory_handler.generate_report(
                        inventory_data=data,
                        output_file_path=output_filepath,
                        device_code=device_code,
                        start_date=parse_date(start_date),
                        end_date=parse_date(end_date),
                        oil_name=oil_name
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
        
        # 生成日志文件
        log_file = os.path.join(output_dir, f"{log_prefix}_{start_time.strftime('%Y%m%d_%H%M%S')}.txt")
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_messages))
            print(f"\n日志文件已保存到: {log_file}")
        except Exception as e:
            print(f"保存日志文件失败: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
        
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
                # 不再重复打印错误详情，因为FileHandler已经打印过了
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
                query_config = _load_config()
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
        
        # 创建数据管理器
        data_manager = ReportDataManager(db_handler)
        
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
                
                # 通过数据管理器一次性获取设备原始数据
                raw_data = data_manager.fetch_raw_data(device_id, inventory_query_template, start_date, end_date)
                
                # 从原始数据中计算对账单所需的各种数据
                data = data_manager.extract_inventory_data(raw_data)
                daily_usage_data = data_manager.calculate_daily_usage(raw_data)
                monthly_usage_data = data_manager.calculate_monthly_usage(raw_data, start_date, end_date)
                
                if not data:
                    print(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                    log_messages.append(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                
                # 保存设备数据供后续使用
                # 检查是否存在油品名称列
                if not raw_data[2] or '油品名称' not in raw_data[1]:
                    error_msg = f"  错误：设备 {device_code} 的数据中未找到油品名称列，请检查数据库查询结果"
                    print(error_msg)
                    log_messages.append(error_msg)
                    failed_devices.append(device_code)
                    continue
                
                # 获取第一条记录的油品名称作为该设备的油品名称
                # 注意：这里假设一个设备只使用一种油品，这是业务上的合理假设
                first_row = raw_data[2][0]
                if isinstance(first_row, dict):
                    oil_name = first_row.get('油品名称')
                else:
                    # 如果是元组或列表形式，根据列名索引获取油品名称
                    oil_name_index = raw_data[1].index('油品名称')
                    oil_name = first_row[oil_name_index] if oil_name_index < len(first_row) else None
                
                # 检查油品名称是否有效
                if not oil_name:
                    error_msg = f"  错误：设备 {device_code} 的数据中油品名称为空，请检查数据库数据完整性"
                    print(error_msg)
                    log_messages.append(error_msg)
                    failed_devices.append(device_code)
                    continue
                
                # 保存设备数据供后续使用
                device_data = {
                    'device_code': device_code,
                    'oil_name': oil_name,
                    'data': data,
                    'daily_usage_data': daily_usage_data,
                    'monthly_usage_data': monthly_usage_data,
                    'raw_data': raw_data[2],
                    'columns': raw_data[1],
                    'customer_name': customer_name,
                    'customer_id': customer_id
                }
                all_devices_data.append(device_data)
                
            except Exception as e:
                error_msg = f"  处理设备 {device_code} 时发生错误: {e}"
                print(error_msg)
                print(f"详细错误信息:\n{traceback.format_exc()}")
                log_messages.append(error_msg)
                failed_devices.append(device_code)
                continue
        
        # 检查是否有有效设备数据
        if not all_devices_data:
            error_msg = "没有有效的设备数据可用于生成对账单。"
            print(error_msg)
            log_messages.append(error_msg)
            log_messages.append("")
            
            # 生成日志文件
            log_file = os.path.join(output_dir, f"{log_prefix}_{start_time.strftime('%Y%m%d_%H%M%S')}.txt")
            try:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(log_messages))
                print(f"\n日志文件已保存到: {log_file}")
            except Exception as e:
                print(f"保存日志文件失败: {e}")
                print(f"详细错误信息:\n{traceback.format_exc()}")
            
            try:
                if connection and connection.is_connected():
                    connection.close()
                    print("数据库连接已关闭")
            except Exception as e:
                print(f"关闭数据库连接时发生错误: {e}")
            
            return
        
        # 生成客户对账单
        try:
            print("\n" + "-" * 50)
            print("步骤3：生成客户对账单文件")
            print("-" * 50)
            
            # 获取第一个设备的信息作为对账单信息
            first_device = all_devices_data[0]
            customer_name = first_device['customer_name']
            
            # 生成输出文件名
            first_device_info = valid_devices[0]
            start_date = first_device_info['start_date']
            end_date = first_device_info['end_date']
            
            # 替换日期中的非法字符，确保文件名合法
            safe_start_date = start_date.replace("/", "-").replace("\\", "-")
            safe_end_date = end_date.replace("/", "-").replace("\\", "-")
            output_filename = f"{customer_name}_{safe_start_date}_to_{safe_end_date}_对账单.xlsx"
            output_filepath = os.path.join(output_dir, output_filename)
            
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
            
            # 生成对账单，使用重构后的generate_report方法
            statement_handler = CustomerStatementGenerator()
            statement_handler.generate_report(
                statement_data=all_devices_data,
                output_file_path=output_filepath,
                template_path=None,  # 从现有代码看，这个参数似乎未被使用
                customer_name=customer_name,
                start_date=parse_date(start_date),
                end_date=parse_date(end_date),
                device_data=all_devices_data
            )
            
            success_msg = f"成功生成客户对账单: {output_filepath}"
            print(success_msg)
            log_messages.append(success_msg)
            
        except Exception as e:
            error_msg = f"生成客户对账单失败: {e}"
            print(error_msg)
            print(f"详细错误信息:\n{traceback.format_exc()}")
            log_messages.append(error_msg)
            failed_devices.extend([d['device_code'] for d in all_devices_data])
        
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


def generate_both_reports(log_prefix="综合处理日志", query_config=None):
    """
    同时生成库存表和对账单，优化数据库查询性能
    """
    # 初始化日志列表
    log_messages = []
    failed_devices = []
    
    # 记录程序开始时间
    start_time = datetime.datetime.now()
    log_messages.append(f"程序开始执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append("")  # 添加空行分隔
    
    print("=" * 50)
    print("ZR Daily Report - 综合报表生成功能")
    print("=" * 50)
    print("\n" + "-" * 50)
    print("步骤1：读取配置文件和设备信息（综合报表）")
    print("-" * 50)
    
    try:
        # 初始化处理器
        file_handler = FileHandler()
        
        # 如果没有传入配置，则读取查询配置文件
        if query_config is None:
            query_config = _load_config()
        
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
        try:
            devices = file_handler.read_devices_from_csv(csv_file)
        except Exception as e:
            print(f"读取设备信息文件失败: {csv_file}")
            # 不再重复打印错误详情，因为FileHandler已经打印过了
            print("\n解决建议:")
            print("1. 检查CSV文件是否包含正确列: device_code, start_date, end_date")
            print("2. 检查日期格式（支持 YYYY-MM-DD 或 YYYY/M/D）")
            print("3. 确保开始日期不晚于结束日期且范围不超过2个月")
            print("4. 检查设备编码格式（以字母开头，只包含字母和数字）")
            return None
            
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
        output_dir = choose_directory(title="选择保存目录（综合报表）", initialdir=os.path.join(os.path.expanduser("~"), "Desktop"))
        if not output_dir:
            print("未选择输出目录，程序退出。")
            connection.close()
            return None
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "-" * 50)
        print("步骤2：生成库存报表和客户对账单")
        print("-" * 50)
        
        # 用于存储处理失败的设备
        failed_devices = []
        
        # 创建数据管理器
        data_manager = ReportDataManager(db_handler)
        
        # 存储所有设备的处理后数据
        all_devices_processed_data = []
        
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
                
                # 通过数据管理器一次性获取设备原始数据（仅一次数据库查询）
                raw_data = data_manager.fetch_raw_data(device_id, inventory_query_template, start_date, end_date)
                
                # 从原始数据中提取所有报表所需的数据
                inventory_data = data_manager.extract_inventory_data(raw_data)
                daily_usage_data = data_manager.calculate_daily_usage(raw_data)
                monthly_usage_data = data_manager.calculate_monthly_usage(raw_data, start_date, end_date)
                
                if not inventory_data:
                    print(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                    log_messages.append(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                
                # 保存设备数据供后续使用
                # 检查是否存在油品名称列
                if not raw_data[2] or '油品名称' not in raw_data[1]:
                    error_msg = f"  错误：设备 {device_code} 的数据中未找到油品名称列，请检查数据库查询结果"
                    print(error_msg)
                    log_messages.append(error_msg)
                    failed_devices.append(device_code)
                    continue
                
                # 获取第一条记录的油品名称作为该设备的油品名称
                # 注意：这里假设一个设备只使用一种油品，这是业务上的合理假设
                first_row = raw_data[2][0]
                if isinstance(first_row, dict):
                    oil_name = first_row.get('油品名称')
                else:
                    # 如果是元组或列表形式，根据列名索引获取油品名称
                    oil_name_index = raw_data[1].index('油品名称')
                    oil_name = first_row[oil_name_index] if oil_name_index < len(first_row) else None
                
                # 检查油品名称是否有效
                if not oil_name:
                    error_msg = f"  错误：设备 {device_code} 的数据中油品名称为空，请检查数据库数据完整性"
                    print(error_msg)
                    log_messages.append(error_msg)
                    failed_devices.append(device_code)
                    continue
                
                # 保存所有处理后的数据
                processed_data = {
                    'device_code': device_code,
                    'oil_name': oil_name,
                    'inventory_data': inventory_data,
                    'daily_usage_data': daily_usage_data,
                    'monthly_usage_data': monthly_usage_data,
                    'raw_data': raw_data[2],
                    'columns': raw_data[1],
                    'customer_name': customer_name,
                    'customer_id': customer_id,
                    'start_date': start_date,
                    'end_date': end_date
                }
                all_devices_processed_data.append(processed_data)
                
                # 生成库存报表（使用已处理数据）
                inventory_handler = InventoryReportGenerator()
                # 替换日期中的非法字符，确保文件名合法
                safe_start_date = start_date.replace("/", "-").replace("\\", "-")
                safe_end_date = end_date.replace("/", "-").replace("\\", "-")
                inventory_output_filename = f"{device_code}_{safe_start_date}_to_{safe_end_date}_库存报表.xlsx"
                inventory_output_filepath = os.path.join(output_dir, inventory_output_filename)
                
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
                    
                    # 使用重构后的generate_report方法
                    inventory_handler.generate_report(
                        inventory_data=inventory_data,
                        output_file_path=inventory_output_filepath,
                        device_code=device_code,
                        start_date=parse_date(start_date),
                        end_date=parse_date(end_date),
                        oil_name=oil_name  # 添加油品名称参数
                    )
                    success_msg = f"  成功生成库存报表: {inventory_output_filepath}"
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
        
        # 检查是否有有效设备数据
        if not all_devices_processed_data:
            error_msg = "没有有效的设备数据可用于生成报表。"
            print(error_msg)
            log_messages.append(error_msg)
            log_messages.append("")
            
            # 生成日志文件
            log_file = os.path.join(output_dir, f"{log_prefix}_{start_time.strftime('%Y%m%d_%H%M%S')}.txt")
            try:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(log_messages))
                print(f"\n日志文件已保存到: {log_file}")
            except Exception as e:
                print(f"保存日志文件失败: {e}")
                print(f"详细错误信息:\n{traceback.format_exc()}")
            
            try:
                if connection and connection.is_connected():
                    connection.close()
                    print("数据库连接已关闭")
            except Exception as e:
                print(f"关闭数据库连接时发生错误: {e}")
            
            return
        
        # 生成客户对账单（使用已处理数据）
        try:
            print("\n" + "-" * 50)
            print("步骤3：生成客户对账单文件")
            print("-" * 50)
            
            # 获取第一个设备的信息作为对账单信息
            first_device = all_devices_processed_data[0]
            customer_name = first_device['customer_name']
            start_date = first_device['start_date']
            end_date = first_device['end_date']
            
            # 生成输出文件名
            # 替换日期中的非法字符，确保文件名合法
            safe_start_date = start_date.replace("/", "-").replace("\\", "-")
            safe_end_date = end_date.replace("/", "-").replace("\\", "-")
            statement_output_filename = f"{customer_name}_{safe_start_date}_to_{safe_end_date}_对账单.xlsx"
            statement_output_filepath = os.path.join(output_dir, statement_output_filename)
            
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
            
            # 生成对账单，使用重构后的generate_report方法
            statement_handler = CustomerStatementGenerator()
            statement_handler.generate_report(
                statement_data=all_devices_processed_data,
                output_file_path=statement_output_filepath,
                template_path=None,  # 从现有代码看，这个参数似乎未被使用
                customer_name=customer_name,
                start_date=parse_date(start_date),
                end_date=parse_date(end_date),
                device_data=all_devices_processed_data
            )
            
            success_msg = f"成功生成客户对账单: {statement_output_filepath}"
            print(success_msg)
            log_messages.append(success_msg)
            
        except Exception as e:
            error_msg = f"生成客户对账单失败: {e}"
            print(error_msg)
            print(f"详细错误信息:\n{traceback.format_exc()}")
            log_messages.append(error_msg)
            failed_devices.extend([d['device_code'] for d in all_devices_processed_data])
        
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
        
        print("\n综合报表生成功能执行完毕！")
        try:
            if connection and connection.is_connected():
                connection.close()
                print("数据库连接已关闭")
        except Exception as e:
            print(f"关闭数据库连接时发生错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
        
    except Exception as e:
        error_msg = f"综合报表生成过程中发生未处理异常: {e}"
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

def _load_config():
    """
    加载配置文件，优先加载加密配置文件，如果不存在则加载明文配置文件
    """
    CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
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