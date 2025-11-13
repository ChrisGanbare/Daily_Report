import os
import sys
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.date_utils import parse_date, validate_csv_data, validate_date_span
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
    """utils.date_utils 模块的单元测试"""

    def test_parse_date_with_valid_iso_format(self):
        """
        测试 parse_date 函数处理有效的ISO日期格式
        """
        date_str = "2025-07-01"
        result = parse_date(date_str)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 7)
        self.assertEqual(result.day, 1)

    def test_parse_date_with_valid_slash_format(self):
        """
        测试 parse_date 函数处理有效的斜杠日期格式
        """
        date_str = "2025/7/1"
        result = parse_date(date_str)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 7)
        self.assertEqual(result.day, 1)

    def test_parse_date_with_invalid_format(self):
        """
        测试 parse_date 函数处理无效的日期格式
        """
        date_str = "invalid-date"
        with self.assertRaises(ValueError):
            parse_date(date_str)

    def test_parse_date_with_empty_string(self):
        """
        测试 parse_date 函数处理空字符串
        """
        date_str = ""
        with self.assertRaises(ValueError):
            parse_date(date_str)

    def test_validate_csv_data_with_valid_dates(self):
        """
        测试 validate_csv_data 函数处理有效日期
        """
        row = {"start_date": "2025-07-01", "end_date": "2025-07-10"}
        result = validate_csv_data(row)
        self.assertTrue(result)

    def test_validate_csv_data_with_invalid_start_date_format(self):
        """
        测试 validate_csv_data 函数处理无效的开始日期格式
        """
        row = {"start_date": "invalid-date", "end_date": "2025-07-10"}
        result = validate_csv_data(row)
        self.assertFalse(result)

    def test_validate_csv_data_with_invalid_end_date_format(self):
        """
        测试 validate_csv_data 函数处理无效的结束日期格式
        """
        row = {"start_date": "2025-07-01", "end_date": "invalid-date"}
        result = validate_csv_data(row)
        self.assertFalse(result)

    def test_validate_csv_data_with_start_after_end(self):
        """
        测试 validate_csv_data 函数处理开始日期晚于结束日期的情况
        """
        row = {"start_date": "2025-07-31", "end_date": "2025-07-01"}
        result = validate_csv_data(row)
        self.assertFalse(result)

    def test_validate_date_span_with_valid_span_less_than_1_month(self):
        """
        测试 validate_date_span 函数处理有效日期跨度（小于1个月）
        """
        row = {"start_date": "2025-07-01", "end_date": "2025-07-15"}
        result = validate_date_span(row)
        self.assertTrue(result)

    def test_validate_date_span_with_valid_span_exactly_1_month(self):
        """
        测试 validate_date_span 函数处理有效日期跨度（正好1个月）
        """
        row = {"start_date": "2025-07-01", "end_date": "2025-07-31"}
        result = validate_date_span(row)
        self.assertTrue(result)

    def test_validate_date_span_with_invalid_span_exceeds_1_month(self):
        """
        测试 validate_date_span 函数处理无效日期跨度（超过1个月）
        """
        row = {"start_date": "2025-07-01", "end_date": "2025-08-02"}
        result = validate_date_span(row)
        self.assertFalse(result)

    def test_validate_date_span_with_invalid_span_exactly_1_month_and_one_day(self):
        """
        测试 validate_date_span 函数处理无效日期跨度（正好1个月零1天）
        """
        row = {"start_date": "2025-07-01", "end_date": "2025-08-02"}
        result = validate_date_span(row)
        self.assertFalse(result)

    def test_validate_date_span_with_invalid_span_more_than_1_month(self):
        """
        测试 validate_date_span 函数处理无效日期跨度（超过1个月）
        """
        row = {"start_date": "2025-07-01", "end_date": "2025-08-15"}
        result = validate_date_span(row)
        self.assertFalse(result)

    def test_validate_date_span_with_invalid_start_date_format(self):
        """
        测试 validate_date_span 函数处理无效的开始日期格式
        """
        row = {"start_date": "invalid-date", "end_date": "2025-08-15"}
        result = validate_date_span(row)
        self.assertFalse(result)

    def test_validate_date_span_with_invalid_end_date_format(self):
        """
        测试 validate_date_span 函数处理无效的结束日期格式
        """
        row = {"start_date": "2025-07-01", "end_date": "invalid-date"}
        result = validate_date_span(row)
        self.assertFalse(result)

    def test_validate_date_span_with_same_date(self):
        """
        测试 validate_date_span 函数处理相同日期
        """
        row = {"start_date": "2025-07-01", "end_date": "2025-07-01"}
        result = validate_date_span(row)
        self.assertTrue(result)

    def test_validate_date_span_with_one_day_difference(self):
        """
        测试 validate_date_span 函数处理1天日期差
        """
        row = {"start_date": "2025-07-01", "end_date": "2025-07-02"}
        result = validate_date_span(row)
        self.assertTrue(result)

    def test_validate_date_span_with_leap_year_dates(self):
        """
        测试 validate_date_span 函数处理闰年日期
        """
        row = {"start_date": "2024-02-28", "end_date": "2024-03-28"}
        result = validate_date_span(row)
        # 2月28日到3月28日正好1个月，应该返回True
        self.assertTrue(result)
        
        # 测试超过1个月的情况
        row2 = {"start_date": "2024-02-28", "end_date": "2024-03-29"}
        result2 = validate_date_span(row2)
        # 2月28日到3月29日超过1个月，应该返回False
        self.assertFalse(result2)

    def test_validate_date_span_with_february_dates_edge_case(self):
        """
        测试 validate_date_span 函数处理2月边界情况
        """
        row = {"start_date": "2024-02-28", "end_date": "2024-03-27"}
        result = validate_date_span(row)
        # 2月28日到3月27日未超过1个月，应该返回True
        self.assertTrue(result)

    def test_validate_date_span_with_february_dates(self):
        """
        测试 validate_date_span 函数处理2月日期（非闰年）
        """
        row = {"start_date": "2025-01-31", "end_date": "2025-02-28"}
        result = validate_date_span(row)
        # 1月31日到2月28日未超过1个月，应该返回True
        self.assertTrue(result)
        
        # 测试超过1个月的情况
        row2 = {"start_date": "2025-01-31", "end_date": "2025-03-01"}
        result2 = validate_date_span(row2)
        # 1月31日到3月1日超过1个月，应该返回False
        self.assertFalse(result2)

    def test_validate_date_span_with_year_crossing_dates(self):
        """
        测试 validate_date_span 函数处理跨年日期
        """
        row = {"start_date": "2025-12-01", "end_date": "2025-12-31"}
        result = validate_date_span(row)
        self.assertTrue(result)
        
        # 测试超过1个月的情况 - 从12月1日到次年1月31日，这超过了1个月
        row2 = {"start_date": "2025-12-01", "end_date": "2026-01-31"}
        result2 = validate_date_span(row2)
        self.assertFalse(result2)
        
        # 测试正好1个月的情况 - 从12月1日到次年1月1日，这正好是1个月
        row3 = {"start_date": "2025-12-01", "end_date": "2026-01-01"}
        result3 = validate_date_span(row3)
        self.assertTrue(result3)

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