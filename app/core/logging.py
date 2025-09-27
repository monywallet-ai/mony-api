import logging
import sys
import structlog


def setup_logging(
    log_level: str = "INFO", environment: str = "local", json_logs: bool = True
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: The log level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: The environment (local, staging, production)
        json_logs: Whether to output logs in JSON format
    """

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Common processors for structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.format_exc_info,
    ]

    if json_logs and environment != "local":
        # JSON output for production/staging
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Pretty console output for local development
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: The logger name (usually __name__)

    Returns:
        A configured structlog logger
    """
    return structlog.get_logger(name or "mony-api")


# Logger instances for different components
request_logger = get_logger("mony-api.requests")
database_logger = get_logger("mony-api.database")
openai_logger = get_logger("mony-api.openai")
receipt_logger = get_logger("mony-api.receipts")
general_logger = get_logger("mony-api.general")


def configure_logger_levels(log_level: str = "INFO"):
    """
    Configure specific log levels for different components.

    Args:
        log_level: Base log level for all loggers
    """
    import logging

    base_level = getattr(logging, log_level.upper())

    # Set specific levels for different components
    logger_levels = {
        "mony-api.requests": base_level,
        "mony-api.database": base_level,  # Can be set to DEBUG for detailed DB logs
        "mony-api.openai": base_level,
        "mony-api.receipts": base_level,
        "mony-api.general": base_level,
        "mony-api.transactions": base_level,
        "mony-api.api": base_level,
    }

    # Apply levels to structlog loggers
    for logger_name, level in logger_levels.items():
        logger = get_logger(logger_name)
        # Note: structlog level filtering is handled by processors


def get_component_logger(component: str) -> "structlog.BoundLogger":
    """
    Get a logger for a specific component with predefined naming convention.

    Args:
        component: Component name (e.g., 'auth', 'transactions', 'receipts')

    Returns:
        Configured logger for the component
    """
    return get_logger(f"mony-api.{component}")


# Utility function for creating custom context loggers
def create_context_logger(component: str, **context):
    """
    Create a logger with permanent context for a specific component.

    Args:
        component: Component name
        **context: Additional context to bind to the logger

    Returns:
        Logger with bound context
    """
    logger = get_component_logger(component)
    return logger.bind(**context)
