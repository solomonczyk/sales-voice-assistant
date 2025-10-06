#!/bin/bash

# Скрипт запуска MVP Sales Voice Assistant

set -e

echo "🚀 Запуск MVP Sales Voice Assistant..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker для запуска MVP."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose для запуска MVP."
    exit 1
fi

# Создание .env файла если его нет
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cat > .env << EOF
# Основные настройки
NODE_ENV=development
APP_VERSION=1.0.0

# База данных
POSTGRES_URL=postgresql://postgres:postgres@postgres:5432/sales_voice
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://redis:6379
REDIS_DB=0

# Qdrant
QDRANT_URL=http://qdrant:6333

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_SERVICE_NAME=sales-voice-assistant
OTEL_SERVICE_VERSION=1.0.0

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Yandex SpeechKit (замените на реальные ключи)
YANDEX_SPEECHKIT_API_KEY=your-yandex-api-key
YANDEX_SPEECHKIT_FOLDER_ID=your-folder-id

# OpenAI (замените на реальный ключ)
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000

# Bitrix24 (замените на реальные данные)
BITRIX24_WEBHOOK_URL=your-bitrix24-webhook-url
BITRIX24_ACCESS_TOKEN=your-bitrix24-token

# Телефония
VOXIMPLANT_ACCOUNT_ID=your-voximplant-account
VOXIMPLANT_API_KEY=your-voximplant-key
VOXIMPLANT_APPLICATION_ID=your-application-id

# SIP настройки
SIP_SERVER=localhost
SIP_USERNAME=telephony-gateway
SIP_PASSWORD=password
SIP_DOMAIN=localhost
SIP_DISPLAY_NAME=Sales Voice Assistant

# Настройки звонков
MAX_CALL_DURATION=1800
DEFAULT_LANGUAGE=ru-RU
ASR_PROVIDER=yandex
TTS_PROVIDER=yandex
LLM_PROVIDER=openai

# Безопасность
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
CORS_ALLOW_CREDENTIALS=true

# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=json

# Метрики
METRICS_PORT=9090
EOF
    echo "✅ .env файл создан. Не забудьте заполнить реальные API ключи!"
fi

# Запуск инфраструктуры
echo "🐳 Запуск Docker контейнеров..."
docker-compose -f infra/docker/docker-compose.yml up -d postgres redis qdrant

# Ожидание готовности базы данных
echo "⏳ Ожидание готовности базы данных..."
sleep 10

# Проверка подключения к базе данных
echo "🔍 Проверка подключения к базе данных..."
docker-compose -f infra/docker/docker-compose.yml exec -T postgres pg_isready -U postgres

# Запуск сервисов
echo "🚀 Запуск сервисов MVP..."

# Telephony Gateway
echo "📞 Запуск Telephony Gateway..."
cd apps/telephony-gateway
npm install
npm run build
npm start &
TELEPHONY_PID=$!
cd ../..

# ASR Service
echo "🎤 Запуск ASR Service..."
cd apps/asr-service
pip install -r requirements.txt
python main.py &
ASR_PID=$!
cd ../..

# TTS Service
echo "🔊 Запуск TTS Service..."
cd apps/tts-service
pip install -r requirements.txt
python main.py &
TTS_PID=$!
cd ../..

# Dialog Orchestrator
echo "🤖 Запуск Dialog Orchestrator..."
cd apps/dialog-orchestrator
pip install -r requirements.txt
python main.py &
DIALOG_PID=$!
cd ../..

# CRM Connector
echo "📊 Запуск CRM Connector..."
cd apps/crm-connector
pip install -r requirements.txt
python main.py &
CRM_PID=$!
cd ../..

# Ожидание запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 15

# Проверка здоровья сервисов
echo "🏥 Проверка здоровья сервисов..."

check_service() {
    local name=$1
    local url=$2
    local pid=$3
    
    if curl -f -s "$url" > /dev/null; then
        echo "✅ $name запущен (PID: $pid)"
    else
        echo "❌ $name не отвечает (PID: $pid)"
    fi
}

check_service "Telephony Gateway" "http://localhost:3000/health" $TELEPHONY_PID
check_service "ASR Service" "http://localhost:8001/health" $ASR_PID
check_service "TTS Service" "http://localhost:8002/health" $TTS_PID
check_service "Dialog Orchestrator" "http://localhost:8003/health" $DIALOG_PID
check_service "CRM Connector" "http://localhost:8005/health" $CRM_PID

echo ""
echo "🎉 MVP Sales Voice Assistant запущен!"
echo ""
echo "📋 Доступные сервисы:"
echo "  📞 Telephony Gateway: http://localhost:3000"
echo "  🎤 ASR Service:       http://localhost:8001"
echo "  🔊 TTS Service:       http://localhost:8002"
echo "  🤖 Dialog Orchestrator: http://localhost:8003"
echo "  📊 CRM Connector:     http://localhost:8005"
echo ""
echo "📊 Мониторинг:"
echo "  🐳 Docker контейнеры: docker-compose -f infra/docker/docker-compose.yml ps"
echo "  📈 Логи: docker-compose -f infra/docker/docker-compose.yml logs -f"
echo ""
echo "🛑 Для остановки MVP:"
echo "  kill $TELEPHONY_PID $ASR_PID $TTS_PID $DIALOG_PID $CRM_PID"
echo "  docker-compose -f infra/docker/docker-compose.yml down"
echo ""

# Сохранение PID для остановки
echo "$TELEPHONY_PID $ASR_PID $TTS_PID $DIALOG_PID $CRM_PID" > .mvp-pids

echo "✅ MVP готов к работе!"
