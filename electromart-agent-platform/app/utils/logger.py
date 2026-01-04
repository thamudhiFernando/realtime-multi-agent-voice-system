"""
Logging configuration for ElectroMart Multi-Agent System
"""
import logging
import sys
from typing import Any
from pythonjsonlogger import jsonlogger

from app.utils.config import settings


def setup_logger(name: str) -> logging.Logger:
    """
    Set up structured JSON logger

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    handler = logging.StreamHandler(sys.stdout)

    # JSON formatter for structured logging
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        rename_fields={
            'asctime': 'timestamp',
            'name': 'logger',
            'levelname': 'level'
        }
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Create default logger
logger = setup_logger("electromart")


def log_agent_activity(
    agent_name: str,
    activity: str,
    session_id: str,
    metadata: dict[str, Any] = None
) -> None:
    """
    Log agent activity with structured data

    Args:
        agent_name: Name of the agent
        activity: Activity description
        session_id: Session ID
        metadata: Additional metadata
    """
    log_data = {
        "agent": agent_name,
        "activity": activity,
        "session_id": session_id,
        **(metadata or {})
    }
    logger.info(f"Agent activity: {activity}", extra=log_data)
