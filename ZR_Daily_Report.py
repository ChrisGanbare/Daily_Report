import re
import os
import json
from datetime import datetime, timedelta
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askdirectory
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font

# 添加项目根目录到sys.path，确保能正确导入模块
import sys
sys.path.insert(0, os.path.dirname(__file__))

# 使用包导入简化导入路径
from src.core import DatabaseHandler, ExcelHandler, FileHandler, StatementHandler
from src.utils import ConfigHandler, DataValidator

def main():
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
    
    # 初始化处理器
    config_handler = ConfigHandler()
    file_handler = FileHandler()
    data_validator = DataValidator()
    
    # 读取查询配置文件
    try:
        # 使用项目根目录下的配置文件
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'query_config.json')
        print(f"尝试读取配置文件: {config_path}")
        query_config = config_handler.load_plain_config(config_path)
        log_messages.append("成功读取配置文件")
        log_messages.append("")
    except FileNotFoundError as e:
        error_msg = f"配置文件未找到: {e}"
        print(error_msg)
        log_messages.append(error_msg)
        log_messages.append("")  # 添加空行分隔
        exit(1)
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
    devices = file_handler.read_devices_from_csv(devices_csv)
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
            start_date = data_validator.parse_date(start_date_str)
            end_date = data_validator.parse_date(end_date_str)
            
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
    db_handler = DatabaseHandler(db_config)
    try:
        db_handler.connect()
        log_messages.append("数据库连接成功")
        log_messages.append("")  # 添加空行分隔
    except Exception as e:
        error_msg = f"数据库连接失败: {e}"
        print(error_msg)
        log_messages.append(error_msg)
        log_messages.append("")  # 添加空行分隔
        exit(1)
    
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
        device_id = db_handler.get_device_id_by_no(device_no, device_query_template)
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
        # 使用字符串格式化生成查询语句
        end_condition = f"{end_date} 23:59:59"
        inventory_query = inventory_query_template.format(
            device_id=device_id,
            start_date=start_date,
            end_condition=end_condition
        )
        
        # 执行查询
        query_msg = f"执行查询..."
        print(query_msg)
        log_messages.append(query_msg)
        inventory_data, columns, raw_data = db_handler.fetch_inventory_data(inventory_query)
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
                customer_name = db_handler.get_customer_name_by_device_code(device_no)
        
        all_results.append({
            'oil_name': oil_name,
            'device_code': device_no,
            'data': inventory_data,
            'columns': columns,
            'raw_data': raw_data,
            'customer_name': customer_name
        })
    
    db_handler.disconnect()
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
    
    # 初始化Excel处理器
    excel_handler = ExcelHandler()
    
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
        excel_handler.generate_excel_with_chart(inventory_data, output_file, device_code, start_date, end_date,
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
                # 使用新的对账单处理模块生成对账单
                statement_handler = StatementHandler()
                statement_handler.generate_statement_from_template(
                    all_results,
                    enhanced_output_file,
                    customer_name,
                    overall_start_date,
                    overall_end_date
                )
                print(f"已生成对账单: {enhanced_filename}")
                log_messages.append(f"对账单生成成功: {enhanced_filename}")
            except FileNotFoundError as e:
                error_msg = f"模板文件错误: {e}"
                print(error_msg)
                log_messages.append(error_msg)
            except Exception as e:
                error_msg = f"生成对账单失败: {e}"
                print(error_msg)
                log_messages.append(error_msg)
                log_messages.append(str(e))

        except Exception as e:
            error_msg = f"处理对账单数据时出错: {e}"
            print(error_msg)
            log_messages.append(error_msg)
            log_messages.append(str(e))

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


if __name__ == "__main__":
    main()
