"""
Клиент для работы с Supabase
"""

import logging
import json
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, DB_TABLES

logger = logging.getLogger(__name__)

# Глобальная переменная для клиента
_supabase_client: Client = None

async def init_supabase():
    """Инициализирует подключение к Supabase"""
    global _supabase_client
    
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase credentials не настроены, используем заглушку")
            _supabase_client = None
            return
        
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Проверяем подключение
        response = _supabase_client.table('user_requests').select('count').limit(1).execute()
        logger.info("Supabase подключение успешно установлено")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации Supabase: {e}")
        _supabase_client = None

async def save_user_request(user_id: int, chat_id: int, request_type: str, 
                          original_content: str, processed_text: str, user_intent: dict):
    """Сохраняет запрос пользователя в БД"""
    try:
        if not _supabase_client:
            logger.warning("Supabase не инициализирован, пропускаем сохранение")
            return
        
        data = {
            'user_id': user_id,
            'chat_id': chat_id,
            'request_type': request_type,
            'original_content': original_content,
            'processed_text': processed_text,
            'user_intent': json.dumps(user_intent, ensure_ascii=False),
            'created_at': 'now()'
        }
        
        # Пытаемся сохранить, но не прерываем работу при ошибке
        try:
            response = _supabase_client.table(DB_TABLES['user_requests']).insert(data).execute()
            logger.info(f"Запрос пользователя {user_id} сохранен в БД")
        except Exception as db_error:
            error_msg = str(db_error)
            if 'row-level security policy' in error_msg.lower():
                logger.warning(f"Ошибка RLS политики - нужно исправить политики доступа в Supabase: {db_error}")
            elif 'permission denied' in error_msg.lower():
                logger.warning(f"Ошибка прав доступа - проверьте настройки Supabase: {db_error}")
            else:
                logger.warning(f"Не удалось сохранить в БД (продолжаем работу): {db_error}")
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении запроса в БД: {e}")
        # Продолжаем работу без сохранения в БД

