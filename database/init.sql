-- Создание таблиц
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS tariff_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    duration_days INTEGER NOT NULL,
    request_limit INTEGER NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    payment_id VARCHAR(255),
    plan VARCHAR(100),
    request_limit INTEGER DEFAULT 0,
    used_requests INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_links (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    link TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE SET NULL,
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_link TEXT
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tariff_plan_id INTEGER REFERENCES tariff_plans(id),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'RUB',
    status VARCHAR(50) DEFAULT 'pending',
    payment_system VARCHAR(50),
    yookassa_payment_id VARCHAR(255),
    yookassa_confirmation_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS instructions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    text_content TEXT,
    video_url VARCHAR(500),
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставляем базовые тарифные планы
INSERT INTO tariff_plans (id, name, price, duration_days, request_limit, description) VALUES
(1, '1 месяц (5 запросов)', 500.00, 30, 5, 'Месячная подписка с 5 запросами ссылок'),
(2, '3 месяца (15 запросов)', 1200.00, 90, 15, '3 месяца с 15 запросами ссылок'),
(3, '6 месяцев (30 запросов)', 2000.00, 180, 30, '6 месяцев с 30 запросами ссылок'),
(4, '12 месяцев (60 запросов)', 3500.00, 365, 60, 'Годовая подписка с 60 запросами ссылок')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    price = EXCLUDED.price,
    duration_days = EXCLUDED.duration_days,
    request_limit = EXCLUDED.request_limit,
    description = EXCLUDED.description;

-- Базовые инструкции
INSERT INTO instructions (title, text_content, order_index) VALUES
('Как пользоваться ботом', '1. Купите подписку через кнопку "💎 Купить подписку"\n2. После оплаты вы сможете добавлять ссылки\n3. Используйте кнопку "🔗 Добавить ссылку" для сохранения ссылок\n4. Следите за своим лимитом запросов в "📊 Моя статистика"', 1),
('Как добавить ссылку', '1. Нажмите кнопку "🔗 Добавить ссылку"\n2. Отправьте ссылку в формате https://example.com\n3. Бот сохранит ссылку и покажет оставшийся лимит\n4. Вы можете добавлять ссылки пока не исчерпаете лимит вашего тарифа', 2),
('О тарифных планах', '💎 Доступные тарифы:\n\n• 1 месяц - 500₽ (5 запросов)\n• 3 месяца - 1200₽ (15 запросов)\n• 6 месяцев - 2000₽ (30 запросов)\n• 12 месяцев - 3500₽ (60 запросов)\n\nЗапрос - это добавление одной ссылки. Лимит обновляется при покупке новой подписки.', 3)
ON CONFLICT DO NOTHING;

-- Создаем индексы для производительности
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON subscriptions(is_active, end_date);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);
CREATE INDEX IF NOT EXISTS idx_user_requests_user_id ON user_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_user_links_user_id ON user_links(user_id);