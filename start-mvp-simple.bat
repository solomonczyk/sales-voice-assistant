@echo off
REM Упрощенный запуск MVP без Docker (только Python сервисы)

echo 🚀 Запуск MVP Sales Voice Assistant (упрощенная версия)...

REM Проверка Python
py --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.11+ для запуска MVP.
    exit /b 1
)

echo ✅ Python найден

REM Создание .env файла если его нет
if not exist .env (
    echo 📝 Создание .env файла...
    (
        echo NODE_ENV=development
        echo APP_VERSION=1.0.0
        echo LOG_LEVEL=INFO
        echo LOG_FORMAT=json
    ) > .env
    echo ✅ .env файл создан
)

REM Запуск ASR Service
echo 🎤 Запуск ASR Service...
cd apps\asr-service
py -m pip install -r requirements.txt --quiet
start "ASR Service" cmd /k "py main.py"
cd ..\..

REM Запуск TTS Service
echo 🔊 Запуск TTS Service...
cd apps\tts-service
py -m pip install -r requirements.txt --quiet
start "TTS Service" cmd /k "py main.py"
cd ..\..

REM Запуск Dialog Orchestrator
echo 🤖 Запуск Dialog Orchestrator...
cd apps\dialog-orchestrator
py -m pip install -r requirements.txt --quiet
start "Dialog Orchestrator" cmd /k "py main.py"
cd ..\..

REM Запуск CRM Connector
echo 📊 Запуск CRM Connector...
cd apps\crm-connector
py -m pip install -r requirements.txt --quiet
start "CRM Connector" cmd /k "py main.py"
cd ..\..

REM Ожидание запуска сервисов
echo ⏳ Ожидание запуска сервисов...
timeout /t 10 /nobreak >nul

echo.
echo 🎉 MVP Python сервисы запущены!
echo.
echo 📋 Доступные сервисы:
echo   🎤 ASR Service:       http://localhost:8001
echo   🔊 TTS Service:       http://localhost:8002
echo   🤖 Dialog Orchestrator: http://localhost:8003
echo   📊 CRM Connector:     http://localhost:8005
echo.
echo 🧪 Тестирование:
echo   py test-mvp-simple.py
echo.
echo 🛑 Для остановки закройте все окна командной строки
echo.

echo ✅ MVP готов к тестированию!
pause
