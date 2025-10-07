#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создание тестового аудио файла для тестирования OpenAI Whisper
"""

import wave
import struct
import math
import os

def create_test_audio():
    """Создает простой тестовый WAV файл"""
    
    # Параметры аудио
    sample_rate = 16000  # 16 kHz
    duration = 2.0  # 2 секунды
    frequency = 440  # A4 нота (440 Hz)
    
    # Создаем синусоидальную волну
    samples = []
    for i in range(int(sample_rate * duration)):
        # Простая синусоида
        sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        samples.append(sample)
    
    # Сохраняем как WAV файл
    filename = "test-audio.wav"
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Моно
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Записываем аудио данные
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"Created test audio file: {filename}")
    print(f"File size: {os.path.getsize(filename)} bytes")
    print(f"Duration: {duration} seconds")
    print(f"Sample rate: {sample_rate} Hz")
    
    return filename

if __name__ == "__main__":
    create_test_audio()
