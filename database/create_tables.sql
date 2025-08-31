-- =====================================================
-- ГОТОВЫЕ SQL ЗАПРОСЫ ДЛЯ SUPABASE
-- Бот "Крепеж AI" - Создание таблиц
-- =====================================================
-- Копируйте и вставляйте каждый блок по очереди в SQL Editor
-- Нажимайте "Run" после каждого блока

-- =====================================================
-- БЛОК 1: Включение расширений
-- =====================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- БЛОК 2: Создание таблицы aliases (алиасы для поиска)
-- =====================================================
CREATE TABLE IF NOT EXISTS aliases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alias TEXT NOT NULL,
    maps_to JSONB NOT NULL,
    source_url TEXT,
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    notes TEXT,
    category TEXT DEFAULT 'general',
    language TEXT DEFAULT 'ru',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_alias UNIQUE(alias)
);

-- =====================================================
-- БЛОК 3: Создание таблицы parts_catalog (каталог деталей)
-- =====================================================
CREATE TABLE IF NOT EXISTS parts_catalog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT,                              -- ← ИЗМЕНЕНО: убрано NOT NULL
    diameter TEXT,
    length TEXT,
    material TEXT,
    coating TEXT,
    grade TEXT,
    pack_size DECIMAL(10,3),               -- ← ИЗМЕНЕНО: INTEGER → DECIMAL(10,3)
    unit TEXT DEFAULT 'шт',
    features JSONB,
    specifications JSONB,
    price DECIMAL(10,2),
    currency TEXT DEFAULT 'RUB',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT positive_pack_size CHECK (pack_size > 0)
    -- ← ИЗМЕНЕНО: убрано CONSTRAINT unique_sku
);

-- =====================================================
-- БЛОК 4: Создание таблицы user_requests (запросы пользователей)
-- =====================================================
CREATE TABLE IF NOT EXISTS user_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    username TEXT,
    request_type TEXT NOT NULL,
    original_content TEXT,
    processed_text TEXT,
    user_intent JSONB,
    confidence DECIMAL(3,2),
    found_parts_count INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- БЛОК 5: Создание таблицы search_history (история поиска)
-- =====================================================
CREATE TABLE IF NOT EXISTS search_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query TEXT NOT NULL,
    query_type TEXT NOT NULL,
    results_count INTEGER DEFAULT 0,
    execution_time_ms INTEGER,
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- БЛОК 6: Создание таблицы file_uploads (загруженные файлы)
-- =====================================================
CREATE TABLE IF NOT EXISTS file_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type TEXT,
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    status TEXT DEFAULT 'uploaded',
    processing_result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- БЛОК 7: Создание таблицы search_suggestions (подсказки)
-- =====================================================
CREATE TABLE IF NOT EXISTS search_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    suggestion TEXT NOT NULL UNIQUE,
    category TEXT,
    popularity INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- БЛОК 8: Создание таблицы bot_statistics (статистика)
-- =====================================================
CREATE TABLE IF NOT EXISTS bot_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    successful_searches INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_date UNIQUE(date)
);

-- =====================================================
-- БЛОК 9: Создание индексов для aliases
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_aliases_alias ON aliases USING gin(to_tsvector('russian', alias));
CREATE INDEX IF NOT EXISTS idx_aliases_maps_to ON aliases USING gin(maps_to);
CREATE INDEX IF NOT EXISTS idx_aliases_confidence ON aliases(confidence);
CREATE INDEX IF NOT EXISTS idx_aliases_category ON aliases(category);
CREATE INDEX IF NOT EXISTS idx_aliases_active ON aliases(is_active);

-- =====================================================
-- БЛОК 10: Создание индексов для parts_catalog
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_parts_sku ON parts_catalog(sku);
CREATE INDEX IF NOT EXISTS idx_parts_name ON parts_catalog USING gin(to_tsvector('russian', name));
CREATE INDEX IF NOT EXISTS idx_parts_type ON parts_catalog(type);
CREATE INDEX IF NOT EXISTS idx_parts_diameter ON parts_catalog(diameter);
CREATE INDEX IF NOT EXISTS idx_parts_features ON parts_catalog USING gin(features);

