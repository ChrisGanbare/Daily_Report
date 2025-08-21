import tempfile
import os
from src.core.file_handler import FileHandler, FileReadError

def test_duplicate_check_all_rows():
    """测试修复后检查所有具有相同设备编码的设备"""
    file_handler = FileHandler()
    
    # 创建包含多个相同设备编码的CSV文件，其中第1个和第3个设备日期范围相同
    csv_content = """device_code,start_date,end_date
MO24111301600017,2025/7/1,2025/7/31
MO24111301600017,2025/8/1,2025/8/31
MO24111301600017,2025-07-01,2025-07-31
MO24111301600017,2025/9/1,2025/9/30
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name

    try:
        # 应该抛出FileReadError异常，因为第1个和第3个设备日期范围实质相同
        devices = file_handler.read_devices_from_csv(csv_file_path)
        print("问题：应该抛出FileReadError异常，但实际上没有抛出")
        print("读取到的设备信息数量：", len(devices))
        for i, device in enumerate(devices):
            print(f"设备 {i+1}：{device}")
        return False
    except FileReadError as e:
        print("正确：捕获到FileReadError异常")
        print("异常信息：", str(e))
        return True
    except Exception as e:
        print("错误：捕获到其他异常类型")
        print("异常类型：", type(e))
        print("异常信息：", str(e))
        return False
    finally:
        os.unlink(csv_file_path)

def test_duplicate_check_no_duplicates():
    """测试没有重复的情况"""
    file_handler = FileHandler()
    
    # 创建包含多个相同设备编码但日期范围都不同的CSV文件
    csv_content = """device_code,start_date,end_date
MO24111301600017,2025/7/1,2025/7/31
MO24111301600017,2025/8/1,2025/8/31
MO24111301600017,2025/9/1,2025/9/30
MO24111301600017,2025/10/1,2025/10/31
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name

    try:
        # 应该正常读取所有设备信息
        devices = file_handler.read_devices_from_csv(csv_file_path)
        print("正确：成功读取所有设备信息")
        print("读取到的设备信息数量：", len(devices))
        for i, device in enumerate(devices):
            print(f"设备 {i+1}：{device}")
        return True
    except Exception as e:
        print("错误：不应该抛出异常")
        print("异常类型：", type(e))
        print("异常信息：", str(e))
        return False
    finally:
        os.unlink(csv_file_path)

if __name__ == "__main__":
    print("=== 测试修复后检查所有具有相同设备编码的设备 ===")
    result1 = test_duplicate_check_all_rows()
    
    print("\n=== 测试没有重复的情况 ===")
    result2 = test_duplicate_check_no_duplicates()
    
    print("\n=== 测试结果总结 ===")
    if result1:
        print("1. 修复后检查所有具有相同设备编码的设备测试通过")
    else:
        print("1. 修复后检查所有具有相同设备编码的设备测试未通过")
        
    if result2:
        print("2. 没有重复的情况测试通过")
    else:
        print("2. 没有重复的情况测试未通过")