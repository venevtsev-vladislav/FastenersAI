"""
Сервис валидации результатов поиска с помощью ИИ
Проверяет соответствие найденных товаров исходному запросу пользователя
"""

import logging
import json
from typing import List, Dict, Any, Tuple
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class ValidationService:
    """Сервис валидации результатов поиска"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        from services.validation_prompts import VALIDATION_PROMPT
        self.validation_prompt = VALIDATION_PROMPT

    async def validate_search_results(
        self, 
        original_request: str, 
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Валидирует результаты поиска с помощью ИИ
        
        Args:
            original_request: Исходный запрос пользователя
            search_results: Результаты поиска
            
        Returns:
            Dict: Результат валидации
        """
        try:
            logger.info("🔍 Начинаю валидацию результатов поиска с помощью ИИ")
            
            # Формируем данные для анализа
            validation_data = self._prepare_validation_data(original_request, search_results)
            
            # Отправляем на анализ ИИ
            validation_result = await self._analyze_with_ai(validation_data)
            
            logger.info(f"✅ Валидация завершена: {validation_result.get('status')}")
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при валидации: {e}")
            return {
                "status": "ERROR",
                "message": f"Ошибка валидации: {str(e)}",
                "issues": [],
                "confidence": 0.0
            }
    
    def _prepare_validation_data(
        self, 
        original_request: str, 
        search_results: List[Dict[str, Any]]
    ) -> str:
        """Подготавливает данные для валидации"""
        
        # Группируем результаты по позициям
        positions_data = {}
        for result in search_results:
            position = result.get('order_position', 0)
            if position not in positions_data:
                positions_data[position] = {
                    'search_query': result.get('full_query', ''),
                    'found_items': []
                }
            
            if result.get('sku') != 'НЕ НАЙДЕНО':
                positions_data[position]['found_items'].append({
                    'sku': result.get('sku', ''),
                    'name': result.get('name', ''),
                    'type': result.get('type', ''),
                    'confidence': result.get('confidence_score', 0)
                })
        
        # Формируем текст для анализа
        analysis_text = f"""
ИСХОДНЫЙ ЗАПРОС ПОЛЬЗОВАТЕЛЯ:
{original_request}

АНАЛИЗ ПОЗИЦИЙ:
"""
        
        for position in sorted(positions_data.keys()):
            pos_data = positions_data[position]
            analysis_text += f"""
ПОЗИЦИЯ {position}:
Поисковый запрос: {pos_data['search_query']}
Найдено товаров: {len(pos_data['found_items'])}
"""
            
            if pos_data['found_items']:
                for item in pos_data['found_items']:
                    analysis_text += f"  - {item['name']} (SKU: {item['sku']}, уверенность: {item['confidence']:.2f})\n"
            else:
                analysis_text += "  - ТОВАР НЕ НАЙДЕН\n"
        
        return analysis_text
    
    async def _analyze_with_ai(self, validation_data: str) -> Dict[str, Any]:
        """Анализирует данные с помощью ИИ"""
        try:
            # Формируем полный промпт
            full_prompt = f"{self.validation_prompt}\n\nДАННЫЕ ДЛЯ АНАЛИЗА:\n{validation_data}"
            
            # Отправляем на анализ через OpenAI API напрямую
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": self.validation_prompt},
                    {"role": "user", "content": f"ДАННЫЕ ДЛЯ АНАЛИЗА:\n{validation_data}"}
                ],
                temperature=0.1,  # Низкая температура для более точных ответов
                max_tokens=1000
            )
            
            # Получаем ответ
            ai_response = response.choices[0].message.content
            
            # Парсим ответ
            try:
                # Пытаемся извлечь JSON из ответа
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = ai_response[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    # Fallback: если JSON не найден, анализируем текстовый ответ
                    result = self._parse_text_response(ai_response)
                
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"Не удалось распарсить JSON ответ: {e}")
                return self._parse_text_response(ai_response)
                
        except Exception as e:
            logger.error(f"Ошибка при анализе с ИИ: {e}")
            return {
                "status": "ERROR",
                "message": f"Ошибка анализа ИИ: {str(e)}",
                "issues": [],
                "confidence": 0.0
            }
    
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """Парсит текстовый ответ ИИ, если JSON не получен"""
        response_lower = response.lower()
        
        if "approved" in response_lower or "одобрено" in response_lower or "все ок" in response_lower:
            status = "APPROVED"
        elif "refinement" in response_lower or "доработка" in response_lower or "уточнение" in response_lower:
            status = "NEEDS_REFINEMENT"
        elif "clarification" in response_lower or "уточнение" in response_lower or "вопрос" in response_lower:
            status = "NEEDS_CLARIFICATION"
        else:
            status = "NEEDS_CLARIFICATION"
        
        return {
            "status": status,
            "message": response,
            "issues": [],
            "confidence": 0.7 if status == "APPROVED" else 0.5
        }
    
    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """Формирует краткое резюме валидации для пользователя"""
        status = validation_result.get('status', 'UNKNOWN')
        message = validation_result.get('message', '')
        
        if status == "APPROVED":
            return f"✅ Валидация пройдена успешно!\n\n{message}"
        
        elif status == "NEEDS_REFINEMENT":
            return f"⚠️ Требуется доработка заказа\n\n{message}"
        
        elif status == "NEEDS_CLARIFICATION":
            return f"❓ Нужны уточнения\n\n{message}"
        
        else:
            return f"❌ Ошибка валидации\n\n{message}"
