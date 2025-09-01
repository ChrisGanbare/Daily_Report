"""
报表数据管理器模块
负责统一管理报表所需的数据获取和处理，避免重复数据库查询
"""
import datetime
from collections import defaultdict
from ..utils.date_utils import parse_date


class ReportDataManager:
    """报表数据管理器，负责统一管理报表所需的数据获取和处理"""
    
    def __init__(self, db_handler):
        """
        初始化报表数据管理器
        
        Args:
            db_handler: 数据库处理器实例
        """
        self.db_handler = db_handler
        self._raw_data_cache = {}
        
    def fetch_raw_data(self, device_id, query_template, start_date, end_date):
        """
        一次性获取设备的原始数据
        
        Args:
            device_id: 设备ID
            query_template: 查询模板
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            tuple: (数据, 列名, 原始数据)
        """
        cache_key = (device_id, query_template, start_date, end_date)
        if cache_key not in self._raw_data_cache:
            print("  正在获取设备原始数据...")
            data, columns, raw_data = self.db_handler.fetch_inventory_data(
                device_id, query_template, start_date, end_date
            )
            self._raw_data_cache[cache_key] = (data, columns, raw_data)
        return self._raw_data_cache[cache_key]
        
    def extract_inventory_data(self, raw_data):
        """
        从原始数据中提取库存表所需数据
        
        Args:
            raw_data: 原始数据元组 (data, columns, raw_data)
            
        Returns:
            list: 库存数据
        """
        # 直接返回原始数据，因为fetch_inventory_data已经处理好了
        return raw_data[0]  # data部分
        
    def calculate_daily_usage(self, raw_data):
        """
        从原始数据中计算每日用量数据
        
        Args:
            raw_data: 原始数据元组 (data, columns, raw_data)
            
        Returns:
            list: 按日期排序的每日用量数据 [(date, usage), ...]
        """
        data, columns, raw_data_content = raw_data
        # 按日期分组并累加油加注值
        daily_usage = defaultdict(float)
        
        for i, row in enumerate(raw_data_content):
            row_dict = dict(zip(columns, row))
            order_time = row_dict.get("加注时间")
            oil_val = row_dict.get("油加注值", 0) if row_dict.get("油加注值") is not None else 0
            
            if isinstance(order_time, datetime.datetime):
                order_date = order_time.date()
                daily_usage[order_date] += float(oil_val)
            elif isinstance(order_time, str):
                # 处理字符串格式的日期
                parsed_datetime = None
                for fmt in ["%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        parsed_datetime = datetime.datetime.strptime(order_time, fmt)
                        break
                    except ValueError:
                        continue
                if parsed_datetime:
                    order_date = parsed_datetime.date()
                    daily_usage[order_date] += float(oil_val)
        
        return sorted(daily_usage.items())
        
    def calculate_monthly_usage(self, raw_data, start_date=None, end_date=None):
        """
        从原始数据中计算每月用量数据
        
        Args:
            raw_data: 原始数据元组 (data, columns, raw_data)
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            list: 按月份排序的每月用量数据 [(month, usage), ...]
        """
        data, columns, raw_data_content = raw_data
        # 按月份分组并累加油加注值
        monthly_usage = defaultdict(float)
        
        for i, row in enumerate(raw_data_content):
            row_dict = dict(zip(columns, row))
            order_time = row_dict.get("加注时间")
            oil_val = row_dict.get("油加注值", 0) if row_dict.get("油加注值") is not None else 0
            
            if isinstance(order_time, datetime.datetime):
                # 按记录本身的日期归属月份，除非开始日期与结束日期不同，则以结束日期为归属月份
                if start_date and end_date and start_date != end_date:
                    # 跨月对账处理：以结束日期为归属月份
                    order_month = parse_date(end_date).strftime("%Y-%m")
                else:
                    # 正常情况：按记录本身的日期归属月份
                    order_month = order_time.strftime("%Y-%m")
                
                monthly_usage[order_month] += float(oil_val)
            elif isinstance(order_time, str):
                # 处理字符串格式的日期
                parsed_datetime = None
                for fmt in ["%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        parsed_datetime = datetime.datetime.strptime(order_time, fmt)
                        break
                    except ValueError:
                        continue
                if parsed_datetime:
                    # 按记录本身的日期归属月份，除非开始日期与结束日期不同，则以结束日期为归属月份
                    if start_date and end_date and start_date != end_date:
                        # 跨月对账处理：以结束日期为归属月份
                        order_month = parse_date(end_date).strftime("%Y-%m")
                    else:
                        # 正常情况：按记录本身的日期归属月份
                        order_month = parsed_datetime.strftime("%Y-%m")
                    
                    monthly_usage[order_month] += float(oil_val)
        
        return sorted(monthly_usage.items())


class CustomerGroupingUtil:
    """客户分组工具类，用于按客户维度对设备进行分组"""

    @staticmethod
    def group_devices_by_customer(devices_data):
        """
        按客户ID对设备进行分组

        Args:
            devices_data (list): 设备数据列表，每个设备应包含customer_id和customer_name字段

        Returns:
            dict: 按客户ID分组的设备数据
                  格式: {
                      customer_id: {
                          'customer_name': customer_name,
                          'devices': [device_data, ...]
                      },
                      ...
                  }
        """
        customers_data = {}
        for device_data in devices_data:
            customer_id = device_data.get('customer_id')
            customer_name = device_data.get('customer_name')

            # 确保customer_id和customer_name存在
            if customer_id is None or customer_name is None:
                continue

            # 使用客户ID作为键，但保存客户名称用于文件命名
            if customer_id not in customers_data:
                customers_data[customer_id] = {
                    'customer_name': customer_name,
                    'devices': []
                }
            customers_data[customer_id]['devices'].append(device_data)

        return customers_data

    @staticmethod
    def get_customer_list(devices_data):
        """
        获取设备列表中涉及的所有客户

        Args:
            devices_data (list): 设备数据列表

        Returns:
            list: 客户信息列表，格式: [{'customer_id': id, 'customer_name': name}, ...]
        """
        customers = {}
        for device_data in devices_data:
            customer_id = device_data.get('customer_id')
            customer_name = device_data.get('customer_name')

            if customer_id and customer_name and customer_id not in customers:
                customers[customer_id] = {
                    'customer_id': customer_id,
                    'customer_name': customer_name
                }

        return list(customers.values())