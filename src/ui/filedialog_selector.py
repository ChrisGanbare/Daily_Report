"""
文件对话框选择器模块
提供文件和目录选择功能
"""
import logging
import tkinter as tk
from tkinter import filedialog
import threading
import time
import os
import sys
from typing import Optional
from .selector import Selector


class FileDialogSelector(Selector):
    """
    文件对话框选择器类
    提供文件和目录选择功能
    """
    
    def __init__(self, width: int = 800, height: int = 600, topmost: bool = True):
        """
        初始化文件对话框选择器
        
        Args:
            width: 对话框窗口宽度
            height: 对话框窗口高度
            topmost: 是否置顶显示
        """
        super().__init__(width, height, topmost)
        # Excel风格的文件对话框尺寸
        self.dialog_width = 960  # 固定为960像素宽度
        self.dialog_height = 600  # 固定为600像素高度

    def _resize_dialog(self, title: str) -> None:
        """
        调整文件对话框大小的辅助方法
        使用系统命令调整对话框大小，模拟Excel风格的文件对话框
        
        Args:
            title: 对话框标题
        """
        # 在Windows系统上使用win32api调整对话框大小
        if sys.platform.startswith('win'):
            try:
                import win32gui
                import win32api
                import win32con
                
                def resize_window():
                    # 增加初始等待时间，确保窗口完全初始化
                    time.sleep(0.1)
                    attempts = 0
                    max_attempts = 30  # 增加尝试次数
                    
                    # 扩展窗口标题匹配列表，包括常见的中文和英文标题
                    common_titles = [
                        title,
                        "选择设备信息CSV文件",
                        "选择保存目录",
                        "打开",
                        "选择文件夹",
                        "选择文件",
                        "浏览文件夹",
                        "文件打开",
                        "Folder Selection",
                        "File Selection",
                        "Open File",
                        "Select Folder"
                    ]
                    
                    # 循环尝试查找窗口，增加成功率
                    while attempts < max_attempts:
                        hwnd = None
                        # 尝试匹配所有可能的标题
                        for possible_title in common_titles:
                            hwnd = win32gui.FindWindow(None, possible_title)
                            if hwnd:
                                break
                        
                        # 如果通过标题找不到，尝试通过类名查找
                        if not hwnd:
                            # 查找常见的文件对话框类名
                            common_classes = [
                                "#32770",  # 标准Windows对话框类名
                                "TOpenDialog",  # Delphi对话框类名
                            ]
                            for class_name in common_classes:
                                hwnd = win32gui.FindWindow(class_name, None)
                                if hwnd:
                                    break
                        
                        if hwnd:
                            # 获取屏幕尺寸
                            screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                            screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                            # 计算居中位置
                            x = (screen_width - self.dialog_width) // 2
                            y = (screen_height - self.dialog_height) // 2
                            # 调整窗口大小和位置
                            win32gui.MoveWindow(hwnd, x, y, self.dialog_width, self.dialog_height, True)
                            break
                        else:
                            # 增加等待时间
                            time.sleep(0.1)
                            attempts += 1
                
                # 在单独的线程中调整窗口大小
                resize_thread = threading.Thread(target=resize_window)
                resize_thread.daemon = True
                resize_thread.start()
            except ImportError:
                # 如果没有win32gui库，则使用默认大小
                logging.warning("未安装pywin32库，无法调整对话框大小")
                pass
            except Exception as e:
                # 捕获其他可能的异常
                logging.warning(f"调整对话框大小时出现异常: {e}")
                pass

    def choose_file(self, title: str = "选择文件", 
                   filetypes: Optional[list] = None,
                   initialdir: Optional[str] = None) -> Optional[str]:
        """
        显示文件选择对话框
        
        Args:
            title: 对话框标题
            filetypes: 文件类型过滤器
            initialdir: 初始目录
            
        Returns:
            选择的文件路径，如果用户取消则返回None
        """
        if filetypes is None:
            filetypes = [("All files", "*.*")]
            
        # 启动调整大小的线程
        self._resize_dialog(title)
        
        root = self._create_root()
        try:
            file_path = filedialog.askopenfilename(
                title=title,
                filetypes=filetypes,
                initialdir=initialdir
            )
            return file_path if file_path else None
        except Exception as e:
            logging.warning(f"文件选择对话框出现异常: {e}")
            return None
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
        # 启动调整大小的线程
        self._resize_dialog(title)
        
        root = self._create_root()
        try:
            dir_path = filedialog.askdirectory(
                title=title,
                initialdir=initialdir
            )
            return dir_path if dir_path else None
        except Exception as e:
            logging.warning(f"目录选择对话框出现异常: {e}")
            return None
        finally:
            root.destroy()


# 创建全局实例，使用类似Office Excel的尺寸
file_dialog_selector = FileDialogSelector(width=960, height=600, topmost=True)