-- =====================================================
-- БЛОК 11: Создание индексов для остальных таблиц
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_user_requests_user_id ON user_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_user_requests_created_at ON user_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query);
CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at);
CREATE INDEX IF NOT EXISTS idx_file_uploads_user_id ON file_uploads(user_id);
CREATE INDEX IF NOT EXISTS idx_file_uploads_status ON file_uploads(status);
CREATE INDEX IF NOT EXISTS idx_file_uploads_created_at ON file_uploads(created_at);
CREATE INDEX IF NOT EXISTS idx_search_suggestions_suggestion ON search_suggestions(suggestion);
CREATE INDEX IF NOT EXISTS idx_search_suggestions_popularity ON search_suggestions(popularity);

-- =====================================================
-- БЛОК 12: Создание функции для обновления updated_at
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =====================================================
-- БЛОК 13: Создание триггеров для обновления updated_at
-- =====================================================
CREATE TRIGGER update_aliases_updated_at BEFORE UPDATE ON aliases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_parts_catalog_updated_at BEFORE UPDATE ON parts_catalog
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_search_suggestions_updated_at BEFORE UPDATE ON search_suggestions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- БЛОК 14: Вставка базовых подсказок для поиска
-- =====================================================
INSERT INTO search_suggestions (suggestion, category, popularity) VALUES
('болт М8х20', 'болты', 100),
('гайка шестигранная М10', 'гайки', 90),
('шайба пружинная', 'шайбы', 85),
('анкер М12х100', 'анкеры', 80),
('саморез клоп', 'саморезы', 75),
('дюбель распорный', 'дюбели', 70),
('винт потайной', 'винты', 65),
('шуруп по дереву', 'шурупы', 60)
ON CONFLICT (suggestion) DO NOTHING;

-- =====================================================
-- БЛОК 15: Включение RLS (Row Level Security)
-- =====================================================
ALTER TABLE aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE parts_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_statistics ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- БЛОК 16: Создание политик доступа
-- =====================================================
-- Политики для работы бота без аутентификации
CREATE POLICY "Aliases are viewable by everyone" ON aliases
    FOR SELECT USING (true);

CREATE POLICY "Parts catalog is viewable by everyone" ON parts_catalog
    FOR SELECT USING (true);

-- Политики для user_requests - разрешаем вставку без аутентификации
CREATE POLICY "Bot can insert user requests" ON user_requests
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Bot can view user requests" ON user_requests
    FOR SELECT USING (true);

-- Политики для file_uploads - разрешаем работу бота
CREATE POLICY "Bot can upload files" ON file_uploads
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Bot can view files" ON file_uploads
    FOR SELECT USING (true);

CREATE POLICY "Search suggestions are viewable by everyone" ON search_suggestions
    FOR SELECT USING (true);

CREATE POLICY "Bot statistics are viewable by everyone" ON bot_statistics
    FOR SELECT USING (true);

-- Дополнительные политики для полного доступа бота
CREATE POLICY "Bot can update user requests" ON user_requests
    FOR UPDATE USING (true);

CREATE POLICY "Bot can delete user requests" ON user_requests
    FOR DELETE USING (true);

CREATE POLICY "Bot can update files" ON file_uploads
    FOR UPDATE USING (true);

CREATE POLICY "Bot can delete files" ON file_uploads
    FOR DELETE USING (true);

-- =====================================================
-- БЛОК 17: Добавление комментариев к таблицам
-- =====================================================
COMMENT ON TABLE aliases IS 'Алиасы для поиска крепежных деталей';
COMMENT ON TABLE parts_catalog IS 'Основной каталог крепежных деталей';
COMMENT ON TABLE user_requests IS 'Запросы пользователей к боту';
COMMENT ON TABLE search_history IS 'История поисковых запросов';
COMMENT ON TABLE file_uploads IS 'Загруженные пользователями файлы';
COMMENT ON TABLE search_suggestions IS 'Подсказки для поиска';
COMMENT ON TABLE bot_statistics IS 'Статистика использования бота';

-- =====================================================
-- ГОТОВО! Все таблицы созданы
-- =====================================================
-- Теперь можно загружать CSV файлы через Table Editor
-- 
-- СТРУКТУРА CSV ДЛЯ ЗАГРУЗКИ:
-- 
-- 1. parts_catalog.csv:
--    sku,name,type,pack_size,unit
--    5-0010170,Анкер забиваемый латунный М6,Анкер забиваемый латунный М6,0.25,тыс.шт
-- 
-- 2. aliases.csv:
--    alias,maps_to,source_url,confidence,notes,category,language,is_active
--    клоп,"{""type"": ""Саморез"", ""subtype"": ""с прессшайбой""}",https://example.com,0.9,строительный сленг,жаргон,ru,true
