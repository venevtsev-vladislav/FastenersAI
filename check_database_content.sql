-- =====================================================
-- ПРОВЕРКА СОДЕРЖИМОГО БАЗЫ ДАННЫХ
-- =====================================================
-- Выполните эти команды в SQL Editor Supabase

-- 1. Проверяем общее количество записей
SELECT COUNT(*) as total_records FROM parts_catalog;

-- 2. Проверяем типы деталей
SELECT DISTINCT type, COUNT(*) as count 
FROM parts_catalog 
GROUP BY type 
ORDER BY count DESC;

-- 3. Ищем болты
SELECT id, sku, name, type, diameter, length, coating, standard
FROM parts_catalog 
WHERE type ILIKE '%болт%' 
   OR name ILIKE '%болт%'
LIMIT 10;

-- 4. Ищем болты с грибовидной головкой
SELECT id, sku, name, type, diameter, length, coating, standard
FROM parts_catalog 
WHERE name ILIKE '%гриб%' 
   OR name ILIKE '%DIN 603%'
   OR name ILIKE '%грибовид%'
LIMIT 10;

-- 5. Ищем по диаметру M6
SELECT id, sku, name, type, diameter, length, coating, standard
FROM parts_catalog 
WHERE diameter ILIKE '%M6%' 
   OR name ILIKE '%M6%'
LIMIT 10;

-- 6. Ищем по длине 40
SELECT id, sku, name, type, diameter, length, coating, standard
FROM parts_catalog 
WHERE length ILIKE '%40%' 
   OR name ILIKE '%40%'
LIMIT 10;

-- 7. Ищем по покрытию цинк
SELECT id, sku, name, type, diameter, length, coating, standard
FROM parts_catalog 
WHERE coating ILIKE '%цинк%' 
   OR name ILIKE '%цинк%'
   OR name ILIKE '%оцинкован%'
LIMIT 10;

-- 8. Комбинированный поиск (болт + M6 + 40)
SELECT id, sku, name, type, diameter, length, coating, standard
FROM parts_catalog 
WHERE (type ILIKE '%болт%' OR name ILIKE '%болт%')
  AND (diameter ILIKE '%M6%' OR name ILIKE '%M6%')
  AND (length ILIKE '%40%' OR name ILIKE '%40%')
LIMIT 10;
