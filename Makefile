# Sales Voice Assistant - Makefile
# Управление проектом голосового ассистента

.PHONY: help install dev build test lint clean docker-build docker-up docker-down k8s-deploy k8s-undeploy

# Переменные
DOCKER_COMPOSE = docker-compose -f infra/docker/docker-compose.yml
KUBECTL = kubectl
HELM = helm

# Цвета для вывода
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Показать справку по командам
	@echo "$(GREEN)Sales Voice Assistant - Команды управления$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости для всех сервисов
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	@if [ -f package.json ]; then npm install; fi
	@if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
	@if [ -f pyproject.toml ]; then pip install -e .; fi
	@echo "$(GREEN)Зависимости установлены$(NC)"

dev: ## Запустить проект в режиме разработки
	@echo "$(GREEN)Запуск в режиме разработки...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Сервисы запущены. Логи: docker-compose logs -f$(NC)"

build: ## Собрать все сервисы
	@echo "$(GREEN)Сборка сервисов...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)Сборка завершена$(NC)"

test: ## Запустить все тесты
	@echo "$(GREEN)Запуск тестов...$(NC)"
	@if [ -f package.json ]; then npm test; fi
	@if [ -f pytest.ini ]; then python -m pytest tests/; fi
	@echo "$(GREEN)Тесты завершены$(NC)"

lint: ## Проверить код линтерами
	@echo "$(GREEN)Проверка кода...$(NC)"
	@if [ -f package.json ]; then npm run lint; fi
	@if [ -f .flake8 ]; then flake8 .; fi
	@if [ -f pyproject.toml ]; then black --check .; fi
	@echo "$(GREEN)Проверка завершена$(NC)"

clean: ## Очистить временные файлы и контейнеры
	@echo "$(GREEN)Очистка...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f
	@if [ -f package.json ]; then rm -rf node_modules; fi
	@if [ -d __pycache__ ]; then find . -name "__pycache__" -type d -exec rm -rf {} +; fi
	@if [ -d .pytest_cache ]; then rm -rf .pytest_cache; fi
	@echo "$(GREEN)Очистка завершена$(NC)"

# Docker команды
docker-build: ## Собрать Docker образы
	@echo "$(GREEN)Сборка Docker образов...$(NC)"
	$(DOCKER_COMPOSE) build --no-cache
	@echo "$(GREEN)Docker образы собраны$(NC)"

docker-up: ## Запустить Docker контейнеры
	@echo "$(GREEN)Запуск Docker контейнеров...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Контейнеры запущены$(NC)"

docker-down: ## Остановить Docker контейнеры
	@echo "$(GREEN)Остановка Docker контейнеров...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Контейнеры остановлены$(NC)"

docker-logs: ## Показать логи Docker контейнеров
	$(DOCKER_COMPOSE) logs -f

# Kubernetes команды
k8s-deploy: ## Развернуть в Kubernetes
	@echo "$(GREEN)Развертывание в Kubernetes...$(NC)"
	$(KUBECTL) apply -f infra/k8s/
	@echo "$(GREEN)Развертывание завершено$(NC)"

k8s-undeploy: ## Удалить из Kubernetes
	@echo "$(GREEN)Удаление из Kubernetes...$(NC)"
	$(KUBECTL) delete -f infra/k8s/
	@echo "$(GREEN)Удаление завершено$(NC)"

k8s-status: ## Показать статус в Kubernetes
	$(KUBECTL) get pods,services,deployments

# Мониторинг
monitor: ## Запустить мониторинг (Prometheus, Grafana, Jaeger)
	@echo "$(GREEN)Запуск мониторинга...$(NC)"
	$(DOCKER_COMPOSE) -f infra/docker/monitoring.yml up -d
	@echo "$(GREEN)Мониторинг запущен:$(NC)"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana: http://localhost:3000"
	@echo "  Jaeger: http://localhost:16686"

# Разработка
dev-telephony: ## Запустить только telephony-gateway в dev режиме
	@echo "$(GREEN)Запуск telephony-gateway...$(NC)"
	cd apps/telephony-gateway && npm run dev

dev-asr: ## Запустить только asr-service в dev режиме
	@echo "$(GREEN)Запуск asr-service...$(NC)"
	cd apps/asr-service && python -m uvicorn main:app --reload --port 8001

dev-tts: ## Запустить только tts-service в dev режиме
	@echo "$(GREEN)Запуск tts-service...$(NC)"
	cd apps/tts-service && python -m uvicorn main:app --reload --port 8002

dev-dialog: ## Запустить только dialog-orchestrator в dev режиме
	@echo "$(GREEN)Запуск dialog-orchestrator...$(NC)"
	cd apps/dialog-orchestrator && python -m uvicorn main:app --reload --port 8003

# Утилиты
logs: ## Показать логи всех сервисов
	$(DOCKER_COMPOSE) logs -f

restart: ## Перезапустить все сервисы
	@echo "$(GREEN)Перезапуск сервисов...$(NC)"
	$(DOCKER_COMPOSE) restart
	@echo "$(GREEN)Сервисы перезапущены$(NC)"

status: ## Показать статус всех сервисов
	@echo "$(GREEN)Статус сервисов:$(NC)"
	$(DOCKER_COMPOSE) ps

# Безопасность
security-scan: ## Сканирование безопасности
	@echo "$(GREEN)Сканирование безопасности...$(NC)"
	@if [ -f package.json ]; then npm audit; fi
	@if [ -f requirements.txt ]; then safety check; fi
	@echo "$(GREEN)Сканирование завершено$(NC)"

# Документация
docs: ## Генерировать документацию
	@echo "$(GREEN)Генерация документации...$(NC)"
	@if [ -f package.json ]; then npm run docs; fi
	@if [ -f pyproject.toml ]; then sphinx-build -b html docs/ docs/_build/html; fi
	@echo "$(GREEN)Документация сгенерирована$(NC)"

# Git hooks
setup-hooks: ## Настроить git hooks
	@echo "$(GREEN)Настройка git hooks...$(NC)"
	@if [ -f .git/hooks/pre-commit ]; then chmod +x .git/hooks/pre-commit; fi
	@echo "$(GREEN)Git hooks настроены$(NC)"

# По умолчанию показываем справку
.DEFAULT_GOAL := help
