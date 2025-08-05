import re
import os
import json
import mysql.connector
from openpyxl import load_workbook, Workbook
from openpyxl.chart import LineChart, Reference, BarChart
from openpyxl.styles import Alignment, PatternFill, Font
from openpyxl.chart.marker import Marker
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.drawing.line import LineProperties
from openpyxl.utils import get_column_letter
from tkinter import Tk
from datetime import datetime, date
from collections import defaultdict
from tkinter.filedialog import askopenfilename, askdirectory
from datetime import datetime, timedelta
import traceback
import csv
from cryptography.fernet import Fernet

def validate_inventory_value(value):
    """
    验证库存值是否有效
    - 允许大于100的值
    - 不允许小于0的值
    - 不允许非数字值
    """
    try:
        float_value = float(value)
        if float_value < 0:
            raise ValueError("库存值不能为负数")
        return float_value
    except (ValueError, TypeError):
        raise ValueError(f"无效的库存值: {value}")


def validate_file_name(file_name):
    """
    验证文件名称是否符合规范
    规范格式：设备使用油品名称_设备编码_月份
    示例：AW46抗磨液压油_TW24011700700016_202506.xlsx
    """
    try:
        if not file_name.endswith(".xlsx"):
            raise ValueError("文件扩展名必须为 .xlsx")

        base_name = os.path.splitext(file_name)[0]
        parts = base_name.split("_")
        if len(parts) != 3:
            raise ValueError(f"文件名称组成部分的数量错误，当前为 {len(parts)} 部分，应为 3 部分")

        if "_" not in file_name:
            raise ValueError("文件名称的连接符必须为下划线 '_'")

        # 验证设备编码格式（假设设备编码有固定格式）
        device_code = parts[1]
        if not re.match(r"^[A-Z0-9]+$", device_code):
            raise ValueError("设备编码格式不正确")

        # 验证月份格式
        month = parts[2]
        if not re.match(r"^\d{6}$", month):
            raise ValueError("月份格式不正确，应为YYYYMM格式")

        return True
    except ValueError as e:
        print(f"文件名验证失败: {e}")
        return False


def fetch_inventory_data_from_db(connection, query):
    """
    从数据库获取库存数据
    """
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description]
        print(f"查询返回 {len(results)} 条记录")
        
        # 处理数据
        data = {}
        for row in results:
            row_dict = dict(zip(columns, row))
            order_time = row_dict.get('加注时间')
            oil_remaining = row_dict.get('原油剩余比例', 0) if row_dict.get('原油剩余比例') is not None else 0
            
            if isinstance(order_time, datetime):
                order_date = order_time.date()
                if order_date not in data or order_time > data[order_date]["datetime"]:
                    data[order_date] = {"datetime": order_time, "oil_remaining": oil_remaining}
        
        # 转换为与原来read_inventory_data函数相同的格式
        result = [(date, record["oil_remaining"] * 100) for date, record in sorted(data.items())]
        print("\n步骤2：库存数据读取完成。")
        return result, columns, results
    except mysql.connector.Error as err:
        print(f"数据库查询失败: {err}")
        exit(1)
    finally:
        if cursor:
            cursor.close()


def get_customer_name_by_device_code(connection, device_code):
    """
    根据设备编号获取客户名称
    """
    cursor = None
    try:
        cursor = connection.cursor()
        query = """
        SELECT c.customer_name
        FROM oil.t_device d
        LEFT JOIN oil.t_customer c ON d.customer_id = c.id
        LEFT JOIN (
            SELECT ta.*
            FROM oil.t_oil_type ta
            INNER JOIN (
                SELECT device_id, max(id) AS id
                FROM oil.t_oil_type
                WHERE status=1
                GROUP BY device_id
            ) tb ON ta.id = tb.id
        ) ot ON d.id = ot.device_id
        LEFT JOIN oil.t_device_oil o ON ot.id = o.oil_type_id
        WHERE d.device_code = %s
        AND d.del_status = 1
        AND o.STATUS = 1
        AND ot.STATUS = 1
        """
        cursor.execute(query, (device_code,))
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        else:
            print(f"警告：未找到设备编号 {device_code} 对应的客户信息")
            return "未知客户"
    except mysql.connector.Error as err:
        print(f"通过设备编号查询客户名称失败: {err}")
        print(f"可能的原因：")
        print("1. 数据库连接异常")
        print("2. t_device、t_customer表不存在或表结构不正确")
        print("3. 设备编号不存在")
        print("4. 数据库权限不足")
        print("5. 设备与客户之间没有建立关联关系")
        return "未知客户"
    except Exception as e:
        print(f"查询客户名称时发生未知错误: {e}")
        return "未知客户"
    finally:
        if cursor:
            cursor.close()


