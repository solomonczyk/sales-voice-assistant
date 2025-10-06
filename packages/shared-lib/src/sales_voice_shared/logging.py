"""
Настройка логирования для Sales Voice Assistant
"""

import logging
import sys
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from .config import get_settings

settings = get_settings()


def setup_logging():
    """Настройка структурированного логирования"""
    
    # Настройка structlog
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
            structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Настройка стандартного логирования
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # Настройка JSON форматера для обычных логов
    if settings.log_format == "json":
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        handler.setFormatter(formatter)
        
        # Применяем к корневому логгеру
        root_logger = logging.getLogger()
        root_logger.handlers = [handler]
    
    # Настройка уровней для внешних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Получить структурированный логгер
    
    Args:
        name: Имя логгера (по умолчанию используется имя модуля)
        
    Returns:
        Настроенный логгер
    """
    if name is None:
        # Получаем имя вызывающего модуля
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return structlog.get_logger(name)


class LoggerMixin:
    """Миксин для добавления логгера в классы"""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Получить логгер для класса"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__module__ + '.' + self.__class__.__name__)
        return self._logger


def log_function_call(func):
    """Декоратор для логирования вызовов функций"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.info(
            "Function called",
            function=func.__name__,
            args=args,
            kwargs=kwargs
        )
        try:
            result = func(*args, **kwargs)
            logger.info(
                "Function completed",
                function=func.__name__,
                result=result
            )
            return result
        except Exception as e:
            logger.error(
                "Function failed",
                function=func.__name__,
                error=str(e),
                exc_info=True
            )
            raise
    return wrapper


def log_async_function_call(func):
    """Декоратор для логирования вызовов асинхронных функций"""
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.info(
            "Async function called",
            function=func.__name__,
            args=args,
            kwargs=kwargs
        )
        try:
            result = await func(*args, **kwargs)
            logger.info(
                "Async function completed",
                function=func.__name__,
                result=result
            )
            return result
        except Exception as e:
            logger.error(
                "Async function failed",
                function=func.__name__,
                error=str(e),
                exc_info=True
            )
            raise
    return wrapper


class RequestLogger:
    """Логгер для HTTP запросов"""
    
    def __init__(self, name: str = "http"):
        self.logger = get_logger(name)
    
    def log_request(self, method: str, url: str, headers: Dict[str, Any] = None, body: Any = None):
        """Логирование входящего запроса"""
        self.logger.info(
            "HTTP request received",
            method=method,
            url=url,
            headers=headers,
            body=body
        )
    
    def log_response(self, status_code: int, headers: Dict[str, Any] = None, body: Any = None):
        """Логирование ответа"""
        self.logger.info(
            "HTTP response sent",
            status_code=status_code,
            headers=headers,
            body=body
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Логирование ошибки"""
        self.logger.error(
            "HTTP error occurred",
            error=str(error),
            context=context,
            exc_info=True
        )


class DatabaseLogger:
    """Логгер для операций с базой данных"""
    
    def __init__(self, name: str = "database"):
        self.logger = get_logger(name)
    
    def log_query(self, query: str, params: Dict[str, Any] = None, duration: float = None):
        """Логирование SQL запроса"""
        self.logger.debug(
            "Database query executed",
            query=query,
            params=params,
            duration=duration
        )
    
    def log_slow_query(self, query: str, duration: float, threshold: float = 1.0):
        """Логирование медленного запроса"""
        if duration > threshold:
            self.logger.warning(
                "Slow database query detected",
                query=query,
                duration=duration,
                threshold=threshold
            )
    
    def log_connection(self, action: str, details: Dict[str, Any] = None):
        """Логирование подключений к БД"""
        self.logger.info(
            "Database connection event",
            action=action,
            details=details
        )


class MetricsLogger:
    """Логгер для метрик"""
    
    def __init__(self, name: str = "metrics"):
        self.logger = get_logger(name)
    
    def log_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Логирование метрики"""
        self.logger.info(
            "Metric recorded",
            metric_name=name,
            value=value,
            labels=labels
        )
    
    def log_counter_increment(self, name: str, increment: int = 1, labels: Dict[str, str] = None):
        """Логирование увеличения счетчика"""
        self.logger.info(
            "Counter incremented",
            counter_name=name,
            increment=increment,
            labels=labels
        )
    
    def log_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Логирование гистограммы"""
        self.logger.info(
            "Histogram recorded",
            histogram_name=name,
            value=value,
            labels=labels
        )


class CallLogger:
    """Специализированный логгер для звонков"""
    
    def __init__(self, name: str = "calls"):
        self.logger = get_logger(name)
    
    def log_call_start(self, call_id: str, phone: str, direction: str):
        """Логирование начала звонка"""
        self.logger.info(
            "Call started",
            call_id=call_id,
            phone=phone,
            direction=direction
        )
    
    def log_call_end(self, call_id: str, duration: int, status: str):
        """Логирование окончания звонка"""
        self.logger.info(
            "Call ended",
            call_id=call_id,
            duration=duration,
            status=status
        )
    
    def log_transcript(self, call_id: str, transcript: str, confidence: float = None):
        """Логирование транскрипта"""
        self.logger.info(
            "Call transcript",
            call_id=call_id,
            transcript=transcript,
            confidence=confidence
        )
    
    def log_dialog_turn(self, call_id: str, session_id: str, user_message: str, assistant_message: str):
        """Логирование диалогового хода"""
        self.logger.info(
            "Dialog turn",
            call_id=call_id,
            session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message
        )
    
    def log_intent_detected(self, call_id: str, intent: str, confidence: float, entities: Dict[str, Any] = None):
        """Логирование обнаруженного намерения"""
        self.logger.info(
            "Intent detected",
            call_id=call_id,
            intent=intent,
            confidence=confidence,
            entities=entities
        )
