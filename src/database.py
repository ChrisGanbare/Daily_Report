"""
数据库连接管理模块
使用SQLAlchemy Core和aiomysql实现异步连接池
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from config import settings
from logger import logger

# 构建数据库连接URL
# 注意：SQLAlchemy 2.x for aiomysql的URL格式是 mysql+aiomysql://
DATABASE_URL = (
    f"mysql+aiomysql://{settings.db_config.user}:{settings.db_config.password}@"
    f"{settings.db_config.host}:{settings.db_config.port}/{settings.db_config.database}"
)

try:
    # 创建异步数据库引擎
    engine = create_async_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # 在每次检出时测试连接
        pool_recycle=3600,   # 每小时回收一次连接
        echo=False,          # 在生产中关闭SQL语句打印
    )

    # 创建一个异步Session工厂
    AsyncSessionFactory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    logger.info("数据库连接池创建成功")

except Exception as e:
    logger.critical(f"数据库引擎创建失败: {e}")
    raise


@asynccontextmanager
async def get_db_session() -> AsyncSession:
    """
    提供一个数据库会话的上下文管理器
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话期间发生错误: {e}")
            raise
        finally:
            await session.close()


async def get_db() -> AsyncSession:
    """
    FastAPI依赖项，用于在API路由中获取数据库会话
    """
    async with get_db_session() as session:
        yield session


if __name__ == "__main__":
    # 用于测试数据库连接
    import asyncio
    from sqlalchemy import text

    async def test_connection():
        logger.info("开始测试数据库连接...")
        try:
            async with get_db_session() as session:
                result = await session.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    logger.info("数据库连接成功！")
                else:
                    logger.error("数据库连接测试失败，查询未返回1")
        except Exception as e:
            logger.error(f"数据库连接测试期间发生错误: {e}")

    asyncio.run(test_connection())