def get_customer_id(connection, device_id):
    """
    根据设备ID获取客户ID
    """
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT customer_id FROM oil.t_device WHERE id = %s", (device_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except mysql.connector.Error as err:
        print(f"查询客户ID失败: {err}")
        return None
    finally:
        if cursor:
            cursor.close()


def batch_query_from_config(config_file):
    """
    从配置文件中批量读取查询条件并执行查询
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        db_config = config.get("db_config", {})
        queries = config.get("queries", [])
        
        if not db_config or not queries:
            print("配置文件格式错误或缺少必要配置")
            return []
        
        # 连接数据库
        connection = mysql.connector.connect(**db_config)
        
        results = []
        for query_config in queries:
            table_name = query_config.get("table_name")
            conditions = query_config.get("conditions", [])
            
            # 构建查询语句
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM {table_name} WHERE {where_clause}"
            
            print(f"执行查询: {query}")
            
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            results.append({
                "table_name": table_name,
                "columns": columns,
                "data": result
            })
            
            cursor.close()
        
        connection.close()
        return results
        
    except Exception as e:
        print(f"批量查询执行失败: {e}")
        return []


def connect_to_database(db_config):
    """
    连接到数据库
    """
    try:
        connection = mysql.connector.connect(**db_config)
        print("数据库连接成功")
        return connection
    except mysql.connector.Error as err:
        print(f"数据库连接失败: {err}")
        exit(1)


def read_devices_from_csv(csv_file):
    """
    从CSV文件读取设备信息，支持多种编码格式
    """
    devices = []
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
    
    print(f"正在尝试读取设备信息文件: {csv_file}")
    
    # 检查文件是否存在
    if not os.path.exists(csv_file):
        print(f"错误：设备信息文件不存在: {csv_file}")
        return []
    
    # 检查文件是否为空
    if os.path.getsize(csv_file) == 0:
        print(f"错误：设备信息文件为空: {csv_file}")
        return []
    
    # 尝试不同的编码格式
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                # 尝试读取文件内容
                content = f.read()
                if not content.strip():
                    print(f"警告：使用 {encoding} 编码读取的文件内容为空")
                    continue
                
                # 重新打开文件用于CSV读取
                f.seek(0)
                reader = csv.DictReader(f)
                
                # 检查是否有列标题
                if not reader.fieldnames:
                    print(f"警告：使用 {encoding} 编码未能正确识别CSV列标题")
                    continue
                
                # 验证列标题是否包含必要字段
                required_fields = {'device_no', 'start_date', 'end_date'}
                if not all(field in reader.fieldnames for field in required_fields):
                    print(f"警告：CSV文件列标题不完整，缺少必要字段: {required_fields - set(reader.fieldnames)}")
                    continue
                
                # 读取数据行
                row_count = 0
                for row in reader:
                    devices.append(row)
                    row_count += 1
                
                if row_count == 0:
                    print(f"警告：使用 {encoding} 编码读取的CSV文件没有数据行")
                else:
                    print(f"成功使用 {encoding} 编码读取设备信息文件，共读取 {row_count} 行设备数据")
                    print(f"CSV列标题: {', '.join(reader.fieldnames)}")
                    return devices
                    
        except UnicodeDecodeError as e:
            print(f"使用 {encoding} 编码读取文件失败: {str(e)}")
            continue
        except csv.Error as e:
            print(f"使用 {encoding} 编码解析CSV文件失败: {str(e)}")
            continue
        except Exception as e:
            print(f"使用 {encoding} 编码读取文件时发生未知错误: {str(e)}")
            continue
    
    # 如果所有编码都失败了
    supported_encodings = ", ".join(encodings)
    print(f"错误：无法使用任何支持的编码格式读取设备信息文件")
    print(f"支持的编码格式: {supported_encodings}")
    print(f"请确保设备信息文件是有效的CSV格式，并使用上述编码之一")
    print(f"建议: 尝试用记事本或Excel重新保存为UTF-8编码的CSV文件")
    return []


def get_device_id_by_no(connection, device_no, device_query_template):
    """
    根据设备编号查询设备ID，如果有多个相同设备编号，则返回create_time最新的记录
    """
    cursor = None
    try:
        cursor = connection.cursor()
        # 使用参数化查询防止SQL注入
        cursor.execute(device_query_template, (device_no,))
        result = cursor.fetchone()
        return result[0] if result else None
    except mysql.connector.Error as err:
        print(f"查询设备ID失败: {err}")
        return None
    finally:
        if cursor:
            cursor.close()


def generate_query_for_device(inventory_query_template, device_id, start_date, end_date):
    """
    根据设备ID和日期范围生成查询语句

    Args:
        inventory_query_template: SQL模板字符串
        device_id: 设备ID
        start_date: 开始日期 (datetime.date)
        end_date: 结束日期 (datetime.date)
    """
    # 将日期转换为字符串格式
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # 计算下一个月的第一天作为结束条件
    next_month = (end_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    end_condition = next_month.strftime('%Y-%m-%d')

    # 使用格式化后的字符串生成查询
    query = inventory_query_template.format(
        device_id=device_id,
        start_date=start_date_str,
        end_condition=end_condition
    )

    return query


def validate_date(date_string):
    """
    验证日期字符串格式是否正确 (支持 YYYY-MM-DD 和 YYYY/M/D 格式)
    """
    try:
        # 尝试解析标准的 YYYY-MM-DD 格式
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        pass
    
    try:
        # 尝试解析 YYYY/M/D 格式
        datetime.strptime(date_string, '%Y/%m/%d')
        return True
    except ValueError:
        pass
    
    return False


def parse_date(date_string):
    """
    解析日期字符串，支持多种日期格式
    """
    try:
        # 尝试解析标准的 YYYY-MM-DD 格式
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        pass
    
    try:
        # 尝试解析 YYYY/M/D 格式
        return datetime.strptime(date_string, '%Y/%m/%d').date()
    except ValueError:
        pass
    
    # 如果以上两种格式都不匹配，抛出异常
    raise ValueError(f"日期格式错误: {date_string}。期望格式: 'YYYY-MM-DD' 或 'YYYY/M/D'")


def generate_excel_with_chart(data, output_file, device_code, start_date, end_date,
                            chart_style=None, export_format='xlsx'):
    """
    根据数据生成折线图并保存为Excel文件
    """
    try:
        # 验证并清理数据
        cleaned_data = []
        invalid_records = []
        for date, value in data:
            try:
                validated_value = validate_inventory_value(value)
                if validated_value > 100:
                    print(f"提示：日期 {date} 的库存值 {validated_value}% 超过100%")
                cleaned_data.append((date, validated_value))
            except ValueError as e:
                invalid_records.append((date, value, str(e)))
                print(f"警告：日期 {date} 的数据已跳过 - {str(e)}")

        if invalid_records:
            print("\n无效数据汇总：")
            for date, value, reason in invalid_records:
                print(f"- {date}: {value} ({reason})")

        # 如果没有有效数据，尝试生成一个带有默认值的图表
        if not cleaned_data:
            print("警告：没有有效的库存数据可供处理，将生成默认数据图表")
            # 使用默认数据点，确保能生成图表
            cleaned_data = [(start_date, 0), (end_date, 0)]
            print(f"使用默认数据点: {cleaned_data}")

        # 处理不同导出格式
        if export_format.lower() == 'csv':
            with open(output_file.replace('.xlsx', '.csv'), 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['日期', '库存百分比'])
                writer.writerows(cleaned_data)
            print(f"数据已导出为CSV格式：{output_file.replace('.xlsx', '.csv')}")
            return

        # 补全数据
        data_dict = dict(cleaned_data)
        complete_data = []
        current_date = start_date
        last_inventory = next(iter(cleaned_data))[1] if cleaned_data else 0

        while current_date <= end_date:
            current_inventory = data_dict.get(current_date, last_inventory)
            complete_data.append([current_date, current_inventory])
            last_inventory = current_inventory
            current_date += timedelta(days=1)

        # Excel处理
        wb = Workbook()
        ws = wb.active
        ws.title = "库存数据"

        # 添加标题行
        title = f"{device_code}每日库存余量变化趋势({start_date} - {end_date})"
        ws.append([title])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=2)
        ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")

        # 添加数据列标题
        ws.append(["日期", "库存百分比"])

        # 写入补全后的数据
        for row in complete_data:
            ws.append(row)

        # 创建图表
        chart = LineChart()
        chart.title = "每日库存余量变化趋势"
        chart.style = 13
        chart.y_axis.title = "库存百分比"
        chart.x_axis.title = "日期"

        # 添加这部分配置来调整x轴日期显示
        chart.x_axis.tickLblSkip = 3  # 每隔3个标签显示一个
        chart.x_axis.tickLblPos = "low"  # 将标签位置调整到底部
        chart.x_axis.textRotation = 0  # 将文本旋转角度设为0度（水平显示）

        # 设置数据范围
        data_range = Reference(ws, min_col=2, min_row=2, max_col=2, max_row=len(complete_data) + 2)
        dates = Reference(ws, min_col=1, min_row=3, max_row=len(complete_data) + 2)

        # 添加数据到图表
        chart.add_data(data_range, titles_from_data=True)
        chart.set_categories(dates)

        # 应用图表样式
        if chart_style:
            marker_style = chart_style.get('marker_style', 'circle')
            marker_size = chart_style.get('marker_size', 8)
            line_color = chart_style.get('line_color', '0000FF')
            line_width = chart_style.get('line_width', 2.5)

            series = chart.series[0]
            series.graphicalProperties = GraphicalProperties()
            series.graphicalProperties.line = LineProperties(w=line_width * 12700, solidFill=line_color)
            series.marker = Marker(symbol=marker_style, size=marker_size)
        else:
            # 默认样式
            chart.series[0].marker = Marker(symbol='circle', size=8)

        # 添加图表到工作表
        ws.add_chart(chart, "E5")

        try:
            wb.save(output_file)
            print(f"步骤3：库存余量图表已生成并保存为{export_format.upper()}格式")
        except PermissionError:
            print(f"错误：无法保存文件 '{output_file}'，可能是文件正在被其他程序占用。")
            print("请关闭相关文件后重试。")
            exit(1)
    except Exception as e:
        print("发生错误：")
        print(traceback.format_exc())
        exit(1)


def generate_enhanced_excel(all_devices_data, output_file, customer_name, start_date, end_date):
    """
    生成增强版Excel报表

    Args:
        all_devices_data: 所有设备的数据 [{device_code, oil_name, data, raw_data, columns}, ...]
        output_file: 输出文件路径
        customer_name: 客户名称
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        # 创建工作簿
        wb = Workbook()
        wb.remove(wb.active)  # 删除默认工作表

        # 按设备分组处理数据
        device_groups = defaultdict(list)
        for device_data in all_devices_data:
            device_groups[device_data['device_code']].append(device_data)

        # 创建工作表
        sheet_creators = {
            "中润对账单": create_statement_sheet,
            "订单明细": create_order_details_sheet,
            "每日用量明细": create_daily_usage_sheet,
            "每月用量对比": create_monthly_comparison_sheet
        }

        # 调用各个工作表创建函数
        oil_data = {}
        for sheet_name, creator_func in sheet_creators.items():
            if sheet_name == "中润对账单":
                oil_data = creator_func(wb, all_devices_data, customer_name, start_date, end_date)
            else:
                creator_func(wb, all_devices_data, start_date, end_date)

        try:
            wb.save(output_file)
            print(f"增强版Excel报表已生成并保存为: {output_file}")
        except PermissionError:
            print(f"错误：无法保存文件 '{output_file}'，可能是文件正在被其他程序占用。")
            print("请关闭相关文件后重试。")
            raise

    except Exception as e:
        print("生成增强版Excel报表时发生错误：")
        print(traceback.format_exc())
        raise

