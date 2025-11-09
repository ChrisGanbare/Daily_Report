"""
报表服务模块
负责处理所有与报表生成相关的业务逻辑
"""
import tempfile
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import zipfile
import os
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

from src.repositories.device_repository import DeviceRepository
from src.logger import logger


class ReportService:
    """
    封装报表生成的核心业务逻辑
    """

    def __init__(self, device_repo: DeviceRepository):
        self.device_repo = device_repo

    # --- Main Dispatch Method ---
    async def generate_report(
        self,
        report_type: str,
        devices: List[str], # 接收设备编码列表
        start_date: str,
        end_date: str,
    ) -> Path:
        """
        主调度方法，根据报表类型调用相应的生成逻辑。
        """
        logger.info(f"收到报表生成请求: 类型='{report_type}', 设备数={len(devices)}")

        if report_type == "daily_consumption":
            return await self._generate_daily_consumption_report(
                devices, start_date, end_date
            )
        elif report_type == "monthly_consumption":
            return await self._generate_monthly_consumption_report(
                devices, start_date, end_date
            )
        # --- Future report types can be added here ---
        else:
            raise NotImplementedError(f"报表类型 '{report_type}' 的生成逻辑尚未实现。")

    # --- Specific Report Generation Logic ---

    async def _generate_daily_consumption_report(
        self,
        device_codes: List[str],
        start_date_str: str,
        end_date_str: str,
    ) -> Path:
        """
        为设备列表生成每日消耗误差报表。
        """
        raw_report_data = await self.device_repo.get_daily_consumption_raw_data(
            device_codes, start_date_str, end_date_str
        )

        if not raw_report_data:
            raise ValueError("在指定日期范围内未找到任何设备的消耗数据。")

        data_by_device = defaultdict(list)
        for row in raw_report_data:
            data_by_device[row['device_code']].append(row)

        report_files = []
        for device_code in device_codes:
            device_data = data_by_device.get(device_code)
            if not device_data:
                logger.warning(f"设备 {device_code} 没有可用于计算的数据，已跳过。")
                continue

            try:
                logger.info(f"正在为设备 {device_code} 计算最佳桶数...")
                best_barrel_count, final_report_data = self._find_best_barrel_count(device_data, "daily")
                logger.info(f"设备 {device_code} 的最佳桶数为: {best_barrel_count}")

                customer_name = final_report_data[0].get('customer_name', '未知客户')
                
                report_path = self._generate_daily_detail_excel(
                    final_report_data, device_code, customer_name, start_date_str, end_date_str, best_barrel_count
                )
                report_files.append(report_path)
            except Exception as e:
                logger.error(f"为设备 {device_code} 生成Excel文件失败: {e}", exc_info=True)
                continue
        
        if not report_files:
            raise ValueError("所有设备的报表都生成失败，无法创建压缩包。")

        if len(report_files) == 1:
            return report_files[0]

        zip_path = Path(tempfile.gettempdir()) / f"ZR_Daily_Reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in report_files:
                zipf.write(file_path, os.path.basename(file_path))
                os.remove(file_path)
        return zip_path

    async def _generate_monthly_consumption_report(
        self,
        device_codes: List[str],
        start_date_str: str,
        end_date_str: str,
    ) -> Path:
        """
        为设备列表生成每月消耗误差报表。
        """
        raw_report_data = await self.device_repo.get_monthly_consumption_raw_data(
            device_codes, start_date_str, end_date_str
        )

        if not raw_report_data:
            raise ValueError("在指定日期范围内未找到任何设备的消耗数据。")

        data_by_device = defaultdict(list)
        for row in raw_report_data:
            data_by_device[row['device_code']].append(row)

        report_files = []
        for device_code in device_codes:
            device_data = data_by_device.get(device_code)
            if not device_data:
                logger.warning(f"设备 {device_code} 没有可用于计算的数据，已跳过。")
                continue

            try:
                logger.info(f"正在为设备 {device_code} 计算最佳桶数...")
                best_barrel_count, final_report_data = self._find_best_barrel_count(device_data, "monthly")
                logger.info(f"设备 {device_code} 的最佳桶数为: {best_barrel_count}")

                customer_name = final_report_data[0].get('customer_name', '未知客户')
                
                report_path = self._generate_monthly_detail_excel(
                    final_report_data, device_code, customer_name, start_date_str, end_date_str, best_barrel_count
                )
                report_files.append(report_path)
            except Exception as e:
                logger.error(f"为设备 {device_code} 生成Excel文件失败: {e}", exc_info=True)
                continue
        
        if not report_files:
            raise ValueError("所有设备的报表都生成失败，无法创建压缩包。")

        if len(report_files) == 1:
            return report_files[0]

        zip_path = Path(tempfile.gettempdir()) / f"ZR_Monthly_Reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in report_files:
                zipf.write(file_path, os.path.basename(file_path))
                os.remove(file_path)
        return zip_path

    def _find_best_barrel_count(self, device_raw_data: List[Dict[str, Any]], period: str) -> tuple[int, List[Dict[str, Any]]]:
        """
        在Python内存中计算最佳桶数。
        """
        best_fit = {'barrel_count': 1, 'total_error': float('inf')}
        final_report_data_for_best_fit = []

        order_volume_key = 'daily_order_volume' if period == 'daily' else 'monthly_order_volume'
        inventory_key = 'end_of_day_inventory' if period == 'daily' else 'end_of_month_inventory'
        prev_inventory_key = 'prev_day_inventory' if period == 'daily' else 'prev_month_inventory'
        refill_key = 'daily_refill' if period == 'daily' else 'monthly_refill'

        for barrel_count in range(1, 6): # 1 to 5
            total_absolute_error = 0
            temp_report_data = []

            for row in device_raw_data:
                prev_inventory = row[prev_inventory_key] or 0
                end_inventory = row[inventory_key] or 0
                refill = row[refill_key] or 0
                
                inventory_consumption = (prev_inventory - end_inventory) + refill
                real_consumption = inventory_consumption * barrel_count
                
                order_volume = row[order_volume_key] or 0
                error = real_consumption - order_volume
                total_absolute_error += abs(error)

                day_data = row.copy()
                day_data['real_consumption'] = real_consumption
                day_data['error'] = error
                temp_report_data.append(day_data)

            if total_absolute_error < best_fit['total_error']:
                best_fit['total_error'] = total_absolute_error
                best_fit['barrel_count'] = barrel_count
                final_report_data_for_best_fit = temp_report_data
        
        return best_fit['barrel_count'], final_report_data_for_best_fit

    def _generate_daily_detail_excel(self, report_data: List[Dict[str, Any]], device_code: str, customer_name: str, start_date_str: str, end_date_str: str, best_barrel_count: int) -> Path:
        wb = Workbook()
        ws = wb.active
        ws.title = "每日消耗明细"
        title = f"{customer_name}_{device_code} 每日消耗误差报表 ({start_date_str} to {end_date_str}) - 最佳桶数: {best_barrel_count}"
        ws.append([title])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=5)
        ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=1, column=1).font = Font(size=14, bold=True)
        headers = ["日期", "订单总量(L)", "真实消耗量(L)", "误差(L)", "期末库存(L)"]
        ws.append(headers)
        for row in report_data:
            ws.append([row['report_date'].isoformat(), row['daily_order_volume'], row['real_consumption'], row['error'], row['end_of_day_inventory']])
        for i, col in enumerate(ws.columns):
            max_length = 0
            column_letter = get_column_letter(i + 1)
            for cell in col:
                if cell.value is not None:
                    cell_length = len(str(cell.value))
                    if cell_length > max_length:
                        max_length = cell_length
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = adjusted_width
        final_filename = f"{customer_name}_{device_code}_{start_date_str}_to_{end_date_str}_每日消耗误差报表.xlsx"
        output_path = Path(tempfile.gettempdir()) / final_filename
        wb.save(output_path)
        logger.info(f"Excel报表已生成: {output_path}")
        return output_path

    def _generate_monthly_detail_excel(self, report_data: List[Dict[str, Any]], device_code: str, customer_name: str, start_date_str: str, end_date_str: str, best_barrel_count: int) -> Path:
        wb = Workbook()
        ws = wb.active
        ws.title = "每月消耗明细"
        title = f"{customer_name}_{device_code} 每月消耗误差报表 ({start_date_str} to {end_date_str}) - 最佳桶数: {best_barrel_count}"
        ws.append([title])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=5)
        ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=1, column=1).font = Font(size=14, bold=True)
        headers = ["月份", "订单总量(L)", "真实消耗量(L)", "误差(L)", "期末库存(L)"]
        ws.append(headers)
        for row in report_data:
            ws.append([row['report_month'], row['monthly_order_volume'], row['real_consumption'], row['error'], row['end_of_month_inventory']])
        for i, col in enumerate(ws.columns):
            max_length = 0
            column_letter = get_column_letter(i + 1)
            for cell in col:
                if cell.value is not None:
                    cell_length = len(str(cell.value))
                    if cell_length > max_length:
                        max_length = cell_length
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = adjusted_width
        final_filename = f"{customer_name}_{device_code}_{start_date_str}_to_{end_date_str}_每月消耗误差报表.xlsx"
        output_path = Path(tempfile.gettempdir()) / final_filename
        wb.save(output_path)
        logger.info(f"Excel报表已生成: {output_path}")
        return output_path
