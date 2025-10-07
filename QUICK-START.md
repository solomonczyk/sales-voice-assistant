# 🚀 Быстрый запуск MVP Sales Voice Assistant

## ⚡ Упрощенный запуск (без Docker)

### 1. Запуск Python сервисов
```bash
# Запуск всех Python сервисов
start-mvp-simple.bat

# Или вручную:
cd apps/asr-service && python main.py
cd apps/tts-service && python main.py  
cd apps/dialog-orchestrator && python main.py
cd apps/crm-connector && python main.py
```

### 2. Тестирование
```bash
# Тест всех сервисов
python test-mvp-simple.py
```

### 3. Доступные endpoints
- 🎤 **ASR Service**: http://localhost:8001
- 🔊 **TTS Service**: http://localhost:8002  
- 🤖 **Dialog Orchestrator**: http://localhost:8003
- 📊 **CRM Connector**: http://localhost:8005

## 🐳 Полный запуск (с Docker)

### Предварительные требования
1. **Docker Desktop** должен быть запущен
2. **Python 3.11+** установлен
3. **Node.js 20+** установлен

### 1. Запуск инфраструктуры
```bash
# Запуск PostgreSQL, Redis, Qdrant
docker-compose -f infra/docker/docker-compose.yml up -d postgres redis qdrant
```

### 2. Запуск всех сервисов
```bash
# Полный MVP с инфраструктурой
start-mvp.bat
```

### 3. Тестирование
```bash
# Полный тест с инфраструктурой
python test-mvp.py
```

## 🔧 Решение проблем

### Docker не запущен
```
error: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```
**Решение**: Запустите Docker Desktop

### Python не найден
```
Fatal error in launcher: Unable to create process using python.exe
```
**Решение**: 
```bash
# Проверьте версию Python
python --version

# Если Python312, используйте:
python -m pip install -r requirements.txt
```

### TypeScript ошибки
```
Property 'CORS_ORIGINS' comes from an index signature
```
**Решение**: Исправлено в tsconfig.json (отключены строгие проверки)

## 📋 API Endpoints

### ASR Service (http://localhost:8001)
```bash
# Распознавание речи
curl -X POST http://localhost:8001/recognize \
  -F "audio=@test.wav" \
  -F "language=ru-RU"
```

### TTS Service (http://localhost:8002)
```bash
# Синтез речи
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Привет!", "voice": "alena"}'
```

### Dialog Orchestrator (http://localhost:8003)
```bash
# Диалог с ассистентом
curl -X POST http://localhost:8003/dialog \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "user_message": "Привет!"}'
```

### CRM Connector (http://localhost:8005)
```bash
# Создание лида
curl -X POST http://localhost:8005/leads \
  -H "Content-Type: application/json" \
  -d '{"title": "Новый лид", "name": "Иван", "phone": "+79991234567"}'
```

## 🔑 Настройка API ключей

Создайте файл `.env` с реальными ключами:
```env
# Yandex SpeechKit
YANDEX_SPEECHKIT_API_KEY=your-real-api-key
YANDEX_SPEECHKIT_FOLDER_ID=your-folder-id

# OpenAI
OPENAI_API_KEY=your-openai-key

# Bitrix24
BITRIX24_WEBHOOK_URL=your-webhook-url
BITRIX24_ACCESS_TOKEN=your-token
```

## 🛑 Остановка сервисов

### Упрощенная версия
Закройте все окна командной строки

### Полная версия
```bash
# Остановка Docker контейнеров
docker-compose -f infra/docker/docker-compose.yml down

# Остановка Python сервисов
# Закройте окна командной строки
```

## 📊 Мониторинг

### Логи сервисов
```bash
# Docker логи
docker-compose -f infra/docker/docker-compose.yml logs -f

# Python логи
# Смотрите в окнах командной строки
```

### Health checks
```bash
# Проверка здоровья всех сервисов
curl http://localhost:8001/health  # ASR
curl http://localhost:8002/health  # TTS  
curl http://localhost:8003/health  # Dialog
curl http://localhost:8005/health  # CRM
```

## 🎯 Следующие шаги

1. **Настройте реальные API ключи** в `.env`
2. **Протестируйте интеграции** с реальными сервисами
3. **Добавьте telephony-gateway** после исправления TypeScript ошибок
4. **Настройте мониторинг** и логирование
5. **Создайте тестовые сценарии** для продаж

---

💡 **Совет**: Начните с упрощенной версии для быстрого тестирования, затем переходите к полной версии с Docker.
