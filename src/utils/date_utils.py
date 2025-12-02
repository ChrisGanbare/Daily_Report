from datetime import datetime
from dateutil.relativedelta import relativedelta

def parse_date(date_str):
    """
    解析日期字符串，支持多种常用格式。
    """
    supported_formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S'
    ]
    for fmt in supported_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    raise ValueError(f"日期格式无效: '{date_str}'. 请使用 'YYYY-MM-DD' 或 'YYYY/MM/DD' 格式。")

def validate_csv_data(row, mode="default"):
    """
    验证并清洗CSV数据行中的日期字段。
    验证通过后，会将日期统一为 'YYYY-MM-DD' 格式。
    """
    try:
        start_date_obj = parse_date(row["start_date"])
        end_date_obj = parse_date(row["end_date"])
        
        # --- 数据清洗：统一格式 ---
        row['start_date'] = start_date_obj.strftime('%Y-%m-%d')
        row['end_date'] = end_date_obj.strftime('%Y-%m-%d')

    except (ValueError, KeyError) as e:
        print(f"日期格式或字段错误: {row}。错误: {e}")
        return False

    # 验证开始日期不能晚于结束日期
    if start_date_obj > end_date_obj:
        print(f"日期逻辑错误: 开始日期 {row['start_date']} 不能晚于结束日期 {row['end_date']}")
        return False

    # 根据模式选择不同的日期跨度验证
    if mode == "monthly_consumption":
        from dateutil.relativedelta import relativedelta
        if end_date_obj > start_date_obj + relativedelta(months=12):
            print(f"日期跨度错误: {row['start_date']} 到 {row['end_date']} 范围超过12个月。")
            return False
    elif mode == "daily_consumption":
        from dateutil.relativedelta import relativedelta
        if end_date_obj > start_date_obj + relativedelta(months=2):
             print(f"日期跨度错误: {row['start_date']} 到 {row['end_date']} 范围超过2个月。")
             return False
    
    return True

def validate_date_span(row, max_months=1):
    """
    验证日期跨度是否在指定月数范围内。
    
    Args:
        row (dict): 包含 'start_date' 和 'end_date' 的字典
        max_months (int): 最大允许的月数，默认为1
    
    Returns:
        bool: 如果日期跨度在允许范围内返回True，否则返回False
    """
    try:
        start_date_obj = parse_date(row["start_date"])
        end_date_obj = parse_date(row["end_date"])
        
        # 验证开始日期不能晚于结束日期
        if start_date_obj > end_date_obj:
            print(f"日期逻辑错误: 开始日期 {row['start_date']} 不能晚于结束日期 {row['end_date']}")
            return False
        
        # 计算日期跨度
        if end_date_obj > start_date_obj + relativedelta(months=max_months):
            print(f"日期跨度错误: {row['start_date']} 到 {row['end_date']} 范围超过{max_months}个月。")
            return False
        
        return True
    except (ValueError, KeyError) as e:
        print(f"日期格式或字段错误: {row}。错误: {e}")
        return False
