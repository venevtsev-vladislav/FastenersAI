"""
Конвертер для преобразования ответа OpenAI Assistant в формат Excel
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class AssistantExcelConverter:
    """Конвертирует ответ Assistant в формат для Excel генератора"""
    
    @staticmethod
    def convert_assistant_response_to_excel_format(assistant_response: Dict) -> List[Dict]:
        """Конвертирует ответ Assistant в формат для Excel"""
        try:
            rows = assistant_response.get('rows', [])
            converted_results = []
            
            for row in rows:
                converted_row = AssistantExcelConverter._convert_single_row(row)
                converted_results.append(converted_row)
            
            logger.info(f"Конвертировано {len(converted_results)} строк для Excel")
            return converted_results
            
        except Exception as e:
            logger.error(f"Ошибка при конвертации ответа Assistant: {e}")
            return []
    
    @staticmethod
    def _convert_single_row(row: Dict) -> Dict:
        """Конвертирует одну строку из Assistant в формат Excel"""
        try:
            # Конвертируем поля Assistant в поля Excel
            converted = {
                'sku': row.get('SKU', ''),
                'name': row.get('Наименование', ''),
                'type': AssistantExcelConverter._extract_type_from_name(row.get('Наименование', '')),
                'pack_size': row.get('Фасовка_шт_уп', 0),
                'unit': 'шт',
                'confidence_score': int(row.get('Вероятность', 0) * 100),  # Конвертируем в проценты
                'clarification_question': row.get('Вопрос_пользователю', ''),
                'quantity_requested': row.get('Запрошено_шт', 0),
                'quantity_total': row.get('Итог_шт', 0),
                'quantity_excess': row.get('Излишек_шт', 0),
                'packages_count': row.get('Упаковок_шт', 0),
                'alternatives': row.get('Альтернативы', []),
                'group': row.get('Группа', ''),
                'original_query': row.get('Запрос', '')
            }
            
            return converted
            
        except Exception as e:
            logger.error(f"Ошибка при конвертации строки: {e}")
            return {
                'sku': '',
                'name': 'Ошибка конвертации',
                'type': 'Неизвестно',
                'pack_size': 0,
                'unit': 'шт',
                'confidence_score': 0,
                'clarification_question': 'Ошибка при обработке данных',
                'quantity_requested': 0,
                'quantity_total': 0,
                'quantity_excess': 0,
                'packages_count': 0,
                'alternatives': [],
                'group': '',
                'original_query': ''
            }
    
    @staticmethod
    def _extract_type_from_name(name: str) -> str:
        """Извлекает тип детали из названия"""
        if not name:
            return 'Неизвестно'
        
        name_lower = name.lower()
        
        # Определяем тип по ключевым словам
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
        elif 'блок' in name_lower:
            return 'Блок'
        else:
            return 'Крепеж'
    
    @staticmethod
    def validate_assistant_response(assistant_response: Dict) -> bool:
        """Валидирует структуру ответа Assistant"""
        try:
            if not isinstance(assistant_response, dict):
                return False
            
            if 'rows' not in assistant_response:
                return False
            
            if not isinstance(assistant_response['rows'], list):
                return False
            
            # Проверяем каждую строку
            for row in assistant_response['rows']:
                if not isinstance(row, dict):
                    return False
                
                required_fields = ['Номер', 'Группа', 'Запрос', 'Запрошено_шт', 'SKU', 'Наименование']
                for field in required_fields:
                    if field not in row:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка валидации ответа Assistant: {e}")
            return False
    
    @staticmethod
    def get_response_summary(assistant_response: Dict) -> Dict:
        """Получает сводку по ответу Assistant"""
        try:
            rows = assistant_response.get('rows', [])
            
            summary = {
                'total_rows': len(rows),
                'total_requested': sum(row.get('Запрошено_шт', 0) for row in rows),
                'total_available': sum(row.get('Итог_шт', 0) for row in rows),
                'total_excess': sum(row.get('Излишек_шт', 0) for row in rows),
                'average_confidence': sum(row.get('Вероятность', 0) for row in rows) / len(rows) if rows else 0,
                'rows_with_questions': len([row for row in rows if row.get('Вопрос_пользователю')]),
                'unique_groups': len(set(row.get('Группа', '') for row in rows))
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Ошибка при получении сводки: {e}")
            return {}
