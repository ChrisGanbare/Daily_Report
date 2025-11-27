"""
一个简单的Tkinter对话框，用于选择开始和结束日期。
"""
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime

class DateRangeDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, max_days=None):
        """
        初始化日期范围对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            max_days: 最大日期跨度（天数），None 表示不限制
        """
        self.max_days = max_days
        super().__init__(parent, title)
    
    def body(self, master):
        tk.Label(master, text="开始日期 (YYYY-MM-DD):").grid(row=0)
        tk.Label(master, text="结束日期 (YYYY-MM-DD):").grid(row=1)

        self.start_date_entry = tk.Entry(master)
        self.end_date_entry = tk.Entry(master)

        # 设置默认值为今天
        today_str = datetime.now().strftime('%Y-%m-%d')
        self.start_date_entry.insert(0, today_str)
        self.end_date_entry.insert(0, today_str)

        self.start_date_entry.grid(row=0, column=1)
        self.end_date_entry.grid(row=1, column=1)
        return self.start_date_entry # initial focus

    def validate(self):
        start_str = self.start_date_entry.get()
        end_str = self.end_date_entry.get()
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_str, '%Y-%m-%d')
            if start_date > end_date:
                messagebox.showerror("日期错误", "开始日期不能晚于结束日期。")
                return 0
            
            # 验证日期跨度限制
            if self.max_days is not None:
                date_span = (end_date.date() - start_date.date()).days + 1
                if date_span > self.max_days:
                    messagebox.showerror("日期跨度错误", f"日期跨度不能超过{self.max_days}天，当前跨度为{date_span}天。\n请选择不超过{self.max_days}天的日期范围。")
                    return 0
            
            return 1
        except ValueError:
            messagebox.showerror("格式错误", "日期格式无效，请使用 YYYY-MM-DD 格式。")
            return 0

    def apply(self):
        self.result = (self.start_date_entry.get(), self.end_date_entry.get())

def get_date_range(max_days=None):
    """
    显示日期范围选择对话框并返回用户选择的日期。

    Args:
        max_days (int, optional): 最大日期跨度（天数），None 表示不限制

    Returns:
        tuple: (start_date_str, end_date_str) or None if canceled.
    """
    
    # 创建一个隐藏的根窗口
    root = tk.Tk()
    root.withdraw()
    
    dialog = DateRangeDialog(root, "选择报表日期范围", max_days=max_days)
    
    # 销毁根窗口
    root.destroy()
    
    return dialog.result