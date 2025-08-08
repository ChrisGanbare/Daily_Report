import unittest
from datetime import datetime, date, timedelta
import os
import json
import mysql.connector
import csv
import sys
from openpyxl import load_workbook

# 添加项目根目录到sys.path，确保能正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 使用包导入简化导入路径
from src.core import DatabaseHandler, ExcelHandler, FileHandler
from src.utils import ConfigHandler, DataValidator

# 添加当前目录到Python路径，以便导入新创建的测试模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from test_statement_handler import TestStatementHandler
    STATEMENT_HANDLER_AVAILABLE = True
except ImportError:
    STATEMENT_HANDLER_AVAILABLE = False
    print("警告：未找到对账单处理模块的测试文件")


class TestZRDailyReport(unittest.TestCase):
    """综合测试ZR Daily Report的所有功能"""
    
    def setUp(self):
        """测试前准备"""
        # 读取配置文件，使用项目根目录下的配置文件
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'query_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.query_config = json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，创建一个模拟的配置
            self.query_config = {
                "db_config": {
                    "host": "localhost",
                    "port": 3306,
                    "user": "test_user",
                    "password": "test_password",
                    "database": "test_db"
                },
                "sql_templates": {
                    "get_device_id": "SELECT id FROM devices WHERE device_no = %s",
                    "fetch_inventory_data": "SELECT date, inventory_value FROM inventory WHERE device_id = %s AND date BETWEEN %s AND %s ORDER BY date"
                }
            }
        
        # 初始化处理器
        self.db_handler = DatabaseHandler()
        self.excel_handler = ExcelHandler()
        self.config_handler = ConfigHandler()
        self.file_handler = FileHandler()
        self.data_validator = DataValidator()

    def test_file_name_validation(self):
        """测试文件名验证功能"""
        print("\n开始测试文件名验证...")
        valid_filename = "AW46抗磨液压油_TW24011700700016_202401.xlsx"
        invalid_filenames = [
            "AW46抗磨液压油-TW24011700700016-202401.xlsx",  # 错误连接符
            "AW46抗磨液压油_TW24011700700016_2024.xlsx",    # 错误月份格式
            "AW46抗磨液压油_TW24011700700016.xlsx",         # 缺少月份
            "AW46抗磨液压油_TW24011700700016_202401.xls"    # 错误扩展名
        ]
        
        # 测试有效文件名
        result = self.file_handler.validate_file_name(valid_filename)
        self.assertTrue(result)
        print(f"验证通过: {valid_filename}")
        
        # 测试无效文件名
        for filename in invalid_filenames:
            result = self.file_handler.validate_file_name(filename)
            self.assertFalse(result, f"文件名应该验证失败: {filename}")
            print(f"验证失败: {filename}")

    def test_database_connection(self):
        """测试数据库连接功能"""
        print("\n开始测试数据库连接...")
        
        try:
            connection = self.db_handler.connect()
            
            # 检查连接是否成功建立
            self.assertIsNotNone(connection)
            self.assertTrue(connection.is_connected())
            
            # 测试执行简单查询
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"数据库版本: {version[0]}")
            
            # 关闭连接
            cursor.close()
            self.db_handler.disconnect()
            print("数据库连接功能测试通过")
        except Exception as e:
            self.fail(f"数据库连接测试失败: {e}")

    def test_get_device_id_by_no(self):
        """测试根据设备编号查询设备ID功能"""
        print("\n开始测试根据设备编号查询设备ID功能...")
        
        try:
            self.db_handler.connect()
            
            # 从配置中获取SQL模板
            sql_templates = self.query_config.get('sql_templates', {})
            device_query_template = sql_templates.get('device_id_query', "SELECT id FROM oil.t_device WHERE device_no = %s ORDER BY create_time DESC LIMIT 1")
            
            # 测试查询一个不存在的设备编号
            device_id = self.db_handler.get_device_id_by_no("NON_EXISTENT_DEVICE", device_query_template)
            self.assertIsNone(device_id)
            
            self.db_handler.disconnect()
            print("根据设备编号查询设备ID功能测试通过（验证了函数能正确处理不存在的设备）")
        except Exception as e:
            self.fail(f"测试过程中出现异常: {e}")

    def test_fetch_inventory_data_from_db(self):
        """测试从数据库获取库存数据功能"""
        print("\n开始测试从数据库获取库存数据功能...")
        
        try:
            self.db_handler.connect()
            
            # 使用一个简单的测试查询
            test_query = "SELECT 1 as id, NOW() as '加注时间', '测试油品' as '油品名称', 0.95 as '原油剩余比例'"
            data, columns, raw_data = self.db_handler.fetch_inventory_data(test_query)
            
            # 验证返回的数据结构
            self.assertIsInstance(data, list)
            self.assertIsInstance(columns, list)
            self.assertIsInstance(raw_data, list)
            
            self.db_handler.disconnect()
            print(f"从数据库获取库存数据功能测试通过，共获取到 {len(data)} 条处理后的数据")
        except Exception as e:
            self.fail(f"测试过程中出现异常: {e}")

    def test_read_devices_from_csv(self):
        """测试读取设备信息CSV文件功能"""
        print("\n开始测试读取设备信息CSV文件功能...")
        
        # 创建临时设备信息文件用于测试 (UTF-8编码)
        test_devices = [
            {"device_no": "MO24111301600008", "start_date": "2025-07-01", "end_date": "2025-07-31"},
            {"device_no": "TW24011700700016", "start_date": "2025-07-01", "end_date": "2025-07-31"}
        ]
        
        # 写入临时CSV文件 (UTF-8编码)
        with open('temp_devices.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["device_no", "start_date", "end_date"])
            writer.writeheader()
            writer.writerows(test_devices)
        
        try:
            # 读取设备信息
            devices = self.file_handler.read_devices_from_csv('temp_devices.csv')
            
            # 验证结果
            self.assertIsInstance(devices, list)
            self.assertEqual(len(devices), 2)
            
            first_device = devices[0]
            self.assertIn('device_no', first_device)
            self.assertIn('start_date', first_device)
            self.assertIn('end_date', first_device)
            
        finally:
            # 清理临时文件
            if os.path.exists('temp_devices.csv'):
                os.remove('temp_devices.csv')
        
        print("读取设备信息CSV文件功能测试通过")

    def test_excel_generation(self):
        """测试Excel文件生成功能"""
        print("\n开始测试Excel文件生成...")
        
        # 模拟数据
        test_data = [
            (date(2024, 1, 1), 80.0),
            (date(2024, 1, 2), 75.0),
            (date(2024, 1, 3), 70.0)
        ]
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 3)
        
        # 生成Excel文件
        output_dir = 'test_output'
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "test_excel_generation.xlsx")
        
        try:
            self.excel_handler.generate_excel_with_chart(
                test_data,
                output_file,
                "TW24011700700016",
                start_date,
                end_date
            )
            
            # 验证文件存在
            self.assertTrue(os.path.exists(output_file), f"Excel文件未生成: {output_file}")
            print(f"Excel文件已生成: {output_file}")
            
            # 验证Excel内容
            wb = load_workbook(output_file)
            ws = wb.active
            
            # 检查标题
            title_cell = ws['A1']
            self.assertIn("TW24011700700016每日库存余量变化趋势", title_cell.value)
            
            # 检查表头
            self.assertEqual(ws['A2'].value, "日期")
            self.assertEqual(ws['B2'].value, "库存百分比")
            
            # 验证数据行数（包括补全的数据）
            # 由于数据补全功能，应该有完整的日期范围数据
            expected_rows = (end_date - start_date).days + 1 + 2  # +2 for title and header rows
            actual_rows = ws.max_row
            self.assertEqual(actual_rows, expected_rows)
            
            print("Excel内容验证通过")
            
            # 验证图表是否存在
            self.assertTrue(len(ws._charts) > 0, "图表未添加到工作表")
            chart = ws._charts[0]
            # 获取图表标题文本
            chart_title = chart.title.tx.rich.p[0].r[0].t if chart.title and chart.title.tx and chart.title.tx.rich and chart.title.tx.rich.p and chart.title.tx.rich.p[0].r else None
            self.assertEqual(chart_title, "每日库存余量变化趋势")
            print("图表已成功添加")
            
        except Exception as e:
            print(f"Excel生成测试失败: {e}")
            raise
        finally:
            # 清理测试文件
            if os.path.exists(output_file):
                os.remove(output_file)

    def test_inventory_value_validation(self):
        """测试库存值验证功能"""
        print("\n开始测试库存值验证...")
        
        # 测试有效值
        valid_values = [0, 50, 100, 150, 1000]
        for value in valid_values:
            result = self.excel_handler._validate_inventory_value(value)
            self.assertEqual(result, value)
            print(f"验证通过 - 有效值: {value}")
        
        # 测试无效值
        invalid_values = [-1, -10, -100]
        for value in invalid_values:
            with self.assertRaises(ValueError, msg=f"值应为无效: {value}"):
                self.excel_handler._validate_inventory_value(value)
            print(f"验证通过 - 无效值正确抛出异常: {value}")

    def test_empty_data_handling(self):
        """测试空数据处理功能"""
        print("\n开始测试空数据处理...")
        
        # 测试空数据列表
        empty_data = []
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 3)
        
        output_dir = 'test_output'
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "test_empty_data.xlsx")
        
        # 空数据不会引发异常，而是会生成默认数据图表
        try:
            self.excel_handler.generate_excel_with_chart(
                empty_data,
                output_file,
                "TW24011700700016",
                start_date,
                end_date
            )
            
            # 验证文件存在
            self.assertTrue(os.path.exists(output_file), f"Excel文件未生成: {output_file}")
            print(f"空数据Excel文件已生成: {output_file}")
            
        except Exception as e:
            print(f"空数据处理测试失败: {e}")
            raise
        finally:
            # 清理测试文件
            if os.path.exists(output_file):
                os.remove(output_file)

    def test_date_validation(self):
        """测试日期验证功能"""
        print("\n开始测试日期验证...")
        
        # 测试有效日期格式
        valid_dates = ["2025-07-01", "2025/7/1"]
        for date_str in valid_dates:
            result = self.data_validator.validate_date(date_str)
            self.assertTrue(result, f"有效日期应验证通过: {date_str}")
            print(f"日期验证通过: {date_str}")
        
        # 测试无效日期格式
        invalid_dates = ["2025.07.01", "07/01/2025", "20250701"]
        for date_str in invalid_dates:
            result = self.data_validator.validate_date(date_str)
            self.assertFalse(result, f"无效日期应验证失败: {date_str}")
            print(f"日期验证失败（预期）: {date_str}")

    def test_date_parsing(self):
        """测试日期解析功能"""
        print("\n开始测试日期解析...")
        
        # 测试可解析的日期格式
        date_tests = [
            ("2025-07-01", date(2025, 7, 1)),
            ("2025/7/1", date(2025, 7, 1))
        ]
        
        for date_str, expected_date in date_tests:
            parsed_date = self.data_validator.parse_date(date_str)
            self.assertEqual(parsed_date, expected_date, f"日期解析不正确: {date_str}")
            print(f"日期解析正确: {date_str} -> {parsed_date}")
        
        # 测试不可解析的日期格式
        invalid_dates = ["2025.07.01", "07/01/2025", "invalid_date"]
        for date_str in invalid_dates:
            with self.assertRaises(ValueError, msg=f"应抛出ValueError异常: {date_str}"):
                self.data_validator.parse_date(date_str)
            print(f"日期解析失败（预期）: {date_str}")

    def test_generate_query_for_device(self):
        """测试为设备生成查询语句功能"""
        print("\n开始测试生成设备查询语句...")
        
        # 测试查询语句生成
        inventory_query_template = "SELECT * FROM table WHERE device_id = {device_id} AND date >= '{start_date}' AND date < '{end_condition}'"
        device_id = 12345
        start_date = date(2025, 7, 1)
        end_date = date(2025, 7, 31)
        
        query = self.config_handler.generate_query_for_device(
            inventory_query_template, device_id, start_date, end_date
        )
        
        # 验证查询语句包含必要的参数
        self.assertIn(str(device_id), query)
        self.assertIn(start_date.strftime('%Y-%m-%d'), query)
        self.assertIn("2025-08-01", query)  # 下月第一天作为结束条件
        print(f"查询语句生成正确: {query}")


def create_test_suite():
    """创建测试套件"""
    suite = unittest.TestSuite()
    
    # 添加主测试类中的所有测试方法
    test_cases = [
        TestZRDailyReport
    ]
    
    # 如果对账单处理模块测试可用，则添加到测试套件中
    if STATEMENT_HANDLER_AVAILABLE:
        test_cases.append(TestStatementHandler)
    
    for test_case in test_cases:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_case)
        suite.addTests(tests)
    
    return suite


if __name__ == '__main__':
    # 运行测试套件
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print("\n" + "="*50)
    print("测试结果摘要:")
    print(f"运行测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.2f}%" if result.testsRun > 0 else "无测试运行")
    print("="*50)