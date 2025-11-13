"""
核心模块初始化文件
"""

# 确保所有核心模块都被正确导入
from .cache_handler import CacheHandler
from .async_processor import AsyncDatabaseHandler, AsyncFileProcessor, AsyncReportGenerator
from .base_report import BaseReportGenerator
from .dependency_injection import (
    ServiceProvider, 
    IConfigService, 
    IDatabaseService, 
    IExcelService, 
    ICacheService,
    service_provider, 
    register_services, 
    get_service
)

__all__ = [
    "CacheHandler",
    "AsyncDatabaseHandler",
    "AsyncFileProcessor",
    "AsyncReportGenerator",
    "BaseReportGenerator",
    "ServiceProvider",
    "IConfigService",
    "IDatabaseService",
    "IExcelService",
    "ICacheService",
    "service_provider",
    "register_services",
    "get_service"
]