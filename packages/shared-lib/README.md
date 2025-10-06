# Sales Voice Shared Library

Общие утилиты, модели и компоненты для всех сервисов проекта Sales Voice Assistant.

## Установка

```bash
pip install -e .
```

## Компоненты

### Конфигурация (`config.py`)

Централизованная система конфигурации на основе Pydantic:

```python
from sales_voice_shared import get_settings

settings = get_settings()
print(settings.postgres_url)
```

### Модели данных (`models.py`)

SQLAlchemy модели и Pydantic схемы для всех сущностей:

```python
from sales_voice_shared import User, Client, Call, UserCreate, UserResponse

# Создание пользователя
user_data = UserCreate(email="user@example.com", name="John Doe")
user = User(**user_data.dict())
```

### База данных (`database.py`)

Управление подключениями к базе данных:

```python
from sales_voice_shared import get_database, get_sync_session, get_async_session

# Синхронная сессия
for session in get_sync_session():
    # Работа с БД
    pass

# Асинхронная сессия
async for session in get_async_session():
    # Работа с БД
    pass
```

### Логирование (`logging.py`)

Структурированное логирование с поддержкой JSON:

```python
from sales_voice_shared import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

logger.info("User created", user_id="123", email="user@example.com")
```

### Метрики (`metrics.py`)

Система метрик Prometheus:

```python
from sales_voice_shared import get_metrics

metrics = get_metrics()
metrics.record_http_request("GET", "/users", 200, 0.1)
metrics.record_call("incoming", "completed", 120.5)
```

### Трассировка (`tracing.py`)

OpenTelemetry трассировка:

```python
from sales_voice_shared import setup_tracing, get_tracer, trace_function

setup_tracing()

@trace_function("user_creation")
def create_user(user_data):
    # Создание пользователя
    pass

tracer = get_tracer(__name__)
with tracer.start_as_current_span("operation") as span:
    span.set_attribute("user.id", "123")
    # Операция
```

### Утилиты (`utils.py`)

Общие утилиты:

```python
from sales_voice_shared import (
    validate_phone, format_phone, generate_session_id,
    hash_password, verify_password, create_access_token,
    encrypt_data, decrypt_data, sanitize_for_logging
)

# Валидация телефона
if validate_phone("+7 (999) 123-45-67"):
    formatted = format_phone("+7 (999) 123-45-67")

# Работа с паролями
hashed = hash_password("password123")
is_valid = verify_password("password123", hashed)

# JWT токены
token = create_access_token({"user_id": "123"})
payload = verify_access_token(token)
```

## Использование в сервисах

### FastAPI сервис

```python
from fastapi import FastAPI, Depends
from sales_voice_shared import (
    setup_logging, setup_tracing, get_metrics,
    get_sync_session, UserCreate, UserResponse
)
from sqlalchemy.orm import Session

setup_logging()
setup_tracing("my-service")
metrics = get_metrics("my-service")

app = FastAPI()

@app.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_sync_session)
):
    metrics.record_http_request("POST", "/users", 200, 0.1)
    # Создание пользователя
    pass
```

### Асинхронный сервис

```python
from fastapi import FastAPI, Depends
from sales_voice_shared import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

@app.post("/users")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    # Асинхронная работа с БД
    pass
```

## Переменные окружения

Основные переменные окружения для конфигурации:

```bash
# База данных
POSTGRES_URL=postgresql://user:pass@localhost:5432/sales_voice

# Redis
REDIS_URL=redis://localhost:6379

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=my-service

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Провайдеры
YANDEX_SPEECHKIT_API_KEY=your-api-key
OPENAI_API_KEY=your-api-key
BITRIX24_WEBHOOK_URL=your-webhook-url
```

## Разработка

### Установка зависимостей для разработки

```bash
pip install -e ".[dev]"
```

### Запуск тестов

```bash
pytest
```

### Линтинг

```bash
black .
isort .
flake8 .
mypy .
```

### Pre-commit hooks

```bash
pre-commit install
```

## Структура проекта

```
src/sales_voice_shared/
├── __init__.py          # Экспорты
├── config.py            # Конфигурация
├── models.py            # Модели данных
├── database.py          # База данных
├── logging.py           # Логирование
├── metrics.py           # Метрики
├── tracing.py           # Трассировка
└── utils.py             # Утилиты
```

## Лицензия

MIT License
