import csv
import os
from datetime import timedelta
from collections import defaultdict

from dateutil.relativedelta import relativedelta
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.chart.marker import Marker
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.drawing.line import LineProperties
from openpyxl.styles import Alignment, Font

from .base_report import BaseReportGenerator


class DailyConsumptionErrorReportGenerator(BaseReportGenerator):
    """每日消耗误差报表生成器，专门负责生成设备每日消耗误差报表和图表。
    
    报表基于油桶的原油剩余量计算真实的消耗量，并与订单累积量进行对比，
    以发现消耗误差。计算公式：
    真实消耗量 = 前一天结束库存 - 当天结束库存 + 当天加油量
    """

    def __init__(self):
        """初始化每日消耗误差报表生成器"""
        super().__init__()

    def generate_report(self, inventory_data, error_data, output_file_path, **kwargs):
        """
        生成每日消耗误差报表的实现方法
        
        报表基于油桶的原油剩余量计算真实的消耗量，并与订单累积量进行对比，
        以发现消耗误差。计算公式：
        真实消耗量 = 前一天结束库存 - 当天结束库存 + 当天加油量

        Args:
            inventory_data (list): 库存数据列表
            error_data (dict): 误差数据字典
            output_file_path (str): 输出文件路径
            **kwargs: 其他参数
            
        Returns:
            bool: 报表生成是否成功
        """
        device_code = kwargs.get('device_code')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        oil_name = kwargs.get('oil_name')
        chart_style = kwargs.get('chart_style')
        export_format = kwargs.get('export_format', 'xlsx')
        
        return self.generate_daily_consumption_error_report_with_chart(
            inventory_data, error_data, output_file_path, device_code, start_date, end_date,
            oil_name, chart_style, export_format
        )

    def generate_daily_consumption_error_report_with_chart(
        self,
        inventory_data,
        error_data,
        output_file_path,
        device_code,
        start_date,
        end_date,
        oil_name=None,
        chart_style=None,
        export_format="xlsx",
    ):
        """
        生成包含库存数据和误差分析的Excel报告文件
        
        报表基于油桶的原油剩余量计算真实的消耗量，并与订单累积量进行对比，
        以发现消耗误差。计算公式：
        真实消耗量 = 前一天结束库存 - 当天结束库存 + 当天加油量

        Args:
            inventory_data (list): 库存数据列表，格式为[(date, value), ...]
            error_data (dict): 误差数据字典
            output_file_path (str): 输出文件路径
            device_code (str): 设备编码
            start_date (date): 开始日期
            end_date (date): 结束日期
            oil_name (str): 油品名称
            chart_style (dict): 图表样式配置
            export_format (str): 导出格式，支持xlsx和csv
        """
        try:
            # 确保输出文件路径不重复，如果重复则添加序号
            output_file_path = self._get_unique_filename(output_file_path)
            
            # 验证并清理库存数据
            cleaned_inventory_data = []
            invalid_records = []
            for date, value in inventory_data:
                try:
                    validated_value = self._validate_inventory_value(value)
                    cleaned_inventory_data.append((date, validated_value))
                except ValueError as e:
                    invalid_records.append((date, value, str(e)))
                    print(f"警告：日期 {date} 的数据已跳过 - {str(e)}")

            if invalid_records:
                print("\n无效数据汇总：")
                for date, value, reason in invalid_records:
                    print(f"- {date}: {value} ({reason})")

            # 如果没有有效数据，尝试生成一个带有默认值的图表
            if not cleaned_inventory_data:
                print("警告：没有有效的原油剩余量数据可供处理，将生成默认数据图表")
                # 使用默认数据点，确保能生成图表
                cleaned_inventory_data = [(start_date, 0), (end_date, 0)]
                print(f"使用默认数据点: {cleaned_inventory_data}")

            # 初始化工作簿
            wb = Workbook()
            
            # 补全库存数据
            data_dict = dict(cleaned_inventory_data)
            complete_inventory_data = []
            current_date = start_date

            # 处理空数据情况，避免索引错误
            if cleaned_inventory_data:
                last_inventory = next(iter(cleaned_inventory_data))[1]
            else:
                last_inventory = 0
                print("警告：没有有效的原油剩余量数据可供处理，将生成默认数据图表")
                # 使用默认数据点，确保能生成图表
                cleaned_inventory_data = [(start_date, 0), (end_date, 0)]
                print(f"使用默认数据点: {cleaned_inventory_data}")

            while current_date <= end_date:
                current_inventory = data_dict.get(current_date, last_inventory)
                complete_inventory_data.append([current_date, current_inventory])
                last_inventory = current_inventory
                current_date += timedelta(days=1)

            # Excel处理
            wb = Workbook()
            ws = wb.active
            ws.title = "消耗误差分析"

            # 添加标题行
            oil_name_str = f" {oil_name} " if oil_name else " "
            title = f"{device_code}{oil_name_str}每日消耗误差分析({start_date} - {end_date})"
            ws.append([title])
            # 将合并单元格的宽度增加到18列
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=20)
            ws.cell(row=1, column=1).alignment = Alignment(horizontal="center", wrap_text=True)  # 修复换行参数
            ws.cell(row=1, column=1).font = Font(size=14, bold=True)

            # 添加数据列标题（删除了原油剩余量(L)列）
            ws.append(["日期", "订单累积总量(L)", "库存消耗总量(L)","库存误差(L)\n(消耗量>订单量)", "订单误差(L)\n(订单量>消耗量)"])

            # 准备误差数据
            daily_order_totals = error_data.get('daily_order_totals', {})  # 每日订单累计总量数据
            daily_shortage_errors = error_data.get('daily_shortage_errors', {})  # 每日亏空误差数据（消耗量超过订单量的部分）
            daily_excess_errors = error_data.get('daily_excess_errors', {})  # 每日超额误差数据（订单量超过消耗量的部分）
            daily_consumption = error_data.get('daily_consumption', {})  # 获取每日消耗量数据

            # 写入补全后的数据（删除了原油剩余量列）
            for row in complete_inventory_data:
                date = row[0]
                order_total = daily_order_totals.get(date, 0)
                # 处理可能为字典格式的误差数据
                shortage_data = daily_shortage_errors.get(date, 0)
                excess_data = daily_excess_errors.get(date, 0)
                consumption_data = daily_consumption.get(date, 0)  # 获取每日消耗量
                
                # 如果是字典格式，提取value字段
                if isinstance(shortage_data, dict):
                    shortage_error = shortage_data.get('value', 0)
                else:
                    shortage_error = shortage_data
                    
                if isinstance(excess_data, dict):
                    excess_error = excess_data.get('value', 0)
                else:
                    excess_error = excess_data
                    
                if isinstance(consumption_data, dict):
                    consumption_value = consumption_data.get('value', 0)
                else:
                    consumption_value = consumption_data
                    
                ws.append([date, order_total, consumption_value, shortage_error, excess_error])

            # 调整列宽
            ws.column_dimensions["A"].width = 12  # 日期列宽度
            ws.column_dimensions["B"].width = 15  # 订单累积总量列宽度
            ws.column_dimensions["C"].width = 15  # 库存消耗总量列宽度
            ws.column_dimensions["D"].width = 12  # 亏空误差列宽度
            ws.column_dimensions["E"].width = 12  # 订单误差列宽度

            # 创建图表
            chart = LineChart()
            chart.title = "每日消耗误差分析"
            chart.style = 13
            chart.y_axis.title = "值(L)"
            chart.y_axis.titleLayout = None  # 垂直显示Y轴标题
            chart.x_axis.title = "日期"

            # 设置图表显示数据标签
            # 添加这部分配置来调整x轴日期显示
            chart.x_axis.tickLblSkip = 5  # 每隔5个标签显示一个
            chart.x_axis.tickLblPos = "low"  # 将标签位置调整到底部
            chart.x_axis.textRotation = 0  # 将文本旋转角度设为0度（水平显示）

            # 设置数据范围（现在只有4列数据）
            data_range = Reference(
                ws, min_col=2, min_row=2, max_col=5, max_row=len(complete_inventory_data) + 2
            )
            dates = Reference(ws, min_col=1, min_row=3, max_row=len(complete_inventory_data) + 2)

            # 添加数据到图表
            chart.add_data(data_range, titles_from_data=True)
            chart.set_categories(dates)

            # 修改数据系列的名称，添加注释说明
            # 由于openpyxl的限制，我们不能直接修改已存在的series的title
            # 所以我们保留原来的标题，仅在图例说明中提供详细解释

            # 为不同数据系列设置不同的颜色
            # 订单累积总量 - 淡绿色（与库存报表保持一致）
            chart.series[0].graphicalProperties = GraphicalProperties()
            chart.series[0].graphicalProperties.line = LineProperties(w=2.5 * 12700, solidFill="90EE90")
            chart.series[0].marker = Marker(symbol="circle", size=8)
            
            # 库存消耗总量 - 紫色
            chart.series[1].graphicalProperties = GraphicalProperties()
            chart.series[1].graphicalProperties.line = LineProperties(w=2.5 * 12700, solidFill="800080")
            chart.series[1].marker = Marker(symbol="circle", size=8)
            
            # 亏空误差 - 红色
            chart.series[2].graphicalProperties = GraphicalProperties()
            chart.series[2].graphicalProperties.line = LineProperties(w=2.5 * 12700, solidFill="FF0000")
            chart.series[2].marker = Marker(symbol="circle", size=8)
            
            # 订单误差 - 橙色
            chart.series[3].graphicalProperties = GraphicalProperties()
            chart.series[3].graphicalProperties.line = LineProperties(w=2.5 * 12700, solidFill="FFA500")
            chart.series[3].marker = Marker(symbol="circle", size=8)

            # 恢复图表到初始大小
            chart.width = 30
            chart.height = 15

            # 添加图表到工作表，从F5开始绘制
            ws.add_chart(chart, "F5")
            
            # 在图表下方添加注释说明
            # 计算注释的起始行（数据行数 + 标题行 + 适当间隔）
            data_end_row = len(complete_inventory_data) + 2  # 数据结束行
            annotation_row = data_end_row + 3  # 在数据下方留出一些空间
            
            # 添加图例说明标题
            ws.cell(row=annotation_row, column=1).value = "图例说明："
            ws.cell(row=annotation_row, column=1).font = Font(bold=True)
            
            # 添加库存误差定义
            annotation_row += 1
            ws.cell(row=annotation_row, column=1).value = "库存误差(L)："
            ws.cell(row=annotation_row, column=1).font = Font(bold=True)
            ws.cell(row=annotation_row, column=2).value = "当月原油消耗量超过当月订单累积总量的部分"
            
            # 添加订单误差定义
            annotation_row += 1
            ws.cell(row=annotation_row, column=1).value = "订单误差(L)："
            ws.cell(row=annotation_row, column=1).font = Font(bold=True)
            ws.cell(row=annotation_row, column=2).value = "当月订单累积总量超过当月原油消耗量的部分"
            
            # 添加库存消耗总量定义
            annotation_row += 1
            ws.cell(row=annotation_row, column=1).value = "库存消耗总量(L)："
            ws.cell(row=annotation_row, column=1).font = Font(bold=True)
            ws.cell(row=annotation_row, column=2).value = "基于原油剩余量变化计算出的真实消耗量"

            try:
                wb.save(output_file_path)
                print(f"  每日消耗误差图表已生成并保存为{export_format.upper()}格式")
                return True
            except PermissionError:
                print(
                    f"错误：无法保存文件 '{output_file_path}'，可能是文件正在被其他程序占用。"
                )
                print("请关闭相关文件后重试。")
                raise
            finally:
                # 确保工作簿被关闭
                if wb is not None:
                    try:
                        wb.close()
                    except:
                        pass
        except Exception as e:
            print("发生错误：")
            print(str(e))
            import traceback
            traceback.print_exc()
            raise

    def _validate_inventory_value(self, value):
        """
        验证原油剩余量值是否有效
        - 不允许小于0的值
        - 不允许非数字值
        """
        try:
            float_value = float(value)
            if float_value < 0:
                raise ValueError("原油剩余量不能为负数")
            return float_value
        except (ValueError, TypeError):
            raise ValueError(f"无效的原油剩余量值: {value}")
            
    def _get_unique_filename(self, file_path):
        """
        生成唯一的文件名，如果文件已存在，则添加序号
        
        Args:
            file_path (str): 原始文件路径
            
        Returns:
            str: 唯一的文件路径
        """
        import os
        # 如果文件不存在，直接返回原路径
        if not os.path.exists(file_path):
            return file_path
            
        # 分离文件名和扩展名
        base_name, extension = os.path.splitext(file_path)
        counter = 1
        new_file_path = file_path
        
        # 循环查找未被占用的文件名
        while os.path.exists(new_file_path):
            new_file_path = f"{base_name}({counter}){extension}"
            counter += 1
            
        return new_file_path


