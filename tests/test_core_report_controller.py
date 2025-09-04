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
    generate_both_reports,
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

    @patch("src.core.report_controller.file_dialog_selector")
    @patch("src.core.report_controller._load_config")
    @patch("src.core.report_controller.FileHandler")
    @patch("src.core.report_controller.DatabaseHandler")
    def test_generate_inventory_reports(self, mock_db_handler, mock_file_handler, mock_load_config, mock_file_dialog_selector):
        """测试generate_inventory_reports函数"""
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

        # 模拟文件对话框选择器
        mock_file_dialog_selector.choose_file.return_value = "test.csv"
        mock_file_dialog_selector.choose_directory.return_value = self.test_output_dir

        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {"device_code": "DEV001", "start_date": "2025/07/01", "end_date": "2025/07/10"}
        ]

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.connect.return_value = MagicMock()
        mock_db_instance.get_latest_device_id_and_customer_id.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"

        # 执行函数
        result = generate_inventory_reports()

        # 验证调用
        mock_file_dialog_selector.choose_file.assert_called_once()
        mock_file_dialog_selector.choose_directory.assert_called_once()
        mock_file_instance.read_devices_from_csv.assert_called_once()
        mock_db_instance.connect.assert_called_once()
        mock_db_instance.get_latest_device_id_and_customer_id.assert_called_once()
        mock_db_instance.get_customer_name_by_device_code.assert_called_once()

    @patch("src.core.report_controller.file_dialog_selector")
    @patch("src.core.report_controller._load_config")
    @patch("src.core.report_controller.FileHandler")
    @patch("src.core.report_controller.DatabaseHandler")
    @patch("src.core.report_controller.CustomerStatementGenerator")
    def test_generate_customer_statement(self, mock_statement_handler, mock_db_handler, mock_file_handler, mock_load_config, mock_file_dialog_selector):
        """测试generate_customer_statement函数"""
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

        # 模拟文件对话框选择器
        mock_file_dialog_selector.choose_file.return_value = "test.csv"
        mock_file_dialog_selector.choose_directory.return_value = self.test_output_dir

        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {"device_code": "DEV001", "start_date": "2025/07/01", "end_date": "2025/07/10"}
        ]

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.connect.return_value = MagicMock()
        mock_db_instance.get_latest_device_id_and_customer_id.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"

        # 模拟对账单处理器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_customer_statement_from_template.return_value = None

        # 执行函数
        result = generate_customer_statement()

        # 验证调用
        mock_file_dialog_selector.choose_file.assert_called_once()
        mock_file_dialog_selector.choose_directory.assert_called_once()
        mock_file_instance.read_devices_from_csv.assert_called_once()
        mock_db_instance.connect.assert_called_once()
        mock_db_instance.get_latest_device_id_and_customer_id.assert_called_once()
        mock_db_instance.get_customer_name_by_device_code.assert_called_once()

    @patch("src.core.report_controller.file_dialog_selector")
    @patch("src.core.report_controller._load_config")
    @patch("src.core.report_controller.FileHandler")
    @patch("src.core.report_controller.DatabaseHandler")
    @patch("src.core.report_controller.InventoryReportGenerator")
    @patch("src.core.report_controller.CustomerStatementGenerator")
    def test_generate_both_reports(self, mock_statement_handler, mock_inventory_handler, mock_db_handler, mock_file_handler, mock_load_config, mock_file_dialog_selector):
        """测试generate_both_reports函数"""
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

        # 模拟文件对话框选择器
        mock_file_dialog_selector.choose_file.return_value = "test.csv"
        mock_file_dialog_selector.choose_directory.return_value = self.test_output_dir

        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {"device_code": "DEV001", "start_date": "2025/07/01", "end_date": "2025/07/10"}
        ]

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.connect.return_value = MagicMock()
        mock_db_instance.get_latest_device_id_and_customer_id.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"

        # 模拟库存报表处理器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_excel_with_chart.return_value = None

        # 模拟对账单处理器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_customer_statement_from_template.return_value = None

        # 执行函数
        result = generate_both_reports()

        # 验证调用
        mock_file_dialog_selector.choose_file.assert_called()
        mock_file_dialog_selector.choose_directory.assert_called()
        mock_file_instance.read_devices_from_csv.assert_called_once()
        mock_db_instance.connect.assert_called_once()
        mock_db_instance.get_latest_device_id_and_customer_id.assert_called_once()
        mock_db_instance.get_customer_name_by_device_code.assert_called_once()
