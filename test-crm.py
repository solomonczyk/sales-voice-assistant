#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест CRM Connector с Bitrix24 интеграцией
"""

import requests
import sys

# Устанавливаем UTF-8 кодировку для вывода
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def test_crm():
    """Тестируем CRM Connector"""
    print("Testing CRM Connector with Bitrix24 integration...")
    
    try:
        # Тест создания лида
        print("\n1. Testing Lead Creation")
        print("-" * 30)
        
        lead_data = {
            "title": "Новый лид от голосового ассистента",
            "name": "Иван Петров",
            "phone": "+79991234567",
            "email": "ivan.petrov@example.com",
            "company": "ООО Тестовая компания",
            "source": "phone_call",
            "product_interest": "Консультация по продуктам",
            "notes": "Клиент заинтересован в наших услугах"
        }
        
        response = requests.post(
            'http://localhost:8005/leads',
            json=lead_data
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Lead created: {result['message']}")
            print(f"   Lead ID: {result['id']}")
            print(f"   Data: {result['data']}")
        else:
            print(f"❌ Lead creation error: {response.text}")
        
        # Тест создания сделки
        print("\n2. Testing Deal Creation")
        print("-" * 30)
        
        deal_data = {
            "title": "Сделка от голосового ассистента",
            "value": 50000,
            "client_id": "123",
            "notes": "Потенциальная сделка с новым клиентом"
        }
        
        response = requests.post(
            'http://localhost:8005/deals',
            json=deal_data
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Deal created: {result['message']}")
            print(f"   Deal ID: {result['id']}")
            print(f"   Data: {result['data']}")
        else:
            print(f"❌ Deal creation error: {response.text}")
        
        # Тест статистики
        print("\n3. Testing CRM Statistics")
        print("-" * 30)
        
        response = requests.get('http://localhost:8005/stats')
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ CRM Stats: {result['stats']}")
        else:
            print(f"❌ Stats error: {response.text}")
            
    except Exception as e:
        print(f"❌ CRM Test Error: {e}")

if __name__ == "__main__":
    test_crm()
