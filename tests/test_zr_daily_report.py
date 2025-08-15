import argparse
import csv
import json
import os
import sys
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

import mysql.connector
from openpyxl import load_workbook

# 添加项目根目录到sys.path，确保能正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 使用包导入简化导入路径
from src.core.db_handler import DatabaseHandler
from src.core.inventory_handler import InventoryReportGenerator
from src.core.file_handler import FileHandler
from src.utils import ConfigHandler, DataValidator
from ZR_Daily_Report import (
    generate_customer_statement,
    generate_inventory_reports,
    load_config,
)

# 添加当前目录到Python路径，以便导入新创建的测试模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from test_statement_handler import TestStatementHandler

    STATEMENT_HANDLER_AVAILABLE = True
except ImportError:
    STATEMENT_HANDLER_AVAILABLE = False
    print("警告：未找到对账单处理模块的测试文件")

from base_test import BaseTestCase


class TestZRDailyReport(BaseTestCase):
    """综合测试ZR Daily Report的所有功能"""

    def setUp(self):
        """测试前准备"""
        super().setUp()

    @patch("ZR_Daily_Report.load_config")
    def test_load_configuration_success(self, mock_load_config):
        """测试配置加载成功"""
        # 模拟配置数据（使用实际的配置结构）
        mock_config = {
            "db_config": {
                "host": "8.139.83.130",
                "port": 3306,
                "user": "query_zr",
                "password": "ZRYLPass220609!",
                "database": "oil",
            },
            "sql_templates": {
                "device_id_query": "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s ORDER BY create_time DESC LIMIT 1",
                "inventory_query": "SELECT a.id AS '订单序号', a.order_time AS '加注时间', a.oil_type_id AS '油品序号', b.oil_name AS '油品名称', a.water AS '水油比：水값', a.oil AS '水油比：油값', a.water_val AS '水加注', a.oil_val AS '油加注', a.avai_oil AS '原油剩余量', a.avai_oil / 1000 AS '原油剩余比例', a.oil_set_val AS '油加设量', a.is_settlement AS '是否结算：1=待结算 2=待生效 3=已结算', a.fill_mode AS '加注模式：1=近程自动 2=远程自动 3=手动' FROM oil.t_device_oil_order a LEFT JOIN oil.t_oil_type b ON a.oil_type_id = b.id WHERE a.device_id = '{device_id}' AND a.status = 1 AND a.order_time >= '{start_date}' AND a.order_time < '{end_condition}' ORDER BY a.order_time DESC;",
                "customer_query": "SELECT customer_name FROM oil.t_customer WHERE id = %s",
            }
        }
        mock_load_config.return_value = mock_config

        config = load_config()

        self.assertEqual(config["db_config"]["host"], "8.139.83.130")
        self.assertEqual(config["db_config"]["port"], 3306)
        self.assertEqual(config["db_config"]["user"], "query_zr")
        self.assertEqual(config["db_config"]["password"], "ZRYLPass220609!")
        self.assertEqual(config["db_config"]["database"], "oil")

        self.assertEqual(
            config["sql_templates"]["device_id_query"],
            "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s ORDER BY create_time DESC LIMIT 1",
        )
        self.assertEqual(
            config["sql_templates"]["inventory_query"],
            "SELECT a.id AS '订单序号', a.order_time AS '加注时间', a.oil_type_id AS '油品序号', b.oil_name AS '油品名称', a.water AS '水油比：水값', a.oil AS '水油比：油값', a.water_val AS '水加注', a.oil_val AS '油加注', a.avai_oil AS '原油剩余量', a.avai_oil / 1000 AS '原油剩余比例', a.oil_set_val AS '油加设量', a.is_settlement AS '是否结算：1=待结算 2=待生效 3=已结算', a.fill_mode AS '加注模式：1=近程自动 2=远程自动 3=手动' FROM oil.t_device_oil_order a LEFT JOIN oil.t_oil_type b ON a.oil_type_id = b.id WHERE a.device_id = '{device_id}' AND a.status = 1 AND a.order_time >= '{start_date}' AND a.order_time < '{end_condition}' ORDER BY a.order_time DESC;",
        )
        self.assertEqual(
            config["sql_templates"]["customer_query"],
            "SELECT customer_name FROM oil.t_customer WHERE id = %s",
        )
