"""
设备与客户数据仓库
负责所有与设备和客户相关的数据库操作
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, bindparam

from logger import logger
from config import settings

# --- 异步缓存实现 ---
class AsyncTTLCache:
    """异步TTL缓存实现"""
    
    def __init__(self, maxsize=50, ttl=600):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key):
        """获取缓存值"""
        async with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if asyncio.get_event_loop().time() - timestamp < self.ttl:
                    return value
                else:
                    del self._cache[key]
            return None
    
    async def set(self, key, value):
        """设置缓存值"""
        async with self._lock:
            # 如果超过最大大小，删除最旧的条目
            if len(self._cache) >= self.maxsize:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
            
            self._cache[key] = (value, asyncio.get_event_loop().time())

def async_cached(cache):
    """异步缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键 - 只使用函数名和实际参数，忽略self实例
            # 对于实例方法，args[0]是self，我们只需要实际的参数
            actual_args = args[1:] if args and hasattr(args[0], '__class__') else args
            key = (func.__name__, actual_args, tuple(sorted(kwargs.items())))
            
            # 尝试从缓存获取
            cached_result = await cache.get(key)
            if cached_result is not None:
                logger.info(f"缓存命中: {func.__name__}")
                return cached_result
            
            # 执行函数并缓存结果
            logger.info(f"缓存未命中，执行函数: {func.__name__}")
            result = await func(*args, **kwargs)
            await cache.set(key, result)
            
            return result
        
        return wrapper
    
    return decorator

# --- 缓存配置 ---
# 报表数据缓存：最大缓存50个查询，每个查询结果存活10分钟
report_data_cache = AsyncTTLCache(maxsize=50, ttl=600)


