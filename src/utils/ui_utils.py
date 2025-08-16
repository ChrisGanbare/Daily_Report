import tkinter as tk
from tkinter import filedialog
from typing import Optional, Union


class FileDialogUtil:
    """
    统一的文件/目录选择对话框工具类
    确保所有对话框遵循用户的偏好设置
    """

    def __init__(self, width: int = 400, height: int = 300, topmost: bool = True):
        """
        初始化文件对话框工具
        
        Args:
            width: 对话框窗口宽度
            height: 对话框窗口高度
            topmost: 是否置顶显示
        """
        self.width = width
        self.height = height
        self.topmost = topmost

    def _create_root(self) -> tk.Tk:
        """
        创建并配置根窗口
        
        Returns:
            配置好的根窗口
        """
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        root.geometry(f"{self.width}x{self.height}")
        root.attributes('-topmost', self.topmost)  # 设置窗口置顶
        return root

    def choose_file(self, title: str = "选择文件", 
                   filetypes: Optional[list] = None,
                   initialdir: Optional[str] = None) -> Optional[str]:
        """
        显示文件选择对话框
        
        Args:
            title: 对话框标题
            filetypes: 文件类型过滤器，例如 [("CSV files", "*.csv"), ("All files", "*.*")]
            initialdir: 初始目录
            
        Returns:
            选择的文件路径，如果用户取消则返回None
        """
        if filetypes is None:
            filetypes = [("All files", "*.*")]
            
        root = self._create_root()
        try:
            file_path = filedialog.askopenfilename(
                title=title,
                filetypes=filetypes,
                initialdir=initialdir
            )
            return file_path if file_path else None
        finally:
            root.destroy()

    def choose_directory(self, title: str = "选择目录",
                        initialdir: Optional[str] = None) -> Optional[str]:
        """
        显示目录选择对话框
        
        Args:
            title: 对话框标题
            initialdir: 初始目录
            
        Returns:
            选择的目录路径，如果用户取消则返回None
        """
        root = self._create_root()
        try:
            dir_path = filedialog.askdirectory(
                title=title,
                initialdir=initialdir
            )
            return dir_path if dir_path else None
        finally:
            root.destroy()


# 创建全局实例，确保所有地方使用统一的设置
file_dialog_util = FileDialogUtil(width=400, height=300, topmost=True)

# 便捷函数，直接使用全局实例
def choose_file(title: str = "选择文件", 
                filetypes: Optional[list] = None,
                initialdir: Optional[str] = None) -> Optional[str]:
    """
    便捷函数：显示文件选择对话框
    
    Args:
        title: 对话框标题
        filetypes: 文件类型过滤器
        initialdir: 初始目录
        
    Returns:
        选择的文件路径，如果用户取消则返回None
    """
    return file_dialog_util.choose_file(title, filetypes, initialdir)


def choose_directory(title: str = "选择目录",
                     initialdir: Optional[str] = None) -> Optional[str]:
    """
    便捷函数：显示目录选择对话框
    
    Args:
        title: 对话框标题
        initialdir: 初始目录
        
    Returns:
        选择的目录路径，如果用户取消则返回None
    """
    return file_dialog_util.choose_directory(title, initialdir)