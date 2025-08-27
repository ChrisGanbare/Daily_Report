"""
文件对话框选择器模块
提供文件和目录选择功能
"""
import logging
from tkinter import filedialog
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


# 创建全局实例
file_dialog_selector = FileDialogSelector(width=800, height=600, topmost=True)

# 便捷函数，保持向后兼容性
def choose_file(title: str = "选择文件", 
               filetypes: Optional[list] = None,
               initialdir: Optional[str] = None) -> Optional[str]:
    """
    显示文件选择对话框（保持向后兼容）
    
    Args:
        title: 对话框标题
        filetypes: 文件类型过滤器
        initialdir: 初始目录
        
    Returns:
        选择的文件路径，如果用户取消则返回None
    """
    return file_dialog_selector.choose_file(title, filetypes, initialdir)

def choose_directory(title: str = "选择目录",
                    initialdir: Optional[str] = None) -> Optional[str]:
    """
    显示目录选择对话框（保持向后兼容）
    
    Args:
        title: 对话框标题
        initialdir: 初始目录
        
    Returns:
        选择的目录路径，如果用户取消则返回None
    """
    return file_dialog_selector.choose_directory(title, initialdir)