class DeviceRepository:
    """
    封装了对设备和客户表的数据库访问
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    @async_cached(report_data_cache)
    async def get_daily_consumption_raw_data(
        self,
        device_codes: Tuple[str, ...], # 参数必须是可哈希的，所以用元组
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        使用高性能的单一SQL查询，获取用于计算每日消耗的原始数据。
        """
        
        query_template = settings.sql_templates.daily_consumption_raw_query
        if not query_template:
            raise ValueError("每日消耗原始数据查询模板 'daily_consumption_raw_query' 未在配置中找到。")

        params = {
            "start_date_param": start_date,
            "end_date_param": end_date,
            "start_date_param_full": f"{start_date} 00:00:00",
            "end_date_param_full": f"{end_date} 23:59:59",
            "device_codes": device_codes,
        }

        statement = text(query_template).bindparams(
            bindparam('device_codes', expanding=True)
        )
        
        try:
            result = await self.session.execute(statement, params)
            data = [row._asdict() for row in result.fetchall()]
            logger.info(f"为设备 {device_codes} 查询到 {len(data)} 条原始数据记录。")
            return data
        except Exception as e:
            logger.error(f"查询每日消耗原始数据时出错: {e}", exc_info=True)
            raise



    async def get_devices_with_customers(
        self,
        customer_name: Optional[str] = None,
        device_code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        通过一次高效的JOIN查询，获取所有正常状态的设备及其关联的客户名称。
        """
        try:
            query_sql = """
                SELECT
                    d.device_code AS code,
                    c.customer_name AS name
                FROM
                    oil.t_device d
                JOIN
                    oil.t_customer c ON d.customer_id = c.id
                WHERE
                    d.del_status = 1
                    AND c.status = 1
            """
            params = {}
            if customer_name:
                query_sql += " AND c.customer_name LIKE :customer_name"
                params["customer_name"] = f"%{customer_name}%"

            if device_code:
                query_sql += " AND d.device_code LIKE :device_code"
                params["device_code"] = f"%{device_code}%"

            query_sql += " ORDER BY c.customer_name, d.device_code;"

            statement = text(query_sql)
            result = await self.session.execute(statement, params)
            
            devices = [row._asdict() for row in result.fetchall()]
            return devices
        except Exception as e:
            logger.error(f"查询设备和客户信息时出错: {e}", exc_info=True)
            raise

    @async_cached(report_data_cache)
    async def get_inventory_raw_data(
        self,
        device_codes: Tuple[str, ...],
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        获取库存报表的原始数据。
        """
        try:
            query_template = settings.sql_templates.inventory_query
            if not query_template:
                raise ValueError("库存查询模板 'inventory_query' 未在配置中找到。")

            # 为每个设备单独查询库存数据
            all_data = []
            for device_code in device_codes:
                # 获取设备ID
                device_id_query = text(settings.sql_templates.device_id_query)
                device_id_result = await self.session.execute(
                    device_id_query, {"device_code": device_code}
                )
                device_row = device_id_result.fetchone()
                
                if not device_row:
                    logger.warning(f"设备 {device_code} 未找到，跳过库存查询")
                    continue
                
                device_id = device_row[0]
                
                # 执行库存查询
                formatted_query = query_template.format(
                    device_id=device_id,
                    start_date=start_date,
                    end_condition=f"{end_date} 23:59:59"
                )
                
                statement = text(formatted_query)
                result = await self.session.execute(statement)
                device_data = [row._asdict() for row in result.fetchall()]
                
                # 添加设备编码信息
                for row in device_data:
                    row['device_code'] = device_code
                
                all_data.extend(device_data)
            
            logger.info(f"为设备 {device_codes} 查询到 {len(all_data)} 条库存数据记录。")
            return all_data
        except Exception as e:
            logger.error(f"查询库存数据时出错: {e}", exc_info=True)
            raise

    @async_cached(report_data_cache)
    async def get_refueling_details_raw_data(
        self,
        device_codes: Tuple[str, ...],
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        获取加注明细报表的原始数据。
        """
        try:
            query_template = settings.sql_templates.refueling_details_query
            if not query_template:
                raise ValueError("加注明细查询模板 'refueling_details_query' 未在配置中找到。")

            # 为每个设备单独查询加注明细数据
            all_data = []
            for device_code in device_codes:
                # 获取设备ID
                device_id_query = text(settings.sql_templates.device_id_query)
                device_id_result = await self.session.execute(
                    device_id_query, {"device_code": device_code}
                )
                device_row = device_id_result.fetchone()
                
                if not device_row:
                    logger.warning(f"设备 {device_code} 未找到，跳加注明细查询")
                    continue
                
                device_id = device_row[0]
                
                # 执行加注明细查询
                formatted_query = query_template.format(
                    device_id=device_id,
                    start_date=start_date,
                    end_condition=f"{end_date} 23:59:59"
                )
                
                statement = text(formatted_query)
                result = await self.session.execute(statement)
                device_data = [row._asdict() for row in result.fetchall()]
                
                # 添加设备编码信息
                for row in device_data:
                    row['device_code'] = device_code
                
                all_data.extend(device_data)
            
            logger.info(f"为设备 {device_codes} 查询到 {len(all_data)} 条加注明细数据记录。")
            return all_data
        except Exception as e:
            logger.error(f"查询加注明细数据时出错: {e}", exc_info=True)
            raise

    @async_cached(report_data_cache)
    async def get_error_summary_raw_data(
        self,
        device_codes: Tuple[str, ...],
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        获取误差汇总报表的原始数据。
        """
        try:
            # 获取每日消耗数据用于误差计算
            daily_data = await self.get_daily_consumption_raw_data(
                device_codes, start_date, end_date
            )
            
            # 获取离线事件数据
            offline_query_template = settings.sql_templates.error_summary_offline_query
            if not offline_query_template:
                raise ValueError("离线事件查询模板 'error_summary_offline_query' 未在配置中找到。")

            params = {
                "start_date_param_full": f"{start_date} 00:00:00",
                "end_date_param_full": f"{end_date} 23:59:59",
                "device_codes": device_codes,
            }

            statement = text(offline_query_template).bindparams(
                bindparam('device_codes', expanding=True)
            )
            
            offline_result = await self.session.execute(statement, params)
            offline_data = [row._asdict() for row in offline_result.fetchall()]
            
            # 合并数据
            combined_data = {
                "daily_consumption": daily_data,
                "offline_events": offline_data
            }
            
            logger.info(f"为设备 {device_codes} 查询到误差汇总数据：每日消耗 {len(daily_data)} 条，离线事件 {len(offline_data)} 条。")
            return combined_data
        except Exception as e:
            logger.error(f"查询误差汇总数据时出错: {e}", exc_info=True)
            raise

    @async_cached(report_data_cache)
    async def get_customer_statement_raw_data(
        self,
        device_codes: Tuple[str, ...],
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        获取客户对账单的原始数据。
        """
        try:
            # 客户对账单需要每日消耗数据
            daily_data = await self.get_daily_consumption_raw_data(
                device_codes, start_date, end_date
            )
            
            logger.info(f"为设备 {device_codes} 查询到客户对账单数据：{len(daily_data)} 条记录。")
            return daily_data
        except Exception as e:
            logger.error(f"查询客户对账单数据时出错: {e}", exc_info=True)
            raise