def generate_enhanced_excel_from_template(all_devices_data, output_file, customer_name, start_date, end_date):
    """基于模板生成对账单Excel报表"""
    template_path = os.path.join(os.path.dirname(__file__), 'template', 'statement_template.xlsx')

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
        wb = load_workbook(template_path)

        # 修改工作表名称以匹配本地模板
        sheets = {
            "对账单": update_statement_sheet,
            "订单记录": update_order_details_sheet,
            "日用量": update_daily_usage_sheet,
            "月用量": update_monthly_comparison_sheet
        }

        missing_sheets = [name for name in sheets if name not in wb.sheetnames]
        if missing_sheets:
            raise KeyError(
                f"模板缺少以下工作表: {', '.join(missing_sheets)}\n"
                f"请确保模板包含所有必需的工作表:\n"
                f"- {chr(10).join(sheets.keys())}"
            )

        # 更新各工作表
        for name, update_func in sheets.items():
            try:
                update_func(wb[name], all_devices_data, customer_name, start_date, end_date)
            except Exception as e:
                raise RuntimeError(f"更新工作表 '{name}' 时出错: {e}")

        # 保存结果前处理图表相关警告
        for sheet in wb.worksheets:
            if sheet._charts:
                for chart in sheet._charts:
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

def update_statement_sheet(ws, all_devices_data, customer_name, start_date, end_date):
    """更新对账单工作表"""
    try:
        # 更新客户信息和日期范围
        ws['B2'] = customer_name
        ws['D2'] = f"{start_date.strftime('%Y-%m-%d')}至{end_date.strftime('%Y-%m-%d')}"

        # 在此添加更新表格内容的代码
        current_row = 4
        for device_data in all_devices_data:
            device_code = device_data['device_code']
            oil_name = device_data['oil_name']
            for date, value in device_data['data']:
                ws.cell(row=current_row, column=1, value=date)
                ws.cell(row=current_row, column=2, value=device_code)
                ws.cell(row=current_row, column=3, value=oil_name)
                ws.cell(row=current_row, column=4, value=value)
                current_row += 1

    except Exception as e:
        print(f"更新对账单工作表时出错: {e}")
        raise

