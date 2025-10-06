"""
Конфигурация приложения
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class Settings(PydanticBaseSettings):
    """Настройки приложения"""
    
    # Основные настройки
    app_name: str = Field(default="Sales Voice Assistant", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # База данных
    postgres_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/sales_voice",
        env="POSTGRES_URL"
    )
    postgres_pool_size: int = Field(default=10, env="POSTGRES_POOL_SIZE")
    postgres_max_overflow: int = Field(default=20, env="POSTGRES_MAX_OVERFLOW")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    
    # OpenTelemetry
    otel_exporter_otlp_endpoint: str = Field(
        default="http://localhost:4317", 
        env="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    otel_service_name: str = Field(default="sales-voice-assistant", env="OTEL_SERVICE_NAME")
    otel_service_version: str = Field(default="1.0.0", env="OTEL_SERVICE_VERSION")
    
    # JWT
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Yandex SpeechKit
    yandex_speechkit_api_key: Optional[str] = Field(default=None, env="YANDEX_SPEECHKIT_API_KEY")
    yandex_speechkit_folder_id: Optional[str] = Field(default=None, env="YANDEX_SPEECHKIT_FOLDER_ID")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    
    # Bitrix24
    bitrix24_webhook_url: Optional[str] = Field(default=None, env="BITRIX24_WEBHOOK_URL")
    bitrix24_access_token: Optional[str] = Field(default=None, env="BITRIX24_ACCESS_TOKEN")
    
    # Телефония
    voximplant_account_id: Optional[str] = Field(default=None, env="VOXIMPLANT_ACCOUNT_ID")
    voximplant_api_key: Optional[str] = Field(default=None, env="VOXIMPLANT_API_KEY")
    voximplant_application_id: Optional[str] = Field(default=None, env="VOXIMPLANT_APPLICATION_ID")
    
    # Настройки звонков
    max_call_duration: int = Field(default=1800, env="MAX_CALL_DURATION")  # 30 минут
    default_language: str = Field(default="ru-RU", env="DEFAULT_LANGUAGE")
    asr_provider: str = Field(default="yandex", env="ASR_PROVIDER")
    tts_provider: str = Field(default="yandex", env="TTS_PROVIDER")
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    
    # Безопасность
    cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: list[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: list[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # Логирование
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json или text
    
    # Метрики
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    metrics_path: str = Field(default="/metrics", env="METRICS_PATH")
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("cors_allow_methods", pre=True)
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v
    
    @validator("cors_allow_headers", pre=True)
    def parse_cors_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v
    
    @validator("environment")
    def validate_environment(cls, v):
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Получить настройки приложения (кэшированные)"""
    return Settings()
