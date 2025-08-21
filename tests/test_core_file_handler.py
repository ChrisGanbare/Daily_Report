import csv
import os
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import Mock, patch

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.file_handler import FileHandler, FileReadError
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
            # 应该抛出FileReadError异常
            with self.assertRaises(FileReadError):
                self.file_handler.read_devices_from_csv(csv_file_path)
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_invalid_device_code_format(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理无效设备编码格式
        """
        # 创建包含无效设备编码格式的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
123DEV,2025-07-01,2025-07-10
DEV@002,2025-07-01,2025-07-10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # 应该抛出FileReadError异常，因为设备编码验证失败会终止整个处理过程
            with self.assertRaises(FileReadError):
                self.file_handler.read_devices_from_csv(csv_file_path)
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_duplicate_devices_same_dates(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理重复设备编码且日期相同的情况
        """
        # 创建包含重复设备编码且日期相同的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-10
DEV001,2025-07-01,2025-07-10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # 应该抛出FileReadError异常
            with self.assertRaises(FileReadError):
                self.file_handler.read_devices_from_csv(csv_file_path)
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_duplicate_devices_different_dates(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理重复设备编码但日期不同的情况
        """
        # 创建包含重复设备编码但日期不同的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-10
DEV001,2025-07-05,2025-07-15
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # 应该正常读取两个设备信息
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(len(devices), 2)
            self.assertEqual(devices[0]["device_code"], "DEV001")
            self.assertEqual(devices[0]["start_date"], "2025-07-01")
            self.assertEqual(devices[0]["end_date"], "2025-07-10")
            self.assertEqual(devices[1]["device_code"], "DEV001")
            self.assertEqual(devices[1]["start_date"], "2025-07-05")
            self.assertEqual(devices[1]["end_date"], "2025-07-15")
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_invalid_date_span(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理日期跨度超过2个月的情况
        """
        # 创建包含日期跨度超过2个月的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-10-01
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # 应该抛出FileReadError异常
            with self.assertRaises(FileReadError):
                self.file_handler.read_devices_from_csv(csv_file_path)
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_device_limit_exceeded(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理设备数量超过限制的情况
        """
        # 创建包含超过限制设备数量的CSV文件用于测试
        csv_content = "device_code,start_date,end_date\n"
        for i in range(301):  # 超过最大限制300台
            csv_content += f"DEV{i:03d},2025-07-01,2025-07-10\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # 应该抛出FileReadError异常
            with self.assertRaises(FileReadError):
                self.file_handler.read_devices_from_csv(csv_file_path)
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_empty_content(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理文件内容为空的情况
        """
        # 创建内容为空的CSV文件用于测试
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("")
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(devices, [])
        finally:
            os.unlink(csv_file_path)

    # 新增测试用例

    def test_filehandler_read_devices_from_csv_with_invalid_file_type(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理非CSV文件
        """
        # 创建一个.txt文件用于测试
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("device_code,start_date,end_date\nDEV001,2025-07-01,2025-07-10")
            txt_file_path = f.name

        try:
            # 应该抛出FileReadError异常
            with self.assertRaises(FileReadError):
                self.file_handler.read_devices_from_csv(txt_file_path)
        finally:
            os.unlink(txt_file_path)

    def test_filehandler_read_devices_from_csv_with_missing_required_fields(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理缺少必要字段的情况
        """
        # 创建缺少必要字段的CSV文件用于测试
        csv_content = """device_code,start_date
DEV001,2025-07-01
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # 应该返回空列表
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(devices, [])
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_no_header(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理没有标题行的CSV文件
        """
        # 创建没有标题行的CSV文件用于测试
        csv_content = """DEV001,2025-07-01,2025-07-10"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            # 没有标题行应该无法正确解析，返回空列表
            self.assertEqual(devices, [])
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_invalid_encoding(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理包含无效设备编码的文件
        """
        # 创建包含无效设备编码的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-10
设备002,2025-07-01,2025-07-10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding='gbk') as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # 应该抛出FileReadError异常
            with self.assertRaises(FileReadError):
                self.file_handler.read_devices_from_csv(csv_file_path)
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_date_validation_failure(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理日期验证失败的情况
        """
        # 创建包含无效日期格式的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,invalid-date,2025-07-10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # 应该抛出FileReadError异常
            with self.assertRaises(FileReadError):
                self.file_handler.read_devices_from_csv(csv_file_path)
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_device_code_not_start_with_letter(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理设备编码不以字母开头的情况
        """
        # 创建设备编码不以字母开头的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
123DEV,2025-07-01,2025-07-10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # 应该抛出FileReadError异常
            with self.assertRaises(FileReadError):
                self.file_handler.read_devices_from_csv(csv_file_path)
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_device_code_special_characters(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理设备编码包含特殊字符的情况
        """
        # 创建设备编码包含特殊字符的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV@001,2025-07-01,2025-07-10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # 应该抛出FileReadError异常
            with self.assertRaises(FileReadError):
                self.file_handler.read_devices_from_csv(csv_file_path)
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_valid_device_limit(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理设备数量在限制范围内的情况
        """
        # 创建设备数量在限制范围内的CSV文件用于测试
        csv_content = "device_code,start_date,end_date\n"
        for i in range(5):  # 5台设备，在限制范围内
            csv_content += f"DEV{i:03d},2025-07-01,2025-07-10\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(len(devices), 5)
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_valid_file_extended(self):
        """
        测试 FileHandler.read_devices_from_csv 方法读取更复杂的有效CSV文件
        包含多种日期格式、设备编码格式和边界情况
        """
        # 创建包含多种日期格式和设备编码的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-10
DEV002,2025/07/05,2025/08/05
DEV003A,2025-06-15,2025-08-14
DEVICE004,2025/01/01,2025/02/28
DEV5,2025-05-01,2025-06-30
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(len(devices), 5)
            
            # 验证设备编码
            self.assertEqual(devices[0]["device_code"], "DEV001")
            self.assertEqual(devices[1]["device_code"], "DEV002")
            self.assertEqual(devices[2]["device_code"], "DEV003A")
            self.assertEqual(devices[3]["device_code"], "DEVICE004")
            self.assertEqual(devices[4]["device_code"], "DEV5")
            
            # 验证日期格式
            self.assertEqual(devices[0]["start_date"], "2025-07-01")
            self.assertEqual(devices[0]["end_date"], "2025-07-10")
            self.assertEqual(devices[1]["start_date"], "2025/07/05")
            self.assertEqual(devices[1]["end_date"], "2025/08/05")
            self.assertEqual(devices[2]["start_date"], "2025-06-15")
            self.assertEqual(devices[2]["end_date"], "2025-08-14")
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_single_device(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理只有一个设备的情况
        """
        # 创建只包含一个设备的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]["device_code"], "DEV001")
            self.assertEqual(devices[0]["start_date"], "2025-07-01")
            self.assertEqual(devices[0]["end_date"], "2025-07-10")
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_max_devices(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理最大设备数量的情况
        """
        # 创建刚好达到最大设备数量限制的CSV文件用于测试
        csv_content = "device_code,start_date,end_date\n"
        for i in range(200):  # 最大限制200台设备
            csv_content += f"DEV{i:03d},2025-07-01,2025-07-10\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(len(devices), 200)
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_utf8_sig_encoding(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理UTF-8-SIG编码的文件
        """
        # 创建UTF-8-SIG编码的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-10
DEV002,2025-07-05,2025-07-15
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding='utf-8-sig') as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(len(devices), 2)
            self.assertEqual(devices[0]["device_code"], "DEV001")
            self.assertEqual(devices[1]["device_code"], "DEV002")
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_gbk_encoding(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理GBK编码的文件
        """
        # 创建GBK编码的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-10
DEV002,2025-07-05,2025-07-15
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding='gbk') as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(len(devices), 2)
            self.assertEqual(devices[0]["device_code"], "DEV001")
            self.assertEqual(devices[1]["device_code"], "DEV002")
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_date_validation(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理日期验证功能
        """
        # 创建包含各种日期格式的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-10
DEV002,2025/07/05,2025/07/15
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            devices = self.file_handler.read_devices_from_csv(csv_file_path)
            self.assertEqual(len(devices), 2)
            self.assertEqual(devices[0]["start_date"], "2025-07-01")
            self.assertEqual(devices[0]["end_date"], "2025-07-10")
            self.assertEqual(devices[1]["start_date"], "2025/07/05")
            self.assertEqual(devices[1]["end_date"], "2025/07/15")
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_invalid_date_logic(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理日期逻辑错误（开始日期晚于结束日期）
        """
        # 创建包含日期逻辑错误的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-10,2025-07-01
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # 应该抛出FileReadError异常
            with self.assertRaises(FileReadError):
                self.file_handler.read_devices_from_csv(csv_file_path)
        finally:
            os.unlink(csv_file_path)

    def test_filehandler_read_devices_from_csv_with_date_span_exceeding_limit(self):
        """
        测试 FileHandler.read_devices_from_csv 方法处理日期跨度超过2个月的情况
        """
        # 创建日期跨度超过2个月的CSV文件用于测试
        csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-10-01
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # 应该抛出FileReadError异常
            with self.assertRaises(FileReadError):
                self.file_handler.read_devices_from_csv(csv_file_path)
        finally:
            os.unlink(csv_file_path)

if __name__ == "__main__":
    unittest.main()