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
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass

    # 新增: 尝试解析 YYYY/M/D 格式
    try:
        return datetime.strptime(date_str, "%Y/%m/%d")
    except ValueError:
        pass

    # 如果以上两种格式都不匹配，抛出异常
    raise ValueError("日期格式无效。请使用 'YYYY-MM-DD' 或 'YYYY/M/D' 格式（例如: 2025-07-01 或 2025/7/1）")


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
        start_date = parse_date(row["start_date"])
        end_date = parse_date(row["end_date"])
    except ValueError as e:
        print(f"日期格式错误: {row}。{e}")
        return False

    # 验证开始日期不能晚于结束日期
    if start_date > end_date:
        print(f"日期逻辑错误: 开始日期 {row['start_date']} 不能晚于结束日期 {row['end_date']}")
        return False

    return True

def validate_date_span(row):
    """
    验证CSV数据行中的日期字段跨度是否在2个月以内

    Args:
        row (dict): CSV数据行，应包含'start_date'和'end_date'字段

    Returns:
        bool: 验证通过返回True，否则返回False
    """
    try:
        start_date = parse_date(row["start_date"])
        end_date = parse_date(row["end_date"])
    except ValueError as e:
        print(f"日期格式错误: {row}。{e}")
        return False

    # 验证日期跨度是否超过2个月
    # 通过将开始日期加2个月后与结束日期比较来实现
    # 需要考虑跨年和月末等情况
    if start_date.year == end_date.year:
        month_diff = end_date.month - start_date.month
    else:
        month_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    
    # 考虑到日期的具体天数，如果结束日期的天数小于开始日期的天数，
    # 实际月份跨度会比计算的月份数少一天到一个月不等
    # 因此，如果月份差为2时，还需要进一步检查具体的日期
    if month_diff > 1:
        print(f"日期跨度错误: 从 {row['start_date']} 到 {row['end_date']} 的日期范围超过了1个月")
        return False
    elif month_diff == 1 and end_date.day >= start_date.day:
        print(f"日期跨度错误: 从 {row['start_date']} 到 {row['end_date']} 的日期范围超过了1个月")
        return False
    
    return True