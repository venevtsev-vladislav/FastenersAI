"""
Сервис генерации таблиц из данных Supabase
Можно использовать локально и в Railway
"""

import asyncio
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from database.supabase_client_legacy import get_supabase_client_legacy

logger = logging.getLogger(__name__)

class TableGeneratorService:
    """Сервис для генерации таблиц из данных Supabase"""
    
    def __init__(self):
        self.supabase_client = None
    
    async def initialize(self):
        """Инициализация Supabase клиента"""
        if not self.supabase_client:
            self.supabase_client = await get_supabase_client_legacy()
            if not self.supabase_client or not self.supabase_client.client:
                raise Exception("Не удалось подключиться к Supabase")
            logger.info("✅ TableGeneratorService инициализирован")
    
    async def get_analysis_data(self, days: int = 30) -> Dict[str, Any]:
        """Получает данные для анализа"""
        try:
            await self.initialize()
            
            # Вычисляем дату начала периода
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Получаем все запросы за период
            response = self.supabase_client.client.table('user_requests').select('*').gte('created_at', start_date).order('created_at', desc=True).execute()
            
            if not response.data:
                logger.warning("Нет данных за указанный период")
                return {'requests': [], 'items': [], 'statistics': {}}
            
            # Фильтруем только запросы с GPT результатами
            gpt_requests = []
            all_items = []
            
            for record in response.data:
                user_intent = record.get('user_intent')
                if user_intent:
                    try:
                        if isinstance(user_intent, str):
                            user_intent = json.loads(user_intent)
                        
                        if 'gpt_result' in user_intent and 'items' in user_intent['gpt_result']:
                            gpt_requests.append(record)
                            
                            # Извлекаем элементы
                            items = self._extract_gpt_items(record)
                            all_items.extend(items)
                    except Exception as e:
                        logger.warning(f"Ошибка при обработке записи {record.get('id')}: {e}")
                        continue
            
            # Создаем статистику
            statistics = self._create_statistics(gpt_requests, all_items)
            
            logger.info(f"✅ Получено {len(gpt_requests)} запросов с {len(all_items)} позициями")
            
            return {
                'requests': gpt_requests,
                'items': all_items,
                'statistics': statistics
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении данных: {e}")
            return {'requests': [], 'items': [], 'statistics': {}}
    
    def _extract_gpt_items(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлекает элементы GPT из записи"""
        try:
            user_intent = record.get('user_intent')
            if isinstance(user_intent, str):
                user_intent = json.loads(user_intent)
            
            gpt_result = user_intent.get('gpt_result', {})
            items = gpt_result.get('items', [])
            
            extracted_items = []
            for i, item in enumerate(items, 1):
                extracted_item = {
                    'request_id': record.get('id'),
                    'user_id': record.get('user_id'),
                    'chat_id': record.get('chat_id'),
                    'request_type': record.get('request_type'),
                    'original_content': record.get('original_content', ''),
                    'created_at': record.get('created_at'),
                    'item_number': i,
                    'item_type': item.get('type', ''),
                    'item_diameter': item.get('diameter', ''),
                    'item_length': item.get('length', ''),
                    'item_material': item.get('material', ''),
                    'item_coating': item.get('coating', ''),
                    'item_quantity': item.get('quantity', ''),
                    'item_confidence': item.get('confidence', 0),
                    'item_standard': item.get('standard', ''),
                    'item_subtype': item.get('subtype', '')
                }
                extracted_items.append(extracted_item)
            
            return extracted_items
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении элементов GPT: {e}")
            return []
    
    def _create_statistics(self, requests: List[Dict[str, Any]], items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Создает статистику"""
        if not items:
            return {}
        
        # Общая статистика
        total_requests = len(requests)
        total_items = len(items)
        
        # Статистика по типам
        type_counts = {}
        for item in items:
            item_type = item['item_type']
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        # Статистика по уверенности
        confidence_scores = [item['item_confidence'] for item in items if item['item_confidence']]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Статистика по пользователям
        user_counts = {}
        for item in items:
            user_id = item['user_id']
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        # Статистика по дням
        daily_counts = {}
        for item in items:
            date = item['created_at'][:10]  # YYYY-MM-DD
            daily_counts[date] = daily_counts.get(date, 0) + 1
        
        return {
            'total_requests': total_requests,
            'total_items': total_items,
            'type_counts': type_counts,
            'avg_confidence': avg_confidence,
            'user_counts': user_counts,
            'daily_counts': daily_counts,
            'date_range': {
                'from': min(item['created_at'] for item in items) if items else None,
                'to': max(item['created_at'] for item in items) if items else None
            }
        }
    
    async def generate_excel_report(self, output_file: str = None, days: int = 30) -> Optional[str]:
        """Генерирует Excel отчет"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"supabase_analysis_{timestamp}.xlsx"
            
            # Получаем данные
            data = await self.get_analysis_data(days)
            items = data['items']
            statistics = data['statistics']
            
            if not items:
                logger.warning("Нет данных для генерации отчета")
                return None
            
            # Создаем DataFrame
            df = pd.DataFrame(items)
            
            # Создаем Excel файл
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Основная таблица
                df.to_excel(writer, sheet_name='GPT_Items', index=False)
                
                # Статистика по типам
                if statistics.get('type_counts'):
                    type_df = pd.DataFrame(list(statistics['type_counts'].items()), 
                                         columns=['Тип изделия', 'Количество'])
                    type_df = type_df.sort_values('Количество', ascending=False)
                    type_df.to_excel(writer, sheet_name='Статистика_по_типам', index=False)
                
                # Статистика по пользователям
                if statistics.get('user_counts'):
                    user_df = pd.DataFrame(list(statistics['user_counts'].items()), 
                                         columns=['User_ID', 'Количество_запросов'])
                    user_df = user_df.sort_values('Количество_запросов', ascending=False)
                    user_df.to_excel(writer, sheet_name='Статистика_по_пользователям', index=False)
                
                # Статистика по дням
                if statistics.get('daily_counts'):
                    daily_df = pd.DataFrame(list(statistics['daily_counts'].items()), 
                                          columns=['Дата', 'Количество_позиций'])
                    daily_df = daily_df.sort_values('Дата')
                    daily_df.to_excel(writer, sheet_name='Статистика_по_дням', index=False)
                
                # Сводная информация
                summary_data = [
                    ['Общее количество запросов', statistics.get('total_requests', 0)],
                    ['Общее количество позиций', statistics.get('total_items', 0)],
                    ['Средняя уверенность GPT', f"{statistics.get('avg_confidence', 0):.2f}"],
                    ['Период анализа', f"{statistics.get('date_range', {}).get('from', 'N/A')} - {statistics.get('date_range', {}).get('to', 'N/A')}"],
                    ['Дата генерации отчета', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    ['Количество уникальных типов', len(statistics.get('type_counts', {}))],
                    ['Количество уникальных пользователей', len(statistics.get('user_counts', {}))]
                ]
                summary_df = pd.DataFrame(summary_data, columns=['Параметр', 'Значение'])
                summary_df.to_excel(writer, sheet_name='Сводка', index=False)
            
            logger.info(f"✅ Excel отчет создан: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Ошибка при генерации Excel отчета: {e}")
            return None
    
    async def generate_csv_report(self, output_file: str = None, days: int = 30) -> Optional[str]:
        """Генерирует CSV отчет"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"supabase_analysis_{timestamp}.csv"
            
            # Получаем данные
            data = await self.get_analysis_data(days)
            items = data['items']
            
            if not items:
                logger.warning("Нет данных для генерации отчета")
                return None
            
            # Создаем DataFrame и сохраняем в CSV
            df = pd.DataFrame(items)
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            logger.info(f"✅ CSV отчет создан: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Ошибка при генерации CSV отчета: {e}")
            return None
    
    async def get_summary_report(self, days: int = 30) -> Dict[str, Any]:
        """Получает сводный отчет в JSON формате"""
        try:
            data = await self.get_analysis_data(days)
            return data['statistics']
        except Exception as e:
            logger.error(f"Ошибка при получении сводного отчета: {e}")
            return {}

# Глобальный экземпляр сервиса
_table_generator_service = None

def get_table_generator_service() -> TableGeneratorService:
    """Получает глобальный экземпляр сервиса"""
    global _table_generator_service
    if _table_generator_service is None:
        _table_generator_service = TableGeneratorService()
    return _table_generator_service
