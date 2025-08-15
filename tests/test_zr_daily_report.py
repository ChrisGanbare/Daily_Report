"""测试ZR Daily Report的主程序功能"""
import os
import sys
import unittest

from tests.base_test import BaseTestCase

# 添加项目根目录到sys.path，确保能正确导入模块
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestZRDailyReport(BaseTestCase):
    """综合测试ZR Daily Report的主程序功能"""

    def test_import_main_modules(self):
        """测试主要模块是否能正确导入"""
        try:
            # 测试核心模块导入
            from src.core.db_handler import DatabaseHandler  # noqa: F401
            from src.core.inventory_handler import InventoryReportGenerator  # noqa: F401
            from src.core.file_handler import FileHandler  # noqa: F401
            from src.core.statement_handler import CustomerStatementGenerator  # noqa: F401
            
            # 测试工具模块导入
            from src.utils.config_handler import ConfigHandler  # noqa: F401
            from src.utils.data_validator import DataValidator  # noqa: F401
            from src.utils.date_utils import parse_date  # noqa: F401
            
            # 测试主程序导入
            import ZR_Daily_Report  # noqa: F401
            
        except ImportError as e:
            self.fail(f"模块导入失败: {str(e)}")
        
        # 如果没有抛出异常，说明导入成功
        self.assertTrue(True)