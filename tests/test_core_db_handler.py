import os
import sys
import tempfile
import unittest
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.db_handler import DatabaseHandler
from tests.base_test import BaseTestCase

# 尝试导入数据库模块
try:
    from src.core.db_handler import DatabaseHandler, USE_PYMYSQL
    DATABASE_HANDLER_AVAILABLE = True
except ImportError as e:
    DATABASE_HANDLER_AVAILABLE = False
    USE_PYMYSQL = False
    print(f"警告：无法导入数据库处理模块: {e}")


class TestCoreDbHandler(BaseTestCase):
    """
    core.db_handler 模块的单元测试
    """
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.db_config = {
            'host': 'localhost',
            'user': 'test_user',
            'password': 'test_password',
            'database': 'test_db'
        }
        self.db_handler = DatabaseHandler(self.db_config)
        
    def test_databasehandler_initialization(self):
        """
        测试 DatabaseHandler 类的初始化
        """
        self.assertEqual(self.db_handler.db_config, self.db_config)
        self.assertIsNone(self.db_handler.connection)
        self.assertIsNone(self.db_handler.connection_pool)

    @patch('src.core.db_handler.mysql.connector.connect')
    def test_databasehandler_connect_with_pymysql(self, mock_connect):
        """
        测试 DatabaseHandler.connect 方法使用PyMySQL连接
        """
        with patch('src.core.db_handler.USE_PYMYSQL', True):
            mock_connection = Mock()
            mock_connect.return_value = mock_connection
            
            # 创建一个不包含'pool_reset_session'键的配置副本
            expected_config = self.db_config.copy()
            
            connection = self.db_handler.connect()
            self.assertEqual(connection, mock_connection)
            mock_connect.assert_called_once_with(**expected_config)

    @patch('src.core.db_handler.pooling.MySQLConnectionPool')
    def test_databasehandler_connect_with_mysql_connector(self, mock_pool_class):
        """
        测试 DatabaseHandler.connect 方法使用mysql-connector-python连接
        """
        with patch('src.core.db_handler.USE_PYMYSQL', False):
            mock_pool = Mock()
            mock_connection = Mock()
            mock_pool.get_connection.return_value = mock_connection
            mock_pool_class.return_value = mock_pool
            connection = self.db_handler.connect()
            self.assertEqual(connection, mock_connection)
            mock_pool.get_connection.assert_called_once()

    def test_databasehandler_disconnect_with_no_connection(self):
        """
        测试 DatabaseHandler.disconnect 方法在没有连接时的行为
        """
        self.db_handler.connection = None
        # 不应抛出异常
        self.db_handler.disconnect()

    @patch('src.core.db_handler.mysql.connector')
    def test_databasehandler_disconnect_with_mysql_connector_connection(self, mock_mysql):
        """
        测试 DatabaseHandler.disconnect 方法关闭mysql-connector连接
        """
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        self.db_handler.connection = mock_connection
        
        self.db_handler.disconnect()
        mock_connection.close.assert_called_once()

    @patch('src.core.db_handler.mysql.connector')
    def test_databasehandler_disconnect_with_pymysql_connection(self, mock_mysql):
        """
        测试 DatabaseHandler.disconnect 方法关闭PyMySQL连接
        """
        mock_connection = Mock()
        mock_connection.open = True
        mock_connection.is_connected = None  # PyMySQL没有is_connected方法
        self.db_handler.connection = mock_connection
        
        self.db_handler.disconnect()
        mock_connection.close.assert_called_once()

    @patch('src.core.db_handler.mysql.connector')
    def test_databasehandler_disconnect_with_closed_connection(self, mock_mysql):
        """
        测试 DatabaseHandler.disconnect 方法处理已关闭的连接
        """
        mock_connection = Mock()
        mock_connection.is_connected.return_value = False
        self.db_handler.connection = mock_connection
        
        self.db_handler.disconnect()
        # close方法不应被调用
        mock_connection.close.assert_not_called()

    @patch('src.core.db_handler.mysql.connector')
    def test_databasehandler_disconnect_with_exception(self, mock_mysql):
        """
        测试 DatabaseHandler.disconnect 方法处理关闭连接时的异常
        """
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connection.close.side_effect = Exception("关闭连接时出错")
        self.db_handler.connection = mock_connection
        
        # 不应抛出异常
        self.db_handler.disconnect()

    def test_databasehandler_get_device_and_customer_info(self):
        """
        测试 DatabaseHandler.get_device_and_customer_info 方法
        """
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1, 100)
        self.db_handler.connection = mock_connection
        
        result = self.db_handler.get_device_and_customer_info("DEV001", "SELECT id, customer_id FROM device WHERE code = %s")
        self.assertEqual(result, (1, 100))
        mock_cursor.execute.assert_called_once_with("SELECT id, customer_id FROM device WHERE code = %s", ("DEV001",))

    def test_databasehandler_get_device_and_customer_info_not_found(self):
        """
        测试 DatabaseHandler.get_device_and_customer_info 方法未找到设备时的行为
        """
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        self.db_handler.connection = mock_connection
        
        result = self.db_handler.get_device_and_customer_info("DEV001", "SELECT id, customer_id FROM device WHERE code = %s")
        self.assertIsNone(result)

    @patch('src.core.db_handler.mysql.connector')
    def test_databasehandler_get_customer_name_by_device_code(self, mock_mysql):
        """
        测试 DatabaseHandler.get_customer_name_by_device_code 方法
        """
        # 模拟设备信息查询结果
        mock_device_cursor = Mock()
        mock_device_cursor.fetchone.return_value = (1, 100)  # 设备ID, 客户ID
        
        # 模拟客户名称查询结果
        mock_customer_cursor = Mock()
        mock_customer_cursor.fetchone.return_value = ("测试客户",)
        
        # 模拟连接和游标
        mock_connection = Mock()
        mock_connection.cursor.side_effect = [mock_device_cursor, mock_customer_cursor]
        self.db_handler.connection = mock_connection
        
        customer_name = self.db_handler.get_customer_name_by_device_code("DEV001")
        
        self.assertEqual(customer_name, "测试客户")
        self.assertEqual(mock_connection.cursor.call_count, 2)

    @patch('src.core.db_handler.mysql.connector')
    def test_databasehandler_get_customer_name_by_device_code_not_found(self, mock_mysql):
        """
        测试 DatabaseHandler.get_customer_name_by_device_code 方法处理未找到客户的情况
        """
        # 模拟设备信息查询结果为空（设备不存在）
        mock_device_cursor = Mock()
        mock_device_cursor.fetchone.return_value = None
        
        # 模拟连接和游标
        mock_connection = Mock()
        mock_connection.cursor.side_effect = [mock_device_cursor]
        self.db_handler.connection = mock_connection
        
        customer_name = self.db_handler.get_customer_name_by_device_code("DEV001")
        
        self.assertEqual(customer_name, "未知客户")

    @patch('src.core.db_handler.mysql.connector')
    def test_databasehandler_fetch_inventory_data(self, mock_mysql):
        """
        测试 DatabaseHandler.fetch_inventory_data 方法
        """
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        self.db_handler.connection = mock_connection
        
        # 模拟查询结果
        mock_cursor.fetchall.return_value = [
            (date(2025, 7, 1), 95.5),
            (date(2025, 7, 2), 93.2)
        ]
        
        inventory_data = self.db_handler.fetch_inventory_data(
            1, "SELECT * FROM oil.t_order WHERE device_id = %s"
        )
        
        self.assertIsNotNone(inventory_data)
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_cursor.close.assert_called_once()

    @patch('src.core.db_handler.mysql.connector')
    def test_databasehandler_fetch_inventory_data_empty_result(self, mock_mysql):
        """
        测试 DatabaseHandler.fetch_inventory_data 方法处理空结果
        """
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        self.db_handler.connection = mock_connection
        
        # 模拟查询结果为空
        mock_cursor.fetchall.return_value = []
        
        inventory_data = self.db_handler.fetch_inventory_data(
            1, "SELECT * FROM oil.t_order WHERE device_id = %s"
        )
        
        self.assertEqual(inventory_data, ([], [], []))
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_cursor.close.assert_called_once()

    @patch('src.core.db_handler.pooling.MySQLConnectionPool')
    def test_databasehandler_connect_exception_handling(self, mock_pool_class):
        """
        测试 DatabaseHandler.connect 方法处理连接异常
        """
        mock_pool_class.side_effect = Exception("连接失败")

        with self.assertRaises(Exception) as context:
            self.db_handler.connect()
            
        self.assertIn("连接失败", str(context.exception))

    # 以下是从test_db_connection.py合并过来的测试用例
    @unittest.skipIf(not DATABASE_HANDLER_AVAILABLE, "数据库处理模块不可用")
    def test_database_handler_initialization_with_real_config(self):
        """测试数据库处理器初始化（使用真实配置）"""
        db_config = {
            'host': '8.139.83.130',
            'port': 3306,
            'user': 'query_zr',
            'password': 'ZRYLPass220609!',
            'database': 'oil'
        }
        db_handler = DatabaseHandler(db_config)
        self.assertIsInstance(db_handler, DatabaseHandler)
        self.assertEqual(db_handler.db_config, db_config)

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
        db_config = {
            'host': '8.139.83.130',
            'port': 3306,
            'user': 'query_zr',
            'password': 'ZRYLPass220609!',
            'database': 'oil'
        }
        db_handler = DatabaseHandler(db_config)
        connection = db_handler.connect()
        
        # 验证连接方法被正确调用
        if not USE_PYMYSQL:
            # mysql-connector-python 方式使用连接池
            mock_pool.assert_called_once()
            mock_pool_instance.get_connection.assert_called_once()
        else:
            # PyMySQL 方式直接连接
            pymsql_config = db_config.copy()
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
        db_config = {
            'host': '8.139.83.130',
            'port': 3306,
            'user': 'query_zr',
            'password': 'ZRYLPass220609!',
            'database': 'oil'
        }
        db_handler = DatabaseHandler(db_config)
        
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
        db_config = {
            'host': '8.139.83.130',
            'port': 3306,
            'user': 'query_zr',
            'password': 'ZRYLPass220609!',
            'database': 'oil'
        }
        db_handler = DatabaseHandler(db_config)
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
        mock_device_cursor = MagicMock()
        mock_customer_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.side_effect = [mock_device_cursor, mock_customer_cursor]

        # 模拟查询结果
        mock_device_cursor.fetchone.return_value = (1, 100)  # 设备ID, 客户ID
        mock_customer_cursor.fetchone.return_value = ("测试客户",)  # 客户名称

        # 模拟连接池
        if not USE_PYMYSQL:
            mock_pool_instance = MagicMock()
            mock_pool_instance.get_connection.return_value = mock_connection
            mock_pool.return_value = mock_pool_instance

        # 创建数据库处理器并连接
        db_config = {
            'host': '8.139.83.130',
            'port': 3306,
            'user': 'query_zr',
            'password': 'ZRYLPass220609!',
            'database': 'oil'
        }
        db_handler = DatabaseHandler(db_config)
        db_handler.connect()

        # 调用方法
        result = db_handler.get_customer_name_by_device_code("DEV001")

        # 验证结果
        self.assertEqual(result, "测试客户")
        mock_customer_cursor.execute.assert_called_once_with(
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
        db_config = {
            'host': '8.139.83.130',
            'port': 3306,
            'user': 'query_zr',
            'password': 'ZRYLPass220609!',
            'database': 'oil'
        }
        db_handler = DatabaseHandler(db_config)
        db_handler.connect()
        
        if not USE_PYMYSQL:
            # 仅在使用mysql-connector-python时检查连接池
            self.assertIsNotNone(db_handler.connection_pool)
        else:
            # PyMySQL不支持连接池
            self.assertIsNone(db_handler.connection_pool)


if __name__ == "__main__":
    unittest.main()