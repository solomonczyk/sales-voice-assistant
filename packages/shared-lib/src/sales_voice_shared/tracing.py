"""
Настройка трассировки OpenTelemetry для Sales Voice Assistant
"""

import functools
from typing import Any, Callable, Dict, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

from .config import get_settings
from .logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


def setup_tracing(service_name: str = None, service_version: str = None):
    """
    Настройка трассировки OpenTelemetry
    
    Args:
        service_name: Имя сервиса
        service_version: Версия сервиса
    """
    service_name = service_name or settings.otel_service_name
    service_version = service_version or settings.otel_service_version
    
    # Создание ресурса с информацией о сервисе
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "service.instance.id": f"{service_name}-{service_version}",
        "deployment.environment": settings.environment,
    })
    
    # Настройка провайдера трассировки
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer_provider = trace.get_tracer_provider()
    
    # Настройка экспортера OTLP
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=True,  # Для разработки
    )
    
    # Добавление процессора для экспорта спанов
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    # Инструментирование библиотек
    try:
        FastAPIInstrumentor().instrument()
        logger.info("FastAPI instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI: {e}")
    
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument HTTPX: {e}")
    
    try:
        RedisInstrumentor().instrument()
        logger.info("Redis instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument Redis: {e}")
    
    try:
        SQLAlchemyInstrumentor().instrument()
        logger.info("SQLAlchemy instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument SQLAlchemy: {e}")
    
    logger.info(f"Tracing setup completed for service: {service_name}")


def get_tracer(name: str = None) -> trace.Tracer:
    """
    Получить трасер для создания спанов
    
    Args:
        name: Имя трасера (по умолчанию используется имя модуля)
        
    Returns:
        Настроенный трасер
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return trace.get_tracer(name)


def trace_function(span_name: str = None, attributes: Dict[str, Any] = None):
    """
    Декоратор для трассировки функций
    
    Args:
        span_name: Имя спана (по умолчанию используется имя функции)
        attributes: Атрибуты для добавления в спан
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            span_name_final = span_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name_final) as span:
                # Добавляем атрибуты
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Добавляем информацию о функции
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


