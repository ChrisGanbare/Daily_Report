import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

from openpyxl import load_workbook
from openpyxl.chart import BarChart, LineChart, Reference

# 修复导入语句，使用正确的相对导入
from ..utils.date_utils import parse_date
from .base_report import BaseReportGenerator


class CustomerStatementGenerator(BaseReportGenerator):
    """客户对账单生成器类，负责生成客户对账单Excel报表"""

    def __init__(self):
        """初始化客户对账单生成器"""
        super().__init__()

    def generate_report(self, statement_data, output_file_path, **kwargs):
        """
        生成对账单报表的实现方法
        
        Args:
            statement_data: 对账单数据
            output_file_path (str): 输出文件路径
            **kwargs: 其他参数
            
        Returns:
            bool: 报表生成是否成功
        """
        # 提取参数
        template_path = kwargs.get('template_path')
        customer_name = kwargs.get('customer_name')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        device_data = kwargs.get('device_data', {})
        
        return self.generate_customer_statement_from_template(
            all_devices_data=device_data,  # 注意参数名称变化
            output_file=output_file_path,  # 注意参数名称变化
            customer_name=customer_name,
            start_date=start_date,
            end_date=end_date
        )

    def _write_cell_safe(self, worksheet, row, column, value):
        """
        安全地写入单元格值，避免对合并单元格进行写操作

        Args:
            worksheet: 工作表对象
            row: 行号（从1开始）
            column: 列号（从1开始）
            value: 要写入的值
        """
        try:
            cell = worksheet.cell(row=row, column=column)
            # 检查单元格是否为合并单元格，如果是则不进行写操作
            if cell.coordinate not in worksheet.merged_cells:
                cell.value = value
        except Exception as e:
            print(f"写入单元格({row}, {column})时出错: {e}")

    def _generate_date_list(self, start_date, end_date):
        """
        生成从开始日期到结束日期的日期列表

        Args:
            start_date: 开始日期 (date对象)
            end_date: 结束日期 (date对象)

        Returns:
            list: 包含所有日期的列表
        """
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        return date_list

    def _update_charts_data_source(self, wb, all_devices_data, start_date, end_date):
        """
        更新工作簿中图表的数据源引用

        Args:
            wb: 工作簿对象
            all_devices_data: 所有设备数据
            start_date: 开始日期
            end_date: 结束日期
        """
        try:
            # 获取工作表引用
            daily_usage_ws = wb["每日用量明细"]
            monthly_usage_ws = wb["每月用量对比"]
            homepage_ws = wb["中润对账单"]

            # 更新每日用量明细工作表中的图表
            if daily_usage_ws._charts:
                for i, chart in enumerate(daily_usage_ws._charts):
                    try:
                        self._update_chart_series_data(
                            chart, daily_usage_ws, "每日用量明细"
                        )
                    except Exception as e:
                        print(f"警告: 更新每日用量明细工作表中的图表{i+1}时出错: {e}")
                        # 保留原图表，不抛出异常

            # 更新每月用量对比工作表中的图表
            if monthly_usage_ws._charts:
                for i, chart in enumerate(monthly_usage_ws._charts):
                    try:
                        self._update_chart_series_data(
                            chart, monthly_usage_ws, "每月用量对比"
                        )
                    except Exception as e:
                        print(f"警告: 更新每月用量对比工作表中的图表{i+1}时出错: {e}")
                        # 保留原图表，不抛出异常

            # 更新中润对账单工作表中的图表
            if homepage_ws._charts:
                for i, chart in enumerate(homepage_ws._charts):
                    try:
                        self._update_chart_in_homepage(
                            chart, daily_usage_ws, monthly_usage_ws
                        )
                    except Exception as e:
                        print(f"警告: 更新中润对账单工作表中的图表{i+1}时出错: {e}")
                        # 保留原图表，不抛出异常

        except Exception as e:
            print(f"更新图表数据源时出错: {e}")
            # 不抛出异常，因为图表问题不应该导致整个流程失败

    def _update_chart_series_data(self, chart, worksheet, sheet_name):
        """
        更新图表系列的数据引用

        Args:
            chart: 图表对象
            worksheet: 工作表对象
            sheet_name: 工作表名称
        """
        try:
            # 检查图表是否有外部数据引用问题
            if hasattr(chart, "externalData") and chart.externalData is not None:
                # 如果externalData的id为None，说明引用失败
                if hasattr(chart.externalData, "id") and chart.externalData.id is None:
                    # 图表引用外部数据失败，保持模板原图不变
                    print(f"警告: 图表引用外部数据失败，保持原图不变")
                    return

            if not hasattr(chart, "series"):
                return

            # 获取油品列表
            oil_names = self._get_oil_names_from_sheet(worksheet, sheet_name)

            # 更新图表系列
            for i, series in enumerate(chart.series):
                if i < len(oil_names):
                    # 更新系列名称
                    if hasattr(series, "tx") and hasattr(series.tx, "strRef"):
                        series.tx.strRef.f = f"{sheet_name}!${chr(65+i+2)}$3"

                    # 更新系列数据范围
                    if hasattr(series, "val") and hasattr(series.val, "numRef"):
                        data_rows = worksheet.max_row - 3
                        if sheet_name == "每日用量明细":
                            series.val.numRef.f = f"{sheet_name}!${chr(65+i+2)}$4:${chr(65+i+2)}${3+data_rows}"
                        elif sheet_name == "每月用量对比":
                            series.val.numRef.f = f"{sheet_name}!${chr(65+i+1)}$4:${chr(65+i+1)}${3+data_rows}"

        except Exception as e:
            print(f"更新图表系列数据时出错: {e}")
            raise

    def _get_oil_names_from_sheet(self, worksheet, sheet_name):
        """
        从工作表中获取油品名称列表

        Args:
            worksheet: 工作表对象
            sheet_name: 工作表名称

        Returns:
            list: 油品名称列表
        """
        oil_names = []
        if sheet_name == "每日用量明细":
            # 从第3行开始查找油品名称
            for col in range(3, worksheet.max_column + 1):
                cell_value = worksheet.cell(row=3, column=col).value
                if cell_value:
                    oil_names.append(cell_value)
        elif sheet_name == "每月用量对比":
            # 从第3行开始查找油品名称
            for col in range(2, worksheet.max_column + 1):
                cell_value = worksheet.cell(row=3, column=col).value
                if cell_value:
                    oil_names.append(cell_value)
        return oil_names

    def _update_chart_in_homepage(self, chart, daily_usage_ws, monthly_usage_ws):
        """
        更新对账单工作表中的图表

        Args:
            chart: 图表对象
            daily_usage_ws: 每日用量明细工作表
            monthly_usage_ws: 每月用量对比工作表
        """
        try:
            # 检查图表是否有外部数据引用问题
            if hasattr(chart, "externalData") and chart.externalData is not None:
                # 如果externalData的id为None，说明引用失败
                if hasattr(chart.externalData, "id") and chart.externalData.id is None:
                    # 图表引用外部数据失败，保持模板原图不变
                    print(f"警告: 对账单图表引用外部数据失败，保持原图不变")
                    return

            # 检查图表标题以确定图表类型
            chart_title = self._get_chart_title(chart)

            print(f"处理图表: {chart_title}")

            # 根据图表标题更新数据源
            if "月度使用量趋势分析" in chart_title:
                # 更新月度使用量趋势分析图表
                self._update_monthly_chart_data(chart, monthly_usage_ws)
            elif "每日使用量" in chart_title:
                # 更新每日使用量图表
                self._update_daily_chart_data(chart, daily_usage_ws)

        except Exception as e:
            print(f"更新对账单图表时出错: {e}")
            raise

    def _get_chart_title(self, chart):
        """
        获取图表标题

        Args:
            chart: 图表对象

        Returns:
            str: 图表标题
        """
        chart_title = ""
        if hasattr(chart, "title") and chart.title:
            if (
                hasattr(chart.title, "tx")
                and hasattr(chart.title.tx, "rich")
                and hasattr(chart.title.tx.rich, "p")
            ):
                try:
                    chart_title = chart.title.tx.rich.p[0].endParaRPr.t
                except:
                    pass
        return chart_title

    def _update_monthly_chart_data(self, chart, monthly_usage_ws):
        """
        更新月度使用量趋势分析图表的数据

        Args:
            chart: 图表对象
            monthly_usage_ws: 每月用量对比工作表
        """
        try:
            if not hasattr(chart, "series"):
                return

            # 获取油品列表
            oil_names = []
            for col in range(2, monthly_usage_ws.max_column + 1):
                cell_value = monthly_usage_ws.cell(row=3, column=col).value
                if cell_value:
                    oil_names.append(cell_value)

            print(f"月度图表油品: {oil_names}")

            # 更新每个系列的数据
            for i, series in enumerate(chart.series):
                if i < len(oil_names):
                    # 更新系列名称
                    if hasattr(series, "tx") and hasattr(series.tx, "strRef"):
                        series.tx.strRef.f = f"每月用量对比!${chr(65+i+1)}$3"

                    # 更新系列数据范围
                    if hasattr(series, "val") and hasattr(series.val, "numRef"):
                        data_rows = monthly_usage_ws.max_row - 3
                        if data_rows > 0:
                            series.val.numRef.f = f"每月用量对比!${chr(65+i+1)}$4:${chr(65+i+1)}${3+data_rows}"

        except Exception as e:
            print(f"更新月度图表数据时出错: {e}")

    def _update_daily_chart_data(self, chart, daily_usage_ws):
        """
        更新每日使用量图表的数据

        Args:
            chart: 图表对象
            daily_usage_ws: 每日用量明细工作表
        """
        try:
            if not hasattr(chart, "series"):
                return

            # 获取油品列表
            oil_names = []
            for col in range(3, daily_usage_ws.max_column + 1):
                cell_value = daily_usage_ws.cell(row=3, column=col).value
                if cell_value:
                    oil_names.append(cell_value)

            print(f"每日图表油品: {oil_names}")

            # 更新每个系列的数据
            for i, series in enumerate(chart.series):
                if i < len(oil_names):
                    # 更新系列名称
                    if hasattr(series, "tx") and hasattr(series.tx, "strRef"):
                        series.tx.strRef.f = f"每日用量明细!${chr(65+i+2)}$3"

                    # 更新系列数据范围
                    if hasattr(series, "val") and hasattr(series.val, "numRef"):
                        data_rows = daily_usage_ws.max_row - 5  # 从第6行开始数据
                        if data_rows > 0:
                            series.val.numRef.f = f"每日用量明细!${chr(65 + i + 2)}$6:${chr(65 + i + 2)}${5 + data_rows}"

        except Exception as e:
            print(f"更新每日图表数据时出错: {e}")

    def generate_customer_statement_from_template(
        self, all_devices_data, output_file, customer_name, start_date, end_date
    ):
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
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "template",
            "statement_template.xlsx",
        )

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

        wb = None
        try:
            # 加载模板工作簿
            wb = load_workbook(template_path)

            # 检查必需的工作表是否存在
            required_sheets = ["中润对账单", "每日用量明细", "每月用量对比"]
            missing_sheets = [
                name for name in required_sheets if name not in wb.sheetnames
            ]

            if missing_sheets:
                available_sheets = ", ".join(wb.sheetnames)
                raise KeyError(
                    f"模板工作表不完整。当前模板包含的工作表: {available_sheets}\n"
                    f"缺少工作表: {', '.join(missing_sheets)}\n"
                    f"需要以下工作表: {', '.join(required_sheets)}"
                )

            # 更新各工作表
            # 先更新每日用量明细和每月用量对比工作表（数据工作表）
            self._update_daily_usage_sheet(
                wb["每日用量明细"], all_devices_data, start_date, end_date
            )
            self._update_monthly_comparison_sheet(
                wb["每月用量对比"], all_devices_data, start_date, end_date
            )

            # 最后更新中润对账单工作表（主页工作表）- 只更新最基本的信息
            self._update_homepage_sheet_minimal(
                wb["中润对账单"], customer_name, start_date, end_date
            )

            # 更新图表数据源引用
            self._update_charts_data_source(wb, all_devices_data, start_date, end_date)

            # 保存结果前处理图表相关属性
            for sheet in wb.worksheets:
                if sheet._charts:
                    for chart in sheet._charts:
                        # 清理可能导致警告的图表外部数据引用
                        if (
                            hasattr(chart, "externalData")
                            and chart.externalData is not None
                        ):
                            # 如果externalData的id为None，将其设置为空字符串以避免警告
                            if (
                                hasattr(chart.externalData, "id")
                                and chart.externalData.id is None
                            ):
                                chart.externalData.id = ""
                            # 如果externalData没有id属性或者id为空列表，设置为空字符串
                            elif (
                                hasattr(chart.externalData, "id")
                                and not chart.externalData.id
                            ):
                                chart.externalData.id = ""

            try:
                wb.save(output_file)
                print(f"已生成对账单: {output_file}")
            except PermissionError:
                raise PermissionError(
                    f"无法保存文件，可能被其他程序占用: {output_file}"
                )

        except Exception as e:
            print(f"生成对账单时发生错误: {str(e)}")
            raise
        finally:
            # 确保工作簿被关闭
            if wb is not None:
                try:
                    wb.close()
                    # 添加短暂延迟确保文件被系统完全释放
                    time.sleep(0.1)
                except:
                    pass

    def _prepare_date_range(self, start_date, end_date):
        """
        准备日期范围，确保输入是date对象

        Args:
            start_date: 开始日期 (date对象或字符串)
            end_date: 结束日期 (date对象或字符串)

        Returns:
            tuple: (start_date, end_date) 日期对象元组
        """
        from src.utils.date_utils import parse_date
        
        # 确保start_date和end_date是date对象
        if isinstance(start_date, str):
            start_date = parse_date(start_date).date()
        if isinstance(end_date, str):
            end_date = parse_date(end_date).date()
        return start_date, end_date

    def _clear_old_data(self, worksheet, start_row, num_rows, start_col=3):
        """
        清除工作表中的旧数据

        Args:
            worksheet: 工作表对象
            start_row: 开始行号
            num_rows: 需要清除的行数
            start_col: 开始列号（默认为3，即C列）
        """
        max_cols = worksheet.max_column
        if max_cols >= start_col:
            for col in range(start_col, max_cols + 1):
                # 清除数据
                for row in range(start_row, start_row + num_rows):
                    cell = worksheet.cell(row=row, column=col)
                    if cell.coordinate not in worksheet.merged_cells:
                        cell.value = None

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
            start_date, end_date = self._prepare_date_range(start_date, end_date)
            
            # 检查日期跨度是否超过31天
            date_span = (end_date - start_date).days + 1
            if date_span > 31:
                raise ValueError(f"日期跨度不能超过31天，当前跨度为{date_span}天")

            # 在G3单元格写入开始日期，格式：2025/7/1
            self._write_cell_safe(
                ws, 3, 7, f"{start_date.year}/{start_date.month}/{start_date.day}"
            )
            # 在H3单元格写入结束日期
            self._write_cell_safe(
                ws, 3, 8, f"{end_date.year}/{end_date.month}/{end_date.day}"
            )

            # 收集所有设备的油品信息，使用(device_code, oil_name)作为复合键
            # 确保每个设备的每种油品只出现一次
            daily_usage = defaultdict(lambda: defaultdict(float))
            oil_columns = []  # 保持油品列的顺序

            for device_data in all_devices_data:
                device_code = device_data["device_code"]
                oil_name = device_data["oil_name"]
                oil_key = (device_code, oil_name)

                # 只有当这个设备油品组合还没有添加时才添加
                if oil_key not in oil_columns:
                    oil_columns.append(oil_key)

                # 使用正确的数据源（对账单应该使用油加注值，而不是原油剩余比例）
                data_source = device_data.get("daily_usage_data", None)
                if data_source is None:
                    data_source = device_data["data"]
                
                for date, value in data_source:
                    # 确保日期是date对象
                    if isinstance(date, str):
                        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                    else:
                        date_obj = date
                    # 将数值统一转换为 float 类型
                    value = float(value) if value is not None else 0.0
                    daily_usage[date_obj][oil_key] += value
                    
                    # 添加调试信息，帮助追踪特定设备的数据
                    if device_code == "MO24111301600002" and date_obj == datetime(2025, 7, 1).date():
                        print(f"设备 {device_code} 在 {date_obj} 的数据: 原始值={value}, 累计值={daily_usage[date_obj][oil_key]}")

            # 写入日期列 (B列)
            current_date = start_date
            row_index = 6  # 从第6行开始写入数据
            date_list = []

            while current_date <= end_date:
                date_list.append(current_date)
                # 日期格式调整为：7.1
                self._write_cell_safe(
                    ws,
                    row_index,
                    2,
                    f"{current_date.month}.{current_date.day}",
                )
                current_date += timedelta(days=1)
                row_index += 1

            print(f"日期列表长度: {len(date_list)}")

            # 清除模板中可能存在的旧数据（C列及之后的列）
            # 从第5行开始清除表头
            # 从第6行开始清除数据
            self._clear_old_data(ws, 5, 1, 3)  # 清除表头（第5行）
            self._clear_old_data(
                ws, 6, len(date_list), 3
            )  # 清除数据（第6行到第6+日期数量-1行）

            # 为每个设备的油品写入数据
            print(f"设备油品组合: {oil_columns}")
            for col_index, (device_code, oil_name) in enumerate(
                oil_columns, start=3
            ):  # 从第3列开始(C列)
                print(f"  写入设备 {device_code} 的油品 {oil_name} 到第{col_index}列")
                # 写入油品名称到第5行，格式为：设备编码\n油品名称
                oil_key = (device_code, oil_name)
                self._write_cell_safe(ws, 5, col_index, f"{device_code}\n{oil_name}")

                # 写入每日用量数据
                for row_index, date in enumerate(date_list, start=6):
                    usage = daily_usage[date].get(oil_key, 0)
                    cell_value = round(usage, 2)
                    self._write_cell_safe(ws, row_index, col_index, cell_value)
                    
                    # 添加调试信息，帮助追踪特定设备的数据写入
                    if device_code == "MO24111301600002" and date == datetime(2025, 7, 31).date():
                        print(f"写入设备 {device_code} 在 {date} 的数据: 值={cell_value}")

        except Exception as e:
            print(f"更新每日用量明细工作表时出错: {e}")
            raise

    def _update_monthly_comparison_sheet(
        self, ws, all_devices_data, start_date, end_date
    ):
        """
        更新每月用量对比工作表

        Args:
            ws: 工作表对象
            all_devices_data: 所有设备的数据
            start_date: 开始日期 (date对象)
            end_date: 结束日期 (date对象)
        """
        try:
            start_date, end_date = self._prepare_date_range(start_date, end_date)

            # 构建显示日期范围的字符串
            # 在A1单元格写入截止日期信息
            cell = ws.cell(row=1, column=1)
            cell.value = f"截止日期：{end_date.strftime('%Y年%m月%d日')}"
            # 设置对齐方式为靠右居中
            from openpyxl.styles import Alignment
            cell.alignment = Alignment(horizontal='right', vertical='center')
            # 合并A1到I1单元格
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=9)

            # 收集月度数据
            # 修改数据结构，使用(设备ID, 油品名称)作为键，确保不同设备的相同油品创建独立列
            monthly_stats = defaultdict(lambda: defaultdict(float))
            oil_columns = []  # 存储(设备ID, 油品名称)元组的列表，保持顺序

            # 为每个设备的每种油品创建独立列
            for device_data in all_devices_data:
                device_code = device_data["device_code"]
                oil_name = device_data["oil_name"]
                oil_key = (device_code, oil_name)  # 使用设备ID和油品名称组合作为唯一键

                # 只有当这个设备油品组合还没有添加时才添加
                if oil_key not in oil_columns:
                    oil_columns.append(oil_key)

                # 使用正确的数据源（对账单应该使用油加注值，而不是原油剩余比例）
                for date, value in device_data.get("monthly_usage_data", device_data["data"]):
                    # 确保日期是date对象
                    if isinstance(date, str):
                        # 处理不同格式的日期字符串
                        # monthly_usage_data中的日期格式是"YYYY-MM"（例如"2025-07"）
                        # 而data中的日期可能是完整日期格式
                        date_obj = datetime.strptime(date, "%Y-%m").date()

                    else:
                        print(f"方法名: _update_monthly_comparison_sheet")
                        exit()

                    # 格式化月份为"YYYY-MM"用于键值
                    month = date_obj.strftime("%Y-%m")
                    # 将数值统一转换为 float 类型
                    value = float(value) if value is not None else 0.0
                    monthly_stats[month][oil_key] += value

            # 按照新要求写入数据
            # A列从A7开始写入设备编码
            # B列从B7开始写入油品名称
            # C列从C6开始写入月份（格式如：7月），从C7开始写入该行设备该月用量之和
            current_row = 7
            
            # 获取所有月份并排序
            sorted_months = sorted(monthly_stats.keys())
            
            # 写入月份标题到C6单元格开始
            for i, month in enumerate(sorted_months):
                # 从C6开始写入月份，格式化为"7月"这样的形式
                month_cell = ws.cell(row=6, column=3+i)
                # 从"2023-07"格式提取月份并添加"月"字
                month_name = str(int(month.split("-")[1])) + "月"
                month_cell.value = month_name
            
            # 为每个设备和油品组合写入数据
            for device_code, oil_name in oil_columns:
                oil_key = (device_code, oil_name)
                
                # A列写入设备编码
                device_cell = ws.cell(row=current_row, column=1)
                device_cell.value = device_code
                
                # B列写入油品名称
                oil_cell = ws.cell(row=current_row, column=2)
                oil_cell.value = oil_name
                
                # 从C列开始写入各月份的用量数据
                for i, month in enumerate(sorted_months):
                    month_data = monthly_stats[month]
                    value = month_data.get(oil_key, 0)
                    data_cell = ws.cell(row=current_row, column=3+i)
                    data_cell.value = round(float(value), 2)
                    
                current_row += 1

        except Exception as e:
            print(f"更新每月用量对比工作表时出错: {e}")
            raise

    def _update_homepage_sheet_minimal(self, ws, customer_name, start_date, end_date):
        """
        最小化更新中润对账单工作表（主页），只更新最基本的信息
        
        Args:
            ws: 工作表对象
            customer_name: 客户名称
            start_date: 开始日期
            end_date: 结束日期
        """
        try:
            # 只更新客户名称和统计日期等最基本的信息
            self._write_cell_safe(ws, 5, 1, f"客户名称：{customer_name}")
            self._write_cell_safe(
                ws,
                5,
                5,
                f"统计日期：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
            )
            
            # 不再进行其他操作，最大程度保护模板中的样式和元素

        except Exception as e:
            print(f"最小化更新中润对账单工作表时出错: {e}")
            raise