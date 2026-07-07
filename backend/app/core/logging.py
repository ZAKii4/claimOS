"""
Structured logging configuration for claimOS.

- **Development**: human-readable coloured output.
- **Production**: JSON-formatted output for log aggregation.
"""

import logging
import logging.config
import sys

from app.config.settings import get_settings


def setup_logging() -> None:
    """Configure application-wide logging."""
    settings = get_settings()
    is_dev = settings.ENVIRONMENT == "development"

    config: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "standard" if is_dev else "json",
                "level": settings.LOG_LEVEL,
            },
        },
        "loggers": {
            "claimOS": {
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "WARNING" if not settings.DEBUG else "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    }

    logging.config.dictConfig(config)


def get_logger(name: str = "claimOS") -> logging.Logger:
    """Return a named logger under the claimOS namespace."""
    return logging.getLogger(name)
