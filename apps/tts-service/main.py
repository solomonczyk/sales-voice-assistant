"""
TTS Service - Синтез речи с Yandex SpeechKit
"""

import asyncio
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from typing import Optional, List

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация OpenAI TTS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"

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

async def synthesize_with_openai(text: str, voice: str = "alloy", format: str = "wav") -> bytes:
    """
    Синтез речи через OpenAI TTS
    
    Args:
        text: Текст для синтеза
        voice: Голос для синтеза (alloy, echo, fable, onyx, nova, shimmer)
        format: Формат аудио (mp3, opus, aac, flac)
    
    Returns:
        Аудио данные в байтах
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API ключ не настроен")
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "tts-1",
        "input": text,
        "voice": voice,
        "response_format": format
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                OPENAI_TTS_URL,
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    return audio_data
                else:
                    error_text = await response.text()
                    logger.error(f"OpenAI TTS API error: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"OpenAI TTS API error: {error_text}"
                    )
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

# Доступные голоса OpenAI
AVAILABLE_VOICES = [
    VoiceInfo(id="alloy", name="Alloy", language="en-US", gender="neutral", sample_rate=24000),
    VoiceInfo(id="echo", name="Echo", language="en-US", gender="male", sample_rate=24000),
    VoiceInfo(id="fable", name="Fable", language="en-US", gender="male", sample_rate=24000),
    VoiceInfo(id="onyx", name="Onyx", language="en-US", gender="male", sample_rate=24000),
    VoiceInfo(id="nova", name="Nova", language="en-US", gender="female", sample_rate=24000),
    VoiceInfo(id="shimmer", name="Shimmer", language="en-US", gender="female", sample_rate=24000)
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

@app.get("/voices", response_model=List[VoiceInfo])
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
        
        # Синтез через OpenAI TTS
        if OPENAI_API_KEY:
            try:
                audio_data = await synthesize_with_openai(
                    request.text, 
                    request.voice, 
                    request.format
                )
                
                # Сохраняем аудио во временный файл
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{request.format}") as temp_file:
                    temp_file.write(audio_data)
                    temp_file_path = temp_file.name
                
                # Примерная длительность (1 символ = 0.1 секунды)
                audio_duration = len(request.text) * 0.1
                audio_url = f"/audio/synthesized_{hash(request.text)}.{request.format}"
                
                logger.info(f"OpenAI TTS синтез завершен: {len(audio_data)} байт аудио")
            except Exception as e:
                logger.error(f"Ошибка OpenAI TTS: {e}")
                # Fallback к заглушке
                audio_duration = len(request.text) * 0.1
                audio_url = f"/audio/synthesized_{hash(request.text)}.wav"
        else:
            # Заглушка для синтеза (если нет API ключа)
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
