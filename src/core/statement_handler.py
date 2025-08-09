import os
from datetime import datetime, timedelta
from collections import defaultdict
from openpyxl import load_workbook
from openpyxl.chart import LineChart, BarChart, Reference


class StatementHandler:
    """对账单处理类，负责对账单的生成和处理"""

    def __init__(self):
        """初始化对账单处理器"""
        pass

    def generate_statement_from_template(self, all_devices_data, output_file, customer_name, start_date, end_date):
        """
        基于模板生成对账单Excel报表
        
        Args:
            all_devices_data: 所有设备的数据 [{device_code, oil_name, data, raw_data, columns}, ...]
            output_file: 输出文件路径
            customer_name: 客户名称
            start_date: 开始日期
            end_date: 结束日期
        """
        # 修复模板路径，使用项目根目录下的template目录
        template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'template', 'statement_template.xlsx')

        # 检查模板目录是否存在
        template_dir = os.path.dirname(template_path)
        if not os.path.exists(template_dir):
            try:
                os.makedirs(template_dir)
            except Exception as e:
                raise FileNotFoundError(f"无法创建模板目录: {template_dir}\n错误: {e}")
            raise FileNotFoundError(f"已创建模板目录，请将模板文件放入: {template_dir}")

        if not os.path.exists(template_path):
            raise FileNotFoundError(
                f"模板文件不存在: {template_path}\n"
                f"请确保文件 'statement_template.xlsx' 位于 '{template_dir}' 目录下"
            )

        try:
            # 加载模板工作簿
            wb = load_workbook(template_path)

            # 检查必需的工作表是否存在（支持中英文名称）
            required_sheets_chinese = ["中润对账单", "每日用量明细", "每月用量对比"]
            required_sheets_english = ["Statement", "Daily Usage", "Monthly Comparison"]
            
            # 检查是否存在中文名称的工作表
            missing_sheets_chinese = [name for name in required_sheets_chinese if name not in wb.sheetnames]
            # 检查是否存在英文名称的工作表
            missing_sheets_english = [name for name in required_sheets_english if name not in wb.sheetnames]
            
            # 确定使用哪种命名方式
            if len(missing_sheets_chinese) == 0:  # 中文工作表都存在
                # 使用中文名称
                sheet_mapping = {
                    "statement": "中润对账单",
                    "daily_usage": "每日用量明细",
                    "monthly_comparison": "每月用量对比"
                }
            elif len(missing_sheets_english) == 0:  # 英文工作表都存在
                # 使用英文名称
                sheet_mapping = {
                    "statement": "Statement",
                    "daily_usage": "Daily Usage",
                    "monthly_comparison": "Monthly Comparison"
                }
            else:
                # 混合命名或缺少工作表
                available_sheets = ", ".join(wb.sheetnames)
                missing_chinese_info = f"缺少中文工作表: {', '.join(missing_sheets_chinese)}" if missing_sheets_chinese else ""
                missing_english_info = f"缺少英文工作表: {', '.join(missing_sheets_english)}" if missing_sheets_english else ""
                raise KeyError(
                    f"模板工作表名称不匹配。当前模板包含的工作表: {available_sheets}\n"
                    f"{missing_chinese_info}\n"
                    f"{missing_english_info}\n"
                    f"需要以下中文工作表: {', '.join(required_sheets_chinese)}\n"
                    f"或以下英文工作表: {', '.join(required_sheets_english)}"
                )

            # 更新各工作表
            # 先更新每日用量明细和每月用量对比工作表
            self._update_daily_usage_sheet(wb[sheet_mapping["daily_usage"]], all_devices_data, start_date, end_date)
            self._update_monthly_comparison_sheet(wb[sheet_mapping["monthly_comparison"]], all_devices_data, start_date, end_date)
            
            # 最后更新中润对账单工作表
            self._update_statement_sheet(wb[sheet_mapping["statement"]], all_devices_data, customer_name, start_date, end_date)

            # 保存结果前处理图表相关警告
            for sheet in wb.worksheets:
                if sheet._charts:
                    for chart in sheet._charts:
                        # 清理可能导致警告的图表外部数据引用
                        if hasattr(chart, 'externalData'):
                            chart.externalData = None

            try:
                wb.save(output_file)
                print(f"已生成对账单: {output_file}")
            except PermissionError:
                raise PermissionError(f"无法保存文件，可能被其他程序占用: {output_file}")

        except Exception as e:
            print(f"生成对账单时发生错误: {str(e)}")
            raise

    def _update_daily_usage_sheet(self, ws, all_devices_data, start_date, end_date):
        """
        更新每日用量明细工作表
        
        Args:
            ws: 工作表对象
            all_devices_data: 所有设备的数据
            start_date: 开始日期 (date对象)
            end_date: 结束日期 (date对象)
        """
        try:
            # 确保start_date和end_date是date对象
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                
            # 更新标题日期范围 (第3行)
            ws.cell(row=3, column=2, value=f"({start_date.strftime('%Y.%m.%d')}-{end_date.strftime('%Y.%m.%d')})")

            # 收集每日用量数据，统一使用 float
            daily_usage = defaultdict(lambda: defaultdict(float))
            oil_names = set()

            for device_data in all_devices_data:
                oil_name = device_data['oil_name']
                oil_names.add(oil_name)
                for date, value in device_data['data']:
                    # 确保日期是date对象
                    if isinstance(date, str):
                        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                    else:
                        date_obj = date
                    # 将数值统一转换为 float 类型
                    value = float(value) if value is not None else 0.0
                    daily_usage[date_obj][oil_name] += value

            # 获取排序后的油品名称列表
            sorted_oils = sorted(oil_names)
            
            # 写入日期列 (B列)
            current_date = start_date
            row_index = 6  # 从第6行开始写入数据
            date_list = []
            
            while current_date <= end_date:
                date_list.append(current_date)
                # 日期格式调整为：7.1
                ws.cell(row=row_index, column=2, value=f"{current_date.month}.{current_date.day}")
                current_date += timedelta(days=1)
                row_index += 1
            
            print(f"日期列表长度: {len(date_list)}")
            
            # 清除模板中可能存在的旧数据（C列及之后的列）
            # 从第5行开始清除表头
            # 从第6行开始清除数据
            max_cols = ws.max_column
            if max_cols > 2:  # 如果存在C列及之后的列
                for col in range(3, max_cols + 1):
                    # 清除表头（第5行）
                    cell = ws.cell(row=5, column=col)
                    if not hasattr(cell, 'merged') or not cell.merged:
                        cell.value = None
                    # 清除数据（第6行到第6+日期数量-1行）
                    for row in range(6, 6 + len(date_list)):
                        cell = ws.cell(row=row, column=col)
                        if not hasattr(cell, 'merged') or not cell.merged:
                            cell.value = None
            
            # 为每个油品写入数据
            print(f"排序后的油品: {sorted_oils}")
            for col_index, oil_name in enumerate(sorted_oils, start=3):  # 从第3列开始(C列)
                print(f"  写入油品 {oil_name} 到第{col_index}列")
                # 写入油品名称到第5行
                ws.cell(row=5, column=col_index, value=oil_name)
                
                # 写入每日用量数据
                for row_index, date in enumerate(date_list, start=6):
                    usage = daily_usage[date].get(oil_name, 0)
                    cell_value = round(usage, 2)
                    ws.cell(row=row_index, column=col_index, value=cell_value)
            
            
        except Exception as e:
            print(f"更新每日用量明细工作表时出错: {e}")
            raise

    def _update_monthly_comparison_sheet(self, ws, all_devices_data, start_date, end_date):
        """
        更新每月用量对比工作表
        
        Args:
            ws: 工作表对象
            all_devices_data: 所有设备的数据
            start_date: 开始日期 (date对象)
            end_date: 结束日期 (date对象)
        """
        try:
            # 确保start_date和end_date是date对象
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                
            ws.cell(row=3, column=2, value=f"({start_date.strftime('%Y.%m.%d')}-{end_date.strftime('%Y.%m.%d')})")

            # 收集月度数据
            monthly_stats = defaultdict(lambda: defaultdict(float))
            for device_data in all_devices_data:
                oil_name = device_data['oil_name']
                for date, value in device_data['data']:
                    # 确保日期是date对象
                    if isinstance(date, str):
                        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                    else:
                        date_obj = date
                    month = date_obj.strftime('%Y-%m')
                    monthly_stats[month][oil_name] += float(value) if value is not None else 0.0

            # 写入数据
            current_row = 6
            for month, oil_stats in sorted(monthly_stats.items()):
                ws.cell(row=current_row, column=2, value=month)
                for col, (oil_name, value) in enumerate(sorted(oil_stats.items()), 3):
                    ws.cell(row=current_row, column=col, value=round(value, 2))
                current_row += 1

        except Exception as e:
            print(f"更新每月用量对比工作表时出错: {e}")
            raise

    def _update_statement_sheet(self, ws, all_devices_data, customer_name, start_date, end_date):
        """
        更新对账单工作表
        
        Args:
            ws: 工作表对象
            all_devices_data: 所有设备的数据
            customer_name: 客户名称
            start_date: 开始日期 (date对象)
            end_date: 结束日期 (date对象)
        """
        try:
            # 确保start_date和end_date是date对象
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                
            # 更新客户信息和日期范围
            customer_cell = ws.cell(row=2, column=2)
            date_range_cell = ws.cell(row=2, column=4)
            
            # 检查单元格是否为合并单元格，如果是则不进行写操作
            if not hasattr(customer_cell, 'merged') or not customer_cell.merged:
                customer_cell.value = customer_name
            if not hasattr(date_range_cell, 'merged') or not date_range_cell.merged:
                date_range_cell.value = f"{start_date.strftime('%Y-%m-%d')}至{end_date.strftime('%Y-%m-%d')}"

            # 在此添加更新表格内容的代码
            current_row = 4
            for device_data in all_devices_data:
                device_code = device_data['device_code']
                oil_name = device_data['oil_name']
                for date, value in device_data['data']:
                    # 确保日期是date对象
                    if isinstance(date, str):
                        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                    else:
                        date_obj = date
                    
                    # 写入数据前检查单元格是否为合并单元格
                    date_cell = ws.cell(row=current_row, column=1)
                    device_cell = ws.cell(row=current_row, column=2)
                    oil_cell = ws.cell(row=current_row, column=3)
                    value_cell = ws.cell(row=current_row, column=4)
                    
                    if not hasattr(date_cell, 'merged') or not date_cell.merged:
                        date_cell.value = date_obj
                    if not hasattr(device_cell, 'merged') or not device_cell.merged:
                        device_cell.value = device_code
                    if not hasattr(oil_cell, 'merged') or not oil_cell.merged:
                        oil_cell.value = oil_name
                    if not hasattr(value_cell, 'merged') or not value_cell.merged:
                        value_cell.value = value
                    
                    current_row += 1

        except Exception as e:
            print(f"更新对账单工作表时出错: {e}")
            raise