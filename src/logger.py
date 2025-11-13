"""
全局日志模块
"""
import logging
import sys


def setup_logger():
    """
    配置并返回一个全局日志记录器
    """
    # 延迟导入settings，避免循环导入问题
    from src.config import settings
    
    # 获取日志级别，如果无效则默认为INFO
    log_level = getattr(logging, settings.logging.level.upper(), logging.INFO)

    # 创建一个日志记录器
    logger = logging.getLogger("ZR_Daily_Report")
    logger.setLevel(log_level)

    # 如果已经有处理器，则不重复添加，防止日志重复输出
    if logger.hasHandlers():
        return logger

    # 创建一个处理器，用于将日志输出到控制台
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # 创建一个格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # 将处理器添加到日志记录器
    logger.addHandler(handler)

    return logger


# 全局可用的日志实例
logger = setup_logger()

if __name__ == "__main__":
    # 用于测试日志功能
    logger.debug("这是一条debug信息")
    logger.info("这是一条info信息")
    logger.warning("这是一条warning信息")
    logger.error("这是一条error信息")
    logger.critical("这是一条critical信息")