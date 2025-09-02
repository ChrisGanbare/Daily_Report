"""
核心模块初始化文件
"""

# 确保所有核心模块都被正确导入
from .base_report import BaseReportGenerator
from .data_manager import ReportDataManager, CustomerGroupingUtil
from .db_handler import DatabaseHandler
from .file_handler import FileHandler
from .inventory_handler import InventoryReportGenerator
from .statement_handler import CustomerStatementGenerator
from .refueling_details_handler import RefuelingDetailsReportGenerator
from .report_controller import (
    generate_inventory_reports,
    generate_customer_statement,
    generate_both_reports,
    generate_refueling_details
)

__all__ = [
    'BaseReportGenerator',
    'ReportDataManager',
    'CustomerGroupingUtil',
    'DatabaseHandler',
    'FileHandler',
    'InventoryReportGenerator',
    'CustomerStatementGenerator',
    'RefuelingDetailsReportGenerator',
    'generate_inventory_reports',
    'generate_customer_statement',
    'generate_both_reports',
    'generate_refueling_details'
]