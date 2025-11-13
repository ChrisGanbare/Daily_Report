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


def validate_csv_data(row, mode="default"):
    """
    验证CSV数据行中的日期字段格式和逻辑关系

    Args:
        row (dict): CSV数据行，应包含'start_date'和'end_date'字段
        mode (str): 验证模式，可选值: "default", "daily_consumption"

    Returns:
        bool: 验证通过返回True，否则返回False
    """
    # 根据模式选择合适的验证函数
    if mode == "daily_consumption":
        return validate_daily_consumption_date_span(row)
    else:
        # 默认验证逻辑
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





def validate_daily_consumption_date_span(row):
    """
    验证每日消耗误差报表的日期范围（小于等于2个月）

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

    # 验证开始日期不能晚于结束日期
    if start_date > end_date:
        print(f"日期逻辑错误: 开始日期 {row['start_date']} 不能晚于结束日期 {row['end_date']}")
        return False

    # 计算总天数
    total_days = (end_date - start_date).days
    
    # 计算年份差和月份差
    year_diff = end_date.year - start_date.year
    month_diff = end_date.month - start_date.month
    
    # 总月份差
    total_month_diff = year_diff * 12 + month_diff
    
    # 检查是否在2个月范围内（范围 <= 2个月）
    if total_month_diff > 2 or (total_month_diff == 2 and total_days > 61):  # 允许最多2个月，但总天数不超过61天
        print(f"日期跨度错误: 从 {row['start_date']} 到 {row['end_date']} 的日期范围超过2个月")
        return False
    
    return True


def validate_error_summary_date_span(row):
    """
    验证误差汇总报表的日期范围（小于等于2个月）

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

    # 验证开始日期不能晚于结束日期
    if start_date > end_date:
        print(f"日期逻辑错误: 开始日期 {row['start_date']} 不能晚于结束日期 {row['end_date']}")
        return False

    # 计算总天数
    total_days = (end_date - start_date).days
    
    # 计算年份差和月份差
    year_diff = end_date.year - start_date.year
    month_diff = end_date.month - start_date.month
    
    # 总月份差
    total_month_diff = year_diff * 12 + month_diff
    
    # 检查是否在2个月范围内（范围 <= 2个月）
    if total_month_diff > 2 or (total_month_diff == 2 and total_days > 61):  # 允许最多2个月，但总天数不超过61天
        print(f"日期跨度错误: 从 {row['start_date']} 到 {row['end_date']} 的日期范围超过2个月")
        return False
    
    return True


def validate_date_span(row):
    """
    验证CSV数据行中的日期字段跨度是否在1个月以内

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

    # 验证日期跨度是否超过1个月
    # 通过将开始日期加1个月后与结束日期比较来实现
    # 需要考虑跨年和月末等情况
    
    # 计算月份差
    if start_date.year == end_date.year:
        month_diff = end_date.month - start_date.month
    else:
        month_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    
    # 如果月份差超过1个月，直接返回False
    if month_diff > 1:
        print(f"日期跨度错误: 从 {row['start_date']} 到 {row['end_date']} 的日期范围超过了1个月")
        return False
    elif month_diff < 1:
        # 如果月份差小于1个月，直接返回True
        return True
    
    # 如果月份差正好是1个月，需要进一步检查具体的日期
    # 在这种情况下，我们需要检查结束日期是否超过开始日期一个月后的日期
    
    # 计算开始日期一个月后的日期
    try:
        if start_date.month == 12:
            # 如果开始日期是12月，一个月后应该是次年1月
            one_month_later = start_date.replace(year=start_date.year + 1, month=1)
        else:
            # 其他情况正常加1个月
            one_month_later = start_date.replace(month=start_date.month + 1)
    except ValueError:
        # 处理月末日期问题，比如1月31日加一个月会出错
        # 在这种情况下，我们将日期设置为下一个月的最后一天
        if start_date.month == 12:
            # 如果是12月，需要跨年
            year = start_date.year + 1
            month = 1
        else:
            year = start_date.year
            month = start_date.month + 1
            
        # 获取下一个月的最后一天
        if month == 2:
            # 2月需要考虑闰年
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                day = 29
            else:
                day = 28
        elif month in [4, 6, 9, 11]:
            day = 30
        else:
            day = 31
            
        one_month_later = datetime(year, month, day)
    
    # 比较结束日期和一个月后的日期
    if end_date > one_month_later:
        print(f"日期跨度错误: 从 {row['start_date']} 到 {row['end_date']} 的日期范围超过了1个月")
        return False
    
    return True