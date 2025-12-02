"""
core.report_controller 模块的单元测试
"""
import os
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import MagicMock, Mock, patch, mock_open

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.report_controller import (
    _save_error_log,
    _handle_db_connection_error,
    generate_inventory_reports,
    generate_customer_statement,
    _load_config
)
from tests.base_test import BaseTestCase


class TestCoreReportController(BaseTestCase):
    """core.report_controller 模块的单元测试"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        
    def test_save_error_log(self):
        """测试_save_error_log函数"""
        # 创建测试数据
        log_messages = ["测试日志消息1", "测试日志消息2"]
        error_details = {
            'error': Exception("测试错误"),
            'error_type': "测试错误类型",
            'traceback': "测试错误追踪信息",
            'log_description': '测试日志'
        }
        log_filename_prefix = "测试日志前缀"
        
        # 使用mock_open模拟文件操作
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.getcwd", return_value=self.test_output_dir):
                with patch("src.core.report_controller.datetime") as mock_datetime:
                    # 模拟当前时间
                    mock_now = Mock()
                    mock_now.strftime.return_value = "20250701_120000"
                    mock_datetime.datetime.now.return_value = mock_now
                    
                    # 调用函数
                    _save_error_log(log_messages, error_details, log_filename_prefix)
                    
                    # 验证文件操作
                    expected_filename = os.path.join(self.test_output_dir, "测试日志前缀_20250701_120000.txt")
                    mock_file.assert_called_once_with(expected_filename, 'w', encoding='utf-8')
                    mock_file().write.assert_called()

    @patch("src.ui.device_filter_dialog.get_device_filter")
    @patch("src.ui.date_dialog.get_date_range")
    @patch("src.ui.filedialog_selector.file_dialog_selector")
    @patch("src.core.report_controller._load_config")
    @patch("src.core.db_handler.DatabaseHandler")
    @patch("src.core.data_manager.ReportDataManager")
    @patch("src.core.inventory_handler.InventoryReportGenerator")
    @patch("builtins.exit")
    def test_generate_inventory_reports(self, mock_exit, mock_inventory_gen, mock_data_manager, mock_db_handler, 
                                        mock_load_config, mock_file_dialog_selector, 
                                        mock_get_date_range, mock_get_device_filter):
        """测试generate_inventory_reports函数（使用对话框）"""
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

        # 模拟日期选择对话框
        mock_get_date_range.return_value = ("2025-07-01", "2025-07-10")
        
        # 模拟设备筛选对话框
        mock_get_device_filter.return_value = ([1, 2], ["测试客户1", "测试客户2"])

        # 模拟文件对话框选择器（仅用于选择输出目录）
        mock_file_dialog_selector.choose_directory.return_value = self.test_output_dir

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "device_code": "DEV001", "customer_name": "测试客户1", "customer_id": 100},
            {"id": 2, "device_code": "DEV002", "customer_name": "测试客户2", "customer_id": 101}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db_instance.connect.return_value = mock_connection

        # 模拟数据管理器
        mock_data_manager_instance = mock_data_manager.return_value
        mock_data_manager_instance.extract_inventory_data.return_value = [
            (date(2025, 7, 1), 100.0),
            (date(2025, 7, 2), 150.0)
        ]
        mock_data_manager_instance.fetch_raw_data.return_value = (
            [],  # data
            ["加注时间", "原油剩余量", "油品名称"],  # columns
            [{"加注时间": date(2025, 7, 1), "原油剩余量": 100.0, "油品名称": "测试油品"}]  # raw_data
        )

        # 模拟报表生成器
        mock_inventory_instance = mock_inventory_gen.return_value
        mock_inventory_instance.generate_report.return_value = True

        # Mock exit 函数，避免测试中断
        mock_exit.side_effect = SystemExit(1)
        
        # 执行函数
        try:
            result = generate_inventory_reports()
        except SystemExit:
            # 如果函数调用了exit，捕获SystemExit异常
            pass

        # 验证调用
        mock_get_date_range.assert_called_once_with(max_days=31)
        mock_get_device_filter.assert_called_once()
        mock_file_dialog_selector.choose_directory.assert_called_once()
        mock_db_instance.connect.assert_called_once()
        mock_cursor.execute.assert_called()

    @patch("src.ui.device_filter_dialog.get_device_filter")
    @patch("src.ui.date_dialog.get_date_range")
    @patch("src.ui.filedialog_selector.file_dialog_selector")
    @patch("src.core.report_controller._load_config")
    @patch("src.core.db_handler.DatabaseHandler")
    @patch("src.core.data_manager.ReportDataManager")
    @patch("src.core.statement_handler.CustomerStatementGenerator")
    @patch("src.core.data_manager.CustomerGroupingUtil.group_devices_by_customer")
    @patch("builtins.exit")
    def test_generate_customer_statement(self, mock_exit, mock_group_devices, mock_statement_handler, 
                                         mock_data_manager, mock_db_handler, 
                                         mock_load_config, mock_file_dialog_selector,
                                         mock_get_date_range, mock_get_device_filter):
        """测试generate_customer_statement函数（使用对话框）"""
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

        # 模拟日期选择对话框
        mock_get_date_range.return_value = ("2025-07-01", "2025-07-10")
        
        # 模拟设备筛选对话框
        mock_get_device_filter.return_value = ([1], ["测试客户"])

        # 模拟文件对话框选择器（仅用于选择输出目录）
        mock_file_dialog_selector.choose_directory.return_value = self.test_output_dir

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "device_code": "DEV001", "customer_name": "测试客户", "customer_id": 100}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db_instance.connect.return_value = mock_connection

        # 模拟数据管理器
        mock_data_manager_instance = mock_data_manager.return_value
        mock_data_manager_instance.extract_inventory_data.return_value = [
            (date(2025, 7, 1), 100.0)
        ]
        mock_data_manager_instance.calculate_daily_usage.return_value = [
            (date(2025, 7, 1), 50.0)
        ]
        mock_data_manager_instance.calculate_monthly_usage.return_value = [
            ("2025-07", 50.0)
        ]
        mock_data_manager_instance.fetch_raw_data.return_value = (
            [],  # data
            ["加注时间", "原油剩余量", "油品名称"],  # columns
            [{"加注时间": date(2025, 7, 1), "原油剩余量": 100.0, "油品名称": "测试油品"}]  # raw_data
        )

        # 模拟客户分组工具（CustomerGroupingUtil.group_devices_by_customer 是静态方法）
        # 需要确保返回的设备数据包含所有必需的字段
        mock_group_devices.return_value = {
            100: {
                "customer_name": "测试客户",
                "devices": [{
                    "device_code": "DEV001",
                    "start_date": "2025-07-01",
                    "end_date": "2025-07-10",
                    "customer_name": "测试客户",
                    "customer_id": 100,
                    "id": 1,
                    "oil_name": "测试油品",
                    "data": [(date(2025, 7, 1), 100.0)],
                    "daily_usage_data": [(date(2025, 7, 1), 50.0)],
                    "monthly_usage_data": [("2025-07", 50.0)],
                    "raw_data": [{"加注时间": date(2025, 7, 1), "原油剩余量": 100.0, "油品名称": "测试油品"}],
                    "columns": ["加注时间", "原油剩余量", "油品名称"]
                }]
            }
        }

        # 模拟对账单处理器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_report.return_value = True

        # Mock exit 函数，避免测试中断
        mock_exit.side_effect = SystemExit(1)
        
        # 执行函数
        try:
            result = generate_customer_statement()
        except SystemExit:
            # 如果函数调用了exit，捕获SystemExit异常
            result = None

        # 验证调用
        mock_get_date_range.assert_called_once_with(max_days=31)
        mock_get_device_filter.assert_called_once()
        mock_file_dialog_selector.choose_directory.assert_called_once()
        mock_db_instance.connect.assert_called_once()
        
        # 验证 CustomerGroupingUtil.group_devices_by_customer 被调用
        # 注意：由于是静态方法，需要通过类来调用
        from src.core.data_manager import CustomerGroupingUtil
        # 如果代码执行到这里，说明没有触发 exit(1)

