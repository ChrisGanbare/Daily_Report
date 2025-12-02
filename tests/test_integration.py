import os
import sys
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

# 添加项目根目录到sys.path，确保能正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.base_test import BaseTestCase
from zr_daily_report import (
    main
)


class TestIntegration(BaseTestCase):
    """集成测试，验证整个流程的正确性"""

    def setUp(self):
        """测试前准备"""
        super().setUp()

    @patch("src.ui.device_filter_dialog.get_device_filter")
    @patch("src.ui.date_dialog.get_date_range")
    @patch("src.ui.filedialog_selector.file_dialog_selector.choose_directory")
    @patch("src.core.report_controller._load_config")
    @patch("src.core.inventory_handler.InventoryReportGenerator")
    @patch("src.core.data_manager.ReportDataManager")
    @patch("src.core.db_handler.DatabaseHandler")
    def test_inventory_mode_success_with_dialog(
        self,
        mock_db_handler,
        mock_data_manager,
        mock_inventory_handler,
        mock_load_config,
        mock_choose_directory,
        mock_get_date_range,
        mock_get_device_filter
    ):
        """测试库存报表完整流程（使用对话框）"""
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

        # 模拟日期选择对话框
        mock_get_date_range.return_value = ("2025-07-01", "2025-07-31")
        
        # 模拟设备筛选对话框
        mock_get_device_filter.return_value = ([1], ["测试客户"])
        
        # 模拟输出目录选择
        mock_choose_directory.return_value = self.test_output_dir

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
            (date(2025, 7, 1), 50.0)
        ]
        mock_data_manager_instance.fetch_raw_data.return_value = (
            [(date(2025, 7, 1), 50.0)],
            ["加注时间", "原油剩余比例", "油品名称"],
            [{"加注时间": date(2025, 7, 1), "原油剩余比例": 50.0, "油品名称": "测试油品"}]
        )

        # 模拟库存报告处理器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_report.return_value = True

        # 执行函数
        from src.core.report_controller import generate_inventory_reports
        result = generate_inventory_reports()

        # 验证调用
        mock_get_date_range.assert_called_once_with(max_days=31)
        mock_get_device_filter.assert_called_once()
        mock_choose_directory.assert_called_once()
        mock_db_instance.connect.assert_called_once()
        mock_inventory_handler.assert_called_once()

    @patch("src.ui.device_filter_dialog.get_device_filter")
    @patch("src.ui.date_dialog.get_date_range")
    @patch("src.ui.filedialog_selector.file_dialog_selector.choose_directory")
    @patch("src.core.report_controller._load_config")
    @patch("src.core.device_config_manager.DeviceConfigManager")
    @patch("src.core.data_manager.ReportDataManager")
    @patch("src.core.consumption_error_handler.DailyConsumptionErrorReportGenerator")
    @patch("src.core.db_handler.DatabaseHandler")
    def test_daily_consumption_error_reports_integration(
        self,
        mock_db_handler,
        mock_daily_gen,
        mock_data_manager,
        mock_config_manager,
        mock_load_config,
        mock_choose_directory,
        mock_get_date_range,
        mock_get_device_filter
    ):
        """测试每日消耗误差报表完整流程（使用对话框）"""
        from src.core.report_controller import generate_daily_consumption_error_reports
        
        mock_load_config.return_value = {
            "db_config": {"host": "localhost"},
            "sql_templates": {
                "inventory_query": "SELECT * FROM t_order WHERE device_id = {device_id}",
                "device_id_query": "SELECT id, customer_id FROM t_device WHERE device_code = %s"
            }
        }
        
        mock_get_date_range.return_value = ("2025-07-01", "2025-07-10")
        mock_get_device_filter.return_value = ([1], ["测试客户"])
        mock_choose_directory.return_value = self.test_output_dir
        
        mock_db_instance = mock_db_handler.return_value
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "device_code": "DEV001", "customer_name": "测试客户", "customer_id": 100}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db_instance.connect.return_value = mock_connection
        
        mock_config_instance = mock_config_manager.return_value
        mock_config_instance.get_barrel_count.return_value = 1
        mock_config_instance.show_config_info.return_value = None
        
        mock_data_manager_instance = mock_data_manager.return_value
        mock_data_manager_instance.extract_inventory_data.return_value = [
            (date(2025, 7, 1), 100.0)
        ]
        mock_data_manager_instance.calculate_daily_errors.return_value = {
            "daily_order_totals": {},
            "daily_shortage_errors": {},
            "daily_excess_errors": {},
            "daily_consumption": {}
        }
        mock_data_manager_instance.fetch_raw_data.return_value = (
            [],
            ["加注时间", "原油剩余量", "油品名称"],
            [{"加注时间": date(2025, 7, 1), "原油剩余量": 100.0, "油品名称": "测试油品"}]
        )
        
        mock_daily_instance = mock_daily_gen.return_value
        mock_daily_instance.generate_report.return_value = True
        
        result = generate_daily_consumption_error_reports()
        
        # 验证完整流程
        mock_get_date_range.assert_called_once_with(max_days=62)
        mock_get_device_filter.assert_called_once()
        mock_config_instance.get_barrel_count.assert_called()
        mock_daily_instance.generate_report.assert_called()
