"""
统一配置管理模块
使用Pydantic进行类型安全、层次化的配置管理
"""
import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import ClassVar, Optional

from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv, find_dotenv

# 明确 .env 文件路径，确保无论从哪里运行都能正确加载
BASE_DIR = Path(__file__).parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"

# 在模块加载时就执行，确保环境变量在任何配置类实例化之前就绪
load_dotenv(dotenv_path=ENV_FILE_PATH)


class LoggingSettings(BaseSettings):
    """日志配置"""
    # 从环境变量或.env文件读取，否则使用默认值
    level: str = "INFO"

    # Pydantic V2 的配置方式
    model_config = SettingsConfigDict(
        env_prefix="LOG_", case_sensitive=False
    )


class DBSettings(BaseSettings):
    """数据库连接配置"""
    # 从环境变量或.env文件读取，否则使用默认值
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = "oil"
    
    # Pydantic V2 的配置方式 (推荐使用 SettingsConfigDict)
    model_config = SettingsConfigDict(
        env_prefix="DB_", case_sensitive=False
    )

class SQLTemplates(BaseModel):
    """SQL查询模板"""
    device_id_query: str
    device_id_fallback_query: str
    inventory_query: str
    customer_query: str
    refueling_details_query: str
    error_summary_main_query: Optional[str] = None
    error_summary_offline_query: Optional[str] = None
    daily_consumption_raw_query: Optional[str] = None
    monthly_consumption_raw_query: Optional[str] = None

class Settings(BaseModel):
    """主配置模型"""
    logging: LoggingSettings = LoggingSettings()
    db_config: DBSettings = DBSettings()
    sql_templates: SQLTemplates

    # 定义配置文件的路径
    _config_path: ClassVar[Path] = Path(__file__).parent.parent / "config" / "query_config.json"

    @classmethod
    def load_from_json(cls) -> "Settings":
        """从JSON文件中加载SQL模板，并结合环境变量构建完整配置"""
        if not cls._config_path.exists():
            raise FileNotFoundError(f"主配置文件未找到: {cls._config_path}")
        
        try:
            # 仅加载SQL模板部分
            sql_templates_data = json.loads(cls._config_path.read_text(encoding="utf-8"))
            
            # Pydantic BaseSettings 会自动从已加载的环境变量中填充 logging 和 db_config
            # 我们只需提供 json 中读取的 sql_templates
            return cls(
                sql_templates=SQLTemplates(**sql_templates_data.get("sql_templates", {}))
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}") from e
        except ValidationError as e:
            raise ValueError(f"配置项校验失败: {e}") from e


@lru_cache()
def get_settings() -> Settings:
    """
    获取全局配置实例
    使用lru_cache确保配置只被加载一次
    """
    return Settings.load_from_json()


# 全局可用的配置实例
settings = get_settings()

if __name__ == "__main__":
    try:
        print("尝试加载配置...")
        print(f"日志级别: {settings.logging.level}")
        print(f"数据库主机: {settings.db_config.host}")
        if settings.sql_templates.daily_consumption_raw_query:
            print("每日消耗原始数据查询模板已加载！")
        else:
            print("警告: 未找到每日消耗原始数据查询模板。")
        print("配置加载成功！")
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}")