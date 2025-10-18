"""
Centralized logging configuration for SIM-ONE MCP Server.

Provides standardized logging setup with rotating file handlers,
console output, and performance tracking utilities.
"""

import logging
import logging.handlers
from pathlib import Path
import os
import time
import functools
from typing import Callable, Any

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log level from environment (default: INFO)
LOG_LEVEL = os.environ.get("SIM_ONE_MCP_LOG_LEVEL", "INFO")


def setup_logger(name: str, log_file: str) -> logging.Logger:
    """
    Create logger with rotating file handler and console output.

    Args:
        name: Logger name (e.g., "five_laws_validator")
        log_file: Filename (e.g., "five_laws_validator.log")

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger("five_laws_validator", "five_laws_validator.log")
        >>> logger.info("Tool invoked")
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Prevent duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # File handler with rotation (10MB max, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(LOG_LEVEL)

    # Console handler (INFO and above only)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter with timestamp, level, module, function, line, and message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_performance(logger: logging.Logger, operation: str, duration: float, **metrics):
    """
    Log performance metrics for an operation.

    Args:
        logger: Logger instance
        operation: Operation name
        duration: Duration in seconds
        **metrics: Additional metrics to log (key=value pairs)

    Example:
        >>> logger = setup_logger("test", "test.log")
        >>> log_performance(logger, "validation", 0.123, text_length=1234, score=85.2)
    """
    metrics_str = " | ".join(f"{k}={v}" for k, v in metrics.items())
    logger.info(f"[PERF] {operation} completed in {duration:.3f}s | {metrics_str}")


def log_tool_execution(logger: logging.Logger) -> Callable:
    """
    Decorator to automatically log tool execution time and status.

    Logs tool invocation, completion, duration, and any exceptions.
    Also logs to a separate performance logger for monitoring.

    Args:
        logger: Logger instance for the tool

    Returns:
        Decorator function

    Example:
        >>> logger = setup_logger("my_tool", "my_tool.log")
        >>> @log_tool_execution(logger)
        >>> def my_tool(param1, param2):
        >>>     return "result"
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            tool_name = func.__name__
            start_time = time.time()

            logger.info(f"[START] {tool_name} invoked")
            logger.debug(f"[START] {tool_name} args={args[:2] if args else []}, kwargs keys={list(kwargs.keys())}")

            try:
                # Execute the tool
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(f"[SUCCESS] {tool_name} completed in {duration:.3f}s")

                # Log to performance logger
                perf_logger = logging.getLogger("performance")
                if not perf_logger.handlers:
                    perf_logger = setup_logger("performance", "performance.log")
                perf_logger.info(
                    f"{tool_name} | duration={duration:.3f}s | status=success"
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"[FAILURE] {tool_name} failed after {duration:.3f}s: {str(e)}",
                    exc_info=True
                )

                # Log to performance logger
                perf_logger = logging.getLogger("performance")
                if not perf_logger.handlers:
                    perf_logger = setup_logger("performance", "performance.log")
                perf_logger.error(
                    f"{tool_name} | duration={duration:.3f}s | status=failure | error={str(e)}"
                )

                raise

        return wrapper
    return decorator


# Initialize performance logger
performance_logger = setup_logger("performance", "performance.log")
