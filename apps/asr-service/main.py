"""
ASR Service - Распознавание речи с Yandex SpeechKit
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Модели данных
class RecognitionRequest(BaseModel):
    language: str = "ru-RU"
    format: str = "wav"
    sample_rate: int = 16000
    channels: int = 1

class RecognitionResponse(BaseModel):
    text: str
    confidence: float
    duration: float

class RecognitionStatus(BaseModel):
    status: str
    message: Optional[str] = None

# Глобальное состояние
recognition_stats = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "total_audio_duration": 0.0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("ASR Service запускается...")
    yield
    logger.info("ASR Service останавливается...")

app = FastAPI(
    title="ASR Service",
    description="Сервис распознавания речи с Yandex SpeechKit",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "ASR Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Сервис распознавания речи"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "asr-service",
        "stats": recognition_stats
    }

@app.post("/recognize", response_model=RecognitionResponse)
async def recognize_speech(
    audio: UploadFile = File(...),
    language: str = "ru-RU",
    format: str = "wav"
):
    """
    Распознавание речи из аудио файла
    
    Args:
        audio: Аудио файл для распознавания
        language: Язык распознавания (ru-RU, en-US)
        format: Формат аудио (wav, mp3, ogg)
    
    Returns:
        Распознанный текст с оценкой уверенности
    """
    try:
        recognition_stats["total_requests"] += 1
        
        # Проверка типа файла
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Файл должен быть аудио")
        
        # Чтение аудио данных
        audio_data = await audio.read()
        audio_size = len(audio_data)
        
        logger.info(f"Получен аудио файл: {audio.filename}, размер: {audio_size} байт")
        
        # Заглушка для распознавания
        # В реальной реализации здесь будет интеграция с Yandex SpeechKit
        recognized_text = "Привет! Это тестовое распознавание речи."
        confidence = 0.95
        duration = audio_size / 16000  # Примерная длительность
        
        recognition_stats["successful_requests"] += 1
        recognition_stats["total_audio_duration"] += duration
        
        logger.info(f"Распознавание завершено: '{recognized_text}' (уверенность: {confidence})")
        
        return RecognitionResponse(
            text=recognized_text,
            confidence=confidence,
            duration=duration
        )
        
    except Exception as e:
        recognition_stats["failed_requests"] += 1
        logger.error(f"Ошибка распознавания: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка распознавания: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Получение статистики сервиса"""
    return {
        "service": "asr-service",
        "stats": recognition_stats,
        "uptime": "running"
    }

@app.post("/recognize/stream")
async def recognize_stream(audio_data: bytes = File(...)):
    """
    Потоковое распознавание речи
    
    Args:
        audio_data: Поток аудио данных
    
    Returns:
        Частичные результаты распознавания
    """
    try:
        # Заглушка для потокового распознавания
        # В реальной реализации здесь будет WebSocket или Server-Sent Events
        return {
            "partial_text": "Частичный результат...",
            "is_final": False,
            "confidence": 0.8
        }
    except Exception as e:
        logger.error(f"Ошибка потокового распознавания: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
