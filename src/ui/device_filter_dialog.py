"""
设备筛选对话框
支持按客户名称筛选设备，用于误差汇总报表
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Optional, Tuple


class DeviceFilterDialog(tk.Tk):
    """设备筛选对话框"""
    
    def __init__(self, parent, db_handler, max_devices=200):
        """
        初始化设备筛选对话框
        
        Args:
            parent: 父窗口（保留参数以兼容，但不再使用）
            db_handler: 数据库处理器
            max_devices: 最大可选设备数量
        """
        try:
            super().__init__()
            self.db_handler = db_handler
            self.max_devices = max_devices
            self.selected_customer_ids = []  # 选中的客户ID列表
            self.all_customers = []  # 所有客户列表
            self.customer_devices_map = {}  # 客户ID -> 设备列表的映射
            self.result = None  # 返回结果：(selected_device_ids, selected_customer_names)
            
            self.title("设备筛选")
            self.geometry("700x600")  # 增加窗口高度，确保按钮可见
            self.resizable(True, True)
            self.minsize(600, 500)  # 设置最小尺寸
            
            # 使对话框模态（不再需要transient，因为这是主窗口）
            self.grab_set()
            
            # 设置关闭协议
            self.protocol("WM_DELETE_WINDOW", self._on_cancel)
            
            # 创建UI组件
            self._create_widgets()
            
            # 居中显示
            self.update_idletasks()
            x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
            y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")
            
            # 立即显示对话框
            self.deiconify()
            self.lift()
            self.focus_force()
            self.update()
            
            # 确保对话框显示在最前（延迟设置，避免与父窗口冲突）
            self.after(50, lambda: self.attributes('-topmost', True))
            
            # 在显示后再加载数据（避免阻塞UI）
            self.after(100, self._load_customers)
        except Exception as e:
            import traceback
            print(f"设备筛选对话框初始化错误: {e}")
            print(traceback.format_exc())
            raise
    
    def _create_widgets(self):
        """创建UI组件"""
        # 主容器 - 用于整体布局
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 内容区域
        main_frame = ttk.Frame(main_container)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 客户筛选区域
        customer_frame = ttk.LabelFrame(main_frame, text="客户筛选", padding="10")
        customer_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        # 客户输入框（用于搜索）
        ttk.Label(customer_frame, text="客户名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.customer_search_var = tk.StringVar()
        self.customer_search_var.trace('w', self._on_search_changed)
        customer_search_entry = ttk.Entry(customer_frame, textvariable=self.customer_search_var, width=30)
        customer_search_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # 客户下拉列表（多选）
        ttk.Label(customer_frame, text="选择客户:").grid(row=1, column=0, sticky=tk.W+tk.N, pady=5)
        
        # 使用带滚动条的Frame来容纳客户列表
        customer_list_container = ttk.Frame(customer_frame)
        customer_list_container.grid(row=1, column=1, sticky=tk.W+tk.E+tk.N+tk.S, padx=5, pady=5)
        
        # 创建Canvas和Scrollbar用于滚动
        customer_canvas = tk.Canvas(customer_list_container, height=120)
        customer_scrollbar = ttk.Scrollbar(customer_list_container, orient=tk.VERTICAL, command=customer_canvas.yview)
        customer_scrollable_frame = ttk.Frame(customer_canvas)
        
        customer_scrollable_frame.bind(
            "<Configure>",
            lambda e: customer_canvas.configure(scrollregion=customer_canvas.bbox("all"))
        )
        
        customer_canvas.create_window((0, 0), window=customer_scrollable_frame, anchor="nw")
        customer_canvas.configure(yscrollcommand=customer_scrollbar.set)
        
        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            customer_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        customer_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        customer_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        customer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 存储客户Checkbox变量
        self.customer_vars = {}  # {customer_id: tk.BooleanVar}
        self.customer_checkboxes = {}  # {customer_id: ttk.Checkbutton}
        self.customer_scrollable_frame = customer_scrollable_frame
        self.customer_canvas = customer_canvas  # 保存引用以便更新滚动区域
        
        # 注意：不再使用Listbox，改用Checkbox
        self.customer_listbox = None  # 保持兼容性，但不再使用
        
        # 客户操作按钮
        customer_btn_frame = ttk.Frame(customer_frame)
        customer_btn_frame.grid(row=1, column=2, sticky=tk.W, padx=5)
        
        ttk.Button(customer_btn_frame, text="重置", command=self._reset_customers).pack(pady=2)
        
        # 设备列表区域
        device_frame = ttk.LabelFrame(main_frame, text="设备列表", padding="10")
        device_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 设备列表（Treeview）- 限制高度，确保按钮可见
        device_tree_frame = ttk.Frame(device_frame)
        device_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview - 设置固定高度，避免占用过多空间
        columns = ('customer_name', 'device_code')
        self.device_tree = ttk.Treeview(device_tree_frame, columns=columns, show='headings', height=8)
        self.device_tree.heading('customer_name', text='客户名称')
        self.device_tree.heading('device_code', text='设备编码')
        self.device_tree.column('customer_name', width=300, anchor=tk.W)
        self.device_tree.column('device_code', width=300, anchor=tk.W)  # 改为左对齐
        self.device_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 设备列表滚动条
        device_scrollbar = ttk.Scrollbar(device_tree_frame, orient=tk.VERTICAL, command=self.device_tree.yview)
        device_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.device_tree.config(yscrollcommand=device_scrollbar.set)
        
        # 统计信息
        self.stats_label = ttk.Label(device_frame, text="已选择 0 个客户，0 台设备", font=('Arial', 9))
        self.stats_label.pack(pady=5)
        
        # 按钮区域 - 固定在主容器底部，确保始终可见
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 创建按钮，设置固定大小，确保可见
        ok_button = ttk.Button(button_frame, text="确定", command=self._on_ok, width=12)
        ok_button.pack(side=tk.RIGHT, padx=(5, 5))
        
        cancel_button = ttk.Button(button_frame, text="取消", command=self._on_cancel, width=12)
        cancel_button.pack(side=tk.RIGHT, padx=(0, 5))
    
    def _load_customers(self):
        """加载所有客户列表"""
        try:
            # 显示加载提示
            loading_label = ttk.Label(self.customer_scrollable_frame, text="正在加载客户列表...")
            loading_label.pack(pady=10)
            self.update()
            
            self._ensure_connection()
            cursor = self.db_handler.connection.cursor(dictionary=True)
            
            # 查询所有有效客户
            query = """
                SELECT DISTINCT c.id, c.customer_name
                FROM t_customer c
                INNER JOIN t_device d ON c.id = d.customer_id
                WHERE c.status = 1 AND d.del_status = 1
                ORDER BY c.customer_name
            """
            cursor.execute(query)
            self.all_customers = cursor.fetchall()
            cursor.close()
            
            # 更新客户列表显示
            self._update_customer_listbox()
            
        except Exception as e:
            import traceback
            error_msg = f"加载客户列表失败: {str(e)}\n\n您可以关闭对话框取消操作。"
            print(f"设备筛选对话框 - 加载客户列表错误: {e}")
            print(traceback.format_exc())
            try:
                messagebox.showerror("错误", error_msg)
            except:
                # 如果消息框也无法显示，至少打印错误
                print(error_msg)
            self.all_customers = []
            # 即使出错也允许用户关闭对话框
            self._update_customer_listbox()
    
    def _ensure_connection(self):
        """确保数据库连接有效"""
        if not self.db_handler.connection or not self.db_handler.connection.is_connected():
            self.db_handler.connect()
    
    def _update_customer_listbox(self):
        """更新客户列表显示（使用Checkbox）"""
        # 注意：搜索时不应该清除已选中的客户
        # selected_customer_ids 应该保持不变，只更新当前可见客户的Checkbox显示状态
        
        # 清除现有的Checkbox
        for widget in self.customer_scrollable_frame.winfo_children():
            widget.destroy()
        self.customer_vars.clear()
        self.customer_checkboxes.clear()
        
        # 获取搜索关键词（去除首尾空格）
        search_text = self.customer_search_var.get().strip()
        
        # 过滤客户（只在有搜索关键词时过滤，空字符串显示所有客户）
        filtered_customers = self.all_customers
        if search_text:
            search_text_lower = search_text.lower()
            filtered_customers = [
                c for c in self.all_customers
                if search_text_lower in c['customer_name'].lower()
            ]
        
        # 为每个客户创建Checkbox
        for customer in filtered_customers:
            customer_id = customer['id']
            customer_name = customer['customer_name']
            
            # 创建BooleanVar
            var = tk.BooleanVar()
            
            # 如果之前已选中，恢复选中状态（在设置trace之前设置值，避免触发回调）
            if customer_id in self.selected_customer_ids:
                var.set(True)
            
            # 设置trace回调（在设置值之后，避免初始化时触发）
            var.trace('w', lambda *args, cid=customer_id: self._on_customer_checkbox_changed(cid))
            
            # 创建Checkbutton
            checkbox = ttk.Checkbutton(
                self.customer_scrollable_frame,
                text=customer_name,
                variable=var
            )
            checkbox.pack(anchor=tk.W, pady=2)
            
            self.customer_vars[customer_id] = var
            self.customer_checkboxes[customer_id] = checkbox
        
        # 更新Canvas滚动区域
        self.customer_scrollable_frame.update_idletasks()
        self.customer_canvas.configure(scrollregion=self.customer_canvas.bbox("all"))
    
    def _on_search_changed(self, *args):
        """搜索框内容改变时的回调"""
        # 获取搜索关键词，如果为空或只有空格，不进行过滤
        search_text = self.customer_search_var.get().strip()
        if not search_text:
            # 如果搜索框为空，显示所有客户，不触发数据库查询
            self._update_customer_listbox()
            return
        
        # 搜索时只更新客户列表显示，不更新设备列表
        # 设备列表应该始终显示所有已选中客户的设备，不受搜索影响
        self._update_customer_listbox()
        # 注意：不需要调用 _update_device_list()，因为设备列表应该基于 selected_customer_ids
        # 而 selected_customer_ids 在搜索时不会改变
    
    def _on_customer_checkbox_changed(self, customer_id):
        """客户Checkbox状态改变时的回调"""
        # 获取当前Checkbox的状态
        var = self.customer_vars.get(customer_id)
        if var is None:
            return
        
        is_selected = var.get()
        
        # 更新selected_customer_ids：只更新当前客户的选中状态，保留其他已选中的客户
        if is_selected:
            # 如果选中，添加到列表（如果不在列表中）
            if customer_id not in self.selected_customer_ids:
                self.selected_customer_ids.append(customer_id)
        else:
            # 如果取消选中，从列表中移除
            if customer_id in self.selected_customer_ids:
                self.selected_customer_ids.remove(customer_id)
        
        # 更新设备列表（基于所有已选中的客户，不仅仅是当前可见的）
        self._update_device_list()
    
    def _update_device_list(self):
        """更新设备列表显示"""
        # 清空设备列表
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        if not self.selected_customer_ids:
            self._update_stats()
            return
        
        try:
            self._ensure_connection()
            cursor = self.db_handler.connection.cursor(dictionary=True)
            
            # 查询选中客户的设备（只获取每个device_code对应的最新设备）
            placeholders = ','.join(['%s'] * len(self.selected_customer_ids))
            query = f"""
                WITH LatestDevices AS (
                    SELECT id AS device_id, device_code, customer_id
                    FROM (
                        SELECT id, device_code, customer_id, 
                               ROW_NUMBER() OVER (PARTITION BY device_code ORDER BY create_time DESC, id DESC) AS rn
                        FROM t_device
                        WHERE del_status = 1 
                        AND device_code IS NOT NULL 
                        AND device_code != ''
                        AND customer_id IN ({placeholders})
                    ) AS RankedDevices
                    WHERE rn = 1
                )
                SELECT 
                    c.customer_name,
                    ld.device_code,
                    ld.device_id
                FROM LatestDevices ld
                INNER JOIN t_customer c ON ld.customer_id = c.id
                WHERE c.status = 1
                ORDER BY c.customer_name, ld.device_code
            """
            cursor.execute(query, self.selected_customer_ids)
            devices = cursor.fetchall()
            cursor.close()
            
            # 添加到设备列表
            for device in devices:
                self.device_tree.insert('', tk.END, values=(
                    device['customer_name'],
                    device['device_code']
                ), tags=(device['device_id'],))
            
            # 更新统计信息
            self._update_stats()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载设备列表失败: {str(e)}")
    
    def _update_stats(self):
        """更新统计信息"""
        device_count = len(self.device_tree.get_children())
        customer_count = len(self.selected_customer_ids)
        
        self.stats_label.config(
            text=f"已选择 {customer_count} 个客户，{device_count} 台设备"
        )
    
    def _reset_customers(self):
        """重置客户选择"""
        # 先清空选中列表，避免触发设备列表查询
        self.selected_customer_ids = []
        
        # 清除所有Checkbox的选中状态（批量操作，减少UI更新）
        for var in self.customer_vars.values():
            var.set(False)
        
        # 直接清空设备列表，不查询数据库
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        # 更新统计信息
        self._update_stats()
    
    def _on_ok(self):
        """确定按钮点击"""
        # 获取选中的设备ID
        selected_device_ids = []
        for item in self.device_tree.get_children():
            tags = self.device_tree.item(item, 'tags')
            if tags:
                selected_device_ids.append(int(tags[0]))
        
        # 检查设备数量限制
        if len(selected_device_ids) > self.max_devices:
            messagebox.showerror(
                "设备数量超限",
                f"最多只能选择 {self.max_devices} 台设备，当前选择了 {len(selected_device_ids)} 台。\n请减少选择的客户或设备。"
            )
            return
        
        if not selected_device_ids:
            messagebox.showwarning("警告", "请至少选择一个客户和设备。")
            return
        
        # 获取选中的客户名称
        selected_customer_names = [
            next((c['customer_name'] for c in self.all_customers if c['id'] == cid), f"客户ID:{cid}")
            for cid in self.selected_customer_ids
        ]
        
        self.result = (selected_device_ids, selected_customer_names)
        self.quit()  # 退出主事件循环
        self.destroy()
    
    def _on_cancel(self):
        """取消按钮点击"""
        self.result = None
        self.quit()  # 退出主事件循环
        self.destroy()


def get_device_filter(db_handler, max_devices=200):
    """
    显示设备筛选对话框并返回用户选择的设备。
    
    Args:
        db_handler: 数据库处理器
        max_devices: 最大可选设备数量
    
    Returns:
        tuple: (selected_device_ids, selected_customer_names) or None if canceled.
    """
    dialog = None
    try:
        print("步骤1: 正在创建设备筛选对话框...")
        # 直接创建对话框（作为Tk主窗口，不需要父窗口）
        try:
            dialog = DeviceFilterDialog(None, db_handler, max_devices=max_devices)
            print("步骤2: 设备筛选对话框已创建")
        except Exception as init_error:
            print(f"步骤2失败: 对话框创建时出错: {init_error}")
            import traceback
            print(traceback.format_exc())
            raise
        
        # 强制刷新并显示对话框
        print("步骤3: 正在显示对话框...")
        dialog.update_idletasks()
        
        # 确保对话框可见
        dialog.deiconify()
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)  # 确保对话框在最前
        
        # 强制更新显示
        dialog.update_idletasks()
        dialog.update()
        
        # 验证对话框是否真的可见
        try:
            is_visible = dialog.winfo_viewable()
            print(f"步骤4: 对话框可见性检查: {is_visible}")
            if not is_visible:
                print("警告: 对话框不可见，尝试强制显示...")
                # 尝试将对话框移到屏幕中央并强制显示
                screen_width = dialog.winfo_screenwidth()
                screen_height = dialog.winfo_screenheight()
                x = (screen_width // 2) - 300
                y = (screen_height // 2) - 250
                dialog.geometry(f"600x500+{x}+{y}")
                dialog.deiconify()
                dialog.lift()
                dialog.focus_force()
                dialog.attributes('-topmost', True)
                dialog.update()
                
                # 再次检查
                is_visible = dialog.winfo_viewable()
                print(f"步骤4重试: 对话框可见性检查: {is_visible}")
        except Exception as e:
            print(f"步骤4警告: 无法检查对话框可见性: {e}")
        
        print("步骤5: 设备筛选对话框已显示，等待用户操作...")
        print("提示：如果看不到对话框，请尝试 Alt+Tab 切换窗口，或检查是否被其他窗口遮挡。")
        
        # 启动主事件循环（等待对话框关闭）
        dialog.mainloop()
        
        print("步骤6: 设备筛选对话框已关闭")
        result = dialog.result if dialog else None
    except KeyboardInterrupt:
        # 处理Ctrl+C中断
        print("\n用户中断操作")
        result = None
    except Exception as e:
        import traceback
        print(f"设备筛选对话框错误: {e}")
        print(traceback.format_exc())
        result = None
    finally:
        # 确保对话框被销毁
        try:
            if dialog:
                dialog.quit()  # 退出事件循环
                dialog.destroy()
        except:
            pass
    
    return result

