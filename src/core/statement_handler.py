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
            self._update_statement_sheet(wb[sheet_mapping["statement"]], customer_name, start_date, end_date)

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
            start_date: 开始日期
            end_date: 结束日期
        """
        try:
            
            # 在G3单元格写入开始日期，使用Excel日期格式
            ws['G3'] = start_date
            # 设置日期格式为"2025年7月1日"样式
            ws['G3'].number_format = 'yyyy"年"m"月"d"日"'
            
            # 在H3单元格写入结束日期，使用Excel日期格式
            ws['H3'] = end_date
            # 设置日期格式为"2025年7月31日"样式
            ws['H3'].number_format = 'yyyy"年"m"月"d"日"'
            
            # 在A6单元格写入年月
            ws['A6'] = start_date.strftime('%Y年%m月')
            
            # 收集每日用量数据
            daily_usage = defaultdict(lambda: defaultdict(float))
            oil_names = set()
            
            for device_data in all_devices_data:
                oil_name = device_data['oil_name']
                oil_names.add(oil_name)
                for date, value in device_data['data']:
                    # 确保value是float类型，避免decimal.Decimal和float相加的问题
                    daily_usage[date][oil_name] += float(value)
            

            # 按油品名称排序
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
            start_date: 开始日期
            end_date: 结束日期
        """
        try:
            # 收集月度数据
            monthly_stats = defaultdict(lambda: defaultdict(float))
            for device_data in all_devices_data:
                oil_name = device_data['oil_name']
                for date, value in device_data['data']:
                    month = date.strftime('%Y-%m')
                    # 确保value是float类型，避免decimal.Decimal和float相加的问题
                    monthly_stats[month][oil_name] += float(value)

            # 写入数据
            current_row = 4
            sorted_months = sorted(monthly_stats.keys())
            oil_names = set()
            
            # 收集所有油品名称
            for month_data in monthly_stats.values():
                oil_names.update(month_data.keys())
            
            sorted_oils = sorted(oil_names)
            
            
            # 写入表头
            for col, oil_name in enumerate(sorted_oils, 2):
                ws.cell(row=3, column=col, value=oil_name)

            # 写入每月数据
            for month in sorted_months:
                ws.cell(row=current_row, column=1, value=month)
                month_data = monthly_stats[month]
                for col, oil_name in enumerate(sorted_oils, 2):
                    value = month_data.get(oil_name, 0)
                    ws.cell(row=current_row, column=col, value=round(float(value), 2))
                current_row += 1
                

        except Exception as e:
            print(f"更新每月用量对比工作表时出错: {e}")
            raise

    def _update_statement_sheet(self, ws, customer_name, start_date, end_date):
        """
        更新中润对账单工作表
        
        Args:
            ws: 工作表对象
            customer_name: 客户名称
            start_date: 开始日期
            end_date: 结束日期
        """
        try:
            # 更新客户信息和日期范围
            ws['B2'] = customer_name
            ws['D2'] = f"{start_date.strftime('%Y-%m-%d')}至{end_date.strftime('%Y-%m-%d')}"
            

        except Exception as e:
            print(f"更新中润对账单工作表时出错: {e}")
            raise