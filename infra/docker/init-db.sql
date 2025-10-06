-- Инициализация базы данных для Sales Voice Assistant

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица клиентов
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    company VARCHAR(255),
    status VARCHAR(50) DEFAULT 'new',
    source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица звонков
CREATE TABLE IF NOT EXISTS calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id),
    phone_number VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL, -- 'incoming' or 'outgoing'
    status VARCHAR(50) DEFAULT 'initiated',
    duration INTEGER DEFAULT 0,
    recording_url TEXT,
    transcript TEXT,
    summary TEXT,
    sentiment VARCHAR(20),
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица диалогов
CREATE TABLE IF NOT EXISTS dialogs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID REFERENCES calls(id),
    session_id VARCHAR(255) NOT NULL,
    user_message TEXT,
    assistant_message TEXT,
    intent VARCHAR(100),
    entities JSONB,
    confidence DECIMAL(3,2),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица лидов
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id),
    call_id UUID REFERENCES calls(id),
    bitrix24_lead_id INTEGER,
    status VARCHAR(50) DEFAULT 'new',
    source VARCHAR(100),
    product_interest VARCHAR(255),
    budget_range VARCHAR(100),
    timeline VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица сделок
CREATE TABLE IF NOT EXISTS deals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id),
    client_id UUID REFERENCES clients(id),
    bitrix24_deal_id INTEGER,
    status VARCHAR(50) DEFAULT 'new',
    value DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'RUB',
    probability INTEGER DEFAULT 0,
    expected_close_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица продуктов
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'RUB',
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица настроек
CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица метрик
CREATE TABLE IF NOT EXISTS metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    labels JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_calls_client_id ON calls(client_id);
CREATE INDEX IF NOT EXISTS idx_calls_phone_number ON calls(phone_number);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at);
CREATE INDEX IF NOT EXISTS idx_dialogs_call_id ON dialogs(call_id);
CREATE INDEX IF NOT EXISTS idx_dialogs_session_id ON dialogs(session_id);
CREATE INDEX IF NOT EXISTS idx_leads_client_id ON leads(client_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_deals_lead_id ON deals(lead_id);
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
CREATE INDEX IF NOT EXISTS idx_metrics_service_name ON metrics(service_name);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);

-- Триггеры для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calls_updated_at BEFORE UPDATE ON calls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deals_updated_at BEFORE UPDATE ON deals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_settings_updated_at BEFORE UPDATE ON settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Вставка тестовых данных
INSERT INTO users (email, name, role) VALUES 
    ('admin@sales-voice.com', 'Администратор', 'admin'),
    ('manager@sales-voice.com', 'Менеджер продаж', 'manager')
ON CONFLICT (email) DO NOTHING;

INSERT INTO products (name, description, price, category) VALUES 
    ('Базовый пакет', 'Базовый пакет услуг для малого бизнеса', 50000.00, 'package'),
    ('Премиум пакет', 'Расширенный пакет услуг для среднего бизнеса', 150000.00, 'package'),
    ('Корпоративный пакет', 'Полный пакет услуг для крупного бизнеса', 500000.00, 'package')
ON CONFLICT DO NOTHING;

INSERT INTO settings (key, value, description) VALUES 
    ('asr_provider', '"yandex"', 'Провайдер распознавания речи'),
    ('tts_provider', '"yandex"', 'Провайдер синтеза речи'),
    ('llm_provider', '"openai"', 'Провайдер языковой модели'),
    ('max_call_duration', '1800', 'Максимальная длительность звонка в секундах'),
    ('default_language', '"ru-RU"', 'Язык по умолчанию')
ON CONFLICT (key) DO NOTHING;
