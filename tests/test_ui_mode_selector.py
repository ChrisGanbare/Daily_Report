import os
import sys
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ui.mode_selector import ModeSelector, show_mode_selection_dialog
from tests.base_test import BaseTestCase


class TestUiModeSelector(BaseTestCase):
    """
    ui.mode_selector 模块的单元测试
    """

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.mode_selector = ModeSelector(width=400, height=200, topmost=True)

    def test_modeselector_initialization(self):
        """
        测试 ModeSelector 类的初始化
        """
        # 测试默认参数
        selector = ModeSelector()
        self.assertEqual(selector.width, 400)
        self.assertEqual(selector.height, 200)
        self.assertTrue(selector.topmost)

        # 测试自定义参数
        selector = ModeSelector(width=800, height=600, topmost=False)
        self.assertEqual(selector.width, 800)
        self.assertEqual(selector.height, 600)
        self.assertFalse(selector.topmost)

    @patch("src.ui.mode_selector.mode_selector")
    def test_show_mode_selection_dialog(self, mock_selector):
        """
        测试 show_mode_selection_dialog 函数
        """
        # 模拟返回值
        mock_selector.show_mode_selection_dialog.return_value = "both"

        # 调用函数
        result = show_mode_selection_dialog()

        # 验证结果
        self.assertEqual(result, "both")
        mock_selector.show_mode_selection_dialog.assert_called_once()


if __name__ == "__main__":
    unittest.main()