#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест полного пайплайна голосового ассистента
ASR -> Dialog -> TTS
"""

import requests
import sys
import json

# Устанавливаем UTF-8 кодировку для вывода
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def test_full_pipeline():
    """Тестируем полный пайплайн голосового ассистента"""
    print("Testing Full Voice Assistant Pipeline")
    print("=" * 50)
    
    try:
        # 1. ASR - Распознавание речи
        print("\n1. ASR (Speech Recognition)")
        print("-" * 30)
        
        with open('test-audio.wav', 'rb') as audio_file:
            files = {'audio': audio_file}
            params = {'language': 'en'}
            
            asr_response = requests.post(
                'http://localhost:8001/recognize',
                files=files,
                params=params
            )
        
        if asr_response.status_code == 200:
            asr_result = asr_response.json()
            recognized_text = asr_result['text']
            print(f"✅ ASR: '{recognized_text}'")
        else:
            print(f"❌ ASR Error: {asr_response.text}")
            return
        
        # 2. Dialog - Обработка диалога
        print("\n2. Dialog (Conversation)")
        print("-" * 30)
        
        dialog_response = requests.post(
            'http://localhost:8003/dialog',
            json={
                'session_id': 'pipeline-test-123',
                'user_message': recognized_text
            }
        )
        
        if dialog_response.status_code == 200:
            dialog_result = dialog_response.json()
            assistant_message = dialog_result['assistant_message']
            intent = dialog_result['intent']
            print(f"✅ Dialog: '{assistant_message}'")
            print(f"   Intent: {intent}")
        else:
            print(f"❌ Dialog Error: {dialog_response.text}")
            return
        
        # 3. TTS - Синтез речи
        print("\n3. TTS (Speech Synthesis)")
        print("-" * 30)
        
        tts_response = requests.post(
            'http://localhost:8002/synthesize',
            json={
                'text': assistant_message,
                'voice': 'alloy',
                'format': 'mp3'
            }
        )
        
        if tts_response.status_code == 200:
            tts_result = tts_response.json()
            audio_url = tts_result['audio_url']
            duration = tts_result['duration']
            print(f"✅ TTS: {audio_url}")
            print(f"   Duration: {duration:.2f}s")
        else:
            print(f"❌ TTS Error: {tts_response.text}")
            return
        
        # 4. Итоговый результат
        print("\n4. Pipeline Summary")
        print("-" * 30)
        print(f"🎤 Input: Audio file (test-audio.wav)")
        print(f"📝 Recognized: '{recognized_text}'")
        print(f"🤖 Response: '{assistant_message}'")
        print(f"🔊 Output: {audio_url} ({duration:.2f}s)")
        print(f"🎯 Intent: {intent}")
        
        print("\n🎉 Full pipeline test completed successfully!")
        
    except Exception as e:
        print(f"❌ Pipeline Error: {e}")

if __name__ == "__main__":
    test_full_pipeline()
