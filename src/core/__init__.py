"""
核心模块初始化文件
"""

# 只导出最基础的、不会引起循环依赖的基类或工具类
from .base_report import BaseReportGenerator
from .db_handler import DatabaseHandler
from .file_handler import FileHandler

__all__ = [
    'BaseReportGenerator',
    'DatabaseHandler',
    'FileHandler'
]