def trace_async_function(span_name: str = None, attributes: Dict[str, Any] = None):
    """
    Декоратор для трассировки асинхронных функций
    
    Args:
        span_name: Имя спана (по умолчанию используется имя функции)
        attributes: Атрибуты для добавления в спан
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            span_name_final = span_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name_final) as span:
                # Добавляем атрибуты
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Добавляем информацию о функции
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


class SpanContext:
    """Контекстный менеджер для создания спанов"""
    
    def __init__(self, name: str, attributes: Dict[str, Any] = None, tracer_name: str = None):
        self.name = name
        self.attributes = attributes or {}
        self.tracer = get_tracer(tracer_name)
        self.span = None
    
    def __enter__(self):
        self.span = self.tracer.start_span(self.name)
        
        # Добавляем атрибуты
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
            self.span.record_exception(exc_val)
        else:
            self.span.set_status(Status(StatusCode.OK))
        
        self.span.end()


def trace_call(operation: str, attributes: Dict[str, Any] = None):
    """
    Создать спан для операции
    
    Args:
        operation: Название операции
        attributes: Атрибуты для спана
        
    Returns:
        Контекстный менеджер для спана
    """
    return SpanContext(operation, attributes)


class CallTracer:
    """Специализированный трасер для звонков"""
    
    def __init__(self, call_id: str):
        self.call_id = call_id
        self.tracer = get_tracer("calls")
        self.root_span = None
    
    def start_call(self, phone: str, direction: str):
        """Начать трассировку звонка"""
        self.root_span = self.tracer.start_span("call.lifecycle")
        self.root_span.set_attribute("call.id", self.call_id)
        self.root_span.set_attribute("call.phone", phone)
        self.root_span.set_attribute("call.direction", direction)
        return self.root_span
    
    def end_call(self, status: str, duration: int = None):
        """Завершить трассировку звонка"""
        if self.root_span:
            self.root_span.set_attribute("call.status", status)
            if duration is not None:
                self.root_span.set_attribute("call.duration", duration)
            self.root_span.set_status(Status(StatusCode.OK))
            self.root_span.end()
    
    def trace_asr(self, provider: str, processing_time: float, confidence: float = None):
        """Трассировка ASR обработки"""
        with self.tracer.start_span("call.asr") as span:
            span.set_attribute("call.id", self.call_id)
            span.set_attribute("asr.provider", provider)
            span.set_attribute("asr.processing_time", processing_time)
            if confidence is not None:
                span.set_attribute("asr.confidence", confidence)
            span.set_status(Status(StatusCode.OK))
    
    def trace_tts(self, provider: str, processing_time: float):
        """Трассировка TTS обработки"""
        with self.tracer.start_span("call.tts") as span:
            span.set_attribute("call.id", self.call_id)
            span.set_attribute("tts.provider", provider)
            span.set_attribute("tts.processing_time", processing_time)
            span.set_status(Status(StatusCode.OK))
    
    def trace_llm(self, provider: str, model: str, processing_time: float, tokens: Dict[str, int] = None):
        """Трассировка LLM обработки"""
        with self.tracer.start_span("call.llm") as span:
            span.set_attribute("call.id", self.call_id)
            span.set_attribute("llm.provider", provider)
            span.set_attribute("llm.model", model)
            span.set_attribute("llm.processing_time", processing_time)
            if tokens:
                for token_type, count in tokens.items():
                    span.set_attribute(f"llm.tokens.{token_type}", count)
            span.set_status(Status(StatusCode.OK))
    
    def trace_dialog_turn(self, intent: str, confidence: float, entities: Dict[str, Any] = None):
        """Трассировка диалогового хода"""
        with self.tracer.start_span("call.dialog_turn") as span:
            span.set_attribute("call.id", self.call_id)
            span.set_attribute("dialog.intent", intent)
            span.set_attribute("dialog.confidence", confidence)
            if entities:
                for key, value in entities.items():
                    span.set_attribute(f"dialog.entity.{key}", str(value))
            span.set_status(Status(StatusCode.OK))
    
    def trace_crm_operation(self, operation: str, provider: str, processing_time: float, success: bool = True):
        """Трассировка CRM операции"""
        with self.tracer.start_span("call.crm_operation") as span:
            span.set_attribute("call.id", self.call_id)
            span.set_attribute("crm.operation", operation)
            span.set_attribute("crm.provider", provider)
            span.set_attribute("crm.processing_time", processing_time)
            span.set_status(Status(StatusCode.OK) if success else Status(StatusCode.ERROR))


class DatabaseTracer:
    """Специализированный трасер для операций с базой данных"""
    
    def __init__(self):
        self.tracer = get_tracer("database")
    
    def trace_query(self, query: str, params: Dict[str, Any] = None, duration: float = None):
        """Трассировка SQL запроса"""
        with self.tracer.start_span("db.query") as span:
            span.set_attribute("db.statement", query)
            if params:
                # Маскируем чувствительные данные
                masked_params = {}
                for key, value in params.items():
                    if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret']):
                        masked_params[key] = "***MASKED***"
                    else:
                        masked_params[key] = str(value)
                span.set_attribute("db.parameters", str(masked_params))
            if duration is not None:
                span.set_attribute("db.duration", duration)
            span.set_status(Status(StatusCode.OK))
    
    def trace_transaction(self, operation: str, duration: float = None):
        """Трассировка транзакции"""
        with self.tracer.start_span("db.transaction") as span:
            span.set_attribute("db.operation", operation)
            if duration is not None:
                span.set_attribute("db.duration", duration)
            span.set_status(Status(StatusCode.OK))


class ExternalServiceTracer:
    """Специализированный трасер для внешних сервисов"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tracer = get_tracer(f"external.{service_name}")
    
    def trace_request(self, method: str, url: str, duration: float = None, status_code: int = None):
        """Трассировка внешнего запроса"""
        with self.tracer.start_span("external.request") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", url)
            span.set_attribute("external.service", self.service_name)
            if duration is not None:
                span.set_attribute("http.duration", duration)
            if status_code is not None:
                span.set_attribute("http.status_code", status_code)
                span.set_status(Status(StatusCode.OK) if 200 <= status_code < 400 else Status(StatusCode.ERROR))
            else:
                span.set_status(Status(StatusCode.OK))
    
    def trace_error(self, error: Exception):
        """Трассировка ошибки внешнего сервиса"""
        with self.tracer.start_span("external.error") as span:
            span.set_attribute("external.service", self.service_name)
            span.set_attribute("error.message", str(error))
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.record_exception(error)
