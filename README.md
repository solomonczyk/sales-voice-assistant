# Sales Voice Assistant

Голосовой ассистент для автоматизации входящих и исходящих звонков отдела продаж с интеграцией в CRM системы.

## 🎯 Цели проекта

- Автоматизация входящих/исходящих звонков отдела продаж
- Квалификация лидов и сбор намерений клиентов
- Интеграция с CRM (Bitrix24) для создания лидов и сделок
- Русскоязычная речь в реальном времени
- Масштабируемая архитектура для роста нагрузки

## 🏗️ Архитектура

### Микросервисы

- **telephony-gateway** - SIP/WebRTC шлюз для обработки звонков
- **asr-service** - Распознавание речи (Yandex SpeechKit)
- **tts-service** - Синтез речи (Yandex SpeechKit)
- **dialog-orchestrator** - Диалоговый агент на LangGraph
- **rag-service** - Векторное хранилище знаний (Qdrant)
- **crm-connector** - Интеграция с Bitrix24
- **analytics** - Аналитика и метрики
- **admin-api** - Управление и настройки

### Технологический стек

- **Телефония**: Voximplant (CPaaS)
- **ASR/TTS**: Yandex SpeechKit
- **LLM**: OpenAI Realtime API
- **Оркестрация**: LangGraph
- **RAG**: Qdrant
- **Мониторинг**: OpenTelemetry + Prometheus + Jaeger
- **Контейнеризация**: Docker + Kubernetes

## 🚀 Быстрый старт

```bash
# Клонирование репозитория
git clone <repository-url>
cd sales-voice-assistant

# Запуск инфраструктуры
docker-compose -f infra/docker/docker-compose.yml up -d

# Запуск сервисов
make start
```

## 📁 Структура проекта

```
sales-voice-assistant/
├── apps/                    # Микросервисы
│   ├── telephony-gateway/   # SIP/WebRTC шлюз
│   ├── asr-service/         # Распознавание речи
│   ├── tts-service/         # Синтез речи
│   ├── dialog-orchestrator/ # Диалоговый агент
│   ├── rag-service/         # Векторное хранилище
│   ├── crm-connector/       # CRM интеграция
│   ├── analytics/           # Аналитика
│   └── admin-api/           # Админ API
├── packages/                # Общие пакеты
│   ├── shared-proto/        # gRPC схемы
│   └── shared-lib/          # Общие утилиты
├── infra/                   # Инфраструктура
│   ├── docker/              # Docker конфигурации
│   ├── k8s/                 # Kubernetes манифесты
│   └── otel/                # OpenTelemetry конфигурации
├── docs/                    # Документация
│   ├── architecture.md      # Архитектурная документация
│   ├── runbook.md          # Руководство по эксплуатации
│   └── diary.md            # Дневник разработки
└── tests/                   # Тесты
    ├── e2e/                # Сквозные тесты
    ├── contract/           # Контрактные тесты
    └── unit/               # Юнит тесты
```

## 📋 План разработки

### Этап 1 (1-2 недели): MVP
- [x] Базовая структура проекта
- [ ] Настройка CI/CD
- [ ] Telephony gateway
- [ ] Базовый диалоговый агент
- [ ] Интеграция с Bitrix24

### Этап 2 (2-3 недели): Расширенная функциональность
- [ ] Инструментальные вызовы
- [ ] Сценарии маршрутизации
- [ ] Аналитика диалогов

### Этап 3 (2-4 недели): RAG и оптимизация
- [ ] Векторное хранилище знаний
- [ ] A/B тестирование
- [ ] Оптимизация производительности

## 🔧 Разработка

### Требования
- Node.js 20+
- Python 3.11+
- Docker & Docker Compose
- Git

### Команды разработки

```bash
# Установка зависимостей
make install

# Запуск тестов
make test

# Линтинг
make lint

# Сборка
make build

# Запуск в dev режиме
make dev
```

## 📊 Мониторинг

- **Метрики**: Prometheus + Grafana
- **Трассировка**: Jaeger
- **Логи**: OpenTelemetry Collector
- **Алерты**: Prometheus AlertManager

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Сделайте коммит (`git commit -m 'Add amazing feature'`)
4. Запушьте в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 📞 Контакты

- Проект: Sales Voice Assistant
- Документация: [docs/](docs/)
- Дневник разработки: [docs/diary.md](docs/diary.md)
