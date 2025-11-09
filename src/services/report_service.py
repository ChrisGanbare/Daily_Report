"""
报表服务模块
负责处理所有与报表生成相关的业务逻辑
"""
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import zipfile
import os
from collections import defaultdict
import math
import pandas as pd

from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.chart.axis import ChartLines
from openpyxl.chart.marker import Marker
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.drawing.line import LineProperties
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
        self._load_barrel_overrides()

    def _load_barrel_overrides(self):
        """使用pandas加载人工校准的桶数配置文件，更健壮"""
        self.barrel_overrides = {}
        override_file = Path(__file__).parent.parent.parent / "config" / "barrel_count_override.csv"
        
        logger.info(f"正在尝试加载桶数校准文件: {override_file.resolve()}")
        
        if not override_file.exists():
            logger.warning(f"桶数校准文件未找到。")
            return

        try:
            df = pd.read_csv(override_file, comment='#')
            df.columns = [col.strip() for col in df.columns]
            df = df.dropna(subset=['device_code', 'barrel_count'])
            df['device_code'] = df['device_code'].astype(str).str.strip()
            df = df[pd.to_numeric(df['barrel_count'], errors='coerce').notna()]
            df['barrel_count'] = df['barrel_count'].astype(int)
            self.barrel_overrides = pd.Series(df.barrel_count.values, index=df.device_code).to_dict()
            logger.info(f"成功加载 {len(self.barrel_overrides)} 条桶数校准记录。")
        except Exception as e:
            logger.error(f"使用pandas读取桶数校准文件时出错: {e}", exc_info=True)

    # --- Main Dispatch Method ---
    async def generate_report(
        self,
        report_type: str,
        devices: List[str], # 接收设备编码列表
        start_date: str,
        end_date: str,
    ) -> Tuple[Path, List[str]]:
        logger.info(f"收到报表生成请求: 类型='{report_type}', 设备数={len(devices)}")

        if report_type == "daily_consumption":
            return await self._generate_daily_consumption_report(
                devices, start_date, end_date
            )
        elif report_type == "monthly_consumption":
            return await self._generate_monthly_consumption_report(
                devices, start_date, end_date
            )
        else:
            raise NotImplementedError(f"报表类型 '{report_type}' 的生成逻辑尚未实现。")

    # --- Specific Report Generation Logic ---

    async def _generate_daily_consumption_report(
        self,
        device_codes: List[str],
        start_date_str: str,
        end_date_str: str,
    ) -> Tuple[Path, List[str]]:
        raw_report_data = await self.device_repo.get_daily_consumption_raw_data(
            device_codes, start_date_str, end_date_str
        )
        if not raw_report_data:
            raise ValueError("在指定日期范围内所有选定设备均未找到任何消耗数据。")

        data_by_device = defaultdict(list)
        for row in raw_report_data:
            data_by_device[row['device_code']].append(row)

        report_files = []
        warnings = []
        for device_code in device_codes:
            device_data = data_by_device.get(device_code)
            if not device_data:
                warnings.append(f"设备 {device_code} 没有可用于计算的数据，已跳过。")
                continue
            try:
                barrel_count = self.barrel_overrides.get(device_code, 1)
                logger.info(f"设备 {device_code} 使用桶数: {barrel_count}")
                final_report_data = self._calculate_final_data(device_data, barrel_count, "daily")
                customer_name = final_report_data[0].get('customer_name', '未知客户')
                oil_name = final_report_data[0].get('oil_name', '未知油品')
                report_path = self._generate_daily_detail_excel(
                    final_report_data, device_code, customer_name, oil_name, start_date_str, end_date_str, barrel_count
                )
                if report_path:
                    report_files.append(report_path)
            except Exception as e:
                warnings.append(f"为设备 {device_code} 生成Excel文件失败: {e}")
                logger.error(f"为设备 {device_code} 生成Excel文件失败: {e}", exc_info=True)
        
        if not report_files:
            raise ValueError("所有选定设备均未能成功生成报表。")

        if len(report_files) == 1:
            return report_files[0], warnings

        zip_path = Path(tempfile.gettempdir()) / f"ZR_Daily_Reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in report_files:
                if file_path:
                    zipf.write(file_path, os.path.basename(file_path))
                    os.remove(file_path)
        return zip_path, warnings

    async def _generate_monthly_consumption_report(
        self,
        device_codes: List[str],
        start_date_str: str,
        end_date_str: str,
    ) -> Tuple[Path, List[str]]:
        raw_report_data = await self.device_repo.get_monthly_consumption_raw_data(
            device_codes, start_date_str, end_date_str
        )
        if not raw_report_data:
            raise ValueError("在指定日期范围内所有选定设备均未找到任何消耗数据。")

        data_by_device = defaultdict(list)
        for row in raw_report_data:
            data_by_device[row['device_code']].append(row)

        report_files = []
        warnings = []
        for device_code in device_codes:
            device_data = data_by_device.get(device_code)
            if not device_data:
                warnings.append(f"设备 {device_code} 没有可用于计算的数据，已跳过。")
                continue
            try:
                barrel_count = self.barrel_overrides.get(device_code, 1)
                logger.info(f"设备 {device_code} 使用桶数: {barrel_count}")
                final_report_data = self._calculate_final_data(device_data, barrel_count, "monthly")
                customer_name = final_report_data[0].get('customer_name', '未知客户')
                oil_name = final_report_data[0].get('oil_name', '未知油品')
                report_path = self._generate_monthly_detail_excel(
                    final_report_data, device_code, customer_name, oil_name, start_date_str, end_date_str, barrel_count
                )
                if report_path:
                    report_files.append(report_path)
            except Exception as e:
                warnings.append(f"为设备 {device_code} 生成Excel文件失败: {e}")
                logger.error(f"为设备 {device_code} 生成Excel文件失败: {e}", exc_info=True)
        
        if not report_files:
            raise ValueError("所有选定设备均未能成功生成报表。")

        if len(report_files) == 1:
            return report_files[0], warnings

        zip_path = Path(tempfile.gettempdir()) / f"ZR_Monthly_Reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in report_files:
                if file_path:
                    zipf.write(file_path, os.path.basename(file_path))
                    os.remove(file_path)
        return zip_path, warnings

    def _calculate_final_data(self, device_raw_data: List[Dict[str, Any]], barrel_count: int, period: str) -> List[Dict[str, Any]]:
        order_volume_key = 'daily_order_volume' if period == 'daily' else 'monthly_order_volume'
        inventory_key = 'end_of_day_inventory' if period == 'daily' else 'end_of_month_inventory'
        prev_inventory_key = 'prev_day_inventory' if period == 'daily' else 'prev_month_inventory'
        refill_key = 'daily_refill' if period == 'daily' else 'monthly_refill'
        final_data = []
        for row in device_raw_data:
            prev_inventory = row.get(prev_inventory_key) or 0
            end_inventory = row.get(inventory_key) or 0
            refill = row.get(refill_key) or 0
            # 确保库存消耗量不为负数
            inventory_consumption = max(0, (prev_inventory - end_inventory) + refill)
            real_consumption = inventory_consumption * barrel_count
            order_volume = row.get(order_volume_key) or 0
            error = real_consumption - order_volume
            day_data = row.copy()
            day_data['real_consumption'] = real_consumption
            day_data['error'] = error
            final_data.append(day_data)
        return final_data

    def _generate_daily_detail_excel(self, report_data: List[Dict[str, Any]], device_code: str, customer_name: str, oil_name: str, start_date_str: str, end_date_str: str, barrel_count: int) -> Path:
        # ... (Excel generation logic remains the same)
        pass

    def _generate_monthly_detail_excel(self, report_data: List[Dict[str, Any]], device_code: str, customer_name: str, oil_name: str, start_date_str: str, end_date_str: str, barrel_count: int) -> Path:
        # ... (Excel generation logic remains the same)
        pass
