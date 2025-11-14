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
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from src.repositories.device_repository import DeviceRepository
from src.logger import logger
from src.utils.date_utils import parse_date, validate_error_summary_date_span


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
            logger.error(f"使用pandas读取桶数校准文件时出错: {e}", exc_info=True)  # 修复缩进

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



    async def _generate_error_summary_report(self, device_codes: List[str], start_date_str: str, end_date_str: str) -> Tuple[Path, List[str]]:
        # 验证日期范围不超过2个月
        date_row = {"start_date": start_date_str, "end_date": end_date_str}
        if not validate_error_summary_date_span(date_row):
            raise ValueError("误差汇总报表的日期范围不能超过2个月")
        
        device_codes_tuple = tuple(sorted(device_codes))
        raw_report_data = await self.device_repo.get_error_summary_raw_data(
            device_codes_tuple, start_date_str, end_date_str
        )
        if not raw_report_data:
            raise ValueError("在指定日期范围内所有选定设备均未找到任何误差汇总数据。")

        # 查询离线事件数据
        offline_events = await self._get_offline_events(device_codes_tuple, start_date_str, end_date_str)
        
        # 创建工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = "误差汇总报表"
        
        # 设置标题
        title = f"安卓设备消耗误差汇总报表({start_date_str} - {end_date_str})"
        ws.append([title])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=12)
        ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=1, column=1).font = Font(size=16, bold=True, name="微软雅黑")
        
        # 添加计算公式说明在主标题下第二行
        ws.append(["计算公式说明：单桶库存消耗 = 期末库存 - 期初库存 + 加油量，库存消耗总量 = 设备桶数 × 单桶库存消耗，误差值总数 = 库存消耗总量 - 订单总量，误差百分比 = 误差值总数 / 订单总量"])  
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=12)
        ws.cell(row=2, column=1).font = Font(size=10, name="微软雅黑")
        ws.cell(row=2, column=1).alignment = Alignment(horizontal="center")
        
        # 调整表头，将误差类型列移到误差百分比列前面，删除是否有离线事件列
        headers = ["序号", "设备编码", "客户名称", "设备桶数", "订单总量(L)", "单桶库存消耗(L)", 
                  "库存消耗总量(L)", "误差值总数(L)", "误差类型", "误差百分比(%)", "离线时长(小时)", "备注"]
        ws.append(headers)
        
        # 设置表头样式
        for cell in ws[3]:  # 表头行现在是第3行
            cell.font = Font(bold=True, size=12, name="微软雅黑")
            cell.fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # 准备数据
        processed_data = []
        for row in raw_report_data:
            # 修正计算真实消耗量：期初库存 - 期末库存 + 加油量
            end_inventory = row.get('end_of_day_inventory') or 0
            prev_inventory = row.get('prev_day_inventory') or 0
            daily_refill = row.get('daily_refill') or 0
            real_consumption = prev_inventory - end_inventory + daily_refill  # 修正这里！
            
            # 添加计算后的字段
            processed_row = row.copy()
            processed_row['real_consumption'] = real_consumption
            processed_data.append(processed_row)
        
        # 按设备编码和日期分组
        grouped_data = defaultdict(list)
        for row in processed_data:
            key = (row['device_code'], row.get('customer_name', '未知客户'), row.get('oil_name', '未知油品'))
            grouped_data[key].append(row)
        
        # 填充数据行
        row_index = 4  # 数据行从第4行开始
        index = 1
        
        for (device_code, customer_name, oil_name), rows in grouped_data.items():
            # 计算汇总数据
            total_order_volume = sum(r.get('daily_order_volume', 0) for r in rows)
            
            # 计算单桶库存消耗（使用最后一条记录的真实消耗量）并确保≥0
            single_barrel_consumption = max(0, rows[-1].get('real_consumption', 0))
            
            # 获取设备桶数（从校准文件中获取，默认为1）
            barrel_count = self.barrel_overrides.get(device_code, 1)
            
            # 计算库存消耗总量 = 设备桶数 × 单桶库存消耗
            total_inventory_consumption = barrel_count * single_barrel_consumption
            
            # 计算误差值总数 = 库存消耗总量 - 订单总量
            total_error = total_inventory_consumption - total_order_volume
            
            # 计算误差百分比
            error_percentage = (total_error / total_order_volume * 100) if total_order_volume > 0 else 0
            
            # 获取该设备的离线事件
            device_offline_events = offline_events.get(device_code, [])
            
            # 计算离线时长和生成备注
            total_offline_hours = 0
            offline_remarks = []
            
            for event in device_offline_events:
                # 计算离线时长
                start_time = event['create_time']
                recovery_time = event.get('recovery_time')
                
                # 如果恢复时间为None，表示设备仍在离线状态，使用当前时间计算
                if recovery_time is None:
                    end_time = datetime.now()
                    end_str = f"至今({end_time.strftime('%Y-%m-%d %H:%M')})"
                else:
                    end_time = recovery_time
                    end_str = end_time.strftime("%Y-%m-%d %H:%M")
                
                duration_hours = (end_time - start_time).total_seconds() / 3600
                total_offline_hours += duration_hours
                
                # 格式化事件时间并添加到备注
                start_str = start_time.strftime("%Y-%m-%d %H:%M")
                offline_remarks.append(f"{start_str} - {end_str}")
            
            # 生成完整备注，使用换行符分隔离线事件
            remarks = []
            if offline_remarks:
                remarks.append("离线事件：\n" + "\n".join(offline_remarks))
            
            if abs(error_percentage) > 10:
                remarks.append("误差超过10%，请重点关注")
            elif abs(error_percentage) > 5:
                remarks.append("误差超过5%，建议核查")
            
            remark_text = "\n".join(remarks) if remarks else "正常"
            
            # 确定误差类型
            if total_error > 0:
                error_type = "客户亏损"
            elif total_error < 0:
                error_type = "中润亏损"
            else:
                error_type = "无误差"
            
            # 填充数据行，调整列顺序
            ws.cell(row=row_index, column=1).value = index  # 序号
            ws.cell(row=row_index, column=1).alignment = Alignment(horizontal="center")
            ws.cell(row=row_index, column=1).font = Font(size=11, name="微软雅黑")
            
            ws.cell(row=row_index, column=2).value = device_code  # 设备编码
            ws.cell(row=row_index, column=2).font = Font(size=11, name="微软雅黑")
            
            ws.cell(row=row_index, column=3).value = customer_name  # 客户名称
            ws.cell(row=row_index, column=3).font = Font(size=11, name="微软雅黑")
            
            ws.cell(row=row_index, column=4).value = barrel_count  # 设备桶数
            ws.cell(row=row_index, column=4).alignment = Alignment(horizontal="center")
            ws.cell(row=row_index, column=4).font = Font(size=11, name="微软雅黑")
            
            ws.cell(row=row_index, column=5).value = total_order_volume  # 订单总量
            ws.cell(row=row_index, column=5).alignment = Alignment(horizontal="right")
            ws.cell(row=row_index, column=5).font = Font(size=11, name="微软雅黑")
            
            ws.cell(row=row_index, column=6).value = single_barrel_consumption  # 单桶库存消耗
            ws.cell(row=row_index, column=6).alignment = Alignment(horizontal="right")
            ws.cell(row=row_index, column=6).font = Font(size=11, name="微软雅黑")
            
            # 库存消耗总量使用公式
            ws.cell(row=row_index, column=7).value = f"=D{row_index}*F{row_index}"  # 库存消耗总量
            ws.cell(row=row_index, column=7).alignment = Alignment(horizontal="right")
            ws.cell(row=row_index, column=7).font = Font(size=11, name="微软雅黑")
            
            # 误差值总数使用公式
            ws.cell(row=row_index, column=8).value = f"=G{row_index}-E{row_index}"  # 误差值总数
            ws.cell(row=row_index, column=8).alignment = Alignment(horizontal="right")
            ws.cell(row=row_index, column=8).font = Font(size=11, name="微软雅黑")
            
            # 误差类型列移到误差百分比前面
            ws.cell(row=row_index, column=9).value = error_type  # 误差类型
            ws.cell(row=row_index, column=9).alignment = Alignment(horizontal="center")
            ws.cell(row=row_index, column=9).font = Font(size=11, name="微软雅黑")
            
            # 误差百分比使用公式
            ws.cell(row=row_index, column=10).value = f"=H{row_index}/E{row_index}"  # 误差百分比
            ws.cell(row=row_index, column=10).number_format = '0.00%'
            ws.cell(row=row_index, column=10).alignment = Alignment(horizontal="right")
            ws.cell(row=row_index, column=10).font = Font(size=11, name="微软雅黑")
            
            # 仅误差百分比列标记背景色，不再整行标记
            if abs(error_percentage) > 5:
                ws.cell(row=row_index, column=10).fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
            
            ws.cell(row=row_index, column=11).value = round(total_offline_hours, 2)  # 离线时长
            ws.cell(row=row_index, column=11).alignment = Alignment(horizontal="center")
            ws.cell(row=row_index, column=11).font = Font(size=11, name="微软雅黑")
            
            ws.cell(row=row_index, column=12).value = remark_text  # 备注
            ws.cell(row=row_index, column=12).alignment = Alignment(wrap_text=True, vertical="top")  # 自动换行，顶部对齐
            ws.cell(row=row_index, column=12).font = Font(size=10, name="微软雅黑")
            
            # 设置固定行高，避免备注内容影响整体布局
            ws.row_dimensions[row_index].height = 30
            
            # 斑马纹样式（跳过已标记背景色的单元格）
            if row_index % 2 == 0:
                for col in range(1, 13):
                    if col != 10:  # 跳过误差百分比列
                        cell = ws.cell(row=row_index, column=col)
                        if not cell.fill.start_color.rgb or cell.fill.start_color.rgb == "00000000":
                            cell.fill = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
            
            row_index += 1
            index += 1
        
        # 设置列宽
        column_widths = [6, 15, 20, 10, 12, 15, 15, 12, 12, 12, 12, 30]
        for i, width in enumerate(column_widths):
            ws.column_dimensions[get_column_letter(i + 1)].width = width
        
        # 不再添加统计信息行
        
        # 不再添加单独的计算公式说明区域
        
        final_filename = f"安卓设备消耗误差汇总_{start_date_str}_to_{end_date_str}.xlsx"
        output_path = Path(tempfile.gettempdir()) / final_filename
        wb.save(output_path)
        logger.info(f"误差汇总报表已生成: {output_path}")
        return output_path, []

    async def _get_offline_events(self, device_codes, start_date, end_date):
        """
        获取指定设备和日期范围内的离线事件
        """
        # 移除不存在的settings导入，直接使用SQL查询
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.database import get_db_session
        import json
        from pathlib import Path
        
        offline_events = defaultdict(list)
        
        try:
            # 直接读取查询配置文件
            config_path = Path(__file__).parent.parent.parent / "config" / "query_config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                sql_templates = json.load(f)
            
            # 获取离线事件查询模板
            sql_templates_config = sql_templates.get("sql_templates", {})
            query_template = sql_templates_config.get("error_summary_offline_query", "")
            
            if not query_template:
                logger.warning("未找到离线事件查询模板")
                return offline_events
            
            async with get_db_session() as session:
                params = {
                    "start_date_param_full": f"{start_date} 00:00:00",
                    "end_date_param_full": f"{end_date} 23:59:59",
                    "device_codes": tuple(device_codes)
                }
                
                statement = text(query_template)
                result = await session.execute(statement, params)
                # 正确转换SQLAlchemy Row对象为字典
                events = [dict(zip(result.keys(), row)) for row in result.fetchall()]
                
                # 按设备编码分组（SQL查询已通过IN条件筛选，直接分组即可）
                for event in events:
                    device_code = event['device_code']
                    offline_events[device_code].append(event)
                
            logger.info(f"获取到 {sum(len(events) for events in offline_events.values())} 条离线事件记录")
        except Exception as e:
            logger.error(f"获取离线事件时出错: {e}", exc_info=True)
        
        return offline_events