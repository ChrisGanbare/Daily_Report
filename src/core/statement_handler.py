import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

from openpyxl import load_workbook
from openpyxl.chart import BarChart, LineChart, Reference


class CustomerStatementGenerator:
    """客户对账单生成器类，负责生成客户对账单Excel报表"""

    def __init__(self):
        """初始化客户对账单生成器"""
        pass

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
            statement_ws = wb["中润对账单"]

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
            if statement_ws._charts:
                for i, chart in enumerate(statement_ws._charts):
                    try:
                        self._update_chart_in_statement(
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

    def _update_chart_in_statement(self, chart, daily_usage_ws, monthly_usage_ws):
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
            # 先更新每日用量明细和每月用量对比工作表
            self._update_daily_usage_sheet(
                wb["每日用量明细"], all_devices_data, start_date, end_date
            )
            self._update_monthly_comparison_sheet(
                wb["每月用量对比"], all_devices_data, start_date, end_date
            )

            # 最后更新中润对账单工作表
            self._update_statement_sheet(
                wb["中润对账单"], all_devices_data, customer_name, start_date, end_date
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
        # 确保start_date和end_date是date对象
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
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

            # 在G3单元格写入开始日期，格式：2025/7/1
            ws["G3"] = start_date.strftime("%Y/%m/%d").replace("/0", "/").lstrip("0")

            # 在G4单元格写入结束日期，格式：2025/7/31
            ws["G4"] = end_date.strftime("%Y/%m/%d").replace("/0", "/").lstrip("0")

            # 在A6单元格写入年月，格式：2025年7月
            ws["A6"] = start_date.strftime("%Y年%m月").replace("年0", "年")

            # 收集每日用量数据，统一使用 float
            # 修改数据结构，使用(设备ID, 油品名称)作为键，确保不同设备的相同油品创建独立列
            daily_usage = defaultdict(lambda: defaultdict(float))
            oil_columns = []  # 存储(设备ID, 油品名称)元组的列表，保持顺序

            # 为每个设备的每种油品创建独立列
            for device_data in all_devices_data:
                device_code = device_data["device_code"]
                oil_name = device_data["oil_name"]
                oil_key = (device_code, oil_name)  # 使用设备ID和油品名称组合作为唯一键

                # 只有当这个设备油品组合还没有添加时才添加
                if oil_key not in oil_columns:
                    oil_columns.append(oil_key)

                for date, value in device_data["data"]:
                    # 确保日期是date对象
                    if isinstance(date, str):
                        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                    else:
                        date_obj = date
                    # 将数值统一转换为 float 类型
                    value = float(value) if value is not None else 0.0
                    daily_usage[date_obj][oil_key] += value

            # 写入日期列 (B列)
            current_date = start_date
            row_index = 6  # 从第6行开始写入数据
            date_list = []

            while current_date <= end_date:
                date_list.append(current_date)
                # 日期格式调整为：7.1
                ws.cell(
                    row=row_index,
                    column=2,
                    value=f"{current_date.month}.{current_date.day}",
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
                # 写入油品名称到第5行，保持油品名称与数据库读取的数据一致
                oil_key = (device_code, oil_name)
                oil_name_cell = ws.cell(row=5, column=col_index)
                if oil_name_cell.coordinate not in ws.merged_cells:
                    oil_name_cell.value = oil_name

                # 写入每日用量数据
                for row_index, date in enumerate(date_list, start=6):
                    usage = daily_usage[date].get(oil_key, 0)
                    cell_value = round(usage, 2)
                    data_cell = ws.cell(row=row_index, column=col_index)
                    if data_cell.coordinate not in ws.merged_cells:
                        data_cell.value = cell_value

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
            ws.cell(
                row=3,
                column=2,
                value=f"({start_date.strftime('%Y.%m.%d')}-{end_date.strftime('%Y.%m.%d')})",
            )

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

                for date, value in device_data["data"]:
                    # 确保日期是date对象
                    if isinstance(date, str):
                        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                    else:
                        date_obj = date
                    month = date_obj.strftime("%Y-%m")
                    # 将数值统一转换为 float 类型
                    value = float(value) if value is not None else 0.0
                    monthly_stats[month][oil_key] += value

            # 写入表头，从第2列（B列之后）开始
            for col_index, (device_code, oil_name) in enumerate(oil_columns, start=2):
                header_cell = ws.cell(row=3, column=col_index)
                if header_cell.coordinate not in ws.merged_cells:
                    header_cell.value = oil_name

            # 写入数据
            current_row = 6
            sorted_months = sorted(monthly_stats.keys())

            for month in sorted_months:
                # 写入月份到B列
                month_cell = ws.cell(row=current_row, column=2)
                if month_cell.coordinate not in ws.merged_cells:
                    month_cell.value = month

                # 写入各设备油品数据
                month_data = monthly_stats[month]
                for col_index, (device_code, oil_name) in enumerate(
                    oil_columns, start=2
                ):
                    oil_key = (device_code, oil_name)
                    value = month_data.get(oil_key, 0)
                    data_cell = ws.cell(row=current_row, column=col_index)
                    if data_cell.coordinate not in ws.merged_cells:
                        data_cell.value = round(float(value), 2)
                current_row += 1

        except Exception as e:
            print(f"更新每月用量对比工作表时出错: {e}")
            raise

    def _collect_oil_types(self, all_devices_data):
        """
        收集所有油品类型

        Args:
            all_devices_data: 所有设备的数据

        Returns:
            list: 排序后的油品类型列表
        """
        oil_types = set()
        for device_data in all_devices_data:
            oil_types.add(device_data["oil_name"])
        return sorted(list(oil_types))

    def _update_statement_sheet(
        self, ws, all_devices_data, customer_name, start_date, end_date
    ):
        """更新对账单工作表"""
        try:
            # 更新标题和日期
            self._write_cell_safe(ws, 5, 1, f"客户名称：{customer_name}")
            self._write_cell_safe(
                ws,
                5,
                5,
                f"统计日期：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
            )

            # 收集所有油品类型
            sorted_oil_types = self._collect_oil_types(all_devices_data)
            print(f"排序后的油品: {sorted_oil_types}")

        except Exception as e:
            print(f"更新对账单工作表时出错: {e}")
            raise
