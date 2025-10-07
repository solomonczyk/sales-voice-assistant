#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки правильного Folder ID
"""

import asyncio
import os
import sys
import aiohttp
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def check_folder_id():
    """Проверяем правильный Folder ID через API"""
    
    api_key = os.getenv("YANDEX_SPEECHKIT_API_KEY")
    current_folder_id = os.getenv("YANDEX_SPEECHKIT_FOLDER_ID")
    
    if not api_key:
        print("API key not found in .env file")
        return
    
    print(f"Current Folder ID: {current_folder_id}")
    print(f"API key: {api_key[:10]}...")
    
    # Пробуем разные варианты Folder ID
    test_folder_ids = [
        current_folder_id,  # Текущий
        "b1g9sbe74tutstjb73q4",  # Из ошибки
    ]
    
    for folder_id in test_folder_ids:
        if not folder_id:
            continue
            
        print(f"\nTesting Folder ID: {folder_id}")
        
        # Тест TTS API
        url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
        headers = {
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "text": "Тест",
            "lang": "ru-RU",
            "voice": "alena",
            "format": "wav",
            "folderId": folder_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        print(f"SUCCESS: Folder ID {folder_id} - WORKS!")
                        return folder_id
                    else:
                        error_text = await response.text()
                        print(f"ERROR: Folder ID {folder_id} - status: {response.status}")
                        if "folder ID" in error_text:
                            print(f"   Message: {error_text}")
        except Exception as e:
            print(f"ERROR: Folder ID {folder_id} - exception: {e}")
    
    print("\nERROR: No working Folder ID found")
    return None

async def main():
    print("Checking correct Folder ID for Yandex SpeechKit")
    print("=" * 60)
    
    working_folder_id = await check_folder_id()
    
    if working_folder_id:
        print(f"\nSUCCESS: Found working Folder ID: {working_folder_id}")
        print(f"\nUpdate .env file:")
        print(f"YANDEX_SPEECHKIT_FOLDER_ID={working_folder_id}")
    else:
        print("\nERROR: Could not find working Folder ID")
        print("\nTry:")
        print("1. Check in Yandex Cloud console - which catalog the service account was created in")
        print("2. Make sure the API key is correct")
        print("3. Check that the service account has ai.speechkit.user permissions")

if __name__ == "__main__":
    asyncio.run(main())
