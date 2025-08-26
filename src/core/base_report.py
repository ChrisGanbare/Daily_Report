"""
基础报表类模块
提供所有报表生成器的通用功能
"""
import os
from abc import ABC, abstractmethod
from datetime import datetime


class BaseReportGenerator(ABC):
    """
    基础报表生成器类
    提供所有报表生成器的通用功能，如文件操作、日期处理等
    """
    
    def __init__(self):
        """初始化基础报表生成器"""
        pass

    def _validate_date_range(self, start_date, end_date):
        """
        验证日期范围的有效性
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            bool: 日期范围是否有效
            
        Raises:
            ValueError: 日期范围无效时抛出异常
        """
        if start_date > end_date:
            raise ValueError("开始日期不能晚于结束日期")
        return True

    def _create_output_directory(self, output_path):
        """
        创建输出目录
        
        Args:
            output_path (str): 输出文件路径
            
        Returns:
            str: 输出目录路径
        """
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        return output_dir

    @abstractmethod
    def generate_report(self, data, output_file_path, **kwargs):
        """
        生成报表的抽象方法
        
        Args:
            data: 报表数据
            output_file_path (str): 输出文件路径
            **kwargs: 其他参数
            
        Returns:
            bool: 报表生成是否成功
        """
        pass

    def _format_date_for_display(self, date):
        """
        格式化日期用于显示
        
        Args:
            date: 日期对象
            
        Returns:
            str: 格式化后的日期字符串
        """
        if date:
            return date.strftime("%Y-%m-%d")
        return "未知日期"