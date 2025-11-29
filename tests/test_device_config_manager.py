"""
设备配置管理器测试
测试汇总报表桶数配置文件的各种情况
"""
import csv
import os
import sys
import tempfile
import unittest
from io import StringIO

# 添加项目根目录到sys.path
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

# 直接导入模块，避免触发__init__.py中的其他导入
import importlib.util
spec = importlib.util.spec_from_file_location(
    "device_config_manager",
    os.path.join(project_root, "src", "core", "device_config_manager.py")
)
device_config_manager_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(device_config_manager_module)
DeviceConfigManager = device_config_manager_module.DeviceConfigManager

from tests.base_test import BaseTestCase


class TestDeviceConfigManager(BaseTestCase):
    """设备配置管理器测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        # 创建临时配置文件目录
        self.test_config_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.test_config_dir, "device_config.csv")

    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        if os.path.exists(self.test_config_dir):
            os.rmdir(self.test_config_dir)
        super().tearDown()

    def create_config_file(self, content, encoding='utf-8'):
        """创建测试配置文件"""
        with open(self.test_config_file, 'w', encoding=encoding, newline='') as f:
            f.write(content)

    def test_encoding_utf8(self):
        """测试1: 配置文件支持UTF-8编码格式"""
        content = "device_code,barrel_count\nMO24032700700011,2\nMO24032700700020,3\n"
        self.create_config_file(content, encoding='utf-8')
        
        manager = DeviceConfigManager(self.test_config_file)
        config = manager.load_config()
        
        self.assertEqual(len(config), 2)
        self.assertEqual(config.get('MO24032700700011'), 2)
        self.assertEqual(config.get('MO24032700700020'), 3)

    def test_encoding_utf8_sig(self):
        """测试2: 配置文件支持UTF-8-SIG编码格式（带BOM）"""
        # 使用utf-8-sig编码创建文件，Python会自动添加BOM
        content = "device_code,barrel_count\nMO24032700700011,2\nMO24032700700020,3\n"
        # 直接写入BOM和内容
        with open(self.test_config_file, 'w', encoding='utf-8-sig', newline='') as f:
            f.write(content)
        
        manager = DeviceConfigManager(self.test_config_file)
        config = manager.load_config()
        
        self.assertEqual(len(config), 2)
        self.assertEqual(config.get('MO24032700700011'), 2)
        self.assertEqual(config.get('MO24032700700020'), 3)

    def test_encoding_gbk(self):
        """测试3: 配置文件支持GBK编码格式"""
        # 创建包含中文注释的GBK文件
        content = "device_code,barrel_count\nMO24032700700011,2\nMO24032700700020,3\n"
        self.create_config_file(content, encoding='gbk')
        
        manager = DeviceConfigManager(self.test_config_file)
        config = manager.load_config()
        
        self.assertEqual(len(config), 2)
        self.assertEqual(config.get('MO24032700700011'), 2)
        self.assertEqual(config.get('MO24032700700020'), 3)

    def test_encoding_gb2312(self):
        """测试4: 配置文件支持GB2312编码格式"""
        content = "device_code,barrel_count\nMO24032700700011,2\nMO24032700700020,3\n"
        self.create_config_file(content, encoding='gb2312')
        
        manager = DeviceConfigManager(self.test_config_file)
        config = manager.load_config()
        
        self.assertEqual(len(config), 2)
        self.assertEqual(config.get('MO24032700700011'), 2)
        self.assertEqual(config.get('MO24032700700020'), 3)

    def test_empty_device_code(self):
        """测试5: 设备编码为空的情况（应跳过该行）"""
        content = "device_code,barrel_count\n,2\nMO24032700700011,2\n,3\nMO24032700700020,3\n"
        self.create_config_file(content)
        
        manager = DeviceConfigManager(self.test_config_file)
        config = manager.load_config()
        
        # 应该只包含有设备编码的行
        self.assertEqual(len(config), 2)
        self.assertEqual(config.get('MO24032700700011'), 2)
        self.assertEqual(config.get('MO24032700700020'), 3)
        # 空设备编码的行应该被跳过，不在配置中

    def test_empty_barrel_count(self):
        """测试6: 桶数为空的情况（应使用默认值1）"""
        content = "device_code,barrel_count\nMO24032700700011,\nMO24032700700020,3\nMO24032700700030,\n"
        self.create_config_file(content)
        
        manager = DeviceConfigManager(self.test_config_file)
        config = manager.load_config()
        
        self.assertEqual(len(config), 3)
        # 桶数为空时，应该使用默认值1
        self.assertEqual(config.get('MO24032700700011'), 1)
        self.assertEqual(config.get('MO24032700700020'), 3)
        self.assertEqual(config.get('MO24032700700030'), 1)

    def test_empty_device_code_and_barrel_count(self):
        """测试7: 设备编码和桶数都为空的情况（应跳过该行）"""
        content = "device_code,barrel_count\nMO24032700700011,2\n,\nMO24032700700020,3\n"
        self.create_config_file(content)
        
        manager = DeviceConfigManager(self.test_config_file)
        config = manager.load_config()
        
        # 应该只包含有设备编码的行
        self.assertEqual(len(config), 2)
        self.assertEqual(config.get('MO24032700700011'), 2)
        self.assertEqual(config.get('MO24032700700020'), 3)

    def test_invalid_barrel_count_string(self):
        """测试8: 桶数输入字符（非数字）的情况（应使用默认值1）"""
        content = "device_code,barrel_count\nMO24032700700011,abc\nMO24032700700020,3\nMO24032700700030,xyz\nMO24032700700040,2.5\n"
        self.create_config_file(content)
        
        manager = DeviceConfigManager(self.test_config_file)
        config = manager.load_config()
        
        self.assertEqual(len(config), 4)
        # 桶数为非数字字符时，应该使用默认值1
        self.assertEqual(config.get('MO24032700700011'), 1)
        self.assertEqual(config.get('MO24032700700020'), 3)
        self.assertEqual(config.get('MO24032700700030'), 1)
        # 浮点数2.5无法用int()直接转换，会抛出ValueError，所以使用默认值1
        self.assertEqual(config.get('MO24032700700040'), 1)

    def test_invalid_barrel_count_negative(self):
        """测试9: 桶数为负数的情况（应使用默认值1）"""
        content = "device_code,barrel_count\nMO24032700700011,-1\nMO24032700700020,0\nMO24032700700030,3\n"
        self.create_config_file(content)
        
        manager = DeviceConfigManager(self.test_config_file)
        config = manager.load_config()
        
        self.assertEqual(len(config), 3)
        # 桶数小于1时，应该使用默认值1
        self.assertEqual(config.get('MO24032700700011'), 1)
        self.assertEqual(config.get('MO24032700700020'), 1)
        self.assertEqual(config.get('MO24032700700030'), 3)

    def test_mixed_valid_and_invalid_data(self):
        """测试10: 混合有效和无效数据的情况"""
        content = "device_code,barrel_count\nMO24032700700011,2\n,3\nMO24032700700020,\nMO24032700700030,abc\nMO24032700700040,4\n"
        self.create_config_file(content)
        
        manager = DeviceConfigManager(self.test_config_file)
        config = manager.load_config()
        
        # 应该只包含有效的设备编码
        self.assertEqual(len(config), 4)
        self.assertEqual(config.get('MO24032700700011'), 2)
        # 空设备编码的行被跳过
        self.assertEqual(config.get('MO24032700700020'), 1)  # 空桶数使用默认值1
        self.assertEqual(config.get('MO24032700700030'), 1)  # 无效桶数使用默认值1
        self.assertEqual(config.get('MO24032700700040'), 4)

    def test_get_barrel_count_with_valid_device(self):
        """测试11: 通过get_barrel_count获取有效设备的桶数"""
        content = "device_code,barrel_count\nMO24032700700011,2\nMO24032700700020,3\n"
        self.create_config_file(content)
        
        manager = DeviceConfigManager(self.test_config_file)
        
        # 测试存在的设备
        self.assertEqual(manager.get_barrel_count('MO24032700700011'), 2)
        self.assertEqual(manager.get_barrel_count('MO24032700700020'), 3)
        
        # 测试不存在的设备（应返回默认值1）
        self.assertEqual(manager.get_barrel_count('NOT_EXIST'), 1)

    def test_get_barrel_count_with_empty_device_code(self):
        """测试12: 通过get_barrel_count获取空设备编码的桶数（应返回默认值1）"""
        content = "device_code,barrel_count\nMO24032700700011,2\n"
        self.create_config_file(content)
        
        manager = DeviceConfigManager(self.test_config_file)
        
        # 测试空设备编码
        self.assertEqual(manager.get_barrel_count(''), 1)
        # 注意：虽然类型提示是str，但实际代码可以处理None（通过if not device_code检查）
        # 为了测试健壮性，我们测试空字符串即可

    def test_config_file_not_exists(self):
        """测试13: 配置文件不存在的情况（应返回空字典，使用默认值1）"""
        non_exist_file = os.path.join(self.test_config_dir, "non_exist.csv")
        manager = DeviceConfigManager(non_exist_file)
        
        config = manager.load_config()
        self.assertEqual(len(config), 0)
        
        # 任何设备编码都应该返回默认值1
        self.assertEqual(manager.get_barrel_count('ANY_DEVICE'), 1)

    def test_config_cache(self):
        """测试14: 配置缓存功能"""
        content = "device_code,barrel_count\nMO24032700700011,2\n"
        self.create_config_file(content)
        
        manager = DeviceConfigManager(self.test_config_file)
        
        # 第一次加载
        config1 = manager.load_config()
        self.assertEqual(len(config1), 1)
        
        # 第二次加载应该使用缓存
        config2 = manager.load_config()
        self.assertEqual(len(config2), 1)
        self.assertIs(config1, config2)  # 应该是同一个对象（缓存）
        
        # 清除缓存后重新加载
        manager.clear_cache()
        config3 = manager.load_config()
        self.assertEqual(len(config3), 1)
        # 注意：由于重新创建了字典，可能不是同一个对象，但内容应该相同


if __name__ == '__main__':
    unittest.main()

