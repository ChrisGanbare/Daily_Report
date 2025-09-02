import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from .base_report import BaseReportGenerator


class RefuelingDetailsReportGenerator(BaseReportGenerator):
    """加注明细报表生成器类，负责生成设备加注明细Excel报表"""

    def __init__(self):
        """初始化加注明细报表生成器"""
        super().__init__()

    def generate_report(self, refueling_data, output_file_path, **kwargs):
        """
        生成加注明细报表的实现方法

        Args:
            refueling_data: 加注明细数据
            output_file_path (str): 输出文件路径
            **kwargs: 其他参数

        Returns:
            bool: 报表生成是否成功
        """
        device_code = kwargs.get('device_code')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        customer_name = kwargs.get('customer_name')
        columns = kwargs.get('columns')

        return self.generate_refueling_details_report(
            refueling_data, output_file_path, device_code, start_date, end_date,
            customer_name, columns
        )

    def generate_refueling_details_report(
        self,
        refueling_data,
        output_file_path,
        device_code,
        start_date,
        end_date,
        customer_name=None,
        columns=None
    ):
        """
        生成加注明细Excel报告文件

        Args:
            refueling_data (list): 加注明细数据列表
            output_file_path (str): 输出文件路径
            device_code (str): 设备编码
            start_date (date): 开始日期
            end_date (date): 结束日期
            customer_name (str): 客户名称
            columns (list): 列名列表
        """
        try:
            # 初始化工作簿
            wb = Workbook()
            ws = wb.active
            ws.title = "加注明细"

            # 添加列标题（直接从第一行开始，不添加合并的标题行）
            if columns:
                ws.append(columns)
            else:
                ws.append([
                    '订单序号', '加注时间', '油品序号', '油品名称', '水油比：水值', '水油比：油值',
                    '水加注值', '油加注值', '原油剩余量', '原油剩余比例', '油加设量', 
                    '是否结算：1=待结算 2=待生效 3=已结算', '加注模式：1=近程自动 2=远程自动 3=手动'
                ])

            # 写入数据
            for row in refueling_data:
                # 确保row是列表或元组格式
                if isinstance(row, (list, tuple)):
                    ws.append(list(row))
                else:
                    # 如果是字典格式，按列顺序提取值
                    if columns and isinstance(row, dict):
                        row_data = [row.get(col, '') for col in columns]
                        ws.append(row_data)
                    else:
                        ws.append([str(row)])

            # 调整列宽
            for col_idx, col in enumerate(ws.columns, 1):
                max_length = 0
                # 获取列字母标识
                column_letter = ws.cell(row=1, column=col_idx).column_letter
                for cell in col:
                    try:
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column_letter].width = min(adjusted_width, 50)

            # 保存文件
            wb.save(output_file_path)
            # print(f"  成功生成加注明细报表: {output_file_path}")
            return True
            
        except Exception as e:
            print(f"  生成加注明细报表失败: {e}")
            raise
        finally:
            # 确保工作簿被关闭
            if 'wb' in locals():
                try:
                    wb.close()
                except:
                    pass
