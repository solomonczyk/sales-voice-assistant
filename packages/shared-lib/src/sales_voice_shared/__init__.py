"""
Sales Voice Assistant - Shared Library

Общие утилиты, модели и компоненты для всех сервисов проекта.
"""

__version__ = "1.0.0"
__author__ = "Sales Voice Team"
__email__ = "dev@sales-voice.com"

from .config import Settings, get_settings
from .database import Database, get_database
from .logging import setup_logging, get_logger
from .metrics import MetricsCollector, get_metrics
from .tracing import setup_tracing, get_tracer
from .models import *
from .utils import *

__all__ = [
    # Config
    "Settings",
    "get_settings",
    # Database
    "Database", 
    "get_database",
    # Logging
    "setup_logging",
    "get_logger",
    # Metrics
    "MetricsCollector",
    "get_metrics",
    # Tracing
    "setup_tracing",
    "get_tracer",
    # Models
    "BaseModel",
    "User",
    "Client", 
    "Call",
    "Dialog",
    "Lead",
    "Deal",
    "Product",
    "Setting",
    "Metric",
    # Utils
    "validate_phone",
    "format_phone",
    "generate_session_id",
    "hash_password",
    "verify_password",
    "create_access_token",
    "verify_access_token",
]
