import os
import sys
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.date_utils import parse_date, validate_csv_data
from tests.base_test import BaseTestCase


def get_date_range(start_date, end_date):
    """
    生成从开始日期到结束日期的日期列表（包含边界）
    
    Args:
        start_date (date): 开始日期
        end_date (date): 结束日期
        
    Returns:
        list[date]: 日期列表
    """
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date = current_date + timedelta(days=1)
    return date_list


def format_date(date_obj):
    """
    格式化日期对象为字符串
    
    Args:
        date_obj (datetime/date): 日期对象
        
    Returns:
        str: 格式化后的日期字符串
    """
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%Y-%m-%d")
    elif isinstance(date_obj, date):
        return date_obj.strftime("%Y-%m-%d")
    else:
        raise ValueError("Invalid date object")


class TestUtilsDateUtils(BaseTestCase):
    """
    utils.date_utils 模块的单元测试
    """
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        
    def test_parse_date_with_valid_string(self):
        """
        测试 parse_date 函数处理有效的日期字符串
        """
        result = parse_date("2025-07-01")
        self.assertEqual(result, datetime(2025, 7, 1))

    def test_parse_date_with_invalid_string(self):
        """
        测试 parse_date 函数处理无效的日期字符串
        """
        with self.assertRaises(ValueError):
            parse_date("invalid-date")

    def test_validate_csv_data_with_valid_data(self):
        """
        测试 validate_csv_data 函数处理有效的CSV数据
        """
        row = {
            "start_date": "2025-07-01",
            "end_date": "2025-07-31"
        }
        result = validate_csv_data(row)
        self.assertTrue(result)

    def test_validate_csv_data_with_invalid_start_date(self):
        """
        测试 validate_csv_data 函数处理无效的开始日期
        """
        row = {
            "start_date": "invalid-date",
            "end_date": "2025-07-31"
        }
        result = validate_csv_data(row)
        self.assertFalse(result)

    def test_validate_csv_data_with_invalid_end_date(self):
        """
        测试 validate_csv_data 函数处理无效的结束日期
        """
        row = {
            "start_date": "2025-07-01",
            "end_date": "invalid-date"
        }
        result = validate_csv_data(row)
        self.assertFalse(result)

    def test_validate_csv_data_with_start_after_end(self):
        """
        测试 validate_csv_data 函数处理开始日期晚于结束日期的情况
        """
        row = {
            "start_date": "2025-07-31",
            "end_date": "2025-07-01"
        }
        result = validate_csv_data(row)
        self.assertFalse(result)

    def test_get_date_range_with_valid_inputs(self):
        """
        测试 get_date_range 函数处理有效输入
        """
        start_date = date(2025, 7, 1)
        end_date = date(2025, 7, 5)
        result = get_date_range(start_date, end_date)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], start_date)
        self.assertEqual(result[-1], end_date)

    def test_get_date_range_with_start_after_end(self):
        """
        测试 get_date_range 函数处理开始日期晚于结束日期的情况
        """
        start_date = date(2025, 7, 5)
        end_date = date(2025, 7, 1)
        result = get_date_range(start_date, end_date)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], end_date)
        self.assertEqual(result[-1], start_date)

    def test_format_date_with_date_object(self):
        """
        测试 format_date 函数格式化日期对象
        """
        d = date(2025, 7, 1)
        result = format_date(d)
        self.assertEqual(result, "2025-07-01")

    def test_format_date_with_datetime_object(self):
        """
        测试 format_date 函数格式化datetime对象
        """
        dt = datetime(2025, 7, 1, 10, 30, 0)
        result = format_date(dt)
        self.assertEqual(result, "2025-07-01")


if __name__ == "__main__":
    unittest.main()