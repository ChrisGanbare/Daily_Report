import os
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import Mock, patch
from cryptography.fernet import Fernet
import json

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.config_handler import ConfigHandler
from tests.base_test import BaseTestCase


class TestUtilsConfigHandler(BaseTestCase):
    """
    utils.config_handler 模块的单元测试
    """
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.config_handler = ConfigHandler(self.test_output_dir)
        
        # 示例配置数据
        self.sample_config = {
            "db_config": {
                "host": "localhost",
                "port": 3306,
                "user": "test_user",
                "password": "test_password",
                "database": "test_db"
            },
            "sql_templates": {
                "device_id_query": "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s",
                "inventory_query": "SELECT * FROM oil.t_order WHERE device_id = {device_id}",
                "customer_query": "SELECT customer_name FROM oil.t_customer WHERE id = %s"
            }
        }
        
    def test_confighandler_initialization(self):
        """
        测试 ConfigHandler 类的初始化
        """
        # ConfigHandler的__init__方法目前为空，只需确认能创建实例
        self.assertIsInstance(self.config_handler, ConfigHandler)

    # 以下是从test_config_handler.py合并过来的测试用例
    def test_init_with_default_config_dir(self):
        """
        测试使用默认配置目录初始化ConfigHandler
        """
        # 创建ConfigHandler实例而不传递参数
        default_handler = ConfigHandler()
        # 验证配置目录是否正确设置
        expected_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config"
        )
        self.assertEqual(default_handler.config_dir, expected_path)

    def test_init_with_custom_config_dir(self):
        """测试使用自定义配置目录初始化"""
        custom_handler = ConfigHandler("/custom/config/path")
        self.assertEqual(custom_handler.config_dir, "/custom/config/path")

    def test_create_and_load_encrypted_config(self):
        """测试创建和加载加密配置文件"""
        # 创建临时密钥文件
        key = Fernet.generate_key()
        key_file = os.path.join(self.test_output_dir, ".env")
        with open(key_file, "wb") as f:
            f.write(key)
        
        # 创建加密配置文件
        encrypted_file = os.path.join(self.test_output_dir, "query_config_encrypted.json")
        self.config_handler.create_encrypted_config(self.sample_config, encrypted_file)
        
        # 验证加密文件存在
        self.assertTrue(os.path.exists(encrypted_file))
        
        # 测试加载加密配置
        loaded_config = self.config_handler.load_encrypted_config(encrypted_file)
        self.assertEqual(loaded_config["db_config"]["host"], "localhost")
        self.assertEqual(loaded_config["db_config"]["user"], "test_user")
        self.assertIn("sql_templates", loaded_config)

    def test_load_encrypted_config_file_not_found(self):
        """
        测试 load_encrypted_config 方法处理配置文件不存在的情况
        """
        with self.assertRaises(FileNotFoundError):
            self.config_handler.load_encrypted_config("non_existent_config.json")

    @patch("src.utils.config_handler.os.path.exists")
    @patch("src.utils.config_handler.open")
    def test_load_encrypted_config_key_file_not_found(self, mock_open, mock_exists):
        """
        测试 load_encrypted_config 方法处理密钥文件不存在的情况
        """
        # 配置模拟返回值
        mock_exists.side_effect = lambda path: not path.endswith(".env")
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.read = Mock(return_value="{}")
        mock_open.return_value = mock_file
        
        with self.assertRaises(FileNotFoundError) as context:
            self.config_handler.load_encrypted_config()
            
        self.assertIn(".env", str(context.exception))

    @patch("src.utils.config_handler.os.path.exists")
    @patch("src.utils.config_handler.open")
    def test_decrypt_config_data_success(self, mock_open, mock_exists):
        """
        测试 decrypt_config_data 方法成功解密配置数据
        """
        # 配置模拟返回值
        mock_exists.return_value = True
        
        # 创建模拟文件对象，支持上下文管理器协议
        mock_key_file = Mock()
        mock_key_file.__enter__ = Mock(return_value=mock_key_file)
        mock_key_file.read = Mock(return_value=b"test_key")
        
        mock_config_file = Mock()
        mock_config_file.__enter__ = Mock(return_value=mock_config_file)
        mock_config_file.read = Mock(return_value=b"encrypted_data")
        
        mock_open.side_effect = [
            mock_key_file,
            mock_config_file
        ]
        
        # 模拟Fernet解密
        with patch("src.utils.config_handler.Fernet") as mock_fernet:
            mock_fernet_instance = Mock()
            mock_fernet_instance.decrypt.return_value = b'{"db_config": {"host": "localhost"}}'
            mock_fernet.return_value = mock_fernet_instance
            
            result = self.config_handler.load_encrypted_config()
            
            self.assertIsInstance(result, dict)
            self.assertIn("db_config", result)

    @patch("src.utils.config_handler.os.path.exists")
    @patch("src.utils.config_handler.open")
    def test_decrypt_config_data_invalid_json(self, mock_open, mock_exists):
        """
        测试 decrypt_config_data 方法处理无效JSON数据的情况
        """
        # 配置模拟返回值
        mock_exists.return_value = True
        
        # 创建模拟文件对象，支持上下文管理器协议
        mock_key_file = Mock()
        mock_key_file.__enter__ = Mock(return_value=mock_key_file)
        mock_key_file.read = Mock(return_value=b"test_key")
        
        mock_config_file = Mock()
        mock_config_file.__enter__ = Mock(return_value=mock_config_file)
        mock_config_file.read = Mock(return_value=b"encrypted_data")
        
        mock_open.side_effect = [
            mock_key_file,
            mock_config_file
        ]
        
        # 模拟Fernet解密返回无效JSON
        with patch("src.utils.config_handler.Fernet") as mock_fernet:
            mock_fernet_instance = Mock()
            mock_fernet_instance.decrypt.return_value = b'invalid json'
            mock_fernet.return_value = mock_fernet_instance
            
            with self.assertRaises(Exception):
                self.config_handler.load_encrypted_config()

    def test_load_plain_config_success(self):
        """
        测试 load_plain_config 方法成功加载明文配置
        """
        # 创建临时配置文件
        config_data = {
            "db_config": {
                "host": "localhost",
                "port": 3306,
                "user": "test_user",
                "password": "test_password",
                "database": "test_db"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file_path = f.name
            
        try:
            result = self.config_handler.load_plain_config(config_file_path)
            self.assertEqual(result, config_data)
        finally:
            os.unlink(config_file_path)

    def test_load_plain_config_file_not_found(self):
        """
        测试 load_plain_config 方法处理配置文件不存在的情况
        """
        with self.assertRaises(FileNotFoundError):
            self.config_handler.load_plain_config("non_existent_config.json")

    def test_load_plain_config_invalid_json(self):
        """
        测试 load_plain_config 方法处理无效JSON格式的情况
        """
        # 创建临时包含无效JSON的配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json")
            config_file_path = f.name
            
        try:
            with self.assertRaises(json.JSONDecodeError):
                self.config_handler.load_plain_config(config_file_path)
        finally:
            os.unlink(config_file_path)

    def test_decrypt_config_data_decryption_error(self):
        """
        测试 decrypt_config_data 方法处理解密错误的情况
        """
        # 配置模拟返回值
        with patch("src.utils.config_handler.os.path.exists") as mock_exists, \
             patch("src.utils.config_handler.open") as mock_open:
            mock_exists.return_value = True
            
            # 创建模拟文件对象，支持上下文管理器协议
            mock_key_file = Mock()
            mock_key_file.__enter__ = Mock(return_value=mock_key_file)
            mock_key_file.read = Mock(return_value=b"test_key")
            
            mock_config_file = Mock()
            mock_config_file.__enter__ = Mock(return_value=mock_config_file)
            mock_config_file.read = Mock(return_value=b"encrypted_data")
            
            mock_open.side_effect = [
                mock_key_file,
                mock_config_file
            ]
            
            # 模拟Fernet解密引发异常
            with patch("src.utils.config_handler.Fernet") as mock_fernet:
                mock_fernet_instance = Mock()
                mock_fernet_instance.decrypt.side_effect = Exception("解密失败")
                mock_fernet.return_value = mock_fernet_instance
                
                with self.assertRaises(Exception) as context:
                    self.config_handler.load_encrypted_config()
                    
                self.assertIn("解密失败", str(context.exception))

if __name__ == "__main__":
    unittest.main()