import csv
import os
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
        使用device_code作为设备标识字段

        Args:
            csv_file (str): CSV文件路径

        Returns:
            list: 设备信息列表
        """
        devices = []
        encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312"]

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
                with open(csv_file, "r", encoding=encoding) as f:
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
                    required_fields = {"start_date", "end_date", "device_code"}
                    fieldnames = set(reader.fieldnames)

                    # 检查是否存在设备标识字段
                    has_device_code = "device_code" in fieldnames

                    if not has_device_code:
                        print(
                            "警告：CSV文件缺少设备标识字段，应包含'device_code'"
                        )
                        continue

                    # 读取设备信息
                    for row in reader:
                        # 跳过空行
                        if not any(row.values()):
                            continue

                        # 获取设备标识
                        device_code = (
                            row.get("device_code", "").strip()
                            if has_device_code
                            else ""
                        )

                        # 确保设备标识不为空
                        if not device_code:
                            print(f"警告：跳过设备标识为空的行: {row}")
                            continue

                        devices.append(
                            {
                                "device_code": device_code,
                                "start_date": row["start_date"].strip(),
                                "end_date": row["end_date"].strip(),
                            }
                        )

                    if not devices:
                        print(f"警告：使用 {encoding} 编码读取的CSV文件没有设备信息")
                    else:
                        print(
                            f"成功使用 {encoding} 编码读取设备信息文件，共读取 {len(devices)} 条设备信息"
                        )
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
        print("错误：无法使用任何支持的编码格式读取设备信息文件")
        print(f"支持的编码格式: {supported_encodings}")
        print("请确保设备信息文件是有效的CSV格式，并使用上述编码之一")
        print("建议: 尝试用记事本或Excel重新保存为UTF-8编码的CSV文件")
        return []