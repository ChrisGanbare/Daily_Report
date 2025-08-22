import os
import sys
import tempfile
import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch

import mysql.connector

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.db_handler import DatabaseHandler
from tests.base_test import BaseTestCase

# 导入数据库模块
try:
    from src.core.db_handler import DatabaseHandler

    DATABASE_HANDLER_AVAILABLE = True
except ImportError as e:
    DATABASE_HANDLER_AVAILABLE = False
    print(f"警告：无法导入数据库处理模块: {e}")


class TestCoreDbHandler(BaseTestCase):
    """
    core.db_handler 模块的单元测试
    """

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.db_config = {
            "host": "localhost",
            "user": "test_user",
            "password": "test_password",
            "database": "test_db",
        }
        self.db_handler = DatabaseHandler(self.db_config)

    def test_databasehandler_initialization(self):
        """
        测试 DatabaseHandler 类的初始化
        """
        self.assertEqual(self.db_handler.db_config, self.db_config)
        self.assertIsNone(self.db_handler.connection)
        self.assertIsNone(self.db_handler.connection_pool)

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    @patch("src.core.db_handler.pooling.MySQLConnectionPool")
    @patch("src.core.db_handler.mysql.connector.connect")
    def test_database_connection_success(self, mock_connect, mock_pool):
        """测试数据库连接成功"""
        # 模拟连接对象
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        # 模拟连接池
        mock_pool_instance = MagicMock()
        mock_pool_instance.get_connection.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance

        # 创建数据库处理器并尝试连接
        db_config = {
            "host": "8.139.83.130",
            "port": 3306,
            "user": "query_zr",
            "password": "ZRYLPass220609!",
            "database": "oil",
        }
        db_handler = DatabaseHandler(db_config)
        connection = db_handler.connect()

        # 验证连接方法被正确调用
        mock_pool.assert_called_once()
        mock_pool_instance.get_connection.assert_called_once()
        self.assertEqual(connection, mock_connection)

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    @patch("src.core.db_handler.pooling.MySQLConnectionPool")
    @patch("src.core.db_handler.mysql.connector.connect")
    def test_database_connection_failure(self, mock_connect, mock_pool):
        """测试数据库连接失败"""
        # 模拟连接异常
        mock_connect.side_effect = mysql.connector.Error("连接失败")
        mock_pool.side_effect = mysql.connector.Error("连接池创建失败")

        # 创建数据库处理器并尝试连接
        db_config = {
            "host": "8.139.83.130",
            "port": 3306,
            "user": "query_zr",
            "password": "ZRYLPass220609!",
            "database": "oil",
        }
        db_handler = DatabaseHandler(db_config)
        with self.assertRaises(Exception):
            db_handler.connect()

        # 验证连接方法被调用
        mock_pool.assert_called_once()

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    @patch('src.core.db_handler.pooling.MySQLConnectionPool')
    @patch('src.core.db_handler.mysql.connector.connect')
    def test_get_latest_device_id_and_customer_id_success(self, mock_connect, mock_pool):
        """测试获取设备和客户信息成功"""
        # 模拟连接和游标
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # 模拟查询结果
        mock_cursor.fetchone.return_value = (1, 100)
        mock_cursor.fetchall.return_value = [(1, 100)]

        # 模拟连接池
        mock_pool_instance = MagicMock()
        mock_pool_instance.get_connection.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance

        # 创建数据库处理器并连接
        db_config = {
            "host": "8.139.83.130",
            "port": 3306,
            "user": "query_zr",
            "password": "ZRYLPass220609!",
            "database": "oil",
        }
        db_handler = DatabaseHandler(db_config)
        db_handler.connect()

        # 调用方法
        result = db_handler.get_latest_device_id_and_customer_id(
            "TEST001", "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s"
        )

        # 验证结果
        self.assertEqual(result, (1, 100))
        mock_cursor.execute.assert_called_once_with(
            "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s ORDER BY create_time DESC, id DESC",
            ("TEST001",),
        )

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    @patch("src.core.db_handler.pooling.MySQLConnectionPool")
    @patch("src.core.db_handler.mysql.connector.connect")
    def test_get_customer_name_success(self, mock_connect, mock_pool):
        """测试获取客户名称成功"""
        # 模拟连接和游标
        mock_connection = MagicMock()
        mock_device_cursor = MagicMock()
        mock_customer_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.side_effect = [mock_device_cursor, mock_customer_cursor]

        # 模拟查询结果
        mock_device_cursor.fetchone.return_value = None
        mock_device_cursor.fetchall.return_value = [(1, 100)]  # 设备ID, 客户ID
        mock_customer_cursor.fetchone.return_value = ("测试客户",)  # 客户名称

        # 模拟连接池
        mock_pool_instance = MagicMock()
        mock_pool_instance.get_connection.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance

        # 创建数据库处理器并连接
        db_config = {
            "host": "8.139.83.130",
            "port": 3306,
            "user": "query_zr",
            "password": "ZRYLPass220609!",
            "database": "oil",
        }
        db_handler = DatabaseHandler(db_config)
        db_handler.connect()

        # 调用方法
        result = db_handler.get_customer_name_by_device_code("DEV001")

        # 验证结果
        self.assertEqual(result, "测试客户")
        mock_customer_cursor.execute.assert_called_once_with(
            "SELECT customer_name FROM oil.t_customer WHERE id = %s",
            (100,),  # 注意这里应该是客户ID而不是设备ID
        )

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    def test_driver_selection(self):
        """测试数据库驱动选择"""
        # 检查是否正确选择了数据库驱动
        print("当前使用 mysql-connector-python 作为数据库驱动")

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    @patch("src.core.db_handler.pooling.MySQLConnectionPool")
    @patch("src.core.db_handler.mysql.connector.connect")
    def test_connection_pool_functionality(self, mock_connect, mock_pool):
        """测试连接池功能（仅适用于mysql-connector-python）"""
        # 模拟连接对象
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        # 模拟连接池（仅适用于mysql-connector-python）
        mock_pool_instance = MagicMock()
        mock_pool_instance.get_connection.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance

        # 创建数据库处理器并尝试连接
        db_config = {
            "host": "8.139.83.130",
            "port": 3306,
            "user": "query_zr",
            "password": "ZRYLPass220609!",
            "database": "oil",
        }
        db_handler = DatabaseHandler(db_config)
        db_handler.connect()

        # 检查连接池
        self.assertIsNotNone(db_handler.connection_pool)

    @patch('ZR_Daily_Report.load_config')
    @patch('ZR_Daily_Report.InventoryData')
    @patch('ZR_Daily_Report.ExcelWithChart')
    @patch('ZR_Daily_Report.CustomerStatementFromTemplate')
    @patch('ZR_Daily_Report.DatabaseHandler')
    def test_main_functionality(self, mock_db, mock_statement, mock_inventory, mock_excel, mock_config):
        """测试主功能"""
        mock_config.return_value = {
            "db_config": {
                "host": "8.139.83.130",
                "port": 3306,
                "user": "query_zr",
                "password": "ZRYLPass220609!",
                "database": "oil",
            },
            "device_code": "TEST001",
            "output_dir": "/tmp",
            "template_dir": "/tmp",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
        }
        mock_db_instance = mock_db.return_value
        mock_inventory_instance = mock_inventory.return_value
        mock_statement_instance = mock_statement.return_value
        mock_excel_instance = mock_excel.return_value

        mock_db_instance.get_latest_device_id_and_customer_id.return_value = (1, 100)
        mock_db_instance.get_customer_name_by_device_code.return_value = "测试客户"
        mock_db_instance.fetch_inventory_data.return_value = (
            [],
            [],
            []
        )

        # 模拟库存报告处理器
        mock_inventory_instance.generate_excel_with_chart.return_value = "inventory_report.xlsx"

        # 模拟客户报表处理器
        mock_statement_instance.generate_customer_statement_from_template.return_value = "customer_statement.xlsx"

        # 模拟Excel图表处理器
        mock_excel_instance.generate_excel_with_chart.return_value = "chart.xlsx"

        # 调用主函数
        ZR_Daily_Report.main()

if __name__ == "__main__":
    unittest.main()