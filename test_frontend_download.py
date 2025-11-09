"""
测试前端下载功能，验证文件格式是否正确
"""
import requests
import json
import tempfile
import os
from pathlib import Path

def test_report_download():
    """测试前端报表下载功能"""
    
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
        
        print(f"响应状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Disposition: {response.headers.get('content-disposition')}")
        
        if response.status_code == 200:
            # 保存文件到临时目录
            temp_dir = Path(tempfile.gettempdir()) / "test_download"
            temp_dir.mkdir(exist_ok=True)
            
            # 从content-disposition中提取文件名
            content_disposition = response.headers.get('content-disposition', '')
            filename = "test_report.xlsx"
            if 'filename=' in content_disposition:
                # 处理URL编码的文件名
                filename_match = content_disposition.split('filename=')[1].strip('"')
                if filename_match:
                    # 处理filename*=utf-8格式
                    if 'filename*=' in content_disposition:
                        filename_part = content_disposition.split('filename*=')[1].strip('"')
                        if 'utf-8\'\'' in filename_part:
                            filename = filename_part.split('utf-8\'\'')[1]
                    else:
                        filename = filename_match
            
            # 确保文件名有正确的扩展名
            if not filename.lower().endswith('.xlsx'):
                filename += '.xlsx'
            
            file_path = temp_dir / filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
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
                print("✓ 文件扩展名表明是Excel文件")
            else:
                print(f"✗ 文件扩展名不是Excel格式: {file_path.suffix}")
                
        else:
            print(f"请求失败: {response.text}")
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")

if __name__ == "__main__":
    print("开始测试前端下载功能...")
    test_report_download()