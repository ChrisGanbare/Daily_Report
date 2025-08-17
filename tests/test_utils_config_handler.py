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
        """测试使用默认配置目录初始化"""
        default_handler = ConfigHandler()
        # 检查是否正确设置了默认配置目录
        self.assertIn("config", default_handler.config_dir)

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
        """测试加载不存在的加密配置文件"""
        non_existent_file = os.path.join(self.test_output_dir, "non_existent.json")
        with self.assertRaises(FileNotFoundError) as context:
            self.config_handler.load_encrypted_config(non_existent_file)
        self.assertIn("加密配置文件不存在", str(context.exception))

    def test_load_encrypted_config_key_file_not_found(self):
        """测试密钥文件不存在的情况"""
        # 创建一个空的加密配置文件
        encrypted_file = os.path.join(self.test_output_dir, "query_config_encrypted.json")
        with open(encrypted_file, "wb") as f:
            f.write(b"fake encrypted data")
        
        with self.assertRaises(FileNotFoundError) as context:
            self.config_handler.load_encrypted_config(encrypted_file)
        self.assertIn("密钥文件不存在", str(context.exception))

    @patch("src.utils.config_handler.Fernet")
    def test_load_encrypted_config_decryption_failure(self, mock_fernet):
        """测试解密失败的情况"""
        # 创建临时密钥文件
        key_file = os.path.join(self.test_output_dir, ".env")
        with open(key_file, "wb") as f:
            f.write(b'test_key')
        
        # 创建加密配置文件
        encrypted_file = os.path.join(self.test_output_dir, "query_config_encrypted.json")
        with open(encrypted_file, "wb") as f:
            f.write(b"fake encrypted data")
        
        # 模拟解密失败
        mock_cipher = mock_fernet.return_value
        mock_cipher.decrypt.side_effect = Exception("解密失败")
        
        with self.assertRaises(Exception) as context:
            self.config_handler.load_encrypted_config(encrypted_file)
        self.assertIn("解密配置文件失败", str(context.exception))

    def test_load_plain_config_success(self):
        """测试成功加载明文配置文件"""
        # 创建明文配置文件
        plain_file = os.path.join(self.test_output_dir, "query_config.json")
        with open(plain_file, "w", encoding="utf-8") as f:
            json.dump(self.sample_config, f, ensure_ascii=False, indent=2)
        
        # 测试加载明文配置
        loaded_config = self.config_handler.load_plain_config(plain_file)
        self.assertEqual(loaded_config["db_config"]["host"], "localhost")
        self.assertEqual(loaded_config["db_config"]["user"], "test_user")
        self.assertIn("sql_templates", loaded_config)

    def test_load_plain_config_file_not_found(self):
        """测试加载不存在的明文配置文件"""
        non_existent_file = os.path.join(self.test_output_dir, "non_existent.json")
        with self.assertRaises(FileNotFoundError) as context:
            self.config_handler.load_plain_config(non_existent_file)
        self.assertIn("明文配置文件不存在", str(context.exception))

    def test_load_plain_config_invalid_json(self):
        """测试加载无效JSON格式的明文配置文件"""
        # 创建无效JSON文件
        plain_file = os.path.join(self.test_output_dir, "invalid_config.json")
        with open(plain_file, "w", encoding="utf-8") as f:
            f.write("invalid json content")
        
        with self.assertRaises(Exception):
            self.config_handler.load_plain_config(plain_file)


if __name__ == "__main__":
    unittest.main()