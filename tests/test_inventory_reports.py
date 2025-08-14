import os
import tempfile
import unittest
from datetime import date
from unittest.mock import Mock, patch

from src.core.inventory_handler import InventoryReportHandler
from tests.base_test import BaseTestCase


class TestInventoryReports(BaseTestCase):
    """测试库存报表生成功能"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.excel_handler = InventoryReportHandler()

    def test_generate_excel_with_chart_success(self):
        """测试成功生成带图表的Excel文件"""
        # 准备测试数据
        test_data = [
            (date(2025, 7, 1), 100.0),
            (date(2025, 7, 2), 95.0),
            (date(2025, 7, 3), 90.0),
        ]

        # 生成测试文件路径
        output_file = os.path.join(self.test_output_dir, "test_inventory_report.xlsx")

        # 执行测试
        self.excel_handler.generate_excel_with_chart(
            data=test_data,
            output_file=output_file,
            device_code="TEST001",
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 3),
        )

        # 验证结果
        self.assert_file_exists(output_file)

    def test_generate_excel_with_empty_data(self):
        """测试生成空数据的Excel文件"""
        # 准备空数据
        test_data = []

        # 生成测试文件路径
        output_file = os.path.join(self.test_output_dir, "test_empty_report.xlsx")

        # 执行测试
        self.excel_handler.generate_excel_with_chart(
            data=test_data,
            output_file=output_file,
            device_code="TEST001",
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 3),
        )

        # 验证结果
        self.assert_file_exists(output_file)

    def test_generate_excel_with_invalid_data(self):
        """测试生成包含无效数据的Excel文件"""
        # 准备包含无效数据的测试数据
        test_data = [
            (date(2025, 7, 1), 100.0),
            (date(2025, 7, 2), -5.0),  # 无效数据
            (date(2025, 7, 3), 150.0),  # 超过100%的数据
        ]

        # 生成测试文件路径
        output_file = os.path.join(self.test_output_dir, "test_invalid_report.xlsx")

        # 执行测试
        self.excel_handler.generate_excel_with_chart(
            data=test_data,
            output_file=output_file,
            device_code="TEST001",
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 3),
        )

        # 验证结果
        self.assert_file_exists(output_file)


if __name__ == "__main__":
    unittest.main()