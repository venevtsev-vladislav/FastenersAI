-- =====================================================
-- ИСПРАВЛЕНИЕ ПОЛИТИК RLS ДЛЯ РАБОТЫ БОТА
-- =====================================================
-- Выполните эти команды в SQL Editor Supabase

-- Вариант 1: Отключение RLS для таблиц бота (рекомендуется для разработки)
ALTER TABLE user_requests DISABLE ROW LEVEL SECURITY;
ALTER TABLE file_uploads DISABLE ROW LEVEL SECURITY;
ALTER TABLE search_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE bot_statistics DISABLE ROW LEVEL SECURITY;

-- Вариант 2: Если хотите оставить RLS, используйте эти политики
-- (выполните только если не используете Вариант 1)

-- Удаляем старые политики
DROP POLICY IF EXISTS "Users can view own requests" ON user_requests;
DROP POLICY IF EXISTS "Users can insert own requests" ON user_requests;
DROP POLICY IF EXISTS "Users can view own files" ON file_uploads;
DROP POLICY IF EXISTS "Users can upload files" ON file_uploads;
DROP POLICY IF EXISTS "Bot statistics are viewable by admins" ON bot_statistics;

-- Создаем новые политики для бота
CREATE POLICY "Bot can insert user requests" ON user_requests
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Bot can view user requests" ON user_requests
    FOR SELECT USING (true);

CREATE POLICY "Bot can update user requests" ON user_requests
    FOR UPDATE USING (true);

CREATE POLICY "Bot can delete user requests" ON user_requests
    FOR DELETE USING (true);

CREATE POLICY "Bot can upload files" ON file_uploads
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Bot can view files" ON file_uploads
    FOR SELECT USING (true);

CREATE POLICY "Bot can update files" ON file_uploads
    FOR UPDATE USING (true);

CREATE POLICY "Bot can delete files" ON file_uploads
    FOR DELETE USING (true);

CREATE POLICY "Bot can insert search history" ON search_history
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Bot can view search history" ON search_history
    FOR SELECT USING (true);

CREATE POLICY "Bot can insert statistics" ON bot_statistics
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Bot can view statistics" ON bot_statistics
    FOR SELECT USING (true);

CREATE POLICY "Bot can update statistics" ON bot_statistics
    FOR UPDATE USING (true);

-- Проверяем статус RLS
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename IN ('user_requests', 'file_uploads', 'search_history', 'bot_statistics');

-- Проверяем политики
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('user_requests', 'file_uploads', 'search_history', 'bot_statistics');
