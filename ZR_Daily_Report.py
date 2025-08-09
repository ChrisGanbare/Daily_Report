import csv
import re
import os
import json
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

def main():
    # 初始化日志列表
    log_messages = []
    failed_devices = []
    
    # 记录程序开始时间
    start_time = datetime.now()
    log_messages.append(f"程序开始执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append("")  # 添加空行分隔
    
    print("=" * 50)
    print("步骤1：读取配置文件和设备信息")
    print("=" * 50)
    
    # 初始化处理器
    config_handler = ConfigHandler()
    file_handler = FileHandler()
    data_validator = DataValidator()
    
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
    finally:
        if cursor:
            cursor.close()
    
    # 读取查询配置文件
    try:
        # 使用项目根目录下的配置文件
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'query_config.json')
        print(f"尝试读取配置文件: {config_path}")
        query_config = config_handler.load_plain_config(config_path)
        log_messages.append("成功读取配置文件")
        log_messages.append("")
    except FileNotFoundError as e:
        error_msg = f"配置文件未找到: {e}"
        print(error_msg)
        log_messages.append(error_msg)
        log_messages.append("")  # 添加空行分隔
        exit(1)
    except Exception as e:
        error_msg = f"读取查询配置文件失败: {e}"
        print(error_msg)
        log_messages.append(error_msg)
        log_messages.append("")  # 添加空行分隔
        exit(1)
    
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