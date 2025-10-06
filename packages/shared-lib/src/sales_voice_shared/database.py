"""
Подключение к базе данных и управление сессиями
"""

from functools import lru_cache
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from .config import get_settings
from .models import Base

settings = get_settings()


class Database:
    """Класс для управления подключениями к базе данных"""
    
    def __init__(self):
        self.sync_engine = None
        self.async_engine = None
        self.sync_session_factory = None
        self.async_session_factory = None
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Инициализация движков базы данных"""
        # Синхронный движок
        self.sync_engine = create_engine(
            settings.postgres_url,
            pool_size=settings.postgres_pool_size,
            max_overflow=settings.postgres_max_overflow,
            pool_pre_ping=True,
            echo=settings.debug,
        )
        
        # Асинхронный движок
        async_url = settings.postgres_url.replace("postgresql://", "postgresql+asyncpg://")
        self.async_engine = create_async_engine(
            async_url,
            pool_size=settings.postgres_pool_size,
            max_overflow=settings.postgres_max_overflow,
            pool_pre_ping=True,
            echo=settings.debug,
        )
        
        # Фабрики сессий
        self.sync_session_factory = sessionmaker(
            bind=self.sync_engine,
            autocommit=False,
            autoflush=False,
        )
        
        self.async_session_factory = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
        )
    
    def create_tables(self):
        """Создание всех таблиц"""
        Base.metadata.create_all(bind=self.sync_engine)
    
    def drop_tables(self):
        """Удаление всех таблиц"""
        Base.metadata.drop_all(bind=self.sync_engine)
    
    def get_sync_session(self) -> Generator:
        """Получить синхронную сессию"""
        session = self.sync_session_factory()
        try:
            yield session
        finally:
            session.close()
    
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получить асинхронную сессию"""
        async with self.async_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()
    
    def close(self):
        """Закрыть соединения"""
        if self.sync_engine:
            self.sync_engine.dispose()
        if self.async_engine:
            # В реальном приложении нужно использовать asyncio.run()
            pass


# Глобальный экземпляр базы данных
_db: Database = None


@lru_cache()
def get_database() -> Database:
    """Получить экземпляр базы данных (кэшированный)"""
    global _db
    if _db is None:
        _db = Database()
    return _db


def get_sync_session() -> Generator:
    """Dependency для получения синхронной сессии"""
    db = get_database()
    yield from db.get_sync_session()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения асинхронной сессии"""
    db = get_database()
    async for session in db.get_async_session():
        yield session
