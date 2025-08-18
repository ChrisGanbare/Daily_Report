import os
import sys
import unittest
from datetime import date
from unittest.mock import patch, MagicMock

# 添加项目根目录到sys.path，确保能正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.base_test import BaseTestCase
from ZR_Daily_Report import main, generate_inventory_reports, generate_customer_statement


class TestIntegration(BaseTestCase):
    """集成测试，验证整个流程的正确性"""

    def setUp(self):
        """测试前准备"""
        super().setUp()

    @patch('ZR_Daily_Report.load_config')
    @patch('ZR_Daily_Report.InventoryReportGenerator')
    @patch('ZR_Daily_Report.FileHandler')
    @patch('ZR_Daily_Report.DatabaseHandler')
    def test_main_workflow_success(self, mock_db_handler, mock_file_handler,
                                   mock_inventory_handler, mock_load_config):
        """测试主工作流程成功执行"""
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

        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {
                "device_code": "DEV001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            }
        ]

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_device_and_customer_info.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_inventory_data.return_value = (
            [(date(2025, 7, 1), 95.5), (date(2025, 7, 2), 93.2)],
            ["加注时间", "原油剩余比例", "油品名称"],
            [{"加注时间": date(2025, 7, 1), "原油剩余比例": 95.5, "油品名称": "切削液"},
             {"加注时间": date(2025, 7, 2), "原油剩余比例": 93.2, "油品名称": "切削液"}]
        )

        # 模拟库存报告处理器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_inventory_report_with_chart.return_value = None

        # 执行主函数
        test_args = ['ZR_Daily_Report.py', '--mode', 'inventory']
        with patch.object(sys, 'argv', test_args):
            with patch('src.utils.ui_utils.choose_file', return_value='test.csv'), \
                 patch('src.utils.ui_utils.choose_directory', return_value=self.test_output_dir), \
                 patch('builtins.print'):  # 避免打印干扰
                result = main()

        # 验证结果
        self.assertIsNone(result)  # main函数没有返回值
        mock_load_config.assert_called_once()
        mock_file_instance.read_devices_from_csv.assert_called_once()
        mock_db_instance.connect.assert_called_once()
        mock_db_instance.get_device_and_customer_info.assert_called()
        mock_db_instance.fetch_inventory_data.assert_called()
        mock_inventory_instance.generate_inventory_report_with_chart.assert_called()

    @patch('ZR_Daily_Report.load_config')
    def test_main_with_missing_config(self, mock_load_config):
        """测试配置文件缺失的情况"""
        mock_load_config.side_effect = FileNotFoundError("配置文件不存在")

        test_args = ['ZR_Daily_Report.py', '--mode', 'inventory']
        with patch.object(sys, 'argv', test_args):
            with patch('src.utils.ui_utils.choose_file', return_value='test.csv'), \
                 patch('src.utils.ui_utils.choose_directory', return_value=self.test_output_dir), \
                 patch('builtins.print'):
                # 由于程序会调用exit(1)，我们需要捕获SystemExit异常
                with self.assertRaises(SystemExit) as cm:
                    main()
                # 验证退出码是1
                self.assertEqual(cm.exception.code, 1)

    @patch('ZR_Daily_Report.load_config')
    @patch('ZR_Daily_Report.FileHandler')
    def test_main_with_empty_device_list(self, mock_file_handler, mock_load_config):
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

        # 执行主函数
        test_args = ['ZR_Daily_Report.py', '--mode', 'inventory']
        with patch.object(sys, 'argv', test_args):
            with patch('src.utils.ui_utils.choose_file', return_value='test.csv'), \
                 patch('src.utils.ui_utils.choose_directory', return_value=self.test_output_dir), \
                 patch('builtins.print'):  # 避免打印干扰
                result = main()

        # 验证结果
        self.assertIsNone(result)
        mock_load_config.assert_called_once()
        mock_file_instance.read_devices_from_csv.assert_called_once()

    @patch('ZR_Daily_Report.load_config')
    @patch('ZR_Daily_Report.FileHandler')
    @patch('ZR_Daily_Report.DatabaseHandler')
    @patch('ZR_Daily_Report.CustomerStatementGenerator')
    def test_statement_generation_success(self, mock_statement_handler, mock_db_handler, 
                                          mock_file_handler, mock_load_config):
        """测试对账单生成功能成功执行"""
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

        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {
                "device_code": "DEV001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            }
        ]

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_device_and_customer_info.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_inventory_data.return_value = (
            [(date(2025, 7, 1), 95.5), (date(2025, 7, 2), 93.2)],
            ["加注时间", "原油剩余比例"],
            [(date(2025, 7, 1), 95.5), (date(2025, 7, 2), 93.2)]
        )

        # 模拟对账单处理器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_customer_statement_from_template.return_value = None

        # 执行主函数
        test_args = ['ZR_Daily_Report.py', '--mode', 'statement']
        with patch.object(sys, 'argv', test_args):
            with patch('src.utils.ui_utils.choose_file', return_value='test.csv'), \
                 patch('src.utils.ui_utils.choose_directory', return_value=self.test_output_dir), \
                 patch('builtins.print'):  # 避免打印干扰
                result = main()

        # 验证结果
        self.assertIsNone(result)
        mock_load_config.assert_called_once()
        mock_file_instance.read_devices_from_csv.assert_called_once()
        mock_db_instance.connect.assert_called_once()
        mock_db_instance.get_device_and_customer_info.assert_called()
        mock_statement_instance.generate_customer_statement_from_template.assert_called()

    @patch('ZR_Daily_Report.load_config')
    @patch('ZR_Daily_Report.FileHandler')
    @patch('ZR_Daily_Report.DatabaseHandler')
    @patch('ZR_Daily_Report.InventoryReportGenerator')
    @patch('ZR_Daily_Report.CustomerStatementGenerator')
    def test_both_modes_success(self, mock_statement_handler, mock_inventory_handler,
                                mock_db_handler, mock_file_handler, mock_load_config):
        """测试同时生成库存报表和对账单功能成功执行"""
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

        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {
                "device_code": "DEV001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            }
        ]

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_device_and_customer_info.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_inventory_data.return_value = (
            [(date(2025, 7, 1), 95.5), (date(2025, 7, 2), 93.2)],
            ["加注时间", "原油剩余比例", "油品名称"],
            [{"加注时间": date(2025, 7, 1), "原油剩余比例": 95.5, "油品名称": "切削液"},
             {"加注时间": date(2025, 7, 2), "原油剩余比例": 93.2, "油品名称": "切削液"}]
        )

        # 模拟库存报告处理器
        mock_inventory_instance = mock_inventory_handler.return_value
        mock_inventory_instance.generate_inventory_report_with_chart.return_value = None

        # 模拟对账单处理器
        mock_statement_instance = mock_statement_handler.return_value
        mock_statement_instance.generate_customer_statement_from_template.return_value = None

        # 执行主函数
        test_args = ['ZR_Daily_Report.py', '--mode', 'both']
        with patch.object(sys, 'argv', test_args):
            with patch('src.utils.ui_utils.choose_file', return_value='test.csv'), \
                 patch('src.utils.ui_utils.choose_directory', return_value=self.test_output_dir), \
                 patch('builtins.print'):  # 避免打印干扰
                result = main()

        # 验证结果
        self.assertIsNone(result)
        # 在both模式下，load_config会被调用两次（库存报表和对账单各一次）
        self.assertEqual(mock_load_config.call_count, 2)
        mock_file_instance.read_devices_from_csv.assert_called_once()
        mock_db_instance.connect.assert_called()
        # 应该至少调用一次
        mock_db_instance.get_device_and_customer_info.assert_called()
        mock_db_instance.fetch_inventory_data.assert_called()
        mock_inventory_instance.generate_inventory_report_with_chart.assert_called()
        mock_statement_instance.generate_customer_statement_from_template.assert_called()

    @patch('ZR_Daily_Report.load_config')
    @patch('ZR_Daily_Report.FileHandler')
    @patch('ZR_Daily_Report.DatabaseHandler')
    def test_generate_inventory_reports_function(self, mock_db_handler, mock_file_handler, mock_load_config):
        """测试generate_inventory_reports函数独立执行"""
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

        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {
                "device_code": "DEV001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            }
        ]

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_device_and_customer_info.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_inventory_data.return_value = (
            [(date(2025, 7, 1), 95.5), (date(2025, 7, 2), 93.2)],
            ["加注时间", "原油剩余比例", "油品名称"],
            [{"加注时间": date(2025, 7, 1), "原油剩余比例": 95.5, "油品名称": "切削液"},
             {"加注时间": date(2025, 7, 2), "原油剩余比例": 93.2, "油品名称": "切削液"}]
        )

        # 执行generate_inventory_reports函数
        with patch('src.utils.ui_utils.choose_file', return_value='test.csv'), \
             patch('src.utils.ui_utils.choose_directory', return_value=self.test_output_dir), \
             patch('builtins.print'):  # 避免打印干扰
            result = generate_inventory_reports()

        # 验证结果
        self.assertIsNotNone(result)  # generate_inventory_reports函数返回有效设备列表
        mock_load_config.assert_called_once()
        mock_file_instance.read_devices_from_csv.assert_called_once()
        mock_db_instance.connect.assert_called_once()

    @patch('ZR_Daily_Report.load_config')
    @patch('ZR_Daily_Report.FileHandler')
    @patch('ZR_Daily_Report.DatabaseHandler')
    @patch('tkinter.Tk')
    def test_generate_customer_statement_function(self, mock_tk, mock_db_handler, mock_file_handler, mock_load_config):
        """测试generate_customer_statement函数独立执行"""
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

        # 模拟文件处理器
        mock_file_instance = mock_file_handler.return_value
        mock_file_instance.read_devices_from_csv.return_value = [
            {
                "device_code": "DEV001",
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            }
        ]

        # 模拟数据库处理器
        mock_db_instance = mock_db_handler.return_value
        mock_db_instance.get_device_and_customer_info.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_inventory_data.return_value = (
            [(date(2025, 7, 1), 95.5), (date(2025, 7, 2), 93.2)],
            ["加注时间", "原油剩余比例"],
            [(date(2025, 7, 1), 95.5), (date(2025, 7, 2), 93.2)]
        )

        # 模拟Tkinter
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_root.mainloop.return_value = None

        # 执行generate_customer_statement函数
        with patch('builtins.print'):  # 避免打印干扰
            result = generate_customer_statement()

        # 验证结果
        self.assertIsNone(result)  # generate_customer_statement函数没有返回值
        mock_load_config.assert_called_once()
        mock_file_instance.read_devices_from_csv.assert_called_once()
        mock_db_instance.connect.assert_called_once()


if __name__ == '__main__':
    unittest.main()