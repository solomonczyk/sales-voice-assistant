"""
Система метрик для Sales Voice Assistant
"""

import time
from functools import wraps
from typing import Any, Dict, Optional

from prometheus_client import (
    Counter, Gauge, Histogram, Info, CollectorRegistry, 
    generate_latest, CONTENT_TYPE_LATEST, start_http_server
)

from .config import get_settings
from .logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class MetricsCollector:
    """Коллектор метрик Prometheus"""
    
    def __init__(self, service_name: str = None):
        self.service_name = service_name or settings.otel_service_name
        self.registry = CollectorRegistry()
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Инициализация всех метрик"""
        
        # Информация о сервисе
        self.service_info = Info(
            'service_info',
            'Information about the service',
            registry=self.registry
        )
        self.service_info.info({
            'name': self.service_name,
            'version': settings.app_version,
            'environment': settings.environment
        })
        
        # HTTP метрики
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status_code', 'service'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'service'],
            registry=self.registry
        )
        
        # Метрики звонков
        self.calls_total = Counter(
            'calls_total',
            'Total number of calls',
            ['direction', 'status', 'service'],
            registry=self.registry
        )
        
        self.call_duration = Histogram(
            'call_duration_seconds',
            'Call duration in seconds',
            ['direction', 'service'],
            registry=self.registry
        )
        
        self.active_calls = Gauge(
            'active_calls',
            'Number of active calls',
            ['service'],
            registry=self.registry
        )
        
        # Метрики ASR
        self.asr_requests_total = Counter(
            'asr_requests_total',
            'Total number of ASR requests',
            ['provider', 'status', 'service'],
            registry=self.registry
        )
        
        self.asr_processing_time = Histogram(
            'asr_processing_time_seconds',
            'ASR processing time in seconds',
            ['provider', 'service'],
            registry=self.registry
        )
        
        self.asr_confidence = Histogram(
            'asr_confidence_score',
            'ASR confidence score',
            ['provider', 'service'],
            registry=self.registry
        )
        
        # Метрики TTS
        self.tts_requests_total = Counter(
            'tts_requests_total',
            'Total number of TTS requests',
            ['provider', 'status', 'service'],
            registry=self.registry
        )
        
        self.tts_processing_time = Histogram(
            'tts_processing_time_seconds',
            'TTS processing time in seconds',
            ['provider', 'service'],
            registry=self.registry
        )
        
        # Метрики LLM
        self.llm_requests_total = Counter(
            'llm_requests_total',
            'Total number of LLM requests',
            ['provider', 'model', 'status', 'service'],
            registry=self.registry
        )
        
        self.llm_processing_time = Histogram(
            'llm_processing_time_seconds',
            'LLM processing time in seconds',
            ['provider', 'model', 'service'],
            registry=self.registry
        )
        
        self.llm_tokens_total = Counter(
            'llm_tokens_total',
            'Total number of LLM tokens',
            ['provider', 'model', 'type', 'service'],
            registry=self.registry
        )
        
        # Метрики диалогов
        self.dialog_turns_total = Counter(
            'dialog_turns_total',
            'Total number of dialog turns',
            ['intent', 'service'],
            registry=self.registry
        )
        
        self.dialog_confidence = Histogram(
            'dialog_confidence_score',
            'Dialog confidence score',
            ['intent', 'service'],
            registry=self.registry
        )
        
        # Метрики CRM
        self.crm_requests_total = Counter(
            'crm_requests_total',
            'Total number of CRM requests',
            ['provider', 'operation', 'status', 'service'],
            registry=self.registry
        )
        
        self.crm_processing_time = Histogram(
            'crm_processing_time_seconds',
            'CRM processing time in seconds',
            ['provider', 'operation', 'service'],
            registry=self.registry
        )
        
        # Метрики лидов и сделок
        self.leads_total = Counter(
            'leads_total',
            'Total number of leads created',
            ['source', 'status', 'service'],
            registry=self.registry
        )
        
        self.deals_total = Counter(
            'deals_total',
            'Total number of deals created',
            ['status', 'service'],
            registry=self.registry
        )
        
        self.deal_value = Histogram(
            'deal_value_rub',
            'Deal value in RUB',
            ['service'],
            registry=self.registry
        )
        
        # Метрики ошибок
        self.errors_total = Counter(
            'errors_total',
            'Total number of errors',
            ['error_type', 'service'],
            registry=self.registry
        )
        
        # Метрики производительности
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            ['service'],
            registry=self.registry
        )
        
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            ['service'],
            registry=self.registry
        )
        
        # Метрики очередей
        self.queue_size = Gauge(
            'queue_size',
            'Queue size',
            ['queue_name', 'service'],
            registry=self.registry
        )
        
        self.queue_processing_time = Histogram(
            'queue_processing_time_seconds',
            'Queue processing time in seconds',
            ['queue_name', 'service'],
            registry=self.registry
        )
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Записать метрику HTTP запроса"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code),
            service=self.service_name
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint,
            service=self.service_name
        ).observe(duration)
    
    def record_call(self, direction: str, status: str, duration: float = None):
        """Записать метрику звонка"""
        self.calls_total.labels(
            direction=direction,
            status=status,
            service=self.service_name
        ).inc()
        
        if duration is not None:
            self.call_duration.labels(
                direction=direction,
                service=self.service_name
            ).observe(duration)
    
    def set_active_calls(self, count: int):
        """Установить количество активных звонков"""
        self.active_calls.labels(service=self.service_name).set(count)
    
    def record_asr_request(self, provider: str, status: str, processing_time: float, confidence: float = None):
        """Записать метрику ASR запроса"""
        self.asr_requests_total.labels(
            provider=provider,
            status=status,
            service=self.service_name
        ).inc()
        
        self.asr_processing_time.labels(
            provider=provider,
            service=self.service_name
        ).observe(processing_time)
        
        if confidence is not None:
            self.asr_confidence.labels(
                provider=provider,
                service=self.service_name
            ).observe(confidence)
    
    def record_tts_request(self, provider: str, status: str, processing_time: float):
        """Записать метрику TTS запроса"""
        self.tts_requests_total.labels(
            provider=provider,
            status=status,
            service=self.service_name
        ).inc()
        
        self.tts_processing_time.labels(
            provider=provider,
            service=self.service_name
        ).observe(processing_time)
    
    def record_llm_request(self, provider: str, model: str, status: str, processing_time: float, tokens: Dict[str, int] = None):
        """Записать метрику LLM запроса"""
        self.llm_requests_total.labels(
            provider=provider,
            model=model,
            status=status,
            service=self.service_name
        ).inc()
        
        self.llm_processing_time.labels(
            provider=provider,
            model=model,
            service=self.service_name
        ).observe(processing_time)
        
        if tokens:
            for token_type, count in tokens.items():
                self.llm_tokens_total.labels(
                    provider=provider,
                    model=model,
                    type=token_type,
                    service=self.service_name
                ).inc(count)
    
    def record_dialog_turn(self, intent: str, confidence: float):
        """Записать метрику диалогового хода"""
        self.dialog_turns_total.labels(
            intent=intent,
            service=self.service_name
        ).inc()
        
        self.dialog_confidence.labels(
            intent=intent,
            service=self.service_name
        ).observe(confidence)
    
    def record_crm_request(self, provider: str, operation: str, status: str, processing_time: float):
        """Записать метрику CRM запроса"""
        self.crm_requests_total.labels(
            provider=provider,
            operation=operation,
            status=status,
            service=self.service_name
        ).inc()
        
        self.crm_processing_time.labels(
            provider=provider,
            operation=operation,
            service=self.service_name
        ).observe(processing_time)
    
    def record_lead(self, source: str, status: str):
        """Записать метрику лида"""
        self.leads_total.labels(
            source=source,
            status=status,
            service=self.service_name
        ).inc()
    
    def record_deal(self, status: str, value: float = None):
        """Записать метрику сделки"""
        self.deals_total.labels(
            status=status,
            service=self.service_name
        ).inc()
        
        if value is not None:
            self.deal_value.labels(service=self.service_name).observe(value)
    
    def record_error(self, error_type: str):
        """Записать метрику ошибки"""
        self.errors_total.labels(
            error_type=error_type,
            service=self.service_name
        ).inc()
    
    def set_memory_usage(self, bytes_used: int):
        """Установить использование памяти"""
        self.memory_usage.labels(service=self.service_name).set(bytes_used)
    
    def set_cpu_usage(self, percent: float):
        """Установить использование CPU"""
        self.cpu_usage.labels(service=self.service_name).set(percent)
    
    def set_queue_size(self, queue_name: str, size: int):
        """Установить размер очереди"""
        self.queue_size.labels(
            queue_name=queue_name,
            service=self.service_name
        ).set(size)
    
    def record_queue_processing(self, queue_name: str, processing_time: float):
        """Записать время обработки очереди"""
        self.queue_processing_time.labels(
            queue_name=queue_name,
            service=self.service_name
        ).observe(processing_time)
    
    def get_metrics(self) -> str:
        """Получить метрики в формате Prometheus"""
        return generate_latest(self.registry)
    
    def start_metrics_server(self, port: int = None):
        """Запустить HTTP сервер для метрик"""
        port = port or settings.metrics_port
        start_http_server(port, registry=self.registry)
        logger.info(f"Metrics server started on port {port}")


# Глобальный экземпляр коллектора метрик
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics(service_name: str = None) -> MetricsCollector:
    """Получить экземпляр коллектора метрик"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(service_name)
    return _metrics_collector


def measure_time(metric_name: str, labels: Dict[str, str] = None):
    """Декоратор для измерения времени выполнения функции"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                metrics = get_metrics()
                
                # Записываем метрику времени выполнения
                if hasattr(metrics, f'{metric_name}_duration'):
                    getattr(metrics, f'{metric_name}_duration').labels(
                        status=status,
                        service=metrics.service_name,
                        **(labels or {})
                    ).observe(duration)
                
                logger.debug(
                    f"Function {func.__name__} executed",
                    duration=duration,
                    status=status,
                    metric_name=metric_name
                )
        return wrapper
    return decorator


def measure_async_time(metric_name: str, labels: Dict[str, str] = None):
    """Декоратор для измерения времени выполнения асинхронной функции"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                metrics = get_metrics()
                
                # Записываем метрику времени выполнения
                if hasattr(metrics, f'{metric_name}_duration'):
                    getattr(metrics, f'{metric_name}_duration').labels(
                        status=status,
                        service=metrics.service_name,
                        **(labels or {})
                    ).observe(duration)
                
                logger.debug(
                    f"Async function {func.__name__} executed",
                    duration=duration,
                    status=status,
                    metric_name=metric_name
                )
        return wrapper
    return decorator
