"""
报表数据管理器模块
负责统一管理报表所需的数据获取和处理，避免重复数据库查询
"""
import datetime
from collections import defaultdict
#from ..utils.date_utils import parse_date
# 改为绝对导入：
from src.utils.date_utils import parse_date


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
            # 使用通用数据获取方法
            data, columns, raw_data = self.db_handler.fetch_generic_data(
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
        # 直接返回原始数据，因为fetch_generic_data已经处理好了
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
        # 按日期分组并累加注加注值
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
        # 按月份分组并累加注加注值
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

    def calculate_daily_errors(self, raw_data, barrel_count=1):
        """
        计算每日消耗误差数据。

        核心业务逻辑:
        1.  **订单总量 (流量计读数)**: 累加当天所有记录的 `油加注值`。
        2.  **库存消耗总量 (液位计推算)**: 根据液位变化和推断的加油量计算得出。
            -   **当天总加油量**: 通过比较当天内连续记录的库存，如果后一条记录的库存 > 前一条记录的库存，
                则差值被视为一次加油（入库），累加得到当天总加油量。
            -   **库存消耗总量公式**: 
                `库存消耗总量 = (上一日结束库存 - 当日结束库存) + 当天总加油量`
        3.  **误差**: `误差 = 库存消耗总量 - 订单总量`。
            -   正数表示库存消耗大于订单记录，记为“中润亏损”。
            -   负数表示订单记录大于库存消耗，记为“客户亏损”。

        Args:
            raw_data: 原始数据元组 (data, columns, raw_data)
            barrel_count (int): 油桶数量，默认为1

        Returns:
            dict: 包含每日订单累积总量、中润亏损和客户亏损的数据
        """
        data, columns, raw_data_content = raw_data

        # 按日期分组数据
        daily_data = defaultdict(list)

        for row in raw_data_content:
            row_dict = dict(zip(columns, row))
            order_time = row_dict.get("加注时间")
            oil_val = float(row_dict.get("油加注值", 0) or 0)
            avai_oil = float(row_dict.get("原油剩余量", 0) or 0)

            if isinstance(order_time, datetime.datetime):
                order_date = order_time.date()
                daily_data[order_date].append({
                    'oil_val': oil_val,
                    'avai_oil': avai_oil,
                    'order_time': order_time
                })
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
                    daily_data[order_date].append({
                        'oil_val': oil_val,
                        'avai_oil': avai_oil,
                        'order_time': parsed_datetime
                    })

        # 计算每日数据
        result = {
            'daily_order_totals': {},  # 每日订单累积总量
            'daily_shortage_errors': {},  # 每日中润亏损
            'daily_excess_errors': {},   # 每日客户亏损
            'daily_inventory_changes': {}, # 每日库存变化量
            'daily_consumption': {}  # 每日消耗量
        }

        # 按日期排序处理
        sorted_dates = sorted(daily_data.keys())
        previous_day_end_inventory = 0

        # 关键修复：正确初始化第一天的“上日结束库存”
        # 应该获取查询开始日期前一天的最后一条库存记录
        if sorted_dates:
            first_day_in_data = sorted_dates[0]
            # 查找在 first_day_in_data 之前的所有记录
            previous_day_records = [
                dict(zip(columns, r)) for r in raw_data_content 
                if (isinstance(dict(zip(columns, r)).get("加注时间"), datetime.datetime) and 
                    dict(zip(columns, r)).get("加注时间").date() < first_day_in_data)
            ]
            if previous_day_records:
                # 如果有前一天的数据，取前一天最晚的一条记录作为基准库存
                previous_day_records.sort(key=lambda x: x['加注时间'])
                previous_day_end_inventory = float(previous_day_records[-1].get("原油剩余量", 0) or 0)
            else:
                # 如果没有前一天的数据，则使用第一天最早的一条记录作为基准库存（作为备用方案）
                first_day_data = sorted(daily_data[first_day_in_data], key=lambda x: x['order_time'])
                if first_day_data:
                    previous_day_end_inventory = first_day_data[0]['avai_oil']

        for date in sorted_dates:
            day_data = sorted(daily_data[date], key=lambda x: x['order_time'])
            
            # 当天开始库存 = 上一天结束库存
            start_inventory = previous_day_end_inventory
            # 当天结束库存 = 当天最晚记录的库存
            end_inventory = day_data[-1]['avai_oil']

            # 计算当天总加油量（推断）
            total_refill_today = 0
            last_inventory_point = start_inventory
            for record in day_data:
                current_inventory_point = record['avai_oil']
                if current_inventory_point > last_inventory_point:
                    total_refill_today += (current_inventory_point - last_inventory_point)
                last_inventory_point = current_inventory_point

            # 计算库存消耗总量
            inventory_consumption = ((start_inventory - end_inventory) + total_refill_today) * barrel_count

            # 计算订单总量
            order_total = sum(item['oil_val'] for item in day_data)

            # 存储结果
            result['daily_order_totals'][date] = order_total
            result['daily_consumption'][date] = inventory_consumption

            # 计算误差
            difference = inventory_consumption - order_total
            if difference > 0:
                result['daily_shortage_errors'][date] = difference
            elif difference < 0:
                result['daily_excess_errors'][date] = abs(difference)

            # 更新上一天结束库存，为下一天做准备
            previous_day_end_inventory = end_inventory

        return result


    def calculate_monthly_errors(self, raw_data, start_date=None, end_date=None, barrel_count=1):
        """
        计算每月消耗误差数据

        Args:
            raw_data: 原始数据元组 (data, columns, raw_data)
            barrel_count (int): 油桶数量，默认为1
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            dict: 包含每月订单累积总量、中润亏损和客户亏损的数据
        """
        data, columns, raw_data_content = raw_data

        # 按月份分组数据
        monthly_data = defaultdict(list)

        for row in raw_data_content:
            row_dict = dict(zip(columns, row))
            order_time = row_dict.get("加注时间")
            oil_val = float(row_dict.get("油加注值", 0) or 0)
            avai_oil = float(row_dict.get("原油剩余量", 0) or 0)

            if isinstance(order_time, datetime.datetime):
                order_month = order_time.strftime("%Y-%m")
                monthly_data[order_month].append({
                    'oil_val': oil_val,
                    'avai_oil': avai_oil,
                    'order_time': order_time
                })
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
                    order_month = parsed_datetime.strftime("%Y-%m")
                    monthly_data[order_month].append({
                        'oil_val': oil_val,
                        'avai_oil': avai_oil,
                        'order_time': parsed_datetime
                    })

        # 计算每月数据
        result = {
            'monthly_order_totals': {},  # 每月订单累积总量
            'monthly_shortage_errors': {},  # 每月中润亏损
            'monthly_excess_errors': {},   # 每月客户亏损
            'monthly_consumption': {}  # 每月消耗量
        }

        # 按月份排序处理
        sorted_months = sorted(monthly_data.keys())

        for i, month in enumerate(sorted_months):
            month_data = monthly_data[month]

            # 计算每月订单累积总量
            monthly_order_total = sum(item['oil_val'] for item in month_data)
            result['monthly_order_totals'][month] = monthly_order_total

            # 获取当月开始和结束的原油剩余量
            if month_data:
                # 按照时间排序获取开始和结束的原油剩余量
                sorted_month_data = sorted(month_data, key=lambda x: x['order_time'])
                start_avai_oil = sorted_month_data[0]['avai_oil']    # 最早时间的原油剩余量作为当月开始值
                end_avai_oil = sorted_month_data[-1]['avai_oil']  # 最晚时间的原油剩余量作为当月结束值

                # 计算库存变化量
                # 正确的计算应该是: 结束值 - 开始值
                # 如果结果为正，表示库存增加(加油)；如果为负，表示库存减少(消耗)
                inventory_change = end_avai_oil - start_avai_oil

                # 根据新的逻辑计算每月消耗量
                monthly_consumption = 0

                # 如果原油剩余量上升（说明加油了）
                if inventory_change > 0:
                    # 如果当月有订单，则消耗量等于订单总量
                    if monthly_order_total > 0:
                        monthly_consumption = monthly_order_total
                    # 如果当月没有订单，则消耗量为0
                    else:
                        monthly_consumption = 0
                # 如果原油剩余量下降或持平（正常消耗）
                else:
                    # 消耗量应该是库存减少的绝对值
                    monthly_consumption = abs(inventory_change) * barrel_count

                # 存储每月消耗量
                result['monthly_consumption'][month] = {
                    'value': monthly_consumption,
                    'inventory_change': inventory_change,
                    'order_total': monthly_order_total
                }

                # 计算误差
                difference = monthly_consumption - monthly_order_total

                if difference > 0:  # 库存误差（消耗量>订单量）
                    result['monthly_shortage_errors'][month] = {
                        'value': difference,
                        'inventory_change': inventory_change,
                        'order_total': monthly_order_total
                    }
                elif difference < 0:  # 订单误差（订单量>消耗量）
                    result['monthly_excess_errors'][month] = {
                        'value': abs(difference),
                        'inventory_change': inventory_change,
                        'order_total': monthly_order_total
                    }

        return result



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