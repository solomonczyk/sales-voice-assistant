"""
Модели данных для Sales Voice Assistant
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, 
    Numeric, String, Text, UUID
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class CallDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class CallStatus(str, Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"


class ClientStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class DealStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    NEGOTIATION = "negotiation"
    APPROVED = "approved"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Client(Base):
    __tablename__ = "clients"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), unique=True, nullable=False)
    name = Column(String(255))
    email = Column(String(255))
    company = Column(String(255))
    status = Column(SQLEnum(ClientStatus), default=ClientStatus.NEW)
    source = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    calls = relationship("Call", back_populates="client")
    leads = relationship("Lead", back_populates="client")
    deals = relationship("Deal", back_populates="client")


class Call(Base):
    __tablename__ = "calls"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(PGUUID(as_uuid=True), ForeignKey("clients.id"))
    phone_number = Column(String(20), nullable=False)
    direction = Column(SQLEnum(CallDirection), nullable=False)
    status = Column(SQLEnum(CallStatus), default=CallStatus.INITIATED)
    duration = Column(Integer, default=0)
    recording_url = Column(Text)
    transcript = Column(Text)
    summary = Column(Text)
    sentiment = Column(SQLEnum(Sentiment))
    confidence_score = Column(Numeric(3, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="calls")
    dialogs = relationship("Dialog", back_populates="call")
    leads = relationship("Lead", back_populates="call")


class Dialog(Base):
    __tablename__ = "dialogs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(PGUUID(as_uuid=True), ForeignKey("calls.id"))
    session_id = Column(String(255), nullable=False)
    user_message = Column(Text)
    assistant_message = Column(Text)
    intent = Column(String(100))
    entities = Column(JSONB)
    confidence = Column(Numeric(3, 2))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    call = relationship("Call", back_populates="dialogs")


class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(PGUUID(as_uuid=True), ForeignKey("clients.id"))
    call_id = Column(PGUUID(as_uuid=True), ForeignKey("calls.id"))
    bitrix24_lead_id = Column(Integer)
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW)
    source = Column(String(100))
    product_interest = Column(String(255))
    budget_range = Column(String(100))
    timeline = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="leads")
    call = relationship("Call", back_populates="leads")
    deals = relationship("Deal", back_populates="lead")


class Deal(Base):
    __tablename__ = "deals"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(PGUUID(as_uuid=True), ForeignKey("leads.id"))
    client_id = Column(PGUUID(as_uuid=True), ForeignKey("clients.id"))
    bitrix24_deal_id = Column(Integer)
    status = Column(SQLEnum(DealStatus), default=DealStatus.NEW)
    value = Column(Numeric(12, 2))
    currency = Column(String(3), default="RUB")
    probability = Column(Integer, default=0)
    expected_close_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    lead = relationship("Lead", back_populates="deals")
    client = relationship("Client", back_populates="deals")


class Product(Base):
    __tablename__ = "products"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(12, 2))
    currency = Column(String(3), default="RUB")
    category = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(JSONB, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String(100), nullable=False)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Numeric(15, 4), nullable=False)
    labels = Column(JSONB)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


# Pydantic Models для API
class BaseModel(BaseModel):
    """Базовая модель с общими настройками"""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            uuid.UUID: lambda v: str(v),
        }


class UserCreate(BaseModel):
    email: str = Field(..., description="Email пользователя")
    name: str = Field(..., description="Имя пользователя")
    role: UserRole = Field(default=UserRole.USER, description="Роль пользователя")


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: UserRole
    created_at: datetime
    updated_at: datetime


class ClientCreate(BaseModel):
    phone: str = Field(..., description="Номер телефона")
    name: Optional[str] = Field(None, description="Имя клиента")
    email: Optional[str] = Field(None, description="Email клиента")
    company: Optional[str] = Field(None, description="Компания")
    source: Optional[str] = Field(None, description="Источник")


class ClientResponse(BaseModel):
    id: uuid.UUID
    phone: str
    name: Optional[str]
    email: Optional[str]
    company: Optional[str]
    status: ClientStatus
    source: Optional[str]
    created_at: datetime
    updated_at: datetime


class CallCreate(BaseModel):
    client_id: Optional[uuid.UUID] = Field(None, description="ID клиента")
    phone_number: str = Field(..., description="Номер телефона")
    direction: CallDirection = Field(..., description="Направление звонка")


class CallResponse(BaseModel):
    id: uuid.UUID
    client_id: Optional[uuid.UUID]
    phone_number: str
    direction: CallDirection
    status: CallStatus
    duration: int
    recording_url: Optional[str]
    transcript: Optional[str]
    summary: Optional[str]
    sentiment: Optional[Sentiment]
    confidence_score: Optional[Decimal]
    created_at: datetime
    updated_at: datetime


class DialogCreate(BaseModel):
    call_id: uuid.UUID = Field(..., description="ID звонка")
    session_id: str = Field(..., description="ID сессии")
    user_message: Optional[str] = Field(None, description="Сообщение пользователя")
    assistant_message: Optional[str] = Field(None, description="Ответ ассистента")
    intent: Optional[str] = Field(None, description="Намерение")
    entities: Optional[Dict[str, Any]] = Field(None, description="Извлеченные сущности")
    confidence: Optional[Decimal] = Field(None, description="Уверенность")


class DialogResponse(BaseModel):
    id: uuid.UUID
    call_id: uuid.UUID
    session_id: str
    user_message: Optional[str]
    assistant_message: Optional[str]
    intent: Optional[str]
    entities: Optional[Dict[str, Any]]
    confidence: Optional[Decimal]
    timestamp: datetime


class LeadCreate(BaseModel):
    client_id: uuid.UUID = Field(..., description="ID клиента")
    call_id: Optional[uuid.UUID] = Field(None, description="ID звонка")
    source: Optional[str] = Field(None, description="Источник")
    product_interest: Optional[str] = Field(None, description="Интерес к продукту")
    budget_range: Optional[str] = Field(None, description="Бюджет")
    timeline: Optional[str] = Field(None, description="Временные рамки")
    notes: Optional[str] = Field(None, description="Заметки")


class LeadResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    call_id: Optional[uuid.UUID]
    bitrix24_lead_id: Optional[int]
    status: LeadStatus
    source: Optional[str]
    product_interest: Optional[str]
    budget_range: Optional[str]
    timeline: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class DealCreate(BaseModel):
    lead_id: uuid.UUID = Field(..., description="ID лида")
    client_id: uuid.UUID = Field(..., description="ID клиента")
    value: Optional[Decimal] = Field(None, description="Сумма сделки")
    currency: str = Field(default="RUB", description="Валюта")
    probability: int = Field(default=0, description="Вероятность закрытия")
    expected_close_date: Optional[datetime] = Field(None, description="Ожидаемая дата закрытия")


class DealResponse(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    client_id: uuid.UUID
    bitrix24_deal_id: Optional[int]
    status: DealStatus
    value: Optional[Decimal]
    currency: str
    probability: int
    expected_close_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ProductCreate(BaseModel):
    name: str = Field(..., description="Название продукта")
    description: Optional[str] = Field(None, description="Описание")
    price: Optional[Decimal] = Field(None, description="Цена")
    currency: str = Field(default="RUB", description="Валюта")
    category: Optional[str] = Field(None, description="Категория")


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    price: Optional[Decimal]
    currency: str
    category: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SettingCreate(BaseModel):
    key: str = Field(..., description="Ключ настройки")
    value: Dict[str, Any] = Field(..., description="Значение настройки")
    description: Optional[str] = Field(None, description="Описание")


class SettingResponse(BaseModel):
    id: uuid.UUID
    key: str
    value: Dict[str, Any]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


class MetricCreate(BaseModel):
    service_name: str = Field(..., description="Название сервиса")
    metric_name: str = Field(..., description="Название метрики")
    metric_value: Decimal = Field(..., description="Значение метрики")
    labels: Optional[Dict[str, Any]] = Field(None, description="Метки")


class MetricResponse(BaseModel):
    id: uuid.UUID
    service_name: str
    metric_name: str
    metric_value: Decimal
    labels: Optional[Dict[str, Any]]
    timestamp: datetime


# Response модели для списков
class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    size: int


class ClientListResponse(BaseModel):
    clients: List[ClientResponse]
    total: int
    page: int
    size: int


class CallListResponse(BaseModel):
    calls: List[CallResponse]
    total: int
    page: int
    size: int


class DialogListResponse(BaseModel):
    dialogs: List[DialogResponse]
    total: int
    page: int
    size: int


class LeadListResponse(BaseModel):
    leads: List[LeadResponse]
    total: int
    page: int
    size: int


class DealListResponse(BaseModel):
    deals: List[DealResponse]
    total: int
    page: int
    size: int


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    size: int
