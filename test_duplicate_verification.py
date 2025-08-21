import tempfile
import os
from src.core.file_handler import FileHandler, FileReadError

def test_multiple_duplicate_devices():
    """测试多次重复的设备编码和日期范围"""
    file_handler = FileHandler()
    
    # 创建包含多次重复设备编码和日期范围的CSV文件
    csv_content = """device_code,start_date,end_date
MO24111301600017,2025/7/1,2025/7/31
MO24111301600017,2025/7/1,2025/7/31
MO24111301600017,2025/7/1,2025/7/31
MO24111301600017,2025/7/1,2025/7/31
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name

    try:
        # 应该在第二次遇到重复设备时抛出FileReadError异常
        devices = file_handler.read_devices_from_csv(csv_file_path)
        print("错误：应该抛出FileReadError异常，但实际上没有抛出")
        print("读取到的设备信息：", devices)
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

def test_different_date_formats():
    """测试不同日期格式但实质相同的日期范围"""
    file_handler = FileHandler()
    
    # 创建包含不同日期格式但实质相同的CSV文件
    csv_content = """device_code,start_date,end_date
MO24111301600017,2025/7/1,2025/7/31
MO24111301600017,2025-07-01,2025-07-31
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name

    try:
        # 应该正常读取两个设备信息（因为日期格式不同，被视为不同日期范围）
        devices = file_handler.read_devices_from_csv(csv_file_path)
        print("正确：成功读取设备信息")
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
    print("=== 测试多次重复设备编码和日期范围的情况 ===")
    result1 = test_multiple_duplicate_devices()
    
    print("\n=== 测试不同日期格式但实质相同的日期范围 ===")
    result2 = test_different_date_formats()
    
    print("\n=== 测试结果总结 ===")
    if result1:
        print("1. 多次重复设备编码和日期范围测试通过")
    else:
        print("1. 多次重复设备编码和日期范围测试失败")
        
    if result2:
        print("2. 不同日期格式但实质相同的日期范围测试通过")
    else:
        print("2. 不同日期格式但实质相同的日期范围测试失败")