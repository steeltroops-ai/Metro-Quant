"""Logging configuration using loguru for structured logging."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None
) -> None:
    """
    Configure logging with loguru.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Format type ("json" or "text")
        log_file: Optional file path for log output
        
    Example:
        >>> setup_logging(log_level="DEBUG", log_format="json")
    """
    # Remove default handler
    logger.remove()
    
    # Determine format
    if log_format == "json":
        format_string = (
            "{{"
            '"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
            '"level": "{level}", '
            '"module": "{module}", '
            '"function": "{function}", '
            '"line": {line}, '
            '"message": "{message}"'
            "}}"
        )
    else:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # Add console handler
    logger.add(
        sys.stderr,
        format=format_string,
        level=log_level,
        colorize=(log_format != "json"),
        serialize=(log_format == "json")
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format=format_string,
            level=log_level,
            rotation="100 MB",
            retention="7 days",
            compression="zip",
            serialize=(log_format == "json")
        )
    
    logger.info(f"Logging initialized at {log_level} level with {log_format} format")


def get_logger():
    """
    Get the configured logger instance.
    
    Returns:
        Loguru logger instance
    """
    return logger
