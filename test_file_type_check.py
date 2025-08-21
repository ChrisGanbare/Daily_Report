import tempfile
import os
from src.core.file_handler import FileHandler, FileReadError

def test_csv_file_type():
    """测试CSV文件类型检查"""
    file_handler = FileHandler()
    
    # 创建CSV文件
    csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-31
DEV002,2025-07-01,2025-07-31
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name

    try:
        # 应该正常读取CSV文件
        devices = file_handler.read_devices_from_csv(csv_file_path)
        print("正确：成功读取CSV文件")
        print("读取到的设备信息数量：", len(devices))
        return True
    except FileReadError as e:
        print("错误：读取CSV文件时发生FileReadError异常")
        print("异常信息：", str(e))
        return False
    except Exception as e:
        print("错误：读取CSV文件时发生其他异常")
        print("异常类型：", type(e))
        print("异常信息：", str(e))
        return False
    finally:
        os.unlink(csv_file_path)

def test_non_csv_file_type():
    """测试非CSV文件类型检查"""
    file_handler = FileHandler()
    
    # 创建TXT文件（非CSV格式）
    txt_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-31
DEV002,2025-07-01,2025-07-31
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(txt_content)
        txt_file_path = f.name

    try:
        # 应该抛出FileReadError异常
        devices = file_handler.read_devices_from_csv(txt_file_path)
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
        os.unlink(txt_file_path)

def test_uppercase_csv_file_type():
    """测试大写CSV文件扩展名"""
    file_handler = FileHandler()
    
    # 创建大写扩展名的CSV文件
    csv_content = """device_code,start_date,end_date
DEV001,2025-07-01,2025-07-31
DEV002,2025-07-01,2025-07-31
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".CSV", delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name

    try:
        # 应该正常读取大写扩展名的CSV文件
        devices = file_handler.read_devices_from_csv(csv_file_path)
        print("正确：成功读取大写扩展名的CSV文件")
        print("读取到的设备信息数量：", len(devices))
        return True
    except FileReadError as e:
        print("错误：读取大写扩展名的CSV文件时发生FileReadError异常")
        print("异常信息：", str(e))
        return False
    except Exception as e:
        print("错误：读取大写扩展名的CSV文件时发生其他异常")
        print("异常类型：", type(e))
        print("异常信息：", str(e))
        return False
    finally:
        os.unlink(csv_file_path)

if __name__ == "__main__":
    print("=== 测试CSV文件类型检查 ===")
    result1 = test_csv_file_type()
    
    print("\n=== 测试非CSV文件类型检查 ===")
    result2 = test_non_csv_file_type()
    
    print("\n=== 测试大写CSV文件扩展名 ===")
    result3 = test_uppercase_csv_file_type()
    
    print("\n=== 测试结果总结 ===")
    if result1:
        print("1. CSV文件类型检查测试通过")
    else:
        print("1. CSV文件类型检查测试失败")
        
    if result2:
        print("2. 非CSV文件类型检查测试通过")
    else:
        print("2. 非CSV文件类型检查测试失败")
        
    if result3:
        print("3. 大写CSV文件扩展名测试通过")
    else:
        print("3. 大写CSV文件扩展名测试失败")