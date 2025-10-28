"""
Comprehensive logging module for BulkFoodHub.
Provides structured logging with different handlers and formatters.
"""

import logging
import sys
from typing import Any, Dict, Optional
from pathlib import Path
import structlog
from structlog.stdlib import LoggerFactory
import json
from datetime import datetime

from app.core.config import settings


def setup_logging() -> None:
    """Set up structured logging for the application."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.log_format == "json" 
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # Set up file handlers
    _setup_file_handlers()


def _setup_file_handlers() -> None:
    """Set up file handlers for different log levels."""
    
    # Application logs
    app_handler = logging.FileHandler("logs/app.log")
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Error logs
    error_handler = logging.FileHandler("logs/error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Database logs
    db_handler = logging.FileHandler("logs/database.log")
    db_handler.setLevel(logging.INFO)
    db_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # API logs
    api_handler = logging.FileHandler("logs/api.log")
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Add handlers to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    
    # Add specific handlers to module loggers
    logging.getLogger("sqlalchemy.engine").addHandler(db_handler)
    logging.getLogger("fastapi").addHandler(api_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger instance for this class."""
        return get_logger(self.__class__.__name__)


def log_function_call(func_name: str, **kwargs) -> None:
    """Log function calls with parameters."""
    logger = get_logger("function_calls")
    logger.info("Function called", function=func_name, parameters=kwargs)


def log_api_request(method: str, path: str, user_id: Optional[str] = None, **kwargs) -> None:
    """Log API requests."""
    logger = get_logger("api_requests")
    logger.info(
        "API request",
        method=method,
        path=path,
        user_id=user_id,
        **kwargs
    )


def log_api_response(method: str, path: str, status_code: int, response_time: float, **kwargs) -> None:
    """Log API responses."""
    logger = get_logger("api_responses")
    logger.info(
        "API response",
        method=method,
        path=path,
        status_code=status_code,
        response_time_ms=round(response_time * 1000, 2),
        **kwargs
    )


def log_database_operation(operation: str, table: str, **kwargs) -> None:
    """Log database operations."""
    logger = get_logger("database_operations")
    logger.info(
        "Database operation",
        operation=operation,
        table=table,
        **kwargs
    )


def log_user_action(user_id: str, action: str, **kwargs) -> None:
    """Log user actions for audit trail."""
    logger = get_logger("user_actions")
    logger.info(
        "User action",
        user_id=user_id,
        action=action,
        timestamp=datetime.utcnow().isoformat(),
        **kwargs
    )


def log_security_event(event_type: str, severity: str = "medium", **kwargs) -> None:
    """Log security-related events."""
    logger = get_logger("security_events")
    logger.warning(
        "Security event",
        event_type=event_type,
        severity=severity,
        timestamp=datetime.utcnow().isoformat(),
        **kwargs
    )


def log_business_event(event_type: str, **kwargs) -> None:
    """Log business events (orders, payments, etc.)."""
    logger = get_logger("business_events")
    logger.info(
        "Business event",
        event_type=event_type,
        timestamp=datetime.utcnow().isoformat(),
        **kwargs
    )


def log_performance_metric(metric_name: str, value: float, unit: str = "ms", **kwargs) -> None:
    """Log performance metrics."""
    logger = get_logger("performance_metrics")
    logger.info(
        "Performance metric",
        metric_name=metric_name,
        value=value,
        unit=unit,
        **kwargs
    )


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Log errors with context."""
    logger = get_logger("errors")
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        exc_info=True
    )


# Initialize logging when module is imported
setup_logging()