def update_order_details_sheet(ws, all_devices_data):
    """更新订单明细工作表"""
    try:
        # 清除现有数据（保留表头）
        for row in range(4, ws.max_row + 1):
            ws.delete_rows(row)

        # 数据写入的起始行（根据模板格式调整）
        current_row = 4

        # 写入所有设备的订单数据
        for device_data in all_devices_data:
            if device_data['raw_data']:
                for row_data in device_data['raw_data']:
                    for col, value in enumerate(row_data, 1):
                        ws.cell(row=current_row, column=col, value=value)
                    current_row += 1

    except Exception as e:
        print(f"更新订单明细工作表时出错: {e}")
        raise

def update_daily_usage_sheet(ws, all_devices_data, start_date, end_date):
    """更新每日用量明细工作表"""
    try:
        # 更新标题日期范围
        ws['A1'] = f"每日用量明细({start_date}至{end_date})"

        # 收集每日用量数据
        daily_usage = defaultdict(lambda: defaultdict(float))
        oil_names = set()

        for device_data in all_devices_data:
            oil_name = device_data['oil_name']
            oil_names.add(oil_name)
            for date, value in device_data['data']:
                daily_usage[date][oil_name] += value

        # 写入数据（从第4行开始，保留表头）
        current_row = 4
        sorted_dates = sorted(daily_usage.keys())
        sorted_oils = sorted(oil_names)

        # 更新表头
        for col, oil_name in enumerate(sorted_oils, 2):
            ws.cell(row=3, column=col, value=oil_name)

        # 写入每日数据
        for date in sorted_dates:
            ws.cell(row=current_row, column=1, value=date)
            for col, oil_name in enumerate(sorted_oils, 2):
                value = daily_usage[date].get(oil_name, 0)
                ws.cell(row=current_row, column=col, value=round(value, 2))
            current_row += 1

        # 更新图表（如果模板中包含图表）
        if ws._charts:
            chart = ws._charts[0]
            # 更新图表数据范围
            data = Reference(ws, min_col=2, min_row=3, max_col=len(sorted_oils)+1,
                           max_row=current_row-1)
            cats = Reference(ws, min_col=1, min_row=4, max_row=current_row-1)
            chart.set_categories(cats)
            chart.series[0].values = data

    except Exception as e:
        print(f"更新每日用量明细工作表时出错: {e}")
        raise

