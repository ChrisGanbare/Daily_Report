"""
报表生成控制器模块
负责协调库存报表和客户对账单的生成流程
"""
import datetime
import json
import os
import traceback
import mysql.connector

def _save_error_log(log_messages, error_details, log_filename_prefix):
    """
    保存错误日志到文件
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
    """
    error_msg = f"数据库连接失败 ({error_type}): {error}"
    print(error_msg)
    if hasattr(error, 'errno'):
        print(f"错误代码: {error.errno}")
    print(f"详细错误信息:\n{traceback.format_exc()}")
    log_messages.append(error_msg)
    
    error_details = {
        'error': error,
        'error_type': error_type,
        'traceback': traceback.format_exc(),
        'log_description': '数据库连接错误日志'
    }
    if hasattr(error, 'errno'):
        error_details['error_code'] = error.errno
    
    _save_error_log(log_messages, error_details, "数据库连接错误日志")

def _check_device_dates_consistency(devices_data):
    """
    检查设备日期范围一致性
    """
    if not devices_data:
        return True, ""
    
    first_device = devices_data[0]
    expected_start_date = first_device['start_date']
    expected_end_date = first_device['end_date']
    
    inconsistent_devices = [
        {'device_code': d['device_code'], 'start_date': d['start_date'], 'end_date': d['end_date']}
        for d in devices_data
        if d['start_date'] != expected_start_date or d['end_date'] != expected_end_date
    ]
    
    if inconsistent_devices:
        error_msg = f"设备日期范围不一致。基准: {expected_start_date} to {expected_end_date}。不一致:\n"
        for dev in inconsistent_devices:
            error_msg += f"  设备 {dev['device_code']}: {dev['start_date']} to {dev['end_date']}\n"
        return False, error_msg
    
    return True, ""

