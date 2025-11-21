import csv
import os
import sys
import re
from datetime import datetime
from src.utils.date_utils import parse_date, validate_csv_data

class FileReadError(Exception):
    """文件读取相关错误"""
    pass

class StructuralError(FileReadError):
    """与编码无关的结构性错误（如列顺序、字段缺失等）"""
    pass

class FileHandler:
    """文件处理类，负责所有文件相关操作"""

    def __init__(self):
        """初始化文件处理器"""
        self.encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
        self.max_devices = 200
        self.required_fields = {'start_date', 'end_date', 'device_code'}

    def read_devices_from_csv(self, csv_file):
        """
        从CSV文件读取设备信息，支持多种编码格式
        """
        print(f"正在尝试读取设备信息文件: {csv_file}")

        if not self._validate_file(csv_file):
            return []
        
        if not self._validate_file_type(csv_file):
            error_msg = f"错误：只支持CSV文件格式，当前文件: {csv_file}"
            print(error_msg)
            raise FileReadError(error_msg)

        state = self._init_processing_state()
        devices = []
        
        for encoding in self.encodings:
            try:
                result, success = self._try_read_with_encoding(csv_file, encoding, state)
                if success:
                    devices = result
                    state['success'] = True
                    print(f"成功使用 {encoding} 编码读取设备信息文件，共读取 {len(devices)} 条设备信息")
                    break
            except StructuralError as e:
                if not state['device_field_warning_printed']:
                    print(str(e))
                    state['device_field_warning_printed'] = True
                raise FileReadError(str(e)) from e
            except FileReadError as e:
                raise e
            except Exception:
                continue

        if not state['success']:
            if state['empty_content_warning_printed']:
                error_msg = "错误：设备信息文件为空。"
            else:
                error_msg = f"错误：无法使用任何支持的编码格式 {', '.join(self.encodings)} 读取文件。"
            raise FileReadError(error_msg)
        
        return devices

    def _validate_file(self, csv_file):
        if not os.path.exists(csv_file):
            print(f"错误：设备信息文件不存在: {csv_file}")
            return False
        if os.path.getsize(csv_file) == 0:
            print(f"错误：设备信息文件为空: {csv_file}")
            return False
        return True

    def _validate_file_type(self, csv_file):
        return os.path.splitext(csv_file)[1].lower() == '.csv'

    def _init_processing_state(self):
        return {
            'device_field_warning_printed': False,
            'empty_content_warning_printed': False,
            'success': False,
        }

    def _try_read_with_encoding(self, csv_file, encoding, state):
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                content = f.read()
                if not content.strip():
                    state['empty_content_warning_printed'] = True
                    return None, False

                f.seek(0)
                reader = csv.DictReader(f)
                
                if not reader.fieldnames:
                    return None, False

                fieldnames = [name.strip('\ufeff') for name in reader.fieldnames]
                reader.fieldnames = fieldnames

                missing_fields = self.required_fields - set(fieldnames)
                if missing_fields:
                    raise StructuralError(f"错误：CSV文件缺少必要字段: {', '.join(missing_fields)}")

                devices = self._read_device_rows(reader, state)
                if len(devices) > self.max_devices:
                    raise FileReadError(f"错误：设备数量超过最大限制 ({self.max_devices}台)")
                
                return devices, True

        except (UnicodeDecodeError, csv.Error):
            return None, False
            
        return [], False

    def _read_device_rows(self, reader, state):
        devices = []
        for row in reader:
            if not any(row.values()):
                continue
            
            processed_device = self._validate_and_process_row(row, reader.line_num)
            if processed_device:
                devices.append(processed_device)
        
        return devices

    def _validate_and_process_row(self, row, line_num):
        device_code = row.get('device_code', '').strip()
        if not device_code:
            return {}

        if not re.match(r'^[A-Za-z0-9]+$', device_code) or not re.match(r'^[A-Za-z]', device_code):
            raise FileReadError(f"错误：设备编码格式无效，第{line_num}行: {device_code}")

        if not row.get('start_date') or not row.get('end_date'):
            raise FileReadError(f"错误：日期信息不完整，第{line_num}行: {row}")

        # --- 使用新的验证函数，并让它直接清洗row ---
        if not validate_csv_data(row, mode="daily_consumption"): # 假设默认是daily模式
             raise FileReadError(f"错误：日期验证失败，第{line_num}行: {row}")

        device_data = {key: value.strip() for key, value in row.items()}
        return device_data