async def search_parts(query: str, user_intent: dict = None) -> list:
    """Ищет детали в каталоге по запросу используя Edge Function"""
    try:
        if not _supabase_client:
            logger.warning("Supabase не инициализирован, возвращаем заглушку")
            return []
        
        # Вызываем Edge Function для умного поиска
        import aiohttp
        
        edge_function_url = f"{SUPABASE_URL}/functions/v1/fastener-search"
        headers = {
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Создаем поисковый запрос из user_intent
        if user_intent and user_intent.get('type'):
            parts = []
            item_type = user_intent.get('type', '')
            parts.append(item_type)

            diameter = (user_intent.get('diameter') or '').strip()
            length = (user_intent.get('length') or '').strip()

            # Приводим размеры к формату 4.2x90 и добавляем варианты с х/×
            def clean_mm(value: str) -> str:
                v = value.lower().replace('мм', '').replace(' ', '')
                return v

            if diameter and length:
                d = clean_mm(diameter)
                l = clean_mm(length)
                size_tokens = [f"{d}x{l}", f"{d}х{l}", f"{d}×{l}"]
                parts.extend(size_tokens)
            else:
                if diameter:
                    parts.append(diameter)
                if length:
                    parts.append(length)

            if user_intent.get('coating'):
                parts.append(user_intent['coating'])
            if user_intent.get('standard'):
                parts.append(user_intent['standard'])

            # Если исходный текст содержит ГКЛ — добавим синонимы для повышения совпадений
            ql = (query or '').lower()
            if 'гкл' in ql or 'гипсокарт' in ql:
                parts.extend(['гкл', 'гипсокартон'])

            search_query = ' '.join([p for p in parts if p])
        else:
            # Fallback на исходный запрос
            search_query = query

        # Расширяем токены по справочнику синонимов
        try:
            from services.alias_service import AliasService
            alias_service = AliasService()
            base_tokens = [t for t in search_query.split() if t]
            expanded_tokens = await alias_service.expand_tokens(base_tokens, original_text=query)
            # Собираем строку, избегая повторов
            if expanded_tokens:
                search_query = ' '.join(expanded_tokens)
        except Exception as e:
            logger.warning(f"Не удалось расширить синонимы: {e}")

        # Логируем финальный поисковый запрос (после расширения)
        logger.info(f"Умный поиск через Edge Function по запросу: {search_query}")
        
        # Сохраняем оригинальный user_intent для лучшего поиска
        simplified_user_intent = user_intent.copy() if user_intent else {}
        
        payload = {
            'search_query': search_query,
            'user_intent': simplified_user_intent
        }
        
        # Логируем что отправляем в Edge Function
        logger.info(f"Отправляем в Edge Function: user_intent.type = {simplified_user_intent.get('type')}")
        logger.info(f"Отправляем в Edge Function: user_intent.diameter = {simplified_user_intent.get('diameter')}")
        logger.info(f"Отправляем в Edge Function: user_intent.length = {simplified_user_intent.get('length')}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(edge_function_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                else:
                    logger.error(f"Edge Function вернул ошибку: {response.status}")
                    # Fallback на старый поиск
                    return await _fallback_search_parts(query, user_intent)
        
        # Конвертируем в формат для Excel
        formatted_results = []
        for result in results:
            # Рассчитываем упаковку если указано количество
            if user_intent and user_intent.get('quantity'):
                # Извлекаем числовое значение из строки количества
                qty_str = str(user_intent['quantity'])
                qty_number = int(''.join(filter(str.isdigit, qty_str)))
                
                packaging = await _calculate_packaging_for_result(
                    qty_number, 
                    result.get('pack_size', 1)
                )
            else:
                packaging = {
                    'packages_needed': 0,
                    'total_quantity': 0,
                    'excess_quantity': 0
                }
            
            # Форматируем результат
            formatted_result = {
                'sku': result.get('sku', ''),
                'name': result.get('name', ''),
                'type': _extract_type_from_name(result.get('name', '')),
                'pack_size': result.get('pack_size', 1),
                'unit': result.get('unit', 'шт'),
                'relevance_score': result.get('relevance_score', 0),
                'match_reason': result.get('match_reason', ''),
                'packages_needed': packaging['packages_needed'],
                'total_quantity': packaging['total_quantity'],
                'excess_quantity': packaging['excess_quantity'],
                'confidence_score': int(result.get('relevance_score', 0) * 100),
                'probability_percent': result.get('probability_percent', 1.0),  # Добавляем probability_percent из Edge Function
                'user_intent': user_intent,  # Добавляем user_intent для Excel
                'search_query': result.get('search_query', query),  # Добавляем search_query
                'full_query': result.get('full_query', query)  # Добавляем full_query
            }
            
            formatted_results.append(formatted_result)
        
        # Сортируем по релевантности
        formatted_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"Edge Function поиск вернул {len(formatted_results)} результатов")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Ошибка при поиске через Edge Function: {e}")
        # Fallback на старый поиск
        return await _fallback_search_parts(query, user_intent)

async def _calculate_packaging_for_result(requested_qty: int, pack_size: float) -> dict:
    """Рассчитывает упаковку для одного результата"""
    try:
        if pack_size <= 0:
            return {
                'packages_needed': 0,
                'total_quantity': 0,
                'excess_quantity': 0
            }
        
        # Простой расчет упаковки
        packages_needed = int(requested_qty / pack_size)
        if requested_qty % pack_size > 0:
            packages_needed += 1
        
        total_quantity = packages_needed * pack_size
        excess_quantity = total_quantity - requested_qty
        
        return {
            'packages_needed': packages_needed,
            'total_quantity': total_quantity,
            'excess_quantity': excess_quantity
        }
        
    except Exception as e:
        logger.warning(f"Не удалось рассчитать упаковку: {e}")
        return {
            'packages_needed': 0,
            'total_quantity': 0,
            'excess_quantity': 0
        }

async def _fallback_search_parts(query: str, user_intent: dict = None) -> list:
    """Fallback поиск если умные функции не работают"""
    try:
        logger.info("Используем fallback поиск...")
        
        # Простой поиск по названию
        response = _supabase_client.table(DB_TABLES['parts_catalog'])\
            .select('*')\
            .ilike('name', f'%{query}%')\
            .limit(20)\
            .execute()
        
        results = response.data if response.data else []
        
        # Базовое форматирование
        formatted_results = []
        for result in results:
            formatted_result = {
                'sku': result.get('sku', ''),
                'name': result.get('name', ''),
                'type': _extract_type_from_name(result.get('name', '')),
                'pack_size': result.get('pack_size', 1),
                'unit': 'шт',
                'relevance_score': 0.5,
                'match_reason': 'Fallback поиск',
                'packages_needed': 0,
                'total_quantity': 0,
                'excess_quantity': 0,
                'confidence_score': 50,
                'probability_percent': 1.0  # Низкая вероятность для fallback
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Ошибка в fallback поиске: {e}")
        return []

def _extract_type_from_name(name: str) -> str:
    """Извлекает тип детали из названия"""
    if not name:
        return 'Неизвестно'
    
    name_lower = name.lower()
    
    if any(word in name_lower for word in ['болт', 'винт']):
        return 'Болт/Винт'
    elif 'саморез' in name_lower:
        return 'Саморез'
    elif 'анкер' in name_lower:
        return 'Анкер'
    elif 'гайка' in name_lower:
        return 'Гайка'
    elif 'шайба' in name_lower:
        return 'Шайба'
    elif 'дюбель' in name_lower:
        return 'Дюбель'
    elif 'шуруп' in name_lower:
        return 'Шуруп'
    else:
        return 'Крепеж'

async def get_aliases() -> list:
    """Получает список алиасов для поиска"""
    try:
        if not _supabase_client:
            logger.warning("Supabase не инициализирован, возвращаем заглушку")
            return []
        
        response = _supabase_client.table(DB_TABLES['aliases']).select('*').execute()
        return response.data if response.data else []
        
    except Exception as e:
        logger.error(f"Ошибка при получении алиасов: {e}")
        return []

async def create_tables():
    """Создает необходимые таблицы в БД (для разработки)"""
    try:
        if not _supabase_client:
            logger.warning("Supabase не инициализирован, пропускаем создание таблиц")
            return
        
        # SQL для создания таблиц
        tables_sql = {
            'user_requests': '''
                CREATE TABLE IF NOT EXISTS user_requests (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    chat_id BIGINT NOT NULL,
                    request_type VARCHAR(50) NOT NULL,
                    original_content TEXT,
                    processed_text TEXT,
                    user_intent JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            ''',
            
            'parts_catalog': '''
                CREATE TABLE IF NOT EXISTS parts_catalog (
                    id SERIAL PRIMARY KEY,
                    sku VARCHAR(100) UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    type VARCHAR(200),
                    pack_size INTEGER,
                    unit VARCHAR(20),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            ''',
            
            'aliases': '''
                CREATE TABLE IF NOT EXISTS aliases (
                    id SERIAL PRIMARY KEY,
                    alias VARCHAR(200) NOT NULL,
                    maps_to JSONB NOT NULL,
                    source_url TEXT,
                    confidence DECIMAL(3,2),
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            '''
        }
        
        # Выполняем SQL
        for table_name, sql in tables_sql.items():
            try:
                _supabase_client.rpc('exec_sql', {'sql': sql}).execute()
                logger.info(f"Таблица {table_name} создана/проверена")
            except Exception as e:
                logger.warning(f"Не удалось создать таблицу {table_name}: {e}")
        
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")


def _rank_results_by_relevance(results: list, query: str) -> list:
    """Ранжирует результаты по релевантности запросу"""
    if not results:
        return results
    
    def calculate_relevance_score(item):
        name = item.get('name', '').lower()
        query_lower = query.lower()
        score = 0
        
        # Точное совпадение - высший балл
        if query_lower in name:
            score += 100
        
        # Совпадение по словам
        query_words = query_lower.split()
        name_words = name.split()
        
        # Подсчитываем совпадающие слова
        matching_words = 0
        for q_word in query_words:
            if len(q_word) > 2:  # Игнорируем короткие слова
                for n_word in name_words:
                    if q_word in n_word or n_word in q_word:
                        matching_words += 1
                        break
        
        # Балл за совпадающие слова
        score += matching_words * 20
        
        # Бонус за длину совпадения
        if len(query_lower) > 5:
            if query_lower[:5] in name:
                score += 10
        
        return score
    
    # Сортируем по релевантности
    ranked_results = sorted(results, key=calculate_relevance_score, reverse=True)
    
    # Возвращаем только топ результаты (максимум 20)
    return ranked_results[:20]

