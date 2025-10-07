#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощенный тест MVP (только Python сервисы)
"""

import asyncio
import aiohttp
import json
import time
import sys

# Устанавливаем UTF-8 кодировку для вывода
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Конфигурация Python сервисов
SERVICES = {
    "asr-service": "http://localhost:8001", 
    "tts-service": "http://localhost:8002",
    "dialog-orchestrator": "http://localhost:8003",
    "crm-connector": "http://localhost:8005"
}

async def check_service_health(session: aiohttp.ClientSession, service_name: str, url: str):
    """Проверка здоровья сервиса"""
    try:
        async with session.get(f"{url}/health", timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "service": service_name,
                    "status": "healthy",
                    "url": url,
                    "data": data
                }
            else:
                return {
                    "service": service_name,
                    "status": "unhealthy",
                    "url": url,
                    "error": f"HTTP {response.status}"
                }
    except Exception as e:
        return {
            "service": service_name,
            "status": "unreachable",
            "url": url,
            "error": str(e)
        }

async def test_asr_service(session: aiohttp.ClientSession):
    """Тест ASR сервиса"""
    try:
        # Создаем тестовые аудио данные
        test_audio = b"fake_audio_data_for_testing"
        
        data = aiohttp.FormData()
        data.add_field('audio', test_audio, filename='test.wav', content_type='audio/wav')
        data.add_field('language', 'ru-RU')
        
        async with session.post(f"{SERVICES['asr-service']}/recognize", data=data, timeout=10) as response:
            if response.status == 200:
                result = await response.json()
                return {"status": "success", "result": result}
            else:
                return {"status": "error", "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def test_tts_service(session: aiohttp.ClientSession):
    """Тест TTS сервиса"""
    try:
        payload = {
            "text": "Привет! Это тестовый синтез речи.",
            "voice": "alena",
            "format": "wav"
        }
        
        async with session.post(f"{SERVICES['tts-service']}/synthesize", json=payload, timeout=10) as response:
            if response.status == 200:
                result = await response.json()
                return {"status": "success", "result": result}
            else:
                return {"status": "error", "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def test_dialog_orchestrator(session: aiohttp.ClientSession):
    """Тест Dialog Orchestrator"""
    try:
        payload = {
            "session_id": "test-session-123",
            "user_message": "Привет! Расскажи о ваших продуктах"
        }
        
        async with session.post(f"{SERVICES['dialog-orchestrator']}/dialog", json=payload, timeout=10) as response:
            if response.status == 200:
                result = await response.json()
                return {"status": "success", "result": result}
            else:
                return {"status": "error", "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def test_crm_connector(session: aiohttp.ClientSession):
    """Тест CRM Connector"""
    try:
        payload = {
            "title": "Тестовый лид",
            "name": "Иван Иванов",
            "phone": "+7 (999) 123-45-67",
            "source": "phone_call",
            "product_interest": "premium_package"
        }
        
        async with session.post(f"{SERVICES['crm-connector']}/leads", json=payload, timeout=10) as response:
            if response.status == 200:
                result = await response.json()
                return {"status": "success", "result": result}
            else:
                return {"status": "error", "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def main():
    """Основная функция тестирования"""
    print("Тестирование MVP Sales Voice Assistant (Python сервисы)")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 1. Проверка здоровья сервисов
        print("\n1️⃣ Проверка здоровья сервисов:")
        health_results = []
        
        for service_name, url in SERVICES.items():
            result = await check_service_health(session, service_name, url)
            health_results.append(result)
            
            status_icon = "✅" if result["status"] == "healthy" else "❌"
            print(f"  {status_icon} {service_name}: {result['status']}")
            if result["status"] != "healthy":
                print(f"     Ошибка: {result.get('error', 'Unknown')}")
        
        # 2. Тестирование функциональности
        print("\n2️⃣ Тестирование функциональности:")
        
        # ASR тест
        print("  🎤 Тест ASR Service...")
        asr_result = await test_asr_service(session)
        if asr_result["status"] == "success":
            print(f"     ✅ ASR: {asr_result['result']['text']}")
        else:
            print(f"     ❌ ASR: {asr_result['error']}")
        
        # TTS тест
        print("  🔊 Тест TTS Service...")
        tts_result = await test_tts_service(session)
        if tts_result["status"] == "success":
            print(f"     ✅ TTS: аудио {tts_result['result']['duration']:.2f}с")
        else:
            print(f"     ❌ TTS: {tts_result['error']}")
        
        # Dialog тест
        print("  🤖 Тест Dialog Orchestrator...")
        dialog_result = await test_dialog_orchestrator(session)
        if dialog_result["status"] == "success":
            print(f"     ✅ Dialog: {dialog_result['result']['assistant_message']}")
        else:
            print(f"     ❌ Dialog: {dialog_result['error']}")
        
        # CRM тест
        print("  📊 Тест CRM Connector...")
        crm_result = await test_crm_connector(session)
        if crm_result["status"] == "success":
            print(f"     ✅ CRM: лид создан (ID: {crm_result['result']['id']})")
        else:
            print(f"     ❌ CRM: {crm_result['error']}")
        
        # 3. Итоговая статистика
        print("\n3️⃣ Итоговая статистика:")
        healthy_services = sum(1 for r in health_results if r["status"] == "healthy")
        total_services = len(health_results)
        
        functional_tests = [asr_result, tts_result, dialog_result, crm_result]
        successful_tests = sum(1 for r in functional_tests if r["status"] == "success")
        total_tests = len(functional_tests)
        
        print(f"  📊 Сервисы: {healthy_services}/{total_services} работают")
        print(f"  🧪 Тесты: {successful_tests}/{total_tests} прошли успешно")
        
        if healthy_services == total_services and successful_tests == total_tests:
            print("\n🎉 MVP Python сервисы полностью функциональны!")
        elif healthy_services == total_services:
            print("\n⚠️  Все сервисы работают, но есть проблемы с функциональностью")
        else:
            print("\n❌ Есть проблемы с сервисами")
        
        print("\n📋 Доступные endpoints:")
        for service_name, url in SERVICES.items():
            print(f"  {service_name}: {url}")

if __name__ == "__main__":
    asyncio.run(main())
