import os
import sys
import unittest
from datetime import date, datetime
from unittest.mock import Mock, patch

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.data_validator import DataValidator
from tests.base_test import BaseTestCase


class TestUtilsDataValidator(BaseTestCase):
    """
    utils.data_validator 模块的单元测试
    """

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.validator = DataValidator()

    def test_validate_date_with_valid_string(self):
        """
        测试 validate_date 函数处理有效的日期字符串
        """
        result = self.validator.validate_date("2025-07-01")
        self.assertTrue(result)

    def test_validate_date_with_invalid_string(self):
        """
        测试 validate_date 函数处理无效的日期字符串
        """
        result = self.validator.validate_date("invalid-date")
        self.assertFalse(result)

    def test_parse_date_with_valid_string(self):
        """
        测试 parse_date 函数处理有效的日期字符串
        """
        result = self.validator.parse_date("2025-07-01")
        self.assertEqual(result, date(2025, 7, 1))

    def test_parse_date_with_invalid_string(self):
        """
        测试 parse_date 函数处理无效的日期字符串
        """
        with self.assertRaises(ValueError):
            self.validator.parse_date("invalid-date")

    def test_parse_date_with_different_formats(self):
        """
        测试 parse_date 函数处理不同日期格式
        """
        # 测试 YYYY/MM/DD 格式
        result = self.validator.parse_date("2025/07/01")
        self.assertEqual(result, date(2025, 7, 1))

        # 测试 YYYY-MM-DD HH:MM:SS 格式
        result = self.validator.parse_date("2025-07-01 10:30:00")
        self.assertEqual(result, date(2025, 7, 1))

        # 测试 YYYY/MM/DD HH:MM:SS 格式
        result = self.validator.parse_date("2025/07/01 10:30:00")
        self.assertEqual(result, date(2025, 7, 1))

    def test_parse_date_with_unsupported_format(self):
        """
        测试 parse_date 函数处理不支持的日期格式
        """
        with self.assertRaises(ValueError) as context:
            self.validator.parse_date("01-07-2025")  # DD-MM-YYYY 格式不支持

        self.assertIn("日期格式错误", str(context.exception))

    def test_validate_csv_data_success(self):
        """
        测试 validate_csv_data 函数验证有效的CSV数据行
        """
        row = {"start_date": "2025-07-01", "end_date": "2025-07-31"}

        result = self.validator.validate_csv_data(row)
        self.assertTrue(result)

    def test_validate_csv_data_invalid_start_date(self):
        """
        测试 validate_csv_data 函数处理无效的开始日期
        """
        row = {"start_date": "invalid-date", "end_date": "2025-07-31"}

        result = self.validator.validate_csv_data(row)
        self.assertFalse(result)

    def test_validate_csv_data_invalid_end_date(self):
        """
        测试 validate_csv_data 函数处理无效的结束日期
        """
        row = {"start_date": "2025-07-01", "end_date": "invalid-date"}

        result = self.validator.validate_csv_data(row)
        self.assertFalse(result)

    def test_validate_csv_data_date_logic_error(self):
        """
        测试 validate_csv_data 函数处理日期逻辑错误（开始日期晚于结束日期）
        """
        row = {"start_date": "2025-07-31", "end_date": "2025-07-01"}

        result = self.validator.validate_csv_data(row)
        self.assertFalse(result)

    def test_validate_csv_data_missing_fields(self):
        """
        测试 validate_csv_data 函数处理缺少必要字段的情况
        """
        row = {
            "start_date": "2025-07-01"
            # 缺少 end_date 字段
        }

        # 应该引发 KeyError
        with self.assertRaises(KeyError):
            self.validator.validate_csv_data(row)


if __name__ == "__main__":
    unittest.main()
