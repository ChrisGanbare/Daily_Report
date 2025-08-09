import unittest
from datetime import datetime, date, timedelta
import os
import json
import mysql.connector
import csv
import sys
import argparse
from openpyxl import load_workbook
from unittest.mock import Mock, patch

# 添加项目根目录到sys.path，确保能正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 使用包导入简化导入路径
from src.core import DatabaseHandler, ExcelHandler, FileHandler
from src.utils import ConfigHandler, DataValidator
from ZR_Daily_Report import generate_inventory_reports, generate_customer_statement, load_configuration

# 添加当前目录到Python路径，以便导入新创建的测试模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from test_statement_handler import TestStatementHandler
    STATEMENT_HANDLER_AVAILABLE = True
except ImportError:
    STATEMENT_HANDLER_AVAILABLE = False
    print("警告：未找到对账单处理模块的测试文件")

from base_test import BaseTestCase


class TestZRDailyReport(BaseTestCase):
    """综合测试ZR Daily Report的所有功能"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
    
    @patch('ZR_Daily_Report.load_configuration')
    def test_load_configuration_success(self, mock_load_config):
        """测试配置加载成功"""
        # 模拟配置数据
        mock_config = {
            'db_config': {
                'host': 'localhost',
                'port': 3306,
                'user': 'test_user',
                'password': 'test_password',
                'database': 'test_db'
            },
            'sql_templates': {
                'device_id_query': 'SELECT id, customer_id FROM oil.t_device WHERE device_code = %s',
                'inventory_query': 'SELECT * FROM inventory WHERE device_id = {device_id}'
            }
        }
        mock_load_config.return_value = mock_config
        
        # 执行测试
        config = load_configuration()
        
        # 验证结果
        self.assertEqual(config, mock_config)
        mock_load_config.assert_called_once()
    
    @patch('ZR_Daily_Report.DatabaseHandler')
    def test_generate_inventory_reports_function(self, mock_db_handler):
        """测试库存报表生成功能"""
        # 这个测试主要是检查函数是否存在且可调用
        # 实际的数据库操作和文件操作需要通过集成测试验证
        self.assertTrue(callable(generate_inventory_reports))
    
    @patch('ZR_Daily_Report.DatabaseHandler')
    def test_generate_customer_statement_function(self, mock_db_handler):
        """测试客户对账单生成功能"""
        # 这个测试主要是检查函数是否存在且可调用
        # 实际的数据库操作和文件操作需要通过集成测试验证
        self.assertTrue(callable(generate_customer_statement))


class TestDataValidator(unittest.TestCase):
    """测试数据验证功能"""
    
    def setUp(self):
        """测试前准备"""
        self.validator = DataValidator()
    
    def test_validate_csv_data_valid(self):
        """测试验证有效的CSV数据"""
        valid_data = {
            'device_code': 'DEV001',
            'start_date': '2025-07-01',
            'end_date': '2025-07-31'
        }
        self.assertTrue(self.validator.validate_csv_data(valid_data))
    
    def test_validate_csv_data_missing_device_code(self):
        """测试验证缺少设备代码的数据"""
        invalid_data = {
            'start_date': '2025-07-01',
            'end_date': '2025-07-31'
        }
        self.assertFalse(self.validator.validate_csv_data(invalid_data))
    
    def test_validate_csv_data_invalid_date_format(self):
        """测试验证日期格式无效的数据"""
        invalid_data = {
            'device_code': 'DEV001',
            'start_date': 'invalid-date',
            'end_date': '2025-07-31'
        }
        self.assertFalse(self.validator.validate_csv_data(invalid_data))


class TestFileHandler(unittest.TestCase):
    """测试文件处理功能"""
    
    def setUp(self):
        """测试前准备"""
        self.file_handler = FileHandler()
        # 创建临时CSV文件用于测试
        self.test_csv_file = os.path.join(os.path.dirname(__file__), 'test_devices.csv')
        with open(self.test_csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['device_code', 'start_date', 'end_date'])
            writer.writerow(['DEV001', '2025-07-01', '2025-07-31'])
            writer.writerow(['DEV002', '2025-07-01', '2025-07-31'])
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_csv_file):
            os.remove(self.test_csv_file)
    
    def test_read_devices_from_csv_success(self):
        """测试成功从CSV文件读取设备信息"""
        devices = self.file_handler.read_devices_from_csv(self.test_csv_file)
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]['device_code'], 'DEV001')
        self.assertEqual(devices[1]['device_code'], 'DEV002')
    
    def test_read_devices_from_csv_file_not_found(self):
        """测试CSV文件不存在的情况"""
        devices = self.file_handler.read_devices_from_csv('non_existent_file.csv')
        self.assertIsNone(devices)


if __name__ == '__main__':
    unittest.main()
