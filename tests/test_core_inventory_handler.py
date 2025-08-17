import os
import sys
import tempfile
import unittest
from datetime import date, timedelta
from unittest.mock import Mock, patch

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.inventory_handler import InventoryReportGenerator
from tests.base_test import BaseTestCase


class TestCoreInventoryHandler(BaseTestCase):
    """
    core.inventory_handler 模块的单元测试
    """
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.inventory_handler = InventoryReportGenerator()
        self.test_data = [
            (date(2025, 7, 1), 100.0),
            (date(2025, 7, 2), 95.0),
            (date(2025, 7, 3), 90.0),
        ]
        
    def test_inventoryreportgenerator_initialization(self):
        """
        测试 InventoryReportGenerator 类的初始化
        """
        # InventoryReportGenerator的__init__方法目前为空，只需确认能创建实例
        self.assertIsInstance(self.inventory_handler, InventoryReportGenerator)

    def test_inventoryreportgenerator_validate_inventory_value_valid(self):
        """
        测试 InventoryReportGenerator._validate_inventory_value 方法验证有效值
        """
        # 测试正常值
        self.assertEqual(self.inventory_handler._validate_inventory_value(100), 100.0)
        self.assertEqual(self.inventory_handler._validate_inventory_value(0), 0.0)
        self.assertEqual(self.inventory_handler._validate_inventory_value("50.5"), 50.5)
        # 测试大于100的值（应该允许）
        self.assertEqual(self.inventory_handler._validate_inventory_value(150), 150.0)

    def test_inventoryreportgenerator_validate_inventory_value_invalid(self):
        """
        测试 InventoryReportGenerator._validate_inventory_value 方法处理无效值
        """
        # 测试负数（应该抛出异常）
        with self.assertRaises(ValueError):
            self.inventory_handler._validate_inventory_value(-10)

        # 测试无效值（应该抛出异常）
        with self.assertRaises(ValueError):
            self.inventory_handler._validate_inventory_value("abc")

        with self.assertRaises(ValueError):
            self.inventory_handler._validate_inventory_value(None)

    def test_inventoryreportgenerator_generate_inventory_report_with_chart_xlsx(self):
        """
        测试 InventoryReportGenerator.generate_inventory_report_with_chart 方法生成XLSX文件
        """
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            output_file_path = f.name

        try:
            self.inventory_handler.generate_inventory_report_with_chart(
                inventory_data=self.test_data,
                output_file_path=output_file_path,
                device_code="TEST001",
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 3),
                oil_name="切削液"
            )
            
            # 验证文件已创建
            self.assertTrue(os.path.exists(output_file_path))
            
            # 验证文件不为空
            self.assertGreater(os.path.getsize(output_file_path), 0)
        finally:
            if os.path.exists(output_file_path):
                os.unlink(output_file_path)

    def test_inventoryreportgenerator_generate_inventory_report_with_chart_csv(self):
        """
        测试 InventoryReportGenerator.generate_inventory_report_with_chart 方法生成CSV文件
        """
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            output_file_path = f.name

        try:
            self.inventory_handler.generate_inventory_report_with_chart(
                inventory_data=self.test_data,
                output_file_path=output_file_path,
                device_code="TEST001",
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 3),
                oil_name="切削液",
                export_format="csv"
            )
            
            # CSV文件应该保存为.csv扩展名
            csv_file_path = output_file_path.replace('.xlsx', '.csv')
            
            # 验证文件已创建
            self.assertTrue(os.path.exists(csv_file_path))
            
            # 验证文件不为空
            self.assertGreater(os.path.getsize(csv_file_path), 0)
            
            # 清理CSV文件
            if os.path.exists(csv_file_path):
                os.unlink(csv_file_path)
        finally:
            # 确保原始xlsx文件也被清理（如果存在）
            if os.path.exists(output_file_path):
                os.unlink(output_file_path)

    def test_inventoryreportgenerator_generate_inventory_report_with_invalid_data(self):
        """
        测试 InventoryReportGenerator.generate_inventory_report_with_chart 方法处理包含无效数据的情况
        """
        # 包含无效数据的测试数据
        invalid_data = [
            (date(2025, 7, 1), 100.0),
            (date(2025, 7, 2), -5.0),  # 无效：负数
            (date(2025, 7, 3), "abc"),  # 无效：非数字
            (date(2025, 7, 4), 90.0),
        ]

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            output_file_path = f.name

        try:
            # 应该能够处理无效数据并生成文件
            self.inventory_handler.generate_inventory_report_with_chart(
                inventory_data=invalid_data,
                output_file_path=output_file_path,
                device_code="TEST001",
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 4),
                oil_name="切削液"
            )
            
            # 验证文件已创建
            self.assertTrue(os.path.exists(output_file_path))
        finally:
            if os.path.exists(output_file_path):
                os.unlink(output_file_path)

    def test_inventoryreportgenerator_generate_inventory_report_with_empty_data(self):
        """
        测试 InventoryReportGenerator.generate_inventory_report_with_chart 方法处理空数据的情况
        """
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            output_file_path = f.name

        try:
            # 应该能够处理空数据并生成文件
            self.inventory_handler.generate_inventory_report_with_chart(
                inventory_data=[],
                output_file_path=output_file_path,
                device_code="TEST001",
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 3),
                oil_name="切削液"
            )
            
            # 验证文件已创建
            self.assertTrue(os.path.exists(output_file_path))
        finally:
            if os.path.exists(output_file_path):
                os.unlink(output_file_path)


if __name__ == "__main__":
    unittest.main()