def update_monthly_comparison_sheet(ws, all_devices_data, start_date, end_date):
    """更新每月用量对比工作表"""
    try:
        ws['A1'] = f"每月用量对比({start_date}至{end_date})"

        # 收集月度数据
        monthly_stats = defaultdict(lambda: defaultdict(float))
        for device_data in all_devices_data:
            oil_name = device_data['oil_name']
            for date, value in device_data['data']:
                month = date.strftime('%Y-%m')
                monthly_stats[month][oil_name] += value

        # 写入数据
        current_row = 4
        for month, oil_stats in sorted(monthly_stats.items()):
            ws.cell(row=current_row, column=1, value=month)
            for col, (oil_name, value) in enumerate(sorted(oil_stats.items()), 2):
                ws.cell(row=current_row, column=col, value=round(value, 2))
            current_row += 1

    except Exception as e:
        print(f"更新每月用量对比工作表时出错: {e}")
        raise


def load_encrypted_config():
    """加载并解密配置"""
    try:
        # 读取加密密钥
        if not os.path.exists('.env'):
            raise FileNotFoundError("未找到加密密钥文件")

        with open('.env', 'rb') as f:
            key = f.read()

        # 读取加密配置
        with open('query_config_encrypted.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 解密密码
        fernet = Fernet(key)
        db_config = config['db_config']
        db_config['password'] = fernet.decrypt(db_config['password'].encode()).decode()

        return config
    except Exception as e:
        print(f"加载配置失败: {e}")
        exit(1)

if __name__ == "__main__":
    # 初始化日志列表
    log_messages = []
    failed_devices = []
    
    # 记录程序开始时间
    start_time = datetime.now()
    log_messages.append(f"程序开始执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append("")  # 添加空行分隔
    
    print("=" * 50)
    print("步骤1：读取配置文件和设备信息")
    print("=" * 50)
    
    # 读取查询配置文件
    try:
        query_config = load_encrypted_config()
        log_messages.append("成功读取加密配置文件")
        log_messages.append("")
    except Exception as e:
        error_msg = f"读取查询配置文件失败: {e}"
        print(error_msg)
        log_messages.append(error_msg)
        log_messages.append("")  # 添加空行分隔
        exit(1)
    
    # 提取数据库配置和SQL模板
    db_config = query_config.get('db_config', {})
    sql_templates = query_config.get('sql_templates', {})
    
    # 获取SQL查询模板
    device_query_template = sql_templates.get('device_id_query', "SELECT id FROM oil.t_device WHERE device_no = %s ORDER BY create_time DESC LIMIT 1")
    inventory_query_template = sql_templates.get('inventory_query', "")
    
    # 显示文件选择对话框，让用户选择设备信息CSV文件
    Tk().withdraw()  # 隐藏主窗口
    devices_csv = askopenfilename(
        title="选择设备信息文件",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not devices_csv:
        cancel_msg = "未选择设备信息文件，程序退出。"
        print(cancel_msg)
        log_messages.append(cancel_msg)
        log_messages.append("")  # 添加空行分隔
        exit(1)
    
    log_messages.append(f"选择的设备信息文件: {devices_csv}")
    log_messages.append("")  # 添加空行分隔
    
    # 从CSV文件读取设备信息
    devices = read_devices_from_csv(devices_csv)
    if not devices:
        error_msg = "错误：设备信息文件为空或读取失败"
        print(error_msg)
        log_messages.append(error_msg)
        log_messages.append("")  # 添加空行分隔
        print("可能的原因:")
        log_messages.append("可能的原因:")
        print("1. 文件格式不正确（应为CSV格式）")
        log_messages.append("1. 文件格式不正确（应为CSV格式）")
        print("2. 文件编码不支持（支持UTF-8、GBK、GB2312等）")
        log_messages.append("2. 文件编码不支持（支持UTF-8、GBK、GB2312等）")
        print("3. 文件内容为空或没有有效数据")
        log_messages.append("3. 文件内容为空或没有有效数据")
        print("4. 文件列标题不正确（应包含device_no、start_date、end_date）")
        log_messages.append("4. 文件列标题不正确（应包含device_no、start_date、end_date）")
        print("\n解决方法:")
        log_messages.append("")
        log_messages.append("解决方法:")
        print("1. 检查文件是否存在且非空")
        log_messages.append("1. 检查文件是否存在且非空")
        print("2. 确保文件是有效的CSV格式")
        log_messages.append("2. 确保文件是有效的CSV格式")
        print("3. 尝试用记事本或Excel重新保存为UTF-8编码的CSV文件")
        log_messages.append("3. 尝试用记事本或Excel重新保存为UTF-8编码的CSV文件")
        print("4. 确保文件包含正确的列标题: device_no, start_date, end_date")
        log_messages.append("4. 确保文件包含正确的列标题: device_no, start_date, end_date")
        log_messages.append("")  # 添加空行分隔
        exit(1)
    
    # 验证和过滤有效的设备信息
    valid_devices = []
    for device in devices:
        device_no = device.get('device_no', '').strip()
        start_date_str = device.get('start_date', '').strip()
        end_date_str = device.get('end_date', '').strip()
        
        # 检查必要字段是否存在
        if not device_no or not start_date_str or not end_date_str:
            warn_msg = f"警告：设备信息不完整，跳过该设备。设备编号: {device_no}, 开始日期: {start_date_str}, 结束日期: {end_date_str}"
            print(warn_msg)
            log_messages.append(warn_msg)
            log_messages.append("")  # 添加空行分隔
            continue
        
        # 验证日期格式
        try:
            start_date = parse_date(start_date_str)
            end_date = parse_date(end_date_str)
            
            # 验证日期逻辑
            if start_date > end_date:
                error_msg = f"错误：设备 {device_no} 的起始日期({start_date_str})晚于结束日期({end_date_str})，跳过该设备"
                print(error_msg)
                log_messages.append(error_msg)
                log_messages.append("")  # 添加空行分隔
                continue
                
            # 更新设备信息
            device['start_date'] = start_date
            device['end_date'] = end_date
            valid_devices.append(device)
            
        except ValueError as e:
            error_msg = f"错误：设备 {device_no} 的日期格式不正确 - {str(e)}，跳过该设备"
            print(error_msg)
            log_messages.append(error_msg)
            log_messages.append("")  # 添加空行分隔
            continue
    
    if not valid_devices:
        error_msg = "没有有效的设备信息，程序退出。"
        print(error_msg)
        log_messages.append(error_msg)
        log_messages.append("")  # 添加空行分隔
        exit(1)
    
    device_count_msg = f"共读取 {len(devices)} 台设备信息，其中有效设备 {len(valid_devices)} 台"
    print(device_count_msg)
    log_messages.append(device_count_msg)
    log_messages.append("")  # 添加空行分隔
    
    print("\n" + "=" * 50)
    print("步骤2：连接数据库并查询数据")
    print("=" * 50)
    
    # 连接数据库
    connection = connect_to_database(db_config)
    if not connection:
        error_msg = "数据库连接失败，程序退出。"
        print(error_msg)
        log_messages.append(error_msg)
        log_messages.append("")  # 添加空行分隔
        exit(1)
    
    log_messages.append("数据库连接成功")
    log_messages.append("")  # 添加空行分隔
    
    # 存储所有查询结果
    all_results = []
    failed_devices = []
    
    # 为每个有效设备执行查询
    for i, device in enumerate(valid_devices):
        device_no = device['device_no']
        start_date = device['start_date']
        end_date = device['end_date']
        
        process_msg = f"处理第 {i+1} 台设备: {device_no}"
        date_msg = f"查询日期范围: {start_date} 至 {end_date}"
        print(process_msg)
        print(date_msg)
        log_messages.append(process_msg)
        log_messages.append(date_msg)
        log_messages.append("")  # 添加空行分隔
        
        # 根据设备编号查询设备ID
        device_id = get_device_id_by_no(connection, device_no, device_query_template)
        if not device_id:
            warn_msg = f"警告：未找到设备编号 {device_no} 对应的设备ID，跳过该设备"
            print(warn_msg)
            log_messages.append(warn_msg)
            log_messages.append("")  # 添加空行分隔
            failed_devices.append({
                'device_no': device_no,
                'reason': '未找到对应的设备ID'
            })
            continue
        
        # 生成查询语句
        inventory_query = generate_query_for_device(inventory_query_template, device_id, start_date, end_date)
        
        # 执行查询
        query_msg = f"执行查询..."
        print(query_msg)
        log_messages.append(query_msg)
        inventory_data, columns, raw_data = fetch_inventory_data_from_db(connection, inventory_query)
        log_messages.append("")  # 添加空行分隔
        
        # 获取油品名称用于文件命名
        oil_name = "未知油品"
        customer_name = "未知客户"  # 初始化客户名称
        if raw_data and len(columns) > 3:
            # 从查询结果中获取油品名称
            oil_name_index = columns.index('油品名称') if '油品名称' in columns else 3
            if oil_name_index < len(raw_data[0]):
                oil_name = raw_data[0][oil_name_index]
            
            # 尝试从查询结果中获取客户名称
            customer_name_index = columns.index('customer_name') if 'customer_name' in columns else -1
            if customer_name_index >= 0 and customer_name_index < len(raw_data[0]) and raw_data[0][customer_name_index]:
                customer_name = raw_data[0][customer_name_index]
            else:
                # 如果查询结果中没有客户名称，则通过设备编号查询
                customer_name = get_customer_name_by_device_code(connection, device_no)
        
        all_results.append({
            'oil_name': oil_name,
            'device_code': device_no,
            'data': inventory_data,
            'columns': columns,
            'raw_data': raw_data,
            'customer_name': customer_name
        })
    
    connection.close()
    log_messages.append("数据库连接已关闭")
    log_messages.append("")  # 添加空行分隔
    
    if not all_results:
        warn_msg = "警告：所有设备查询均未返回结果，但仍继续执行程序"
        print(warn_msg)
        log_messages.append(warn_msg)
        log_messages.append("")  # 添加空行分隔
    
    print("\n" + "=" * 50)
    print("步骤3：选择保存目录并生成文件")
    print("=" * 50)
    
    save_dir = askdirectory(title="选择保存文件的目录")
    if not save_dir:
        cancel_msg = "未选择保存路径，程序退出。"
        print(cancel_msg)
        log_messages.append(cancel_msg)
        log_messages.append("")  # 添加空行分隔
        exit(1)
    
    log_messages.append(f"选择的保存目录: {save_dir}")
    log_messages.append("")  # 添加空行分隔
    
    # 如果没有结果，仍然创建一个空的结果目录
    if not all_results:
        info_msg = "提示：没有查询到任何数据，将创建空的结果目录"
        print(info_msg)
        log_messages.append(info_msg)
        log_messages.append("")  # 添加空行分隔
    
    # 默认样式和导出格式
    default_chart_style = {
        "line_color": "0000FF",
        "marker_style": "circle",
        "marker_size": 8,
        "line_width": 2.5
    }
    
    # 为每个查询结果生成Excel文件
    for i, result in enumerate(all_results):
        oil_name = result['oil_name']
        device_code = result['device_code']
        inventory_data = result['data']
        
        # 从查询结果中提取日期范围
        if inventory_data:
            start_date = min(inventory_data, key=lambda x: x[0])[0]
            end_date = max(inventory_data, key=lambda x: x[0])[0]
        else:
            # 如果没有数据，使用设备信息中的日期
            # 先找到该设备在valid_devices中的索引
            device_info = next((d for d in valid_devices if d['device_no'] == device_code), None)
            if device_info:
                start_date_str = device_info.get('start_date', '')
                end_date_str = device_info.get('end_date', '')
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                # fallback到默认日期
                start_date = datetime.strptime("2025-07-01", '%Y-%m-%d').date()
                end_date = datetime.strptime("2025-07-31", '%Y-%m-%d').date()
        
        # 根据需求修改输出文件名格式: 油品名称'oil_name'+设备编码'device_code'+月份
        output_file = os.path.join(save_dir, f"{oil_name}_{device_code}_{start_date.strftime('%Y%m')}.xlsx")
        generate_excel_with_chart(inventory_data, output_file, device_code, start_date, end_date,
                                chart_style=default_chart_style)
        
        save_msg = f"第 {i+1} 个文件已保存: {os.path.basename(output_file)}"
        print(save_msg)
        log_messages.append(save_msg)
        log_messages.append("")  # 添加空行分隔


    # 如果有查询结果，生成增强版Excel报表
    if all_results:
        try:
            # 获取整体的日期范围和客户信息
            customer_name = all_results[0].get('customer_name', '未知客户')
            overall_start_date = min(result['data'][0][0] for result in all_results if result['data'])
            overall_end_date = max(result['data'][-1][0] for result in all_results if result['data'])

            # 生成对账单文件名和路径
            enhanced_filename = f"{customer_name}{overall_start_date.strftime('%Y年%m月')}对账单.xlsx"
            enhanced_output_file = os.path.join(save_dir, enhanced_filename)

            try:
                generate_enhanced_excel_from_template(
                    all_results,
                    enhanced_output_file,
                    customer_name,
                    overall_start_date,
                    overall_end_date
                )
                print(f"已基于模板生成对账单: {enhanced_filename}")
                log_messages.append(f"对账单生成成功: {enhanced_filename}")
            except FileNotFoundError as e:
                error_msg = f"模板文件错误: {e}"
                print(error_msg)
                log_messages.append(error_msg)
            except Exception as e:
                error_msg = f"生成对账单失败: {e}"
                print(error_msg)
                print(f"错误详情: {traceback.format_exc()}")
                log_messages.append(error_msg)
                log_messages.append(traceback.format_exc())

        except Exception as e:
            error_msg = f"处理对账单数据时出错: {e}"
            print(error_msg)
            log_messages.append(error_msg)
            log_messages.append(traceback.format_exc())

    # 程序结束前的日志记录
    end_time = datetime.now()
    log_messages.append(f"程序结束执行时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append(f"程序总执行时间: {end_time - start_time}")

    print("\n" + "=" * 50)
    print("步骤4：保存结果文件")
    print("=" * 50)
    print(f"步骤4：所有Excel文件已保存至：")
    print(f"    文件保存路径：{save_dir}")

    # 保存日志文件
    log_filename = f"程序执行日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    log_filepath = os.path.join(save_dir, log_filename)
    with open(log_filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_messages))
    print(f"程序执行日志已保存至: {log_filename}")

    print("\n" + "=" * 50)
    print("程序执行完成")
    print("=" * 50)
    print(f"程序总执行时间: {end_time - start_time}")

    # 处理失败设备的信息，并创建对应的Excel文件记录
    if failed_devices:
        failed_file = os.path.join(save_dir, f"失败设备信息_{start_time.strftime('%Y%m%d_%H%M%S')}.xlsx")
        wb = Workbook()
        ws = wb.active
        ws.title = "失败设备信息"
        
        # 添加标题行
        ws.append(["设备编号", "失败原因"])
        
        # 添加数据行
        for device in failed_devices:
            ws.append([device['device_no'], device['reason']])
        
        # 设置失败设备信息为红色字体
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=2):
            for cell in row:
                cell.font = Font(color="FF0000")  # 红色字体
        
        try:
            wb.save(failed_file)
            failed_save_msg = f"失败设备信息已保存至: {os.path.basename(failed_file)}"
            print(failed_save_msg)
            log_messages.append(failed_save_msg)
            log_messages.append("")  # 添加空行分隔
        except Exception as e:
            failed_error_msg = f"保存失败设备信息文件时出错: {e}"
            print(failed_error_msg)
            log_messages.append(failed_error_msg)
            log_messages.append("")  # 添加空行分隔
    
    print("\n" + "=" * 50)
    print("步骤4：保存结果文件")
    print("=" * 50)

    # 如果有查询结果，生成增强版Excel报表
    if all_results:
        success_msg = "步骤4：所有Excel文件已保存至："
        print(success_msg)
        print(f"    文件保存路径：{save_dir}")
        log_messages.append(success_msg)
        log_messages.append(f"    文件保存路径：{save_dir}")
        log_messages.append("")  # 添加空行分隔
    else:
        empty_msg = "步骤4：已创建空的结果目录："
        print(empty_msg)
        print(f"    目录路径：{save_dir}")
        log_messages.append(empty_msg)
        log_messages.append(f"    目录路径：{save_dir}")
        log_messages.append("")  # 添加空行分隔
    
    # 保存日志文件
    end_time = datetime.now()
    log_file = os.path.join(save_dir, f"程序执行日志_{start_time.strftime('%Y%m%d_%H%M%S')}.txt")
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            for message in log_messages:
                f.write(message + '\n')
        log_saved_msg = f"程序执行日志已保存至: {os.path.basename(log_file)}"
        print(log_saved_msg)
        log_messages.append(log_saved_msg)
    except Exception as e:
        log_error_msg = f"保存日志文件时出错: {e}"
        print(log_error_msg)
        log_messages.append(log_error_msg)
    
    log_messages.append(f"程序结束执行时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append(f"程序总执行时间: {end_time - start_time}")
    
    print("\n" + "=" * 50)
    print("程序执行完成")
    print("=" * 50)
    print(f"程序总执行时间: {end_time - start_time}")