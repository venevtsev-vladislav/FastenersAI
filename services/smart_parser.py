"""
Умный парсер запросов для крепежных деталей
Определяет когда нужен GPT, а когда можно обойтись правилами
"""

import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SmartParser:
    """Умный парсер для определения необходимости использования GPT"""
    
    def __init__(self):
        # Паттерны для простых форматов (НЕ нужен GPT)
        self.simple_patterns = [
            # DIN стандарты
            r'DIN\s+\d+\s+[M]\d+[x×]\d+',        # DIN 965 M6x20, DIN 603 M6×40
            r'DIN\s+\d+\s+[M]\d+',               # DIN 965 M6
            
            # Метрические размеры
            r'[М]\d+\s+\d+\s*мм',                # M6 20 мм
            r'[М]\d+\s+\d+\s*см',                # M6 2 см
            r'[М]\d+\s+\d+\s*дюйм',              # M6 1 дюйм
            
            # Простые описания
            r'винт\s+[М]\d+',                    # винт M6
            r'гайка\s+[М]\d+',                   # гайка M6
            r'шайба\s+[М]\d+',                   # шайба M6
            r'болт\s+[М]\d+',                    # болт M8
            r'саморез\s+[М]\d+',                 # саморез M4
            
            # С размерами
            r'винт\s+[М]\d+\s+\d+\s*мм',         # винт M6 20 мм
            r'болт\s+[М]\d+\s+\d+\s*мм',         # болт M8 30 мм
            r'саморез\s+[М]\d+\s+\d+\s*мм',      # саморез M4 16 мм
            r'гайка\s+[М]\d+\s+\d+\s*мм',        # гайка M6 20 мм
            r'шайба\s+[М]\d+\s+\d+\s*мм',        # шайба M6 20 мм
            
            # С материалами
            r'винт\s+[М]\d+\s+\d+\s*мм\s+сталь', # винт M6 20 мм сталь
            r'гайка\s+[М]\d+\s+нержавеющая',     # гайка M6 нержавеющая
            
            # С покрытиями
            r'винт\s+[М]\d+\s+\d+\s*мм\s+цинк',  # винт M6 20 мм цинк
            r'болт\s+[М]\d+\s+\d+\s*мм\s+оцинкованный', # болт M8 30 мм оцинкованный
            
            # Расширенные паттерны для болтов
            r'болт\s+[М]\d+[x×]\d+\s+цинк',      # болт М6x40 цинк
            r'болт\s+DIN\s+\d+\s+[М]\d+[x×]\d+', # болт DIN 603 М6×40
            
            # Альтернативные покрытия
            r'[М]\d+\s+цинкованный',              # М6 цинкованный
            r'[М]\d+\s+оцинкованный',             # М6 оцинкованный
        ]
        
        # Индикаторы множественных заказов (НУЖЕН GPT)
        self.multiple_order_indicators = [
            'нужно', 'требуется', 'заказать', 'заказать',
            'разных', 'различных', 'несколько', 'много',
            'комплект', 'набор', 'партия', 'упаковка'
        ]
        
        # Нечеткие описания (НУЖЕН GPT)
        self.vague_words = [
            'что-то', 'какой-то', 'подходящий', 'подходящая',
            'для крепления', 'для сборки', 'мебельный', 'мебельная',
            'с головкой', 'с резьбой', 'специальный', 'специальная',
            'универсальный', 'универсальная', 'конструкционный',
            'грибком', 'грибковая', 'грибковый', 'тарельчатый',
            'потай', 'полупотай', 'шестигранный', 'квадратный',
            'с фрезой', 'самоконтролирующаяся', 'самоконтролирующийся'
        ]
        
        # Слова для голосовых сообщений (НУЖЕН GPT)
        self.voice_indicators = [
            'штука', 'штуки', 'штук', 'кусок', 'куски'
        ]
    
    def should_use_gpt(self, text: str) -> bool:
        """
        Определяет нужен ли GPT для анализа запроса
        
        Returns:
            bool: True если нужен GPT, False если можно обойтись правилами
        """
        text_lower = text.lower().strip()
        
        # Правило 1: Простые форматы - НЕ нужен GPT (высший приоритет)
        if self.is_simple_format(text_lower):
            logger.info(f"🔍 SmartParser: Простой формат, GPT НЕ нужен: {text}")
            return False
        
        # Правило 2: Множественные заказы - нужен GPT
        if self.is_multiple_order(text_lower):
            logger.info(f"🔍 SmartParser: Множественный заказ, GPT нужен: {text}")
            return True
        
        # Правило 3: Нечеткие описания - нужен GPT
        if self.is_vague_description(text_lower):
            logger.info(f"🔍 SmartParser: Нечеткое описание, GPT нужен: {text}")
            return True
        
        # Правило 4: Нестандартные конструкции - нужен GPT
        if self.has_nonstandard_construction(text_lower):
            logger.info(f"🔍 SmartParser: Нестандартная конструкция, GPT нужен: {text}")
            return True
        
        # Правило 5: Длинные запросы - нужен GPT
        if len(text_lower.split()) > 8:
            logger.info(f"🔍 SmartParser: Длинный запрос, GPT нужен: {text}")
            return True
        
        # Правило 6: Специальные символы - нужен GPT
        if self.has_special_formatting(text_lower):
            logger.info(f"🔍 SmartParser: Специальное форматирование, GPT нужен: {text}")
            return True
        
        # По умолчанию - НЕ нужен GPT
        logger.info(f"🔍 SmartParser: Стандартный запрос, GPT НЕ нужен: {text}")
        return False
    
    def is_simple_format(self, text: str) -> bool:
        """Проверяет соответствует ли текст простым паттернам"""
        for pattern in self.simple_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def is_multiple_order(self, text: str) -> bool:
        """Проверяет является ли запрос множественным заказом"""
        # Сначала проверяем простые форматы
        if self.is_simple_format(text):
            return False
        
        # Затем проверяем индикаторы множественных заказов
        return any(indicator in text for indicator in self.multiple_order_indicators)
    
    def is_vague_description(self, text: str) -> bool:
        """Проверяет содержит ли запрос нечеткие описания"""
        return any(word in text for word in self.vague_words)
    
    def has_special_formatting(self, text: str) -> bool:
        """Проверяет есть ли специальное форматирование"""
        special_chars = ['/', '\\', '(', ')', '[', ']', '{', '}', '|', '&', '+']
        return any(char in text for char in special_chars)
    
    def has_nonstandard_construction(self, text: str) -> bool:
        """Проверяет есть ли нестандартные конструкции в запросе"""
        # Нестандартные предлоги и конструкции
        nonstandard_patterns = [
            r'с\s+\w+',           # "с грибком", "с фрезой"
            r'на\s+\d+',          # "на 40", "на 20"
            r'для\s+\w+',         # "для дерева", "для металла"
        ]
        
        for pattern in nonstandard_patterns:
            if re.search(pattern, text):
                logger.info(f"🔍 SmartParser: Найдена нестандартная конструкция '{pattern}' в '{text}'")
                return True
        
        # Проверяем специфические слова
        specific_words = ['грибком', 'грибковая', 'грибковый', 'тарельчатый', 'потай']
        if any(word in text for word in specific_words):
            logger.info(f"🔍 SmartParser: Найдено специфическое слово в '{text}'")
            return True
        
        return False
    
    def parse_simple_query(self, text: str) -> Dict[str, Any]:
        """
        Парсит простой запрос по правилам (без GPT)
        
        Args:
            text: Текст запроса
            
        Returns:
            dict: Структурированные данные
        """
        # Предварительная обработка текста
        text = self._preprocess_text(text)
        text_lower = text.lower().strip()
        parts = text_lower.split()
        
        result = {
            'type': None,
            'diameter': None,
            'length': None,
            'material': None,
            'coating': None,
            'standard': None,
            'grade': None,
            'quantity': 1,
            'confidence': 0.95,
            'is_simple_parsed': True
        }
        
        # Определяем тип детали
        type_keywords = ['винт', 'гайка', 'шайба', 'болт', 'саморез', 'шуруп', 'анкер', 'дюбель']
        for i, part in enumerate(parts):
            if part in type_keywords:
                result['type'] = part
                break
        
        # Ищем диаметр (M6, M8, 6 мм, 8 мм)
        for i, part in enumerate(parts):
            if part.startswith('m') or part.startswith('м'):
                result['diameter'] = part.upper()
                break
            elif 'мм' in part or 'см' in part:
                # Извлекаем число
                number = re.search(r'(\d+(?:[,.]\d+)?)', part)
                if number:
                    result['diameter'] = number.group(1) + ' мм'
                break
        
        # Ищем размеры в формате M6x40, M6×40
        for i, part in enumerate(parts):
            if re.search(r'[МM]\d+[x×]\d+', part, re.IGNORECASE):
                # Разделяем на диаметр и длину
                match = re.search(r'([МM]\d+)[x×](\d+)', part, re.IGNORECASE)
                if match:
                    result['diameter'] = match.group(1).upper()
                    result['length'] = f"{match.group(2)} мм"
                break
        
        # Ищем длину
        for i, part in enumerate(parts):
            if 'мм' in part or 'см' in part or 'дюйм' in part:
                if i > 0 and parts[i-1].isdigit():
                    result['length'] = f"{parts[i-1]} {part}"
                elif re.search(r'(\d+(?:[,.]\d+)?)', part):
                    number = re.search(r'(\d+(?:[,.]\d+)?)', part).group(1)
                    unit = re.search(r'(мм|см|дюйм)', part).group(1)
                    result['length'] = f"{number} {unit}"
                break
        
        # Ищем материал
        materials = ['сталь', 'нержавеющая', 'латунь', 'алюминий', 'пластик', 'металл']
        for part in parts:
            if part in materials:
                result['material'] = part
                break
        
        # Ищем покрытие
        coatings = ['цинк', 'оцинкованный', 'хромированный', 'крашеный', 'железо', 'цинкованный']
        for part in parts:
            if part in coatings:
                result['coating'] = part
                break
        
        # Ищем покрытие в конце слова (цинкованный, оцинкованный)
        for part in parts:
            if part.endswith('ный') and ('цинк' in part or 'оцинк' in part):
                result['coating'] = part
                break
        
        # Ищем стандарт (DIN, ISO, ГОСТ)
        for i, part in enumerate(parts):
            if part.upper() in ['DIN', 'ISO', 'ГОСТ', 'EN']:
                if i + 1 < len(parts) and parts[i + 1].isdigit():
                    result['standard'] = f"{part.upper()} {parts[i + 1]}"
                break
        
        # Ищем класс прочности (A2, A4, 8.8, 10.9)
        for part in parts:
            if re.match(r'[A]\d+', part.upper()) or re.match(r'\d+\.\d+', part):
                result['grade'] = part.upper()
                break
        
        # Ищем количество
        for part in parts:
            if part.isdigit():
                result['quantity'] = int(part)
                break
        
        logger.info(f"🔍 SmartParser: Разобран простой запрос: {result}")
        return result
    
    def _preprocess_text(self, text: str) -> str:
        """Предварительная обработка текста для лучшего распознавания"""
        # Заменяем символы на стандартные
        text = text.replace('×', 'x')  # Заменяем × на x
        text = text.replace('Х', 'x')  # Заменяем Х на x
        text = text.replace('х', 'x')  # Заменяем х на x
        
        # Нормализуем пробелы
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def parse_query(self, text: str) -> Dict[str, Any]:
        """
        Основной метод парсинга - решает нужен ли GPT
        
        Args:
            text: Текст запроса
            
        Returns:
            dict: Результат парсинга с флагом need_gpt
        """
        if self.should_use_gpt(text):
            return {
                'need_gpt': True,
                'processed_text': text,
                'reason': 'Сложный запрос требует GPT анализа'
            }
        else:
            parsed = self.parse_simple_query(text)
            return {
                'need_gpt': False,
                'user_intent': parsed,
                'processed_text': text,
                'reason': 'Простой запрос разобран по правилам'
            }
