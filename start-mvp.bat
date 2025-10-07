@echo off
REM Скрипт запуска MVP Sales Voice Assistant для Windows

echo 🚀 Запуск MVP Sales Voice Assistant...

REM Проверка Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker не установлен. Установите Docker для запуска MVP.
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose не установлен. Установите Docker Compose для запуска MVP.
    exit /b 1
)

REM Создание .env файла если его нет
if not exist .env (
    echo 📝 Создание .env файла...
    (
        echo # Основные настройки
        echo NODE_ENV=development
        echo APP_VERSION=1.0.0
        echo.
        echo # База данных
        echo POSTGRES_URL=postgresql://postgres:postgres@postgres:5432/sales_voice
        echo POSTGRES_POOL_SIZE=10
        echo POSTGRES_MAX_OVERFLOW=20
        echo.
        echo # Redis
        echo REDIS_URL=redis://redis:6379
        echo REDIS_DB=0
        echo.
        echo # Qdrant
        echo QDRANT_URL=http://qdrant:6333
        echo.
        echo # OpenTelemetry
        echo OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
        echo OTEL_SERVICE_NAME=sales-voice-assistant
        echo OTEL_SERVICE_VERSION=1.0.0
        echo.
        echo # JWT
        echo JWT_SECRET_KEY=your-secret-key-change-in-production
        echo JWT_ALGORITHM=HS256
        echo JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo.
        echo # Yandex SpeechKit (замените на реальные ключи)
        echo YANDEX_SPEECHKIT_API_KEY=your-yandex-api-key
        echo YANDEX_SPEECHKIT_FOLDER_ID=your-folder-id
        echo.
        echo # OpenAI (замените на реальный ключ)
        echo OPENAI_API_KEY=your-openai-api-key
        echo OPENAI_MODEL=gpt-4
        echo OPENAI_TEMPERATURE=0.7
        echo OPENAI_MAX_TOKENS=1000
        echo.
        echo # Bitrix24 (замените на реальные данные)
        echo BITRIX24_WEBHOOK_URL=your-bitrix24-webhook-url
        echo BITRIX24_ACCESS_TOKEN=your-bitrix24-token
        echo.
        echo # Телефония
        echo VOXIMPLANT_ACCOUNT_ID=your-voximplant-account
        echo VOXIMPLANT_API_KEY=your-voximplant-key
        echo VOXIMPLANT_APPLICATION_ID=your-application-id
        echo.
        echo # SIP настройки
        echo SIP_SERVER=localhost
        echo SIP_USERNAME=telephony-gateway
        echo SIP_PASSWORD=password
        echo SIP_DOMAIN=localhost
        echo SIP_DISPLAY_NAME=Sales Voice Assistant
        echo.
        echo # Настройки звонков
        echo MAX_CALL_DURATION=1800
        echo DEFAULT_LANGUAGE=ru-RU
        echo ASR_PROVIDER=yandex
        echo TTS_PROVIDER=yandex
        echo LLM_PROVIDER=openai
        echo.
        echo # Безопасность
        echo CORS_ORIGINS=http://localhost:3000,http://localhost:3001
        echo CORS_ALLOW_CREDENTIALS=true
        echo.
        echo # Логирование
        echo LOG_LEVEL=INFO
        echo LOG_FORMAT=json
        echo.
        echo # Метрики
        echo METRICS_PORT=9090
    ) > .env
    echo ✅ .env файл создан. Не забудьте заполнить реальные API ключи!
)

REM Запуск инфраструктуры
echo 🐳 Запуск Docker контейнеров...
docker-compose -f infra/docker/docker-compose.yml up -d postgres redis qdrant

REM Ожидание готовности базы данных
echo ⏳ Ожидание готовности базы данных...
timeout /t 10 /nobreak >nul

REM Проверка подключения к базе данных
echo 🔍 Проверка подключения к базе данных...
docker-compose -f infra/docker/docker-compose.yml exec -T postgres pg_isready -U postgres

REM Запуск сервисов
echo 🚀 Запуск сервисов MVP...

REM Telephony Gateway
echo 📞 Запуск Telephony Gateway...
cd apps\telephony-gateway
call npm install
call npm run build
start "Telephony Gateway" cmd /k "npm start"
cd ..\..

REM ASR Service
echo 🎤 Запуск ASR Service...
cd apps\asr-service
py -m pip install -r requirements.txt
start "ASR Service" cmd /k "py main.py"
cd ..\..

REM TTS Service
echo 🔊 Запуск TTS Service...
cd apps\tts-service
py -m pip install -r requirements.txt
start "TTS Service" cmd /k "py main.py"
cd ..\..

REM Dialog Orchestrator
echo 🤖 Запуск Dialog Orchestrator...
cd apps\dialog-orchestrator
py -m pip install -r requirements.txt
start "Dialog Orchestrator" cmd /k "py main.py"
cd ..\..

REM CRM Connector
echo 📊 Запуск CRM Connector...
cd apps\crm-connector
py -m pip install -r requirements.txt
start "CRM Connector" cmd /k "py main.py"
cd ..\..

REM Ожидание запуска сервисов
echo ⏳ Ожидание запуска сервисов...
timeout /t 15 /nobreak >nul

echo.
echo 🎉 MVP Sales Voice Assistant запущен!
echo.
echo 📋 Доступные сервисы:
echo   📞 Telephony Gateway: http://localhost:3000
echo   🎤 ASR Service:       http://localhost:8001
echo   🔊 TTS Service:       http://localhost:8002
echo   🤖 Dialog Orchestrator: http://localhost:8003
echo   📊 CRM Connector:     http://localhost:8005
echo.
echo 📊 Мониторинг:
echo   🐳 Docker контейнеры: docker-compose -f infra/docker/docker-compose.yml ps
echo   📈 Логи: docker-compose -f infra/docker/docker-compose.yml logs -f
echo.
echo 🛑 Для остановки MVP закройте все окна командной строки и выполните:
echo   docker-compose -f infra/docker/docker-compose.yml down
echo.

echo ✅ MVP готов к работе!
pause
