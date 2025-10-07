"""
ASR Service - Распознавание речи с Yandex SpeechKit
"""

import asyncio
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from typing import Optional

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация OpenAI Whisper
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"

logger.info(f"OpenAI API Key loaded: {OPENAI_API_KEY[:10] + '...' if OPENAI_API_KEY else 'None'}")

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

async def recognize_with_openai(audio_data: bytes, language: str = "ru") -> dict:
    """
    Распознавание речи через OpenAI Whisper
    
    Args:
        audio_data: Аудио данные в байтах
        language: Язык распознавания (ru, en, etc.)
    
    Returns:
        Результат распознавания от OpenAI API
    """
    if not OPENAI_API_KEY:
        logger.error(f"OpenAI API ключ не настроен: {OPENAI_API_KEY}")
        raise HTTPException(status_code=500, detail="OpenAI API ключ не настроен")
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    # Подготавливаем данные для multipart/form-data
    data = aiohttp.FormData()
    data.add_field('file', audio_data, filename='audio.wav', content_type='audio/wav')
    data.add_field('model', 'whisper-1')
    data.add_field('language', language)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                OPENAI_WHISPER_URL,
                headers=headers,
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"OpenAI Whisper API error: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"OpenAI Whisper API error: {error_text}"
                    )
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("ASR Service запускается...")
    
    # Проверка конфигурации
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY не настроен - будет использоваться заглушка")
    
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
        if audio.content_type and not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Файл должен быть аудио")
        
        # Чтение аудио данных
        audio_data = await audio.read()
        audio_size = len(audio_data)
        
        logger.info(f"Получен аудио файл: {audio.filename}, размер: {audio_size} байт, content_type: {audio.content_type}")
        
        # Распознавание через OpenAI Whisper
        if OPENAI_API_KEY:
            try:
                logger.info(f"Вызываем OpenAI Whisper с языком: {language}")
                openai_result = await recognize_with_openai(audio_data, language)
                recognized_text = openai_result.get("text", "")
                confidence = 0.9  # OpenAI не возвращает confidence, используем стандартное значение
                duration = audio_size / 16000  # Примерная длительность
                
                logger.info(f"OpenAI Whisper результат: '{recognized_text}'")
            except Exception as e:
                logger.error(f"Ошибка OpenAI Whisper: {e}", exc_info=True)
                # Fallback к заглушке
                recognized_text = "Ошибка распознавания через OpenAI Whisper"
                confidence = 0.1
                duration = audio_size / 16000
        else:
            # Заглушка для распознавания (если нет API ключа)
            logger.warning("OpenAI API ключ не настроен, используем заглушку")
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
