"""测试ZR Daily Report的主程序功能"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.dirname(__file__))

# 导入主程序模块
import zr_daily_report
from zr_daily_report import main, get_user_input


class TestZRDailyReport(unittest.TestCase):
    """综合测试ZR Daily Report的主程序功能"""

    def test_import_main_modules(self):
        """测试主要模块是否能正确导入"""
        try:
            # 测试核心模块导入
            # 测试主程序导入
            import zr_daily_report  # noqa: F401
            from zr_daily_report.src.core.db_handler import DatabaseHandler  # noqa: F401
            from zr_daily_report.src.core.file_handler import FileHandler  # noqa: F401
            from zr_daily_report.src.core.inventory_handler import (  # noqa: F401
                InventoryReportGenerator,
            )
            from zr_daily_report.src.core.statement_handler import (  # noqa: F401
                CustomerStatementGenerator,
            )

            # 测试工具模块导入
            from zr_daily_report.src.utils.config_handler import ConfigHandler  # noqa: F401
            from zr_daily_report.src.utils.date_utils import parse_date  # noqa: F401

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

        # 模拟没有命令行参数的情况
        with patch("sys.argv", ["zr_daily_report.py"]):
            main()

        # 验证调用了使用说明和对话框
        mock_print_usage.assert_called_once()
        mock_dialog.assert_called_once()

    @patch("zr_daily_report.generate_inventory_reports")
    def test_main_function_with_inventory_mode(self, mock_generate_inventory):
        """测试主程序在库存模式下的行为"""
        from zr_daily_report import main

        # 模拟命令行参数
        with patch("sys.argv", ["zr_daily_report.py", "--mode", "inventory"]):
            main()

        # 验证调用了库存报表生成函数
        mock_generate_inventory.assert_called_once()

    @patch("zr_daily_report.generate_customer_statement")
    def test_main_function_with_statement_mode(self, mock_generate_statement):
        """测试主程序在对账单模式下的行为"""
        from zr_daily_report import main

        # 模拟命令行参数
        with patch("sys.argv", ["zr_daily_report.py", "--mode", "statement"]):
            main()

        # 验证调用了客户对账单生成函数
        mock_generate_statement.assert_called_once()

    @patch("zr_daily_report.generate_inventory_reports")
    @patch("zr_daily_report.generate_customer_statement")
    def test_main_function_with_both_mode(
        self, mock_generate_statement, mock_generate_inventory
    ):
        """测试主程序在同时生成两种报表模式下的行为"""
        from zr_daily_report import main

        mock_generate_inventory.return_value = []

        # 模拟命令行参数
        with patch("sys.argv", ["zr_daily_report.py", "--mode", "both"]):
            main()

        # 验证调用了库存报表和客户对账单生成函数
        mock_generate_inventory.assert_called_once()
        mock_generate_statement.assert_called_once()

    @patch("zr_daily_report.load_config")
    @patch("zr_daily_report.generate_inventory_reports")
    @patch("zr_daily_report.generate_customer_statement")
    def test_main_function_with_both_mode_device_data_passed(
        self, mock_generate_statement, mock_generate_inventory, mock_load_config
    ):
        """测试主程序在both模式下正确传递设备数据"""
        from zr_daily_report import main

        # 模拟配置加载
        mock_load_config.return_value = {
            "db_config": {
                "host": "localhost",
                "port": 3306,
                "user": "test_user",
                "password": "test_password",
                "database": "test_db"
            },
            "sql_templates": {
                "device_id_query": "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s",
                "inventory_query": "SELECT * FROM oil.t_order WHERE device_id = {device_id}",
                "customer_query": "SELECT customer_name FROM oil.t_customer WHERE id = %s"
            }
        }

        # 模拟库存报表函数返回设备数据
        mock_generate_inventory.return_value = [
            {
                "device_code": "DEV001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            }
        ]

        # 模拟命令行参数
        with patch("sys.argv", ["zr_daily_report.py", "--mode", "both"]):
            main()

        # 验证调用了库存报表和客户对账单生成函数
        mock_generate_inventory.assert_called_once_with("库存表处理日志", mock_load_config.return_value)
        
        # 验证客户对账单函数被调用时传入了设备数据和配置
        mock_generate_statement.assert_called_once_with(
            "对账单处理日志", 
            mock_generate_inventory.return_value,  # 确保传递了设备数据
            mock_load_config.return_value
        )

    @patch("zr_daily_report.load_config")
    @patch("zr_daily_report.generate_inventory_reports")
    @patch("zr_daily_report.generate_customer_statement")
    def test_main_function_with_both_mode_empty_device_data(
        self, mock_generate_statement, mock_generate_inventory, mock_load_config
    ):
        """测试主程序在both模式下处理空设备数据的情况"""
        from zr_daily_report import main

        # 模拟配置加载
        mock_load_config.return_value = {
            "db_config": {
                "host": "localhost",
                "port": 3306,
                "user": "test_user",
                "password": "test_password",
                "database": "test_db"
            },
            "sql_templates": {
                "device_id_query": "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s",
                "inventory_query": "SELECT * FROM oil.t_order WHERE device_id = {device_id}",
                "customer_query": "SELECT customer_name FROM oil.t_customer WHERE id = %s"
            }
        }

        # 模拟库存报表函数返回空设备数据
        mock_generate_inventory.return_value = []

        # 模拟命令行参数
        with patch("sys.argv", ["zr_daily_report.py", "--mode", "both"]):
            main()

        # 验证调用了库存报表和客户对账单生成函数
        mock_generate_inventory.assert_called_once_with("库存表处理日志", mock_load_config.return_value)
        
        # 验证客户对账单函数被调用时传入了None（因为设备数据为空列表）
        mock_generate_statement.assert_called_once_with(
            "对账单处理日志", 
            None,  # 空列表应该传入None
            mock_load_config.return_value
        )
