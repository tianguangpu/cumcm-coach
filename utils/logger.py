"""
统一日志系统

替代 print 输出，提供结构化日志记录。
支持控制台和文件输出，可配置日志级别。

Usage:
    from utils.logger import setup_logger, get_logger

    # 方式1：创建新 logger
    logger = setup_logger("my_module", level=logging.INFO)
    logger.info("Processing started")

    # 方式2：获取已创建的 logger
    logger = get_logger("my_module")
    logger.debug("Debug message")
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# 默认日志格式
DEFAULT_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 已创建的 logger 缓存
_loggers: dict[str, logging.Logger] = {}


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_dir: str = "logs",
    fmt: str = DEFAULT_FORMAT,
    date_fmt: str = DEFAULT_DATE_FORMAT,
    console: bool = True,
    file: bool = True,
) -> logging.Logger:
    """
    配置并返回 logger 实例。

    Args:
        name: logger 名称，通常为模块名
        level: 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
        log_file: 日志文件名，默认为 <name>.log
        log_dir: 日志文件目录
        fmt: 日志格式
        date_fmt: 日期格式
        console: 是否输出到控制台
        file: 是否输出到文件

    Returns:
        logging.Logger: 配置好的 logger 实例

    Examples:
        >>> logger = setup_logger("solver", level=logging.DEBUG)
        >>> logger.info("Solver initialized")
        2026-09-11 10:00:00 [solver] INFO: Solver initialized
    """
    # 如果已创建，直接返回
    if name in _loggers:
        return _loggers[name]

    # 创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 格式器
    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    # 控制台 handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件 handler
    if file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        if log_file is None:
            log_file = f"{name}.log"

        file_handler = logging.FileHandler(
            log_path / log_file,
            encoding="utf-8",
            mode="a",  # 追加模式
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 缓存
    _loggers[name] = logger

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取已创建的 logger 实例。

    如果 logger 未创建，返回默认配置的 logger。

    Args:
        name: logger 名称

    Returns:
        logging.Logger: logger 实例

    Examples:
        >>> logger = get_logger("solver")
        >>> logger.info("Message")
    """
    if name in _loggers:
        return _loggers[name]

    # 如果未创建，使用默认配置
    return setup_logger(name)


def set_global_level(level: int) -> None:
    """
    设置所有已创建 logger 的日志级别。

    Args:
        level: 日志级别

    Examples:
        >>> set_global_level(logging.DEBUG)  # 打开调试日志
    """
    for logger in _loggers.values():
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)


# 预定义的模块 logger
def get_solver_logger() -> logging.Logger:
    """获取求解器模块的 logger"""
    return setup_logger("solver", level=logging.INFO)


def get_algorithm_logger() -> logging.Logger:
    """获取算法库的 logger"""
    return setup_logger("algorithms", level=logging.INFO)


def get_pipeline_logger() -> logging.Logger:
    """获取流水线的 logger"""
    return setup_logger("pipeline", level=logging.INFO)


def get_check_logger() -> logging.Logger:
    """获取检查工具的 logger"""
    return setup_logger("checker", level=logging.INFO)
