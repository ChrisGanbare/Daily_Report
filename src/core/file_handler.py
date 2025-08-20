import csv
import os
import sys
import re
from datetime import datetime
from src.utils.date_utils import parse_date, validate_csv_data, validate_date_span


class FileHandler:
    """文件处理类，负责所有文件相关操作"""

    def __init__(self):
        """初始化文件处理器"""
        pass

    def read_devices_from_csv(self, csv_file):
        """
        从CSV文件读取设备信息，支持多种编码格式
        使用device_code作为设备标识字段

        Args:
            csv_file (str): CSV文件路径

        Returns:
            list: 设备信息列表
        """
        devices = []
        encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
        max_devices = 300  # 最大支持设备数量

        print(f"正在尝试读取设备信息文件: {csv_file}")

        # 检查文件是否存在
        if not os.path.exists(csv_file):
            print(f"错误：设备信息文件不存在: {csv_file}")
            return []

        # 检查文件是否为空
        if os.path.getsize(csv_file) == 0:
            print(f"错误：设备信息文件为空: {csv_file}")
            return []

        # 标记是否已经打印过相关警告信息
        device_field_warning_printed = False
        empty_content_warning_printed = False
        no_header_warning_printed = False
        incomplete_row_warning_printed = False
        empty_device_warning_printed = False
        date_format_error_printed = False
        invalid_device_code_warning_printed = False
        
        # 标记是否成功读取到设备信息
        success = False
        # 标记是否遇到数据问题
        data_issue_found = False
        # 标记是否已输出最终总结信息
        final_message_printed = False

        # 尝试不同的编码格式
        for encoding in encodings:
            try:
                with open(csv_file, 'r', encoding=encoding) as f:
                    # 尝试读取文件内容
                    content = f.read()
                    if not content.strip():
                        if not empty_content_warning_printed:
                            print(f"警告：使用 {encoding} 编码读取的文件内容为空")
                            empty_content_warning_printed = True
                        continue

                    # 重新打开文件用于CSV读取
                    f.seek(0)
                    reader = csv.DictReader(f)

                    # 检查是否有列标题
                    if not reader.fieldnames:
                        if not no_header_warning_printed:
                            print(f"警告：使用 {encoding} 编码未能正确识别CSV列标题")
                            no_header_warning_printed = True
                        continue

                    # 验证列标题是否包含必要字段
                    required_fields = {'start_date', 'end_date', 'device_code'}
                    fieldnames = set(reader.fieldnames)

                    # 检查是否所有必需字段都存在
                    missing_fields = required_fields - fieldnames
                    if missing_fields:
                        if not device_field_warning_printed:
                            print(f"错误：CSV文件缺少必要字段: {', '.join(missing_fields)}")
                            device_field_warning_printed = True
                            data_issue_found = True
                        continue

                    # 临时存储当前编码读取的设备信息
                    current_devices = []
                    row_count = 0
                    
                    # 读取设备信息
                    for row in reader:
                        row_count += 1
                        # 跳过空行
                        if not any(row.values()):
                            continue

                        # 获取设备标识
                        device_code = row.get('device_code', '').strip()

                        # 确保设备标识不为空
                        if not device_code:
                            if not empty_device_warning_printed:
                                print(f"警告：跳过设备标识为空的行: {row}")
                                empty_device_warning_printed = True
                                data_issue_found = True
                            continue

                        # 验证设备编码只能包含英文字母和阿拉伯数字
                        if not re.match(r'^[A-Za-z0-9]+$', device_code):
                            print(f"错误：设备编码只能包含英文字母和阿拉伯数字，第{reader.line_num}行: {device_code}")
                            sys.exit(1)

                        # 验证设备编码必须以英文字母开头
                        if not re.match(r'^[A-Za-z]', device_code):
                            print(f"错误：设备编码必须以英文字母开头，第{reader.line_num}行: {device_code}")
                            sys.exit(1)

                        # 获取开始和结束日期
                        start_date = row.get('start_date', '').strip()
                        end_date = row.get('end_date', '').strip()

                        # 确保关键字段都不为空
                        if not start_date or not end_date:
                            print(f"错误：日期信息不完整，第{reader.line_num}行: {row}")
                            sys.exit(1)  # 遇到日期为空时退出程序

                        # 使用date_utils.py中的方法验证日期格式和逻辑关系
                        try:
                            # 验证日期格式和逻辑关系
                            if not validate_csv_data(row):
                                print(f"错误：日期验证失败，第{reader.line_num}行: {row}")
                                sys.exit(1)
                        except Exception as e:
                            print(f"错误：日期验证异常，第{reader.line_num}行: {row}，异常信息: {str(e)}")
                            sys.exit(1)
                            
                        # 验证日期跨度是否超过2个月
                        if not validate_date_span(row):
                            print(f"错误：日期跨度超过2个月，第{reader.line_num}行: {row}")
                            sys.exit(1)

                        # 检查设备编码是否重复，但允许相同设备编码具有不同日期范围的情况
                        duplicate_found = False
                        for existing_device in current_devices:
                            if existing_device['device_code'] == device_code:
                                # 如果设备编码相同，检查日期范围是否也相同
                                if existing_device['start_date'] == start_date and existing_device['end_date'] == end_date:
                                    print(f"错误：发现重复的设备编码且日期范围相同，第{reader.line_num}行: {row}")
                                    print(f"     与之前第{current_devices.index(existing_device)+2}行的设备重复")
                                    sys.exit(1)
                                # 设备编码相同但日期范围不同，这是允许的
                                duplicate_found = True
                                break
                        
                        current_devices.append({
                            'device_code': device_code,
                            'start_date': start_date,
                            'end_date': end_date,
                        })
                        
                        # 检查设备数量是否超过限制
                        if len(current_devices) > max_devices:
                            print(f"错误：设备数量超过最大限制 ({max_devices}台)")
                            print(f"当前设备数量: {len(current_devices)}台")
                            print("请减少设备数量或分批处理")
                            sys.exit(1)
        
                    if current_devices:
                        print(
                            f"成功使用 {encoding} 编码读取设备信息文件，共读取 {len(current_devices)} 条设备信息"
                        )
                        print(f"CSV列标题: {', '.join(reader.fieldnames)}")
                        devices = current_devices
                        success = True
                        final_message_printed = True  # 添加这行，标记已成功读取并输出信息
                        break  # 成功读取后跳出循环，不再尝试其他编码


            except UnicodeDecodeError as e:
                print(f"使用 {encoding} 编码读取文件失败: {str(e)}")
                continue
            except csv.Error as e:
                print(f"使用 {encoding} 编码解析CSV文件失败: {str(e)}")
                continue
            except Exception as e:
                print(f"使用 {encoding} 编码读取文件时发生未知错误: {str(e)}")
                continue

        # 根据处理结果输出最终信息
        if data_issue_found and not final_message_printed:
            # 存在数据问题，输出简洁的总结信息
            print("未能读取设备信息，请修改文件错误。")
            final_message_printed = True
        elif not success and not final_message_printed:  # 修改这行，只在未成功时才输出错误信息
            # 没有具体的数据问题，输出通用错误信息
            supported_encodings = ", ".join(encodings)
            print("错误：无法使用任何支持的编码格式读取设备信息文件")
            print(f"支持的编码格式: {supported_encodings}")
            print("请确保设备信息文件是有效的CSV格式，并使用上述编码之一")
            print("建议: 尝试用Excel重新保存为UTF-8编码的CSV文件")
            print("未能读取设备信息，请修改文件错误后再尝试。")
        
        return devices