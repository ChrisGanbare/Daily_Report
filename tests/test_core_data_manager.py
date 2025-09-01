"""
core.data_manager 模块的单元测试
"""
import os
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import MagicMock, Mock, patch, mock_open

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.data_manager import CustomerGroupingUtil
from tests.base_test import BaseTestCase


class TestCustomerGroupingUtil(BaseTestCase):
    """CustomerGroupingUtil 类的单元测试"""

    def test_group_devices_by_customer(self):
        """测试按客户分组设备功能"""
        # 准备测试数据
        devices_data = [
            {
                'device_code': 'DEV001',
                'customer_id': 1,
                'customer_name': '客户A',
                'data': []
            },
            {
                'device_code': 'DEV002',
                'customer_id': 1,
                'customer_name': '客户A',
                'data': []
            },
            {
                'device_code': 'DEV003',
                'customer_id': 2,
                'customer_name': '客户B',
                'data': []
            }
        ]

        # 执行分组操作
        result = CustomerGroupingUtil.group_devices_by_customer(devices_data)

        # 验证结果
        self.assertEqual(len(result), 2)  # 应该有两个客户
        self.assertIn(1, result)  # 客户ID 1应该在结果中
        self.assertIn(2, result)  # 客户ID 2应该在结果中

        # 验证客户A的数据
        self.assertEqual(result[1]['customer_name'], '客户A')
        self.assertEqual(len(result[1]['devices']), 2)  # 客户A应该有两个设备

        # 验证客户B的数据
        self.assertEqual(result[2]['customer_name'], '客户B')
        self.assertEqual(len(result[2]['devices']), 1)  # 客户B应该有一个设备

        # 验证设备数据正确性
        customer_a_devices = [d['device_code'] for d in result[1]['devices']]
        self.assertIn('DEV001', customer_a_devices)
        self.assertIn('DEV002', customer_a_devices)

        customer_b_devices = [d['device_code'] for d in result[2]['devices']]
        self.assertIn('DEV003', customer_b_devices)

    def test_get_customer_list(self):
        """测试获取客户列表功能"""
        # 准备测试数据
        devices_data = [
            {
                'device_code': 'DEV001',
                'customer_id': 1,
                'customer_name': '客户A',
                'data': []
            },
            {
                'device_code': 'DEV002',
                'customer_id': 1,
                'customer_name': '客户A',
                'data': []
            },
            {
                'device_code': 'DEV003',
                'customer_id': 2,
                'customer_name': '客户B',
                'data': []
            }
        ]

        # 执行获取客户列表操作
        result = CustomerGroupingUtil.get_customer_list(devices_data)

        # 验证结果
        self.assertEqual(len(result), 2)  # 应该有两个客户

        # 验证客户信息
        customer_ids = [c['customer_id'] for c in result]
        customer_names = [c['customer_name'] for c in result]

        self.assertIn(1, customer_ids)
        self.assertIn(2, customer_ids)
        self.assertIn('客户A', customer_names)
        self.assertIn('客户B', customer_names)

    def test_group_devices_with_missing_customer_info(self):
        """测试处理缺少客户信息的设备数据"""
        # 准备测试数据，包含缺少客户信息的设备
        devices_data = [
            {
                'device_code': 'DEV001',
                'customer_id': 1,
                'customer_name': '客户A',
                'data': []
            },
            {
                'device_code': 'DEV002',
                'data': []  # 缺少客户信息
            },
            {
                'device_code': 'DEV003',
                'customer_id': 2,
                'customer_name': '客户B',
                'data': []
            }
        ]

        # 执行分组操作
        result = CustomerGroupingUtil.group_devices_by_customer(devices_data)

        # 验证结果
        self.assertEqual(len(result), 2)  # 应该只有两个有效客户
        self.assertIn(1, result)
        self.assertIn(2, result)

        # 验证客户A的数据（应该只有一个设备，因为DEV002被忽略了）
        self.assertEqual(result[1]['customer_name'], '客户A')
        self.assertEqual(len(result[1]['devices']), 1)  # 只有一个有效设备


if __name__ == '__main__':
    unittest.main()
