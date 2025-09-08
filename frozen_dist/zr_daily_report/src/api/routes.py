"""
RESTful API路由定义
提供完整的API接口
"""

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from ..core.async_processor import AsyncTaskManager
from ..core.dependency_injection import get_service

# 创建路由器
router = APIRouter(prefix="/api/v1")


# 数据模型
class DeviceCreate(BaseModel):
    device_code: str
    customer_id: int
    oil_type: str = "切削液"
    description: Optional[str] = None


class DeviceUpdate(BaseModel):
    customer_id: Optional[int] = None
    oil_type: Optional[str] = None
    description: Optional[str] = None


class InventoryQuery(BaseModel):
    device_code: str
    start_date: date
    end_date: date


class ReportGenerateRequest(BaseModel):
    devices: List[InventoryQuery]
    report_type: str  # 'inventory' 或 'statement'
    output_format: str = "xlsx"


class TaskResponse(BaseModel):
    task_id: str
    status: str
    progress: int = 0
    message: str = ""
    created_at: datetime
    updated_at: datetime


# 设备管理API
@router.get("/devices")
async def get_devices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = Query(None),
    device_code: Optional[str] = Query(None),
):
    """获取设备列表"""
    try:
        db_service = get_service("IDatabaseService")

        # 构建查询条件
        where_clause = "WHERE 1=1"
        params = []

        if customer_id:
            where_clause += " AND customer_id = %s"
            params.append(customer_id)

        if device_code:
            where_clause += " AND device_code LIKE %s"
            params.append(f"%{device_code}%")

        # 分页查询
        offset = (page - 1) * size
        query = f"""
            SELECT d.*, c.customer_name 
            FROM oil.t_device d
            LEFT JOIN oil.t_customer c ON d.customer_id = c.id
            {where_clause}
            ORDER BY d.create_time DESC
            LIMIT %s OFFSET %s
        """
        params.extend([size, offset])

        devices = db_service.execute_query(query, tuple(params))

        # 获取总数
        count_query = f"""
            SELECT COUNT(*) as total
            FROM oil.t_device d
            {where_clause}
        """
        count_params = params[:-2] if len(params) > 2 else []
        total_result = db_service.execute_query(count_query, tuple(count_params))
        total = total_result[0]["total"] if total_result else 0

        return {
            "data": devices,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "pages": (total + size - 1) // size,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/{device_id}")
async def get_device(device_id: int = Path(..., ge=1)):
    """获取单个设备详情"""
    try:
        db_service = get_service("IDatabaseService")

        query = """
            SELECT d.*, c.customer_name 
            FROM oil.t_device d
            LEFT JOIN oil.t_customer c ON d.customer_id = c.id
            WHERE d.id = %s
        """

        devices = db_service.execute_query(query, (device_id,))

        if not devices:
            raise HTTPException(status_code=404, detail="设备不存在")

        return devices[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/devices")
async def create_device(device: DeviceCreate):
    """创建设备"""
    try:
        db_service = get_service("IDatabaseService")

        # 检查设备编码是否已存在
        check_query = "SELECT id FROM oil.t_device WHERE device_code = %s"
        existing = db_service.execute_query(check_query, (device.device_code,))

        if existing:
            raise HTTPException(status_code=400, detail="设备编码已存在")

        # 插入新设备
        insert_query = """
            INSERT INTO oil.t_device (device_code, customer_id, oil_type, description, create_time)
            VALUES (%s, %s, %s, %s, NOW())
        """

        db_service.execute_query(
            insert_query,
            (
                device.device_code,
                device.customer_id,
                device.oil_type,
                device.description,
            ),
        )

        return {"message": "设备创建成功", "device_code": device.device_code}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/devices/{device_id}")
async def update_device(device_id: int, device: DeviceUpdate):
    """更新设备"""
    try:
        db_service = get_service("IDatabaseService")

        # 检查设备是否存在
        check_query = "SELECT id FROM oil.t_device WHERE id = %s"
        existing = db_service.execute_query(check_query, (device_id,))

        if not existing:
            raise HTTPException(status_code=404, detail="设备不存在")

        # 构建更新语句
        update_fields = []
        params = []

        if device.customer_id is not None:
            update_fields.append("customer_id = %s")
            params.append(device.customer_id)

        if device.oil_type is not None:
            update_fields.append("oil_type = %s")
            params.append(device.oil_type)

        if device.description is not None:
            update_fields.append("description = %s")
            params.append(device.description)

        if not update_fields:
            raise HTTPException(status_code=400, detail="没有提供更新字段")

        update_fields.append("update_time = NOW()")
        params.append(device_id)

        update_query = f"""
            UPDATE oil.t_device 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """

        db_service.execute_query(update_query, tuple(params))

        return {"message": "设备更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/devices/{device_id}")
async def delete_device(device_id: int):
    """删除设备"""
    try:
        db_service = get_service("IDatabaseService")

        # 检查设备是否存在
        check_query = "SELECT id FROM oil.t_device WHERE id = %s"
        existing = db_service.execute_query(check_query, (device_id,))

        if not existing:
            raise HTTPException(status_code=404, detail="设备不存在")

        # 软删除
        delete_query = (
            "UPDATE oil.t_device SET deleted = 1, update_time = NOW() WHERE id = %s"
        )
        db_service.execute_query(delete_query, (device_id,))

        return {"message": "设备删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 库存数据API
@router.get("/devices/{device_id}/inventory")
async def get_device_inventory(
    device_id: int, start_date: date = Query(...), end_date: date = Query(...)
):
    """获取设备库存数据"""
    try:
        db_service = get_service("IDatabaseService")
        cache_service = get_service("ICacheService")

        # 生成缓存键
        cache_key = cache_service.generate_cache_key(
            "inventory", device_id, start_date, end_date
        )

        # 尝试从缓存获取
        cached_data = cache_service.get(cache_key)
        if cached_data:
            return cached_data

        # 查询数据库
        query = """
            SELECT * FROM inventory_data 
            WHERE device_id = %s AND date BETWEEN %s AND %s
            ORDER BY date
        """

        data = db_service.execute_query(query, (device_id, start_date, end_date))

        # 缓存结果
        cache_service.set(cache_key, data, ttl=1800)

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 报表生成API
@router.post("/reports/generate")
async def generate_report(request: ReportGenerateRequest):
    """生成报表"""
    try:
        task_id = str(uuid.uuid4())

        # 这里应该启动后台任务
        # 暂时返回任务ID
        return {
            "task_id": task_id,
            "status": "submitted",
            "message": "报表生成任务已提交",
            "created_at": datetime.now(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{task_id}")
async def get_report_status(task_id: str):
    """获取报表生成状态"""
    try:
        # 这里应该查询任务状态
        return {
            "task_id": task_id,
            "status": "running",
            "progress": 50,
            "message": "正在生成报表...",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 客户管理API
@router.get("/customers")
async def get_customers(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    """获取客户列表"""
    try:
        db_service = get_service("IDatabaseService")

        offset = (page - 1) * size
        query = """
            SELECT * FROM oil.t_customer 
            WHERE deleted = 0
            ORDER BY create_time DESC
            LIMIT %s OFFSET %s
        """

        customers = db_service.execute_query(query, (size, offset))

        return {
            "data": customers,
            "pagination": {"page": page, "size": size, "total": len(customers)},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}/devices")
async def get_customer_devices(customer_id: int):
    """获取客户的设备列表"""
    try:
        db_service = get_service("IDatabaseService")

        query = """
            SELECT * FROM oil.t_device 
            WHERE customer_id = %s AND deleted = 0
            ORDER BY create_time DESC
        """

        devices = db_service.execute_query(query, (customer_id,))
        return devices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 系统管理API
@router.get("/system/health")
async def system_health():
    """系统健康检查"""
    try:
        db_service = get_service("IDatabaseService")
        cache_service = get_service("ICacheService")

        # 检查数据库连接
        db_status = "healthy"
        try:
            db_service.execute_query("SELECT 1")
        except Exception:
            db_status = "unhealthy"

        # 检查缓存状态
        cache_stats = cache_service.get_stats()

        return {
            "status": "healthy" if db_status == "healthy" else "unhealthy",
            "database": db_status,
            "cache": cache_stats,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/cache/stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    try:
        cache_service = get_service("ICacheService")
        return cache_service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/cache/clear")
async def clear_cache():
    """清空缓存"""
    try:
        cache_service = get_service("ICacheService")
        cache_service.clear()
        return {"message": "缓存已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
