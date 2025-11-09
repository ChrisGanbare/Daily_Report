import asyncio
from src.database import get_db_session
from src.repositories.device_repository import DeviceRepository

async def test_db_connection():
    try:
        async with get_db_session() as session:
            repo = DeviceRepository(session)
            
            # 测试获取设备列表
            devices = await repo.get_devices_with_customers()
            print(f'获取到 {len(devices)} 个设备:')
            for device in devices[:5]:  # 只显示前5个
                print(f'  设备编码: {device["code"]}, 客户名称: {device["name"]}')
            
            if devices:
                # 测试查询设备数据
                device_code = devices[0]['code']
                print(f'\n测试查询设备 {device_code} 的数据...')
                
                try:
                    data = await repo.get_daily_consumption_raw_data(
                        [device_code], '2024-01-01', '2024-01-31'
                    )
                    print(f'查询到 {len(data)} 条数据')
                    if data:
                        print('第一条数据示例:')
                        for key, value in data[0].items():
                            print(f'  {key}: {value}')
                except Exception as e:
                    print(f'查询数据时出错: {e}')
    except Exception as e:
        print(f'数据库连接错误: {e}')

if __name__ == "__main__":
    asyncio.run(test_db_connection())