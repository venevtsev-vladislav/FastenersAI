-- =====================================================
-- ФУНКЦИИ ДЛЯ БИЗНЕС-ЛОГИКИ КРЕПЕЖА
-- =====================================================

-- 1. УМНЫЙ ПОИСК С ВЕСАМИ
CREATE OR REPLACE FUNCTION smart_search_parts(
    search_query TEXT,
    user_intent JSONB DEFAULT '{}'::JSONB
) RETURNS TABLE(
    sku TEXT,
    name TEXT,
    relevance_score DECIMAL,
    match_reason TEXT,
    pack_size DECIMAL,
    unit TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pc.sku,
        pc.name,
        CASE 
            -- Точное совпадение названия
            WHEN pc.name ILIKE '%' || search_query || '%' THEN 1.0
            -- Совпадение по типу из user_intent
            WHEN user_intent->>'type' IS NOT NULL 
                 AND pc.name ILIKE '%' || (user_intent->>'type') || '%' THEN 0.9
            -- Совпадение по диаметру
            WHEN user_intent->>'diameter' IS NOT NULL 
                 AND pc.name ILIKE '%' || (user_intent->>'diameter') || '%' THEN 0.8
            -- Совпадение по материалу
            WHEN user_intent->>'material' IS NOT NULL 
                 AND pc.name ILIKE '%' || (user_intent->>'material') || '%' THEN 0.7
            -- Совпадение по длине
            WHEN user_intent->>'length' IS NOT NULL 
                 AND pc.name ILIKE '%' || (user_intent->>'length') || '%' THEN 0.6
            -- Частичное совпадение слов
            ELSE 0.3
        END as relevance_score,
        CASE 
            WHEN pc.name ILIKE '%' || search_query || '%' THEN 'Точное совпадение'
            WHEN user_intent->>'type' IS NOT NULL 
                 AND pc.name ILIKE '%' || (user_intent->>'type') || '%' THEN 'Совпадение по типу'
            WHEN user_intent->>'diameter' IS NOT NULL 
                 AND pc.name ILIKE '%' || (user_intent->>'diameter') || '%' THEN 'Совпадение по диаметру'
            WHEN user_intent->>'material' IS NOT NULL 
                 AND pc.name ILIKE '%' || (user_intent->>'material') || '%' THEN 'Совпадение по материалу'
            WHEN user_intent->>'length' IS NOT NULL 
                 AND pc.name ILIKE '%' || (user_intent->>'length') || '%' THEN 'Совпадение по длине'
            ELSE 'Частичное совпадение'
        END as match_reason,
        COALESCE(pc.pack_size, 1) as pack_size,
        COALESCE(pc.unit, 'шт') as unit
    FROM parts_catalog pc
    WHERE pc.name ILIKE '%' || search_query || '%'
       OR (user_intent->>'type' IS NOT NULL AND pc.name ILIKE '%' || (user_intent->>'type') || '%')
       OR (user_intent->>'diameter' IS NOT NULL AND pc.name ILIKE '%' || (user_intent->>'diameter') || '%')
       OR (user_intent->>'material' IS NOT NULL AND pc.name ILIKE '%' || (user_intent->>'material') || '%')
       OR (user_intent->>'length' IS NOT NULL AND pc.name ILIKE '%' || (user_intent->>'length') || '%')
    ORDER BY relevance_score DESC
    LIMIT 50;
END;
$$ LANGUAGE plpgsql;

-- 2. РАСЧЕТ УПАКОВОК
CREATE OR REPLACE FUNCTION calculate_packaging(
    requested_qty INTEGER,
    pack_size INTEGER DEFAULT 1
) RETURNS TABLE(
    packages_needed INTEGER,
    total_quantity INTEGER,
    excess_quantity INTEGER,
    cost_efficiency DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CEIL(requested_qty::DECIMAL / pack_size)::INTEGER as packages_needed,
        CEIL(requested_qty::DECIMAL / pack_size)::INTEGER * pack_size as total_quantity,
        (CEIL(requested_qty::DECIMAL / pack_size)::INTEGER * pack_size) - requested_qty as excess_quantity,
        CASE 
            WHEN pack_size = 1 THEN 1.0
            ELSE (requested_qty::DECIMAL / (CEIL(requested_qty::DECIMAL / pack_size) * pack_size))
        END as cost_efficiency;
END;
$$ LANGUAGE plpgsql;

-- 3. ПОИСК АЛЬТЕРНАТИВ
CREATE OR REPLACE FUNCTION find_alternatives(
    target_sku VARCHAR(100),
    max_results INTEGER DEFAULT 5
) RETURNS TABLE(
    sku VARCHAR(100),
    name TEXT,
    similarity_score DECIMAL,
    reason TEXT,
    pack_size DECIMAL,
    unit VARCHAR(20)
) AS $$
DECLARE
    target_name TEXT;
    target_type TEXT;
BEGIN
    -- Получаем информацию о целевом товаре
    SELECT pc.name, pc.type INTO target_name, target_type
    FROM parts_catalog pc
    WHERE pc.sku = target_sku;
    
    RETURN QUERY
    SELECT 
        pc.sku,
        pc.name,
        CASE
            -- Похожий тип
            WHEN pc.type = target_type THEN 0.9
            -- Похожее название
            WHEN similarity(pc.name, target_name) > 0.3 THEN 0.7
            -- Тот же материал
            WHEN pc.material = (SELECT material FROM parts_catalog WHERE sku = target_sku) THEN 0.6
            ELSE 0.3
        END as similarity_score,
        CASE
            WHEN pc.type = target_type THEN 'Тот же тип детали'
            WHEN similarity(pc.name, target_name) > 0.3 THEN 'Похожее название'
            WHEN pc.material = (SELECT material FROM parts_catalog WHERE sku = target_sku) THEN 'Тот же материал'
            ELSE 'Общая категория'
        END as reason,
        COALESCE(pc.pack_size, 1) as pack_size,
        COALESCE(pc.unit, 'шт') as unit
    FROM parts_catalog pc
    WHERE pc.sku != target_sku
    ORDER BY similarity_score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- 4. АНАЛИЗ ЗАПРОСА С РЕКОМЕНДАЦИЯМИ
CREATE OR REPLACE FUNCTION analyze_request_with_recommendations(
    user_intent JSONB
) RETURNS TABLE(
    recommendation_type VARCHAR(50),
    message TEXT,
    suggested_actions JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE
            -- Проверяем полноту запроса
            WHEN user_intent->>'type' IS NULL THEN 'incomplete_type'
            WHEN user_intent->>'diameter' IS NULL THEN 'incomplete_diameter'
            WHEN user_intent->>'quantity' IS NULL THEN 'incomplete_quantity'
            ELSE 'complete'
        END as recommendation_type,
        
        CASE
            WHEN user_intent->>'type' IS NULL THEN 'Укажите тип детали (болт, винт, саморез и т.д.)'
            WHEN user_intent->>'diameter' IS NULL THEN 'Укажите диаметр детали'
            WHEN user_intent->>'quantity' IS NULL THEN 'Укажите количество'
            ELSE 'Запрос полный, ищем детали...'
        END as message,
        
        CASE
            WHEN user_intent->>'type' IS NULL THEN 
                '["болт", "винт", "саморез", "анкер", "гайка", "шайба", "дюбель", "шуруп"]'::JSONB
            WHEN user_intent->>'diameter' IS NULL THEN 
                '["M6", "M8", "M10", "M12", "M16", "M20", "M24", "M30"]'::JSONB
            WHEN user_intent->>'quantity' IS NULL THEN 
                '["1", "10", "50", "100", "500", "1000"]'::JSONB
            ELSE '[]'::JSONB
        END as suggested_actions;
END;
$$ LANGUAGE plpgsql;

-- 5. ПОЛНЫЙ АНАЛИЗ ЗАКАЗА
CREATE OR REPLACE FUNCTION process_complete_order(
    order_items JSONB
) RETURNS TABLE(
    sku VARCHAR(100),
    name TEXT,
    requested_qty INTEGER,
    available_qty INTEGER,
    pack_size DECIMAL,
    packages_needed INTEGER,
    total_quantity INTEGER,
    excess_quantity INTEGER,
    alternatives JSONB,
    status VARCHAR(50)
) AS $$
DECLARE
    item JSONB;
    item_sku VARCHAR(100);
    item_qty INTEGER;
    search_result RECORD;
    packaging_result RECORD;
    alternatives_result RECORD;
BEGIN
    -- Обрабатываем каждый элемент заказа
    FOR item IN SELECT * FROM jsonb_array_elements(order_items)
    LOOP
        item_sku := item->>'sku';
        item_qty := (item->>'quantity')::INTEGER;
        
        -- Ищем деталь
        SELECT * INTO search_result
        FROM parts_catalog pc
        WHERE pc.sku = item_sku
        LIMIT 1;
        
        IF FOUND THEN
            -- Рассчитываем упаковку
            SELECT * INTO packaging_result
            FROM calculate_packaging(item_qty, COALESCE(search_result.pack_size, 1));
            
            -- Ищем альтернативы
            SELECT jsonb_agg(alt.*) INTO alternatives_result
            FROM find_alternatives(item_sku, 3) alt;
            
            -- Возвращаем результат
            RETURN QUERY
            SELECT 
                item_sku,
                search_result.name,
                item_qty,
                0, -- available_quantity не существует в таблице
                search_result.pack_size,
                packaging_result.packages_needed,
                packaging_result.total_quantity,
                packaging_result.excess_quantity,
                COALESCE(alternatives_result, '[]'::JSONB),
                'available'
            FROM packaging_result;
        ELSE
            -- Деталь не найдена
            RETURN QUERY
            SELECT 
                item_sku,
                'Не найдено'::TEXT,
                item_qty,
                0,
                0,
                0,
                0,
                0,
                '[]'::JSONB,
                'not_found';
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 6. ОБРАБОТКА МНОЖЕСТВЕННЫХ ЗАКАЗОВ
CREATE OR REPLACE FUNCTION process_multiple_items_order(
    order_items JSONB
) RETURNS TABLE(
    item_number INTEGER,
    sku TEXT,
    name TEXT,
    requested_qty INTEGER,
    pack_size DECIMAL,
    packages_needed INTEGER,
    total_quantity INTEGER,
    excess_quantity INTEGER,
    alternatives JSONB,
    status TEXT,
    relevance_score DECIMAL,
    match_reason TEXT
) AS $$
DECLARE
    item JSONB;
    item_index INTEGER := 1;
    search_result RECORD;
    packaging_result RECORD;
    alternatives_result RECORD;
    search_query TEXT;
    user_intent JSONB;
BEGIN
    -- Обрабатываем каждый элемент заказа
    FOR item IN SELECT * FROM jsonb_array_elements(order_items)
    LOOP
        -- Формируем поисковый запрос для элемента
        search_query := COALESCE(item->>'type', '') || ' ' || 
                       COALESCE(item->>'diameter', '') || ' ' || 
                       COALESCE(item->>'material', '');
        
        -- Создаем user_intent для поиска
        user_intent := jsonb_build_object(
            'type', item->>'type',
            'diameter', item->>'diameter',
            'length', item->>'length',
            'material', item->>'material',
            'coating', item->>'coating',
            'quantity', item->>'quantity'
        );
        
        -- Ищем деталь через умный поиск
        SELECT * INTO search_result
        FROM smart_search_parts(search_query, user_intent)
        LIMIT 1;
        
        IF FOUND THEN
            -- Рассчитываем упаковку
            SELECT * INTO packaging_result
            FROM calculate_packaging(
                COALESCE((item->>'quantity')::INTEGER, 1), 
                COALESCE(search_result.pack_size, 1)
            );
            
            -- Ищем альтернативы
            SELECT jsonb_agg(alt.*) INTO alternatives_result
            FROM find_alternatives(search_result.sku, 3) alt;
            
            -- Возвращаем результат
            RETURN QUERY
            SELECT 
                item_index,
                search_result.sku,
                search_result.name,
                COALESCE((item->>'quantity')::INTEGER, 1),
                search_result.pack_size,
                packaging_result.packages_needed,
                packaging_result.total_quantity,
                packaging_result.excess_quantity,
                COALESCE(alternatives_result, '[]'::JSONB),
                'available',
                search_result.relevance_score,
                search_result.match_reason
            FROM packaging_result;
        ELSE
            -- Деталь не найдена
            RETURN QUERY
            SELECT 
                item_index,
                ''::TEXT,
                'Не найдено'::TEXT,
                COALESCE((item->>'quantity')::INTEGER, 1),
                0::DECIMAL,
                0,
                0,
                0,
                '[]'::JSONB,
                'not_found',
                0.0::DECIMAL,
                'Деталь не найдена в каталоге'::TEXT;
        END IF;
        
        item_index := item_index + 1;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 7. АНАЛИЗ КОМПЛЕКТОВ И СОПУТСТВУЮЩИХ ТОВАРОВ
CREATE OR REPLACE FUNCTION suggest_complementary_items(
    main_item_sku TEXT,
    max_suggestions INTEGER DEFAULT 5
) RETURNS TABLE(
    sku TEXT,
    name TEXT,
    reason TEXT,
    relevance_score DECIMAL
) AS $$
DECLARE
    main_item RECORD;
BEGIN
    -- Получаем информацию об основном товаре
    SELECT * INTO main_item
    FROM parts_catalog pc
    WHERE pc.sku = main_item_sku
    LIMIT 1;
    
    IF NOT FOUND THEN
        RETURN;
    END IF;
    
    -- Ищем сопутствующие товары
    RETURN QUERY
    SELECT 
        pc.sku,
        pc.name,
        CASE
            -- Для болтов - гайки и шайбы
            WHEN main_item.type IN ('болт', 'винт') AND pc.type IN ('гайка', 'шайба') THEN
                'Сопутствующий товар для ' || main_item.type
            -- Для саморезов - дюбели
            WHEN main_item.type = 'саморез' AND pc.type = 'дюбель' THEN
                'Дюбель для самореза'
            -- Для анкеров - шайбы
            WHEN main_item.type = 'анкер' AND pc.type = 'шайба' THEN
                'Шайба для анкера'
            -- Похожий материал
            WHEN pc.material = main_item.material THEN
                'Тот же материал'
            ELSE
                'Похожий товар'
        END as reason,
        CASE
            -- Высокая релевантность для сопутствующих
            WHEN (main_item.type IN ('болт', 'винт') AND pc.type IN ('гайка', 'шайба')) OR
                 (main_item.type = 'саморез' AND pc.type = 'дюбель') OR
                 (main_item.type = 'анкер' AND pc.type = 'шайба') THEN 0.9
            -- Средняя релевантность для похожих
            WHEN pc.material = main_item.material THEN 0.7
            ELSE 0.5
        END as relevance_score
    FROM parts_catalog pc
    WHERE pc.sku != main_item_sku
      AND (
          -- Сопутствующие товары
          (main_item.type IN ('болт', 'винт') AND pc.type IN ('гайка', 'шайба')) OR
          (main_item.type = 'саморез' AND pc.type = 'дюбель') OR
          (main_item.type = 'анкер' AND pc.type = 'шайба') OR
          -- Похожий материал
          pc.material = main_item.material
      )
    ORDER BY relevance_score DESC
    LIMIT max_suggestions;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ИНДЕКСЫ ДЛЯ БЫСТРОГО ПОИСКА
-- =====================================================

-- Индекс для поиска по названию
CREATE INDEX IF NOT EXISTS idx_parts_catalog_name ON parts_catalog USING gin(to_tsvector('russian', name));

-- Индекс для поиска по типу
CREATE INDEX IF NOT EXISTS idx_parts_catalog_type ON parts_catalog(type);

-- Индекс для поиска по материалу
CREATE INDEX IF NOT EXISTS idx_parts_catalog_material ON parts_catalog(material);

-- Индекс для поиска по длине
CREATE INDEX IF NOT EXISTS idx_parts_catalog_length ON parts_catalog(length);

-- Индекс для поиска по SKU
CREATE INDEX IF NOT EXISTS idx_parts_catalog_sku ON parts_catalog(sku);

-- =====================================================
-- КОММЕНТАРИИ К ФУНКЦИЯМ
-- =====================================================

COMMENT ON FUNCTION smart_search_parts IS 'Умный поиск деталей с учетом user_intent и весами релевантности';
COMMENT ON FUNCTION calculate_packaging IS 'Расчет количества упаковок, итогового количества и излишка';
COMMENT ON FUNCTION find_alternatives IS 'Поиск альтернативных деталей по типу, названию и материалу';
COMMENT ON FUNCTION analyze_request_with_recommendations IS 'Анализ запроса пользователя с рекомендациями по улучшению';
COMMENT ON FUNCTION process_complete_order IS 'Полная обработка заказа с расчетом упаковок и альтернативами';
