"""
设备与客户数据仓库
负责所有与设备和客户相关的数据库操作
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, bindparam

from src.logger import logger
from src.config import settings


class DeviceRepository:
    """
    封装了对设备和客户表的数据库访问
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_daily_consumption_raw_data(
        self,
        device_codes: List[str],
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        使用高性能的单一SQL查询，获取用于计算每日消耗的原始数据。
        """
        logger.info(f"开始为设备 {device_codes} 查询每日消耗的原始数据...")
        
        query_template = settings.sql_templates.daily_consumption_raw_query
        if not query_template:
            raise ValueError("每日消耗原始数据查询模板 'daily_consumption_raw_query' 未在配置中找到。")

        params = {
            "start_date_param": start_date,
            "end_date_param": end_date,
            "start_date_param_full": f"{start_date} 00:00:00",
            "end_date_param_full": f"{end_date} 23:59:59",
            "device_codes": tuple(device_codes),
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

    async def get_monthly_consumption_raw_data(
        self,
        device_codes: List[str],
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        使用高性能的单一SQL查询，获取用于计算每月消耗的原始数据。
        """
        logger.info(f"开始为设备 {device_codes} 查询每月消耗的原始数据...")
        
        query_template = settings.sql_templates.monthly_consumption_raw_query
        if not query_template:
            raise ValueError("每月消耗原始数据查询模板 'monthly_consumption_raw_query' 未在配置中找到。")

        params = {
            "start_date_param": start_date,
            "end_date_param": end_date,
            "start_date_param_full": f"{start_date} 00:00:00",
            "end_date_param_full": f"{end_date} 23:59:59",
            "device_codes": tuple(device_codes),
        }

        statement = text(query_template).bindparams(
            bindparam('device_codes', expanding=True)
        )
        
        try:
            result = await self.session.execute(statement, params)
            data = [row._asdict() for row in result.fetchall()]
            logger.info(f"为设备 {device_codes} 查询到 {len(data)} 条每月消耗原始数据记录。")
            return data
        except Exception as e:
            logger.error(f"查询每月消耗原始数据时出错: {e}", exc_info=True)
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