class MonthlyConsumptionErrorReportGenerator(BaseReportGenerator):
    """每月消耗误差报表生成器，专门负责生成设备每月消耗误差报表和图表。
    
    报表基于油桶的原油剩余量计算真实的消耗量，并与订单累积量进行对比，
    以发现消耗误差。计算公式：
    真实消耗量 = 前一月结束库存 - 当月结束库存 + 当月加油量
    """

    def __init__(self):
        """初始化每月消耗误差报表生成器"""
        super().__init__()

    def generate_report(self, inventory_data, error_data, output_file_path, **kwargs):
        """
        生成每月消耗误差报表的实现方法
        
        报表基于油桶的原油剩余量计算真实的消耗量，并与订单累积量进行对比，
        以发现消耗误差。计算公式：
        真实消耗量 = 前一月结束库存 - 当月结束库存 + 当月加油量

        Args:
            inventory_data (list): 库存数据列表
            error_data (dict): 误差数据字典
            output_file_path (str): 输出文件路径
            **kwargs: 其他参数
            
        Returns:
            bool: 报表生成是否成功
        """
        device_code = kwargs.get('device_code')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        oil_name = kwargs.get('oil_name')
        chart_style = kwargs.get('chart_style')
        export_format = kwargs.get('export_format', 'xlsx')
        
        return self.generate_monthly_consumption_error_report_with_chart(
            inventory_data, error_data, output_file_path, device_code, start_date, end_date,
            oil_name, chart_style, export_format
        )

    def generate_monthly_consumption_error_report_with_chart(
        self,
        inventory_data,
        error_data,
        output_file_path,
        device_code,
        start_date,
        end_date,
        oil_name=None,
        chart_style=None,
        export_format="xlsx",
    ):
        """
        生成包含库存数据和误差分析的Excel报告文件
        
        报表基于油桶的原油剩余量计算真实的消耗量，并与订单累积量进行对比，
        以发现消耗误差。计算公式：
        真实消耗量 = 前一月结束库存 - 当月结束库存 + 当月加油量

        Args:
            inventory_data (list): 库存数据列表，格式为[(date, value), ...]
            error_data (dict): 误差数据字典
            output_file_path (str): 输出文件路径
            device_code (str): 设备编码
            start_date (date): 开始日期
            end_date (date): 结束日期
            oil_name (str): 油品名称
            chart_style (dict): 图表样式配置
            export_format (str): 导出格式，支持xlsx和csv
        """
        try:
            # 确保输出文件路径不重复，如果重复则添加序号
            output_file_path = self._get_unique_filename(output_file_path)

            # 准备月度数据
            complete_inventory_data = []
            
            # 直接使用error_data中的月份数据，而不是生成日期范围
            # 这样可以确保日期格式完全匹配
            monthly_order_totals = error_data.get('monthly_order_totals', {})
            monthly_shortage_errors = error_data.get('monthly_shortage_errors', {})
            monthly_excess_errors = error_data.get('monthly_excess_errors', {})
            monthly_consumption = error_data.get('monthly_consumption', {})
            
            # 获取所有唯一的月份标签并排序
            all_months = set()
            all_months.update(monthly_order_totals.keys())
            all_months.update(monthly_shortage_errors.keys())
            all_months.update(monthly_excess_errors.keys())
            all_months.update(monthly_consumption.keys())
            
            # 排序月份
            sorted_months = sorted(list(all_months))
            
            # 限制只显示最多12个月的数据
            if len(sorted_months) > 12:
                sorted_months = sorted_months[-12:]
            
            # 为每个唯一月份创建数据点
            for month in sorted_months:
                complete_inventory_data.append([month, 0])

            # Excel处理
            wb = Workbook()
            ws = wb.active
            ws.title = "消耗误差分析"

            # 添加标题行
            oil_name_str = f" {oil_name} " if oil_name else " "
            title = f"{device_code}{oil_name_str}每月消耗误差分析({start_date} - {end_date})"
            ws.append([title])
            # 将合并单元格的宽度增加到18列
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=20)
            ws.cell(row=1, column=1).alignment = Alignment(horizontal="center", wrap_text=True)  # 修复换行参数
            ws.cell(row=1, column=1).font = Font(size=14, bold=True)

            # 添加数据列标题（删除了原油剩余量(L)列）
            ws.append(["月份", "订单累积总量(L)", "库存消耗总量(L)","库存误差(L)\n(消耗量>订单量)", "订单误差(L)\n(订单量>消耗量)"])

            # 写入补全后的数据（删除了原油剩余量列）
            for row in complete_inventory_data:
                month_str = row[0]
                
                # 从误差数据中获取实际值，如果不存在则使用默认值0
                order_total = monthly_order_totals.get(month_str, 0)
                
                # 处理可能为字典格式的误差数据
                shortage_data = monthly_shortage_errors.get(month_str, 0)
                excess_data = monthly_excess_errors.get(month_str, 0)
                consumption_data = monthly_consumption.get(month_str, 0)
                
                # 如果是字典格式，提取value字段
                if isinstance(shortage_data, dict):
                    shortage_error = shortage_data.get('value', 0)
                else:
                    shortage_error = shortage_data
                    
                if isinstance(excess_data, dict):
                    excess_error = excess_data.get('value', 0)
                else:
                    excess_error = excess_data
                    
                if isinstance(consumption_data, dict):
                    consumption_value = consumption_data.get('value', 0)
                else:
                    consumption_value = consumption_data
                    
                ws.append([month_str, order_total, consumption_value, shortage_error, excess_error])

            # 调整列宽
            ws.column_dimensions["A"].width = 12  # 月份列宽度
            ws.column_dimensions["B"].width = 15  # 订单累积总量列宽度
            ws.column_dimensions["C"].width = 15  # 库存消耗总量列宽度
            ws.column_dimensions["D"].width = 12  # 亏空误差列宽度
            ws.column_dimensions["E"].width = 12  # 订单误差列宽度

            # 创建图表
            chart = LineChart()
            chart.title = "每月消耗误差分析"
            chart.style = 13
            chart.y_axis.title = "值(L)"
            chart.y_axis.titleLayout = None  # 垂直显示Y轴标题
            chart.x_axis.title = "月份"

            # 设置图表显示数据标签
            # 添加这部分配置来调整x轴日期显示
            chart.x_axis.tickLblSkip = 1  # 每个标签都显示
            chart.x_axis.tickLblPos = "low"  # 将标签位置调整到底部
            chart.x_axis.textRotation = 0  # 将文本旋转角度设为0度（水平显示）

            # 设置数据范围（现在只有4列数据）
            data_range = Reference(
                ws, min_col=2, min_row=2, max_col=5, max_row=len(complete_inventory_data) + 2
            )
            months = Reference(ws, min_col=1, min_row=3, max_row=len(complete_inventory_data) + 2)

            # 添加数据到图表
            chart.add_data(data_range, titles_from_data=True)
            chart.set_categories(months)

            # 为不同数据系列设置不同的颜色
            # 订单累积总量 - 淡绿色（与库存报表保持一致）
            chart.series[0].graphicalProperties = GraphicalProperties()
            chart.series[0].graphicalProperties.line = LineProperties(w=2.5 * 12700, solidFill="90EE90")
            chart.series[0].marker = Marker(symbol="circle", size=8)
            
            # 库存消耗总量 - 紫色
            chart.series[1].graphicalProperties = GraphicalProperties()
            chart.series[1].graphicalProperties.line = LineProperties(w=2.5 * 12700, solidFill="800080")
            chart.series[1].marker = Marker(symbol="circle", size=8)
            
            # 亏空误差 - 红色
            chart.series[2].graphicalProperties = GraphicalProperties()
            chart.series[2].graphicalProperties.line = LineProperties(w=2.5 * 12700, solidFill="FF0000")
            chart.series[2].marker = Marker(symbol="circle", size=8)
            
            # 订单误差 - 橙色
            chart.series[3].graphicalProperties = GraphicalProperties()
            chart.series[3].graphicalProperties.line = LineProperties(w=2.5 * 12700, solidFill="FFA500")
            chart.series[3].marker = Marker(symbol="circle", size=8)

            # 恢复图表到初始大小
            chart.width = 30
            chart.height = 15

            # 添加图表到工作表，从F5开始绘制
            ws.add_chart(chart, "F5")
            
            # 在图表下方添加注释说明
            # 计算注释的起始行（数据行数 + 标题行 + 适当间隔）
            data_end_row = len(complete_inventory_data) + 2  # 数据结束行
            annotation_row = data_end_row + 3  # 在数据下方留出一些空间
            
            # 添加图例说明标题
            ws.cell(row=annotation_row, column=1).value = "图例说明："
            ws.cell(row=annotation_row, column=1).font = Font(bold=True)
            
            # 添加库存误差定义
            annotation_row += 1
            ws.cell(row=annotation_row, column=1).value = "库存误差(L)："
            ws.cell(row=annotation_row, column=1).font = Font(bold=True)
            ws.cell(row=annotation_row, column=2).value = "当月原油消耗量超过当月订单累积总量的部分"
            
            # 添加订单误差定义
            annotation_row += 1
            ws.cell(row=annotation_row, column=1).value = "订单误差(L)："
            ws.cell(row=annotation_row, column=1).font = Font(bold=True)
            ws.cell(row=annotation_row, column=2).value = "当月订单累积总量超过当月原油消耗量的部分"
            
            # 添加库存消耗总量定义
            annotation_row += 1
            ws.cell(row=annotation_row, column=1).value = "库存消耗总量(L)："
            ws.cell(row=annotation_row, column=1).font = Font(bold=True)
            ws.cell(row=annotation_row, column=2).value = "基于原油剩余量变化计算出的真实消耗量"

            try:
                wb.save(output_file_path)
                print(f"  每月消耗误差图表已生成并保存为{export_format.upper()}格式")
                return True
            except PermissionError:
                print(
                    f"错误：无法保存文件 '{output_file_path}'，可能是文件正在被其他程序占用。"
                )
                print("请关闭相关文件后重试。")
                raise
            finally:
                # 确保工作簿被关闭
                if wb is not None:
                    try:
                        wb.close()
                    except:
                        pass
        except Exception as e:
            print("发生错误：")
            print(str(e))
            import traceback
            traceback.print_exc()
            raise

    def _get_unique_filename(self, file_path):
        """
        生成唯一的文件名，如果文件已存在，则添加序号
        
        Args:
            file_path (str): 原始文件路径
            
        Returns:
            str: 唯一的文件路径
        """
        import os
        # 如果文件不存在，直接返回原路径
        if not os.path.exists(file_path):
            return file_path
            
        # 分离文件名和扩展名
        base_name, extension = os.path.splitext(file_path)
        counter = 1
        new_file_path = file_path
        
        # 循环查找未被占用的文件名
        while os.path.exists(new_file_path):
            new_file_path = f"{base_name}({counter}){extension}"
            counter += 1
            
        return new_file_path

    def _validate_inventory_value(self, value):
        """
        验证原油剩余量值是否有效
        - 不允许小于0的值
        - 不允许非数字值
        """
        try:
            float_value = float(value)
            if float_value < 0:
                raise ValueError("原油剩余量不能为负数")
            return float_value
        except (ValueError, TypeError):
            raise ValueError(f"无效的原油剩余量值: {value}")