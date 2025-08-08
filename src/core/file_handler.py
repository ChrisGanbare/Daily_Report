import os
import csv
import re
from datetime import datetime


class FileHandler:
    """文件处理类，负责所有文件相关操作"""

    def __init__(self):
        """初始化文件处理器"""
        pass

    def read_devices_from_csv(self, csv_file):
        """
        从CSV文件读取设备信息，支持多种编码格式
        
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

    def validate_file_name(self, file_name):
        """
        验证文件名称是否符合规范
        规范格式：设备使用油品名称_设备编码_月份
        示例：AW46抗磨液压油_TW24011700700016_202506.xlsx
        
        Args:
            file_name (str): 文件名
            
        Returns:
            bool: 验证结果
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