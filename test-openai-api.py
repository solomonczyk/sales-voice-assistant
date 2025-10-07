#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки интеграции с OpenAI API
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

async def test_openai_tts():
    """Тест синтеза речи через OpenAI TTS"""
    print("Тестирование OpenAI TTS API...")
    
    try:
        import aiohttp
        
        # Получаем API ключ из переменных окружения
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("API ключ не настроен в .env файле")
            return False
        
        print(f"API ключ: {api_key[:10]}...")
        
        # Тестовый запрос к OpenAI TTS
        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "tts-1",
            "input": "Hello! This is a test of OpenAI text-to-speech synthesis.",
            "voice": "alloy",
            "response_format": "mp3"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    print(f"TTS успешно: получено {len(audio_data)} байт аудио")
                    
                    # Сохраняем тестовый файл
                    with open("test-openai-tts-output.mp3", "wb") as f:
                        f.write(audio_data)
                    print("Аудио файл сохранен: test-openai-tts-output.mp3")
                    return True
                else:
                    error_text = await response.text()
                    print(f"TTS ошибка: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"Ошибка TTS: {e}")
        return False

async def test_openai_whisper():
    """Тест распознавания речи через OpenAI Whisper"""
    print("\nТестирование OpenAI Whisper API...")
    
    try:
        import aiohttp
        
        # Получаем API ключ из переменных окружения
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("API ключ не настроен в .env файле")
            return False
        
        # Создаем тестовые аудио данные (заглушка)
        # В реальном тесте здесь должен быть настоящий WAV файл
        test_audio_data = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x00\x04\x00\x00\x00\x08\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        
        # Тестовый запрос к OpenAI Whisper
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Подготавливаем данные для multipart/form-data
        data = aiohttp.FormData()
        data.add_field('file', test_audio_data, filename='test.wav', content_type='audio/wav')
        data.add_field('model', 'whisper-1')
        data.add_field('language', 'en')
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"Whisper успешно: {result}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"Whisper ошибка: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"Ошибка Whisper: {e}")
        return False

async def test_services():
    """Тест наших сервисов с OpenAI интеграцией"""
    print("\nТестирование наших сервисов...")
    
    try:
        import aiohttp
        
        # Тест TTS Service
        print("Тест TTS Service...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8002/synthesize",
                json={
                    "text": "Hello! This is a test of our TTS service with OpenAI.",
                    "voice": "alloy",
                    "format": "mp3"
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
    print("Тестирование интеграции с OpenAI API")
    print("=" * 60)
    
    # Загружаем переменные окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    # Тесты
    tts_success = await test_openai_tts()
    whisper_success = await test_openai_whisper()
    
    print("\nРезультаты тестирования:")
    print(f"OpenAI TTS: {'Работает' if tts_success else 'Не работает'}")
    print(f"OpenAI Whisper: {'Работает' if whisper_success else 'Не работает'}")
    
    if tts_success and whisper_success:
        print("\nВсе тесты прошли успешно! OpenAI API интегрирован.")
    else:
        print("\nНекоторые тесты не прошли. Проверьте API ключ и настройки.")
    
    # Тест наших сервисов (если они запущены)
    try:
        await test_services()
    except:
        print("Наши сервисы не запущены - пропускаем тест")

if __name__ == "__main__":
    asyncio.run(main())
