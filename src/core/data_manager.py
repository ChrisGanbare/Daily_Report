"""
报表数据管理器模块
负责统一管理报表所需的数据获取和处理，避免重复数据库查询
"""
import datetime
from collections import defaultdict
from src.utils.date_utils import parse_date

class ReportDataManager:
    """报表数据管理器，负责统一管理报表所需的数据获取和处理"""
    
    def __init__(self, db_handler):
        self.db_handler = db_handler
        self._raw_data_cache = {}
        
    def fetch_raw_data(self, device_id, query_template, start_date, end_date):
        cache_key = (device_id, query_template, start_date, end_date)
        if cache_key not in self._raw_data_cache:
            print("  正在获取设备原始数据...")
            data, columns, raw_data = self.db_handler.fetch_generic_data(
                device_id, query_template, start_date, end_date
            )
            self._raw_data_cache[cache_key] = (data, columns, raw_data)
        return self._raw_data_cache[cache_key]
        
    def extract_inventory_data(self, raw_data):
        return raw_data[0]
        
    def calculate_daily_usage(self, raw_data):
        data, columns, raw_data_content = raw_data
        daily_usage = defaultdict(float)
        
        for row in raw_data_content:
            row_dict = dict(zip(columns, row))
            order_time = row_dict.get("加注时间")
            oil_val = row_dict.get("油加注值", 0) if row_dict.get("油加注值") is not None else 0
            
            if isinstance(order_time, datetime.datetime):
                order_date = order_time.date()
                daily_usage[order_date] += float(oil_val)
            elif isinstance(order_time, str):
                try:
                    order_date = parse_date(order_time).date()
                    daily_usage[order_date] += float(oil_val)
                except (ValueError, TypeError):
                    continue
        
        return sorted(daily_usage.items())
        
    def calculate_monthly_usage(self, raw_data, start_date_str=None, end_date_str=None):
        data, columns, raw_data_content = raw_data
        monthly_usage = defaultdict(float)
        
        for row in raw_data_content:
            row_dict = dict(zip(columns, row))
            order_time = row_dict.get("加注时间")
            oil_val = row_dict.get("油加注值", 0) if row_dict.get("油加注值") is not None else 0
            
            if order_time:
                try:
                    dt_obj = parse_date(str(order_time))
                    order_month = dt_obj.strftime("%Y-%m")
                    monthly_usage[order_month] += float(oil_val)
                except (ValueError, TypeError):
                    continue
        
        return sorted(monthly_usage.items())

    def calculate_daily_errors(self, raw_data, start_date_str, end_date_str, barrel_count=1, device_id=None):
        """
        计算每日消耗误差数据，确保处理连续的时间序列。
        对于没有订单的日期，使用距离起始日期最近的一次原油剩余量。
        
        Args:
            raw_data: 原始数据，格式为 (data, columns, raw_data_content)
            start_date_str: 起始日期字符串
            end_date_str: 结束日期字符串
            barrel_count: 油桶数量
            device_id: 设备ID，用于查询起始日期之前的数据（可选）
        """
        data, columns, raw_data_content = raw_data
        
        daily_data = defaultdict(list)
        
        for row in raw_data_content:
            row_dict = dict(zip(columns, row))
            order_time_val = row_dict.get("加注时间")
            if not order_time_val:
                continue
            try:
                order_time = parse_date(str(order_time_val))
                order_date = order_time.date()
                
                record_info = {
                    'oil_val': float(row_dict.get("油加注值", 0) or 0),
                    'avai_oil': float(row_dict.get("原油剩余量", 0) or 0),
                    'order_time': order_time,
                    'order_date': order_date
                }
                
                daily_data[order_date].append(record_info)
            except (ValueError, TypeError):
                continue

        result = {
            'daily_order_totals': {},
            'daily_shortage_errors': {},
            'daily_excess_errors': {},
            'daily_consumption': {},
            'daily_end_inventory': {}
        }
        start_date = parse_date(start_date_str).date()
        end_date = parse_date(end_date_str).date()
        all_dates = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]

        # 获取起始日期之前的最后一次原油剩余量
        previous_day_end_inventory = 0
        
        # 首先尝试从 raw_data_content 中查找起始日期之前的记录
        previous_records = []
        for r in raw_data_content:
            try:
                row_dict = dict(zip(columns, r))
                order_time_val = row_dict.get("加注时间")
                if order_time_val:
                    order_date = parse_date(str(order_time_val)).date()
                    if order_date < start_date:
                        previous_records.append(row_dict)
            except (ValueError, TypeError):
                continue
        
        if previous_records:
            previous_records.sort(key=lambda x: parse_date(str(x.get("加注时间", ""))))
            previous_day_end_inventory = float(previous_records[-1].get("原油剩余量", 0) or 0)
        else:
            # 如果查询结果中没有起始日期之前的记录，尝试从数据库查询
            if device_id and self.db_handler:
                try:
                    # 查询起始日期之前最近的一条记录
                    query = (
                        f"SELECT a.avai_oil AS '原油剩余量' "
                        f"FROM oil.t_device_oil_order a "
                        f"WHERE a.device_id = {device_id} "
                        f"AND a.status = 1 "
                        f"AND a.order_time < '{start_date_str} 00:00:00' "
                        f"ORDER BY a.order_time DESC LIMIT 1"
                    )
                    results, cols = self.db_handler._execute_query(device_id, query, None, None)
                    if results and len(results) > 0 and cols:
                        # 获取原油剩余量列的值
                        row_dict = dict(zip(cols, results[0]))
                        avai_oil = row_dict.get("原油剩余量") or row_dict.get("avai_oil")
                        if avai_oil is not None:
                            previous_day_end_inventory = float(avai_oil)
                except Exception as e:
                    print(f"  警告：无法查询起始日期之前的数据: {e}")
            
            # 如果仍然没有找到，且查询范围内有数据，说明起始日期之前确实没有数据
            # 这种情况下，对于没有订单的日期，应该保持起始库存不变
            # 但如果起始日期在第一个数据日期之后，说明起始日期之前没有数据，使用第一个数据日期的第一个记录的值
            if previous_day_end_inventory == 0 and daily_data:
                first_data_day = min(daily_data.keys())
                if start_date > first_data_day:
                    # 起始日期在第一个数据日期之后，使用第一个数据日期的第一个记录的值
                    first_day_records = sorted(daily_data[first_data_day], key=lambda x: x['order_time'])
                    if first_day_records:
                        previous_day_end_inventory = first_day_records[0]['avai_oil']

        # 遍历所有日期，为每个日期生成数据
        for current_date in all_dates:
            start_inventory = previous_day_end_inventory

            if current_date in daily_data:
                # 有订单的日期：使用当天的最后一个记录的原油剩余量
                day_records = sorted(daily_data[current_date], key=lambda x: x['order_time'])
                end_inventory = day_records[-1]['avai_oil']
                
                total_refill_today = 0
                last_inventory_point = start_inventory
                for record in day_records:
                    current_inventory_point = record['avai_oil']
                    if current_inventory_point > last_inventory_point:
                        total_refill_today += (current_inventory_point - last_inventory_point)
                    last_inventory_point = current_inventory_point

                inventory_consumption = ((start_inventory - end_inventory) + total_refill_today)
                order_total = sum(item['oil_val'] for item in day_records)
            else:
                # 没有订单的日期：使用距离起始日期最近的一次原油剩余量
                # 根据用户需求，应该使用起始日期之前最近的一次原油剩余量
                end_inventory = start_inventory
                inventory_consumption = 0
                order_total = 0

            result['daily_order_totals'][current_date] = order_total
            result['daily_consumption'][current_date] = inventory_consumption * barrel_count
            # 原油剩余量是单个油桶的值，不需要除以桶数
            result['daily_end_inventory'][current_date] = end_inventory

            difference = (inventory_consumption * barrel_count) - order_total
            if difference > 0:
                result['daily_shortage_errors'][current_date] = difference
            elif difference < 0:
                result['daily_excess_errors'][current_date] = abs(difference)

            previous_day_end_inventory = end_inventory

        return result

    def calculate_monthly_errors(self, raw_data, start_date_str, end_date_str, barrel_count=1):
        """
        计算每月消耗误差数据，确保处理连续的时间序列。
        """
        data, columns, raw_data_content = raw_data

        monthly_data = defaultdict(list)
        for row in raw_data_content:
            row_dict = dict(zip(columns, row))
            order_time_val = row_dict.get("加注时间")
            if not order_time_val:
                continue
            try:
                order_time = parse_date(str(order_time_val))
                order_month = order_time.strftime("%Y-%m")
                monthly_data[order_month].append({
                    'oil_val': float(row_dict.get("油加注值", 0) or 0),
                    'avai_oil': float(row_dict.get("原油剩余量", 0) or 0),
                    'order_time': order_time
                })
            except (ValueError, TypeError):
                continue

        result = {
            'monthly_order_totals': {},
            'monthly_shortage_errors': {},
            'monthly_excess_errors': {},
            'monthly_consumption': {}
        }
        start_date = parse_date(start_date_str).date()
        end_date = parse_date(end_date_str).date()
        
        sorted_months = []
        current_month = start_date.replace(day=1)
        while current_month <= end_date:
            sorted_months.append(current_month.strftime("%Y-%m"))
            next_month_day1 = (current_month + datetime.timedelta(days=32)).replace(day=1)
            current_month = next_month_day1

        previous_month_end_inventory = 0
        first_month_start_date = start_date.replace(day=1)
        previous_records = [
            dict(zip(columns, r)) for r in raw_data_content
            if dict(zip(columns, r)).get("加注时间") and parse_date(str(dict(zip(columns, r)).get("加注时间"))).date() < first_month_start_date
        ]
        if previous_records:
            previous_records.sort(key=lambda x: parse_date(str(x['加注时间'])))
            previous_month_end_inventory = float(previous_records[-1].get("原油剩余量", 0) or 0)
        else:
            if monthly_data:
                first_data_month = min(monthly_data.keys())
                if start_date.strftime("%Y-%m") >= first_data_month:
                     previous_month_end_inventory = 0

        for month_str in sorted_months:
            start_inventory = previous_month_end_inventory

            if month_str in monthly_data:
                month_records = sorted(monthly_data[month_str], key=lambda x: x['order_time'])
                end_inventory = month_records[-1]['avai_oil']
                
                total_refill_this_month = 0
                last_inventory_point = start_inventory
                for record in month_records:
                    current_inventory_point = record['avai_oil']
                    if current_inventory_point > last_inventory_point:
                        total_refill_this_month += (current_inventory_point - last_inventory_point)
                    last_inventory_point = current_inventory_point

                inventory_consumption = ((start_inventory - end_inventory) + total_refill_this_month)
                order_total = sum(item['oil_val'] for item in month_records)
            else:
                end_inventory = start_inventory
                inventory_consumption = 0
                order_total = 0

            consumption_with_barrel = inventory_consumption * barrel_count
            result['monthly_order_totals'][month_str] = order_total
            result['monthly_consumption'][month_str] = {'value': consumption_with_barrel}
            
            difference = consumption_with_barrel - order_total
            if difference > 0:
                result['monthly_shortage_errors'][month_str] = {'value': difference}
            elif difference < 0:
                result['monthly_excess_errors'][month_str] = {'value': abs(difference)}

            previous_month_end_inventory = end_inventory

        return result

class CustomerGroupingUtil:
    @staticmethod
    def group_devices_by_customer(devices_data):
        customers_data = {}
        for device_data in devices_data:
            customer_id = device_data.get('customer_id')
            customer_name = device_data.get('customer_name')
            if customer_id is None or customer_name is None:
                continue
            if customer_id not in customers_data:
                customers_data[customer_id] = {
                    'customer_name': customer_name,
                    'devices': []
                }
            customers_data[customer_id]['devices'].append(device_data)
        return customers_data

    @staticmethod
    def get_customer_list(devices_data):
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
