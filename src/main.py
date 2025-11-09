"""
应用主入口
基于FastAPI的现代Web服务
"""
import uvicorn
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from pathlib import Path
import multiprocessing
import os
from starlette.background import BackgroundTask
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json # 导入json

from src.config import settings
from src.logger import logger
from src.database import get_db
from src.repositories.device_repository import DeviceRepository
from src.services.report_service import ReportService

# --- 路径配置 ---
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# --- FastAPI 应用初始化 ---
app = FastAPI(
    title="ZR Daily Report Web",
    description="新一代ZR Daily Report Web管理界面",
    version="2.0.0",
)

# --- 挂载静态文件和模板 ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# --- 依赖注入 ---
def get_device_repository(session: AsyncSession = Depends(get_db)) -> DeviceRepository:
    return DeviceRepository(session)

def get_report_service(repo: DeviceRepository = Depends(get_device_repository)) -> ReportService:
    return ReportService(repo)


# --- API 模型 ---
class ReportGenerationRequest(BaseModel):
    report_type: str
    devices: List[str] # 简化为设备编码列表
    start_date: str
    end_date: str


# --- API 路由 ---
@app.get("/", response_class=HTMLResponse)
async def get_index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/devices", response_model=List[Dict[str, Any]])
async def get_devices_list(
    customer_name: Optional[str] = None,
    device_code: Optional[str] = None,
    repo: DeviceRepository = Depends(get_device_repository),
):
    try:
        return await repo.get_devices_with_customers(customer_name, device_code)
    except Exception as e:
        logger.error(f"API /api/devices 出错: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取设备列表时发生服务器内部错误")


@app.post("/api/reports/generate")
async def generate_report_endpoint(
    request: ReportGenerationRequest,
    service: ReportService = Depends(get_report_service),
):
    """
    接收前端请求，调度并生成相应的报表。
    """
    # --- 后端验证 ---
    try:
        start_dt = datetime.strptime(request.start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(request.end_date, '%Y-%m-%d')
        
        if request.report_type == 'daily_consumption':
            if end_dt > start_dt + relativedelta(months=2):
                raise HTTPException(status_code=400, detail="每日消耗误差报表查询日期跨度不能超过两个月。")
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD 格式。")

    report_path = None
    warnings = []
    try:
        logger.info(f"收到报表生成请求: {request.model_dump()}")
        # 正确解包元组
        report_path, warnings = await service.generate_report(
            report_type=request.report_type,
            devices=request.devices,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        
        media_type = 'application/zip' if report_path.suffix == '.zip' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        cleanup_task = BackgroundTask(os.remove, report_path)
        
        # 创建响应头
        headers = {}
        if warnings:
            # 将警告信息编码后放入自定义头
            # 注意：HTTP头不支持非ASCII字符，需要编码
            warnings_json = json.dumps(warnings)
            headers['X-Report-Warnings'] = warnings_json
        
        return FileResponse(
            path=report_path,
            media_type=media_type,
            filename=report_path.name,
            background=cleanup_task,
            headers=headers, # 添加自定义头
        )
    except (ValueError, NotImplementedError) as e:
        logger.warning(f"生成报表时发生业务错误或功能未实现: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"API /api/reports/generate 发生未知错误: {e}", exc_info=True)
        if report_path and os.path.exists(str(report_path)): # 确保路径是字符串
            os.remove(str(report_path))
        raise HTTPException(status_code=500, detail="生成报表时发生服务器内部错误")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": app.version}


# --- 主程序入口 ---
def main():
    logger.info("启动Web服务 (开发模式)...")
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=8000,
        log_level=settings.logging.level.lower(),
        reload=True,
    )

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
