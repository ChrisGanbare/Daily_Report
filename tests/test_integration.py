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

    # 装饰器顺序按照业务流程执行顺序排列：
    # 1. _file_dialog_selector.choose_file - 首先选择输入文件
    # 2. _file_dialog_selector.choose_directory - 然后选择输出目录
    # 3. _load_config - 加载配置信息
    # 4. InventoryReportGenerator - 库存报表生成器
    # 5. FileHandler - 文件处理器
    # 6. DatabaseHandler - 数据库处理器
    @patch("src.ui.filedialog_selector.file_dialog_selector.choose_file")
    @patch("src.ui.filedialog_selector.file_dialog_selector.choose_directory")
    @patch("src.core.report_controller._load_config")
    @patch("src.core.report_controller.InventoryReportGenerator")
    @patch("src.core.report_controller.FileHandler")
    @patch("src.core.report_controller.DatabaseHandler")
    def test_inventory_mode_success(
        self,
        mock_db_handler,          # 对应 DatabaseHandler
        mock_file_handler,        # 对应 FileHandler
        mock_inventory_handler,   # 对应 InventoryReportGenerator
        mock_load_config,         # 对应 _load_config
        mock_choose_directory,    # 对应 _file_dialog_selector.choose_directory
        mock_choose_file          # 对应 _file_dialog_selector.choose_file
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

        # 模拟文件选择对话框
        mock_choose_file.return_value = "test.csv"
        mock_choose_directory.return_value = self.test_output_dir

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
        mock_db_instance.connect.return_value = MagicMock()
        mock_db_instance.get_latest_device_id_and_customer__id.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_generic_data.return_value = (
            [(date(2025, 7, 1), 50.0)],
            ["加注时间", "原油剩余比例", "油品名称"],
            [(date(2025, 7, 1), 50.0, "测试油品")]
        )

        # 模拟库存报告处理器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_inventory_report_with_chart.return_value = None

        # 执行主函数
        test_args = ["zr_daily_report.py", "--mode", "inventory"]
        with patch.object(sys, "argv", test_args):
            with patch('builtins.print'):  # 避免打印干扰
                # 捕获SystemExit异常
                try:
                    result = main()
                except SystemExit as e:
                    # 程序在某些错误条件下会调用exit(1)，我们捕获它
                    self.assertEqual(e.code, 1)
                    result = None

        # 验证调用
        mock_choose_file.assert_called_once()
        mock_choose_directory.assert_called_once()
        mock_file_instance.read_devices_from_csv.assert_called_once()
        mock_db_instance.connect.assert_called_once()
        mock_inventory_handler.assert_called_once()

    # 装饰器顺序按照业务流程执行顺序排列：
    # 1. choose_file - 首先选择输入文件
    # 2. choose_directory - 然后选择输出目录
    # 3. _load_config - 加载配置信息
    # 4. InventoryReportGenerator - 库存报表生成器
    # 5. CustomerStatementGenerator - 对账单生成器
    # 6. FileHandler - 文件处理器
    # 7. DatabaseHandler - 数据库处理器
    @patch("src.ui.filedialog_selector.file_dialog_selector.choose_file")
    @patch("src.ui.filedialog_selector.file_dialog_selector.choose_directory")
    @patch("src.core.report_controller._load_config")
    @patch("src.core.report_controller.InventoryReportGenerator")
    @patch("src.core.report_controller.CustomerStatementGenerator")
    @patch("src.core.report_controller.FileHandler")
    @patch("src.core.report_controller.DatabaseHandler")
    def test_both_modes_success(
        self, 
        mock_db_handler,          # 对应 DatabaseHandler
        mock_file_handler,        # 对应 FileHandler
        mock_statement_handler,   # 对应 CustomerStatementGenerator
        mock_inventory_handler,   # 对应 InventoryReportGenerator
        mock_load_config,         # 对应 _load_config
        mock_choose_directory,    # 对应 _file_dialog_selector.choose_directory
        mock_choose_file          # 对应 _file_dialog_selector.choose_file
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

        # 模拟文件选择对话框
        mock_choose_file.return_value = "test.csv"
        mock_choose_directory.return_value = self.test_output_dir

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
        mock_db_instance.connect.return_value = MagicMock()
        mock_db_instance.get_latest_device_id_and_customer_id.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_generic_data.return_value = (
            [(date(2025, 7, 1), 50.0)],
            ["加注时间", "原油剩余比例", "油品名称"],
            [(date(2025, 7, 1), 50.0, "测试油品")]
        )

        # 模拟库存报告处理器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_inventory_report_with_chart.return_value = None

        # 模拟对账单处理器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_customer_statement_from_template.return_value = None

        # 执行主函数
        test_args = ["zr_daily_report.py", "--mode", "both"]
        with patch.object(sys, "argv", test_args):
            with patch('builtins.print'):  # 避免打印干扰
                # 捕获SystemExit异常
                try:
                    result = main()
                except SystemExit as e:
                    # 程序在某些错误条件下会调用exit(1)，我们捕获它
                    self.assertEqual(e.code, 1)
                    result = None

        # 验证调用
        self.assertEqual(mock_choose_file.call_count, 1)
        self.assertEqual(mock_choose_directory.call_count, 1)
        mock_file_instance.read_devices_from_csv.assert_called_once()
        mock_db_instance.connect.assert_called_once()
        mock_inventory_handler.assert_called_once()
        mock_statement_instance.generate_report.assert_called_once()

        # 装饰器顺序按照业务流程执行顺序排列：
        # 1. choose_file - 首先选择输入文件
        # 2. choose_directory - 然后选择输出目录
        # 3. _load_config - 加载配置信息
        # 4. InventoryReportGenerator - 库存报表生成器
        # 5. CustomerStatementGenerator - 对账单生成器
        # 6. FileHandler - 文件处理器（已删除）
        # @patch("src.core.report_controller.FileHandler")
        # def test_generate_daily_consumption_report_success(self, mock_file_handler, mock_device_repo, mock_report_service, mock_date_utils, mock_logger):
        #     mock_file_handler,        # 对应 FileHandler（已删除）
        #     mock_file_instance = mock_file_handler.return_value  # 删除这行
        # 7. DatabaseHandler - 数据库处理器
        @patch("src.ui.filedialog_selector.file_dialog_selector.choose_file")
        @patch("src.ui.filedialog_selector.file_dialog_selector.choose_directory")
        @patch("src.core.report_controller._load_config")
        @patch("src.core.report_controller.InventoryReportGenerator")
        @patch("src.core.report_controller.CustomerStatementGenerator")
        @patch("src.core.report_controller.FileHandler")
        @patch("src.core.report_controller.DatabaseHandler")
        def test_both_modes_empty_device_list(
                self,
                mock_db_handler,  # 对应 DatabaseHandler
                mock_file_handler,  # 对应 FileHandler
                mock_statement_handler,  # 对应 CustomerStatementGenerator
                mock_inventory_handler,  # 对应 InventoryReportGenerator
                mock_load_config,  # 对应 _load_config
                mock_choose_directory,  # 对应 _file_dialog_selector.choose_directory
                mock_choose_file  # 对应 _file_dialog_selector.choose_file
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

            # 模拟文件选择对话框
            mock_choose_file.return_value = "test.csv"
            mock_choose_directory.return_value = self.test_output_dir

            # 模拟文件处理器返回空设备列表
            mock_file_instance = mock_file_handler.return_value
            mock_file_instance.read_devices_from_csv.return_value = []

            # 模拟数据库处理器
            mock_db_instance = mock_db_handler.return_value
            mock_db_instance.connect.return_value = MagicMock()

            # 模拟库存报告处理器
            mock_inventory_instance = mock_inventory_handler.return_value
            mock_inventory_instance.generate_excel_with_chart.return_value = None

            # 模拟对账单处理器
            mock_statement_instance = mock_statement_handler.return_value
            mock_statement_instance.generate_customer_statement_from_template.return_value = None

            # 执行主函数
            test_args = ['zr_daily_report.py', '--mode', 'both']
            with patch.object(sys, 'argv', test_args):
                with patch('builtins.print'):  # 避免打印干扰
                    # 捕获SystemExit异常
                    try:
                        result = main()
                    except SystemExit as e:
                        # 程序在没有有效设备时会调用exit(1)，我们捕获它
                        self.assertEqual(e.code, 1)
                        result = None

            # 验证调用
            self.assertEqual(mock_choose_file.call_count, 1)
            self.assertEqual(mock_choose_directory.call_count, 0)
            mock_file_instance.read_devices_from_csv.assert_called_once()
            mock_db_instance.connect.assert_not_called()
            mock_inventory_instance.generate_inventory_report_with_chart.assert_not_called()
            mock_statement_instance.generate_customer_statement.assert_not_called()
        # 装饰器顺序按照业务流程执行顺序排列：
        # 1. choose_file - 首先选择输入文件
        # 2. choose_directory - 然后选择输出目录
        # 3. _load_config - 加载配置信息
        # 4. InventoryReportGenerator - 库存报表生成器
        # 5. CustomerStatementGenerator - 对账单生成器
        # 6. FileHandler - 文件处理器（已删除）
        # @patch("src.core.report_controller.FileHandler")
        # def test_generate_daily_consumption_report_success(self, mock_file_handler, mock_device_repo, mock_report_service, mock_date_utils, mock_logger):
        #     mock_file_handler,        # 对应 FileHandler（已删除）
        #     mock_file_instance = mock_file_handler.return_value  # 删除这行
        # 7. DatabaseHandler - 数据库处理器
        @patch("src.ui.filedialog_selector.file_dialog_selector.choose_file")
        @patch("src.ui.filedialog_selector.file_dialog_selector.choose_directory")
        @patch("src.core.report_controller._load_config")
        @patch("src.core.report_controller.InventoryReportGenerator")
        @patch("src.core.report_controller.CustomerStatementGenerator")
        @patch("src.core.report_controller.FileHandler")
        @patch("src.core.report_controller.DatabaseHandler")
        def test_both_modes_empty_device_list(
                self,
                mock_db_handler,  # 对应 DatabaseHandler
                mock_file_handler,  # 对应 FileHandler
                mock_statement_handler,  # 对应 CustomerStatementGenerator
                mock_inventory_handler,  # 对应 InventoryReportGenerator
                mock_load_config,  # 对应 _load_config
                mock_choose_directory,  # 对应 _file_dialog_selector.choose_directory
                mock_choose_file  # 对应 _file_dialog_selector.choose_file
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

            # 模拟文件选择对话框
            mock_choose_file.return_value = "test.csv"
            mock_choose_directory.return_value = self.test_output_dir

            # 模拟文件处理器返回空设备列表
            mock_file_instance = mock_file_handler.return_value
            mock_file_instance.read_devices_from_csv.return_value = []

            # 模拟数据库处理器
            mock_db_instance = mock_db_handler.return_value
            mock_db_instance.connect.return_value = MagicMock()

            # 模拟库存报告处理器
            mock_inventory_instance = mock_inventory_handler.return_value
            mock_inventory_instance.generate_excel_with_chart.return_value = None

            # 模拟对账单处理器
            mock_statement_instance = mock_statement_handler.return_value
            mock_statement_instance.generate_customer_statement_from_template.return_value = None

            # 执行主函数
            test_args = ['zr_daily_report.py', '--mode', 'both']
            with patch.object(sys, 'argv', test_args):
                with patch('builtins.print'):  # 避免打印干扰
                    # 捕获SystemExit异常
                    try:
                        result = main()
                    except SystemExit as e:
                        # 程序在没有有效设备时会调用exit(1)，我们捕获它
                        self.assertEqual(e.code, 1)
                        result = None

            # 验证调用
            self.assertEqual(mock_choose_file.call_count, 1)
            self.assertEqual(mock_choose_directory.call_count, 0)
            mock_file_instance.read_devices_from_csv.assert_called_once()
            mock_db_instance.connect.assert_not_called()
            mock_inventory_instance.generate_inventory_report_with_chart.assert_not_called()
            mock_statement_instance.generate_customer_statement.assert_not_called()
        # 装饰器顺序按照业务流程执行顺序排列：
        # 1. choose_file - 首先选择输入文件
        # 2. choose_directory - 然后选择输出目录
        # 3. _load_config - 加载配置信息
        # 4. InventoryReportGenerator - 库存报表生成器
        # 5. CustomerStatementGenerator - 对账单生成器
        # 6. FileHandler - 文件处理器（已删除）
        # @patch("src.core.report_controller.FileHandler")
        # def test_generate_daily_consumption_report_success(self, mock_file_handler, mock_device_repo, mock_report_service, mock_date_utils, mock_logger):
        #     mock_file_handler,        # 对应 FileHandler（已删除）
        #     mock_file_instance = mock_file_handler.return_value  # 删除这行
        # 7. DatabaseHandler - 数据库处理器
        @patch("src.ui.filedialog_selector.file_dialog_selector.choose_file")
        @patch("src.ui.filedialog_selector.file_dialog_selector.choose_directory")
        @patch("src.core.report_controller._load_config")
        @patch("src.core.report_controller.InventoryReportGenerator")
        @patch("src.core.report_controller.CustomerStatementGenerator")
        @patch("src.core.report_controller.FileHandler")
        @patch("src.core.report_controller.DatabaseHandler")
        def test_both_modes_empty_device_list(
                self,
                mock_db_handler,  # 对应 DatabaseHandler
                mock_file_handler,  # 对应 FileHandler
                mock_statement_handler,  # 对应 CustomerStatementGenerator
                mock_inventory_handler,  # 对应 InventoryReportGenerator
                mock_load_config,  # 对应 _load_config
                mock_choose_directory,  # 对应 _file_dialog_selector.choose_directory
                mock_choose_file  # 对应 _file_dialog_selector.choose_file
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

            # 模拟文件选择对话框
            mock_choose_file.return_value = "test.csv"
            mock_choose_directory.return_value = self.test_output_dir

            # 模拟文件处理器返回空设备列表
            mock_file_instance = mock_file_handler.return_value
            mock_file_instance.read_devices_from_csv.return_value = []

            # 模拟数据库处理器
            mock_db_instance = mock_db_handler.return_value
            mock_db_instance.connect.return_value = MagicMock()

            # 模拟库存报告处理器
            mock_inventory_instance = mock_inventory_handler.return_value
            mock_inventory_instance.generate_excel_with_chart.return_value = None

            # 模拟对账单处理器
            mock_statement_instance = mock_statement_handler.return_value
            mock_statement_instance.generate_customer_statement_from_template.return_value = None

            # 执行主函数
            test_args = ['zr_daily_report.py', '--mode', 'both']
            with patch.object(sys, 'argv', test_args):
                with patch('builtins.print'):  # 避免打印干扰
                    # 捕获SystemExit异常
                    try:
                        result = main()
                    except SystemExit as e:
                        # 程序在没有有效设备时会调用exit(1)，我们捕获它
                        self.assertEqual(e.code, 1)
                        result = None

            # 验证调用
            self.assertEqual(mock_choose_file.call_count, 1)
            self.assertEqual(mock_choose_directory.call_count, 0)
            mock_file_instance.read_devices_from_csv.assert_called_once()
            mock_db_instance.connect.assert_not_called()
            mock_inventory_instance.generate_inventory_report_with_chart.assert_not_called()
            mock_statement_instance.generate_customer_statement.assert_not_called()
        # 装饰器顺序按照业务流程执行顺序排列：
        # 1. choose_file - 首先选择输入文件
        # 2. choose_directory - 然后选择输出目录
        # 3. _load_config - 加载配置信息
        # 4. InventoryReportGenerator - 库存报表生成器
        # 5. CustomerStatementGenerator - 对账单生成器
        # 6. FileHandler - 文件处理器（已删除）
        # @patch("src.core.report_controller.FileHandler")
        # def test_generate_daily_consumption_report_success(self, mock_file_handler, mock_device_repo, mock_report_service, mock_date_utils, mock_logger):
        #     mock_file_handler,        # 对应 FileHandler（已删除）
        #     mock_file_instance = mock_file_handler.return_value  # 删除这行
        # 7. DatabaseHandler - 数据库处理器
        @patch("src.ui.filedialog_selector.file_dialog_selector.choose_file")
        @patch("src.ui.filedialog_selector.file_dialog_selector.choose_directory")
        @patch("src.core.report_controller._load_config")
        @patch("src.core.report_controller.InventoryReportGenerator")
        @patch("src.core.report_controller.CustomerStatementGenerator")
        @patch("src.core.report_controller.FileHandler")
        @patch("src.core.report_controller.DatabaseHandler")
        def test_both_modes_empty_device_list(
                self,
                mock_db_handler,  # 对应 DatabaseHandler
                mock_file_handler,  # 对应 FileHandler
                mock_statement_handler,  # 对应 CustomerStatementGenerator
                mock_inventory_handler,  # 对应 InventoryReportGenerator
                mock_load_config,  # 对应 _load_config
                mock_choose_directory,  # 对应 _file_dialog_selector.choose_directory
                mock_choose_file  # 对应 _file_dialog_selector.choose_file
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

            # 模拟文件选择对话框
            mock_choose_file.return_value = "test.csv"
            mock_choose_directory.return_value = self.test_output_dir

            # 模拟文件处理器返回空设备列表
            mock_file_instance = mock_file_handler.return_value
            mock_file_instance.read_devices_from_csv.return_value = []

            # 模拟数据库处理器
            mock_db_instance = mock_db_handler.return_value
            mock_db_instance.connect.return_value = MagicMock()

            # 模拟库存报告处理器
            mock_inventory_instance = mock_inventory_handler.return_value
            mock_inventory_instance.generate_excel_with_chart.return_value = None

            # 模拟对账单处理器
            mock_statement_instance = mock_statement_handler.return_value
            mock_statement_instance.generate_customer_statement_from_template.return_value = None

            # 执行主函数
            test_args = ['zr_daily_report.py', '--mode', 'both']
            with patch.object(sys, 'argv', test_args):
                with patch('builtins.print'):  # 避免打印干扰
                    # 捕获SystemExit异常
                    try:
                        result = main()
                    except SystemExit as e:
                        # 程序在没有有效设备时会调用exit(1)，我们捕获它
                        self.assertEqual(e.code, 1)
                        result = None

            # 验证调用
            self.assertEqual(mock_choose_file.call_count, 1)
            self.assertEqual(mock_choose_directory.call_count, 0)
            mock_file_instance.read_devices_from_csv.assert_called_once()
            mock_db_instance.connect.assert_not_called()
            mock_inventory_instance.generate_inventory_report_with_chart.assert_not_called()
            mock_statement_instance.generate_customer_statement.assert_not_called()
        # 装饰器顺序按照业务流程执行顺序排列：
        # 1. choose_file - 首先选择输入文件
        # 2. choose_directory - 然后选择输出目录
        # 3. _load_config - 加载配置信息
        # 4. InventoryReportGenerator - 库存报表生成器
        # 5. CustomerStatementGenerator - 对账单生成器
        # 6. FileHandler - 文件处理器（已删除）
        # @patch("src.core.report_controller.FileHandler")
        # def test_generate_daily_consumption_report_success(self, mock_file_handler, mock_device_repo, mock_report_service, mock_date_utils, mock_logger):
        #     mock_file_handler,        # 对应 FileHandler（已删除）
        #     mock_file_instance = mock_file_handler.return_value  # 删除这行
        # 7. DatabaseHandler - 数据库处理器
        @patch("src.ui.filedialog_selector.file_dialog_selector.choose_file")
        @patch("src.ui.filedialog_selector.file_dialog_selector.choose_directory")
        @patch("src.core.report_controller._load_config")
        @patch("src.core.report_controller.InventoryReportGenerator")
        @patch("src.core.report_controller.CustomerStatementGenerator")
        @patch("src.core.report_controller.FileHandler")
        @patch("src.core.report_controller.DatabaseHandler")
        def test_both_modes_empty_device_list(
                self,
                mock_db_handler,  # 对应 DatabaseHandler
                mock_file_handler,  # 对应 FileHandler
                mock_statement_handler,  # 对应 CustomerStatementGenerator
                mock_inventory_handler,  # 对应 InventoryReportGenerator
                mock_load_config,  # 对应 _load_config
                mock_choose_directory,  # 对应 _file_dialog_selector.choose_directory
                mock_choose_file  # 对应 _file_dialog_selector.choose_file
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

            # 模拟文件选择对话框
            mock_choose_file.return_value = "test.csv"
            mock_choose_directory.return_value = self.test_output_dir

            # 模拟文件处理器返回空设备列表
            mock_file_instance = mock_file_handler.return_value
            mock_file_instance.read_devices_from_csv.return_value = []

            # 模拟数据库处理器
            mock_db_instance = mock_db_handler.return_value
            mock_db_instance.connect.return_value = MagicMock()

            # 模拟库存报告处理器
            mock_inventory_instance = mock_inventory_handler.return_value
            mock_inventory_instance.generate_excel_with_chart.return_value = None

            # 模拟对账单处理器
            mock_statement_instance = mock_statement_handler.return_value
            mock_statement_instance.generate_customer_statement_from_template.return_value = None

            # 执行主函数
            test_args = ['zr_daily_report.py', '--mode', 'both']
            with patch.object(sys, 'argv', test_args):
                with patch('builtins.print'):  # 避免打印干扰
                    # 捕获SystemExit异常
                    try:
                        result = main()
                    except SystemExit as e:
                        # 程序在没有有效设备时会调用exit(1)，我们捕获它
                        self.assertEqual(e.code, 1)
                        result = None

            # 验证调用
            self.assertEqual(mock_choose_file.call_count, 1)
            self.assertEqual(mock_choose_directory.call_count, 0)
            mock_file_instance.read_devices_from_csv.assert_called_once()
            mock_db_instance.connect.assert_not_called()
            mock_inventory_instance.generate_inventory_report_with_chart.assert_not_called()
            mock_statement_instance.generate_customer_statement.assert_not_called()