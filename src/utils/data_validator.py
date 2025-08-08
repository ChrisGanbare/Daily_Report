from datetime import datetime


class DataValidator:
    """数据验证类，负责所有数据验证相关操作"""

    def __init__(self):
        """初始化数据验证器"""
        pass

    def validate_date(self, date_string):
        """
        验证日期字符串格式是否正确 (支持 YYYY-MM-DD 和 YYYY/M/D 格式)
        
        Args:
            date_string (str): 日期字符串
            
        Returns:
            bool: 验证结果
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

    def parse_date(self, date_string):
        """
        解析日期字符串，支持多种日期格式
        
        Args:
            date_string (str): 日期字符串
            
        Returns:
            date: 解析后的日期对象
            
        Raises:
            ValueError: 当日期格式不匹配时抛出异常
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

    def validate_csv_data(self, row):
        """
        验证CSV数据行中的日期字段格式和逻辑关系

        Args:
            row (dict): CSV数据行，应包含'start_date'和'end_date'字段

        Returns:
            bool: 验证通过返回True，否则返回False
        """
        # 验证 start_date 和 end_date 字段格式
        try:
            start_date = self.parse_date(row['start_date'])
            end_date = self.parse_date(row['end_date'])
        except ValueError as e:
            print(f"Date format error in row: {row}. Error: {e}")
            return False

        # 验证开始日期不能晚于结束日期
        if start_date > end_date:
            print(f"Date logic error in row: {row}. Start date {row['start_date']} cannot be later than end date {row['end_date']}")
            return False

        return True