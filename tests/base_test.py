import os
import sys
import tempfile
import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch

# 添加项目根目录到sys.path，确保能正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class BaseTestCase(unittest.TestCase):
    """测试基类，提供通用的测试工具和方法"""

    def setUp(self):
        """测试前准备"""
        # 创建临时目录用于测试输出
        self.test_output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        # 清理临时目录
        if os.path.exists(self.test_output_dir):
            for file in os.listdir(self.test_output_dir):
                os.remove(os.path.join(self.test_output_dir, file))
            os.rmdir(self.test_output_dir)

    def create_test_device_data(
        self,
        device_code="TEST001",
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 10),
        customer_name="测试客户",
    ):
        """创建测试设备数据"""
        # 生成测试库存数据
        data = []
        current_date = start_date
        while current_date <= end_date:
            # 模拟库存数据，从100%逐渐下降
            inventory_percentage = max(0, 100 - (current_date - start_date).days * 2)
            data.append((current_date, inventory_percentage))
            current_date = date.fromordinal(current_date.toordinal() + 1)

        return {
            "device_code": device_code,
            "oil_name": "切削液",
            "data": data,
            "raw_data": [],  # 简化原始数据
            "columns": ["加注时间", "原油剩余比例"],
            "customer_name": customer_name,
        }

    def create_test_devices_list(self, count=3):
        """创建测试设备列表"""
        devices = []
        for i in range(count):
            device_code = f"TEST{i:03d}"
            device_data = self.create_test_device_data(
                device_code=device_code,
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 10),
                customer_name="测试客户",
            )
            devices.append(device_data)
        return devices

    def create_mock_db_connection(self):
        """创建模拟数据库连接"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        return mock_connection, mock_cursor

    def assert_file_exists(self, file_path, msg=None):
        """断言文件存在"""
        if not os.path.exists(file_path):
            standardMsg = f"文件不存在: {file_path}"
            self.fail(self._formatMessage(msg, standardMsg))

    def assert_file_contains_text(self, file_path, expected_text, msg=None):
        """断言文件包含指定文本"""
        self.assert_file_exists(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if expected_text not in content:
                standardMsg = f"文件 {file_path} 不包含文本: {expected_text}"
                self.fail(self._formatMessage(msg, standardMsg))
