#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки интеграции с Yandex SpeechKit API
"""

import asyncio
import os
import sys
from pathlib import Path

# Устанавливаем UTF-8 кодировку для вывода
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent))

async def test_yandex_tts():
    """Тест синтеза речи через Yandex TTS"""
    print("Тестирование Yandex TTS API...")
    
    try:
        import aiohttp
        
        # Получаем API ключи из переменных окружения
        api_key = os.getenv("YANDEX_SPEECHKIT_API_KEY")
        folder_id = os.getenv("YANDEX_SPEECHKIT_FOLDER_ID")
        
        if not api_key or not folder_id:
            print("API ключи не настроены в .env файле")
            return False
        
        print(f"API ключ: {api_key[:10]}...")
        print(f"Folder ID: {folder_id}")
        
        # Тестовый запрос к Yandex TTS
        url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
        headers = {
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "text": "Привет! Это тест синтеза речи через Yandex SpeechKit.",
            "lang": "ru-RU",
            "voice": "alena",
            "format": "wav",
            "folderId": folder_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    print(f"TTS успешно: получено {len(audio_data)} байт аудио")
                    
                    # Сохраняем тестовый файл
                    with open("test-tts-output.wav", "wb") as f:
                        f.write(audio_data)
                    print("Аудио файл сохранен: test-tts-output.wav")
                    return True
                else:
                    error_text = await response.text()
                    print(f"TTS ошибка: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"Ошибка TTS: {e}")
        return False

async def test_yandex_stt():
    """Тест распознавания речи через Yandex STT"""
    print("\nТестирование Yandex STT API...")
    
    try:
        import aiohttp
        
        # Получаем API ключи из переменных окружения
        api_key = os.getenv("YANDEX_SPEECHKIT_API_KEY")
        folder_id = os.getenv("YANDEX_SPEECHKIT_FOLDER_ID")
        
        if not api_key or not folder_id:
            print("API ключи не настроены в .env файле")
            return False
        
        # Создаем тестовые аудио данные (заглушка)
        # В реальном тесте здесь должен быть настоящий WAV файл
        test_audio_data = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x00\x04\x00\x00\x00\x08\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        
        # Тестовый запрос к Yandex STT
        url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        headers = {
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "audio/wav"
        }
        
        params = {
            "lang": "ru-RU",
            "folderId": folder_id,
            "format": "lpcm",
            "sampleRateHertz": "16000"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, params=params, data=test_audio_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"STT успешно: {result}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"STT ошибка: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"Ошибка STT: {e}")
        return False

async def test_services():
    """Тест наших сервисов с Yandex интеграцией"""
    print("\nТестирование наших сервисов...")
    
    try:
        import aiohttp
        
        # Тест TTS Service
        print("Тест TTS Service...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8002/synthesize",
                json={
                    "text": "Привет! Это тест нашего TTS сервиса с Yandex.",
                    "voice": "alena",
                    "format": "wav"
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"TTS Service: {result}")
                else:
                    error_text = await response.text()
                    print(f"TTS Service ошибка: {response.status} - {error_text}")
        
        # Тест ASR Service (требует аудио файл)
        print("Тест ASR Service...")
        # Здесь нужен реальный аудио файл для тестирования
        
    except Exception as e:
        print(f"Ошибка тестирования сервисов: {e}")

async def main():
    """Основная функция тестирования"""
    print("Тестирование интеграции с Yandex SpeechKit API")
    print("=" * 60)
    
    # Загружаем переменные окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    # Тесты
    tts_success = await test_yandex_tts()
    stt_success = await test_yandex_stt()
    
    print("\nРезультаты тестирования:")
    print(f"Yandex TTS: {'Работает' if tts_success else 'Не работает'}")
    print(f"Yandex STT: {'Работает' if stt_success else 'Не работает'}")
    
    if tts_success and stt_success:
        print("\nВсе тесты прошли успешно! Yandex SpeechKit интегрирован.")
    else:
        print("\nНекоторые тесты не прошли. Проверьте API ключи и настройки.")
    
    # Тест наших сервисов (если они запущены)
    try:
        await test_services()
    except:
        print("ℹ️ Наши сервисы не запущены - пропускаем тест")

if __name__ == "__main__":
    asyncio.run(main())
