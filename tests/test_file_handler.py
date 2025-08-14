import csv
import os
import tempfile
import unittest
from unittest.mock import patch, mock_open
import sys

# 添加项目根目录到sys.path，确保能正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.file_handler import FileHandler
from tests.base_test import BaseTestCase


class TestFileHandler(BaseTestCase):
    """测试文件处理功能"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.file_handler = FileHandler()

    def test_read_devices_from_csv_utf8_success(self):
        """测试成功从UTF-8编码的CSV文件读取设备信息"""
        # 创建临时CSV文件
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-31
DEV002,2025-07-01,2025-07-31
"""
        csv_file = os.path.join(self.test_output_dir, 'test_devices_utf8.csv')
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_content)

        devices = self.file_handler.read_devices_from_csv(csv_file)
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]['device_code'], 'DEV001')
        self.assertEqual(devices[1]['device_code'], 'DEV002')

    def test_read_devices_from_csv_gbk_success(self):
        """测试成功从GBK编码的CSV文件读取设备信息"""
        # 创建临时CSV文件
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-31
DEV002,2025-07-01,2025-07-31
"""
        csv_file = os.path.join(self.test_output_dir, 'test_devices_gbk.csv')
        with open(csv_file, 'w', encoding='gbk', newline='') as f:
            f.write(csv_content)

        devices = self.file_handler.read_devices_from_csv(csv_file)
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]['device_code'], 'DEV001')
        self.assertEqual(devices[1]['device_code'], 'DEV002')

    def test_read_devices_from_csv_file_not_found(self):
        """测试CSV文件不存在的情况"""
        devices = self.file_handler.read_devices_from_csv('non_existent_file.csv')
        self.assertEqual(devices, [])

    def test_read_devices_from_csv_empty_file(self):
        """测试读取空CSV文件"""
        # 创建空文件
        csv_file = os.path.join(self.test_output_dir, 'empty.csv')
        with open(csv_file, 'w', encoding='utf-8') as f:
            pass  # 创建空文件

        devices = self.file_handler.read_devices_from_csv(csv_file)
        self.assertEqual(devices, [])

    def test_read_devices_from_csv_with_empty_rows(self):
        """测试读取包含空行的CSV文件"""
        # 创建包含空行的CSV文件
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-31

DEV002,2025-07-01,2025-07-31

"""
        csv_file = os.path.join(self.test_output_dir, 'test_devices_with_empty_rows.csv')
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_content)

        devices = self.file_handler.read_devices_from_csv(csv_file)
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]['device_code'], 'DEV001')
        self.assertEqual(devices[1]['device_code'], 'DEV002')

    def test_read_devices_from_csv_missing_device_code(self):
        """测试读取缺少设备代码字段的CSV文件"""
        # 创建缺少必要字段的CSV文件
        csv_content = """wrong_code,start_date,end_date
DEV001,2025-07-01,2025-07-31
"""
        csv_file = os.path.join(self.test_output_dir, 'test_devices_missing_field.csv')
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_content)

        devices = self.file_handler.read_devices_from_csv(csv_file)
        self.assertEqual(devices, [])

    def test_read_devices_from_csv_empty_device_code(self):
        """测试读取设备代码为空的CSV文件"""
        # 创建包含空设备代码的CSV文件
        csv_content = """device_code,start_date,end_date
,2025-07-01,2025-07-31
DEV002,2025-07-01,2025-07-31
"""
        csv_file = os.path.join(self.test_output_dir, 'test_devices_empty_code.csv')
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_content)

        devices = self.file_handler.read_devices_from_csv(csv_file)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['device_code'], 'DEV002')

    @patch('builtins.open')
    def test_read_devices_from_csv_unicode_error(self, mock_open_func):
        """测试读取文件时发生UnicodeDecodeError"""
        # 模拟打开文件时出现UnicodeDecodeError异常
        mock_open_func.side_effect = UnicodeDecodeError('utf-8', b'\x00\x00', 0, 1, 'error')
        
        csv_file = os.path.join(self.test_output_dir, 'test_unicode_error.csv')
        # 创建一个空文件
        with open(csv_file, 'w') as f:
            pass

        devices = self.file_handler.read_devices_from_csv(csv_file)
        self.assertEqual(devices, [])


if __name__ == '__main__':
    unittest.main()