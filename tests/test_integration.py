import os
import sys
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

# 添加项目根目录到sys.path，确保能正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.base_test import BaseTestCase
from ZR_Daily_Report import (
    generate_customer_statement,
    generate_inventory_reports,
    main,
)


class TestIntegration(BaseTestCase):
    """集成测试，验证整个流程的正确性"""

    def setUp(self):
        """测试前准备"""
        super().setUp()

    @patch("ZR_Daily_Report._load_config")
    @patch("src.core.inventory_handler.InventoryReportGenerator")
    @patch("src.core.file_handler.FileHandler")
    @patch("src.core.db_handler.DatabaseHandler")
    def test_main_workflow_success(
        self,
        mock_db_handler,
        mock_file_handler,
        mock_inventory_handler,
        mock_load_config,
    ):
        """测试主工作流程成功执行"""
        # 模拟配置加载
        mock_load_config.return_value = {
            "db_config": {
                "host": "localhost",
                "port": 3306,
                "user": "test_user",
                "password": "test_password",
                "database": "test_db",
            },
            "sql_templates": {
                "device_id_query": "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s",
                "inventory_query": "SELECT * FROM oil.t_order WHERE device_id = {device_id}",
                "customer_query": "SELECT customer_name FROM oil.t_customer WHERE id = %s",
            },
        }

        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {
                "device_code": "DEV001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31",
            }
        ]

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_latest_device_id_and_customer_id.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_inventory_data.return_value = (
            [],
            [],
            []
        )

        # 模拟库存报告处理器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_inventory_report_with_chart.return_value = None

        # 记录choose_file被调用的次数
        choose_file_call_count = 0
        def mock_choose_file(*args, **kwargs):
            nonlocal choose_file_call_count
            choose_file_call_count += 1
            return 'test.csv'

        # 执行主函数
        test_args = ["zr_daily_report.py", "--mode", "inventory"]
        with patch.object(sys, "argv", test_args):
            with patch('src.ui.filedialog_selector.choose_file', side_effect=mock_choose_file), \
                 patch('src.ui.filedialog_selector.choose_directory', return_value=self.test_output_dir), \
                 patch('builtins.print'):  # 避免打印干扰
                result = main()

        # 验证结果
        self.assertIsNone(result)  # main函数没有返回值
        mock_load_config.assert_called_once()
        mock_file_instance.read_devices_from_csv.assert_called_once()
        mock_db_instance.connect.assert_called_once()
        # 修正断言，使用正确的mock对象方法
        mock_db_instance.get_latest_device_id_and_customer_id.assert_called()

    @patch('ZR_Daily_Report._load_config')
    @patch('src.core.file_handler.FileHandler')
    @patch('src.core.db_handler.DatabaseHandler')
    @patch('src.core.statement_handler.CustomerStatementGenerator')
    def test_both_modes_success(
        self, 
        mock_statement_handler,
        mock_db_handler, 
        mock_file_handler,
        mock_load_config
    ):
        """测试同时生成两种报表模式成功执行"""
        # 模拟配置加载
        mock_load_config.return_value = {
            "db_config": {
                "host": "localhost",
                "port": 3306,
                "user": "test_user",
                "password": "test_password",
                "database": "test_db",
            },
            "sql_templates": {
                "device_id_query": "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s",
                "inventory_query": "SELECT * FROM oil.t_order WHERE device_id = {device_id}",
                "customer_query": "SELECT customer_name FROM oil.t_customer WHERE id = %s",
            },
        }

        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {
                "device_code": "DEV001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31",
            }
        ]

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_latest_device_id_and_customer_id.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_inventory_data.return_value = (
            [(date(2025, 7, 1), 50.0)],
            ["加注时间", "原油剩余比例"],
            [(date(2025, 7, 1), 50.0)]
        )

        # 模拟对账单处理器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_customer_statement_from_template.return_value = None

        # 记录choose_file被调用的次数
        choose_file_call_count = 0
        def mock_choose_file(*args, **kwargs):
            nonlocal choose_file_call_count
            choose_file_call_count += 1
            return 'test.csv'

        # 执行主函数
        test_args = ["ZR_Daily_Report.py", "--mode", "both"]
        with patch.object(sys, "argv", test_args):
            with patch('src.ui.filedialog_selector.choose_file', side_effect=mock_choose_file), \
                 patch('src.ui.filedialog_selector.choose_directory', return_value=self.test_output_dir), \
                 patch('builtins.print'):  # 避免打印干扰
                result = main()

        # 验证结果
        self.assertIsNone(result)
        mock_load_config.assert_called_once()
        mock_file_instance.read_devices_from_csv.assert_called_once()
        mock_db_instance.connect.assert_called_once()
        mock_statement_instance.generate_customer_statement_from_template.assert_called_once()

    @patch('ZR_Daily_Report._load_config')
    @patch('src.core.file_handler.FileHandler')
    def test_both_modes_empty_device_list(
        self,
        mock_file_handler,
        mock_load_config
    ):
        """测试设备列表为空的情况"""
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

        # 模拟文件处理器返回空设备列表
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = []

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_device_and_customer_info.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_inventory_data.return_value = (
            [],
            [],
            []
        )

        # 模拟库存报告处理器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_excel_with_chart.return_value = None

        # 模拟对账单处理器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_customer_statement_from_template.return_value = None

        # 记录choose_file被调用的次数
        choose_file_call_count = 0
        def mock_choose_file(*args, **kwargs):
            nonlocal choose_file_call_count
            choose_file_call_count += 1
            return 'test.csv'

        # 执行主函数
        test_args = ['ZR_Daily_Report.py', '--mode', 'both']
        with patch.object(sys, 'argv', test_args):
            with patch('src.ui.filedialog_selector.choose_file', side_effect=mock_choose_file), \
                 patch('src.ui.filedialog_selector.choose_directory', return_value=self.test_output_dir), \
                 patch('builtins.print'):  # 避免打印干扰
                # 捕获SystemExit异常
                try:
                    result = main()
                except SystemExit as e:
                    # 程序在没有有效设备时会调用exit(1)，我们捕获它
                    self.assertEqual(e.code, 1)
                    result = None

        # 验证结果
        self.assertIsNone(result)
        # 验证choose_file被调用了两次（第一次是库存报表，第二次是对账单因为没有设备数据）
        self.assertEqual(choose_file_call_count, 2)
        mock_load_config.assert_called_once()
        mock_file_instance.read_devices_from_csv.assert_called_once()
        # 验证generate_inventory_reports被调用
        mock_inventory_instance.generate_excel_with_chart.assert_called()
        # 验证generate_customer_statement没有被调用（因为没有设备数据）
        mock_statement_instance.generate_customer_statement_from_template.assert_not_called()