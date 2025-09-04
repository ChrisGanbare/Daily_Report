"""测试ZR Daily Report的主程序功能"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 导入主程序模块
import zr_daily_report


class TestZRDailyReport(unittest.TestCase):
    """综合测试ZR Daily Report的主程序功能"""

    def test_import_main_modules(self):
        """测试主要模块是否能正确导入"""
        try:
            # 测试核心模块导入
            # 测试主程序导入
            import zr_daily_report  # noqa: F401
            from src.core.db_handler import DatabaseHandler  # noqa: F401
            from src.core.file_handler import FileHandler  # noqa: F401
            from src.core.inventory_handler import (  # noqa: F401
                InventoryReportGenerator,
            )
            from src.core.statement_handler import (  # noqa: F401
                CustomerStatementGenerator,
            )

            # 测试工具模块导入
            from src.utils.config_handler import ConfigHandler  # noqa: F401
            from src.utils.date_utils import parse_date  # noqa: F401

        except ImportError as e:
            self.fail(f"模块导入失败: {str(e)}")

        # 如果没有抛出异常，说明导入成功
        self.assertTrue(True)

    @patch("zr_daily_report.print_usage")
    @patch("zr_daily_report.show_mode_selection_dialog")
    def test_main_function_with_no_args(self, mock_dialog, mock_print_usage):
        """测试主程序在没有参数时的行为"""
        from zr_daily_report import main

        mock_dialog.return_value = None

        # 模拟sys.argv为空列表（没有命令行参数）
        with patch("sys.argv", ["zr_daily_report.py"]):
            main()

        # 验证调用了模式选择对话框
        mock_dialog.assert_called_once()
        mock_print_usage.assert_called_once()

    @patch("zr_daily_report.print_usage")
    @patch("zr_daily_report.show_mode_selection_dialog")
    def test_main_function_with_cancelled_dialog(self, mock_dialog, mock_print_usage):
        """测试主程序在取消对话框时的行为"""
        from zr_daily_report import main

        mock_dialog.return_value = None

        # 模拟sys.argv为空列表（没有命令行参数）
        with patch("sys.argv", ["zr_daily_report.py"]):
            with patch("builtins.print") as mock_print:
                main()
                # 验证打印了取消操作的消息
                mock_print.assert_any_call("用户取消操作，程序退出。")

    @patch("zr_daily_report.parse_arguments")
    @patch("zr_daily_report.generate_inventory_reports")
    def test_main_function_with_inventory_mode(self, mock_generate_inventory, mock_parse_args):
        """测试主程序在库存报表模式下的行为"""
        from zr_daily_report import main

        # 模拟命令行参数
        mock_args = MagicMock()
        mock_args.mode = "inventory"
        mock_parse_args.return_value = mock_args

        # 模拟sys.argv包含参数
        with patch("sys.argv", ["zr_daily_report.py", "--mode", "inventory"]):
            main()

        # 验证调用了库存报表生成函数
        mock_generate_inventory.assert_called_once()

    @patch("zr_daily_report.parse_arguments")
    @patch("zr_daily_report.generate_customer_statement")
    def test_main_function_with_statement_mode(self, mock_generate_statement, mock_parse_args):
        """测试主程序在客户对账单模式下的行为"""
        from zr_daily_report import main

        # 模拟命令行参数
        mock_args = MagicMock()
        mock_args.mode = "statement"
        mock_parse_args.return_value = mock_args

        # 模拟sys.argv包含参数
        with patch("sys.argv", ["zr_daily_report.py", "--mode", "statement"]):
            main()

        # 验证调用了客户对账单生成函数
        mock_generate_statement.assert_called_once()

    @patch("zr_daily_report.parse_arguments")
    @patch("zr_daily_report.generate_both_reports")
    def test_main_function_with_both_mode(self, mock_generate_both, mock_parse_args):
        """测试主程序在同时生成两种报表模式下的行为"""
        from zr_daily_report import main

        # 模拟命令行参数
        mock_args = MagicMock()
        mock_args.mode = "both"
        mock_parse_args.return_value = mock_args

        # 模拟sys.argv包含参数
        with patch("sys.argv", ["zr_daily_report.py", "--mode", "both"]):
            main()

        # 验证调用了综合报表生成函数
        mock_generate_both.assert_called_once()

    @patch("zr_daily_report.parse_arguments")
    @patch("zr_daily_report.generate_refueling_details")
    def test_main_function_with_refueling_mode(self, mock_generate_refueling, mock_parse_args):
        """测试主程序在加注明细模式下的行为"""
        from zr_daily_report import main

        # 模拟命令行参数
        mock_args = MagicMock()
        mock_args.mode = "refueling"
        mock_parse_args.return_value = mock_args

        # 模拟sys.argv包含参数
        with patch("sys.argv", ["zr_daily_report.py", "--mode", "refueling"]):
            main()

        # 验证调用了加注明细生成函数
        mock_generate_refueling.assert_called_once()
