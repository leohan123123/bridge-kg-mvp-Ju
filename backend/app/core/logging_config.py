import logging
import sys
from .config import settings # 从同级目录的config.py导入settings

def setup_logging():
    """
    配置应用日志。
    """
    log_level = settings.LOG_LEVEL.upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    # 创建一个日志格式器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level) # 设置根日志级别

    # 移除所有现有的处理器，以避免重复日志 (特别是在uvicorn等环境中)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 创建一个控制台处理器 (StreamHandler)
    console_handler = logging.StreamHandler(sys.stdout) # 输出到标准输出
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level) # 处理器也需要设置级别

    # 将处理器添加到根日志记录器
    root_logger.addHandler(console_handler)

    # 配置特定库的日志级别 (如果需要)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    # 测试日志配置
    # logging.debug("这是 DEBUG 级别日志 (如果LOG_LEVEL设置为DEBUG会显示)")
    # logging.info("日志系统已配置完成。")
    # logging.warning("这是一条 WARNING 级别日志。")
    # logging.error("这是一条 ERROR 级别日志。")
    # logging.critical("这是一条 CRITICAL 级别日志。")

if __name__ == "__main__":
    # 用于单独测试日志配置
    # 需要模拟 settings 对象，或者确保 config.py 可以独立运行并创建 settings
    class MockSettings:
        LOG_LEVEL = "DEBUG" # 测试不同的级别

    original_settings = None
    if 'settings' in globals():
        original_settings = settings # 保存原始的settings

    # 临时的 mock settings
    # from . import config # 确保config模块被加载
    # temp_settings_instance = MockSettings()
    # setattr(config, 'settings', temp_settings_instance)

    # 更简单的方式是直接修改 settings 的属性（如果 settings 已被创建）
    if hasattr(settings, 'LOG_LEVEL'):
        original_log_level = settings.LOG_LEVEL
        settings.LOG_LEVEL = "DEBUG"
        setup_logging() # 使用修改后的settings重新配置日志
        settings.LOG_LEVEL = original_log_level # 还原
    else: # 如果 settings 尚未创建 (例如直接运行此文件)
        # 创建一个临时的 settings 对象用于测试
        from pydantic import BaseSettings
        class TempSettings(BaseSettings):
            LOG_LEVEL: str = "DEBUG"

        # 替换全局的 settings 对象 (或者传递给 setup_logging)
        # 这部分比较hacky，更好的做法是让 setup_logging 接受一个 settings 对象作为参数
        # 为了保持当前结构，我们假设 settings 已经从 .config 导入
        # 如果直接运行此文件，.config 可能无法正确导入，除非调整PYTHONPATH
        print("Warning: Running logging_config.py directly might not use project settings.")
        # setup_logging() # 尝试用默认的settings (可能未正确加载)


    # 运行 setup_logging 后，日志消息应该会根据 LOG_LEVEL 显示
    logger = logging.getLogger(__name__) # 获取当前模块的logger
    logger.debug("测试 DEBUG 日志 from logging_config.py")
    logger.info("测试 INFO 日志 from logging_config.py")
    logger.warning("测试 WARNING 日志 from logging_config.py")

    # if original_settings:
    #     setattr(config, 'settings', original_settings) # 还原 settings (如果被修改)
