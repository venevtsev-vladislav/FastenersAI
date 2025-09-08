#!/usr/bin/env python3
"""
Генерация таблицы из данных Supabase
Создает Excel файл с анализом запросов пользователей и GPT результатов
"""

import asyncio
import sys
import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_client_legacy import get_supabase_client_legacy
from railway_logging import setup_railway_logging

class TableGenerator:
    """Генератор таблиц из данных Supabase"""
    
    def __init__(self):
        self.supabase_client = None
        self.setup_logging()
    
    def setup_logging(self):
        """Настройка логирования"""
        setup_railway_logging()
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Инициализация Supabase клиента"""
        self.supabase_client = await get_supabase_client_legacy()
        if not self.supabase_client or not self.supabase_client.client:
            raise Exception("Не удалось подключиться к Supabase")
        self.logger.info("✅ Supabase клиент инициализирован")
    
    async def get_user_requests_with_gpt_results(self, days: int = 7) -> List[Dict[str, Any]]:
        """Получает запросы пользователей с GPT результатами за последние N дней"""
        try:
            # Вычисляем дату начала периода
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Получаем все запросы за период
            response = self.supabase_client.client.table('user_requests').select('*').gte('created_at', start_date).order('created_at', desc=True).execute()
            
            if not response.data:
                self.logger.warning("Нет данных за указанный период")
                return []
            
            # Фильтруем только запросы с GPT результатами
            gpt_requests = []
            for record in response.data:
                user_intent = record.get('user_intent')
                if user_intent:
                    try:
                        if isinstance(user_intent, str):
                            user_intent = json.loads(user_intent)
                        
                        if 'gpt_result' in user_intent and 'items' in user_intent['gpt_result']:
                            gpt_requests.append(record)
                    except:
                        continue
            
            self.logger.info(f"✅ Найдено {len(gpt_requests)} запросов с GPT результатами за {days} дней")
            return gpt_requests
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении запросов: {e}")
            return []
    
    def extract_gpt_items(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
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
            self.logger.error(f"Ошибка при извлечении элементов GPT: {e}")
            return []
    
    def create_summary_statistics(self, all_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Создает сводную статистику"""
        if not all_items:
            return {}
        
        # Общая статистика
        total_requests = len(set(item['request_id'] for item in all_items))
        total_items = len(all_items)
        
        # Статистика по типам
        type_counts = {}
        for item in all_items:
            item_type = item['item_type']
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        # Статистика по уверенности
        confidence_scores = [item['item_confidence'] for item in all_items if item['item_confidence']]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Статистика по пользователям
        user_counts = {}
        for item in all_items:
            user_id = item['user_id']
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        return {
            'total_requests': total_requests,
            'total_items': total_items,
            'type_counts': type_counts,
            'avg_confidence': avg_confidence,
            'user_counts': user_counts,
            'date_range': {
                'from': min(item['created_at'] for item in all_items),
                'to': max(item['created_at'] for item in all_items)
            }
        }
    
    async def generate_excel_report(self, output_file: str = None) -> str:
        """Генерирует Excel отчет"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"supabase_analysis_{timestamp}.xlsx"
            
            # Получаем данные
            gpt_requests = await self.get_user_requests_with_gpt_results(days=30)
            
            if not gpt_requests:
                self.logger.warning("Нет данных для генерации отчета")
                return None
            
            # Извлекаем все элементы
            all_items = []
            for record in gpt_requests:
                items = self.extract_gpt_items(record)
                all_items.extend(items)
            
            if not all_items:
                self.logger.warning("Нет элементов GPT для генерации отчета")
                return None
            
            # Создаем DataFrame
            df = pd.DataFrame(all_items)
            
            # Создаем статистику
            stats = self.create_summary_statistics(all_items)
            
            # Создаем Excel файл
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Основная таблица
                df.to_excel(writer, sheet_name='GPT_Items', index=False)
                
                # Статистика по типам
                if stats['type_counts']:
                    type_df = pd.DataFrame(list(stats['type_counts'].items()), 
                                         columns=['Тип изделия', 'Количество'])
                    type_df = type_df.sort_values('Количество', ascending=False)
                    type_df.to_excel(writer, sheet_name='Статистика_по_типам', index=False)
                
                # Статистика по пользователям
                if stats['user_counts']:
                    user_df = pd.DataFrame(list(stats['user_counts'].items()), 
                                         columns=['User_ID', 'Количество_запросов'])
                    user_df = user_df.sort_values('Количество_запросов', ascending=False)
                    user_df.to_excel(writer, sheet_name='Статистика_по_пользователям', index=False)
                
                # Сводная информация
                summary_data = [
                    ['Общее количество запросов', stats['total_requests']],
                    ['Общее количество позиций', stats['total_items']],
                    ['Средняя уверенность GPT', f"{stats['avg_confidence']:.2f}"],
                    ['Период анализа', f"{stats['date_range']['from']} - {stats['date_range']['to']}"],
                    ['Дата генерации отчета', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                ]
                summary_df = pd.DataFrame(summary_data, columns=['Параметр', 'Значение'])
                summary_df.to_excel(writer, sheet_name='Сводка', index=False)
            
            self.logger.info(f"✅ Excel отчет создан: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Ошибка при генерации Excel отчета: {e}")
            return None
    
    async def generate_csv_report(self, output_file: str = None) -> str:
        """Генерирует CSV отчет"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"supabase_analysis_{timestamp}.csv"
            
            # Получаем данные
            gpt_requests = await self.get_user_requests_with_gpt_results(days=30)
            
            if not gpt_requests:
                self.logger.warning("Нет данных для генерации отчета")
                return None
            
            # Извлекаем все элементы
            all_items = []
            for record in gpt_requests:
                items = self.extract_gpt_items(record)
                all_items.extend(items)
            
            if not all_items:
                self.logger.warning("Нет элементов GPT для генерации отчета")
                return None
            
            # Создаем DataFrame и сохраняем в CSV
            df = pd.DataFrame(all_items)
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            self.logger.info(f"✅ CSV отчет создан: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Ошибка при генерации CSV отчета: {e}")
            return None

async def main():
    """Основная функция"""
    print("🔍 ГЕНЕРАЦИЯ ТАБЛИЦЫ ИЗ ДАННЫХ SUPABASE")
    print("=" * 60)
    
    generator = TableGenerator()
    
    try:
        # Инициализируем
        await generator.initialize()
        
        # Генерируем Excel отчет
        print("\n📊 ГЕНЕРАЦИЯ EXCEL ОТЧЕТА")
        print("-" * 40)
        excel_file = await generator.generate_excel_report()
        
        if excel_file:
            print(f"✅ Excel отчет создан: {excel_file}")
            
            # Показываем информацию о файле
            if os.path.exists(excel_file):
                file_size = os.path.getsize(excel_file)
                print(f"📁 Размер файла: {file_size / 1024:.1f} KB")
        else:
            print("❌ Не удалось создать Excel отчет")
        
        # Генерируем CSV отчет
        print("\n📊 ГЕНЕРАЦИЯ CSV ОТЧЕТА")
        print("-" * 40)
        csv_file = await generator.generate_csv_report()
        
        if csv_file:
            print(f"✅ CSV отчет создан: {csv_file}")
            
            # Показываем информацию о файле
            if os.path.exists(csv_file):
                file_size = os.path.getsize(csv_file)
                print(f"📁 Размер файла: {file_size / 1024:.1f} KB")
        else:
            print("❌ Не удалось создать CSV отчет")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
