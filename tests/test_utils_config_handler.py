import json
import os
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import Mock, patch

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
                "database": "test_db",
            },
            "sql_templates": {
                "device_id_query": "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s",
                "inventory_query": "SELECT * FROM oil.t_order WHERE device_id = {device_id}",
                "customer_query": "SELECT customer_name FROM oil.t_customer WHERE id = %s",
            },
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
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
        )
        self.assertEqual(default_handler.config_dir, expected_path)

    def test_init_with_custom_config_dir(self):
        """测试使用自定义配置目录初始化"""
        custom_handler = ConfigHandler("/custom/config/path")
        self.assertEqual(custom_handler.config_dir, "/custom/config/path")

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
                "database": "test_db",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            config_file_path = f.name

        try:
            with self.assertRaises(json.JSONDecodeError):
                self.config_handler.load_plain_config(config_file_path)
        finally:
            os.unlink(config_file_path)

if __name__ == "__main__":
    unittest.main()