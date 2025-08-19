import csv
import os
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import Mock, patch

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.file_handler import FileHandler
from tests.base_test import BaseTestCase


class TestCoreFileHandler(BaseTestCase):
    """
    core.file_handler 模块的单元测试
    """

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.file_handler = FileHandler()

    def test_filehandler_initialization(self):
        """
        测试 FileHandler 类的初始化
        """
        # FileHandler的__init__方法目前为空，只需确认能创建实例
        self.assertIsInstance(self.file_handler, FileHandler)

    def test_filehandler_read_devices_from_csv_with_valid_file(self):
        """
        测试 FileHandler.read_devices_from_csv 方法读取有效CSV文件
        """
        # 创建临时CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-10
DEV002,2025-07-01,2025-07-10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(len(devices), 2)
            self.assertEqual(devices[0]["device_code"], "DEV001")
            self.assertEqual(devices[1]["device_code"], "DEV002")
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_empty_file(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理空CSV文件
        """
        # 创建空的CSV文件用于测试
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(devices, [])
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_empty_rows(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理包含空行的CSV文件
        """
        # 创建包含空行的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-10

DEV002,2025-07-01,2025-07-10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(len(devices), 2)
            self.assertEqual(devices[0]["device_code"], "DEV001")
            self.assertEqual(devices[1]["device_code"], "DEV002")
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_missing_device_code(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理缺少device_code的CSV文件
        """
        # 创建缺少device_code列的CSV文件用于测试
        csv_content = """start_date,end_date
2025-07-01,2025-07-10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(devices, [])
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_missing_file(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理文件不存在的情况
        """
        devices = self.file_handler.read_devices_from_csv("non_existent_file.csv")
        self.assertEqual(devices, [])

    def test_filehandler_read_devices_from_csv_with_invalid_data(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理无效数据
        """
        # 创建包含无效数据的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
,2025-07-01,2025-07-10
DEV002,,2025-07-10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            # 应该跳过无效数据行
            self.assertEqual(len(devices), 0)
        finally:
            os.unlink(csv_file_path)


if __name__ == "__main__":
    unittest.main()
