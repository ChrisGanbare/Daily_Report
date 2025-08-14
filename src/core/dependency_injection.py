"""
依赖注入容器
实现模块间的解耦，提高代码的可测试性和可维护性
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Type


class ServiceProvider:
    """服务提供者，管理依赖注入容器"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}

    def register_singleton(self, interface: str, implementation: Any):
        """注册单例服务"""
        self._services[interface] = implementation

    def register_factory(self, interface: str, factory: Callable):
        """注册工厂服务"""
        self._factories[interface] = factory

    def get_service(self, interface: str) -> Any:
        """获取服务实例"""
        if interface in self._singletons:
            return self._singletons[interface]

        if interface in self._services:
            service = self._services[interface]
            if isinstance(service, type):
                service = service()
            self._singletons[interface] = service
            return service

        if interface in self._factories:
            service = self._factories[interface]()
            self._singletons[interface] = service
            return service

        raise KeyError(f"Service '{interface}' not registered")

    def call_with_container(
        self, func: Callable, params: Optional[tuple] = None
    ) -> Any:
        """使用容器调用函数，自动注入依赖"""
        if params is None:
            params = ()
        return func(*params)


class IConfigService(ABC):
    """配置服务接口"""

    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_sql_templates(self) -> Dict[str, str]:
        pass


class IDatabaseService(ABC):
    """数据库服务接口"""

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def execute_query(self, query: str, params: tuple = None) -> list:
        pass


class IExcelService(ABC):
    """Excel服务接口"""

    @abstractmethod
    def generate_report(self, data: list, output_path: str) -> bool:
        pass

    @abstractmethod
    def create_chart(self, worksheet, data_range: str, chart_type: str = "line"):
        pass


class ICacheService(ABC):
    """缓存服务接口"""

    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600):
        pass

    @abstractmethod
    def delete(self, key: str):
        pass

    @abstractmethod
    def clear(self):
        pass


# 全局服务容器
service_provider = ServiceProvider()


def register_services():
    """注册所有服务到依赖注入容器"""
    from .cache_handler import CacheHandler
    from .config_handler import ConfigHandler
    from .db_handler import DatabaseHandler
    from .excel_handler import ExcelHandler

    # 注册配置服务
    service_provider.register_singleton("IConfigService", ConfigHandler())

    # 注册数据库服务
    def create_database_service():
        config = service_provider.get_service("IConfigService")
        db_config = config.get_database_config()
        return DatabaseHandler(db_config)

    service_provider.register_factory("IDatabaseService", create_database_service)

    # 注册Excel服务
    service_provider.register_singleton("IExcelService", ExcelHandler())

    # 注册缓存服务
    service_provider.register_singleton("ICacheService", CacheHandler())


def get_service(interface: str) -> Any:
    """获取服务实例的便捷方法"""
    return service_provider.get_service(interface)
