import csv
import os


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

                    # 检查是否存在设备标识字段
                    has_device_code = 'device_code' in fieldnames

                    if not has_device_code:
                        # 只在第一次打印缺少设备标识字段的警告
                        if not device_field_warning_printed:
                            print("警告：CSV文件缺少设备标识字段，应包含'device_code'")
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
                        device_code = (
                            row.get('device_code', '').strip()
                            if has_device_code
                            else ''
                        )

                        # 确保设备标识不为空
                        if not device_code:
                            if not empty_device_warning_printed:
                                print(f"警告：跳过设备标识为空的行: {row}")
                                empty_device_warning_printed = True
                                data_issue_found = True
                            continue

                        # 获取开始和结束日期
                        start_date = row.get('start_date', '').strip()
                        end_date = row.get('end_date', '').strip()

                        # 确保关键字段都不为空
                        if not start_date or not end_date:
                            if not incomplete_row_warning_printed:
                                print(f"警告：跳过日期信息不完整的行: {row}")
                                incomplete_row_warning_printed = True
                                data_issue_found = True
                            continue

                        current_devices.append({
                            'device_code': device_code,
                            'start_date': start_date,
                            'end_date': end_date,
                        })

                    # 检查是否有设备数据行
                    if row_count == 0:
                        print(f"错误：设备信息文件为空: {csv_file}")
                        return []  # 直接返回空列表，避免继续执行下面的逻辑
        
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
