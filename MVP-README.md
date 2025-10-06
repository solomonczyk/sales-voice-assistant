# 🚀 MVP Sales Voice Assistant

Минимально жизнеспособный продукт голосового ассистента для отдела продаж.

## 🎯 Что включено в MVP

### ✅ Готовые сервисы:
- **📞 Telephony Gateway** (порт 3000) - SIP/WebRTC шлюз
- **🎤 ASR Service** (порт 8001) - распознавание речи
- **🔊 TTS Service** (порт 8002) - синтез речи  
- **🤖 Dialog Orchestrator** (порт 8003) - диалоговый агент
- **📊 CRM Connector** (порт 8005) - интеграция с CRM

### ✅ Инфраструктура:
- **🐘 PostgreSQL** - база данных
- **🔴 Redis** - кэширование
- **🔍 Qdrant** - векторное хранилище
- **📈 Prometheus** - метрики
- **📊 Grafana** - дашборды
- **🔍 Jaeger** - трассировка

## 🚀 Быстрый запуск

### Windows:
```cmd
start-mvp.bat
```

### Linux/macOS:
```bash
chmod +x start-mvp.sh
./start-mvp.sh
```

### Ручной запуск:
```bash
# 1. Запуск инфраструктуры
docker-compose -f infra/docker/docker-compose.yml up -d postgres redis qdrant

# 2. Запуск сервисов
cd apps/telephony-gateway && npm install && npm start &
cd apps/asr-service && pip install -r requirements.txt && python main.py &
cd apps/tts-service && pip install -r requirements.txt && python main.py &
cd apps/dialog-orchestrator && pip install -r requirements.txt && python main.py &
cd apps/crm-connector && pip install -r requirements.txt && python main.py &
```

## 🔧 Настройка API ключей

Перед запуском заполните реальные API ключи в `.env` файле:

```bash
# Yandex SpeechKit
YANDEX_SPEECHKIT_API_KEY=your-real-api-key
YANDEX_SPEECHKIT_FOLDER_ID=your-folder-id

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Bitrix24
BITRIX24_WEBHOOK_URL=your-webhook-url
BITRIX24_ACCESS_TOKEN=your-access-token
```

## 📋 API Endpoints

### Telephony Gateway (3000)
- `GET /health` - проверка здоровья
- `POST /api/v1/calls` - создание звонка
- `GET /api/v1/calls/:id` - получение звонка
- `GET /metrics` - метрики Prometheus

### ASR Service (8001)
- `GET /health` - проверка здоровья
- `POST /recognize` - распознавание речи
- `POST /recognize/stream` - потоковое распознавание
- `GET /stats` - статистика

### TTS Service (8002)
- `GET /health` - проверка здоровья
- `POST /synthesize` - синтез речи
- `POST /synthesize/stream` - потоковый синтез
- `GET /voices` - список голосов
- `GET /stats` - статистика

### Dialog Orchestrator (8003)
- `GET /health` - проверка здоровья
- `POST /dialog` - обработка диалога
- `GET /intents` - доступные намерения
- `GET /stats` - статистика

### CRM Connector (8005)
- `GET /health` - проверка здоровья
- `POST /leads` - создание лида
- `POST /deals` - создание сделки
- `POST /tasks` - создание задачи
- `GET /stats` - статистика

## 🧪 Тестирование MVP

### 1. Проверка здоровья сервисов:
```bash
curl http://localhost:3000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8005/health
```

### 2. Тест распознавания речи:
```bash
curl -X POST http://localhost:8001/recognize \
  -F "audio=@test-audio.wav" \
  -F "language=ru-RU"
```

### 3. Тест синтеза речи:
```bash
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Привет! Это тестовый синтез речи.", "voice": "alena"}'
```

### 4. Тест диалога:
```bash
curl -X POST http://localhost:8003/dialog \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-123", "user_message": "Привет! Расскажи о ваших продуктах"}'
```

### 5. Тест создания лида:
```bash
curl -X POST http://localhost:8005/leads \
  -H "Content-Type: application/json" \
  -d '{"title": "Новый лид", "name": "Иван Иванов", "phone": "+7 (999) 123-45-67", "source": "phone_call"}'
```

## 📊 Мониторинг

### Метрики Prometheus:
- http://localhost:9090 - Prometheus UI
- http://localhost:3000/metrics - метрики Telephony Gateway

### Дашборды Grafana:
- http://localhost:3000 - Grafana UI (admin/admin)

### Трассировка Jaeger:
- http://localhost:16686 - Jaeger UI

## 🛑 Остановка MVP

### Windows:
```cmd
docker-compose -f infra/docker/docker-compose.yml down
```

### Linux/macOS:
```bash
# Остановка сервисов
if [ -f .mvp-pids ]; then
    kill $(cat .mvp-pids)
    rm .mvp-pids
fi

# Остановка инфраструктуры
docker-compose -f infra/docker/docker-compose.yml down
```

## 🔧 Требования

### Системные требования:
- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Node.js** 18+ (для telephony-gateway)
- **Python** 3.11+ (для остальных сервисов)

### API ключи:
- **Yandex SpeechKit** - для ASR/TTS
- **OpenAI API** - для диалогового агента
- **Bitrix24** - для CRM интеграции

## 🚧 Ограничения MVP

### Что работает:
- ✅ Базовая архитектура сервисов
- ✅ HTTP API для всех сервисов
- ✅ Простые диалоговые сценарии
- ✅ Создание лидов и задач
- ✅ Мониторинг и метрики

### Что нужно доработать:
- 🔄 Реальная интеграция с Yandex SpeechKit
- 🔄 Потоковая обработка аудио
- 🔄 Интеграция с OpenAI для диалогов
- 🔄 Реальная интеграция с Bitrix24
- 🔄 SIP/WebRTC интеграция
- 🔄 Обработка ошибок и retry логика

## 📈 Следующие шаги

1. **Получить API ключи** и заполнить .env
2. **Протестировать** все endpoints
3. **Интегрировать** с реальными сервисами
4. **Добавить** обработку ошибок
5. **Настроить** мониторинг и алерты

## 🆘 Поддержка

При проблемах проверьте:
1. Логи сервисов: `docker-compose logs -f`
2. Статус контейнеров: `docker-compose ps`
3. Health checks всех сервисов
4. Наличие API ключей в .env

---

**🎉 MVP готов к тестированию и дальнейшей разработке!**
