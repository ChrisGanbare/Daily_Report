"""
核心模块包初始化文件
导出核心功能模块
"""

from .db_handler import DatabaseHandler
from .file_handler import FileHandler
from .statement_handler import CustomerStatementGenerator
from .inventory_handler import InventoryReportHandler
from .async_processor import AsyncDatabaseHandler, AsyncFileProcessor, AsyncReportGenerator, AsyncTaskManager
from .cache_handler import CacheHandler
from .dependency_injection import service_provider, register_services, get_service