def _load_config():
    """
    加载配置文件
    """
    CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
    config_file_plain = os.path.join(CONFIG_DIR, 'query_config.json')
    
    if not os.path.exists(config_file_plain):
        raise Exception("未找到主配置文件 query_config.json")
        
    with open(config_file_plain, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_error_summary_report(log_prefix="误差汇总处理日志", query_config=None):
    """
    生成所有设备的消耗误差汇总报表 (SQL核心版)。
    支持设备筛选、查询超时、结果集大小限制等优化功能。
    """
    # --- 本地导入 ---
    from src.core.db_handler import DatabaseHandler
    from src.core.consumption_error_handler import ConsumptionErrorSummaryGenerator
    from src.ui.date_dialog import get_date_range
    from src.ui.device_filter_dialog import get_device_filter
    from src.ui.filedialog_selector import file_dialog_selector
    from collections import defaultdict

    log_messages = []
    start_time = datetime.datetime.now()
    log_messages.append(f"程序开始执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    print("=" * 50)
    print("ZR Daily Report - 设备消耗误差汇总报表生成功能")
    print("=" * 50)

    # 配置参数
    MAX_DEVICES = 200  # 最大可查询设备数量
    QUERY_TIMEOUT = 300  # 查询超时时间（秒）

    try:
        if query_config is None:
            query_config = _load_config()
            error_summary_config_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'error_summary_query.json')
            if os.path.exists(error_summary_config_file):
                with open(error_summary_config_file, 'r', encoding='utf-8') as f:
                    error_summary_config = json.load(f)
                if 'sql_templates' in query_config and 'sql_templates' in error_summary_config:
                    query_config['sql_templates'].update(error_summary_config['sql_templates'])

        db_config = query_config.get('db_config', {})
        sql_templates = query_config.get('sql_templates', {})
        
        error_summary_main_query_template = sql_templates.get('error_summary_main_query')
        error_summary_offline_query_template = sql_templates.get('error_summary_offline_query')

        if not error_summary_main_query_template or not error_summary_offline_query_template:
            raise Exception("配置文件中缺少 'error_summary_main_query' 或 'error_summary_offline_query' SQL模板。")

        # 误差汇总报表日期跨度限制：最大31天
        date_range = get_date_range(max_days=31)
        if not date_range:
            print("未选择日期范围，程序退出。")
            return
        start_date_str, end_date_str = date_range
        
        db_handler = DatabaseHandler(db_config)
        connection = db_handler.connect()
        
        # 设备筛选：支持按客户筛选设备，限制最大200台
        print("\n正在打开设备筛选对话框...")
        print("提示：如果对话框没有显示，请检查是否有其他窗口遮挡，或尝试Alt+Tab切换窗口。")
        try:
            device_filter_result = get_device_filter(db_handler, max_devices=MAX_DEVICES)
        except Exception as e:
            print(f"设备筛选对话框错误: {e}")
            import traceback
            print(traceback.format_exc())
            print("程序退出。")
            try:
                if connection is not None and hasattr(connection, 'is_connected') and connection.is_connected():
                    connection.close()
            except Exception:
                pass
            return
        
        if not device_filter_result:
            print("未选择设备，程序退出。")
            try:
                if connection is not None and hasattr(connection, 'is_connected') and connection.is_connected():
                    connection.close()
            except Exception:
                pass
            return
        
        selected_device_ids, selected_customer_names = device_filter_result
        print(f"已选择 {len(selected_device_ids)} 台设备，来自 {len(selected_customer_names)} 个客户")
        
        # 构建设备筛选条件
        if selected_device_ids:
            device_ids_str = ','.join(map(str, selected_device_ids))
            device_filter_condition = f"AND id IN ({device_ids_str})"
        else:
            device_filter_condition = ""
        
        # 构建SQL查询（注入设备筛选条件）
        sql_query = error_summary_main_query_template.format(
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            device_filter_condition=device_filter_condition
        )
        
        offline_query = error_summary_offline_query_template.format(
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            device_filter_condition=device_filter_condition
        )
        
        print("正在执行数据库查询...")
        cursor = connection.cursor(dictionary=True)
        
        # 设置查询超时（MySQL通过设置会话变量实现）
        try:
            cursor.execute(f"SET SESSION max_execution_time = {QUERY_TIMEOUT * 1000}")  # MySQL使用毫秒
        except Exception as e:
            print(f"警告：设置查询超时失败: {e}，继续执行查询...")
        
        # 执行主查询
        cursor.execute(sql_query)
        summary_data = cursor.fetchall()
        
        # 添加调试信息
        print(f"数据库查询返回 {len(summary_data)} 条记录")
        
        # 检查结果集大小
        if len(summary_data) > MAX_DEVICES:
            print(f"警告：查询结果包含 {len(summary_data)} 条记录，超过最大限制 {MAX_DEVICES} 条。")
            print("建议：请使用更严格的筛选条件以减少查询结果。")
            summary_data = summary_data[:MAX_DEVICES]  # 截断结果集
        
        # 验证查询结果数量，并查询缺失设备的详细信息
        if len(summary_data) < len(selected_device_ids):
            missing_count = len(selected_device_ids) - len(summary_data)
            
            # 获取已返回的设备编码
            returned_device_codes = {item.get('device_code') for item in summary_data if item.get('device_code')}
            
            # 查询缺失设备的详细信息（通过device_id查询）
            if selected_device_ids:
                missing_ids_str = ','.join(map(str, selected_device_ids))
                missing_query = f"""
                    SELECT d.id, d.device_code, c.customer_name
                    FROM t_device d
                    LEFT JOIN t_customer c ON d.customer_id = c.id
                    WHERE d.id IN ({missing_ids_str}) AND d.del_status = 1
                """
                cursor.execute(missing_query)
                all_selected_devices = cursor.fetchall()
                
                # 找出缺失的设备（不在返回结果中的设备）
                missing_devices = [
                    device for device in all_selected_devices
                    if device.get('device_code') not in returned_device_codes
                ]
                
                if missing_devices:
                    print(f"\n{'='*60}")
                    print(f"⚠️  警告：选中的 {len(selected_device_ids)} 台设备中，有 {missing_count} 台设备未出现在查询结果中")
                    print(f"{'='*60}")
                    print(f"缺失设备列表：")
                    for device in missing_devices:
                        print(f"  - 设备编码: {device.get('device_code', 'N/A')}, 客户: {device.get('customer_name', 'N/A')}")
                    print(f"\n可能原因：")
                    print(f"  1. 这些设备在指定日期范围（{start_date_str} 至 {end_date_str}）内没有订单数据（total_order_volume IS NULL）")
                    print(f"  2. 这些设备的订单数据状态异常（status != 1）")
                    print(f"  3. 这些设备的数据计算出现问题（如期初库存、期末库存计算失败）")
                    print(f"\n报表中包含 {len(summary_data)} 台设备的数据")
                    print(f"{'='*60}\n")
        elif len(summary_data) == len(selected_device_ids):
            print(f"✓ 所有选中的 {len(selected_device_ids)} 台设备都已包含在报表中")

        # 执行离线事件查询
        cursor.execute(offline_query, (f"{end_date_str} 23:59:59", f"{start_date_str} 00:00:00"))
        offline_events = cursor.fetchall()
        
        # 读取设备桶数配置
        print("\n正在读取设备桶数配置...")
        from src.core.device_config_manager import DeviceConfigManager
        config_manager = DeviceConfigManager()
        
        # 显示配置信息
        config_manager.show_config_info()
        
        # 从summary_data中提取设备编码列表
        device_codes = [item.get('device_code') for item in summary_data if item.get('device_code')]
        
        # 读取桶数配置并创建映射
        barrel_count_map = {}
        for device_code in device_codes:
            barrel_count_map[device_code] = config_manager.get_barrel_count(device_code)
        
        if barrel_count_map:
            configured_count = sum(1 for count in barrel_count_map.values() if count > 1)
            print(f"已读取 {len(barrel_count_map)} 个设备的桶数配置，其中 {configured_count} 个设备配置了非默认桶数")
        
        cursor.close()

        offline_data_map = defaultdict(list)
        for event in offline_events:
            offline_data_map[event['device_code']].append(event)

        if not summary_data:
            print("\n在指定日期范围内未发现任何存在消耗误差的设备。")
            return

        days_in_range = (datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() - datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()).days + 1
        
        # 数据验证和标记，同时添加桶数信息
        data_issues = []
        for item in summary_data:
            item['days_in_range'] = days_in_range
            item['offline_events'] = offline_data_map.get(item.get('device_code'), [])
            # 添加桶数信息
            device_code = item.get('device_code')
            item['barrel_count'] = barrel_count_map.get(device_code, 1)
            
            # 检查数据计算问题
            device_code = item.get('device_code', 'N/A')
            issues = []
            
            # 检查订单总量
            if item.get('total_order_volume') is None:
                issues.append("订单总量为NULL")
            elif item.get('total_order_volume') == 0:
                issues.append("订单总量为0")
            
            # 检查库存消耗计算
            consumption = item.get('total_inventory_consumption_single_barrel')
            if consumption is None:
                issues.append("库存消耗计算为NULL")
            elif abs(consumption) > 100000:  # 异常大的值
                issues.append(f"库存消耗值异常大: {consumption}")
            
            # 如果有问题，记录到数据问题列表
            if issues:
                data_issues.append({
                    'device_code': device_code,
                    'customer_name': item.get('customer_name', 'N/A'),
                    'issues': issues
                })
        
        # 如果有数据问题，输出提示
        if data_issues:
            print(f"\n{'='*60}")
            print(f"⚠️  数据计算问题提示：发现 {len(data_issues)} 台设备的数据计算存在问题")
            print(f"{'='*60}")
            for issue_item in data_issues:
                print(f"设备编码: {issue_item['device_code']}, 客户: {issue_item['customer_name']}")
                for issue in issue_item['issues']:
                    print(f"  - {issue}")
            print(f"\n这些设备的数据仍会出现在报表中，但请注意检查其数据的准确性")
            print(f"{'='*60}\n")

        output_dir = file_dialog_selector.choose_directory(title="选择保存目录（误差汇总报表）")
        if not output_dir:
            print("未选择输出目录，程序退出。")
            return

        summary_generator = ConsumptionErrorSummaryGenerator()
        # 生成文件名，包含客户信息（如果选择了特定客户）
        if len(selected_customer_names) <= 3:
            customer_suffix = "_".join(selected_customer_names)
        else:
            customer_suffix = f"{len(selected_customer_names)}个客户"
        output_filename = f"安卓设备消耗误差汇总_{start_date_str}_to_{end_date_str}_{customer_suffix}.xlsx"
        output_filepath = os.path.join(output_dir, output_filename)
        summary_generator.generate_report(summary_data=summary_data, output_file_path=output_filepath, start_date=start_date_str, end_date=end_date_str)

    except mysql.connector.Error as db_err:
        _handle_db_connection_error(log_messages, db_err)
    except Exception as e:
        _save_error_log(log_messages, {'error': e, 'traceback': traceback.format_exc()}, "错误日志")
    finally:
        # 安全地关闭数据库连接
        try:
            if 'connection' in locals() and connection is not None:
                try:
                    if hasattr(connection, 'is_connected') and connection.is_connected():
                        connection.close()
                except Exception as close_err:
                    print(f"关闭数据库连接时出错: {close_err}")
        except Exception as e:
            print(f"清理数据库连接时出错: {e}")
        print("\n误差汇总报表生成功能执行完毕！")


def generate_daily_consumption_error_reports(log_prefix="每日消耗误差处理日志", query_config=None):
    """
    专门用于生成每日消耗误差报表
    """
    # --- 本地导入 ---
    from src.core.db_handler import DatabaseHandler
    from src.core.file_handler import FileHandler
    from src.core.data_manager import ReportDataManager
    from src.core.consumption_error_handler import DailyConsumptionErrorReportGenerator
    from src.utils.date_utils import validate_csv_data
    from src.ui.filedialog_selector import file_dialog_selector

    log_messages = []
    start_time = datetime.datetime.now()
    log_messages.append(f"程序开始执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("=" * 50)
    print("ZR Daily Report - 每日消耗误差报表生成功能")
    print("=" * 50)
    
    try:
        file_handler = FileHandler()
        if query_config is None:
            query_config = _load_config()
        
        db_config = query_config.get('db_config', {})
        sql_templates = query_config.get('sql_templates', {})
        inventory_query_template = sql_templates.get('inventory_query')
        device_query_template = sql_templates.get('device_id_query')
        
        csv_file = file_dialog_selector.choose_file(title="选择设备信息CSV文件")
        if not csv_file:
            return
        
        devices = file_handler.read_devices_from_csv(csv_file)
        valid_devices = [d for d in devices if validate_csv_data(d, "daily_consumption")]
        if not valid_devices:
            print("没有有效的设备信息。")
            return
        
        # 合并设备配置：从test_data/device_config.csv自动获取设备编码对应的油桶桶数
        from src.core.device_config_manager import DeviceConfigManager
        config_manager = DeviceConfigManager()
        valid_devices = file_handler.merge_device_config(valid_devices, config_manager)
        
        db_handler = DatabaseHandler(db_config)
        connection = db_handler.connect()

        output_dir = file_dialog_selector.choose_directory(title="选择保存目录")
        if not output_dir:
            try:
                if connection is not None and hasattr(connection, 'is_connected') and connection.is_connected():
                    connection.close()
            except Exception:
                pass
            return
        
        os.makedirs(output_dir, exist_ok=True)
        data_manager = ReportDataManager(db_handler)
        
        for device in valid_devices:
            device_code, start_date, end_date = device['device_code'], device['start_date'], device['end_date']
            print(f"\n处理设备 {device_code}...")
            
            try:
                device_id, _ = db_handler.get_latest_device_id_and_customer_id(device_code, device_query_template)
                if not device_id:
                    print(f"  无法找到设备 {device_code} 的信息")
                    continue
                
                customer_name = db_handler.get_customer_name_by_device_code(device_code)
                raw_data = data_manager.fetch_raw_data(device_id, inventory_query_template, start_date, end_date)
                
                barrel_count = int(device.get('barrel_count') or 1)
                error_data = data_manager.calculate_daily_errors(raw_data, start_date, end_date, barrel_count, device_id=device_id)
                
                if not raw_data[2] or '油品名称' not in raw_data[1]:
                    print(f"  错误：设备 {device_code} 的数据中未找到油品名称列。")
                    continue
                
                oil_name = raw_data[2][0].get('油品名称') if isinstance(raw_data[2][0], dict) else raw_data[2][0][raw_data[1].index('油品名称')]
                
                error_handler = DailyConsumptionErrorReportGenerator()
                output_filename = f"{customer_name}_{device_code}_{start_date.replace('/', '-')}_to_{end_date.replace('/', '-')}_每日消耗误差报表.xlsx"
                output_filepath = os.path.join(output_dir, output_filename)
                
                error_handler.generate_report(
                    inventory_data=data_manager.extract_inventory_data(raw_data),
                    error_data=error_data,
                    output_file_path=output_filepath,
                    device_code=device_code,
                    start_date=datetime.datetime.strptime(start_date, '%Y-%m-%d').date(),
                    end_date=datetime.datetime.strptime(end_date, '%Y-%m-%d').date(),
                    oil_name=oil_name,
                    barrel_count=barrel_count
                )
                print(f"  成功生成报表: {output_filepath}")

            except Exception as e:
                print(f"  处理设备 {device_code} 时发生错误: {e}")
                continue
    
    except mysql.connector.Error as db_err:
        _handle_db_connection_error(log_messages, db_err)
    except Exception as e:
        _save_error_log(log_messages, {'error': e, 'traceback': traceback.format_exc()}, "错误日志")
    finally:
        # 安全地关闭数据库连接
        try:
            if 'connection' in locals() and connection is not None:
                try:
                    if hasattr(connection, 'is_connected') and connection.is_connected():
                        connection.close()
                except Exception as close_err:
                    print(f"关闭数据库连接时出错: {close_err}")
        except Exception as e:
            print(f"清理数据库连接时出错: {e}")
        print("\n每日消耗误差报表生成功能执行完毕！")


def generate_monthly_consumption_error_reports(log_prefix="每月消耗误差处理日志", query_config=None):
    """
    专门用于生成每月消耗误差报表
    
    Args:
        log_prefix (str): 日志前缀
        query_config (dict): 查询配置
        
    Returns:
        list: 有效设备列表
    """
    # --- 本地导入 ---
    from src.core.db_handler import DatabaseHandler
    from src.core.file_handler import FileHandler
    from src.core.data_manager import ReportDataManager
    from src.core.consumption_error_handler import MonthlyConsumptionErrorReportGenerator
    from src.utils.date_utils import validate_csv_data
    from src.ui.filedialog_selector import file_dialog_selector
    
    # 初始化日志列表
    log_messages = []
    failed_devices = []
    
    # 记录程序开始时间
    start_time = datetime.datetime.now()
    log_messages.append(f"程序开始执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append("")  # 添加空行分隔
    
    print("=" * 50)
    print("ZR Daily Report - 每月消耗误差报表生成功能")
    print("=" * 50)
    
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
        inventory_query_template = sql_templates.get('inventory_query')
        
        # 如果某些模板未在配置文件中定义，则使用默认值
        if not device_query_template:
            device_query_template = "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s ORDER BY create_time DESC LIMIT 1"
        
        if not customer_query_template:
            customer_query_template = "SELECT customer_name FROM oil.t_customer WHERE id = %s"
            
        if not inventory_query_template:
            inventory_query_template = "SELECT * FROM oil.t_inventory WHERE device_id = %s AND create_time BETWEEN %s AND %s ORDER BY create_time DESC"
        
        # 显示文件选择对话框，让用户选择设备信息CSV文件
        csv_file = file_dialog_selector.choose_file(
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
            return None
            
        if not devices:
            print("未能读取设备信息。")
            return None
        
        # 验证设备信息
        valid_devices = []
        for device in devices:
            # --- 新增：检查月度报表的日期范围 ---
            if "monthly_consumption" in "monthly_consumption": # 确保这是月度报表流程
                try:
                    from dateutil.relativedelta import relativedelta
                    from src.utils.date_utils import parse_date
                    start_dt = parse_date(device['start_date'])
                    end_dt = parse_date(device['end_date'])
                    
                    # 计算日期差异是否超过12个月
                    if end_dt > start_dt + relativedelta(months=12):
                        error_msg = f"  错误：设备 {device['device_code']} 的日期范围超过12个月，无法生成月度报表。"
                        print(error_msg)
                        log_messages.append(error_msg)
                        failed_devices.append(device['device_code'])
                        continue # 跳过此设备
                except (ValueError, TypeError) as e:
                    # 日期格式错误等问题会在 validate_csv_data 中处理，这里只关注范围
                    pass
            # ------------------------------------
            if validate_csv_data(device, "monthly_consumption"):
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
        output_dir = file_dialog_selector.choose_directory(title="选择保存目录（每月消耗误差报表）", initialdir=os.path.join(os.path.expanduser("~"), "Desktop"))
        if not output_dir:
            print("未选择输出目录，程序退出。")
            connection.close()
            return None
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "-" * 50)
        print("步骤2：生成每月消耗误差报表")
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
                end_condition = f"{end_date} 23:59:59"
                query = inventory_query_template.format(
                    device_id=device_id,
                    start_date=start_date,
                    end_condition=end_condition
                )
                
                # 通过数据管理器一次性获取设备原始数据（仅一次数据库查询）
                raw_data = data_manager.fetch_raw_data(device_id, inventory_query_template, start_date, end_date)
                
                # 从原始数据中提取库存表所需数据
                inventory_data = data_manager.extract_inventory_data(raw_data)
                
                # 计算误差数据
                barrel_count = int(device.get('barrel_count') or 1)
                error_data = data_manager.calculate_monthly_errors(raw_data, start_date, end_date, barrel_count)
                
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
                
                # 生成Excel文件
                error_handler = MonthlyConsumptionErrorReportGenerator()
                # 替换日期中的非法字符，确保文件名合法
                safe_start_date = start_date.replace("/", "-").replace("\\", "-")
                safe_end_date = end_date.replace("/", "-").replace("\\", "-")
                output_filename = f"{customer_name}_{device_code}_{safe_start_date}_to_{safe_end_date}_每月消耗误差报表.xlsx"
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
                    error_handler.generate_report(
                        inventory_data=inventory_data,
                        error_data=error_data,
                        output_file_path=output_filepath,
                        device_code=device_code,
                        start_date=parse_date(start_date),
                        end_date=parse_date(end_date),
                        oil_name=oil_name,
                        barrel_count=barrel_count
                    )
                    success_msg = f"  成功生成每月消耗误差报表: {output_filepath}"
                    print(success_msg)
                    log_messages.append(success_msg)
                except Exception as e:
                    error_msg = f"  生成每月消耗误差报表失败: {e}"
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
            log_messages.append("生成每月消耗误差报表失败列表:")
            
            # 按客户分组显示失败设备
            # 创建一个映射：设备代码 -> 客户信息
            device_to_customer = {}
            for device_data in valid_devices:  # 注意：这里使用原始设备数据
                device_code = device_data['device_code']
                if device_code in failed_devices:
                    device_to_customer[device_code] = {
                        'customer_name': device_data.get('customer_name', '未知客户'),
                        'customer_id': device_data.get('customer_id', '未知ID')
                    }
            
            # 按客户分组失败设备
            customers_with_failures = {}
            for device_code in failed_devices:
                if device_code in device_to_customer:
                    customer_info = device_to_customer[device_code]
                    customer_key = (customer_info['customer_id'], customer_info['customer_name'])
                    if customer_key not in customers_with_failures:
                        customers_with_failures[customer_key] = []
                    customers_with_failures[customer_key].append(device_code)
            
            # 打印分组后的失败设备信息
            for (customer_id, customer_name), devices in customers_with_failures.items():
                log_messages.append(f"  客户名称: {customer_name}, 客户ID: {customer_id}")
                log_messages.append(f"    失败设备: {', '.join(devices)}")
        
        # 生成日志文件
        log_file = os.path.join(output_dir, f"{log_prefix}_{start_time.strftime('%Y%m%d_%H%M%S')}.txt")
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_messages))
            print(f"\n日志文件已保存到: {log_file}")
        except Exception as e:
            print(f"保存日志文件失败: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
        
        print("\n每月消耗误差报表生成功能执行完毕！")
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
        error_msg = f"每月消耗误差报表生成过程中发生未处理异常: {e}"
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

def generate_inventory_reports(log_prefix="库存表处理日志", query_config=None):
    """
    专门用于生成库存报表
    """
    # --- 本地导入 ---
    from src.core.db_handler import DatabaseHandler
    from src.core.file_handler import FileHandler
    from src.core.data_manager import ReportDataManager
    from src.core.inventory_handler import InventoryReportGenerator
    from src.utils.date_utils import validate_csv_data
    from src.ui.filedialog_selector import file_dialog_selector
    
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
        csv_file = file_dialog_selector.choose_file(
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
        output_dir = file_dialog_selector.choose_directory(title="选择保存目录（设备库存报表）", initialdir=os.path.join(os.path.expanduser("~"), "Desktop"))
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
                output_filename = f"{customer_name}_{device_code}_{safe_start_date}_to_{safe_end_date}_库存报表.xlsx"
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
            log_messages.append("生成库存报表失败列表:")
            
            # 按客户分组显示失败设备
            # 创建一个映射：设备代码 -> 客户信息
            device_to_customer = {}
            for device_data in valid_devices:  # 注意：这里使用原始设备数据
                device_code = device_data['device_code']
                if device_code in failed_devices:
                    device_to_customer[device_code] = {
                        'customer_name': device_data.get('customer_name', '未知客户'),
                        'customer_id': device_data.get('customer_id', '未知ID')
                    }
            
            # 按客户分组失败设备
            customers_with_failures = {}
            for device_code in failed_devices:
                if device_code in device_to_customer:
                    customer_info = device_to_customer[device_code]
                    customer_key = (customer_info['customer_id'], customer_info['customer_name'])
                    if customer_key not in customers_with_failures:
                        customers_with_failures[customer_key] = []
                    customers_with_failures[customer_key].append(device_code)
            
            # 打印分组后的失败设备信息
            for (customer_id, customer_name), devices in customers_with_failures.items():
                log_messages.append(f"  客户名称: {customer_name}, 客户ID: {customer_id}")
                log_messages.append(f"    失败设备: {', '.join(devices)}")
        
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
    # --- 本地导入 ---
    from src.core.db_handler import DatabaseHandler
    from src.core.file_handler import FileHandler
    from src.core.data_manager import ReportDataManager, CustomerGroupingUtil
    from src.core.statement_handler import CustomerStatementGenerator
    from src.utils.date_utils import validate_csv_data
    from src.ui.filedialog_selector import file_dialog_selector
    
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
            csv_file = file_dialog_selector.choose_file(
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
                error_msg = "没有有效的设备信息，请检查CSV文件内容。"
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
        output_dir = file_dialog_selector.choose_directory(title="选择保存目录（客户对账单）", initialdir=os.path.join(os.path.expanduser("~"), "Desktop"))
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
                    'customer_id': customer_id,
                    'start_date': start_date,  # 添加开始日期
                    'end_date': end_date       # 添加结束日期
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

            # 按客户分组设备数据
            customers_data = CustomerGroupingUtil.group_devices_by_customer(all_devices_data)

            # 为每个客户生成对账单
            for customer_id, customer_info in customers_data.items():
                customer_name = customer_info['customer_name']
                customer_devices = customer_info['devices']

                print(f"\n为客户 {customer_name} (ID: {customer_id}) 生成对账单...")
                log_messages.append(f"为客户 {customer_name} (ID: {customer_id}) 生成对账单...")

                # 检查设备日期范围一致性
                is_consistent, error_msg = _check_device_dates_consistency(customer_devices)
                if not is_consistent:
                    error_msg = f"客户 {customer_name} (ID: {customer_id}) 的设备日期范围不一致，无法生成对账单:\n{error_msg}"
                    print(error_msg)
                    log_messages.append(error_msg)
                    failed_devices.extend([device['device_code'] for device in customer_devices])
                    continue

                # 获取日期范围（使用第一个设备的日期范围）
                first_device = customer_devices[0]
                start_date = first_device['start_date']
                end_date = first_device['end_date']

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
                    statement_data=customer_devices,
                    output_file_path=output_filepath,
                    template_path=None,  # 从现有代码看，这个参数似乎未被使用
                    customer_name=customer_name,
                    start_date=parse_date(start_date),
                    end_date=parse_date(end_date),
                    device_data=customer_devices
                )

                success_msg = f"成功生成客户对账单: {output_filepath}"
                print(success_msg)
                log_messages.append(success_msg)

        except ValueError as e:
            error_msg = f"生成客户对账单失败: {e}"
            print(error_msg)
            log_messages.append(error_msg)
            failed_devices.extend([d['device_code'] for d in all_devices_data])
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
        
        # 记录失败设备（按客户分组显示）
        if failed_devices:
            log_messages.append("")
            log_messages.append("生成对账单失败列表:")
            
            # 按客户分组显示失败设备
            # 创建一个映射：设备代码 -> 客户信息
            device_to_customer = {}
            for device_data in all_devices_data:
                device_code = device_data['device_code']
                if device_code in failed_devices:
                    device_to_customer[device_code] = {
                        'customer_name': device_data['customer_name'],
                        'customer_id': device_data['customer_id']
                    }
            
            # 按客户分组失败设备
            customers_with_failures = {}
            for device_code in failed_devices:
                if device_code in device_to_customer:
                    customer_info = device_to_customer[device_code]
                    customer_key = (customer_info['customer_id'], customer_info['customer_name'])
                    if customer_key not in customers_with_failures:
                        customers_with_failures[customer_key] = []
                    customers_with_failures[customer_key].append(device_code)
            
            # 打印分组后的失败设备信息
            for (customer_id, customer_name), devices in customers_with_failures.items():
                log_messages.append(f"  客户名称: {customer_name}, 客户ID: {customer_id}")
                log_messages.append(f"    失败设备: {', '.join(devices)}")
        elif all_devices_data:  # 如果没有失败设备但有处理过的设备，显示成功信息
            log_messages.append("")
            log_messages.append("所有设备对账单均已成功生成")
        
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

def generate_refueling_details(log_prefix="加注明细处理日志", devices_data=None, query_config=None):
    """
    专门用于生成加注明细报表
    
    Args:
        log_prefix (str): 日志前缀
        devices_data (list): 设备数据列表
        query_config (dict): 查询配置
        
    Returns:
        list: 有效设备列表
    """
    # --- 本地导入 ---
    from src.core.db_handler import DatabaseHandler
    from src.core.file_handler import FileHandler
    from src.core.data_manager import ReportDataManager
    from src.core.refueling_details_handler import RefuelingDetailsReportGenerator
    from src.utils.date_utils import validate_csv_data
    from src.ui.filedialog_selector import file_dialog_selector
    
    # 初始化日志列表
    log_messages = []
    failed_devices = []
    
    # 记录程序开始时间
    start_time = datetime.datetime.now()
    log_messages.append(f"程序开始执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append("")  # 添加空行分隔
    
    print("=" * 50)
    print("ZR Daily Report - 加注明细报表生成功能")
    print("=" * 50)
    
    try:
        # 如果传入了设备数据，则不需要重新选择文件
        if devices_data:
            valid_devices = devices_data
            print("\n" + "-" * 50)
            print("步骤1：使用缓存数据（加注明细报表）")
            print("-" * 50)
            log_messages.append(f"使用已提供的设备数据，设备数量: {len(valid_devices)}")
        else:
            print("\n" + "-" * 50)
            print("步骤1：读取配置文件和设备信息（加注明细报表）")
            print("-" * 50)
            
            # 显示文件选择对话框，让用户选择设备信息CSV文件
            csv_file = file_dialog_selector.choose_file(
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
                error_msg = "没有有效的设备信息，请检查CSV文件设备信息。"
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
            refueling_query_template = query_config['sql_templates']['refueling_details_query']
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
        output_dir = file_dialog_selector.choose_directory(title="选择保存目录（加注明细报表）", initialdir=os.path.join(os.path.expanduser("~"), "Desktop"))
        if not output_dir:
            print("未选择输出目录，程序退出。")
            connection.close()
            return
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "-" * 50)
        print("步骤2：生成加注明细报表")
        print("-" * 50)
        
        # 用于存储所有设备数据，供生成报表使用
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
                query = refueling_query_template.format(
                    device_id=device_id,
                    start_date=start_date,
                    end_condition=end_condition
                )
                
                # 获取加注明细数据
                raw_data = data_manager.fetch_raw_data(device_id, refueling_query_template, start_date, end_date)
                data = raw_data[0]  # 实际数据
                columns = raw_data[1]  # 列名
                raw_rows = raw_data[2]  # 原始行数据
                
                if not data and not raw_rows:
                    print(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                    log_messages.append(f"  警告：设备 {device_code} 在指定时间范围内没有数据")
                
                # 保存设备数据供后续使用
                device_data = {
                    'device_code': device_code,
                    'data': data,
                    'raw_data': raw_rows,
                    'columns': columns,
                    'customer_name': customer_name,
                    'customer_id': customer_id
                }
                all_devices_data.append(device_data)
                
                # 生成Excel文件
                refueling_handler = RefuelingDetailsReportGenerator()
                # 替换日期中的非法字符，确保文件名合法
                safe_start_date = start_date.replace("/", "-").replace("\\", "-")
                safe_end_date = end_date.replace("/", "-").replace("\\", "-")
                output_filename = f"{customer_name}_{device_code}_{safe_start_date}_{safe_end_date}_加注明细.xlsx"
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
                    refueling_handler.generate_report(
                        refueling_data=raw_rows,  # 使用原始行数据，包含所有字段
                        output_file_path=output_filepath,
                        device_code=device_code,
                        start_date=parse_date(start_date),
                        end_date=parse_date(end_date),
                        customer_name=customer_name,
                        columns=columns
                    )
                    success_msg = f"  成功生成加注明细报表: {output_filepath}"
                    print(success_msg)
                    log_messages.append(success_msg)
                except Exception as e:
                    error_msg = f"  生成加注明细报表失败: {e}"
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
            log_messages.append("生成加注明细报表失败列表:")
            
            # 按客户分组显示失败设备
            # 创建一个映射：设备代码 -> 客户信息
            device_to_customer = {}
            for device_data in valid_devices:  # 注意：这里使用原始设备数据
                device_code = device_data['device_code']
                if device_code in failed_devices:
                    device_to_customer[device_code] = {
                        'customer_name': device_data.get('customer_name', '未知客户'),
                        'customer_id': device_data.get('customer_id', '未知ID')
                    }
            
            # 按客户分组失败设备
            customers_with_failures = {}
            for device_code in failed_devices:
                if device_code in device_to_customer:
                    customer_info = device_to_customer[device_code]
                    customer_key = (customer_info['customer_id'], customer_info['customer_name'])
                    if customer_key not in customers_with_failures:
                        customers_with_failures[customer_key] = []
                    customers_with_failures[customer_key].append(device_code)
            
            # 打印分组后的失败设备信息
            for (customer_id, customer_name), devices in customers_with_failures.items():
                log_messages.append(f"  客户名称: {customer_name}, 客户ID: {customer_id}")
                log_messages.append(f"    失败设备: {', '.join(devices)}")
        elif all_devices_data:  # 如果没有失败设备但有处理过的设备，显示成功信息
            log_messages.append("")
            log_messages.append("所有设备加注明细报表均已成功生成")
        
        # 生成日志文件
        log_file = os.path.join(output_dir, f"{log_prefix}_{start_time.strftime('%Y%m%d_%H%M%S')}.txt")
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_messages))
            print(f"\n日志文件已保存到: {log_file}")
        except Exception as e:
            print(f"保存日志文件失败: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
        
        print("\n加注明细报表生成功能执行完毕！")
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
        error_msg = f"加注明细报表生成过程中发生未处理异常: {e}"
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
