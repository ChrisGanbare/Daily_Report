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
                    
                    # 验证文件是否被正确打开
                    expected_filename = os.path.join(self.test_output_dir, "测试日志前缀_20250701_120000.txt")
                    mock_file.assert_called_once_with(expected_filename, 'w', encoding='utf-8')
                    
                    # 验证文件写入操作
                    handle = mock_file()
                    handle.write.assert_called()

    def test_handle_db_connection_error(self):
        """测试_handle_db_connection_error函数"""
        # 创建测试数据
        log_messages = []
        error = Exception("数据库连接错误")
        error_type = "测试错误类型"
        
        # 模拟错误对象有errno属性
        error.errno = 1045
        
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.getcwd", return_value=self.test_output_dir):
                with patch("src.core.report_controller.datetime") as mock_datetime:
                    # 模拟当前时间
                    mock_now = Mock()
                    mock_now.strftime.return_value = "20250701_120000"
                    mock_datetime.datetime.now.return_value = mock_now
                    
                    # 调用函数
                    _handle_db_connection_error(log_messages, error, error_type)
                    
                    # 验证日志消息是否添加到列表中
                    self.assertEqual(len(log_messages), 2)
                    self.assertIn("数据库连接失败", log_messages[0])
                    self.assertEqual(log_messages[1], "")
                    
                    # 验证文件是否被正确打开
                    expected_filename = os.path.join(self.test_output_dir, "数据库连接错误日志_20250701_120000.txt")
                    mock_file.assert_called_once_with(expected_filename, 'w', encoding='utf-8')

    @patch("src.core.report_controller.FileHandler")
    @patch("src.core.report_controller.DatabaseHandler")
    @patch("src.core.report_controller.InventoryReportGenerator")
    @patch("src.core.report_controller._load_config")
    def test_generate_inventory_reports(self, mock_load_config, mock_inventory_handler, mock_db_handler, mock_file_handler):
        """测试generate_inventory_reports函数"""
        # 模拟配置加载
        mock_config = {
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
        mock_load_config.return_value = mock_config
        
        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {
                "device_code": "TEST001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            }
        ]
        
        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_latest_device_id_and_customer_id.return_value = (1, 2)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_inventory_data.return_value = ([], ["列1", "列2"], [])  # 修复返回值格式
        
        # 模拟库存报告生成器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_report.return_value = [
            {
                "device_code": "TEST001",
                "oil_name": "测试油品",
                "data": [(date(2025, 7, 1), 100.0)],
                "raw_data": [],
                "columns": ["加注时间", "原油剩余比例"],
                "customer_name": "测试客户",
                "device_id": 1,
                "start_date": date(2025, 7, 1),
                "end_date": date(2025, 7, 31)
            }
        ]
        
        # 模拟目录选择
        with patch("src.ui.filedialog_selector.choose_directory", return_value=self.test_output_dir):
            with patch("src.ui.filedialog_selector.choose_file", return_value="test.csv"):
                # 调用函数
                result = generate_inventory_reports(query_config=mock_config)
                
                # 验证结果
                self.assertIsNotNone(result)
                mock_load_config.assert_not_called()  # 由于传入了query_config，不应该调用_load_config
                mock_file_instance.read_devices_from_csv.assert_called_once()
                mock_db_instance.connect.assert_called_once()
                mock_inventory_instance.generate_report.assert_called_once()
                
    @patch("src.core.report_controller.CustomerStatementGenerator")
    @patch("src.core.report_controller.DatabaseHandler")
    @patch("src.core.report_controller.ReportDataManager")
    def test_generate_customer_statement(self, mock_data_manager, mock_db_handler, mock_statement_handler):
        """测试generate_customer_statement函数"""
        # 模拟配置
        mock_config = {
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
        
        # 模拟设备数据
        device_data = [
            {
                "device_code": "TEST001",
                "oil_name": "测试油品",
                "data": [(date(2025, 7, 1), 100.0)],
                "raw_data": [("测试数据",)],
                "columns": ["加注时间", "原油剩余比例", "油品名称"],
                "customer_name": "测试客户",
                "device_id": 1,
                "customer_id": 2,
                "start_date": date(2025, 7, 1),
                "end_date": date(2025, 7, 31)
            }
        ]
        
        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.get_latest_device_id_and_customer_id.return_value = (1, 2)
        
        # 模拟数据管理器
        mock_data_manager_instance = mock_data_manager.return_value
        mock_data_manager_instance.fetch_raw_data.return_value = (
            [], 
            ["加注时间", "原油剩余比例", "油品名称"], 
            [("测试数据", "测试油品")]  # 修改为元组形式，第二个元素是油品名称
        )
        mock_data_manager_instance.extract_inventory_data.return_value = [(date(2025, 7, 1), 100.0)]
        mock_data_manager_instance.calculate_daily_usage.return_value = []
        mock_data_manager_instance.calculate_monthly_usage.return_value = []
        
        # 模拟对账单生成器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_report.return_value = None
        
        # 模拟目录选择
        with patch("src.ui.filedialog_selector.choose_directory", return_value=self.test_output_dir):
            # 调用函数
            result = generate_customer_statement(devices_data=device_data, query_config=mock_config)
            
            # 验证结果
            self.assertIsNone(result)
            mock_statement_instance.generate_report.assert_called_once()

    @patch("src.core.report_controller.FileHandler")
    @patch("src.core.report_controller.DatabaseHandler")
    @patch("src.core.report_controller.InventoryReportGenerator")
    @patch("src.core.report_controller.CustomerStatementGenerator")
    @patch("src.core.report_controller.ReportDataManager")
    @patch("src.core.report_controller._load_config")
    def test_generate_both_reports(self, mock_load_config, mock_data_manager, mock_statement_handler, mock_inventory_handler, mock_db_handler, mock_file_handler):
        # 修改参数顺序以匹配实际调用顺序
        # 原顺序: mock_load_config, mock_data_manager, mock_statement_handler, mock_inventory_handler, mock_db_handler, mock_file_handler
        # 新顺序: mock_load_config, mock_file_handler, mock_db_handler, mock_inventory_handler, mock_statement_handler, mock_data_manager
        # 但保持原顺序，因为装饰器是从下往上应用的，所以实际参数顺序是正确的
        pass  # 保持原有方法体不变
       
    # 以下为原有方法内容...
        # 模拟配置加载
        mock_config = {
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
                "customer_query": "SELECT customer_name FROM oil.t_customer WHERE id = %s",
                "usage_query": "SELECT * FROM oil.t_usage WHERE device_id = {device_id}"
            },
            "report_options": {
                "include_daily_usage": True,
                "include_monthly_summary": True
            }
        }
        mock_load_config.return_value = mock_config
        
        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {
                "device_code": "SZ001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            },
            {
                "device_code": "BJ002",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            }
        ]
        
        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_latest_device_id_and_customer_id.side_effect = [
            (1001, 5001),  # 深圳设备
            (1002, 5002)   # 北京设备
        ]
        mock_db_instance.get_customer_name_by_device_code.side_effect = [
            "深圳XX加油站", 
            "北京XX加油站"
        ]
        
        # 模拟数据管理器
        mock_data_manager_instance = mock_data_manager.return_value
        mock_data_manager_instance.fetch_raw_data.side_effect = [
            # 深圳设备数据
            (
                "oil.t_usage", 
                ["加注时间", "消耗量", "油品名称"], 
                [
                    ("2025-07-01 08:00:00", 20.0, "95#汽油"),
                    ("2025-07-02 08:00:00", 25.0, "95#汽油"),
                    ("2025-07-03 08:00:00", 15.0, "95#汽油")
                ]
            ),
            # 北京设备数据
            (
                "oil.t_usage", 
                ["加注时间", "消耗量", "油品名称"], 
                [
                    ("2025-07-01 08:00:00", 30.0, "柴油"),
                    ("2025-07-02 08:00:00", 25.0, "柴油"),
                    ("2025-07-03 08:00:00", 35.0, "柴油")
                ]
            )
        ]
        mock_data_manager_instance.extract_inventory_data.side_effect = [
            # 深圳设备库存数据
            [
                (date(2025, 7, 1), 100.0),
                (date(2025, 7, 2), 80.0),
                (date(2025, 7, 3), 55.0)
            ],
            # 北京设备库存数据
            [
                (date(2025, 7, 1), 200.0),
                (date(2025, 7, 2), 170.0),
                (date(2025, 7, 3), 135.0)
            ]
        ]
        mock_data_manager_instance.calculate_daily_usage.side_effect = [
            # 深圳设备每日用量
            {
                date(2025, 7, 1): 20.0,
                date(2025, 7, 2): 25.0,
                date(2025, 7, 3): 15.0
            },
            # 北京设备每日用量
            {
                date(2025, 7, 1): 30.0,
                date(2025, 7, 2): 25.0,
                date(2025, 7, 3): 35.0
            }
        ]
        mock_data_manager_instance.calculate_monthly_usage.side_effect = [
            # 深圳设备月度汇总
            {
                "2025-07": 60.0
            },
            # 北京设备月度汇总
            {
                "2025-07": 90.0
            }
        ]
        
        # 模拟库存报告生成器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_report.side_effect = [
            "inventory_report_SZ001.xlsx",
            "inventory_report_BJ002.xlsx"
        ]
        
        # 模拟对账单生成器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_report.side_effect = [
            "statement_SZ001.xlsx",
            "statement_BJ002.xlsx"
        ]
        
        # 模拟文件和目录选择
        with patch("src.ui.filedialog_selector.choose_directory", return_value=self.test_output_dir):
            with patch("src.ui.filedialog_selector.choose_file", return_value="test.csv"):
                # 调用函数
                result = generate_both_reports(query_config=mock_config)
                
                # 验证结果
                self.assertIn("库存报告已生成", result)
                self.assertIn("对账单已生成", result)
                self.assertEqual(mock_inventory_instance.generate_report.call_count, 2)
                self.assertEqual(mock_statement_instance.generate_report.call_count, 2)
                
                # 验证报告数据
                inventory_call_args = mock_inventory_instance.generate_report.call_args_list
                statement_call_args = mock_statement_instance.generate_report.call_args_list
                
                # 验证深圳设备数据
                self.assertEqual(inventory_call_args[0][0][0]["device_code"], "SZ001")
                self.assertEqual(inventory_call_args[0][0][0]["customer_name"], "深圳XX加油站")
                self.assertEqual(statement_call_args[0][0][0]["device_code"], "SZ001")
                self.assertEqual(statement_call_args[0][0][0]["customer_name"], "深圳XX加油站")
                
                # 验证北京设备数据
                self.assertEqual(inventory_call_args[1][0][0]["device_code"], "BJ002")
                self.assertEqual(inventory_call_args[1][0][0]["customer_name"], "北京XX加油站")
                self.assertEqual(statement_call_args[1][0][0]["device_code"], "BJ002")
                self.assertEqual(statement_call_args[1][0][0]["customer_name"], "北京XX加油站")
                mock_inventory_instance.generate_report.assert_called_once()
                mock_statement_instance.generate_report.assert_called_once()
        """测试generate_both_reports函数，验证完整报告生成流程"""
        # 模拟配置加载
        mock_config = {
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
                "customer_query": "SELECT customer_name FROM oil.t_customer WHERE id = %s",
                "usage_query": "SELECT * FROM oil.t_usage WHERE device_id = {device_id}"
            },
            "report_options": {
                "include_daily_usage": True,
                "include_monthly_summary": True
            }
        }
        mock_load_config.return_value = mock_config
        
        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {
                "device_code": "SZ001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            },
            {
                "device_code": "BJ002",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            }
        ]
        
        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_latest_device_id_and_customer_id.side_effect = [
            (1001, 5001),  # 深圳设备
            (1002, 5002)   # 北京设备
        ]
        mock_db_instance.get_customer_name_by_device_code.side_effect = [
            "深圳XX加油站", 
            "北京XX加油站"
        ]
        
        # 模拟数据管理器
        mock_data_manager_instance = mock_data_manager.return_value
        mock_data_manager_instance.fetch_raw_data.side_effect = [
            # 深圳设备数据
            (
                "oil.t_usage", 
                ["加注时间", "消耗量", "油品名称"], 
                [
                    ("2025-07-01 08:00:00", 20.0, "95#汽油"),
                    ("2025-07-02 08:00:00", 25.0, "95#汽油"),
                    ("2025-07-03 08:00:00", 15.0, "95#汽油")
                ]
            ),
            # 北京设备数据
            (
                "oil.t_usage", 
                ["加注时间", "消耗量", "油品名称"], 
                [
                    ("2025-07-01 08:00:00", 30.0, "柴油"),
                    ("2025-07-02 08:00:00", 25.0, "柴油"),
                    ("2025-07-03 08:00:00", 35.0, "柴油")
                ]
            )
        ]
        mock_data_manager_instance.extract_inventory_data.side_effect = [
            # 深圳设备库存数据
            [
                (date(2025, 7, 1), 100.0),
                (date(2025, 7, 2), 80.0),
                (date(2025, 7, 3), 55.0)
            ],
            # 北京设备库存数据
            [
                (date(2025, 7, 1), 200.0),
                (date(2025, 7, 2), 170.0),
                (date(2025, 7, 3), 135.0)
            ]
        ]
        mock_data_manager_instance.calculate_daily_usage.side_effect = [
            # 深圳设备每日用量
            {
                date(2025, 7, 1): 20.0,
                date(2025, 7, 2): 25.0,
                date(2025, 7, 3): 15.0
            },
            # 北京设备每日用量
            {
                date(2025, 7, 1): 30.0,
                date(2025, 7, 2): 25.0,
                date(2025, 7, 3): 35.0
            }
        ]
        mock_data_manager_instance.calculate_monthly_usage.side_effect = [
            # 深圳设备月度汇总
            {
                "2025-07": 60.0
            },
            # 北京设备月度汇总
            {
                "2025-07": 90.0
            }
        ]
        
        # 模拟库存报告生成器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_report.side_effect = [
            "inventory_report_SZ001.xlsx",
            "inventory_report_BJ002.xlsx"
        ]
        
        # 模拟对账单生成器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_report.side_effect = [
            "statement_SZ001.xlsx",
            "statement_BJ002.xlsx"
        ]
        
        # 模拟文件和目录选择
        with patch("src.ui.filedialog_selector.choose_directory", return_value=self.test_output_dir):
            with patch("src.ui.filedialog_selector.choose_file", return_value="test.csv"):
                # 调用函数
                result = generate_both_reports(query_config=mock_config)
                
                # 验证结果
                self.assertIn("库存报告已生成", result)
                self.assertIn("对账单已生成", result)
                self.assertEqual(mock_inventory_instance.generate_report.call_count, 2)
                self.assertEqual(mock_statement_instance.generate_report.call_count, 2)
                
                # 验证报告数据
                inventory_call_args = mock_inventory_instance.generate_report.call_args_list
                statement_call_args = mock_statement_instance.generate_report.call_args_list
                
                # 验证深圳设备数据
                self.assertEqual(inventory_call_args[0][0][0]["device_code"], "SZ001")
                self.assertEqual(inventory_call_args[0][0][0]["customer_name"], "深圳XX加油站")
                self.assertEqual(statement_call_args[0][0][0]["device_code"], "SZ001")
                self.assertEqual(statement_call_args[0][0][0]["customer_name"], "深圳XX加油站")
                
                # 验证北京设备数据
                self.assertEqual(inventory_call_args[1][0][0]["device_code"], "BJ002")
                self.assertEqual(inventory_call_args[1][0][0]["customer_name"], "北京XX加油站")
                self.assertEqual(statement_call_args[1][0][0]["device_code"], "BJ002")
                self.assertEqual(statement_call_args[1][0][0]["customer_name"], "北京XX加油站")
                mock_inventory_instance.generate_report.assert_called_once()
                mock_statement_instance.generate_report.assert_called_once()

    @patch("src.ui.filedialog_selector.choose_file")
    @patch("src.ui.filedialog_selector.choose_directory")
    @patch("src.core.report_controller._load_config")
    @patch("src.core.report_controller.InventoryReportGenerator")
    @patch("src.core.report_controller.FileHandler")
    @patch("src.core.report_controller.DatabaseHandler")
    def test_generate_inventory_reports_success(self, mock_db_handler, mock_file_handler, 
                                              mock_inventory_handler, mock_load_config,
                                              mock_choose_directory, mock_choose_file):
        """测试generate_inventory_reports函数"""
        # 模拟配置加载
        mock_config = {
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
        mock_load_config.return_value = mock_config
        
        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {
                "device_code": "TEST001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            }
        ]
        
        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_latest_device_id_and_customer_id.return_value = (1, 2)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_inventory_data.return_value = ([], ["列1", "列2"], [])  # 修复返回值格式
        
        # 模拟库存报告生成器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_report.return_value = [
            {
                "device_code": "TEST001",
                "oil_name": "测试油品",
                "data": [(date(2025, 7, 1), 100.0)],
                "raw_data": [],
                "columns": ["加注时间", "原油剩余比例"],
                "customer_name": "测试客户",
                "device_id": 1,
                "start_date": date(2025, 7, 1),
                "end_date": date(2025, 7, 31)
            }
        ]
        
        # 模拟目录选择
        with patch("src.core.report_controller.choose_directory", return_value=self.test_output_dir):
            with patch("src.core.report_controller.choose_file", return_value="test.csv"):
                # 调用函数
                result = generate_inventory_reports(query_config=mock_config)
                
                # 验证结果
                self.assertIsNotNone(result)
                mock_load_config.assert_not_called()  # 由于传入了query_config，不应该调用_load_config
                mock_file_instance.read_devices_from_csv.assert_called_once()
                mock_db_instance.connect.assert_called_once()
                mock_db_instance.get_latest_device_id_and_customer_id.assert_called_once()
                mock_db_instance.get_customer_name_by_device_code.assert_called_once()
                mock_db_instance.fetch_inventory_data.assert_called_once()

    @patch("src.ui.filedialog_selector.choose_file")
    @patch("src.ui.filedialog_selector.choose_directory")
    @patch("src.core.report_controller.CustomerStatementGenerator")
    @patch("src.core.report_controller.DatabaseHandler")
    @patch("src.core.report_controller.ReportDataManager")
    @patch("src.core.report_controller._load_config")
    def test_generate_customer_statement_success(self, mock_load_config, mock_data_manager, mock_db_handler, mock_statement_handler, mock_choose_directory, mock_choose_file):
        """测试generate_customer_statement函数"""
        # 模拟配置
        mock_config = {
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
        
        # 模拟设备数据
        device_data = [
            {
                "device_code": "TEST001",
                "oil_name": "测试油品",
                "data": [(date(2025, 7, 1), 100.0)],
                "raw_data": [("测试数据",)],
                "columns": ["加注时间", "原油剩余比例", "油品名称"],
                "customer_name": "测试客户",
                "device_id": 1,
                "customer_id": 2,
                "start_date": date(2025, 7, 1),
                "end_date": date(2025, 7, 31)
            }
        ]
        
        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.get_latest_device_id_and_customer_id.return_value = (1, 2)
        
        # 模拟数据管理器
        mock_data_manager_instance = mock_data_manager.return_value
        mock_data_manager_instance.fetch_raw_data.return_value = (
            [], 
            ["加注时间", "原油剩余比例", "油品名称"], 
            [("测试数据", "测试油品")]  # 修改为元组形式，第二个元素是油品名称
        )
        mock_data_manager_instance.extract_inventory_data.return_value = [(date(2025, 7, 1), 100.0)]
        mock_data_manager_instance.calculate_daily_usage.return_value = []
        mock_data_manager_instance.calculate_monthly_usage.return_value = []
        
        # 模拟对账单生成器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_report.return_value = None
        
        # 模拟目录选择
        with patch("src.core.report_controller.choose_directory", return_value=self.test_output_dir):
            # 调用函数
            result = generate_customer_statement(devices_data=device_data, query_config=mock_config)
            
            # 验证结果
            self.assertIsNone(result)
            mock_statement_instance.generate_report.assert_called_once()

    @patch("src.ui.filedialog_selector.choose_file")
    @patch("src.ui.filedialog_selector.choose_directory")
    @patch("src.core.report_controller.CustomerStatementGenerator")
    @patch("src.core.report_controller.InventoryReportGenerator")
    @patch("src.core.report_controller.DatabaseHandler")
    @patch("src.core.report_controller.ReportDataManager")
    @patch("src.core.report_controller._load_config")
    def test_generate_both_reports_success(self, mock_load_config, mock_data_manager, mock_db_handler, 
                                        mock_inventory_handler, mock_statement_handler, mock_choose_directory, mock_choose_file):
        """测试generate_both_reports函数，验证完整报告生成流程"""
        # 模拟配置加载
        mock_config = {
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
                "customer_query": "SELECT customer_name FROM oil.t_customer WHERE id = %s",
                "usage_query": "SELECT * FROM oil.t_usage WHERE device_id = {device_id}"
            },
            "report_options": {
                "include_daily_usage": True,
                "include_monthly_summary": True
            }
        }
        mock_load_config.return_value = mock_config
        
        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {
                "device_code": "SZ001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            },
            {
                "device_code": "BJ002",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            }
        ]
        
        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_latest_device_id_and_customer_id.side_effect = [
            (1001, 5001),  # 深圳设备
            (1002, 5002)   # 北京设备
        ]
        mock_db_instance.get_customer_name_by_device_code.side_effect = [
            "深圳XX加油站", 
            "北京XX加油站"
        ]
        
        # 模拟数据管理器
        mock_data_manager_instance = mock_data_manager.return_value
        mock_data_manager_instance.fetch_raw_data.side_effect = [
            # 深圳设备数据
            (
                "oil.t_usage", 
                ["加注时间", "消耗量", "油品名称"], 
                [
                    ("2025-07-01 08:00:00", 20.0, "95#汽油"),
                    ("2025-07-02 08:00:00", 25.0, "95#汽油"),
                    ("2025-07-03 08:00:00", 15.0, "95#汽油")
                ]
            ),
            # 北京设备数据
            (
                "oil.t_usage", 
                ["加注时间", "消耗量", "油品名称"], 
                [
                    ("2025-07-01 08:00:00", 30.0, "柴油"),
                    ("2025-07-02 08:00:00", 25.0, "柴油"),
                    ("2025-07-03 08:00:00", 35.0, "柴油")
                ]
            )
        ]
        mock_data_manager_instance.extract_inventory_data.side_effect = [
            # 深圳设备库存数据
            [
                (date(2025, 7, 1), 100.0),
                (date(2025, 7, 2), 80.0),
                (date(2025, 7, 3), 55.0)
            ],
            # 北京设备库存数据
            [
                (date(2025, 7, 1), 200.0),
                (date(2025, 7, 2), 170.0),
                (date(2025, 7, 3), 135.0)
            ]
        ]
        mock_data_manager_instance.calculate_daily_usage.side_effect = [
            # 深圳设备每日用量
            {
                date(2025, 7, 1): 20.0,
                date(2025, 7, 2): 25.0,
                date(2025, 7, 3): 15.0
            },
            # 北京设备每日用量
            {
                date(2025, 7, 1): 30.0,
                date(2025, 7, 2): 25.0,
                date(2025, 7, 3): 35.0
            }
        ]
        mock_data_manager_instance.calculate_monthly_usage.side_effect = [
            # 深圳设备月度汇总
            {
                "2025-07": 60.0
            },
            # 北京设备月度汇总
            {
                "2025-07": 90.0
            }
        ]
        
        # 模拟库存报告生成器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_report.side_effect = [
            "inventory_report_SZ001.xlsx",
            "inventory_report_BJ002.xlsx"
        ]
        
        # 模拟对账单生成器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_report.side_effect = [
            "statement_SZ001.xlsx",
            "statement_BJ002.xlsx"
        ]
        
        # 模拟文件和目录选择
        with patch("src.ui.filedialog_selector.choose_directory", return_value=self.test_output_dir):
            with patch("src.ui.filedialog_selector.choose_file", return_value="test.csv"):
                # 调用函数
                result = generate_both_reports(query_config=mock_config)
                
                # 验证结果
                self.assertIn("库存报告已生成", result)
                self.assertIn("对账单已生成", result)
                self.assertEqual(mock_inventory_instance.generate_report.call_count, 2)
                self.assertEqual(mock_statement_instance.generate_report.call_count, 2)
                
                # 验证报告数据
                inventory_call_args = mock_inventory_instance.generate_report.call_args_list
                statement_call_args = mock_statement_instance.generate_report.call_args_list
                
                # 验证深圳设备数据
                self.assertEqual(inventory_call_args[0][0][0]["device_code"], "SZ001")
                self.assertEqual(inventory_call_args[0][0][0]["customer_name"], "深圳XX加油站")
                self.assertEqual(statement_call_args[0][0][0]["device_code"], "SZ001")
                self.assertEqual(statement_call_args[0][0][0]["customer_name"], "深圳XX加油站")
                
                # 验证北京设备数据
                self.assertEqual(inventory_call_args[1][0][0]["device_code"], "BJ002")
                self.assertEqual(inventory_call_args[1][0][0]["customer_name"], "北京XX加油站")
                self.assertEqual(statement_call_args[1][0][0]["device_code"], "BJ002")
                self.assertEqual(statement_call_args[1][0][0]["customer_name"], "北京XX加油站")
                mock_inventory_instance.generate_report.assert_called_once()
                mock_statement_instance.generate_report.assert_called_once()

if __name__ == "__main__":
    unittest.main()