import os
import sys
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.ui_utils import FileDialogUtil, choose_directory, choose_file
from tests.base_test import BaseTestCase


class TestUtilsUi_utils(BaseTestCase):
    """
    utils.ui_utils 模块的单元测试
    """

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.dialog_util = FileDialogUtil(width=400, height=300, topmost=True)

    def test_filedialogutil_initialization(self):
        """
        测试 FileDialogUtil 类的初始化
        """
        # 测试默认参数
        util = FileDialogUtil()
        self.assertEqual(util.width, 400)
        self.assertEqual(util.height, 300)
        self.assertTrue(util.topmost)

        # 测试自定义参数
        util = FileDialogUtil(width=800, height=600, topmost=False)
        self.assertEqual(util.width, 800)
        self.assertEqual(util.height, 600)
        self.assertFalse(util.topmost)

    @patch("src.utils.ui_utils.tk.Tk")
    @patch("src.utils.ui_utils.filedialog.askopenfilename")
    def test_filedialogutil_choose_file(self, mock_askopenfilename, mock_tk):
        """
        测试 FileDialogUtil.choose_file 方法
        """
        # 模拟返回值
        mock_askopenfilename.return_value = "/path/to/file.txt"
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法
        result = self.dialog_util.choose_file(
            "选择文件", [("Text files", "*.txt")], "/initial/dir"
        )

        # 验证结果
        self.assertEqual(result, "/path/to/file.txt")
        mock_tk.assert_called_once()
        mock_askopenfilename.assert_called_once()
        mock_root.destroy.assert_called_once()

    @patch("src.utils.ui_utils.tk.Tk")
    @patch("src.utils.ui_utils.filedialog.askopenfilename")
    def test_filedialogutil_choose_file_user_cancel(
        self, mock_askopenfilename, mock_tk
    ):
        """
        测试 FileDialogUtil.choose_file 方法当用户取消选择时的行为
        """
        # 模拟用户取消选择
        mock_askopenfilename.return_value = ""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法
        result = self.dialog_util.choose_file(
            "选择文件", [("Text files", "*.txt")], "/initial/dir"
        )

        # 验证结果
        self.assertIsNone(result)
        mock_tk.assert_called_once()
        mock_askopenfilename.assert_called_once()
        mock_root.destroy.assert_called_once()

    @patch("src.utils.ui_utils.tk.Tk")
    @patch("src.utils.ui_utils.filedialog.askopenfilename")
    def test_filedialogutil_choose_file_without_optional_params(
        self, mock_askopenfilename, mock_tk
    ):
        """
        测试 FileDialogUtil.choose_file 方法未提供可选参数时的行为
        """
        # 模拟返回值
        mock_askopenfilename.return_value = "/path/to/file.txt"
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法，不提供可选参数
        result = self.dialog_util.choose_file("选择文件")

        # 验证结果
        self.assertEqual(result, "/path/to/file.txt")
        mock_tk.assert_called_once()
        mock_askopenfilename.assert_called_once_with(
            title="选择文件", filetypes=[("All files", "*.*")], initialdir=None
        )
        mock_root.destroy.assert_called_once()

    @patch("src.utils.ui_utils.tk.Tk")
    @patch("src.utils.ui_utils.filedialog.askopenfilename")
    def test_filedialogutil_choose_file_exception_handling(
        self, mock_askopenfilename, mock_tk
    ):
        """
        测试 FileDialogUtil.choose_file 方法的异常处理
        """
        # 模拟异常
        mock_askopenfilename.side_effect = Exception("Dialog error")
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法
        result = self.dialog_util.choose_file("选择文件")

        # 验证结果
        self.assertIsNone(result)
        mock_tk.assert_called_once()
        mock_root.destroy.assert_called_once()

    @patch("src.utils.ui_utils.tk.Tk")
    @patch("src.utils.ui_utils.filedialog.askdirectory")
    def test_filedialogutil_choose_directory(self, mock_askdirectory, mock_tk):
        """
        测试 FileDialogUtil.choose_directory 方法
        """
        # 模拟返回值
        mock_askdirectory.return_value = "/path/to/directory"
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法
        result = self.dialog_util.choose_directory("选择目录", "/initial/dir")

        # 验证结果
        self.assertEqual(result, "/path/to/directory")
        mock_tk.assert_called_once()
        mock_askdirectory.assert_called_once()
        mock_root.destroy.assert_called_once()

    @patch("src.utils.ui_utils.tk.Tk")
    @patch("src.utils.ui_utils.filedialog.askdirectory")
    def test_filedialogutil_choose_directory_user_cancel(
        self, mock_askdirectory, mock_tk
    ):
        """
        测试 FileDialogUtil.choose_directory 方法当用户取消选择时的行为
        """
        # 模拟用户取消选择
        mock_askdirectory.return_value = ""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法
        result = self.dialog_util.choose_directory("选择目录", "/initial/dir")

        # 验证结果
        self.assertIsNone(result)
        mock_tk.assert_called_once()
        mock_askdirectory.assert_called_once()
        mock_root.destroy.assert_called_once()

    @patch("src.utils.ui_utils.tk.Tk")
    @patch("src.utils.ui_utils.filedialog.askdirectory")
    def test_filedialogutil_choose_directory_without_optional_params(
        self, mock_askdirectory, mock_tk
    ):
        """
        测试 FileDialogUtil.choose_directory 方法未提供可选参数时的行为
        """
        # 模拟返回值
        mock_askdirectory.return_value = "/path/to/directory"
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法，不提供可选参数
        result = self.dialog_util.choose_directory("选择目录")

        # 验证结果
        self.assertEqual(result, "/path/to/directory")
        mock_tk.assert_called_once()
        mock_askdirectory.assert_called_once_with(title="选择目录", initialdir=None)
        mock_root.destroy.assert_called_once()

    @patch("src.utils.ui_utils.tk.Tk")
    @patch("src.utils.ui_utils.filedialog.askdirectory")
    def test_filedialogutil_choose_directory_exception_handling(
        self, mock_askdirectory, mock_tk
    ):
        """
        测试 FileDialogUtil.choose_directory 方法的异常处理
        """
        # 模拟异常
        mock_askdirectory.side_effect = Exception("Dialog error")
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法
        result = self.dialog_util.choose_directory("选择目录")

        # 验证结果
        self.assertIsNone(result)
        mock_tk.assert_called_once()
        mock_root.destroy.assert_called_once()

    @patch("src.utils.ui_utils.file_dialog_util")
    def test_choose_file(self, mock_util):
        """
        测试 choose_file 函数
        """
        # 模拟返回值
        mock_util.choose_file.return_value = "/path/to/file.txt"

        # 调用函数
        result = choose_file("选择文件", [("Text files", "*.txt")], "/initial/dir")

        # 验证结果
        self.assertEqual(result, "/path/to/file.txt")
        mock_util.choose_file.assert_called_once_with(
            "选择文件", [("Text files", "*.txt")], "/initial/dir"
        )

    @patch("src.utils.ui_utils.file_dialog_util")
    def test_choose_file_user_cancel(self, mock_util):
        """
        测试 choose_file 函数当用户取消选择时的行为
        """
        # 模拟用户取消选择
        mock_util.choose_file.return_value = None

        # 调用函数
        result = choose_file("选择文件", [("Text files", "*.txt")], "/initial/dir")

        # 验证结果
        self.assertIsNone(result)
        mock_util.choose_file.assert_called_once_with(
            "选择文件", [("Text files", "*.txt")], "/initial/dir"
        )

    @patch("src.utils.ui_utils.file_dialog_util")
    def test_choose_file_without_optional_params(self, mock_util):
        """
        测试 choose_file 函数未提供可选参数时的行为
        """
        # 模拟返回值
        mock_util.choose_file.return_value = "/path/to/file.txt"

        # 调用函数，不提供可选参数
        result = choose_file("选择文件")

        # 验证结果
        self.assertEqual(result, "/path/to/file.txt")
        mock_util.choose_file.assert_called_once_with("选择文件", None, None)

    @patch("src.utils.ui_utils.file_dialog_util")
    def test_choose_directory(self, mock_util):
        """
        测试 choose_directory 函数
        """
        # 模拟返回值
        mock_util.choose_directory.return_value = "/path/to/directory"

        # 调用函数
        result = choose_directory("选择目录", "/initial/dir")

        # 验证结果
        self.assertEqual(result, "/path/to/directory")
        mock_util.choose_directory.assert_called_once_with("选择目录", "/initial/dir")

    @patch("src.utils.ui_utils.file_dialog_util")
    def test_choose_directory_user_cancel(self, mock_util):
        """
        测试 choose_directory 函数当用户取消选择时的行为
        """
        # 模拟用户取消选择
        mock_util.choose_directory.return_value = None

        # 调用函数
        result = choose_directory("选择目录", "/initial/dir")

        # 验证结果
        self.assertIsNone(result)
        mock_util.choose_directory.assert_called_once_with("选择目录", "/initial/dir")

    @patch("src.utils.ui_utils.file_dialog_util")
    def test_choose_directory_without_optional_params(self, mock_util):
        """
        测试 choose_directory 函数未提供可选参数时的行为
        """
        # 模拟返回值
        mock_util.choose_directory.return_value = "/path/to/directory"

        # 调用函数，不提供可选参数
        result = choose_directory("选择目录")

        # 验证结果
        self.assertEqual(result, "/path/to/directory")
        mock_util.choose_directory.assert_called_once_with("选择目录", None)

    @patch("src.utils.ui_utils.tk.Tk")
    def test_filedialogutil_create_root(self, mock_tk):
        """
        测试 FileDialogUtil._create_root 方法
        """
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 创建根窗口
        root = self.dialog_util._create_root()

        # 验证根窗口属性设置
        mock_root.withdraw.assert_called_once()
        mock_root.geometry.assert_called_once_with("400x300")
        mock_root.attributes.assert_called_once_with("-topmost", True)

    def test_global_instance(self):
        """
        测试全局实例的创建和属性
        """
        from src.utils.ui_utils import file_dialog_util

        self.assertIsInstance(file_dialog_util, FileDialogUtil)
        self.assertEqual(file_dialog_util.width, 400)
        self.assertEqual(file_dialog_util.height, 300)
        self.assertTrue(file_dialog_util.topmost)


if __name__ == "__main__":
    unittest.main()
