"""
Утилиты для Sales Voice Assistant
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import phonenumbers
from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext
from phonenumbers import NumberParseException

from .config import get_settings

# Настройки для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки для шифрования
_fernet_key: Optional[bytes] = None


def get_fernet_key() -> bytes:
    """Получить ключ для шифрования"""
    global _fernet_key
    if _fernet_key is None:
        settings = get_settings()
        # В продакшене ключ должен быть в переменных окружения
        key = settings.jwt_secret_key.encode()[:32].ljust(32, b'0')
        _fernet_key = Fernet.generate_key() if len(key) < 32 else key
    return _fernet_key


def validate_phone(phone: str, country_code: str = "RU") -> bool:
    """
    Валидация номера телефона
    
    Args:
        phone: Номер телефона
        country_code: Код страны по умолчанию
        
    Returns:
        True если номер валидный, иначе False
    """
    try:
        parsed_number = phonenumbers.parse(phone, country_code)
        return phonenumbers.is_valid_number(parsed_number)
    except NumberParseException:
        return False


def format_phone(phone: str, country_code: str = "RU", format_type: str = "INTERNATIONAL") -> str:
    """
    Форматирование номера телефона
    
    Args:
        phone: Номер телефона
        country_code: Код страны по умолчанию
        format_type: Тип форматирования (INTERNATIONAL, NATIONAL, E164)
        
    Returns:
        Отформатированный номер телефона
    """
    try:
        parsed_number = phonenumbers.parse(phone, country_code)
        format_map = {
            "INTERNATIONAL": phonenumbers.PhoneNumberFormat.INTERNATIONAL,
            "NATIONAL": phonenumbers.PhoneNumberFormat.NATIONAL,
            "E164": phonenumbers.PhoneNumberFormat.E164,
        }
        return phonenumbers.format_number(parsed_number, format_map.get(format_type, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
    except NumberParseException:
        return phone


def generate_session_id() -> str:
    """Генерация уникального ID сессии"""
    return str(uuid.uuid4())


def generate_api_key() -> str:
    """Генерация API ключа"""
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """
    Хеширование пароля
    
    Args:
        password: Пароль для хеширования
        
    Returns:
        Хешированный пароль
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка пароля
    
    Args:
        plain_password: Обычный пароль
        hashed_password: Хешированный пароль
        
    Returns:
        True если пароль верный, иначе False
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Создание JWT токена
    
    Args:
        data: Данные для включения в токен
        expires_delta: Время жизни токена
        
    Returns:
        JWT токен
    """
    settings = get_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Проверка JWT токена
    
    Args:
        token: JWT токен
        
    Returns:
        Данные из токена или None если токен невалидный
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def encrypt_data(data: str) -> str:
    """
    Шифрование данных
    
    Args:
        data: Данные для шифрования
        
    Returns:
        Зашифрованные данные в base64
    """
    fernet = Fernet(get_fernet_key())
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data.decode()


def decrypt_data(encrypted_data: str) -> str:
    """
    Расшифровка данных
    
    Args:
        encrypted_data: Зашифрованные данные в base64
        
    Returns:
        Расшифрованные данные
    """
    fernet = Fernet(get_fernet_key())
    decrypted_data = fernet.decrypt(encrypted_data.encode())
    return decrypted_data.decode()


def generate_hash(data: str, algorithm: str = "sha256") -> str:
    """
    Генерация хеша от данных
    
    Args:
        data: Данные для хеширования
        algorithm: Алгоритм хеширования
        
    Returns:
        Хеш в hex формате
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data.encode())
    return hash_obj.hexdigest()


def mask_phone(phone: str) -> str:
    """
    Маскирование номера телефона для логирования
    
    Args:
        phone: Номер телефона
        
    Returns:
        Замаскированный номер
    """
    if len(phone) < 4:
        return "*" * len(phone)
    
    return phone[:2] + "*" * (len(phone) - 4) + phone[-2:]


