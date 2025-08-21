import sys
import os

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from src.utils.date_utils import validate_csv_data

def test_validate_csv_data_with_slash_format():
    """测试validate_csv_data函数是否可以正确解析/分隔的日期格式"""
    # 测试有效的/分隔日期格式
    row1 = {
        "start_date": "2025/7/1",
        "end_date": "2025/7/31"
    }
    
    result1 = validate_csv_data(row1)
    print(f"测试1 - 有效的/分隔日期格式: {row1}")
    print(f"结果: {result1}")
    
    # 测试无效的开始日期
    row2 = {
        "start_date": "invalid-date",
        "end_date": "2025/7/31"
    }
    
    result2 = validate_csv_data(row2)
    print(f"\n测试2 - 无效的开始日期: {row2}")
    print(f"结果: {result2}")
    
    # 测试无效的结束日期
    row3 = {
        "start_date": "2025/7/1",
        "end_date": "invalid-date"
    }
    
    result3 = validate_csv_data(row3)
    print(f"\n测试3 - 无效的结束日期: {row3}")
    print(f"结果: {result3}")
    
    # 测试开始日期晚于结束日期的情况
    row4 = {
        "start_date": "2025/7/31",
        "end_date": "2025/7/1"
    }
    
    result4 = validate_csv_data(row4)
    print(f"\n测试4 - 开始日期晚于结束日期: {row4}")
    print(f"结果: {result4}")
    
    # 测试混合日期格式
    row5 = {
        "start_date": "2025/7/1",
        "end_date": "2025-07-31"
    }
    
    result5 = validate_csv_data(row5)
    print(f"\n测试5 - 混合日期格式: {row5}")
    print(f"结果: {result5}")

if __name__ == "__main__":
    print("=== 测试validate_csv_data函数对/分隔日期格式的支持 ===")
    test_validate_csv_data_with_slash_format()