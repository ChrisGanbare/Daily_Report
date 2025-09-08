"""
基础选择器类
提供所有UI选择器的通用功能
"""
import tkinter as tk
from typing import Optional


class Selector:
    """
    基础选择器类
    提供所有UI选择器的通用功能，如窗口创建、居中显示等
    """
    
    def __init__(self, width: int = 900, height: int = 600, topmost: bool = True):
        """
        初始化选择器
        
        Args:
            width: 对话框窗口宽度
            height: 对话框窗口高度
            topmost: 是否置顶显示
        """
        self.width = width
        self.height = height
        self.topmost = topmost

    def _create_root(self, hidden: bool = True) -> tk.Tk:
        """
        创建并配置根窗口
        
        Args:
            hidden: 是否隐藏主窗口
            
        Returns:
            配置好的根窗口
        """
        root = tk.Tk()
        if hidden:
            root.withdraw()  # 隐藏主窗口
        root.geometry(f"{self.width}x{self.height}")
        root.attributes('-topmost', self.topmost)
        return root

    def _center_window(self, root: tk.Tk, width: int, height: int) -> None:
        """
        将窗口居中显示
        
        Args:
            root: Tk根窗口
            width: 窗口宽度
            height: 窗口高度
        """
        root.update_idletasks()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")