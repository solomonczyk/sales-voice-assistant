# Sales Voice Shared Proto

gRPC схемы и сгенерированный код для всех сервисов проекта Sales Voice Assistant.

## Установка

```bash
pip install -e .
```

## Генерация кода

### Автоматическая генерация

```bash
make generate
```

### Ручная генерация

```bash
python -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=src/sales_voice_proto \
    --grpc_python_out=src/sales_voice_proto \
    --mypy_out=src/sales_voice_proto \
    proto/sales_voice/v1/*.proto
```

## Доступные сервисы

### CallService

Управление звонками:

```python
from sales_voice_proto.sales_voice.v1 import calls_pb2, calls_pb2_grpc

# Создание звонка
request = calls_pb2.CreateCallRequest(
    client_id="client-123",
    phone_number="+7 (999) 123-45-67",
    direction=calls_pb2.CallDirection.CALL_DIRECTION_INCOMING
)

response = stub.CreateCall(request)
```

### DialogService

Управление диалогами:

```python
from sales_voice_proto.sales_voice.v1 import dialogs_pb2, dialogs_pb2_grpc

# Создание диалога
request = dialogs_pb2.CreateDialogRequest(
    call_id="call-123",
    session_id="session-456",
    user_message="Привет",
    assistant_message="Здравствуйте! Как дела?",
    intent="greeting",
    confidence=0.95
)

response = stub.CreateDialog(request)
```

### ASRService

Распознавание речи:

```python
from sales_voice_proto.sales_voice.v1 import asr_pb2, asr_pb2_grpc

# Распознавание речи
request = asr_pb2.RecognizeSpeechRequest(
    audio_data=audio_bytes,
    format=asr_pb2.AudioFormat.AUDIO_FORMAT_WAV,
    language="ru-RU",
    session_id="session-123"
)

response = stub.RecognizeSpeech(request)
```

### TTSService

Синтез речи:

```python
from sales_voice_proto.sales_voice.v1 import tts_pb2, tts_pb2_grpc

# Синтез речи
request = tts_pb2.SynthesizeSpeechRequest(
    text="Привет! Как дела?",
    voice_id="alena",
    format=tts_pb2.AudioFormat.AUDIO_FORMAT_WAV,
    session_id="session-123"
)

response = stub.SynthesizeSpeech(request)
```

### LLMService

Языковые модели:

```python
from sales_voice_proto.sales_voice.v1 import llm_pb2, llm_pb2_grpc

# Генерация ответа
context = llm_pb2.DialogContext(
    session_id="session-123",
    messages=[
        llm_pb2.Message(
            role="user",
            content="Привет",
            timestamp=timestamp_pb2.Timestamp()
        )
    ]
)

request = llm_pb2.GenerateResponseRequest(
    context=context,
    model="gpt-4",
    temperature=0.7,
    max_tokens=100
)

response = stub.GenerateResponse(request)
```

### CRMService

Интеграция с CRM:

```python
from sales_voice_proto.sales_voice.v1 import crm_pb2, crm_pb2_grpc

# Создание лида
request = crm_pb2.CreateLeadRequest(
    client_id="client-123",
    call_id="call-456",
    title="Новый лид",
    description="Заинтересован в продукте",
    source="phone_call",
    product_interest="premium_package"
)

response = stub.CreateLead(request)
```

## Использование в сервисах

### Сервер gRPC

```python
import grpc
from concurrent import futures
from sales_voice_proto.sales_voice.v1 import calls_pb2_grpc

class CallServiceImpl(calls_pb2_grpc.CallServiceServicer):
    def CreateCall(self, request, context):
        # Логика создания звонка
        return calls_pb2.CreateCallResponse(call=call)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    calls_pb2_grpc.add_CallServiceServicer_to_server(CallServiceImpl(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()
```

### Клиент gRPC

```python
import grpc
from sales_voice_proto.sales_voice.v1 import calls_pb2, calls_pb2_grpc

def create_call():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = calls_pb2_grpc.CallServiceStub(channel)
        request = calls_pb2.CreateCallRequest(
            client_id="client-123",
            phone_number="+7 (999) 123-45-67",
            direction=calls_pb2.CallDirection.CALL_DIRECTION_INCOMING
        )
        response = stub.CreateCall(request)
        return response.call
```

## Структура проекта

```
proto/
└── sales_voice/
    └── v1/
        ├── calls.proto      # Управление звонками
        ├── dialogs.proto    # Управление диалогами
        ├── asr.proto        # Распознавание речи
        ├── tts.proto        # Синтез речи
        ├── llm.proto        # Языковые модели
        └── crm.proto        # Интеграция с CRM

src/sales_voice_proto/
└── sales_voice/
    └── v1/
        ├── __init__.py
        ├── calls_pb2.py
        ├── calls_pb2_grpc.py
        ├── dialogs_pb2.py
        ├── dialogs_pb2_grpc.py
        ├── asr_pb2.py
        ├── asr_pb2_grpc.py
        ├── tts_pb2.py
        ├── tts_pb2_grpc.py
        ├── llm_pb2.py
        ├── llm_pb2_grpc.py
        ├── crm_pb2.py
        └── crm_pb2_grpc.py
```

## Разработка

### Установка зависимостей

```bash
make dev-install
```

### Генерация кода

```bash
make generate
```

### Тестирование

```bash
make test
```

### Линтинг

```bash
make lint
```

### Форматирование

```bash
make format
```

## Команды Makefile

- `make help` - Показать справку
- `make clean` - Очистить сгенерированные файлы
- `make generate` - Генерировать Python код из proto файлов
- `make install` - Установить пакет
- `make test` - Запустить тесты
- `make lint` - Проверить код линтерами
- `make format` - Отформатировать код
- `make dev-install` - Установить для разработки

## Требования

- Python 3.11+
- grpcio-tools
- protobuf
- mypy-protobuf (для типизации)

## Лицензия

MIT License
