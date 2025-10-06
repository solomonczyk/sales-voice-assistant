"""
Dialog Orchestrator - Диалоговый агент для голосового ассистента
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Модели данных
class DialogMessage(BaseModel):
    role: str  # "user" или "assistant"
    content: str
    timestamp: Optional[str] = None

class DialogContext(BaseModel):
    session_id: str
    messages: list[DialogMessage]
    state: Dict[str, Any] = {}
    intent: Optional[str] = None
    entities: Dict[str, Any] = {}

class DialogRequest(BaseModel):
    session_id: str
    user_message: str
    context: Optional[Dict[str, Any]] = None

class DialogResponse(BaseModel):
    session_id: str
    assistant_message: str
    intent: Optional[str] = None
    entities: Dict[str, Any] = {}
    confidence: float
    state: Dict[str, Any] = {}
    actions: list[str] = []

# Глобальное состояние
dialog_stats = {
    "total_dialogs": 0,
    "active_sessions": 0,
    "total_messages": 0,
    "intents_detected": 0
}

# Простые правила для MVP
DIALOG_RULES = {
    "greeting": {
        "patterns": ["привет", "здравствуйте", "добрый день", "добрый вечер"],
        "response": "Здравствуйте! Я голосовой ассистент отдела продаж. Чем могу помочь?",
        "intent": "greeting"
    },
    "product_inquiry": {
        "patterns": ["продукт", "услуга", "цена", "стоимость", "каталог"],
        "response": "Расскажите, пожалуйста, какой продукт или услуга вас интересует?",
        "intent": "product_inquiry"
    },
    "contact_info": {
        "patterns": ["контакт", "телефон", "адрес", "офис", "связаться"],
        "response": "Наши контакты: телефон +7 (999) 123-45-67, email info@company.com",
        "intent": "contact_info"
    },
    "schedule_meeting": {
        "patterns": ["встреча", "встретиться", "записаться", "время", "расписание"],
        "response": "Конечно! Когда вам удобно встретиться? У нас есть свободные слоты на завтра и послезавтра.",
        "intent": "schedule_meeting"
    },
    "goodbye": {
        "patterns": ["до свидания", "пока", "спасибо", "всего хорошего"],
        "response": "Спасибо за обращение! Хорошего дня!",
        "intent": "goodbye"
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("Dialog Orchestrator запускается...")
    yield
    logger.info("Dialog Orchestrator останавливается...")

app = FastAPI(
    title="Dialog Orchestrator",
    description="Диалоговый агент для голосового ассистента",
    version="1.0.0",
    lifespan=lifespan
)

def detect_intent_and_entities(message: str) -> tuple[Optional[str], Dict[str, Any], float]:
    """
    Простое определение намерения и сущностей
    
    Args:
        message: Сообщение пользователя
    
    Returns:
        Кортеж (intent, entities, confidence)
    """
    message_lower = message.lower()
    
    # Поиск подходящего правила
    for rule_name, rule in DIALOG_RULES.items():
        for pattern in rule["patterns"]:
            if pattern in message_lower:
                # Простое извлечение сущностей
                entities = {}
                if "телефон" in message_lower:
                    entities["phone_requested"] = True
                if "email" in message_lower:
                    entities["email_requested"] = True
                if "встреча" in message_lower or "время" in message_lower:
                    entities["meeting_requested"] = True
                
                return rule["intent"], entities, 0.9
    
    # Если ничего не найдено
    return "unknown", {}, 0.3

def generate_response(intent: str, entities: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Генерация ответа на основе намерения и контекста
    
    Args:
        intent: Определенное намерение
        entities: Извлеченные сущности
        context: Контекст диалога
    
    Returns:
        Ответ ассистента
    """
    if intent == "greeting":
        return "Здравствуйте! Я голосовой ассистент отдела продаж. Чем могу помочь?"
    
    elif intent == "product_inquiry":
        return "Расскажите, пожалуйста, какой продукт или услуга вас интересует? Я помогу подобрать оптимальное решение."
    
    elif intent == "contact_info":
        return "Наши контакты: телефон +7 (999) 123-45-67, email info@company.com, адрес: г. Москва, ул. Примерная, д. 1"
    
    elif intent == "schedule_meeting":
        return "Конечно! Когда вам удобно встретиться? У нас есть свободные слоты на завтра и послезавтра. Какой день предпочтете?"
    
    elif intent == "goodbye":
        return "Спасибо за обращение! Хорошего дня! Если возникнут вопросы, обращайтесь!"
    
    else:
        return "Извините, я не совсем понял ваш вопрос. Можете переформулировать? Я помогу с информацией о продуктах, контактах или записи на встречу."

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "Dialog Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "description": "Диалоговый агент для голосового ассистента"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "dialog-orchestrator",
        "stats": dialog_stats
    }

@app.post("/dialog", response_model=DialogResponse)
async def process_dialog(request: DialogRequest):
    """
    Обработка диалогового сообщения
    
    Args:
        request: Запрос на обработку диалога
    
    Returns:
        Ответ ассистента с контекстом
    """
    try:
        dialog_stats["total_dialogs"] += 1
        dialog_stats["total_messages"] += 1
        
        logger.info(f"Обработка диалога: session_id={request.session_id}, message='{request.user_message[:50]}...'")
        
        # Определение намерения и сущностей
        intent, entities, confidence = detect_intent_and_entities(request.user_message)
        
        if intent != "unknown":
            dialog_stats["intents_detected"] += 1
        
        # Генерация ответа
        context = request.context or {}
        assistant_message = generate_response(intent, entities, context)
        
        # Определение действий
        actions = []
        if intent == "product_inquiry":
            actions.append("create_lead")
        elif intent == "schedule_meeting":
            actions.append("create_task")
        elif intent == "contact_info":
            actions.append("log_interaction")
        
        logger.info(f"Ответ сгенерирован: intent={intent}, confidence={confidence}")
        
        return DialogResponse(
            session_id=request.session_id,
            assistant_message=assistant_message,
            intent=intent,
            entities=entities,
            confidence=confidence,
            state=context,
            actions=actions
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки диалога: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки диалога: {str(e)}")

@app.get("/intents")
async def get_available_intents():
    """Получение списка доступных намерений"""
    return {
        "intents": list(DIALOG_RULES.keys()),
        "rules": DIALOG_RULES
    }

@app.get("/stats")
async def get_stats():
    """Получение статистики сервиса"""
    return {
        "service": "dialog-orchestrator",
        "stats": dialog_stats,
        "available_intents": len(DIALOG_RULES)
    }

@app.post("/session/{session_id}/end")
async def end_session(session_id: str):
    """Завершение диалоговой сессии"""
    try:
        logger.info(f"Завершение сессии: {session_id}")
        # Здесь можно добавить логику сохранения сессии
        return {"status": "session_ended", "session_id": session_id}
    except Exception as e:
        logger.error(f"Ошибка завершения сессии: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
