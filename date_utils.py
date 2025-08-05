from datetime import datetime


def parse_date(date_str):
    """
    解析日期字符串，支持多种日期格式
    支持的格式：
    1. YYYY-MM-DD (例如: 2025-07-01)
    2. YYYY/M/D (例如: 2025/7/1)
    
    Args:
        date_str (str): 日期字符串
        
    Returns:
        datetime: 解析后的日期对象
        
    Raises:
        ValueError: 当日期格式不匹配时抛出异常
    """
    # 尝试解析标准的 YYYY-MM-DD 格式
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        pass
    
    # 新增: 尝试解析 YYYY/M/D 格式
    try:
        return datetime.strptime(date_str, '%Y/%m/%d')
    except ValueError:
        pass
    
    # 如果以上两种格式都不匹配，抛出异常
    raise ValueError("Invalid date format. Expected 'YYYY-MM-DD' or 'YYYY/M/D'.")


def validate_csv_data(row):
    """
    验证CSV数据行中的日期字段格式和逻辑关系
    
    Args:
        row (dict): CSV数据行，应包含'start_date'和'end_date'字段
        
    Returns:
        bool: 验证通过返回True，否则返回False
    """
    # 验证 start_date 和 end_date 字段格式
    try:
        start_date = parse_date(row['start_date'])
        end_date = parse_date(row['end_date'])
    except ValueError as e:
        print(f"Date format error in row: {row}. Error: {e}")
        return False
    
    # 验证开始日期不能晚于结束日期
    if start_date > end_date:
        print(f"Date logic error in row: {row}. Start date {row['start_date']} cannot be later than end date {row['end_date']}")
        return False
    
    return True