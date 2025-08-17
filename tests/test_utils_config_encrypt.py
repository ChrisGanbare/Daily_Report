import os
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import Mock, patch

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.config_encrypt import encrypt_config, decrypt_config
from tests.base_test import BaseTestCase


class TestUtilsConfigEncrypt(BaseTestCase):
    """
    utils.config_encrypt 模块的单元测试
    """
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.test_data = '{"database": {"host": "localhost", "user": "test"}}'
        
    def test_encrypt_config_and_decrypt_config(self):
        """
        测试 encrypt_config 和 decrypt_config 函数
        """
        # 加密数据
        encrypted_data = encrypt_config(self.test_data)
        
        # 验证加密后的数据不是原始数据
        self.assertNotEqual(encrypted_data, self.test_data)
        self.assertIsInstance(encrypted_data, str)
        
        # 解密数据
        decrypted_data = decrypt_config(encrypted_data)
        
        # 验证解密后的数据与原始数据相同
        self.assertEqual(decrypted_data, self.test_data)

    def test_encrypt_config_with_empty_string(self):
        """
        测试 encrypt_config 函数处理空字符串
        """
        encrypted_data = encrypt_config("")
        decrypted_data = decrypt_config(encrypted_data)
        self.assertEqual(decrypted_data, "")

    def test_encrypt_config_with_none(self):
        """
        测试 encrypt_config 函数处理None值
        """
        with self.assertRaises(Exception):
            encrypt_config(None)


if __name__ == "__main__":
    unittest.main()