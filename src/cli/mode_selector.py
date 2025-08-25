"""
模式选择对话框模块
"""
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmsg


def show_mode_selection_dialog():
    """
    显示模式选择对话框
    """
    def on_select():
        selected_value = combo.get()
        if selected_value == "请选择":
            # 显示提示信息并保持对话框打开
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
        # 处理用户点击窗口关闭按钮的情况
        result.set(None)
        root.quit()
    
    root = tk.Tk()
    root.title("ZR Daily Report - 模式选择")
    root.attributes('-topmost', True)
    
    # 设置窗口关闭事件处理函数
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 先设置窗口大小和居中位置，避免窗口在左上角闪烁
    window_width = 400
    window_height = 200
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
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
    
    root.mainloop()
    
    # 只有在root仍然存在时才尝试销毁它
    try:
        if root.winfo_exists():
            root.destroy()
    except:
        pass
    
    return result.get()