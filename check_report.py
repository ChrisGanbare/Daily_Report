import asyncio
from database import get_db_session
from services.report_service import ReportService
from repositories.device_repository import DeviceRepository

async def check_report_file():
    try:
        async with get_db_session() as session:
            repo = DeviceRepository(session)
            service = ReportService(repo)
            
            devices = await repo.get_devices_with_customers()
            if devices:
                device_code = devices[0]['code']
                print(f'为设备 {device_code} 生成报表...')
                
                result = await service.generate_report(
                    'daily_consumption',
                    [device_code],
                    '2024-10-01',
                    '2024-10-31'
                )
                
                print(f'报表文件路径: {result}')
                print(f'文件是否存在: {result.exists()}')
                
                if result.exists():
                    print(f'文件大小: {result.stat().st_size} 字节')
                    
                    # 检查文件内容
                    with open(result, 'rb') as f:
                        header = f.read(100)
                        print(f'文件头签名: {header[:10]}')
                        
                        # 检查是否是Excel文件
                        if header.startswith(b'PK'):
                            print('文件格式: Excel (.xlsx)')
                        else:
                            print('文件格式: 未知')
                            print(f'文件内容预览: {header}')
                            
                            # 读取更多内容查看
                            f.seek(0)
                            content = f.read(500)
                            print(f'文件内容前500字节: {content}')
                else:
                    print('文件不存在')
                
    except Exception as e:
        print(f'检查过程中出错: {e}')

if __name__ == "__main__":
    asyncio.run(check_report_file())