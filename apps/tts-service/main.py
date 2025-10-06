"""
TTS Service - Синтез речи с Yandex SpeechKit
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Модели данных
class SynthesisRequest(BaseModel):
    text: str
    voice: str = "alena"
    format: str = "wav"
    sample_rate: int = 16000
    speed: float = 1.0
    pitch: float = 1.0

class SynthesisResponse(BaseModel):
    audio_url: str
    duration: float
    text_length: int
    voice: str

class VoiceInfo(BaseModel):
    id: str
    name: str
    language: str
    gender: str
    sample_rate: int

# Глобальное состояние
synthesis_stats = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "total_text_length": 0,
    "total_audio_duration": 0.0
}

# Доступные голоса
AVAILABLE_VOICES = [
    VoiceInfo(id="alena", name="Алена", language="ru-RU", gender="female", sample_rate=16000),
    VoiceInfo(id="filipp", name="Филипп", language="ru-RU", gender="male", sample_rate=16000),
    VoiceInfo(id="jane", name="Джейн", language="en-US", gender="female", sample_rate=16000),
    VoiceInfo(id="john", name="Джон", language="en-US", gender="male", sample_rate=16000),
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("TTS Service запускается...")
    yield
    logger.info("TTS Service останавливается...")

app = FastAPI(
    title="TTS Service",
    description="Сервис синтеза речи с Yandex SpeechKit",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "TTS Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Сервис синтеза речи"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "tts-service",
        "stats": synthesis_stats
    }

@app.get("/voices", response_model=list[VoiceInfo])
async def get_voices():
    """Получение списка доступных голосов"""
    return AVAILABLE_VOICES

@app.post("/synthesize", response_model=SynthesisResponse)
async def synthesize_speech(request: SynthesisRequest):
    """
    Синтез речи из текста
    
    Args:
        request: Запрос на синтез речи
    
    Returns:
        Информация о синтезированном аудио
    """
    try:
        synthesis_stats["total_requests"] += 1
        synthesis_stats["total_text_length"] += len(request.text)
        
        # Проверка голоса
        voice = next((v for v in AVAILABLE_VOICES if v.id == request.voice), None)
        if not voice:
            raise HTTPException(status_code=400, detail=f"Голос '{request.voice}' не найден")
        
        logger.info(f"Синтез речи: '{request.text[:50]}...' голосом {voice.name}")
        
        # Заглушка для синтеза
        # В реальной реализации здесь будет интеграция с Yandex SpeechKit
        audio_duration = len(request.text) * 0.1  # Примерная длительность
        audio_url = f"/audio/synthesized_{hash(request.text)}.wav"
        
        synthesis_stats["successful_requests"] += 1
        synthesis_stats["total_audio_duration"] += audio_duration
        
        logger.info(f"Синтез завершен: {audio_duration:.2f}с аудио")
        
        return SynthesisResponse(
            audio_url=audio_url,
            duration=audio_duration,
            text_length=len(request.text),
            voice=request.voice
        )
        
    except Exception as e:
        synthesis_stats["failed_requests"] += 1
        logger.error(f"Ошибка синтеза: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка синтеза: {str(e)}")

@app.post("/synthesize/stream")
async def synthesize_stream(request: SynthesisRequest):
    """
    Потоковый синтез речи
    
    Args:
        request: Запрос на синтез речи
    
    Returns:
        Поток аудио данных
    """
    try:
        logger.info(f"Потоковый синтез: '{request.text[:50]}...'")
        
        # Заглушка для потокового синтеза
        # В реальной реализации здесь будет генерация аудио чанков
        def generate_audio():
            # Генерация заглушки аудио
            for i in range(10):
                yield b"fake_audio_chunk_" + str(i).encode() + b"\n"
        
        return StreamingResponse(
            generate_audio(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=synthesized_{request.voice}.wav"
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка потокового синтеза: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Получение статистики сервиса"""
    return {
        "service": "tts-service",
        "stats": synthesis_stats,
        "available_voices": len(AVAILABLE_VOICES)
    }

@app.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    """
    Получение синтезированного аудио файла
    
    Args:
        audio_id: ID аудио файла
    
    Returns:
        Аудио файл
    """
    try:
        # Заглушка для получения аудио
        # В реальной реализации здесь будет возврат реального аудио файла
        fake_audio_data = b"fake_audio_data_for_" + audio_id.encode()
        
        return StreamingResponse(
            iter([fake_audio_data]),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename={audio_id}.wav"
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения аудио: {e}")
        raise HTTPException(status_code=404, detail="Аудио файл не найден")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
