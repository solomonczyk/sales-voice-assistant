#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест ASR Service с реальным аудио файлом
"""

import requests
import sys

# Устанавливаем UTF-8 кодировку для вывода
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def test_asr():
    """Тестируем ASR Service"""
    print("Testing ASR Service with real audio file...")
    
    try:
        # Отправляем аудио файл
        with open('test-audio.wav', 'rb') as audio_file:
            files = {'audio': audio_file}
            params = {'language': 'en'}
            
            response = requests.post(
                'http://localhost:8001/recognize',
                files=files,
                params=params
            )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Result: {result}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_asr()
