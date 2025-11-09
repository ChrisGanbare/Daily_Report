"""
模拟浏览器下载行为，验证文件处理是否正确
"""
import requests
import json
import tempfile
import os
from pathlib import Path
import urllib.parse

def simulate_browser_download():
    """模拟浏览器下载行为"""
    
    # 测试数据
    test_data = {
        "report_type": "daily_consumption",
        "devices": ["MO25050803700004"],  # 只选择一个设备
        "start_date": "2024-10-01",
        "end_date": "2024-10-31"
    }
    
    try:
        # 发送请求到后端API
        response = requests.post(
            "http://127.0.0.1:8000/api/reports/generate",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print("=== 服务器响应信息 ===")
        print(f"响应状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Disposition: {response.headers.get('content-disposition')}")
        
        if response.status_code == 200:
            # 模拟前端文件名提取逻辑
            content_disposition = response.headers.get('content-disposition', '')
            filename = "report.zip"
            
            # 模拟前端JavaScript代码
            if content_disposition:
                # 优先处理 filename*=utf-8 格式（RFC 5987）
                if 'filename*=' in content_disposition:
                    import re
                    utf8_match = re.search(r"filename\*=['\"]?utf-8['\"]?['\\'\\'\\s]*([^;\\s]+)", content_disposition, re.IGNORECASE)
                    if utf8_match and utf8_match.group(1):
                        filename = urllib.parse.unquote(utf8_match.group(1))
                        print(f"使用RFC 5987格式文件名: {filename}")
                else:
                    # 回退到普通 filename 格式
                    filename_match = re.search(r"filename=['\"]?([^;\\s]+)['\"]?", content_disposition, re.IGNORECASE)
                    if filename_match and filename_match.group(1):
                        filename = urllib.parse.unquote(filename_match.group(1))
                        print(f"使用普通格式文件名: {filename}")
            
            print(f"最终文件名: {filename}")
            
            # 保存文件到下载目录
            download_dir = Path.home() / "Downloads"
            if not download_dir.exists():
                download_dir = Path(tempfile.gettempdir()) / "downloads"
                download_dir.mkdir(exist_ok=True)
            
            file_path = download_dir / filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"\n=== 文件保存信息 ===")
            print(f"文件已保存到: {file_path}")
            print(f"文件大小: {os.path.getsize(file_path)} 字节")
            
            # 检查文件类型
            with open(file_path, 'rb') as f:
                file_header = f.read(8)  # 读取文件头
                
            print(f"文件头签名: {file_header.hex()}")
            
            # 检查是否是Excel文件
            if file_header.startswith(b'PK\x03\x04'):
                print("✓ 文件是ZIP格式（Excel .xlsx文件实际上是ZIP格式）")
                
                # 如果是ZIP文件，检查内容
                import zipfile
                try:
                    with zipfile.ZipFile(file_path, 'r') as zipf:
                        file_list = zipf.namelist()
                        print(f"ZIP文件内容: {file_list}")
                        
                        # 检查是否包含XML文件（正常的Excel文件结构）
                        xml_files = [f for f in file_list if f.endswith('.xml')]
                        if xml_files:
                            print("✓ 包含XML文件 - 这是正常的Excel文件结构")
                            print("\n=== 重要说明 ===")
                            print("用户看到的'一堆包括xml的零散文件'可能是因为：")
                            print("1. 文件被错误地识别为ZIP压缩包并被解压")
                            print("2. 用户手动解压了.xlsx文件（.xlsx实际上是ZIP格式）")
                            print("3. 系统或浏览器设置问题导致文件被错误处理")
                            print("\n解决方案：")
                            print("1. 确保文件以.xlsx扩展名保存")
                            print("2. 不要手动解压下载的文件")
                            print("3. 文件应该用Excel或兼容的电子表格软件打开")
                        else:
                            print("✗ 不包含XML文件 - 可能不是有效的Excel文件")
                            
                except zipfile.BadZipFile:
                    print("✗ 不是有效的ZIP文件")
                    
            elif file_header.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
                print("✓ 文件是旧的Excel格式 (.xls)")
            else:
                print("✗ 文件格式未知")
                
            # 检查文件扩展名
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                print(f"✓ 文件扩展名表明是Excel文件: {file_path.suffix}")
            else:
                print(f"✗ 文件扩展名不是Excel格式: {file_path.suffix}")
                print("这可能是问题的根源！")
                
            # 验证文件是否可以正常打开
            try:
                import openpyxl
                wb = openpyxl.load_workbook(file_path)
                sheet_names = wb.sheetnames
                print(f"✓ 文件可以正常用openpyxl打开，包含工作表: {sheet_names}")
                wb.close()
            except Exception as e:
                print(f"✗ 文件无法用openpyxl打开: {e}")
                
        else:
            print(f"请求失败: {response.text}")
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始模拟浏览器下载行为...")
    simulate_browser_download()