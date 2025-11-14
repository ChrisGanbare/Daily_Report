"""
客户对账单生成器 - 基于development-copy分支的业务逻辑重构
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import tempfile

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class CustomerStatementGenerator:
    """客户对账单生成器"""
    
    def __init__(self, template_path: Optional[str] = None):
        """
        初始化客户对账单生成器
        
        Args:
            template_path: Excel模板文件路径，如果为None则使用默认模板
        """
        self.template_path = template_path
        self.default_template_path = self._get_default_template_path()
    
    def _get_default_template_path(self) -> str:
        """获取默认模板路径"""
        # 这里可以设置默认的模板路径
        return ""
    
    def generate_report(self, 
                       customer_data: Dict[str, Any], 
                       devices_data: List[Dict[str, Any]],
                       output_dir: str,
                       start_date: str,
                       end_date: str) -> str:
        """
        生成客户对账单
        
        Args:
            customer_data: 客户基础信息
            devices_data: 设备数据列表
            output_dir: 输出目录
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            生成的Excel文件路径
        """
        logger.info(f"开始生成客户对账单: {customer_data.get('customer_name', '未知客户')}")
        
        try:
            # 创建Excel工作簿
            if self.template_path and os.path.exists(self.template_path):
                wb = load_workbook(self.template_path)
            else:
                wb = Workbook()
            
            # 更新主页工作表
            self._update_homepage_sheet(wb, customer_data, devices_data, start_date, end_date)
            
            # 更新月度对比工作表
            self._update_monthly_comparison_sheet(wb, devices_data, start_date, end_date)
            
            # 生成文件名
            customer_name = customer_data.get('customer_name', '未知客户').replace('/', '_')
            filename = f"{customer_name}_客户对账单_{start_date}_to_{end_date}.xlsx"
            output_path = Path(output_dir) / filename
            
            # 保存文件
            wb.save(output_path)
            logger.info(f"客户对账单已生成: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"生成客户对账单失败: {e}", exc_info=True)
            raise
    
    def _update_homepage_sheet(self, 
                              wb: Workbook, 
                              customer_data: Dict[str, Any],
                              devices_data: List[Dict[str, Any]],
                              start_date: str,
                              end_date: str) -> None:
        """
        更新主页工作表
        
        Args:
            wb: Excel工作簿对象
            customer_data: 客户基础信息
            devices_data: 设备数据列表
            start_date: 开始日期
            end_date: 结束日期
        """
        # 获取或创建主页工作表
        if "主页" in wb.sheetnames:
            ws = wb["主页"]
            ws.delete_rows(1, ws.max_row)  # 清空现有内容
        else:
            ws = wb.active
            ws.title = "主页"
        
        # 设置标题和基础信息
        self._setup_homepage_header(ws, customer_data, start_date, end_date)
        
        # 添加设备数据表格
        self._add_devices_table(ws, devices_data)
        
        # 添加备注信息
        self._add_notes_section(ws, len(devices_data))
        
        # 调整列宽和格式
        self._adjust_homepage_formatting(ws)
    
    def _setup_homepage_header(self, 
                              ws, 
                              customer_data: Dict[str, Any],
                              start_date: str,
                              end_date: str) -> None:
        """设置主页标题和基础信息"""
        # 主标题
        ws.append(["客户对账单"])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=8)
        title_cell = ws.cell(row=1, column=1)
        title_cell.font = Font(size=16, bold=True)
        title_cell.alignment = Alignment(horizontal="center")
        
        # 客户信息
        customer_name = customer_data.get('customer_name', '未知客户')
        ws.append(["客户名称:", customer_name])
        ws.append(["日期范围:", f"{start_date} 至 {end_date}"])
        ws.append(["生成时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        
        # 空行
        ws.append([])
    
    def _add_devices_table(self, ws, devices_data: List[Dict[str, Any]]) -> None:
        """添加设备数据表格"""
        # 表格标题
        headers = ["设备编号", "设备名称", "油品名称", "期初库存(L)", "期末库存(L)", 
                  "加油量(L)", "订单量(L)", "实际消耗(L)", "误差(L)"]
        ws.append(headers)
        
        # 设置表头样式
        for col in range(1, len(headers) + 1):
            header_cell = ws.cell(row=ws.max_row, column=col)
            header_cell.font = Font(bold=True)
            header_cell.fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
        
        # 添加设备数据行
        for device in devices_data:
            row_data = [
                device.get('device_code', ''),
                device.get('device_name', ''),
                device.get('oil_name', ''),
                device.get('beginning_inventory', 0),
                device.get('ending_inventory', 0),
                device.get('refill_volume', 0),
                device.get('order_volume', 0),
                device.get('actual_consumption', 0),
                device.get('error', 0)
            ]
            ws.append(row_data)
    
    def _add_notes_section(self, ws, device_count: int) -> None:
        """添加备注信息"""
        # 空行
        ws.append([])
        ws.append([])
        
        # 备注标题
        ws.append(["备注:"])
        note_cell = ws.cell(row=ws.max_row, column=1)
        note_cell.font = Font(bold=True)
        
        # 备注内容
        notes = [
            f"1. 本对账单包含 {device_count} 台设备的数据",
            "2. 实际消耗 = (期初库存 - 期末库存 + 加油量)",
            "3. 误差 = 实际消耗 - 订单量",
            "4. 正误差表示中润亏损，负误差表示客户亏损"
        ]
        
        for note in notes:
            ws.append([note])
    
    def _adjust_homepage_formatting(self, ws) -> None:
        """调整主页格式"""
        # 设置列宽
        column_widths = {'A': 12, 'B': 15, 'C': 15, 'D': 12, 'E': 12, 
                        'F': 10, 'G': 10, 'H': 12, 'I': 10}
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # 设置数字格式
        for row in range(5, ws.max_row + 1):  # 从数据行开始
            for col in range(4, 10):  # D-I列（数字列）
                cell = ws.cell(row=row, column=col)
                if isinstance(cell.value, (int, float)):
                    cell.number_format = '0.00'
    
    def _update_monthly_comparison_sheet(self, 
                                       wb: Workbook, 
                                       devices_data: List[Dict[str, Any]],
                                       start_date: str,
                                       end_date: str) -> None:
        """
        更新月度对比工作表
        
        Args:
            wb: Excel工作簿对象
            devices_data: 设备数据列表
            start_date: 开始日期
            end_date: 结束日期
        """
        # 创建或获取月度对比工作表
        if "月度对比" in wb.sheetnames:
            ws = wb["月度对比"]
            ws.delete_rows(1, ws.max_row)
        else:
            ws = wb.create_sheet("月度对比")
        
        # 设置月度对比表格
        self._setup_monthly_comparison_table(ws, devices_data, start_date, end_date)
    
    def _setup_monthly_comparison_table(self, ws, devices_data: List[Dict[str, Any]], start_date: str, end_date: str) -> None:
        """设置月度对比表格"""
        # 标题
        ws.append(["月度消耗对比分析"])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=10)
        title_cell = ws.cell(row=1, column=1)
        title_cell.font = Font(size=14, bold=True)
        title_cell.alignment = Alignment(horizontal="center")
        
        # 日期范围
        ws.append([f"日期范围: {start_date} 至 {end_date}"])
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=10)
        
        # 空行
        ws.append([])
        
        # 按设备和月份组织数据
        monthly_data = self._organize_monthly_data(devices_data, start_date, end_date)
        
        # 生成月度对比表格
        self._generate_monthly_comparison_grid(ws, monthly_data)
    
    def _organize_monthly_data(self, devices_data: List[Dict[str, Any]], start_date: str, end_date: str) -> Dict[str, Any]:
        """按设备和月份组织数据"""
        # 这里实现月度数据组织逻辑
        # 基于development-copy分支的业务逻辑
        monthly_data = {}
        
        # 简化实现：按设备分组
        for device in devices_data:
            device_code = device.get('device_code')
            if device_code not in monthly_data:
                monthly_data[device_code] = {
                    'device_name': device.get('device_name'),
                    'oil_name': device.get('oil_name'),
                    'months': {}
                }
        
        return monthly_data
    
    def _generate_monthly_comparison_grid(self, ws, monthly_data: Dict[str, Any]) -> None:
        """生成月度对比网格"""
        # 这里实现月度对比表格的生成逻辑
        # 基于development-copy分支的业务逻辑
        
        # 简化实现：显示设备列表
        headers = ["设备编号", "设备名称", "油品名称", "备注"]
        ws.append(headers)
        
        # 设置表头样式
        for col in range(1, len(headers) + 1):
            header_cell = ws.cell(row=ws.max_row, column=col)
            header_cell.font = Font(bold=True)
        
        # 添加设备行
        for device_code, device_info in monthly_data.items():
            ws.append([
                device_code,
                device_info['device_name'],
                device_info['oil_name'],
                "月度对比数据待完善"
            ])


class BaseReportGenerator:
    """报表生成器基类"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_input_data(self, data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        raise NotImplementedError("子类必须实现此方法")
    
    def generate(self, data: Dict[str, Any]) -> str:
        """生成报表"""
        raise NotImplementedError("子类必须实现此方法")