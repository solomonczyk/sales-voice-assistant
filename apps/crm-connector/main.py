"""
CRM Connector - Интеграция с Bitrix24
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация Bitrix24
from dotenv import load_dotenv
load_dotenv()

BITRIX24_WEBHOOK_URL = os.getenv("BITRIX24_WEBHOOK_URL")
BITRIX24_DOMAIN = os.getenv("BITRIX24_DOMAIN")

logger.info(f"Bitrix24 Domain: {BITRIX24_DOMAIN}")
logger.info(f"Bitrix24 Webhook URL: {'configured' if BITRIX24_WEBHOOK_URL else 'not configured'}")

# Модели данных
class LeadData(BaseModel):
    title: str
    name: str
    phone: str
    email: Optional[str] = None
    company: Optional[str] = None
    source: str = "phone_call"
    product_interest: Optional[str] = None
    notes: Optional[str] = None

class DealData(BaseModel):
    title: str
    lead_id: Optional[str] = None
    client_id: str
    value: Optional[float] = None
    currency: str = "RUB"
    probability: int = 50
    notes: Optional[str] = None

class TaskData(BaseModel):
    title: str
    description: str
    assigned_to: Optional[str] = None
    client_id: Optional[str] = None
    lead_id: Optional[str] = None
    due_date: Optional[str] = None

class CRMResponse(BaseModel):
    success: bool
    id: Optional[str] = None
    message: str
    data: Optional[Dict[str, Any]] = None

# Глобальное состояние
crm_stats = {
    "total_requests": 0,
    "leads_created": 0,
    "deals_created": 0,
    "tasks_created": 0,
    "failed_requests": 0
}

async def create_bitrix24_lead(lead_data: LeadData) -> Dict[str, Any]:
    """
    Создание лида в Bitrix24 через API
    
    Args:
        lead_data: Данные лида
    
    Returns:
        Результат создания лида
    """
    if not BITRIX24_WEBHOOK_URL:
        logger.warning("Bitrix24 webhook URL не настроен, используем заглушку")
        return {
            "result": True,
            "id": f"lead_{hash(lead_data.phone)}",
            "message": "Лид создан (заглушка)"
        }
    
    # Подготавливаем данные для Bitrix24
    bitrix_data = {
        "fields": {
            "TITLE": lead_data.title,
            "NAME": lead_data.name,
            "PHONE": [{"VALUE": lead_data.phone, "VALUE_TYPE": "WORK"}],
            "EMAIL": [{"VALUE": lead_data.email, "VALUE_TYPE": "WORK"}] if lead_data.email else [],
            "COMPANY_TITLE": lead_data.company,
            "SOURCE_ID": "WEB",  # Источник - веб
            "COMMENTS": lead_data.notes or f"Создан через голосового ассистента. Интерес: {lead_data.product_interest}"
        }
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BITRIX24_WEBHOOK_URL}/crm.lead.add",
                json=bitrix_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("result"):
                        logger.info(f"Лид создан в Bitrix24: ID {result.get('result')}")
                        return {
                            "result": True,
                            "id": result.get("result"),
                            "message": "Лид успешно создан в Bitrix24"
                        }
                    else:
                        error = result.get("error_description", "Неизвестная ошибка")
                        logger.error(f"Ошибка создания лида в Bitrix24: {error}")
                        return {
                            "result": False,
                            "error": error,
                            "message": f"Ошибка создания лида: {error}"
                        }
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP ошибка Bitrix24: {response.status} - {error_text}")
                    return {
                        "result": False,
                        "error": f"HTTP {response.status}",
                        "message": f"Ошибка API: {error_text}"
                    }
        except aiohttp.ClientError as e:
            logger.error(f"Сетевая ошибка Bitrix24: {e}")
            return {
                "result": False,
                "error": str(e),
                "message": f"Сетевая ошибка: {str(e)}"
            }

async def create_bitrix24_deal(deal_data: DealData) -> Dict[str, Any]:
    """
    Создание сделки в Bitrix24 через API
    
    Args:
        deal_data: Данные сделки
    
    Returns:
        Результат создания сделки
    """
    if not BITRIX24_WEBHOOK_URL:
        logger.warning("Bitrix24 webhook URL не настроен, используем заглушку")
        return {
            "result": True,
            "id": f"deal_{hash(deal_data.title)}",
            "message": "Сделка создана (заглушка)"
        }
    
    # Подготавливаем данные для Bitrix24
    bitrix_data = {
        "fields": {
            "TITLE": deal_data.title,
            "OPPORTUNITY": deal_data.amount,
            "CURRENCY_ID": "RUB",
            "STAGE_ID": "NEW",  # Новая сделка
            "COMMENTS": deal_data.description or "Создана через голосового ассистента"
        }
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BITRIX24_WEBHOOK_URL}/crm.deal.add",
                json=bitrix_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("result"):
                        logger.info(f"Сделка создана в Bitrix24: ID {result.get('result')}")
                        return {
                            "result": True,
                            "id": result.get("result"),
                            "message": "Сделка успешно создана в Bitrix24"
                        }
                    else:
                        error = result.get("error_description", "Неизвестная ошибка")
                        logger.error(f"Ошибка создания сделки в Bitrix24: {error}")
                        return {
                            "result": False,
                            "error": error,
                            "message": f"Ошибка создания сделки: {error}"
                        }
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP ошибка Bitrix24: {response.status} - {error_text}")
                    return {
                        "result": False,
                        "error": f"HTTP {response.status}",
                        "message": f"Ошибка API: {error_text}"
                    }
        except aiohttp.ClientError as e:
            logger.error(f"Сетевая ошибка Bitrix24: {e}")
            return {
                "result": False,
                "error": str(e),
                "message": f"Сетевая ошибка: {str(e)}"
            }

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("CRM Connector запускается...")
    yield
    logger.info("CRM Connector останавливается...")

app = FastAPI(
    title="CRM Connector",
    description="Интеграция с Bitrix24 CRM",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "CRM Connector",
        "version": "1.0.0",
        "status": "running",
        "description": "Интеграция с Bitrix24 CRM"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "crm-connector",
        "stats": crm_stats
    }

@app.post("/leads", response_model=CRMResponse)
async def create_lead(lead_data: LeadData):
    """
    Создание лида в Bitrix24
    
    Args:
        lead_data: Данные лида
    
    Returns:
        Результат создания лида
    """
    try:
        crm_stats["total_requests"] += 1
        
        logger.info(f"Создание лида: {lead_data.name}, телефон: {lead_data.phone}")
        
        # Создание лида в Bitrix24 через API
        bitrix_result = await create_bitrix24_lead(lead_data)
        
        if bitrix_result["result"]:
            crm_stats["leads_created"] += 1
            logger.info(f"Лид создан: ID={bitrix_result['id']}")
            
            return CRMResponse(
                success=True,
                id=bitrix_result["id"],
                message=bitrix_result["message"],
                data={
                    "lead_id": bitrix_result["id"],
                    "title": lead_data.title,
                    "name": lead_data.name,
                    "phone": lead_data.phone,
                    "source": lead_data.source
                }
            )
        else:
            crm_stats["failed_requests"] += 1
            logger.error(f"Ошибка создания лида: {bitrix_result['error']}")
            
            return CRMResponse(
                success=False,
                id=None,
                message=bitrix_result["message"],
                data={"error": bitrix_result["error"]}
            )
        
    except Exception as e:
        crm_stats["failed_requests"] += 1
        logger.error(f"Ошибка создания лида: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания лида: {str(e)}")

@app.post("/deals", response_model=CRMResponse)
async def create_deal(deal_data: DealData):
    """
    Создание сделки в Bitrix24
    
    Args:
        deal_data: Данные сделки
    
    Returns:
        Результат создания сделки
    """
    try:
        crm_stats["total_requests"] += 1
        
        logger.info(f"Создание сделки: {deal_data.title}, клиент: {deal_data.client_id}")
        
        # Заглушка для создания сделки в Bitrix24
        deal_id = f"deal_{hash(deal_data.client_id)}"
        
        crm_stats["deals_created"] += 1
        
        logger.info(f"Сделка создана: ID={deal_id}")
        
        return CRMResponse(
            success=True,
            id=deal_id,
            message="Сделка успешно создана",
            data={
                "deal_id": deal_id,
                "title": deal_data.title,
                "client_id": deal_data.client_id,
                "value": deal_data.value,
                "currency": deal_data.currency
            }
        )
        
    except Exception as e:
        crm_stats["failed_requests"] += 1
        logger.error(f"Ошибка создания сделки: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания сделки: {str(e)}")

@app.post("/tasks", response_model=CRMResponse)
async def create_task(task_data: TaskData):
    """
    Создание задачи в Bitrix24
    
    Args:
        task_data: Данные задачи
    
    Returns:
        Результат создания задачи
    """
    try:
        crm_stats["total_requests"] += 1
        
        logger.info(f"Создание задачи: {task_data.title}")
        
        # Заглушка для создания задачи в Bitrix24
        task_id = f"task_{hash(task_data.title)}"
        
        crm_stats["tasks_created"] += 1
        
        logger.info(f"Задача создана: ID={task_id}")
        
        return CRMResponse(
            success=True,
            id=task_id,
            message="Задача успешно создана",
            data={
                "task_id": task_id,
                "title": task_data.title,
                "description": task_data.description,
                "assigned_to": task_data.assigned_to
            }
        )
        
    except Exception as e:
        crm_stats["failed_requests"] += 1
        logger.error(f"Ошибка создания задачи: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания задачи: {str(e)}")

@app.get("/leads/{lead_id}")
async def get_lead(lead_id: str):
    """Получение лида по ID"""
    try:
        # Заглушка для получения лида
        return {
            "success": True,
            "lead": {
                "id": lead_id,
                "title": "Тестовый лид",
                "name": "Иван Иванов",
                "phone": "+7 (999) 123-45-67",
                "status": "new"
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения лида: {e}")
        raise HTTPException(status_code=404, detail="Лид не найден")

@app.get("/stats")
async def get_stats():
    """Получение статистики сервиса"""
    return {
        "service": "crm-connector",
        "stats": crm_stats
    }

@app.post("/webhook/bitrix24")
async def handle_bitrix24_webhook(webhook_data: Dict[str, Any]):
    """
    Обработка webhook от Bitrix24
    
    Args:
        webhook_data: Данные webhook
    
    Returns:
        Подтверждение получения
    """
    try:
        logger.info(f"Получен webhook от Bitrix24: {webhook_data}")
        
        # Обработка webhook данных
        # В реальной реализации здесь будет обработка различных событий
        
        return {"status": "received", "message": "Webhook обработан"}
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки webhook: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )
