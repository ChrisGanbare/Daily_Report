"""测试ZR Daily Report的主程序功能"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

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

    @patch('ZR_Daily_Report.print_usage')
    @patch('ZR_Daily_Report.show_mode_selection_dialog')
    def test_main_function_with_no_args(self, mock_dialog, mock_print_usage):
        """测试主程序在没有参数时的行为"""
        from ZR_Daily_Report import main
        mock_dialog.return_value = None
        
        # 模拟没有命令行参数的情况
        with patch('sys.argv', ['ZR_Daily_Report.py']):
            main()
            
        # 验证调用了使用说明和对话框
        mock_print_usage.assert_called_once()
        mock_dialog.assert_called_once()

    @patch('ZR_Daily_Report.generate_inventory_reports')
    def test_main_function_with_inventory_mode(self, mock_generate_inventory):
        """测试主程序在库存模式下的行为"""
        from ZR_Daily_Report import main
        
        # 模拟命令行参数
        with patch('sys.argv', ['ZR_Daily_Report.py', '--mode', 'inventory']):
            main()
            
        # 验证调用了库存报表生成函数
        mock_generate_inventory.assert_called_once()

    @patch('ZR_Daily_Report.generate_customer_statement')
    def test_main_function_with_statement_mode(self, mock_generate_statement):
        """测试主程序在对账单模式下的行为"""
        from ZR_Daily_Report import main
        
        # 模拟命令行参数
        with patch('sys.argv', ['ZR_Daily_Report.py', '--mode', 'statement']):
            main()
            
        # 验证调用了客户对账单生成函数
        mock_generate_statement.assert_called_once()

    @patch('ZR_Daily_Report.generate_inventory_reports')
    @patch('ZR_Daily_Report.generate_customer_statement')
    def test_main_function_with_both_mode(self, mock_generate_statement, mock_generate_inventory):
        """测试主程序在同时生成两种报表模式下的行为"""
        from ZR_Daily_Report import main
        mock_generate_inventory.return_value = []
        
        # 模拟命令行参数
        with patch('sys.argv', ['ZR_Daily_Report.py', '--mode', 'both']):
            main()
            
        # 验证调用了库存报表和客户对账单生成函数
        mock_generate_inventory.assert_called_once()
        mock_generate_statement.assert_called_once()