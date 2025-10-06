# Telephony Gateway

SIP/WebRTC шлюз для обработки звонков в системе Sales Voice Assistant.

## Возможности

- ✅ Обработка входящих и исходящих SIP звонков
- ✅ Управление WebRTC соединениями
- ✅ Хранение данных о звонках в PostgreSQL
- ✅ Кэширование в Redis
- ✅ Метрики Prometheus
- ✅ Трассировка OpenTelemetry
- ✅ Структурированное логирование
- ✅ Health checks
- ✅ Graceful shutdown

## Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SIP Client    │◄──►│ Telephony Gateway│◄──►│  WebRTC Client  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Call Manager   │
                       └──────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
        │ PostgreSQL  │ │    Redis    │ │  Metrics    │
        └─────────────┘ └─────────────┘ └─────────────┘
```

## Установка и запуск

### Требования

- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Установка зависимостей

```bash
npm install
```

### Настройка окружения

Скопируйте `env.example` в `.env` и настройте переменные:

```bash
cp env.example .env
```

### Запуск в режиме разработки

```bash
npm run dev
```

### Сборка и запуск

```bash
npm run build
npm start
```

## API Endpoints

### Звонки

- `POST /api/v1/calls` - Создать звонок
- `GET /api/v1/calls/:id` - Получить звонок
- `PATCH /api/v1/calls/:id/status` - Обновить статус звонка
- `POST /api/v1/calls/:id/end` - Завершить звонок
- `GET /api/v1/calls` - Получить список звонков
- `POST /api/v1/calls/:id/sessions` - Создать сессию звонка

### Мониторинг

- `GET /health` - Базовый health check
- `GET /health/detailed` - Детальный health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check
- `GET /metrics` - Метрики Prometheus

## WebSocket Events

### Клиент → Сервер

- `join-call` - Присоединиться к звонку
- `leave-call` - Покинуть звонок
- `offer` - WebRTC предложение
- `answer` - WebRTC ответ
- `ice-candidate` - ICE кандидат

### Сервер → Клиент

- `joined-call` - Успешное присоединение
- `offer` - Получение предложения
- `answer` - Получение ответа
- `ice-candidate` - Получение ICE кандидата
- `error` - Ошибка

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `NODE_ENV` | Окружение | `development` |
| `PORT` | Порт сервера | `3000` |
| `POSTGRES_URL` | URL PostgreSQL | `postgresql://postgres:postgres@localhost:5432/sales_voice` |
| `REDIS_URL` | URL Redis | `redis://localhost:6379` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry endpoint | `http://localhost:4317` |
| `LOG_LEVEL` | Уровень логирования | `info` |
| `CORS_ORIGINS` | Разрешенные CORS origins | `*` |

## Разработка

### Запуск тестов

```bash
npm test
```

### Линтинг

```bash
npm run lint
npm run lint:fix
```

### Форматирование

```bash
npm run format
```

## Docker

### Сборка образа

```bash
docker build -t telephony-gateway .
```

### Запуск контейнера

```bash
docker run -p 3000:3000 telephony-gateway
```

## Мониторинг

### Метрики Prometheus

Доступны на `/metrics`:

- `http_requests_total` - Общее количество HTTP запросов
- `http_request_duration_seconds` - Длительность HTTP запросов
- `calls_total` - Общее количество звонков
- `call_duration_seconds` - Длительность звонков
- `active_calls` - Количество активных звонков
- `webrtc_connections_total` - Общее количество WebRTC соединений
- `active_webrtc_connections` - Количество активных WebRTC соединений

### Health Checks

- `/health` - Базовый статус
- `/health/detailed` - Детальная информация о всех компонентах
- `/health/ready` - Готовность к обработке запросов
- `/health/live` - Живость сервиса

## Безопасность

- Helmet.js для базовой защиты
- CORS настройки
- Rate limiting
- Валидация входных данных
- Логирование всех запросов
- Маскирование чувствительных данных

## Производительность

- Connection pooling для PostgreSQL
- Кэширование в Redis
- Сжатие ответов
- Метрики производительности
- Graceful shutdown

## Лицензия

MIT