def mask_email(email: str) -> str:
    """
    Маскирование email для логирования
    
    Args:
        email: Email адрес
        
    Returns:
        Замаскированный email
    """
    if "@" not in email:
        return email
    
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def sanitize_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Очистка данных от чувствительной информации для логирования
    
    Args:
        data: Данные для очистки
        
    Returns:
        Очищенные данные
    """
    sensitive_fields = {
        "password", "token", "api_key", "secret", "key", "authorization",
        "cookie", "session", "credit_card", "ssn", "passport"
    }
    
    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_fields):
            sanitized[key] = "***MASKED***"
        elif isinstance(value, str):
            if "@" in value and "." in value:
                sanitized[key] = mask_email(value)
            elif any(char.isdigit() for char in value) and len(value) >= 10:
                sanitized[key] = mask_phone(value)
            else:
                sanitized[key] = value
        else:
            sanitized[key] = value
    
    return sanitized


def calculate_confidence_score(transcript: str, entities: Dict[str, Any]) -> float:
    """
    Расчет оценки уверенности на основе транскрипта и извлеченных сущностей
    
    Args:
        transcript: Транскрипт разговора
        entities: Извлеченные сущности
        
    Returns:
        Оценка уверенности от 0.0 до 1.0
    """
    if not transcript:
        return 0.0
    
    # Базовая оценка на основе длины транскрипта
    base_score = min(len(transcript) / 100, 1.0)
    
    # Бонус за извлеченные сущности
    entity_bonus = len(entities) * 0.1
    
    # Бонус за ключевые слова
    keywords = ["да", "нет", "хорошо", "понятно", "спасибо", "интересно"]
    keyword_bonus = sum(1 for keyword in keywords if keyword in transcript.lower()) * 0.05
    
    confidence = min(base_score + entity_bonus + keyword_bonus, 1.0)
    return round(confidence, 2)


def extract_phone_from_text(text: str) -> Optional[str]:
    """
    Извлечение номера телефона из текста
    
    Args:
        text: Текст для поиска номера
        
    Returns:
        Найденный номер телефона или None
    """
    import re
    
    # Паттерны для поиска номеров телефонов
    patterns = [
        r'\+7\s?\(\d{3}\)\s?\d{3}-\d{2}-\d{2}',  # +7 (XXX) XXX-XX-XX
        r'\+7\s?\d{3}\s?\d{3}\s?\d{2}\s?\d{2}',   # +7 XXX XXX XX XX
        r'8\s?\(\d{3}\)\s?\d{3}-\d{2}-\d{2}',     # 8 (XXX) XXX-XX-XX
        r'8\s?\d{3}\s?\d{3}\s?\d{2}\s?\d{2}',      # 8 XXX XXX XX XX
        r'\d{3}-\d{3}-\d{2}-\d{2}',                # XXX-XXX-XX-XX
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0)
            if validate_phone(phone):
                return format_phone(phone)
    
    return None


def extract_email_from_text(text: str) -> Optional[str]:
    """
    Извлечение email из текста
    
    Args:
        text: Текст для поиска email
        
    Returns:
        Найденный email или None
    """
    import re
    
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    
    return match.group(0) if match else None


def normalize_text(text: str) -> str:
    """
    Нормализация текста для обработки
    
    Args:
        text: Исходный текст
        
    Returns:
        Нормализованный текст
    """
    import re
    
    # Приведение к нижнему регистру
    text = text.lower()
    
    # Удаление лишних пробелов
    text = re.sub(r'\s+', ' ', text)
    
    # Удаление знаков препинания в конце
    text = text.strip('.,!?;:')
    
    return text.strip()


def calculate_sentiment_score(text: str) -> float:
    """
    Простой расчет тональности текста
    
    Args:
        text: Текст для анализа
        
    Returns:
        Оценка тональности от -1.0 (негативная) до 1.0 (позитивная)
    """
    positive_words = [
        "хорошо", "отлично", "прекрасно", "замечательно", "супер", "классно",
        "да", "согласен", "понятно", "интересно", "спасибо", "благодарю"
    ]
    
    negative_words = [
        "плохо", "ужасно", "не", "нет", "неинтересно", "непонятно",
        "дорого", "слишком", "проблема", "ошибка", "неправильно"
    ]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    total_words = len(text.split())
    if total_words == 0:
        return 0.0
    
    score = (positive_count - negative_count) / total_words
    return max(-1.0, min(1.0, score))


def format_duration(seconds: int) -> str:
    """
    Форматирование длительности в читаемый вид
    
    Args:
        seconds: Длительность в секундах
        
    Returns:
        Отформатированная длительность
    """
    if seconds < 60:
        return f"{seconds}с"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}м {remaining_seconds}с"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}ч {remaining_minutes}м"


def generate_webhook_signature(payload: str, secret: str) -> str:
    """
    Генерация подписи для webhook
    
    Args:
        payload: Тело запроса
        secret: Секретный ключ
        
    Returns:
        Подпись в hex формате
    """
    return generate_hash(payload + secret, "sha256")


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Проверка подписи webhook
    
    Args:
        payload: Тело запроса
        signature: Подпись для проверки
        secret: Секретный ключ
        
    Returns:
        True если подпись верная, иначе False
    """
    expected_signature = generate_webhook_signature(payload, secret)
    return secrets.compare_digest(signature, expected_signature)
