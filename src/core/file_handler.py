import csv
import os
import sys
import re
from datetime import datetime
from src.utils.date_utils import parse_date, validate_csv_data, validate_date_span


class FileReadError(Exception):
    """文件读取相关错误"""
    pass


class FileHandler:
    """文件处理类，负责所有文件相关操作"""

    def __init__(self):
        """初始化文件处理器"""
        self.encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
        self.max_devices = 200  # 最大支持设备数量
        self.required_fields = {'start_date', 'end_date', 'device_code'}

    def read_devices_from_csv(self, csv_file):
        """
        从CSV文件读取设备信息，支持多种编码格式
        使用device_code作为设备标识字段

        Args:
            csv_file (str): CSV文件路径

        Returns:
            list: 设备信息列表
            
        Raises:
            FileReadError: 当文件读取或验证失败时抛出异常
        """
        print(f"正在尝试读取设备信息文件: {csv_file}")

        # 检查文件是否存在和是否为空
        if not self._validate_file(csv_file):
            return []
        
        # 检查文件扩展名是否为CSV
        if not self._validate_file_type(csv_file):
            error_msg = f"错误：只支持CSV文件格式，当前文件: {csv_file}"
            print(error_msg)
            raise FileReadError(error_msg)

        # 初始化状态标记
        state = self._init_processing_state()
        
        # 尝试不同的编码格式
        for encoding in self.encodings:
            try:
                result = self._try_read_with_encoding(csv_file, encoding, state)
                if result is not None:
                    devices, success = result
                    if success:
                        state['success'] = True
                        state['final_message_printed'] = True
                        print(f"成功使用 {encoding} 编码读取设备信息文件，共读取 {len(devices)} 条设备信息")
                        break
            except FileReadError as e:
                # 重新抛出我们自定义的异常
                raise e
            except Exception as e:
                # 其他异常继续尝试其他编码
                print(f"使用 {encoding} 编码读取文件时发生未知错误: {str(e)}")
                continue

        # 输出最终信息
        self._print_final_message(state)
        if not state['success'] and not state['data_issue_found'] and not state['empty_content_warning_printed']:
            supported_encodings = ", ".join(self.encodings)
            error_msg = (
                "错误：无法使用任何支持的编码格式读取设备信息文件\n"
                f"支持的编码格式: {supported_encodings}\n"
                "请确保设备信息文件是有效的CSV格式，并使用上述编码之一\n"
                "建议: 尝试用Excel重新保存为UTF-8编码的CSV文件\n"
                "未能读取设备信息，请修改文件错误后再尝试。"
            )
            raise FileReadError(error_msg)
        elif not state['success'] and state['empty_content_warning_printed'] and not state['data_issue_found']:
            # 文件内容为空的情况
            error_msg = "错误：设备信息文件为空\n未能读取设备信息，请修改文件错误后再尝试。"
            raise FileReadError(error_msg)
            
        return devices if state['success'] else []

    def _validate_file(self, csv_file):
        """验证文件是否存在和是否为空"""
        # 检查文件是否存在
        if not os.path.exists(csv_file):
            print(f"错误：设备信息文件不存在: {csv_file}")
            return False

        # 检查文件是否为空
        if os.path.getsize(csv_file) == 0:
            print(f"错误：设备信息文件为空: {csv_file}")
            return False
            
        return True

    def _validate_file_type(self, csv_file):
        """验证文件类型是否为CSV格式"""
        # 获取文件扩展名并转换为小写
        file_extension = os.path.splitext(csv_file)[1].lower()
        # 检查扩展名是否为.csv
        return file_extension == '.csv'

    def _init_processing_state(self):
        """初始化处理状态标记"""
        return {
            'device_field_warning_printed': False,
            'empty_content_warning_printed': False,
            'no_header_warning_printed': False,
            'empty_device_warning_printed': False,
            'success': False,
            'data_issue_found': False,
            'final_message_printed': False
        }

    def _try_read_with_encoding(self, csv_file, encoding, state):
        """尝试使用指定编码读取文件"""
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                # 尝试读取文件内容
                content = f.read()
                if not content.strip():
                    if not state['empty_content_warning_printed']:
                        print(f"警告：使用 {encoding} 编码读取的文件内容为空")
                        state['empty_content_warning_printed'] = True
                    return None

                # 重新打开文件用于CSV读取
                f.seek(0)
                reader = csv.DictReader(f)

                # 检查是否有列标题
                if not reader.fieldnames:
                    if not state['no_header_warning_printed']:
                        print(f"警告：使用 {encoding} 编码未能正确识别CSV列标题")
                        state['no_header_warning_printed'] = True
                    return None

                # 验证列标题是否包含必要字段
                fieldnames = set(reader.fieldnames)
                missing_fields = self.required_fields - fieldnames
                if missing_fields:
                    if not state['device_field_warning_printed']:
                        print(f"错误：CSV文件缺少必要字段: {', '.join(missing_fields)}")
                        state['device_field_warning_printed'] = True
                        state['data_issue_found'] = True
                    return None

                print(f"CSV列标题: {', '.join(reader.fieldnames)}")

                # 读取设备信息
                devices = self._read_device_rows(reader, state)
                if devices is not None:
                    # 检查设备数量是否超过限制
                    if len(devices) > self.max_devices:
                        error_msg = (
                            f"错误：设备数量超过最大限制 ({self.max_devices}台)\n"
                            f"当前设备数量: {len(devices)}台\n"
                            "请减少设备数量或分批处理"
                        )
                        print(error_msg)
                        raise FileReadError(error_msg)
                    
                    return devices, True

        except UnicodeDecodeError as e:
            # 只有在不是空文件的情况下才打印编码错误
            if not state['empty_content_warning_printed'] and not state['data_issue_found']:
                print(f"使用 {encoding} 编码读取文件失败: {str(e)}")
            return None
        except csv.Error as e:
            # 只有在不是空文件的情况下才打印CSV解析错误
            if not state['empty_content_warning_printed'] and not state['data_issue_found']:
                print(f"使用 {encoding} 编码解析CSV文件失败: {str(e)}")
            return None
            
        return [], False

    def _read_device_rows(self, reader, state):
        """读取并验证设备行数据"""
        devices = []
        
        # 读取设备信息
        for row in reader:
            # 跳过空行
            if not any(row.values()):
                continue

            # 验证并处理行数据
            try:
                device = self._validate_and_process_row(row, reader.line_num, devices, state)
                if device is None:
                    # 出现错误，需要退出程序
                    return None
                elif device:
                    # 有效设备数据
                    devices.append(device)
            except FileReadError:
                # 重新抛出FileReadError异常，中断整个读取过程
                raise
            except Exception as e:
                # 其他异常转换为FileReadError
                error_msg = f"错误：处理行数据时发生未知错误，行号: {reader.line_num}，异常信息: {str(e)}"
                print(error_msg)
                raise FileReadError(error_msg)
        
        return devices

    def _validate_and_process_row(self, row, line_num, devices, state):
        """验证并处理单行设备数据"""
        # 获取设备标识
        device_code = row.get('device_code', '').strip()

        # 确保设备标识不为空
        if not device_code:
            if not state['empty_device_warning_printed']:
                print(f"警告：跳过设备标识为空的行: {row}")
                state['empty_device_warning_printed'] = True
                state['data_issue_found'] = True
            return {}  # 返回空字典表示跳过该行

        # 验证设备编码格式
        try:
            if not self._validate_device_code(device_code, line_num):
                return None  # 返回None表示出现严重错误，需要退出程序
        except FileReadError:
            # 重新抛出FileReadError异常
            raise
        except Exception as e:
            # 其他异常转换为FileReadError
            error_msg = f"错误：设备编码验证失败，第{line_num}行: {device_code}，异常信息: {str(e)}"
            print(error_msg)
            raise FileReadError(error_msg)

        # 获取开始和结束日期
        start_date = row.get('start_date', '').strip()
        end_date = row.get('end_date', '').strip()

        # 确保关键字段都不为空
        if not start_date or not end_date:
            error_msg = f"错误：日期信息不完整，第{line_num}行: {row}"
            print(error_msg)
            raise FileReadError(error_msg)

        # 使用date_utils.py中的方法验证日期格式和逻辑关系
        try:
            if not self._validate_dates(row, line_num):
                state['data_issue_found'] = True
                return {}  # 返回空字典表示跳过该行
        except FileReadError:
            # 重新抛出FileReadError异常
            raise
        except Exception as e:
            # 其他异常转换为FileReadError
            error_msg = f"错误：日期验证失败，第{line_num}行: {row}，异常信息: {str(e)}"
            print(error_msg)
            raise FileReadError(error_msg)

        # 检查设备编码是否重复，但允许相同设备编码具有不同日期范围的情况
        try:
            if not self._check_duplicate_device(device_code, start_date, end_date, devices, line_num, row):
                return None  # 返回None表示出现严重错误，需要退出程序
        except FileReadError:
            # 重新抛出FileReadError异常
            raise
        except Exception as e:
            # 其他异常转换为FileReadError
            error_msg = f"错误：重复设备检查失败，第{line_num}行: {row}，异常信息: {str(e)}"
            print(error_msg)
            raise FileReadError(error_msg)

        # 返回有效设备数据
        return {
            'device_code': device_code,
            'start_date': start_date,
            'end_date': end_date,
        }

    def _validate_device_code(self, device_code, line_num):
        """验证设备编码格式"""
        # 验证设备编码只能包含英文字母和阿拉伯数字
        if not re.match(r'^[A-Za-z0-9]+$', device_code):
            error_msg = f"错误：设备编码只能包含英文字母和阿拉伯数字，第{line_num}行: {device_code}"
            print(error_msg)
            raise FileReadError(error_msg)

        # 验证设备编码必须以英文字母开头
        if not re.match(r'^[A-Za-z]', device_code):
            error_msg = f"错误：设备编码必须以英文字母开头，第{line_num}行: {device_code}"
            print(error_msg)
            raise FileReadError(error_msg)
            
        return True

    def _validate_dates(self, row, line_num):
        """验证日期格式和逻辑关系"""
        try:
            # 验证日期格式和逻辑关系
            if not validate_csv_data(row):
                error_msg = f"错误：日期验证失败，第{line_num}行: {row}"
                print(error_msg)
                raise FileReadError(error_msg)
        except FileReadError:
            # 重新抛出FileReadError异常
            raise
        except Exception as e:
            error_msg = f"错误：日期验证异常，第{line_num}行: {row}，异常信息: {str(e)}"
            print(error_msg)
            raise FileReadError(error_msg)
            
        # 验证日期跨度是否超过2个月
        if not validate_date_span(row):
            error_msg = f"错误：日期跨度超过2个月，第{line_num}行: {row}"
            print(error_msg)
            raise FileReadError(error_msg)
            
        return True

    def _check_duplicate_device(self, device_code, start_date, end_date, devices, line_num, row):
        """检查设备是否重复"""
        # 解析当前设备的日期
        try:
            current_start = parse_date(start_date)
            current_end = parse_date(end_date)
        except ValueError as e:
            error_msg = f"错误：日期格式无效，第{line_num}行: {row}，异常信息: {str(e)}"
            print(error_msg)
            raise FileReadError(error_msg)
        
        # 检查所有具有相同设备编码的设备
        for existing_device in devices:
            if existing_device['device_code'] == device_code:
                # 如果设备编码相同，检查日期范围是否也相同
                try:
                    existing_start = parse_date(existing_device['start_date'])
                    existing_end = parse_date(existing_device['end_date'])
                    
                    # 比较解析后的日期而不是原始字符串
                    if existing_start == current_start and existing_end == current_end:
                        error_msg = (
                            f"错误：发现重复的设备编码且日期范围相同，第{line_num}行: {row}\n"
                            f"     与之前第{devices.index(existing_device)+2}行的设备重复"
                        )
                        print(error_msg)
                        raise FileReadError(error_msg)
                except ValueError as e:
                    # 如果现有设备的日期格式无效，则跳过比较
                    pass
                    
                # 注意：这里不再使用break，需要检查所有相同设备编码的设备
                # 设备编码相同但日期范围不同，这是允许的
                
        return True

    def _print_final_message(self, state):
        """输出最终处理结果信息"""
        # 根据处理结果输出最终信息
        if state['data_issue_found'] and not state['final_message_printed']:
            # 存在数据问题，输出简洁的总结信息
            print("未能读取设备信息，请修改文件错误。")
            state['final_message_printed'] = True
        elif not state['success'] and not state['final_message_printed']:
            # 没有具体的数据问题，输出通用错误信息
            supported_encodings = ", ".join(self.encodings)
            print("错误：无法使用任何支持的编码格式读取设备信息文件")
            print(f"支持的编码格式: {supported_encodings}")
            print("请确保设备信息文件是有效的CSV格式，并使用上述编码之一")
            print("建议: 尝试用Excel重新保存为UTF-8编码的CSV文件")
            print("未能读取设备信息，请修改文件错误后再尝试。")