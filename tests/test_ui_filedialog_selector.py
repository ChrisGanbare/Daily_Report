import unittest
from unittest.mock import Mock, patch

from src.ui.filedialog_selector import FileDialogSelector


class TestFileDialogSelector(unittest.TestCase):
    """
    FileDialogSelector 类的单元测试
    """

    def setUp(self):
        """测试前准备"""
        self.dialog_selector = FileDialogSelector()
        self.default_title = "选择文件"
        self.default_filetypes = [("All files", "*.*")]
        self.default_initialdir = "/initial/dir"

    def test_filedialogselector_initialization(self):
        """
        测试 FileDialogSelector 类的初始化
        """
        # 测试默认参数
        selector = FileDialogSelector()
        self.assertEqual(selector.width, 800)
        self.assertEqual(selector.height, 600)
        self.assertTrue(selector.topmost)

        # 测试自定义参数
        selector = FileDialogSelector(width=1024, height=768, topmost=False)
        self.assertEqual(selector.width, 1024)
        self.assertEqual(selector.height, 768)
        self.assertFalse(selector.topmost)

    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askopenfilename")
    def test_filedialogselector_choose_file_method(self, mock_askopenfilename, mock_tk):
        """
        测试 FileDialogSelector 的 choose_file 方法在用户选择文件时的行为
        """
        # 模拟返回值
        mock_askopenfilename.return_value = "/path/to/file.txt"
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法
        result = self.dialog_selector.choose_file(
            self.default_title, self.default_filetypes, self.default_initialdir
        )

        # 验证结果
        self.assertEqual(result, "/path/to/file.txt")
        mock_tk.assert_called_once()
        mock_askopenfilename.assert_called_once_with(
            title=self.default_title,
            filetypes=self.default_filetypes,
            initialdir=self.default_initialdir
        )
        mock_root.destroy.assert_called_once()

    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askopenfilename")
    def test_filedialogselector_choose_file_user_cancel(self, mock_askopenfilename, mock_tk):
        """
        测试 FileDialogSelector 的 choose_file 方法在用户取消选择时的行为
        """
        # 模拟用户取消选择
        mock_askopenfilename.return_value = ""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法
        result = self.dialog_selector.choose_file(
            self.default_title, self.default_filetypes, self.default_initialdir
        )

        # 验证结果
        self.assertIsNone(result)
        mock_tk.assert_called_once()
        mock_askopenfilename.assert_called_once_with(
            title=self.default_title,
            filetypes=self.default_filetypes,
            initialdir=self.default_initialdir
        )
        mock_root.destroy.assert_called_once()

    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askopenfilename")
    def test_filedialogselector_choose_file_with_default_parameters(self, mock_askopenfilename, mock_tk):
        """
        测试 FileDialogSelector 的 choose_file 方法使用默认参数时的行为
        """
        # 模拟返回值
        mock_askopenfilename.return_value = "/path/to/file.txt"
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法，不提供可选参数
        result = self.dialog_selector.choose_file(self.default_title)

        # 验证结果
        self.assertEqual(result, "/path/to/file.txt")
        mock_tk.assert_called_once()
        mock_askopenfilename.assert_called_once_with(
            title=self.default_title,
            filetypes=[("All files", "*.*")],
            initialdir=None
        )
        mock_root.destroy.assert_called_once()

    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askopenfilename")
    def test_filedialogselector_choose_file_handles_exceptions(self, mock_askopenfilename, mock_tk):
        """
        测试 FileDialogSelector 的 choose_file 方法在发生异常时的处理
        """
        # 模拟异常
        mock_askopenfilename.side_effect = Exception("Dialog error")
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法
        result = self.dialog_selector.choose_file(self.default_title)

        # 验证结果
        self.assertIsNone(result)
        mock_tk.assert_called_once()
        mock_askopenfilename.assert_called_once_with(
            title=self.default_title,
            filetypes=[("All files", "*.*")],
            initialdir=None
        )
        mock_root.destroy.assert_called_once()

    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askdirectory")
    def test_filedialogselector_choose_directory_method(self, mock_askdirectory, mock_tk):
        """
        测试 FileDialogSelector 的 choose_directory 方法在用户选择目录时的行为
        """
        # 模拟返回值
        mock_askdirectory.return_value = "/path/to/directory"
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法
        result = self.dialog_selector.choose_directory(self.default_title, self.default_initialdir)

        # 验证结果
        self.assertEqual(result, "/path/to/directory")
        mock_tk.assert_called_once()
        mock_askdirectory.assert_called_once_with(
            title=self.default_title,
            initialdir=self.default_initialdir
        )
        mock_root.destroy.assert_called_once()

    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askdirectory")
    def test_filedialogselector_choose_directory_user_cancel(self, mock_askdirectory, mock_tk):
        """
        测试 FileDialogSelector 的 choose_directory 方法在用户取消选择时的行为
        """
        # 模拟用户取消选择
        mock_askdirectory.return_value = ""
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法
        result = self.dialog_selector.choose_directory(self.default_title, self.default_initialdir)

        # 验证结果
        self.assertIsNone(result)
        mock_tk.assert_called_once()
        mock_askdirectory.assert_called_once_with(
            title=self.default_title,
            initialdir=self.default_initialdir
        )
        mock_root.destroy.assert_called_once()

    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askdirectory")
    def test_filedialogselector_choose_directory_with_default_parameters(self, mock_askdirectory, mock_tk):
        """
        测试 FileDialogSelector 的 choose_directory 方法使用默认参数时的行为
        """
        # 模拟返回值
        mock_askdirectory.return_value = "/path/to/directory"
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法，不提供可选参数
        result = self.dialog_selector.choose_directory(self.default_title)

        # 验证结果
        self.assertEqual(result, "/path/to/directory")
        mock_tk.assert_called_once()
        mock_askdirectory.assert_called_once_with(
            title=self.default_title,
            initialdir=None
        )
        mock_root.destroy.assert_called_once()

    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askdirectory")
    def test_filedialogselector_choose_directory_handles_exceptions(self, mock_askdirectory, mock_tk):
        """
        测试 FileDialogSelector 的 choose_directory 方法在发生异常时的处理
        """
        # 模拟异常
        mock_askdirectory.side_effect = Exception("Dialog error")
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # 调用方法
        result = self.dialog_selector.choose_directory(self.default_title)

        # 验证结果
        self.assertIsNone(result)
        mock_tk.assert_called_once()
        mock_askdirectory.assert_called_once_with(
            title=self.default_title,
            initialdir=None
        )
        mock_root.destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()