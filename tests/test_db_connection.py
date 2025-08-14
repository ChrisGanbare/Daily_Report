import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到sys.path，确保能正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 使用相对导入
from .base_test import BaseTestCase

# 尝试导入数据库模块
try:
    from src.core.db_handler import DatabaseHandler, USE_PYMYSQL
    DATABASE_HANDLER_AVAILABLE = True
except ImportError as e:
    DATABASE_HANDLER_AVAILABLE = False
    USE_PYMYSQL = False
    print(f"警告：无法导入数据库处理模块: {e}")


class TestDBConnection(BaseTestCase):
    """数据库连接功能测试"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.db_config = {
            'host': '8.139.83.130',
            'port': 3306,
            'user': 'query_zr',
            'password': 'ZRYLPass220609!',
            'database': 'oil'
        }

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    def test_database_handler_initialization(self):
        """测试数据库处理器初始化"""
        db_handler = DatabaseHandler(self.db_config)
        self.assertIsInstance(db_handler, DatabaseHandler)
        self.assertEqual(db_handler.db_config, self.db_config)

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    @patch('src.core.db_handler.pooling.MySQLConnectionPool')
    @patch('src.core.db_handler.mysql.connector.connect')
    def test_database_connection_success(self, mock_connect, mock_pool):
        """测试数据库连接成功"""
        # 模拟连接对象
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        # 模拟连接池
        if not USE_PYMYSQL:
            mock_pool_instance = MagicMock()
            mock_pool_instance.get_connection.return_value = mock_connection
            mock_pool.return_value = mock_pool_instance
        
        # 创建数据库处理器并尝试连接
        db_handler = DatabaseHandler(self.db_config)
        connection = db_handler.connect()
        
        # 验证连接方法被正确调用
        if not USE_PYMYSQL:
            # mysql-connector-python 方式使用连接池
            mock_pool.assert_called_once()
            mock_pool_instance.get_connection.assert_called_once()
        else:
            # PyMySQL 方式直接连接
            pymsql_config = self.db_config.copy()
            if 'pool_reset_session' in pymsql_config:
                del pymsql_config['pool_reset_session']
            mock_connect.assert_called_once_with(**pymsql_config)
            
        self.assertEqual(connection, mock_connection)

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    @patch('src.core.db_handler.pooling.MySQLConnectionPool')
    @patch('src.core.db_handler.mysql.connector.connect')
    def test_database_connection_failure(self, mock_connect, mock_pool):
        """测试数据库连接失败"""
        # 模拟连接异常
        if not USE_PYMYSQL:
            mock_pool.side_effect = Exception("连接池创建失败")
        else:
            mock_connect.side_effect = Exception("连接失败")
        
        # 创建数据库处理器并尝试连接
        db_handler = DatabaseHandler(self.db_config)
        
        # 验证连接失败时抛出异常
        with self.assertRaises(Exception):
            db_handler.connect()

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    @patch('src.core.db_handler.pooling.MySQLConnectionPool')
    @patch('src.core.db_handler.mysql.connector.connect')
    def test_get_device_and_customer_info_success(self, mock_connect, mock_pool):
        """测试获取设备和客户信息成功"""
        # 模拟连接和游标
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        # 模拟查询结果
        mock_cursor.fetchone.return_value = (1, 100)
        
        # 模拟连接池
        if not USE_PYMYSQL:
            mock_pool_instance = MagicMock()
            mock_pool_instance.get_connection.return_value = mock_connection
            mock_pool.return_value = mock_pool_instance
        
        # 创建数据库处理器并连接
        db_handler = DatabaseHandler(self.db_config)
        db_handler.connect()
        
        # 调用方法
        result = db_handler.get_device_and_customer_info("TEST001", "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s")
        
        # 验证结果
        self.assertEqual(result, (1, 100))
        mock_cursor.execute.assert_called_once_with(
            "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s", 
            ("TEST001",)
        )

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    @patch('src.core.db_handler.pooling.MySQLConnectionPool')
    @patch('src.core.db_handler.mysql.connector.connect')
    def test_get_customer_name_success(self, mock_connect, mock_pool):
        """测试获取客户名称成功"""
        # 模拟连接和游标
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_second_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.side_effect = [mock_cursor, mock_second_cursor]
        
        # 模拟查询结果
        mock_cursor.fetchone.return_value = (100,)  # 客户ID
        mock_second_cursor.fetchone.return_value = ("测试客户",)  # 客户名称
        
        # 模拟连接池
        if not USE_PYMYSQL:
            mock_pool_instance = MagicMock()
            mock_pool_instance.get_connection.return_value = mock_connection
            mock_pool.return_value = mock_pool_instance
        
        # 创建数据库处理器并连接
        db_handler = DatabaseHandler(self.db_config)
        db_handler.connect()
        
        # 调用方法
        result = db_handler.get_customer_name_by_device_code(1, "SELECT customer_name FROM oil.t_customer WHERE id = %s")
        
        # 验证结果
        self.assertEqual(result, "测试客户")
        mock_second_cursor.execute.assert_called_once_with(
            "SELECT customer_name FROM oil.t_customer WHERE id = %s", 
            (100,)  # 注意这里应该是客户ID而不是设备ID
        )

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    def test_driver_selection(self):
        """测试数据库驱动选择"""
        # 检查是否正确选择了数据库驱动
        if USE_PYMYSQL:
            print("当前使用 PyMySQL 作为数据库驱动")
        else:
            print("当前使用 mysql-connector-python 作为数据库驱动")
        
        # 验证驱动选择逻辑正常工作
        self.assertIsInstance(USE_PYMYSQL, bool)

    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    @patch('src.core.db_handler.pooling.MySQLConnectionPool')
    @patch('src.core.db_handler.mysql.connector.connect')
    def test_connection_pool_functionality(self, mock_connect, mock_pool):
        """测试连接池功能（仅适用于mysql-connector-python）"""
        # 模拟连接对象
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        # 模拟连接池（仅适用于mysql-connector-python）
        if not USE_PYMYSQL:
            mock_pool_instance = MagicMock()
            mock_pool_instance.get_connection.return_value = mock_connection
            mock_pool.return_value = mock_pool_instance
        
        # 创建数据库处理器并尝试连接
        db_handler = DatabaseHandler(self.db_config)
        db_handler.connect()
        
        if not USE_PYMYSQL:
            # 仅在使用mysql-connector-python时检查连接池
            self.assertIsNotNone(db_handler.connection_pool)
        else:
            # PyMySQL不支持连接池
            self.assertIsNone(db_handler.connection_pool)


if __name__ == '__main__':
    unittest.main()