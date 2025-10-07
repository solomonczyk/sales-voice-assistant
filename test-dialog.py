#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест Dialog Orchestrator с OpenAI GPT
"""

import requests
import sys

# Устанавливаем UTF-8 кодировку для вывода
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def test_dialog():
    """Тестируем Dialog Orchestrator"""
    print("Testing Dialog Orchestrator with OpenAI GPT...")
    
    try:
        # Тестовые сообщения
        test_messages = [
            "Привет! Расскажи мне о ваших продуктах.",
            "Какие у вас есть услуги?",
            "Как с вами связаться?",
            "Спасибо за информацию!"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Test {i} ---")
            print(f"User: {message}")
            
            response = requests.post(
                'http://localhost:8003/dialog',
                json={
                    'session_id': f'test-session-{i}',
                    'user_message': message
                }
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Assistant: {result['assistant_message']}")
                print(f"Intent: {result['intent']}")
                print(f"Confidence: {result['confidence']}")
                print(f"Actions: {result['actions']}")
            else:
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_dialog()
