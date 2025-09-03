"""
Утилита для загрузки промптов из JSON файлов
"""

import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PromptLoader:
    """Класс для загрузки и управления промптами"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        self._cache = {}
    
    def load_prompt(self, filename: str) -> Dict[str, Any]:
        """Загружает промпт из JSON файла"""
        if filename in self._cache:
            return self._cache[filename]
        
        filepath = os.path.join(self.prompts_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Файл промпта не найден: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                prompt_data = json.load(f)
            
            self._cache[filename] = prompt_data
            logger.info(f"Загружен промпт: {filename}")
            return prompt_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {filename}: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка загрузки промпта {filename}: {e}")
            raise
    
    def get_system_prompt(self, filename: str) -> str:
        """Преобразует JSON промпт в текстовый системный промпт"""
        prompt_data = self.load_prompt(filename)
        
        # Собираем системный промпт из структуры JSON
        system_prompt = self._build_system_prompt(prompt_data)
        return system_prompt
    
    def _build_system_prompt(self, data: Dict[str, Any]) -> str:
        """Строит системный промпт из JSON структуры"""
        prompt_parts = []
        
        # Назначение
        if 'purpose' in data:
            prompt_parts.append(f"НАЗНАЧЕНИЕ: {data['purpose']}")
            prompt_parts.append("")
        
        # Глобальные правила
        if 'rules_global' in data:
            prompt_parts.append("ОБЩИЕ ПРАВИЛА:")
            for rule in data['rules_global']:
                prompt_parts.append(f"- {rule}")
            prompt_parts.append("")
        
        # Правила извлечения
        if 'extraction_rules' in data:
            prompt_parts.append("ПРАВИЛА ИЗВЛЕЧЕНИЯ ПАРАМЕТРОВ:")
            
            for section, rules in data['extraction_rules'].items():
                if isinstance(rules, list):
                    prompt_parts.append(f"{section.upper()}:")
                    for rule in rules:
                        prompt_parts.append(f"- {rule}")
                    prompt_parts.append("")
        
        # Векторный поиск
        if 'vector_search' in data:
            prompt_parts.append("ВЕКТОРНЫЙ ПОИСК:")
            vector_data = data['vector_search']
            if 'use_for' in vector_data:
                prompt_parts.append("Используй для:")
                for use_case in vector_data['use_for']:
                    prompt_parts.append(f"- {use_case}")
            if 'strategy' in vector_data:
                prompt_parts.append(f"Стратегия: {vector_data['strategy']}")
            prompt_parts.append("")
        
        # Формат вывода
        if 'output_format' in data:
            prompt_parts.append("ФОРМАТ ВЫВОДА:")
            output_data = data['output_format']
            
            if 'single_item' in output_data:
                prompt_parts.append("Схема объекта:")
                for field, description in output_data['single_item'].items():
                    prompt_parts.append(f"  {field}: {description}")
                prompt_parts.append("")
            
            if 'rules' in output_data:
                prompt_parts.append("Правила вывода:")
                for rule in output_data['rules']:
                    prompt_parts.append(f"- {rule}")
                prompt_parts.append("")
        
        # Расчет уверенности
        if 'confidence_calculation' in data:
            prompt_parts.append("РАСЧЕТ УВЕРЕННОСТИ:")
            for level, description in data['confidence_calculation'].items():
                prompt_parts.append(f"- {level}: {description}")
            prompt_parts.append("")
        
        # Специальные случаи
        if 'special_cases' in data:
            prompt_parts.append("СПЕЦИАЛЬНЫЕ СЛУЧАИ:")
            for case_name, case_data in data['special_cases'].items():
                prompt_parts.append(f"{case_name.upper()}:")
                if 'example' in case_data:
                    prompt_parts.append(f"Пример: {case_data['example']}")
                if 'parsing' in case_data:
                    prompt_parts.append("Парсинг:")
                    for field, value in case_data['parsing'].items():
                        prompt_parts.append(f"  {field}: {value}")
                prompt_parts.append("")
        
        # Контекст примеров
        if 'examples_context' in data:
            prompt_parts.append(f"КОНТЕКСТ: {data['examples_context']}")
            prompt_parts.append("")
        
        return "\n".join(prompt_parts)
    
    def clear_cache(self):
        """Очищает кэш промптов"""
        self._cache.clear()
        logger.info("Кэш промптов очищен")
