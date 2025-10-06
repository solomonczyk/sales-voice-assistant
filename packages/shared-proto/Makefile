# Makefile для генерации Python кода из proto файлов

.PHONY: help clean generate install test

# Переменные
PROTO_DIR = proto
PYTHON_DIR = src/sales_voice_proto
GRPC_PYTHON_PLUGIN = $(shell python -m grpc_tools.protoc --help | grep -q "grpc_python_plugin" && echo "grpc_python_plugin" || echo "grpc_python_plugin")

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

clean: ## Очистить сгенерированные файлы
	@echo "Очистка сгенерированных файлов..."
	rm -rf $(PYTHON_DIR)/*
	find $(PYTHON_DIR) -name "*.py" -delete 2>/dev/null || true
	find $(PYTHON_DIR) -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Очистка завершена"

generate: ## Генерировать Python код из proto файлов
	@echo "Генерация Python кода из proto файлов..."
	@mkdir -p $(PYTHON_DIR)
	
	# Генерация для calls.proto
	python -m grpc_tools.protoc \
		--proto_path=$(PROTO_DIR) \
		--python_out=$(PYTHON_DIR) \
		--grpc_python_out=$(PYTHON_DIR) \
		--mypy_out=$(PYTHON_DIR) \
		$(PROTO_DIR)/sales_voice/v1/calls.proto
	
	# Генерация для dialogs.proto
	python -m grpc_tools.protoc \
		--proto_path=$(PROTO_DIR) \
		--python_out=$(PYTHON_DIR) \
		--grpc_python_out=$(PYTHON_DIR) \
		--mypy_out=$(PYTHON_DIR) \
		$(PROTO_DIR)/sales_voice/v1/dialogs.proto
	
	# Генерация для asr.proto
	python -m grpc_tools.protoc \
		--proto_path=$(PROTO_DIR) \
		--python_out=$(PYTHON_DIR) \
		--grpc_python_out=$(PYTHON_DIR) \
		--mypy_out=$(PYTHON_DIR) \
		$(PROTO_DIR)/sales_voice/v1/asr.proto
	
	# Генерация для tts.proto
	python -m grpc_tools.protoc \
		--proto_path=$(PROTO_DIR) \
		--python_out=$(PYTHON_DIR) \
		--grpc_python_out=$(PYTHON_DIR) \
		--mypy_out=$(PYTHON_DIR) \
		$(PROTO_DIR)/sales_voice/v1/tts.proto
	
	# Генерация для llm.proto
	python -m grpc_tools.protoc \
		--proto_path=$(PROTO_DIR) \
		--python_out=$(PYTHON_DIR) \
		--grpc_python_out=$(PYTHON_DIR) \
		--mypy_out=$(PYTHON_DIR) \
		$(PROTO_DIR)/sales_voice/v1/llm.proto
	
	# Генерация для crm.proto
	python -m grpc_tools.protoc \
		--proto_path=$(PROTO_DIR) \
		--python_out=$(PYTHON_DIR) \
		--grpc_python_out=$(PYTHON_DIR) \
		--mypy_out=$(PYTHON_DIR) \
		$(PROTO_DIR)/sales_voice/v1/crm.proto
	
	# Создание __init__.py файлов
	@touch $(PYTHON_DIR)/__init__.py
	@touch $(PYTHON_DIR)/sales_voice/__init__.py
	@touch $(PYTHON_DIR)/sales_voice/v1/__init__.py
	
	# Исправление импортов в сгенерированных файлах
	@echo "Исправление импортов..."
	@find $(PYTHON_DIR) -name "*_pb2_grpc.py" -exec sed -i 's/import sales_voice\.v1\./from . import /g' {} \;
	@find $(PYTHON_DIR) -name "*_pb2_grpc.py" -exec sed -i 's/from sales_voice\.v1\./from . /g' {} \;
	
	@echo "Генерация завершена"

install: generate ## Установить пакет
	@echo "Установка пакета..."
	pip install -e .
	@echo "Установка завершена"

test: ## Запустить тесты
	@echo "Запуск тестов..."
	pytest tests/ -v
	@echo "Тесты завершены"

lint: ## Проверить код линтерами
	@echo "Проверка кода..."
	black --check .
	isort --check-only .
	flake8 .
	mypy .
	@echo "Проверка завершена"

format: ## Отформатировать код
	@echo "Форматирование кода..."
	black .
	isort .
	@echo "Форматирование завершено"

dev-install: ## Установить для разработки
	@echo "Установка для разработки..."
	pip install -e ".[dev]"
	@echo "Установка завершена"

# По умолчанию показываем справку
.DEFAULT_GOAL := help
