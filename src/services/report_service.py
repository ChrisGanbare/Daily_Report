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
        elif report_type == "error_summary":
            return await self._generate_error_summary_report(
                devices, start_date, end_date
            )
        elif report_type == "inventory":
            return await self._generate_inventory_report(
                devices, start_date, end_date
            )
        elif report_type == "statement":
            return await self._generate_customer_statement_report(
                devices, start_date, end_date
            )
        elif report_type == "refueling":
            return await self._generate_refueling_details_report(
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
        device_codes_tuple = tuple(sorted(device_codes))
        raw_report_data = await self.device_repo.get_daily_consumption_raw_data(
            device_codes_tuple, start_date_str, end_date_str
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
                
                if not final_report_data:
                    warnings.append(f"设备 {device_code} 计算后数据为空，已跳过。")
                    continue

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
        device_codes_tuple = tuple(sorted(device_codes))
        raw_report_data = await self.device_repo.get_monthly_consumption_raw_data(
            device_codes_tuple, start_date_str, end_date_str
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

                if not final_report_data:
                    warnings.append(f"设备 {device_code} 计算后数据为空，已跳过。")
                    continue

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
        wb = Workbook()
        ws = wb.active
        ws.title = "消耗误差分析"
        oil_name_str = f" {oil_name} " if oil_name and pd.notna(oil_name) else " "
        title = f"{device_code}{oil_name_str}每日消耗误差分析({start_date_str} - {end_date_str})"
        ws.append([title])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=20)
        ws.cell(row=1, column=1).alignment = Alignment(horizontal="center", wrap_text=True)
        ws.cell(row=1, column=1).font = Font(size=14, bold=True)
        headers = ["日期", "原油剩余量(L)", "订单累积总量(L)", "库存消耗总量(L)", "中润亏损(L)", "客户亏损(L)"]
        ws.append(headers)
        for row in report_data:
            shortage_error = max(0, row['error'])
            excess_error = max(0, -row['error'])
            ws.append([row['report_date'].isoformat(), row['end_of_day_inventory'], row['daily_order_volume'], row['real_consumption'], shortage_error, excess_error])
        column_widths = {'A': 12, 'B': 15, 'C': 18, 'D': 18, 'E': 15, 'F': 15}
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        chart = LineChart()
        chart.title = "每日消耗误差分析"
        chart.style = 13
        chart.y_axis.title = "值 (L)"
        chart.y_axis.majorGridlines = ChartLines(spPr=GraphicalProperties(noFill=True))
        chart.x_axis.title = "日期"
        chart.x_axis.number_format = 'yyyy-mm-dd'
        chart.x_axis.tickLblSkip = 3
        chart.x_axis.tickLblPos = "low"
        chart.x_axis.textRotation = 0
        chart.width = 30
        chart.height = 15
        dates = Reference(ws, min_col=1, min_row=3, max_row=len(report_data) + 2)
        data = Reference(ws, min_col=2, min_row=2, max_col=4, max_row=len(report_data) + 2)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(dates)
        s1 = chart.series[0]
        s1.graphicalProperties.line.solidFill = "0000FF"
        s1.marker = Marker(symbol="circle", size=8)
        s2 = chart.series[1]
        s2.graphicalProperties.line.solidFill = "00FF00"
        s2.marker = Marker(symbol="circle", size=8)
        s3 = chart.series[2]
        s3.graphicalProperties.line.solidFill = "800080"
        s3.marker = Marker(symbol="circle", size=8)
        ws.add_chart(chart, "H5")
        annotation_row = 34
        ws.cell(row=annotation_row, column=8).value = "计算规则说明："
        ws.cell(row=annotation_row, column=8).font = Font(bold=True)
        consumption_formula = f"库存消耗总量(L) = (前日库存 - 当日库存 + 当日加油量) * {barrel_count} (桶数)"
        ws.cell(row=annotation_row + 1, column=8).value = consumption_formula
        ws.merge_cells(start_row=annotation_row + 1, start_column=8, end_row=annotation_row + 1, end_column=15)
        ws.cell(row=annotation_row + 2, column=8).value = "中润亏损(L) = MAX(0, 库存消耗总量 - 订单累积总量)"
        ws.merge_cells(start_row=annotation_row + 2, start_column=8, end_row=annotation_row + 2, end_column=15)
        ws.cell(row=annotation_row + 3, column=8).value = "客户亏损(L) = MAX(0, 订单累积总量 - 库存消耗总量)"
        ws.merge_cells(start_row=annotation_row + 3, start_column=8, end_row=annotation_row + 3, end_column=15)
        final_filename = f"{customer_name}_{device_code}_{start_date_str}_to_{end_date_str}_每日消耗误差报表.xlsx"
        output_path = Path(tempfile.gettempdir()) / final_filename
        wb.save(output_path)
        logger.info(f"Excel报表已生成: {output_path}")
        return output_path

    def _generate_monthly_detail_excel(self, report_data: List[Dict[str, Any]], device_code: str, customer_name: str, oil_name: str, start_date_str: str, end_date_str: str, barrel_count: int) -> Path:
        wb = Workbook()
        ws = wb.active
        ws.title = "每月消耗明细"
        oil_name_str = f" {oil_name} " if oil_name and pd.notna(oil_name) else " "
        title = f"{device_code}{oil_name_str}每月消耗误差分析({start_date_str} - {end_date_str})"
        ws.append([title])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=5)
        ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=1, column=1).font = Font(size=14, bold=True)
        headers = ["月份", "订单总量(L)", "真实消耗量(L)", "误差(L)", "期末库存(L)"]
        ws.append(headers)
        for row in report_data:
            shortage_error = max(0, row['error'])
            excess_error = max(0, -row['error'])
            ws.append([row['report_month'], row['monthly_order_volume'], row['real_consumption'], shortage_error, excess_error])
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

    async def _generate_error_summary_report(
        self,
        device_codes: List[str],
        start_date_str: str,
        end_date_str: str,
    ) -> Tuple[Path, List[str]]:
        device_codes_tuple = tuple(sorted(device_codes))
        raw_report_data = await self.device_repo.get_error_summary_raw_data(
            device_codes_tuple, start_date_str, end_date_str
        )
        if not raw_report_data:
            raise ValueError("在指定日期范围内所有选定设备均未找到任何误差汇总数据。")

        wb = Workbook()
        ws = wb.active
        ws.title = "误差汇总报表"
        title = f"误差汇总报表({start_date_str} - {end_date_str})"
        ws.append([title])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=8)
        ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=1, column=1).font = Font(size=14, bold=True)
        
        headers = ["设备编码", "客户名称", "油品名称", "日期", "订单总量(L)", "真实消耗量(L)", "误差(L)", "误差类型"]
        ws.append(headers)
        
        for row in raw_report_data:
            error_type = "中润亏损" if row['error'] > 0 else "客户亏损"
            ws.append([
                row['device_code'],
                row.get('customer_name', '未知客户'),
                row.get('oil_name', '未知油品'),
                row['report_date'].isoformat(),
                row['daily_order_volume'],
                row['real_consumption'],
                abs(row['error']),
                error_type
            ])
        
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
        
        final_filename = f"误差汇总报表_{start_date_str}_to_{end_date_str}.xlsx"
        output_path = Path(tempfile.gettempdir()) / final_filename
        wb.save(output_path)
        logger.info(f"误差汇总报表已生成: {output_path}")
        return output_path, []

    async def _generate_inventory_report(
        self,
        device_codes: List[str],
        start_date_str: str,
        end_date_str: str,
    ) -> Tuple[Path, List[str]]:
        device_codes_tuple = tuple(sorted(device_codes))
        raw_report_data = await self.device_repo.get_inventory_raw_data(
            device_codes_tuple, start_date_str, end_date_str
        )
        if not raw_report_data:
            raise ValueError("在指定日期范围内所有选定设备均未找到任何库存数据。")

        wb = Workbook()
        ws = wb.active
        ws.title = "库存报表"
        title = f"库存报表({start_date_str} - {end_date_str})"
        ws.append([title])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=6)
        ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=1, column=1).font = Font(size=14, bold=True)
        
        headers = ["设备编码", "客户名称", "油品名称", "日期", "期初库存(L)", "期末库存(L)", "加油量(L)"]
        ws.append(headers)
        
        for row in raw_report_data:
            ws.append([
                row['device_code'],
                row.get('customer_name', '未知客户'),
                row.get('oil_name', '未知油品'),
                row['report_date'].isoformat(),
                row.get('prev_day_inventory', 0),
                row.get('end_of_day_inventory', 0),
                row.get('daily_refill', 0)
            ])
        
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
        
        final_filename = f"库存报表_{start_date_str}_to_{end_date_str}.xlsx"
        output_path = Path(tempfile.gettempdir()) / final_filename
        wb.save(output_path)
        logger.info(f"库存报表已生成: {output_path}")
        return output_path, []

    async def _generate_customer_statement_report(
        self,
        device_codes: List[str],
        start_date_str: str,
        end_date_str: str,
    ) -> Tuple[Path, List[str]]:
        device_codes_tuple = tuple(sorted(device_codes))
        raw_report_data = await self.device_repo.get_customer_statement_raw_data(
            device_codes_tuple, start_date_str, end_date_str
        )
        if not raw_report_data:
            raise ValueError("在指定日期范围内所有选定设备均未找到任何客户对账单数据。")

        wb = Workbook()
        ws = wb.active
        ws.title = "客户对账单"
        title = f"客户对账单({start_date_str} - {end_date_str})"
        ws.append([title])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=7)
        ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=1, column=1).font = Font(size=14, bold=True)
        
        headers = ["客户名称", "设备编码", "油品名称", "日期", "订单总量(L)", "真实消耗量(L)", "误差(L)"]
        ws.append(headers)
        
        for row in raw_report_data:
            ws.append([
                row.get('customer_name', '未知客户'),
                row['device_code'],
                row.get('oil_name', '未知油品'),
                row['report_date'].isoformat(),
                row['daily_order_volume'],
                row['real_consumption'],
                row['error']
            ])
        
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
        
        final_filename = f"客户对账单_{start_date_str}_to_{end_date_str}.xlsx"
        output_path = Path(tempfile.gettempdir()) / final_filename
        wb.save(output_path)
        logger.info(f"客户对账单已生成: {output_path}")
        return output_path, []

    async def _generate_refueling_details_report(
        self,
        device_codes: List[str],
        start_date_str: str,
        end_date_str: str,
    ) -> Tuple[Path, List[str]]:
        device_codes_tuple = tuple(sorted(device_codes))
        raw_report_data = await self.device_repo.get_refueling_details_raw_data(
            device_codes_tuple, start_date_str, end_date_str
        )
        if not raw_report_data:
            raise ValueError("在指定日期范围内所有选定设备均未找到任何加注明细数据。")

        wb = Workbook()
        ws = wb.active
        ws.title = "加注明细报表"
        title = f"加注明细报表({start_date_str} - {end_date_str})"
        ws.append([title])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=6)
        ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=1, column=1).font = Font(size=14, bold=True)
        
        headers = ["设备编码", "订单序号", "加注时间", "油品名称", "油加注值(L)", "原油剩余量(L)"]
        ws.append(headers)
        
        for row in raw_report_data:
            # 处理加注时间字段
            order_time = row.get('加注时间', '未知时间')
            if hasattr(order_time, 'isoformat'):
                order_time_str = order_time.isoformat()
            else:
                order_time_str = str(order_time)
            
            ws.append([
                row['device_code'],
                row.get('订单序号', ''),
                order_time_str,
                row.get('油品名称', '未知油品'),
                row.get('油加注值', 0),
                row.get('原油剩余量', 0)
            ])
        
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
        
        final_filename = f"加注明细报表_{start_date_str}_to_{end_date_str}.xlsx"
        output_path = Path(tempfile.gettempdir()) / final_filename
        wb.save(output_path)
        logger.info(f"加注明细报表已生成: {output_path}")
        return output_path, []