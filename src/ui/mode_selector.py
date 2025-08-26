"""
模式选择对话框模块
提供模式选择功能
"""
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmsg
from typing import Optional
from .selector import Selector


class ModeSelector(Selector):
    """
    模式选择器类
    提供模式选择功能
    """
    
    def __init__(self, width: int = 400, height: int = 200, topmost: bool = True):
        """
        初始化模式选择器
        
        Args:
            width: 对话框窗口宽度
            height: 对话框窗口高度
            topmost: 是否置顶显示
        """
        super().__init__(width, height, topmost)
    
    def _center_window(self, window: tk.Tk, window_width: int, window_height: int):
        """
        将窗口居中显示在屏幕中央
        
        Args:
            window: 要居中的窗口对象
            window_width: 窗口宽度
            window_height: 窗口高度
        """
        # 获取屏幕尺寸
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # 计算窗口位置
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        # 设置窗口几何位置
        window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def show_mode_selection_dialog(self) -> Optional[str]:
        """
        显示模式选择对话框
        
        Returns:
            选择的模式: "both", "inventory", "statement" 或 None(取消操作)
        """
        def on_select():
            selected_value = combo.get()
            if selected_value == "请选择":
                tkmsg.showwarning("无效选择", "请选择一个有效的执行模式！")
                return
            elif selected_value == "同时生成库存表和对账单":
                result.set("both")
            elif selected_value == "生成库存表":
                result.set("inventory")
            elif selected_value == "生成对账单":
                result.set("statement")
            root.quit()
        
        def on_cancel():
            result.set(None)
            root.quit()
        
        def on_closing():
            result.set(None)
            root.quit()
        
        # 创建主窗口并立即隐藏
        root = tk.Tk()
        root.withdraw()
        root.title("ZR Daily Report - 模式选择")
        root.attributes('-topmost', self.topmost)
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 更新窗口任务以获取准确的屏幕信息
        root.update_idletasks()
        
        # 使用居中方法设置窗口位置
        self._center_window(root, self.width, self.height)
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加标签
        label = ttk.Label(main_frame, text="请选择执行模式:", font=("Arial", 12))
        label.pack(pady=(0, 10))
        
        # 添加下拉框
        options = ["请选择", "同时生成库存表和对账单", "生成库存表", "生成对账单"]
        combo = ttk.Combobox(main_frame, values=options, state="readonly", font=("Arial", 10), width=30)
        combo.set("请选择")
        combo.pack(pady=(0, 20))
        
        # 添加按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 添加确定按钮
        ok_button = ttk.Button(button_frame, text="确定", command=on_select)
        ok_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", command=on_cancel)
        cancel_button.pack(side=tk.LEFT)
        
        # 存储结果
        result = tk.StringVar()
        
        # 绑定回车键
        root.bind('<Return>', lambda event: on_select())
        # 绑定ESC键
        root.bind('<Escape>', lambda event: on_cancel())
        
        # 显示窗口（此时窗口已正确设置位置和大小）
        root.deiconify()
        
        root.mainloop()
        
        try:
            if root.winfo_exists():
                root.destroy()
        except:
            pass
        
        return result.get()


# 创建全局实例
mode_selector = ModeSelector(width=400, height=200, topmost=True)

# 便捷函数，保持向后兼容性
def show_mode_selection_dialog() -> Optional[str]:
    """
    显示模式选择对话框（保持向后兼容）
    
    Returns:
        选择的模式: "both", "inventory", "statement" 或 None(取消操作)
    """
    return mode_selector.show_mode_selection_dialog()